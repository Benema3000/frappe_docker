# AGENTS.md — bench root

Guidance for coding agents working anywhere under `/workspace/development`.
This is the bench-level overview. Per-app specifics live in each app's own
`AGENTS.md` — read both.

---

## Agent Skills

- Project opencode skills live at `/workspace/.opencode/skills/` so agents
  launched anywhere in this workspace can discover them.
- Codex-visible symlinks live at `/home/frappe/.codex/skills/`.
- Claude-visible symlinks live at `/home/frappe/.claude/skills/`.
- Use `/workspace/.opencode/skills/frappe-bench/SKILL.md` for this bench's
  local app map, off-limits apps, commands, and Goodvantage-specific gotchas.
- Use `/workspace/.opencode/skills/frappe-dev/SKILL.md` for general Frappe
  app-development workflows and focused references.
- Additional downloaded Frappe skills from
  `Impertio-Studio/Frappe_Claude_Skill_Package` live under
  `/workspace/.opencode/skills/frappe-claude-skill-package/skills/source/`.
- Use `/workspace/.opencode/skills/frappe-taste/SKILL.md` for Frappe coding
  taste guidance from `frappe/bench-cli/taste.md`.
- Keep durable Frappe agent guidance in this root `AGENTS.md` and app-local
  `AGENTS.md` files; keep reusable triggerable workflow guidance in the skill.

---

## Core Working Style

- Prefer direct implementation over extended planning.
- Infer sensible defaults from the repository before asking questions.
- Ask only when blocked by missing credentials, external access, destructive
  actions, or unresolved business-rule ambiguity.
- Keep changes minimal, upgrade-safe, and aligned with existing Frappe
  patterns.
- **Never modify core apps directly:** `apps/frappe`, `apps/erpnext`,
  `apps/payments`, `apps/builder`, `apps/buzz`. The `apps/Commit` app is also
  off-limits.

## Custom App Documentation

- Every custom app must keep both root-level docs:
  - `HOW_TO.md` for operator/admin workflows and common procedures.
  - `DOCUMENTATION.md` for technical architecture, doctypes, hooks, APIs,
    operational contracts, and tests.
- When changing behavior in a custom app, update the relevant doc in the same
  change. New workflows, doctypes, public APIs, scheduled jobs, email flows,
  migrations, setup steps, or test commands should not land without docs.
- Keep `README.md` short and install/status focused. Keep `AGENTS.md` focused
  on coding-agent rules and gotchas; link to `HOW_TO.md` and
  `DOCUMENTATION.md` for user-facing and technical reference material.
- Do not add these docs to upstream/off-limits apps (`frappe`, `erpnext`,
  `payments`, `builder`, `buzz`, `Commit`) unless explicitly asked.

## Desk Support Links

- Custom apps must not expose Frappe's upstream support links
  (`https://support.frappe.io/help` or `https://frappe.io/support`) in Desk.
  Keep support/help surfaces Goodvantage-owned or app-local. Do not patch
  `apps/frappe` directly; use custom-app setup/hooks, such as
  `good_connector.desk_branding.remove_frappe_support_links()` and its Desk JS
  include, to suppress upstream support items upgrade-safely.

---

## What's in this bench

This is a Frappe v16 bench. Custom apps and extension apps tracked by this
guidance. Read app-local `AGENTS.md` when present; otherwise use the app's
`HOW_TO.md` and `DOCUMENTATION.md`.

| App | Domain | Depends on | Notes |
|---|---|---|---|
| [`good_connector`](frappe-bench/apps/good_connector/AGENTS.md) | Shared portal connector — JWT auth, task management, webhook API endpoints, email templating, permission helpers | (standalone) | Shared substrate for `mopi_app` and `barakah_app` |
| [`good_help`](frappe-bench/apps/good_help/AGENTS.md) | Embedded Desk help center backed by Frappe Wiki | `wiki` | Syncs `fixtures/help/<app>/` Markdown into Wiki Documents |
| [`mopi_app`](frappe-bench/apps/mopi_app/AGENTS.md) | Training modules, certificates, task campaigns, employee groups | `erpnext`, `good_connector`, `good_help` | Innermost dir is `mopiapp/` (mismatch — `frappe.scrub("MoPiApp")`) |
| [`barakah_app`](frappe-bench/apps/barakah_app/AGENTS.md) | Aqeeqa / Well charity order workflows, daily reminders | `erpnext`, `good_connector`, `good_help` | |
| [`non_profit`](frappe-bench/apps/non_profit/AGENTS.md) | Hard fork of Frappe's `non_profit` (OpenNGO-Project). Shared membership substrate (Member, Membership, Donation, Donor, …) | (standalone) | Dev branch in use: `miki-dev`. B2B (`Membership.customer`) and B2C (`Membership.member`) coexist |
| [`good_npo`](frappe-bench/apps/good_npo/AGENTS.md) | Generic Goodvantage NPO Desk / public presentation layer | `non_profit`, `good_connector`, `payrexx_integration`, `good_help` | Keep reusable; no Ilanga, Miki, or demo-only assumptions |
| [`good_demo`](frappe-bench/apps/good_demo/AGENTS.md) | Public demo shell — signup, temporary users, reset/seed routines | `good_npo`, `good_connector`, `good_help` | Reset only data marked as demo seed/demo user |
| [`miki_app`](frappe-bench/apps/miki_app/AGENTS.md) | kibesuisse Beitragserklärung — yearly contribution declaration for KiTa / SEB / TFO providers | `non_profit`, `good_connector`, `good_help` | CRMMember Dataverse rebuild |
| [`ilanga_app`](frappe-bench/apps/ilanga_app/AGENTS.md) | Theming / seeding / dashboard layer for Ilanga fundraising | `non_profit` | No custom doctypes — drives non_profit doctypes |
| [`workflow_visualizer`](frappe-bench/apps/workflow_visualizer/DOCUMENTATION.md) | Opt-in Desk process rail for standard Frappe Workflows | (standalone) | Branch in use: `version-16`; no app-local `AGENTS.md` yet — use `HOW_TO.md` / `DOCUMENTATION.md` |
| [`buzz`](frappe-bench/apps/buzz/AGENTS.md) | Upstream events / ticketing / sponsorships SPA. Provides `Buzz Event`, `Event Booking`, `Event Ticket`, etc. | (standalone) | Upstream — never patch directly |
| [`good_event`](frappe-bench/apps/good_event/AGENTS.md) | Independent event/course registration platform — public catalogue, bookings, correspondence, payment integration, trainer settlement | `payrexx_integration`, `good_connector`, `good_help` | Renamed from `event_app`; hook-based architecture for customization; kibesuisse integrations optional via hooks |
| [`payrexx_integration`](frappe-bench/apps/payrexx_integration/AGENTS.md) | Payrexx hosted-checkout payment gateway. Provides `Payrexx Settings` doctype + pay-by-email URL helper | `payments` | Standalone app on top of upstream `payments`; same pattern as Stripe / Paymob, but external to keep upstream upgrade-safe |

> **Naming confusion — route by doctype, not by name.** `miki_app` and
> `mopi_app` are two **different** apps in this bench. The user often says
> "mopi_app" when their request actually concerns miki_app. Anything mentioning
> `MiKi Declaration`, `MiKi Declaration Campaign`, `Qualikita`, `MiKi Category`,
> kibesuisse, KITA / SEB / TFO, Personnel A–K, or "member solution" → **miki_app**.
> Anything mentioning training modules, training certificates, task campaigns,
> or employee groups → **mopi_app**. Both apps document this routing in their
> own `AGENTS.md` intros.

### App dependency graph

```
good_connector  (standalone)
    ├── mopi_app      (required_apps = ["erpnext", "good_connector", "good_help"])
    └── barakah_app   (required_apps = ["erpnext", "good_connector", "good_help"])

good_help       (required_apps = ["wiki"])

workflow_visualizer  (standalone optional Desk Workflow UI)

non_profit      (standalone)
    ├── good_npo      (required_apps = ["non_profit", "good_connector", "payrexx_integration", "good_help"])
    ├── ilanga_app    (required_apps = ["non_profit"])
    └── miki_app      (required_apps = ["non_profit", "good_connector", "good_help"])

good_npo
    └── good_demo     (required_apps = ["good_npo", "good_connector", "good_help"])

buzz            (standalone — upstream)
payments        (standalone — upstream; never patch)
    └── payrexx_integration  (required_apps = ["payments"])

good_event      (required_apps = ["payrexx_integration", "good_connector", "good_help"])
```

### Cross-cutting patterns to be aware of

- **Workflow state sync** (`good_event` Good Event Booking + Good Event): the
  Frappe `Workflow` is installed and `workflow_state` stays synchronized with
  legacy free-text status fields on each save (`services/workflow.py`).
  Never strip those legacy fields — reporting and compatibility code still
  reads them.
  Adding a new state means updating `STATES`, `TRANSITIONS`, and
  `derive_workflow_state` in lockstep.
- **good_event independence and hooks** (`good_event`): fully independent from
  miki_app as of May 2026. All kibesuisse-specific integrations are now
  optional and provided via hooks. The app ships with generic default
  implementations for:
  - `good_event_salutation_provider` — contact salutation generation
  - `good_event_invoice_email_provider` — invoice email rendering
  - `good_event_invoice_pdf_provider` — invoice PDF generation
  - `good_event_invoice_html_provider` — invoice HTML rendering
  - `good_event_dunning_defaults_provider` — dunning document defaults
  - `good_event_dunning_pdf_provider` — dunning PDF generation
  - `good_event_role_profile_provider` — role profile setup
  - `good_event_seed_data_provider` — seed data loading
  For kibesuisse deployments, configure these hooks in `hooks.py` to point
  to miki_app implementations. Without hooks, good_event uses ERPNext-standard
  defaults. See `INDEPENDENCE_SUMMARY.md` for architecture details.
- **Workflow visualizer** (`workflow_visualizer`): optional Desk enhancement
  that renders an opt-in process rail for standard Frappe Workflows. It must
  remain permission-preserving: data APIs check document read access and the
  client still applies transitions through Frappe's standard workflow action
  path. Owning apps can add display-only transition side-effect notes through
  `workflow_visualizer_transition_notes`; keep actual side effects in the
  owning app's normal workflow/document hooks.
- **Correspondence framework** (`good_event/services/correspondence.py`):
  every outbound email goes through one dispatcher with a flow key. Auto
  triggers honour an auto-toggle (`Good Event Email Settings`) plus per-event
  override (`Good Event.disabled_email_flows`). Manual sends pass
  `manual=True` to bypass the gate. Templates are de/fr/it `Email Template`
  fixtures named `good_event_<flow>_<lang>` — never overwritten on re-install.
- **Payrexx pay-by-email** (`payrexx_integration.api.payrexx_pay_url`):
  HMAC-signed redirect URL keyed off the site's `encryption_key`. The
  Payrexx `Gateway` is created lazily on click via the `pay_invoice`
  endpoint, not eagerly when the email is composed.
- **ERPNext Dunning** is wired via *Dunning Letter Text* (per-language body
  on Dunning Type), NOT via `Email Template`. good_event provides
  localised template bodies and a helper
  (`good_event.services.dunning_setup.apply_good_event_dunning_to_all`)
  that copies them into Dunning Type rows.

### Portal payload gotcha

- `miki_app`'s hosted legacy hub calls do **not** reliably match the newer
  portal test payloads. The live Miki declaration flow can post the full
  body under `data` as a JSON string and omit `finalSubmit` on the last step.
- If you touch `miki_app.api.goodApi_webhook_MikiAction` or
  `miki_app.portal.miki_webhook`, always `_parse_payload(...)` before local
  dispatch. Otherwise the request logs look correct (because the legacy
  logger parses them) while the actual write path silently ignores the body.
- In the legacy Miki shape, a truthy `completeness_confirmed` inside `data`
  is the fallback signal for "this StoreData is the final submit".
- Miki portal final submit also creates operations-queue `ToDo`s via
  `MiKiDeclaration.sync_master_data()`. In production that can trigger assignment
  notification emails during `after_commit`, so the portal final-submit path
  must mute request-local emails or the declaration can sync successfully in
  DB while the HTTP response still fails with an SMTP error.

### Hosted Hub Tenant Mapping

- Hosted selfservice/browser tests must set `Good Connector Settings.org_id`
  to the app-specific NGO before running the hosted flow, then restore the
  previous value in `finally`.
- Current mapping on this bench:
  - `miki_app` -> NGO `11`
  - `barakah_app` -> NGO `2`
  - `mopi_app` -> NGO `9`
- This bench currently has no `site_config.json` override for
  `good_connector_org_id`, so changing the Single setting is enough to drive
  the default NGO for hosted login-token generation during tests.

### Recent Debugging Notes

- Do **not** run multiple `bench run-tests` commands against the same site in
  parallel. `barakah_app.setup.ensure_setup()` reloads DocTypes during
  `before_tests`, and parallel runs deadlock on `tabDocType` / `tabSeries`.
- If an SSO-created Desk user can open an app but list views fail with
  `Insufficient Permission for List Filter`, check the user's `User.user_type`
  and the app role's `Role.desk_access`. Frappe grants the automatic
  `Desk User` role only to `System User` accounts, and standard list views read
  the `List Filter` DocType through `Desk User`. App setup should keep
  app-specific Desk roles enabled with `desk_access = 1` and repair existing
  users with those roles from `Website User` to `System User`; do not grant
  broad `Desk User` DocPerm rows on app doctypes to hide the issue.
- Barakah portal file visibility has two layers:
  - supplier-linked generated files (`supplier` + `generated_file`)
  - open-task fallback via assigned Barakah tasks
  Never return early just because a portal user has no `Portal User ->
  Supplier` rows, or the fallback path stops working.
- For Barakah task visibility, reminder delivery, and file fallbacks, reuse
  `good_connector.portal_helpers.portal_email_can_access_task()` rather than
  re-implementing `_assign` / `ToDo` / `Portal User` checks locally. When
  those paths drift apart, the hub, reminders, and file pages disagree about
  who should see the same task.
- Barakah task targets are explicit Task links, not reactive joins. If
  `Barakah Country.country_office` changes, open Aqeeqa / Well tasks must be
  retargeted to the current Supplier and reassigned to that Supplier's portal
  users. Cancelled `ToDo` rows must not count as portal visibility.
- Portal task status `Overdue` is intentionally **non-terminal**. It must stay
  visible in `GetProcessList` and `GetData` must return the open/editable
  task payload with `gc_taskcomplete: False`. Only `Completed`, `Cancelled`,
  and `Closed` are terminal hub task statuses.
- MoPi is the exception that may include completed assignment history in
  `GetProcessList`. Keep non-terminal/editable rows sorted first, and do not
  use completed history rows for `StoreFiles` or other edit actions.
- Portal file uploads are marked with `File.attached_to_field =
  "portal_upload"`. `DeleteFiles` must only delete those portal-created files;
  generated/customer-facing attachments such as invoices, dunnings, Barakah
  order files, or certificates are read-only from the hub.
- App-scoped endpoints must enforce app context for task and file actions.
  A task/file visible through one app's endpoint should not become mutable via
  another app's endpoint just because the same portal email is assigned.
- Swiss output formatting is driven by Frappe's runtime defaults, not just the
  `System Settings` Single row. If `format_date()` / `fmt_money()` still show
  the old pattern after changing `System Settings.date_format` or
  `number_format`, also update `frappe.db.set_default(...)`, commit if you're
  in a standalone script, and clear cache before trusting the result.
- Hosted Barakah file debugging has two separate layers too:
  - Frappe / `good_connector` can be healthy (`GetFileList` lists files and
    direct `GetFileUrls` returns the attachment bytes)
  - the hosted hub can still fail to open/download because its own
    `/rest/file-urls?ids=...` route returns `200 null`
  If the browser lists file names but clicks do nothing, verify the hub
  wrapper before changing Barakah or `good_connector`.
- `selfservicetest.goodvanta.ge` currently rejected Barakah token-login probes
  with `/rest/session` = `401`, so it could not be used for automated file
  download verification. Treat that as a hub auth/session issue, not a
  Barakah app issue.
- The local browser suites in this bench cannot assume login lands on Desk.
  `POST /api/method/login` currently returns `home_page="dashboard"`, so
  Playwright helpers should normalize to `/desk` explicitly after login before
  exercising Desk forms.
- If local browser tests suddenly fail at `/login` with `ModuleNotFoundError:
  payments`, first check whether the local `bench serve` process is stale.
  In this bench the `payments` source is present, and restarting the web
  process restored `/login` without code changes.
- `miki_app.tests.test_e2e_playwright` uses two different declaration helpers:
  - `_setup_declaration()` = idempotent shared declaration
  - `_setup_fresh_declaration()` = cleanup + fresh reseed for later hub tests
  Reusing the fresh helper too early will delete the declaration that invoice /
  dunning / QR-bill checks still rely on.
- On this dev site, `bench --site development16.localhost run-tests --app
  non_profit` can pass the app tests and then exit non-zero while ERPNext
  lazily bootstraps unrelated test records. The observed cause was
  `Selling Settings.cust_master_name = "Naming Series"` leaving `_Test
  Customer` stored under a numeric Customer docname while ERPNext's own test
  bootstrap expects a link named `_Test Customer`. Do not rename Customer rows
  casually; treat this as a local ERPNext test-data/bootstrap issue, not a
  non_profit regression.

---

## Frappe naming conventions (catches us regularly)

Frappe apps use a three-level package layout: `app_name/app_name/innermost_dir/`.
The innermost name is `frappe.scrub(<module name from modules.txt>)` and
determines DocType file paths. **Do not rename the innermost dir or change
`modules.txt` during ordinary feature work** — it needs an explicit app/module
rename migration and a site install-registry update.

DocType names themselves are effectively site-global. The module name does not
namespace a DocType string: Frappe stores data in `tab<DocType>` tables and all
Link/Table `options` point at the plain DocType name. Avoid generic custom
DocTypes like `Declaration`, `Training Module`, or `Event Booking` in
product-specific apps. Prefix product-specific DocTypes with the app/product
name, and keep only truly shared substrate DocTypes generic.

Current audit outcomes:

| App | Use these product-scoped DocType names |
|---|---|
| `good_event` | `Good Event`, `Good Event Booking`, `Good Event Master`, `Good Event Coupon`, etc. |
| `miki_app` | `MiKi Declaration`, `MiKi Declaration Campaign`, `MiKi Category`, `MiKi Settings`, etc. |
| `mopi_app` | `MoPi Training Module`, `MoPi Training Type`, `MoPi Task Campaign`, `MoPi Employee Group`, etc. |
| `good_connector` | `Good Connector Available Language` for the settings child table |

The mismatched ones in this bench:

| App | Package dir | Innermost dir | Module name |
|---|---|---|---|
| `mopi_app` | `mopi_app/mopi_app/` | `mopiapp/` | `MoPiApp` |
| `miki_app` | `miki_app/miki_app/` | `miki_app/` | `MiKi App` |
| `non_profit` | `non_profit/non_profit/` | `non_profit/` | `Non Profit` |
| `ilanga_app` | `ilanga_app/ilanga_app/` | `ilanga_app/` | `Ilanga App` |

`mopi_app` is the surprising one — Python imports use `mopi_app.*` but
DocType paths under the inner dir use `mopi_app/mopiapp/doctype/`.

---

## Frappe Best Practices

### Metadata First

- Prefer DocType configuration, Custom Fields, Property Setters, Client
  Scripts, and exported customizations before writing custom code.
- For standard DocType field layout changes, use a DocType-level `field_order`
  Property Setter. Field-level `insert_after` can be insufficient when Frappe's
  meta sort is driven by `field_order`.
- For standard DocField property changes such as `hidden`, `read_only`,
  `in_list_view`, defaults, or quick-entry visibility, use Property Setters.
  Do not mutate `tabDocField` directly just to mirror the desired metadata.
- Use client scripts for Desk UX behavior only. Do not move DocFields around in
  the DOM when Frappe metadata can express the layout.
- Business logic belongs server-side; client validation is UX only.
- Reuse existing Frappe utilities, standard DocTypes, and framework patterns
  before creating new abstractions.

### DocType Access Patterns

- Use `frappe.get_cached_doc` when fetching a document repeatedly.
- Use `frappe.get_doc` when you need a document for mutation or hooks.
- Use `frappe.new_doc("DocType")` for creating new documents.
- Avoid `get_doc` inside loops; use `frappe.get_all`, `frappe.get_list`, or
  query builder to avoid N+1 queries.
- For single-field lookups, use `frappe.db.get_value`.

### Database Access

- Prefer ORM and query builder: `frappe.get_all`, `frappe.get_list`,
  `frappe.db.get_value`, `frappe.qb`.
- Avoid raw SQL in new code.
- **Frappe v16: raw SQL functions are not allowed as strings in
  `frappe.db.get_value`.** Use the query builder:

  ```python
  from frappe.query_builder.functions import Max
  dt = frappe.qb.DocType("Child Table")
  max_idx = (
      frappe.qb.from_(dt)
      .select(Max(dt.idx))
      .where(dt.parent == parent_name)
  ).run()[0][0] or 0
  ```

- Never import `pypika` directly — use `frappe.query_builder`.
- Parameterise through query builder expressions; never interpolate user input
  into SQL.

### Datatype Conversion

Use built-in helpers from `frappe.utils.data`: `cint`, `cstr`, `flt`,
`getdate`, `get_datetime`. Do not add custom conversion helpers.

### JSON And Request Handling

- Always use `frappe.parse_json` for inbound JSON-like payloads.
- Never use `json.loads` directly on request data.
- For outbound HTTP, use `frappe.integration.utils.make_get_request` /
  `make_post_request` / `make_put_request` / `make_patch_request`.

### Permissions, Security, And Transactions

- Always respect user permissions.
- Use `ignore_permissions=True` only when absolutely required and justified.
- Validate permissions before reading or mutating documents in custom APIs.
- **Never call `frappe.db.commit()` inside DocType event hooks.**
- **Do NOT call `frappe.db.commit()` in `after_install` or `after_migrate`
  hooks.** Frappe's installer commits the transaction after all hooks run.
- Let Frappe manage request transactions; use explicit commits only in
  standalone scripts or carefully controlled batch jobs.

### Background Jobs

- Use `frappe.enqueue` for long-running work.
- Use `deduplicate=True` to prevent duplicate job queueing.
- Use `enqueue_after_commit=not frappe.flags.in_test` so jobs run
  synchronously during tests.
- Never block request-response cycles with expensive business logic.

### Error Handling

- Use `frappe.throw` or specific framework exceptions for user-facing errors.
- Wrap user-facing strings with `frappe._()` for translation.
- Use `frappe.log_error` for unexpected failures.
- Avoid bare `except:` blocks.

### Naming And Imports

- Use full variable names; avoid unnecessary abbreviations.
- Avoid leading-underscore function names unless they are private helpers
  behind a public or whitelisted function.
- Keep imports at the top of the file.
- In JavaScript, use `camelCase` and follow surrounding project style.

### DocType Safety

- Every custom DocType and child table must have a real Python controller
  class. Missing or commented-out controllers can cause orphan deletion
  during `bench migrate`.
- Add or update tests for new functionality and regressions.

### Custom Fields

- Use `create_custom_fields` from
  `frappe.custom.doctype.custom_field.custom_field`.
- Call the creation in **both** `after_install` and `after_migrate` hooks.
- The target doctype must exist before the custom field is created — early-
  return if `frappe.db.exists("DocType", "<Name>")` is false.

### Seeding Data On Install

- Use `after_install` and `after_migrate` hooks to run seed functions.
- Always check `frappe.db.exists()` before inserting seed data (idempotent).
- Use `ignore_permissions=True` for seed inserts since they run in a system
  context.

### Install/Uninstall Hygiene (keep the working tree clean)

`bench install-app` / `uninstall-app` must not leave the working tree dirty
on a dev site. Some Frappe behaviors silently rewrite app fixtures — guard
against them.

- **Dev-mode auto-export is symmetric with save AND trash.** Any DocType with
  `if frappe.conf.developer_mode and self.is_standard` in its controller
  (e.g. `Number Card.on_update`, `Workspace Sidebar.before_save`) rewrites
  its JSON fixture on every `save()` — and `Workspace Sidebar.on_trash`
  physically *deletes* the source file on uninstall. Production
  (`developer_mode=0`) is unaffected; dev installs/uninstalls need to be
  clean. Each app ships a `before_uninstall` hook that clears
  `Workspace Sidebar.app` for its rows before Frappe's cascade runs, which
  skips the file-delete branch (see `setup.py::before_uninstall` in
  `mopi_app`, `barakah_app`, `ilanga_app`, `miki_app`).
- **Never let a Link field inherit the site's default silently in a shipped
  fixture.** Example: Number Card has a `currency` Link. If you insert a
  Count card without specifying `currency`, Frappe fills it from the
  installing site's default (INR on stock, CHF on Swiss sites) and the
  dev-mode auto-export rewrites the shipped JSON. Pin explicitly
  (`"currency": None`) in both the seed function AND the fixture JSON.
- **Don't re-save fixture-backed documents inside `after_install` /
  `after_migrate` unless something actually changed.** Calls like
  `page.save()` with no-op mutations still trigger the dev-mode export and
  bump the `modified` timestamp. Guard with an "actually changed?" check.
- **Don't duplicate fixture data between seed functions and JSON fixtures.**
  If a Number Card / Print Format / Workspace Sidebar is shipped under
  `<app>/<module>/<doctype>/<name>/<name>.json`, the fixture importer creates
  it on install. A seed that also creates it is redundant — and if seed and
  fixture disagree, the last writer wins and the working tree drifts.
- **Workspace Sidebar fixtures need `app`, `module`, and `standard: 1`.**
  Without those three top-level fields, `frappe/boot.py::get_sidebar_items`
  hides the sidebar from every non-Administrator user. `standard: 1` also
  opts the sidebar into the dev-mode export/delete file lifecycle.
- **Workspace Sidebars need a matching DocPerm base.** A user only sees a
  sidebar if its `module` is in their `allow_modules`, derived from doctypes
  they can read. Granting a module's doctypes only to `System Manager` hides
  the module from every other role. Ship DocPerm for a broader role
  (commonly `Desk User` with create/read/write) — see `barakah_app` for the
  reference pattern.

### All `@frappe.whitelist()` functions must have type hints

`frappe/semgrep-rules` flags untyped whitelisted functions as a security
issue (`frappe-missing-type-hints-in-whitelisted-function`).

---

## Workspace Sidebar (Frappe v16)

### Diagnosing a stale sidebar

1. Open `/app/<workspace>` in a browser, devtools →
   `frappe.boot.workspace_sidebar_item['<label lowercased>']`. Icons
   `wallpaper` / `list` / `panel-top` mean you're seeing
   `auto_generate_sidebar_from_module()`, not the app fixture.
2. Check the DB: `bench --site <site> mariadb -e "select count(*) from
   \`tabWorkspace Sidebar Item\` where parent='<Label>'"`.
3. If DB is correct but boot is wrong, it's the cache. Run `bench --site
   <site> clear-cache` and hard-reload. Do **not** chase it with `bench
   restart`, `frappe.clear_cache()`, or `bench build` — none of those clear
   `@site_cache()`.

### Don't trust any of these to fix a stale sidebar in dev

- `bench restart` — dev uses `honcho`, not supervisor; it's a no-op.
- `frappe.clear_cache()` — only clears Redis, not in-process `_SITE_CACHE`.
- `bench build` — unrelated; rebuilds JS/CSS, not Python caches.
- `bench migrate` alone — won't invalidate the web worker's cached
  `auto_generate_sidebar_from_module` result.

### When adding or changing a workspace, ship both fixtures

- `<app>/<module>/workspace/<slug>/<slug>.json` owns the page body (cards,
  shortcuts, link groups).
- `<app>/<module>/workspace_sidebar/<slug>.json` owns the left navigation
  rail. **Without this, Frappe auto-generates from top-3 DocTypes by row
  count.**
- Sub-items under a `Section Break` must set `"child": 1`, otherwise they
  render as top-level entries.
- If a custom Desk route helper restores/selects a sidebar for a DocType route,
  it must first check whether the current app sidebar already contains that
  DocType and leave the user there. Shared doctypes such as `Member`,
  `Membership`, `Donation`, `Good News`, `Task`, `User`, `Sales Invoice`, or
  `Dunning` can appear in multiple custom app sidebars; clicking one from
  `miki_app`, `ilanga_app`, `barakah_app`, `mopi_app`, etc. must not switch
  the user into another app just because that DocType is also exposed there.

### When resyncing a `Workspace Sidebar` from code

- Do **not** call `frappe.delete_doc("Workspace Sidebar", name)` in developer
  mode. The `on_trash` hook calls `delete_file(app, title)` and removes the
  JSON fixture you're about to reimport.
- Delete rows directly, then reimport:

  ```python
  frappe.db.delete("Workspace Sidebar Item", {"parent": name})
  frappe.db.delete("Workspace Sidebar", {"name": name})
  import_file_by_path(sidebar_fixture_path, force=True, ignore_version=True)
  ```

### Icon names must match Frappe's Lucide sprite exactly

The sprite lives at `apps/frappe/frappe/public/icons/lucide/icons.svg` and
each symbol has `id="icon-<name>"`. If the fixture references an icon not in
the sprite, the `<use>` element resolves to nothing and the link renders
without any glyph (the label still works).

Lucide v1 renamed several icons. Common ones that bite in Frappe v16:

- `alert-triangle` → `triangle-alert`
- `alert-circle` → `circle-alert`
- `alert-octagon` → `octagon-alert`
- `file-edit` → `file-pen`

Verify before trusting a name from lucide.dev:

```bash
grep 'id="icon-<name>"' apps/frappe/frappe/public/icons/lucide/icons.svg
```

In the browser:

```js
!!document.getElementById('icon-<name>')  // true → renders, false → no glyph
```

### Don't report the fix as done until

- `frappe.boot.workspace_sidebar_item['<label>'].items.length` in a real
  browser equals the fixture's item count.
- Every item's `<use href="#icon-...">` resolves to a symbol that
  `document.getElementById(...)` returns — a missing symbol means the icon is
  silently dropped.
- Icons in the DOM match the fixture (`home`, `users`, `building-2`, etc.) —
  not `wallpaper` / `list` / `panel-top`.

### Why `bench --site <site> clear-cache` is the one that works

`auto_generate_sidebar_from_module` is decorated with `@site_cache()` — a
per-process in-memory dict in `frappe.utils.caching._SITE_CACHE`, not Redis.
`frappe.clear_cache()` only touches Redis and doesn't invalidate it. `bench
restart` in dev uses `honcho` (not supervisor) and is a no-op. `bench --site
<site> clear-cache` rebuilds the site cache dict; the next HTTP request
rebuilds the boot from fresh DB state.

---

## Portal Authentication (good_connector pattern)

`good_connector`, `mopi_app`, and `barakah_app` serve external portals that
do not have Frappe sessions. Authentication works via:

1. Portal calls `goodApi_webhook_login` (guest endpoint) with a user email.
2. `good_connector` sends a login link email containing a JWT token.
3. Portal calls subsequent endpoints with the JWT token.
4. `good_connector/api/auth.py` validates the JWT (HS256, server-side
   secret) on every request.
5. API-level actions use a separate API password from
   `Good Connector Settings`.

`good_connector/workflow_support.py` uses `frappe.set_user()` inside a
context manager for workflow transitions — `frappe.model.workflow.apply_workflow()`
checks `frappe.session.user` against the workflow's `allowed` role and has no
`ignore_permissions` parameter. The context manager guarantees the original
user is restored via `try/finally`.

---

## Commands

### Lint / format

All custom apps share the same ruff config: line length 110, tab indentation,
target `py314`.

```bash
# From any app directory
pre-commit run --all-files
ruff check <app_package>/
ruff format <app_package>/

# If CI fails with formatting issues, reset local pre-commit cache:
pre-commit clean && pre-commit run --all-files
```

### Bench / site

```bash
cd frappe-bench
bench --site <site> migrate
bench --site <site> install-app <app_name>
bench --site <site> console
bench --site <site> execute <dotted.path.to.function>
```

Default dev site: `development16.localhost`. Default credentials:
`Administrator` / `admin`.

### Tests

```bash
# All tests for an app
bench --site <site> run-tests --app <app_name>

# Single module
bench --site <site> run-tests --module <app>.tests.<test_module>

# Single test method
bench --site <site> run-tests --module <app>.tests.<test_module> --test <Class>.<method>
```

Prefer `IntegrationTestCase` from `frappe.tests` for DB-backed tests and
`UnitTestCase` for pure logic; existing `FrappeTestCase` suites can remain as
they are unless being touched. In-test jobs run synchronously
(`frappe.flags.in_test` is truthy).

- Run `bench migrate` after DocType schema changes.
- **Install order matters**: `wiki` before `good_help`; `good_help` before
  apps with help fixtures; `good_connector` before `mopi_app` / `barakah_app`;
  `non_profit` before `miki_app` / `ilanga_app`. ERPNext is required for
  `mopi_app`, `barakah_app`, `miki_app` (they add custom fields to `Task`).

---

## CI / GitHub Actions

Each app ships its own workflows. Common shape:

- **CI** (`.github/workflows/ci.yml`): push to `main` and PRs. Python 3.14,
  Node 24, MariaDB 11.8, Redis. Uses `actions/checkout@v6`,
  `actions/setup-python@v6`, `actions/setup-node@v6`, `actions/cache@v5`.
  ERPNext is required for `mopi_app` / `barakah_app` / `miki_app`.
- **Linter** (`.github/workflows/linter.yml`): PRs and `workflow_dispatch`.
  Job 1 runs `pre-commit/action@v3.0.0` + `frappe/semgrep-rules`. Job 2 runs
  `pip-audit --desc on .`.

### Pre-commit cache and prettier

- **Local vs CI formatting mismatch**: CI installs pre-commit hooks from
  scratch, while local environments cache hook environments. A stale local
  cache produces different formatting (especially prettier).
- **Fix**: `pre-commit clean && pre-commit run --all-files` to reset and
  reformat with a fresh environment matching CI. Run `pre-commit clean` after
  changing `.pre-commit-config.yaml` hook versions or `.editorconfig`.
- **Prettier `.prettierrc` is required**: every repo sets `useTabs: true`,
  `tabWidth: 4`, `printWidth: 99` explicitly. CI's pre-commit reads
  `.editorconfig` (which sets `indent_size = 4`) to derive `tabWidth`, but
  local pre-commit may not resolve `.editorconfig` consistently. Without an
  explicit `.prettierrc`, local prettier defaults to `tabWidth: 2`,
  producing different line-wrapping than CI. Keep `.prettierrc` in sync with
  `.editorconfig`.
- **Never use `npx prettier` directly** — always run
  `pre-commit run prettier --all-files`. The pre-commit config pins
  `prettier@2.7.1`; `npx prettier` installs the latest version (e.g. 3.x)
  which formats differently.

---

## Semgrep Overrides

Each app has a `SEMGREP_OVERRIDES.md` documenting every `nosemgrep`
annotation. When adding a new `# nosemgrep`:

1. Add the annotation inline on the flagged line.
2. Document it in the app's `SEMGREP_OVERRIDES.md`: rule name, what it
   prevents, why the override is safe.

Common overrides in these apps:

- `guest-whitelisted-method` — portal endpoints that implement their own
  JWT/API-password auth.
- `frappe-ssti` — `frappe.render_template()` with templates sourced from
  Email Template / Print Format doctypes (only System Managers can edit).
- `frappe-setuser` — workflow transitions using a `try/finally` context
  manager.
- `frappe-security-file-traversal` — hardcoded or `tempfile`-generated paths
  with no user input.
- `tempfile-without-flush` — files used as output destinations for external
  processes (e.g. wkhtmltopdf).

---

## Frontend Best Practices

- Prefer `async`/`await`; avoid callback-heavy flows.
- Use `frappe.call` with promise-based handling.
- Use Frappe global helpers in desk scripts: `cstr()`, `cint()`, `flt()`,
  `is_null()`, `format_currency()`.
- Keep Desk actions mobile-safe. Form and workflow operations belong in
  Frappe's Actions dropdown via `frm.page.add_action_item(...)`, not
  `frm.add_custom_button(...)`, because inner-toolbar buttons overflow on
  mobile. List actions should use `listview.page.add_action_item(...)` for
  always-available actions or `listview.page.add_actions_menu_item(...)` for
  checked-row bulk actions. Custom app pages should expose at most one primary
  top-bar CTA; put additional operational actions in `page.add_action_item(...)`
  and utility actions such as refresh in `page.add_menu_item(...)`.
- Preserve existing UI patterns unless the task explicitly requires redesign.
- Use `frappe.set_route("page-name", param)` for navigation; read params with
  `frappe.get_route()`.

---

## Reports

- Standard entry point: `def execute(filters): return get_columns(),
  get_data(filters)`.
- Use query builder imports from `frappe.query_builder` and
  `frappe.query_builder.functions`.
- Build lookup maps first, then merge in loops to avoid N+1 behavior.
- Cache expensive derived data where needed.

---

## Notes

- Prefer framework conventions over custom implementations.
- Keep business logic out of thin controllers when a service/helper layer
  improves clarity, but avoid abstraction without need.
- Write readable, predictable, maintainable code.
- Add or update tests for new functionality and regressions.
