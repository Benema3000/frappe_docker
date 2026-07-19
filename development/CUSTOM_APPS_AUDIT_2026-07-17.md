# Custom Frappe Apps Audit - 2026-07-17

Read-only security and bloat audit of the custom repositories in this bench.
This is a delta audit on top of `CUSTOM_APPS_AUDIT_2026-07-14.md` and its
10-wave remediation (completed 2026-07-15, tracked in
`AUDIT_REMEDIATION_WORKLIST_2026-07-14.md`). It (1) verifies every prior
finding against current HEAD, and (2) audits all post-remediation commits
plus anything the previous audit missed.

No application source files were changed by the audit itself. A same-day
remediation of N1, N2, NB1, NB3, and NB5 was requested and executed
separately on 2026-07-17 — see the Remediation Log at the end of this
report.

## Scope

Included (14 bench apps + 1 standalone repo):

- `good_connector`, `good_help`, `mopi_app`, `barakah_app`, `non_profit`,
  `good_npo`, `good_demo`, `miki_app`, `ilanga_app`, `workflow_visualizer`,
  `good_event`, `payrexx_integration`, `good_newsletter`, `good_analytics`
  under `/workspace/development/frappe-bench/apps/`
- `good-event-embed` at `/workspace/development/good-event-embed`
  (standalone PHP/JS SEO embed library; first audit)

Excluded: upstream/off-limits apps (`frappe`, `erpnext`, `payments`,
`builder`, `buzz`, `Commit`).

Paths are relative to `/workspace/development/frappe-bench` unless stated
otherwise.

## Method

One read-only audit agent per repository. Each agent:

1. Reviewed every commit since 2026-07-15 (`git log -p`) and its surrounding
   current code for new security issues.
2. Spot-checked each prior finding for the app at HEAD.
3. Swept for bloat/efficiency problems in new code first, then legacy code
   the prior audit missed.

Constraints honored: no file changes, no migrations, no `bench run-tests`
(shared-site deadlock rule). All evidence is static, traced through callers,
hooks, and permission configuration; no pattern-only claims. Documented
intentional decisions (compatibility facades, telemetry holds, per-recipient
Email Queue, native `apply_workflow`) were not re-reported.

## Executive Summary

**All prior findings verified still fixed.** No regressions were found in any
of the C/H/M/L/B register items across all 14 bench apps. The remediation
program held.

**New security findings: 0 Critical, 0 High, 2 Medium, 12 Low.**

The two Medium findings:

1. **MoPi certificate PDFs render manager-editable signature text unescaped**
   (HTML/CSS injection into official credential PDFs, auto-generated without
   review).
2. **MiKi case permissions unintentionally row-scope System Manager** on
   Issue and Sales Invoice, denying legitimate access for the primary admin
   persona (availability/integrity-of-access issue, not escalation).

The Low findings cluster around: published-state gates not enforced on
single-record reads, guest-triggered side effects with bounded blast radius,
cache-key completeness, and fail-open fallback paths in demo/seeding code.

**New bloat findings: 1 P1, 4 P2, ~25 P3.** The P1 is in `good-event-embed`
(no negative caching — a slug-scanning bot can exhaust the shared upstream
rate-limit budget). The P2s: `good_help` sync re-enabling operator-disabled
mappings every migrate, `mopi_app` dashboard count-by-fetch, `ilanga_app`'s
14.5 MB of orphaned tracked images, and `good-event-embed` never forwarding
catalogue query parameters.

**Remediation status (2026-07-17, same day):** N1, N2, NB1, NB3, and NB5 are
fixed and verified — mopi_app full suite 114 tests green, miki_app full
suite 332 tests green. good-event-embed's fixes include a dependency-free
test harness that could not be executed on this machine (no PHP runtime);
run `php tests/run.php` before shipping that repo. All other findings
remain open. Details in the Remediation Log below.

## Severity Definitions

| Severity | Meaning                                                                                     |
| -------- | ------------------------------------------------------------------------------------------- |
| Critical | Direct privilege escalation, fake settlement, or material accounting failure                |
| High     | Significant authorization, financial-integrity, data-exposure, or production-data-loss risk |
| Medium   | Constrained exploit, latent authorization issue, or operational reliability problem         |
| Low      | Bounded issue with preconditions that limit real-world impact                               |
| P1 bloat | Measured hot-path cost or major maintenance risk                                            |
| P2 bloat | Significant recurring duplication, N+1 behavior, or shipped dead weight                     |
| P3 bloat | Cleanup candidate, cohesion improvement, or minor recurring cost                            |

---

## Prior-Finding Verification

All register items from the 2026-07-14 audit verified at HEAD on 2026-07-17.

| App                   | Result                                                                                                                                                                 |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `good_connector`      | H3, H5, M1, M2, B01, B02, B04, B05, B07 all still fixed. B40 shim held for telemetry as documented.                                                                    |
| `good_help`           | M4 three-layer guard intact (route guard + has_permission + API gate); B09 single global pass intact.                                                                  |
| `mopi_app`            | H3, H4, H5, B02, B03, B05, B07, B08 all still fixed with regression tests in place.                                                                                    |
| `barakah_app`         | M2 (savepoint + 409), B02, B05, B06/S08, B08 all still fixed. 2026-07-11 items re-verified clean.                                                                      |
| `non_profit`          | H1, H2, B19, B22, B23, B24 all still fixed; B28 legacy wrappers intact as documented telemetry hold.                                                                   |
| `good_npo`            | C2, H6, B19, B20, B21, B22, B25, B27 all still fixed; B39 opt-out telemetry hold intact.                                                                               |
| `good_demo`           | C2 dual-flag gate, H6 trusted-context marking, H7 containment, B20, B22, B26 all still fixed.                                                                          |
| `miki_app`            | H8, H9, B20, B29-B31, B33, B34, B36, B37 all still fixed; B40 candidates held as documented; S01-S05 deferred per worklist. Prior Administrator-only test gaps closed. |
| `workflow_visualizer` | B32, B35, B38, S09 still fixed; pre-audit no-oracle 403 hardening holds; O03 native boundary preserved.                                                                |
| `good_event`          | C1, H11, L1, B10, B12, B16, B17, B18 all still fixed; S06/S07 improved. B13 remains a documented user decision.                                                        |
| `payrexx_integration` | C3, H12, H13, H14, B21 all still fixed with end-to-end tests.                                                                                                          |
| `good_newsletter`     | C1, H10, M3 (strengthened), B11, B14 all still fixed. O01 remains an operational hold (dev site SNS ARN).                                                              |
| `good_analytics`      | H7, B15 still fixed; restricted-user RPC tests in place.                                                                                                               |
| `ilanga_app`          | No prior findings (excluded from 2026-07-14 audit); B20/B39 items touching it verified resolved on the `good_npo` side.                                                |

### Deliberate drift worth recording

- `good_event` `e1b2a2e`: unstamped legacy Email Templates are now preserved
  as customer-owned instead of adopted-and-overwritten (Wave 10 behavior).
  Safer default, but unstamped sites no longer receive shipped template
  corrections automatically; `reset_email_template_to_default` is the
  documented opt-in (`good_event/services/email_templates.py:1065-1075,1113-1138`),
  test-pinned.

---

## New Security Findings

### Medium

#### N1. MoPi certificate PDFs render signature text unescaped — **FIXED 2026-07-17** (see Remediation Log)

`apps/mopi_app/mopi_app/templates/print_formats/training_certificate_mopi.html:316,325`
renders `module.signature_1_text` / `module.signature_2_text` without `| e`
(every other output in the template is escaped).

- Preconditions: any authenticated `MoPi User` — setup grants that role
  create/read/write on `MoPi Training Module`
  (`apps/mopi_app/mopi_app/setup.py:223`), and the signature Small Text
  fields carry no permlevel or read-only guard.
- Impact: arbitrary HTML/CSS injection into the official credential PDF,
  which is auto-generated with no human review on self-study completion
  (`apps/mopi_app/mopi_app/training.py:1319`). wkhtmltopdf runs with
  `--disable-local-file-access` but without `--disable-javascript`
  (`training.py:1085-1108`). This undercuts the H3/H4 issuer model:
  non-issuers can alter issued-certificate content.
- Predates the 2026-07-14 audit; missed by it.
- Remediation: add `| e` to both outputs, consider `--disable-javascript`,
  add a template-escaping test.

#### N2. MiKi permissions row-scope System Manager unintentionally — **FIXED 2026-07-17** (see Remediation Log)

`apps/miki_app/miki_app/permission.py:8-12` includes `"System Manager"` in
`MIKI_CASE_RESTRICTED_ROLES`, but the independent-role exemptions only cover
`Support Team` (Issue) and `Accounts Manager`/`Accounts User` (Sales
Invoice) (`permission.py:13-16,113-124`). Frappe `has_permission` hooks can
only deny, so:

- An Admin-profile user (System Manager + Accounts Manager, no Support Team
  — the shipped profile at `setup_permissions.py:387-398`) is denied read on
  non-case Issues (`permission.py:51-54,72-79`).
- A bare System Manager loses list/read access to all non-MiKi Sales
  Invoices, e.g. Good Event invoices (`permission.py:63-69,90-98`).

This contradicts the documented intent that "access granted only by MiKi
roles is row-scoped". Availability issue for the primary admin persona, not
an escalation. Remediation: drop `"System Manager"` from
`MIKI_CASE_RESTRICTED_ROLES` or extend the bypass; add a test asserting a
System Manager-only user reads a non-case Issue.

### Low

#### N3. Portal `GetData` bypasses the `enabled=1` gate for Good Link/Good News — **FIXED 2026-07-18** (see Remediation Log)

`_action_get_data` returns any record by ID
(`apps/good_connector/good_connector/api/portal.py:1015-1024`) while the
list endpoints filter `enabled: 1` (`api/user.py:141,162`). IDs are
enumerable series (`NEWS-{#####}`, `LINK-{#####}`), so any portal JWT holder
can read disabled/unpublished content including `owner`/`modified_by` via
`doc.as_dict()`. Pre-existing; missed by the prior audit. Remediation:
reject `enabled != 1` for these two process names in `_action_get_data`.

#### N4. Good Help API leaks staff editor email — **FIXED 2026-07-18** (see Remediation Log)

`_build_article_payload` returns `modified_by` (a staff email) and
`modified` (`apps/good_help/good_help/api.py:185-186`) to any authenticated
session, including Website Users without Desk access. Neither JS consumer
reads these fields — dead payload as well. Remediation: drop both fields.

#### N5. MoPi unattended self-certification chain (hardening note) — **ACCEPTED, no action** (user decision 2026-07-18: not a bug)

An ordinary `MoPi User` can add themselves to `participants` (module write
perm), trigger self-study task creation, complete their own task, and the
Task hook auto-issues the certificate. Largely the documented worklist
decision (MoPi Users retain module editing); reported as hardening only:
consider restricting participant management on self-study modules to
`MoPi Manager`.

#### N6. Good Demo Address/Contact creation not fail-closed when demo mode is off — **FIXED 2026-07-18** (see Remediation Log)

`apps/good_demo/good_demo/address_contact.py:24-97` gates only on demo
identity, never on `is_good_demo_mode()`; `_mark_demo_record` (`:139-143`)
stamps `good_demo_seed=1` directly. With mode switched off, a stale enabled
demo user can create marked records the reset never claims — violates the
app's documented fail-closed rule. Remediation: `require_good_demo_mode()`
at the top of both endpoints.

#### N7. Good Demo seed falls back to an arbitrary existing Company — **FIXED 2026-07-18** (see Remediation Log)

`apps/good_demo/good_demo/seeding.py:321-325`: if creating the `GoodNPO`
company fails, the seed proceeds against the first Company in the DB and
`_ensure_accounting_defaults` overwrites that real company's defaults
(`:504-536`, non-resettable). Preconditions: demo mode on + company-creation
failure on a mixed site. Remediation: `frappe.throw` instead of falling back.

#### N8. Good Demo reset reports attempted deletions as `deleted_records` — **FIXED 2026-07-18** (see Remediation Log)

`apps/good_demo/good_demo/reset.py:156-158` increments the counter
unconditionally around `_delete_doc_if_possible` (`:335-346`), which
swallows/logs failures. Cosmetic reporting inaccuracy against the app's own
contract; rename or count confirmed deletions only.

#### N9. Workflow Visualizer failure dialog renders server messages as HTML — **FIXED 2026-07-18 by escaping** (see Remediation Log)

`workflow_visualizer.js:525-567` joins `_server_messages`/`message` branches
raw into `frappe.msgprint` (the `exception`/`exc` branches added post-remediation
are correctly escaped). Important caveat: this is exact framework parity —
Frappe core renders `_server_messages` through `msgprint` unescaped, and the
standard Workflow Actions path renders the same payload for the same failed
call. Recommendation: accept parity explicitly in `DOCUMENTATION.md`, or
escape (which breaks Frappe's legitimate HTML-link messages). Parity is the
defensible default.

#### N10. Good Event embed-fragment cache key omits request Host — **FIXED 2026-07-18** (see Remediation Log)

Cache key is `kind|slug|modified|query` (`apps/good_event/good_event/embed_api.py:99-124`),
but cached payloads embed absolute URLs resolved via `frappe.utils.get_url()`,
which honors the request Host header when `host_name` is unset. A spoofed
Host poisons the shared fragment cache for up to 60s (canonical/OG/JSON-LD
and card hrefs). Native pages unaffected. Remediation: mix the resolved base
URL into the cache key, or require `seo_public_base_url` before caching.

#### N11. Guest-triggered force delete of draft Payment Requests — **FIXED 2026-07-18** (see Remediation Log)

`apps/payrexx_integration/payrexx_integration/api.py:272-284`
(`_delete_wrong_draft_payment_requests`, called from `api.py:202`): a guest
holding a valid per-invoice HMAC pay link triggers
`frappe.delete_doc(..., ignore_permissions=True, force=True)` on every draft
Payment Request for that invoice whose gateway differs from the resolved
one — including drafts staff created deliberately. Bounded (drafts only,
same invoice, signed link required); predates the prior audit (introduced
`ee3d6a0`, 2026-05-03). Remediation: narrow the filter to flow-owned drafts
or log deletions.

#### N12. Good Newsletter guest confirm link resurrects suppressed subscribers — **FIXED 2026-07-18** (see Remediation Log)

The form path refuses to restart opt-in for Bounced/Complained addresses
(`services/opt_in.py:28-31`), but the confirm-link path has no status guard:
`subscriber.confirm()` flips any non-Confirmed status back to Confirmed
(`api/public.py:120` → `services/opt_in.py:101-117` →
`good_newsletter_subscriber.py:34-47`). An unauthenticated click on a
still-valid token (default 7-day TTL) breaks the suppression invariant.
Actual sending stays blocked by the global-unsubscribe filter
(`services/audience.py:71-74`), hence Low. Remediation: refuse confirmation
for `status in ("Bounced", "Complained")`, mirroring the form gate; add a
regression test.

#### N13-N15. good-event-embed (first audit, standalone repo) — **FIXED 2026-07-18** (see Remediation Log)

- **N13 [Low] WordPress adapter injects upstream title unescaped into
  `<title>`** — `good-event-embed/adapters/wordpress/good-event-embed.php:96-102`;
  WP core echoes `wp_get_document_title()` unescaped while the core library
  escapes the same value in `renderHead` (`src/GoodEventEmbed.php:113-114`).
  Staff-authored event title containing `</title><script>…` → stored XSS on
  host pages. Fix: `esc_html()` in `filterTitle`.
- **N14 [Low] Transport not hardened** — constructor accepts any `baseUrl`
  scheme silently; `httpGet` follows redirects with no max-redirects, no
  protocol allowlist, no size cap (`src/GoodEventEmbed.php:55-65,233-259`).
  The library renders upstream `html` verbatim by design, so transport
  integrity is host-page integrity: an `http://` base URL or http redirect
  lets a MITM inject arbitrary HTML/JS. Fix: enforce/warn on https,
  `CURLOPT_MAXREDIRS`, `CURLOPT_REDIR_PROTOCOLS => CURLPROTO_HTTPS`, size cap.
- **N15 [Low] Default cache dir poisonable on shared hosts** — default
  `cacheDir` is `sys_get_temp_dir() . '/good_event_embed'` created `0775`
  only when absent (`src/GoodEventEmbed.php:60-62,303-306`). A local user
  can pre-create the path in sticky `/tmp` and own it; poisoned cache JSON
  is echoed verbatim into pages. Fix: `mkdir(..., 0700)` and/or verify
  ownership before trusting cached content.

### Areas explicitly traced clean

- `barakah_app`, `non_profit`, `good_npo`, `ilanga_app`, `good_analytics`:
  no new security findings. Post-remediation commits are refactors, docs,
  version bumps, or strictly tightening changes (e.g. good_analytics'
  static-mailing enforcement replaced an unpermissioned `get_value` with
  `get_doc` + `check_permission`).
- `good_event` beyond N10: staff endpoints keep role + doc-permission gates,
  guest mutations keep POST/rate-limit/captcha/published-event checks, and
  the uncommitted deadlock fix set (Address row locking,
  `RetryBackgroundJobError` conversion) is sound.
- `miki_app` beyond N2: guest endpoints keep token/captcha auth, case
  lifecycle blocks mass-assignment of control fields, invoice link/unlink
  uses role gates + row locks in documented order.
- `payrexx_integration` beyond N11: HMAC/signature verified before side
  effects, webhook key bound to IR-owning settings row, redirects pass
  `safe_return_url`, secrets stay out of logs.
- `good_newsletter` beyond N12: signup-widget rework builds DOM via
  `textContent` only; www template escapes params; rate limit falls back to
  per-IP bucket.
- `ilanga_app`: no whitelist endpoints, no SQL, no rendering, no outbound
  HTTP, no file/auth/payment code; Builder seed JSON has zero client scripts;
  patches are exists-guarded and safe.

---

## New Bloat and Efficiency Findings

### P1

#### NB1. good-event-embed: no negative caching — every miss is a live blocking upstream call — **FIXED 2026-07-17** (see Remediation Log)

Only `ok` payloads are cached (`good-event-embed/src/GoodEventEmbed.php:91-93`).
Each unknown slug or upstream outage re-executes a synchronous HTTP fetch
(up to 8s timeout) on every host page render. The upstream guest endpoint is
rate-limited per IP and the host presents as a single IP, so a bot scanning
random slugs can exhaust the shared budget and degrade legitimate pages.
On TYPO3 the miss output is produced inside a cached `USER`, freezing a
transient failure into the page cache. Remediation: cache `ok:false`
payloads for a short TTL (30-60s).

### P2

#### NB2. good_help sync re-enables operator-disabled mappings every migrate — **FIXED 2026-07-18** (see Remediation Log)

`_upsert_mapping` includes `"is_enabled": 1` in its comparison payload and
`set_value`s it back when an operator cleared it
(`apps/good_help/good_help/sync.py:305,309-311`) — contradicting the
ownership-preservation contract the same module adopted in `1550a9e`
(customer `is_published`/body are preserved). Causes a rewrite per disabled
mapping per migrate and silently reverts operator intent. Pre-existing since
the initial commit. Fix: drop `is_enabled` from the update payload (keep on
insert).

#### NB3. MoPi dashboard counts materialize rows instead of COUNT queries — **FIXED 2026-07-17** (see Remediation Log)

`_count_participants_for_modules` plucks all participant names to `len()`
them (`apps/mopi_app/mopi_app/dashboard.py:176-186`);
`_count_certificates_ready_to_send` loads all eligible rows then counts in
Python (`:189-211`). Both run on every `get_home_dashboard` call and grow
with total participants — the count-by-fetch pattern Wave 9 removed
elsewhere. Fix: `frappe.db.count` / grouped COUNT.

#### NB4. ilanga_app: 106 orphaned tracked images, ~14.5 MB

`apps/ilanga_app/ilanga_app/public/images/ilanga/` tracks 187 media files
(~50 MB working tree, ~35 MB `.git`); only 80 paths are referenced by
`builder_seed/pages.json`. The 106 unreferenced files are leftovers from the
deleted `ilanga_website` generator era and ship with every `get-app` and
asset build. Remediation: delete the unreferenced files (list reproducible
from the seed's asset references) or move media to site files.

#### NB5. good-event-embed: catalogue query parameters never forwarded — **FIXED 2026-07-17** (see Remediation Log)

Upstream accepts `page`, `q`, `from`, `to`, `region`, `regions`,
`audience_segments`, `categories`, `category`, `catalog_stream`
(`apps/good_event/good_event/embed_api.py:27-38,94-96`); the client sends
only `kind/slug/lang` and its cache key has no slot for the rest
(`good-event-embed/src/GoodEventEmbed.php:84-88,276-279`). Embedded
list/master_list pages are frozen to page 1, unfiltered. Remediation:
whitelist-forward the documented params and include them in the cache key.

### P3 (grouped by app)

**good_connector**

- Per-save duplicate scan rebuilds the full identity universe for one record
  (`identity_matching.py:228` → `_build_identity_index` with `limit=0`);
  mitigated by job dedup and the daily shared index — residual linear cost.
- QR resolution pipeline duplicated with drifted failure semantics:
  `build_qr_bill_object` vs `build_svg_for_sales_invoice` disagree on debtor
  failure handling (`qr_bill.py:353-420` vs `:288-350`).
- `email_utils` depends on upstream-private `_make` (`email_utils.py:10`) —
  compatible with pinned Frappe v16 today, but an upstream rename breaks
  miki/good_event correspondence at import time. Minor: omitted `sender`
  records the session user on the Communication while sending via the
  default outgoing account.

**good_help**

- `_is_good_demo_user()` re-queried 2-3x per API call
  (`api.py:47,58,92,169,171`) — memoize per request.

**mopi_app**

- Unbounded module-name load feeding dashboard counts (`dashboard.py:76-80`).
- Qualification expiry scan runs 4 unbounded lists + 4 counts per dashboard
  load (`user_profile.py:63-103,106-128`) — collapsible into one OR-grouped
  query each.
- N+1 in admin batch paths: per-recipient task lookup in `run_task_campaign`
  (`actions.py:188-197`), per-user re-lookup in
  `create_and_send_self_study_tasks_for_module` (`training.py:604-617`).

**barakah_app**

- Desk-side `_assigned_task_condition` (`permission.py:76-86`) duplicates the
  now-shared `good_connector.portal_helpers.assigned_task_sql_condition` —
  residual B02 drift.
- Per-save write churn: every order `on_update` unconditionally rewrites
  open-task targets and closes/recreates all ToDo assignments even when
  unchanged (`task_targets.py:107-112`, `task_delivery.py:140-150`) — ~8-12
  queries + several writes per open task per save. Pre-existing.
- Dead branch: `_barakah_task_rows(email=None)` fallback unreachable from
  production callers (`portal_tasks.py:64-71,153-154`).

**non_profit**

- `before_uninstall` re-implements the canonical
  `good_connector.install_utils.clear_workspace_sidebar_app`
  (`setup.py:85-94`) — the lone duplicator among 12 sidebar-shipping apps.

**good_npo**

- Dead tour-navigation JS (~25 lines): `data-tour-next/back` handlers and
  `nextTourStep`/`previousTourStep` unreachable since the intro became
  single-step (`good_npo_home.js:262-263,912-914,976-988`).
- Uncached provider invocation per boot/tile render (`boot.py:29-30`,
  `permission.py:22-27`); good_demo's decorator provider does a DB lookup
  per call — cheap insurance to memoize per request.

**good_demo**

- Decorator provider queries DB per invocation, called ~8x per thank-you
  render (`npo_demo.py:261-266` via `good_npo/demo.py:34-39`).
- `_repair_demo_users` N+1 on a public path (`setup.py:329-378`) — one full
  `get_doc` per demo user per `confirm_demo_access`.
- Unreferenced binary assets: `public/videos/` 8.1 MB (frontend video
  disabled) + `video_storyboards/` 6.0 MB planning material at repo root.
- Dead imports in `membership.py:3-7`.

**miki_app**

- Per-row full document loads in case-invoice typeahead (`cases.py:770-782`)
  — worst case 1000 `get_doc` per keystroke (bounded by
  `MAX_CASE_INVOICE_CANDIDATE_SCAN`); `get_lazy_doc` suffices.
- Count-by-fetch in `_quota_used` (`cases.py:366`) — use the existing
  `get_permission_aware_count` helper.

**ilanga_app**

- Sidebar deleted and re-inserted unconditionally on every migrate
  (`setup.py:50-66`) — resets operator customization; add a change check.
  Note: `frappe.cache.delete_key("bootinfo")` does not clear the in-process
  `@site_cache` sidebar cache (documented bench gotcha; HOW_TO correctly
  prescribes `bench clear-cache`).
- Stale ignored build residue in the working tree (`__pycache__` dirs from
  the deleted packages) — local cleanup only.

**workflow_visualizer**

- No findings. Dismissed: per-transition `frappe.get_roles()` is
  request-cached and negligible.

**good_event**

- `event_lists.py` grew to 1557 lines — cohesion watch item only; split
  highlights/hero rendering when the area next changes.
- Fragment cache-key preflight costs 1-3 indexed reads on every request
  including hits (`embed_api.py:127-136`) — acceptable trade for correct
  invalidation.

**payrexx_integration**

- Dead stub `PayrexxClient.delete_gateway` raises `NotImplementedError`, no
  callers (`payrexx_client.py:59-62`).

**good_newsletter**

- Managed Email Templates have two canonical content forms: insert stamps
  the hash of sanitized content while `_managed_overwrite` writes raw
  strings and stamps their hash (`services/email_templates.py:147-157,206-217`).
  Consequences: the `2f9b46a` patch's `rel="noopener"` fix is reverted by
  the same migrate's `after_migrate`; a no-op Desk save flips a managed row
  to "customer-owned" (shipped updates stop applying); 8 value-identical
  UPDATEs per migrate. Normalize to one form and skip unchanged writes.
- `_bump_campaign_unsubscribed_count` fetches all matching Recipient names
  to count in Python (`services/suppression.py:160-172`) — use `Count()`.
- Large imports ship the full provider member list as RQ job kwargs
  (`api/audience.py:62-74`) — accepted trade-off of the B11 fix; consider a
  persisted snapshot reference if providers grow into the tens of thousands.

**good_analytics**

- `get_campaign_performance` 500s on a force-deleted target segment
  (`analytics/api.py:576` direct dict index) — `segment_names.get(...)`
  one-liner.

**good-event-embed**

- Cache stampede risk (no lock/stale-while-revalidate at TTL expiry) and no
  pruning of expired files (`src/GoodEventEmbed.php:78-95`) — tmp dir grows
  with slug x language count.
- WordPress stash reuse matches `kind` only — a second same-kind shortcode
  with a different slug/language re-renders the first shortcode's body
  (`adapters/wordpress/good-event-embed.php:119-121`).

---

## Cross-Cutting and Documentation Drift

- **Versioning policy:** most apps comply (good_npo 16.0.1, miki_app 16.0.3,
  good_newsletter 16.0.1, good_event 16.1.1 all bumped with behavior).
  Exceptions to decide deliberately at next release: `good_connector` stayed
  16.0.2 across a `chqr` dependency-floor raise (`388f2bf`) and a
  behavior-changing suppression feature + new `doctype_js` fixture
  (`7206e52`); `barakah_app` stayed 16.0.2 across three refactor/perf
  commits plus the Wave 8 409-behavior change.
- **Bench AGENTS.md stale:** `non_profit`'s active branch is now
  `version-16` (miki-dev merged, app version 16.0.0); the bench-root
  AGENTS.md still says "Dev branch in use: `miki-dev`".
- **good_demo homepage takeover:** `hooks.py:19-21` redirects `/` → `/demo`
  and setup forces `Website Settings.home_page = "demo"` on every
  install/migrate regardless of demo mode — intended for dedicated demo
  sites, but installing on a live site repurposes its homepage even with
  mode off. Worth an explicit operator note.
- **good_event uncommitted work:** the working tree contains uncommitted
  deadlock fixes (Address `for_update` lock, scheduler
  `RetryBackgroundJobError`), the `frappe.lang` ticket print-format fixture
  with fr/it tests, and version 16.1.1. Audited as-is; all compile-checked.
  Commit deliberately (dev-mode auto-export hygiene for the fixture JSON).
- **ilanga Google Fonts:** all 19 public seed pages load Google Fonts in
  `head_html` — visitor IPs go to Google on each page view; worth a
  privacy-policy check for a Swiss NPO site.

## Test Gaps (new findings only)

- MoPi: no test pins HTML-escaping of signature/module fields in certificate
  HTML (would catch N1).
- MiKi: no test asserting a System Manager-only user reads a non-case Issue
  (N2).
- good_connector: no gc-local test for `send_referenced_email`'s
  discard-on-mute/unqueued path; no test pinning `validate()`'s admin
  requirement on direct non-admin save of `GC Potential Duplicate`.
- good_newsletter: no test for the confirm-link path on a suppressed
  subscriber (N12).
- payrexx: no test for `payment_success`/reconcile on legacy IRs lacking
  `payrexx_settings` in `data`, and no callback test for legacy IRs with
  empty `data`.
- workflow_visualizer: the Node client tests (including the new
  error-handling tests) are not wired into CI; `node --test` is manual only.
- ilanga_app: `ensure_presentation_sidebar()` and `before_uninstall()` have
  no tests; the two patches are registration-checked but never executed.
- good-event-embed: no tests, no CI, no PHP lint configuration at all.
- non_profit: no runtime verification of the new workspace sidebar in a
  browser (boot item count / icon glyphs) — static checks passed.

## Operational Holds Carried Forward

These remain open from the 2026-07-14 worklist and are unchanged by this
audit:

- Production route/import telemetry before removing B28/B39/B40
  compatibility surfaces.
- Historical Payrexx/Donation/accounting reconciliation (submitted ledger
  rows untouched by remediation).
- Donation `NPO-DTN-2026-00436` over-allocation (excess 246) still flagged
  for manual review.
- Development site has no `sns_topic_arn`; enter the real ARN before
  expecting verified SNS processing.
- Existing demo sites must explicitly set both `developer_mode` and
  `good_demo_mode`; 631 marked records preserved for review.

## Per-App Assessment

| App                   | Prior findings  | New security              | New bloat                    |
| --------------------- | --------------- | ------------------------- | ---------------------------- |
| `good_connector`      | All still fixed | 1 Low (N3)                | 3 P3                         |
| `good_help`           | All still fixed | 1 Low (N4)                | 1 P2 (NB2), 1 P3             |
| `mopi_app`            | All still fixed | 1 Medium (N1), 1 Low (N5) | 1 P2 (NB3), 3 P3             |
| `barakah_app`         | All still fixed | None                      | 3 P3                         |
| `non_profit`          | All still fixed | None                      | 1 P3                         |
| `good_npo`            | All still fixed | None                      | 2 P3                         |
| `good_demo`           | All still fixed | 3 Low (N6-N8)             | 4 P3                         |
| `miki_app`            | All still fixed | 1 Medium (N2)             | 2 P3                         |
| `ilanga_app`          | Fresh audit     | None                      | 1 P2 (NB4), 2 P3             |
| `workflow_visualizer` | All still fixed | 1 Low (N9, parity)        | None                         |
| `good_event`          | All still fixed | 1 Low (N10)               | 2 P3                         |
| `payrexx_integration` | All still fixed | 1 Low (N11)               | 1 P3                         |
| `good_newsletter`     | All still fixed | 1 Low (N12)               | 3 P3                         |
| `good_analytics`      | All still fixed | None                      | 1 P3                         |
| `good-event-embed`    | Fresh audit     | 3 Low (N13-N15)           | 1 P1 (NB1), 1 P2 (NB5), 2 P3 |

## Remediation Log (2026-07-17)

Implemented same-day per user instruction; everything not listed here was
deliberately left as-is. Committed and pushed 2026-07-17: `mopi_app`
`0ec9b9b`, `miki_app` `b9fe94b`, `good-event-embed` `12164f6` (all
`main`).

| Finding | Repo               | Fix                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Verification                                                                                                                                                                                                                                                   |
| ------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| N1      | `mopi_app`         | Escaped all 8 unescaped variable outputs in `templates/print_formats/training_certificate_mopi.html` (both signature texts plus 6 attribute/data outputs); added `--disable-javascript` to the wkhtmltopdf command (`training.py`). New regression test `test_training_certificate_print_format_escapes_signature_text` injects markup at DB level (Frappe's save-time `sanitize_html` already strips `<script>` on Desk/API saves, so the test pins the real residual threat: legacy/direct DB writes) and renders through the production `_build_training_certificate_html`. | Full suite green: 114 tests (106 + 7 + 1, one expected skip), incl. the new test; `--disable-javascript` pinned in the existing wkhtmltopdf mock.                                                                                                              |
| N2      | `miki_app`         | Removed `"System Manager"` from `MIKI_CASE_RESTRICTED_ROLES` and added an explicit System Manager early-exit in `_requires_miki_scope` (`permission.py`), exempting SM on all doctypes in any role combination — a constant-only fix would not have covered the shipped Admin profile (SM + Accounts Manager + MiKi roles). MiKi-role-only users remain row-scoped (existing test `test_miki_roles_only_see_case_issues_and_linked_case_invoices` still passes). AGENTS.md Cases section and DOCUMENTATION.md updated.                                                         | Full suite green: 332 tests (320 + 12), incl. new `test_system_manager_only_user_reads_non_case_issue` and `test_system_manager_only_user_reads_unlinked_sales_invoice`. (The first full run reported 1 transient error, not reproducible on the clean rerun.) |
| NB3     | `mopi_app`         | `_count_participants_for_modules` and `_count_certificates_ready_to_send` rewritten as single set-based query-builder COUNT queries; unbounded `visible_module_names` load removed; module count via `get_permission_aware_count`. Response payload unchanged. Semantics note: the participant counts enumerate all modules behind the doctype-read gate — revisit if row-level permission conditions are ever registered for MoPi Training Module.                                                                                                                            | New tests: fixture-delta count correctness + `assertQueryCount(2)` bound (`tests/test_dashboard.py`); green in the 114-test suite above.                                                                                                                       |
| NB1     | `good-event-embed` | `ok:false` payloads are now cached with a new optional `negativeCacheTtl` (default 60s); positive-cache behavior byte-identical.                                                                                                                                                                                                                                                                                                                                                                                                                                               | Tests written in `tests/run.php` but **not executed — no PHP runtime on this machine**; PHP syntax verified via a structural lexer check only. Run `php tests/run.php` (PHP 7.4+) before shipping.                                                             |
| NB5     | `good-event-embed` | The 10 upstream catalogue params (`page, q, from, to, region, regions, audience_segments, categories, category, catalog_stream`) are whitelist-forwarded from the host `$_GET` (scalar values only) and included in the cache key. Upstream confirmed to parse plural params as comma-separated scalars and to emit relative `?key=value` fragment links, so embedded pagination/filtering now reloads through the host. Added optional `httpTransport` constructor injection for the test harness. README.md and AGENTS.md updated.                                           | Same PHP caveat as NB1.                                                                                                                                                                                                                                        |

Version bumps: `mopi_app` 16.0.1 → 16.0.2 and `miki_app` 16.0.3 → 16.0.4
(all declarations in each repo kept in sync). `good-event-embed` declares no
version (WordPress adapter header stays 1.0.0).

## Remediation Log, Round 2 (2026-07-18)

Implemented per user instruction; N5 recorded as accepted (not a bug) and
NB4 deliberately deferred. Each fix shipped with regression tests and a
`REQUIREMENTS.md` update per the new documentation contract. Final UAT
follow-ups were audited, committed, and pushed on 2026-07-19: `good_event`
`37d3860`, `miki_app` `ed1d9dc`, and `non_profit` `1ad8e3a`.

| Finding | Repo                  | Fix                                                                                                                                                                                                                                                                           | Verification                                                                                                                                                  |
| ------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| N3      | `good_connector`      | `_action_get_data` enforces the `enabled=1` gate for Good Link/Good News with a uniform 403 that also covers nonexistent IDs (no existence oracle); all other portal fetch paths traced closed.                                                                               | Suite green: 168 tests (129+3+36), incl. 4 new contract tests.                                                                                                |
| N4      | `good_help`           | `modified`/`modified_by` dropped from the article payload (consumers re-grepped clean first).                                                                                                                                                                                 | Suite green: 72 tests, incl. new payload-shape test.                                                                                                          |
| NB2     | `good_help`           | `is_enabled` is now insert-only in `_upsert_mapping`; operator-disabled mappings survive sync.                                                                                                                                                                                | Same suite, incl. disabled-preserved and insert-enabled tests.                                                                                                |
| N6      | `good_demo`           | `require_good_demo_mode()` at the top of both Address/Contact endpoints (same error shape as checkout paths).                                                                                                                                                                 | Suite 85/86 green; the 1 failure is the hrms site issue below, not this fix.                                                                                  |
| N7      | `good_demo`           | Company-creation failure now `frappe.throw`s instead of falling back to an arbitrary existing Company.                                                                                                                                                                        | Same suite, incl. failure-aborts test.                                                                                                                        |
| N8      | `good_demo`           | `_delete_doc_if_possible` returns success and only confirmed deletions count toward `deleted_records`; result shape unchanged (no new keys).                                                                                                                                  | Same suite, incl. 2 counting-contract tests.                                                                                                                  |
| N9      | `workflow_visualizer` | All failure-dialog message parts (server messages, messages, message, exception branches) are HTML-escaped at one choke point before the `<br>` join; documented deliberate deviation from core `msgprint` parity.                                                            | Node suite 11/11 green; Python suite 24 green.                                                                                                                |
| N10     | `good_event`          | Resolved `seo.public_base_url()` mixed into the embed-fragment cache key; pinned-config sites keep one stable key (hit rate unaffected).                                                                                                                                      | Unit category 23/23 green, incl. 3 new cache tests.                                                                                                           |
| N11     | `payrexx_integration` | Draft-PR cleanup now ownership-scoped: only `Payrexx-%` gateway drafts owned by the flow's automation user are deleted, each deletion warning-logged. Staff/other-gateway drafts survive.                                                                                     | Suite green: 49 tests, incl. 2 mocked unit tests (zero DB writes — immune to site series state).                                                              |
| N12     | `good_newsletter`     | `SUPPRESSED_STATUSES = ("Bounced", "Complained")` guard on the confirm link; refused confirmations render like invalid/expired tokens (410). Unsubscribed consciously still resubscribes via the mailbox-delivered token (fresh consent); already-Confirmed stays idempotent. | Suite green: 146 tests (8+138), incl. 4 new opt-in tests.                                                                                                     |
| N13     | `good-event-embed`    | `esc_html()` on the WordPress `filterTitle` value.                                                                                                                                                                                                                            | `tests/run.php` extended to 31 checks — **not executed (no PHP runtime on this machine)**; syntax lexer-verified only. Run on a PHP 7.4+ host before release. |
| N14     | `good-event-embed`    | https-only `baseUrl` by default (`allowInsecureHttp` opt-in for dev), max 3 redirects, https protocol allowlist on every hop, 2 MB response cap — enforced identically in the curl and fopen transports.                                                                      | Same PHP caveat.                                                                                                                                              |
| N15     | `good-event-embed`    | Cache dir created `0700`; pre-existing dirs trusted only with matching owner and no group/other perms, otherwise the cache is bypassed entirely (live fetch, no writes).                                                                                                      | Same PHP caveat.                                                                                                                                              |

Final released versions after the UAT follow-ups: `good_connector`
16.0.5, `good_help` 16.0.2, `good_demo` 16.0.3, `workflow_visualizer`
16.0.1, `good_event` 16.2.1, `miki_app` 16.2.1, `non_profit` 16.1.2,
`payrexx_integration` 16.0.1, and `good_newsletter` 16.0.3.
`good-event-embed` declares no package version.

### Environmental blockers discovered during round-2 verification

**1. hrms shadowing of non_profit's Payment Entry override — RESOLVED
2026-07-18 (user decision: hook-based design).** `hrms` (16.13.0) was
installed on `development16.localhost` after `non_profit`, so hrms's
`EmployeePaymentEntry` won the duplicate `override_doctype_class`
resolution (last app wins) and `NonProfitPaymentEntry` was inert —
breaking every Donation-referenced Payment Entry and disabling the H1/H2
safeguards. Resolution: non_profit's Payment Entry delta moved from the
class override to `doc_events` hooks (`before_validate`, `validate`,
`on_submit`, `on_cancel`, `on_change` — fire regardless of the winning
controller), and Donation now
carries maintained read-only `grand_total` (= `amount`) and `advance_paid`
(= submitted allocation) fields mirroring Sales Invoice semantics, so
erpnext's generic `get_reference_details` computes the correct outstanding
under ANY controller class (`set_missing_ref_details(force=True)` can no
longer zero it). A versioned backfill patch populated both fields for
existing Donations. The Payment Entry key was removed from
`override_doctype_class` (Bank Transaction override retained); the class
remains as an import-compatible shell. non_profit 16.1.1 → 16.1.2.
Verification: non_profit 74 + 35 tests green (2 expected skips), good_demo
87 green, good_npo 82 green (1 skip) — including new hook-contract tests
for the exact broken path, mirror-field maintenance on submit/cancel, H1
over-allocation and H2 cross-company rejections, and the backfill patch.
The final audit added the `before_validate` company guard because HRMS can
otherwise fail while resolving a cross-company reference before ordinary
`validate` doc-events run; the focused 23-test Donation module passed under
the active HRMS controller.
Two environment repairs were needed alongside: doc_events handlers must
take `(doc, method=None)` (bench convention) — three initial 1-arg
handlers TypeError'd — and the site's hrms installation had never run
`make_fixtures`, so standard Leave Types (`Casual Leave`, …) were missing
and broke ERPNext's test-record generator; seeded via
`hrms.setup.make_fixtures`.

**2. good_event integration query-bound failure is concurrent-work noise.**
`test_guest_event_list_query_count_is_bounded_at_full_page` (the L1
evidence test) fails with 74 > 45 queries against a working tree
containing ~55 files of unrelated uncommitted good_event changes from
another session (catalogue/payment work, `BROWSER_QA_FAILURE_AUDIT.md`).
N10's own coverage (23/23 unit, incl. the 3 new cache-key tests) is green.
Revalidate the bound after that work lands.

**3. Latent good_demo seed ordering issue — moot under the new mirror
fields.** `seeding.py` creates donations with `paid=1` before creating
their Payment Entry. Under the resolved design, outstanding comes from
`grand_total − advance_paid` (not the `paid` flag), so a pre-paid donation
with no allocations still yields full outstanding and PE creation works.
No code change needed; recorded for the record.

## Suggested Remediation Order (updated 2026-07-18)

Done in rounds 1-2: N1-N4, N6-N15, NB1, NB2, NB3, NB5, plus the hrms
Payment Entry shadowing (hook-based redesign). N5 accepted as not-a-bug
(user decision). NB4 deferred (user decision, kept on record).

1. ~~hrms/non_profit Payment Entry shadowing~~ — resolved 2026-07-18 via
   the hook-based redesign and Donation `grand_total`/`advance_paid`
   mirrors (non_profit 16.1.2); all three affected suites green.
2. Run `php tests/run.php` (31 checks) for good-event-embed on a PHP host;
   then N13-N15 are releasable.
3. The P3 queue (per-app small items) at normal priority. NB4 (ilanga
   orphaned images) stays deferred per user decision.
