# Pagination / Unbounded-List Audit — 2026-07-12

Read-only audit of all custom apps in this bench: what happens when record
counts grow — are list surfaces paginated, capped, or unbounded? Covers Desk
list views, public/portal pages, custom Desk pages/dashboards, and every
custom API endpoint that returns a list. Method: one deep manual pass over
`good_event` (the trigger question: "what happens if there are too many
events?") + 5 read-only sub-agent audits covering the other 13 apps, findings
spot-verified against code. **Audit only — no code changed.**

Severity scale:
- **High** — guest/public/portal-facing unbounded list over a table that grows
  without bound in production.
- **Medium** — staff-facing unbounded custom surface, or payload-capped
  endpoints whose *server-side* work is still unbounded.
- **Low** — background jobs, domain-bounded sets, or by-design full exports.

---

## Framework baseline (what Frappe already does)

These are the defaults custom code inherits — the reference point for every
finding below:

| Surface | Default behavior |
|---|---|
| Desk list view | Paginated: 100 rows/page on large screens, 20 on small (`base_list.js:48`), user-selectable 20/100/500, "Load More" appends. Count badge capped at 1001 → "1,000+". |
| Desk report view | Paginated the same way (100/page + Load More). |
| Link-field typeahead | Capped (10 results). |
| REST `/api/resource` (v1/v2) | Default `limit_page_length` 20; caller-controlled paging params. |
| `frappe.client.get_list` | Default 20. |
| **Server-side `frappe.get_all` / `frappe.get_list` / `frappe.db.get_all` in Python** | **UNLIMITED unless `limit` is passed.** `limit=0` is also unlimited. This is where every finding in this audit comes from. |

**Answer to the trigger question:** the **Good Event Desk list view is fine** —
it is a standard Frappe list view (no custom `listview_settings` for Good
Event; only benign bulk-action/indicator JS for Good Event Attendee and Good
Event Translation Unit). With 10,000 events, Desk loads 100 at a time.
The problem is the **public catalogue and the embed API**, which render every
matching event server-side on every request — see below.

---

## good_event — deep dive

Current dev-site scale for context: 43 events (37 published in catalogue),
7 masters, 82 bookings, 33 attendees. Everything below is invisible at this
scale and becomes a real cost at 500–5,000+ events (a few years of production
use, since past events stay `is_published=1`).

### HIGH — public event catalogue `/lists`, `/lists/<slug>` is fully unbounded

`services/event_lists.py` — one page view does ALL of this, per request, with
`no_cache = 1` (`www/event_list.py:15`, so no website-cache mitigation):

1. **`_get_events` (`services/event_lists.py:620–634`)** —
   `frappe.get_all("Good Event", filters=..., fields=EVENT_LIST_CARD_FIELDS,
   order_by=...)` with **no limit**. Fetches every published+catalogued event
   matching the facets. No `page`/`offset` parameter exists anywhere in the
   flow, and the templates (`templates/includes/event_list_body.html`) have no
   client-side pagination or "load more" either. Every card renders into one
   HTML response.
2. **Completed events are dropped *after* the fetch** (`event_lists.py:141`,
   `derived_status != "Completed"` in Python). Past events keep
   `is_published=1` + `show_in_catalog=1` forever unless staff manually
   unpublish, so the *fetched* set grows with total history even though the
   *visible* grid only shows current/upcoming events.
3. **`_facet_values` (`event_lists.py:966–977`)** — a **second unbounded
   full fetch** of all matching events (name, region, category, language,
   stream) just to build the filter-dropdown options, plus
   `audience_segment_facets_for_events` over the full name list.
4. **Per-row N+1 translation lookups** — `_translate_event_rows`
   (`event_lists.py:659`) calls `translated_value` per event; the
   translation map is request-cached **per owner document**
   (`translation_units.py:354–366`), so N events ≈ N `Good Event Translation
   Value` queries, + one per master, + taxonomy lookups (those are cached per
   distinct value — bounded).
5. **`_booking_count_map` (`services/event_status.py:131–157`)** — fetches
   **one row per booking attendee** across all fetched events and counts in
   Python. Cost scales with total attendees of all listed events, not just
   event count. Should be `COUNT ... GROUP BY` in SQL.
6. `_schedule_by_event`, `_attach_audience_segments`, `_masters_by_name` —
   properly bulk (one `IN` query each); their cost still scales linearly with
   the unbounded event set.
7. Card images render as plain `<img src>` without `loading="lazy"` — at
   hundreds of cards the browser eagerly fetches every image.

**Growth math:** at ~1,000 historical published events, each catalogue page
view ≈ 2 full `tabGood Event` scans + ~1,000 translation-map queries + an
attendee-rows fetch + full HTML render of the non-completed subset — per
visitor, per request, uncached, guest-accessible.

### HIGH — same path exposed via the SEO embed API, guest + no rate limit

`embed_api.fragment` (`embed_api.py:52`) — `allow_guest=True`, **no
`methods=["GET"]` restriction, no `@rate_limit`** — `kind=list` /
`kind=master_list` runs the exact same unbounded
`build_event_list_context` / `build_event_master_list_context` and returns the
full rendered HTML fragment. This is the endpoint the TYPO3/WordPress embed
package calls server-side (host CMS may cache it, but the endpoint itself is
open — a crawler or abuser hitting it directly triggers a full catalogue
render each call). `public/js/embed.js` (client-side embed) fetches the same
fragment.

### MEDIUM — `/course-topics` master catalogue unbounded

`services/event_master_catalog.py`:
- `_catalog_masters` (`:390–400`) — all `show_in_master_catalog=1` masters,
  `limit=0`. Unbounded, but masters grow much slower than events (7 today).
- `_doctype_sort_meta` (`:801`) — full taxonomy fetch, small tables. Fine.
- Master **detail** pages are healthier: `_planned_events_for_master`
  (`:709–724`) filters `start_date >= today()` — domain-bounded to upcoming
  events only. This is the pattern the event list page should copy.

### LOW / OK — the rest of good_event

- **Guest GET APIs are bounded**: `search_organizations` clamps its limit to
  5–50 (`services/organizations.py:104`) and is rate-limited 120/h;
  `event_registration_config`, `get_published_event_title`,
  `event_subsidy_notice`, `event_waitlist_status`, `public_theme` are
  single-record. `get_translations_for_lang` (`api.py:443`) returns the entire
  merged Frappe translation dict for a language (a large payload, MBs for
  `de`) — not a pagination bug, but an unbounded-payload guest endpoint worth
  remembering.
- **Staff bulk APIs** (`create_and_send_invoices`, `cancel_attendees`,
  `send_attendee_correspondence`, …) operate on the caller's explicit
  selection — bounded by Desk's checked rows (max 500/page). Each row does
  synchronous invoice/email work in the request, so a 500-row selection may
  approach timeout — chunking/enqueue is a nice-to-have, not a pagination bug.
- **Reports**: `good_event_registration_answers` hard-requires an `event`
  filter (bounded). `attendees_export` / `events_export` /
  `financial_forecast` run full-table with `limit=0` when opened without
  filters — **by design** for exports; staff-only, on-demand; report view
  paginates the display. Low.
- **Sitemap** (`www/events_sitemap.py` → `seo.build_sitemap_links`) — all
  published events in flat queries, no N+1. Sitemaps must list everything;
  fine (revisit only if events reach 10k+ where sitemap-index chunking is the
  norm).
- **Workflow/booking Desk lists** — standard paginated list views. Fine.

---

## good_connector

No www pages, no custom Desk pages; the audit surface is the JWT-token-gated
hub webhook API (`goodApi_webhook_appAction` / `userAction` action registry,
`api/portal.py:1161`).

### HIGH — `GetNewsList`: unbounded + N+1

`_action_get_news_list` (`api/portal.py:802`) → `_list_good_news`
(`api/user.py:148`): `frappe.get_all("Good News", filters={"enabled": 1},
...)` — **no limit, no pagination params, no cap**, and per row a
`frappe.db.get_value("User", ..., "full_name")` lookup (`api/portal.py:811`)
plus regex URL-absolutification over the HTML content. `Good News` grows
monotonically (disabling is manual). Every portal app-launch that loads news
pays the full table.

### MEDIUM

- **`GetLinkList`** (`api/portal.py:787` → `api/user.py:134`) — unbounded
  `Good Link` fetch; curated table, slow growth, no N+1.
- **`GetProcessList`** (`api/portal.py:840`) — final response **capped at
  100** (`limit=100`, `:857`) ✅, but the candidate set is materialized
  unbounded first: `_get_assigned_task_names` (`:123`) runs a full-table
  `Task` `_assign LIKE` scan (`:128`), unbounded `ToDo` fetch (`:134`),
  unbounded Portal-User membership task queries (`:82–110`), then re-queries
  the whole name set for app-context filtering (`:199`). Per-request cost
  scales with the user's lifetime task count, not the 100 returned.
- **`GetFileList`** (`api/portal.py:821`) — cap `files[:100]` applied **in
  Python after** `_get_accessible_files` (`:568`) fetches and access-checks
  every candidate `File` row (`:599`, `:615`, no limit). Same shape: payload
  capped, server work unbounded.

### LOW / OK

- `userAction get`/`changeemail` — bounded per caller email (small), though
  `get` does per-customer `get_doc` (N+1 over a tiny N).
- `GetFiles` / `GetFileUrls` / `DeleteFiles` — bounded by the id list in the
  request payload.
- `StoreFiles` — **explicit `MAX_PORTAL_UPLOAD_FILES = 10` cap** ✅.
- Background: `reminder_runner` daily full scan of open reminder tasks (Low);
  **`identity_matching` duplicate scans** (`identity_matching.py:336/355/379/407`)
  are explicit `limit=0` full-table scans with per-row lookups (≈O(N²)),
  enqueued on every Contact/Address/Customer/Supplier/Company save + daily —
  not a request-path issue but the worst absolute query pattern in the app;
  worth a ticket as Contact counts grow.
- Positive: rate limits on all four webhook endpoints; log-retention pruning;
  `portal_helpers.coerce_limit` (`portal_helpers.py:272`) is a proper
  clamp-to-max pagination primitive — **currently dead code with no callers**;
  adopting it is the natural fix for the endpoints above.

---

## barakah_app

Hub list actions delegate to good_connector (`handle_scoped_app_action`); the
local surfaces are the file-target hook, `GetProcessList`, and the Desk
dashboard. No www pages, no scheduler events.

### HIGH — portal file targets return every non-cancelled order

`get_portal_file_targets` (`barakah_app/portal.py:36–45`), reached via the
`GetFileList`/`GetFiles` hub actions through the
`good_connector_portal_file_targets` hook: for each of `Barakah Aqeeqa` /
`Barakah Well`, `frappe.get_all(..., supplier IN ..., generated_file set,
workflow_state != Cancelled, pluck="name")` — **no limit, and completed/Done
historical orders are included**. Orders accumulate forever per supplier
(country office), and good_connector then does per-target attachment work, so
the unbounded target list drives unbounded downstream enumeration.

The task fallback in the same function (`portal.py:49–70`) fetches **all open
Barakah tasks system-wide** (every supplier, no limit) and then filters by
email with a per-row `portal_email_can_access_task` N+1 — scoping happens
after materialization. Medium–High.

### MEDIUM — `sync_open_order_tasks_for_country` (`services.py:208–223`)

Fires on staff save of Barakah Country when `country_office` changes: fetches
**all** orders for the country (incl. terminal) and does per-row
`get_doc`+Task work synchronously in the save request. Infrequent trigger.

### LOW / OK

- `list_barakah_processes` (`GetProcessList`) — **double-bounded**:
  `PORTAL_TASK_LIST_LIMIT = 500` and pre-filtered to the caller's visible open
  tasks ✅.
- `get_home_dashboard` (`dashboard.py:18–92`) — **the reference
  implementation** for the whole bench: `coerce_limit(default=12, maximum=50)`
  on every client-supplied limit, explicit `limit=` on every list,
  `get_permission_aware_count` for totals. "View all" buttons route to
  standard paginated Desk lists.
- Guest `get_order_form_dropdown_options` — small curated sets, rate-limited.
- Backfill/maintenance sweeps (`services.py:790+`, workflow bootstrap) —
  unbounded but patch/console/background paths. Low.

---

## mopi_app

Hub actions delegate to good_connector; `GetStartableProcesses` returns `[]`.
Displayed dashboard lists are properly capped. The issues are count helpers
and pickers that materialize everything.

### MEDIUM

- **Dashboard count paths** (`dashboard.py:76–80, 179–186, 201–211`) —
  `limit_page_length=0` fetches of all visible training modules, all
  participants of all modules, and all certificate-ready participants, only
  to `len()` them — while the same file already uses
  `get_permission_aware_count` correctly for tasks/campaigns (`:165`).
- **`get_expiring_qualification_certificates`** (`user_profile.py:53–103`) —
  per qualification type, unbounded User fetch (±90-day window), sorted in
  Python and sliced to 8. The sibling count function does it right.
- **`run_task_campaign`** (`actions.py:168–278`) — bounded by the campaign's
  target list, but creates Tasks + sends emails synchronously per user in the
  request, with no enqueue path (unlike the certificate flow, which has
  `enqueue_generate_and_send_certificates`).
- **`get_filtered_users`** (`user_filters.py:7–72`) — unbounded User scans
  for the campaign target picker; returns all matching IDs (design-inherent
  for a picker; bounded by employee count in practice).

### LOW / OK

- Portal file targets (`training.py:31–48`) — unbounded but **self-scoped**
  to the requesting user's own certificates. Low (contrast with barakah's
  supplier-wide version).
- Certificate generate/send per module (`training.py:464+, 899+`) —
  wkhtmltopdf/sendmail per participant in-request, but domain-bounded to one
  module's participants, and a background path exists. Low–Medium.
- Training-hours report — year-bounded, permission-gated, full materialization
  is normal Desk-report behavior. Low.
- Displayed dashboard lists use `coerce_limit` (max 50/30/30) ✅; view-all
  goes to standard Desk lists ✅.

---

## miki_app

No www pages (portal is 100% hub-webhook driven); no `frappe.enqueue`
anywhere — all fan-out is synchronous in the HTTP request. Desk home page
delegates to a mostly-bounded dashboard endpoint.

### MEDIUM — portal/guest-reachable (via `goodApi_webhook_MikiAction`)

- **`list_declarations_for_user`** (`declaration_service.py:239`) — all of a
  portal user's declarations, no limit/pagination. Tenant-scoped (the user's
  Customers), so small for normal providers; uncapped for umbrella/Treuhand
  users linked to many Customers.
- **`get_portal_file_targets`** (`portal.py:154`) — declarations + Sales
  Invoices + Overdue Payments for the user's Customer set, all unbounded (but
  batched `IN` queries, tenant-scoped), materialized on every portal file
  request.
- **`search_organizations`** (`good_event_organizations.py:12`, the
  good_event org-typeahead hook) — output capped at 50 ✅ but internally
  materializes **all member Customers** (`limit=0`) and filters by the query
  string **in Python, on every keystroke**. Should be a DB `like` + limit.
  (Note: the good_event *default* provider does exactly that, correctly.)
- **`get_event_participants_for_portal_user`** — final cap 500 ✅,
  tenant-scoped intermediates. Low.

### MEDIUM — staff-facing, real timeout risk

- **`start_campaign`**
  (`miki_declaration_campaign.py:174`) — loops **all** campaign member rows
  (thousands): per row `db.get_value` + `db.exists`×3 + declaration
  `insert()`, then fetches all "Selected" declarations (no limit) and runs
  `apply_workflow` + **one correspondence email each — synchronously in one
  HTTP request** (`freeze: true` in JS, no enqueue). The single highest
  operational risk in the app.
- **`populate_members_from_active_provider_memberships`** (same doctype,
  `:90`) — unbounded Membership join (~thousands), N+1
  `find_existing_year_declaration` per candidate, then one giant
  `campaign.save()`.
- **Campaign readiness / home dashboard** (`campaign_readiness.py:57/209`,
  called from `dashboard.get_home_dashboard`) — per active campaign (≤10 ✅)
  loads the full customers child table and runs several queries **per member**
  plus `get_doc` per existing declaration; truncates to 30 rows only *after*
  materializing everything. Also exposed as `check_campaign_readiness_api`
  and invoked inside `start_campaign`.
- **`refresh_for_campaign`** (`declaration_status.py:100`, `on_update` of
  Campaign) — every campaign save refreshes invoice status per declaration,
  unbounded N+1 write loop in-request.
- **`customer_export`** (`exports.py:314`) — no-arg call exports **all**
  Customers to CSV in memory (`limit_page_length=limit or 0`); role-gated,
  but no default cap.
- **`run_daily_escalation`** — fine as a daily scheduler job (Low), but also
  whitelisted (`api.py:29`) and runs the full fan-out synchronously when
  triggered manually.

### LOW / OK

- Dashboard list panels use `get_permission_aware_list` with
  `coerce_limit(max 30)` ✅; `refresh_statistics` is a SQL `COUNT…GROUP BY`
  ✅; `customer_form.py` summaries are single-Customer-scoped;
  invoice/case helpers use `limit=1`. Data-quality reports are full-scan by
  nature (staff analytics, several N+1s worth batching later). Dataverse
  import is offline/bench-only.

---

## good_newsletter

The send pipeline is the **positive example**: `start_campaign` only
enqueues; the Email Queue builder runs in a background `long` job, batched at
`BATCH_SIZE = 500` with per-batch commit + cancel check + progress
(`services/dispatch.py:37,66–142`). Guest endpoints (unsubscribe, subscribe,
open, click, SNS) are single-record.

### MEDIUM

- **`_bump_campaign_unsubscribed_count`** (`services/suppression.py:160–172`)
  — **guest-reachable** via unsubscribe: selects all unsubscribed recipient
  rows of the campaign and `len()`s them. Should be SQL `COUNT()`. The only
  guest-reachable unbounded fetch in this app group.
- **`cancel_campaign`** (`services/dispatch.py:265–293`) — request path:
  fetches **all** "Not Sent" Email Queue rows for the campaign (no limit) +
  per-row `set_value`. Email Queue grows per campaign × audience.
- **`refresh_campaign_stats` → `_sync_recipient_statuses_from_queue`**
  (`services/tracking.py:249–261`) — staff "Refresh Statistics" joins all
  still-Queued recipients (no limit) + N+1 updates in-request. (Main counters
  are SQL aggregates ✅.) Also called per-campaign by the daily reconcile job.
- **`import_from_source`** (`api/audience.py:50–75`) — materializes the full
  source audience in the request **just to count it** against
  `ENQUEUE_THRESHOLD = 500`, then the background job re-fetches it. The
  threshold+enqueue design is right ✅; the count probe should be a count.

### LOW / OK

- Dashboard `get_overview` — aggregates + `limit=8` recent list ✅. Designer
  JS fetches templates with `limit: 60` ✅. Campaign-performance report
  bounded by campaign count. Editor endpoints single-design. www
  subscribe/unsubscribe pages single-record.

---

## good_analytics

Dashboard is well-architected overall: donor filters are IN-subqueries (not
materialized), KPI tiles aggregate in SQL, and RFM rebuilds are
enqueue-only from the UI (`good_analytics_settings.py:75` ✅, daily_long
scheduler). No endpoint pulls raw Donation rows into Python. The gap: several
endpoints materialize **per-donor / per-(donor, year)** rows in Python, which
scales with the continuously-growing donor base:

### MEDIUM (all staff-facing, `analytics/api.py`)

- `get_overview` last-gift block (`:153–165`) — distinct (donor, year) rows
  into Python.
- `get_retention` (`:224–263`) — one row per (donor, year) for the cohort
  matrix.
- `get_volume` value bands (`:349–367, :410`) — one row per donor + Counter.
- `get_migration` (`:458–480`) — two per-donor window fetches **plus** the
  entire donor universe list, iterated twice.
- `get_campaign_performance` (`:514–541`) — full segment member lists
  (`limit_page_length=0`) into Python sets.
- Segment activation (`segments.py:118/148/388`) — `create_email_group`,
  `export_mailing_list` (XLSX in-request, no cap/enqueue), and the
  newsletter audience provider all materialize full segments via
  `get_member_donors` (`limit_page_length=0`). Mitigations already present:
  set-based `_batch_person_data` batching ✅ (the June N+1 fix),
  `bulk_insert` for member refresh ✅.

### LOW / OK

- `get_rfm` — SQL COUNT+GROUP BY with IN-subquery universe ✅ (the pattern
  the Medium items above should follow). `get_filter_options` bounded by
  campaign count. `rebuild_rfm_scores` background ✅.

---

## good_help — fine

Curated domain: `get_help`/`_get_articles` fetch all enabled Good Help
Articles (no limit) but the table is admin-curated (dozens–low hundreds),
visibility lookups are batched (`_wiki_visibility_map` ✅), search is
client-side over the bounded list, `get_article` is single-record. No
pagination concern.

## workflow_visualizer — fine

One endpoint, one document + one workflow definition; history reads the doc's
own child table. Nothing scales with table growth.

## payrexx_integration — fine

Single-record guest endpoints (HMAC/signature-gated); every list probe uses
`limit=1`/`limit=2` ✅. The unbounded-ish `dev_e2e.py` helpers are
deliberately not whitelisted (dev-only).

---

## non_profit

No guest-facing unbounded lists (the `/donate` campaign dropdown fetches all
*Active* Donation Campaigns — curated, low growth; Grant Application web
listing uses Frappe's standard paginated website list ✅).

### MEDIUM (staff-facing)

- **`get_campaign_donation_chart`** (`donation_campaign.py:47–84`) — fetches
  every paid donation of a campaign-year (`limit_page_length=0`) into Python
  to bucket by month, **and returns one `segments` entry per donation to the
  client**. Should be SQL `GROUP BY MONTH`.
- **Expiring Memberships report** (`report/expiring_memberships/…py:46–62`) —
  loads the **entire Membership table** (only `to_date is set` in SQL); the
  month window is applied in Python afterwards. Push the date bounds into the
  query.
- **`generate_yearly_receipts`** (`donation_receipt.py:131–179`) — the read
  is a proper SQL GROUP-BY-donor ✅, but the write loop inserts one receipt
  per donor **synchronously in the request** — a year-end run over thousands
  of donors risks timeout. Belongs in a background job. (The agent flagged
  `GroupConcat` truncation too; verified `group_concat_max_len` is 1 MB on
  this bench's MariaDB — not a practical risk.)

### LOW / OK

- `get_donations_for_selected_year` — one donor × one fiscal year. Low.
- Rollup recomputes (`major_gifts.py:169/177`), recurring-donation
  processing, expired-status update — daily scheduler jobs. Low.
- Everything else is single-record or `limit=1/2` probes ✅.

---

## good_npo

### MEDIUM

- **`_monthly_donation_totals`** (`dashboard.py:171–193`) — the home
  dashboard chart fetches **all paid donations of the year**
  (`limit_page_length=0` — the comment says the limit was removed on purpose
  because it truncated the chart) into Python and buckets by month/campaign,
  on **every staff Desk home load**. The right fix is SQL GROUP BY
  month+campaign, not re-adding a row cap.

### OK

- Everything else on the dashboard is exemplary: summary tiles are
  `get_permission_aware_count/sum` SQL aggregates, lists are capped via
  `coerce_limit(default 8, max 30)` ✅; follow-up lookups are IN-bounded by
  those capped lists. Guest fundraising/membership endpoints are
  single-record + rate-limited. `erp_linking.py:451` even caps an internal
  sweep at 1000 explicitly ✅.

---

## good_demo — fine

All unbounded fetches live in the reset/seed/retention machinery, scoped to
demo-marked records and run by daily/weekly schedulers or the `long` queue.
Guest signup endpoints are single-record + rate-limited. No request-path
concern.

## ilanga_app — fine (cleanest app)

`get_home_dashboard` is fully bounded (`coerce_limit` max 30 + SQL
aggregates); **no `limit_page_length=0` anywhere in the app**. Public donate
pages reuse non_profit's Active-campaign dropdown (Low, curated). Builder-page
generation is setup-path, route-filtered. (PoC app — out of remediation scope
anyway.)

---

## Cross-cutting picture

### 1. Desk list views are a non-issue — everywhere

No custom app overrides Frappe's list pagination. Every "too many rows"
scenario in Desk (events, bookings, donations, declarations, members…) is
handled by the framework: 100 rows/page + Load More. Custom
`listview_settings` across the bench only add indicators and bulk actions on
checked rows. **The user-visible risk lives in public/portal pages, custom
APIs, and custom dashboards — not in Desk lists.**

### 2. The three genuinely High surfaces (guest/portal + unbounded + growing)

| Surface | Why it's the top tier |
|---|---|
| good_event public catalogue `/lists/*` + `embed_api.fragment` | Guest, uncached (`no_cache=1`), un-rate-limited; 2 full event scans + N translation queries + per-attendee rows per view; fetched set grows with event *history* (completed filtered in Python) |
| good_connector `GetNewsList` | Portal, unbounded Good News + per-row User lookup; every portal app-launch pays it |
| barakah `get_portal_file_targets` | Portal, all non-cancelled orders per supplier forever + system-wide open-task fallback with per-row access checks |

### 3. Recurring anti-patterns (the Medium tier, ~20 findings)

1. **Fetch-all-then-slice/len in Python** where SQL should aggregate or
   limit: good_npo monthly chart, non_profit campaign chart + expiring
   memberships, good_analytics per-donor endpoints (5), mopi dashboard
   counts + expiring quals, miki org-search provider, newsletter
   unsubscribe-count (guest-reachable), good_connector process/file lists
   (payload capped at 100, work unbounded).
2. **Synchronous unbounded fan-out in one HTTP request** (timeout class, not
   strictly pagination): miki `start_campaign` (inserts + workflow + email
   per member, thousands), miki `populate_members`, miki manual
   `run_daily_escalation`, non_profit `generate_yearly_receipts`, mopi
   `run_task_campaign`, newsletter `cancel_campaign` +
   `refresh_campaign_stats` queue sync, newsletter `import_from_source`
   count-probe.
3. **Post-fetch filtering** that defeats the SQL filter: good_event completed
   events (Python drop after full fetch), barakah task fallback
   (email-scoping after materialization), non_profit expiring-membership
   month window.

### 4. The house patterns to standardize on (already in the codebase)

- `good_connector.portal_helpers.coerce_limit(value, default, maximum)` —
  the clamp used by every good dashboard (barakah, ilanga, good_npo, mopi,
  miki panels). **Ironically dead code inside good_connector's own API** —
  GetNewsList/GetLinkList/GetProcessList/GetFileList don't use it.
- `get_permission_aware_count` / `get_permission_aware_sum` — SQL aggregates
  for tiles instead of `len(get_all(...))`.
- `barakah services.PORTAL_TASK_LIST_LIMIT = 500` + pre-scoped visibility —
  the bounded portal list.
- good_event `_planned_events_for_master` — `start_date >= today()` domain
  bound at SQL level; exactly what the event catalogue itself should do.
- good_newsletter dispatch — enqueue + `BATCH_SIZE=500` + per-batch commit +
  cancel check; good_analytics `rebuild_rfm_scores_now` — enqueue-only
  request path; mopi `enqueue_generate_and_send_certificates`.
- good_analytics dashboard filters — IN-subqueries instead of materialized
  donor lists; `get_rfm` — COUNT+GROUP BY.

### 5. Proposed remediation order (for discussion — nothing changed yet)

1. **good_event catalogue + embed** (High, the trigger question): bound
   `_get_events` in SQL (e.g. `end_date >= today − small grace window`, the
   status filter Python already enforces), share one fetch between grid and
   facets, make `_booking_count_map` a COUNT…GROUP BY, add
   `loading="lazy"` to card images, and put `methods=["GET"]` + a rate limit
   on `embed_api.fragment`. Optional second step: real `?page=` pagination
   for the "all events" browsing case.
2. **good_connector portal lists** (High/Medium): adopt `coerce_limit` +
   default caps in GetNewsList/GetLinkList; push the 100-cap into SQL for
   GetProcessList/GetFileList; batch the news author lookup.
3. **barakah file targets** (High): bound order targets (open/recent, LIMIT)
   and scope the task fallback by email in SQL before materializing.
4. **miki campaign fan-out** (Medium but worst timeout risk): enqueue
   `start_campaign` / `populate_members` / manual escalation with batching +
   progress, mirroring the newsletter dispatch pattern.
5. **SQL-aggregate conversions** (Medium, mechanical): the chart/count/report
   endpoints listed in §3.1.
6. **Defensive caps** on portal/tenant lists (miki declarations/file
   targets), `customer_export` default limit, newsletter COUNT() fixes.

Items 1–3 change guest/portal behavior at the margins (very long lists get
bounded); everything else is invisible to users except faster.
