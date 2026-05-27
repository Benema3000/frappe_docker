---
name: frappe-bench
description: Use when working on Frappe, ERPNext, bench, DocTypes, hooks, migrations, permissions, workspaces, portals, reports, or tests in this repository.
---

# Frappe Bench

Use this skill for work under `/workspace/development/frappe-bench` and the
custom apps listed in `/workspace/development/AGENTS.md`.

## First Steps

- Read `/workspace/development/AGENTS.md` first.
- Read the app-local `AGENTS.md` before editing any custom app.
- Route by DocType/domain, not app name, when names are ambiguous.
- Never modify upstream or off-limits apps directly: `apps/frappe`,
  `apps/erpnext`, `apps/payments`, `apps/builder`, `apps/buzz`, or
  `apps/Commit`.
- Keep changes minimal, upgrade-safe, and aligned with existing Frappe patterns.

## Custom Apps

- Update `HOW_TO.md` and `DOCUMENTATION.md` in the same custom app when behavior
  changes.
- Keep `README.md` short and install/status focused.
- Add or update tests for behavior changes and regressions.
- All `@frappe.whitelist()` functions need type hints.
- Every custom DocType and child table must have a real Python controller class.

## Frappe Patterns

- Prefer DocType metadata, Custom Fields, Property Setters, fixtures, and hooks
  before custom code.
- Use server-side validation for business rules; client scripts are UX only.
- Prefer `frappe.get_all`, `frappe.get_list`, `frappe.db.get_value`, cached docs,
  and query builder over raw SQL.
- Do not import `pypika` directly; use `frappe.query_builder`.
- Use `frappe.parse_json` for inbound JSON-like payloads.
- Use Frappe conversion helpers: `cint`, `cstr`, `flt`, `getdate`,
  `get_datetime`.
- Use `frappe.throw` for user-facing errors and `frappe.log_error` for
  unexpected failures.

## Permissions And Transactions

- Respect permissions by default.
- Use `ignore_permissions=True` only when necessary and justified.
- Validate permissions before custom API reads or mutations.
- Never call `frappe.db.commit()` inside DocType event hooks.
- Do not call `frappe.db.commit()` in `after_install` or `after_migrate` hooks.
- Let Frappe manage request transactions; explicit commits belong only in
  standalone scripts or controlled batch jobs.

## Setup And Fixtures

- Use `create_custom_fields` for custom fields and call it from both
  `after_install` and `after_migrate`.
- Guard setup/seed code with `frappe.db.exists()` and make it idempotent.
- Do not re-save fixture-backed documents unless something actually changed.
- Pin fields that would otherwise inherit site defaults in shipped fixtures.
- Avoid duplicate ownership between seed functions and JSON fixtures.

## Workspaces

- Workspace changes usually need both fixtures: `workspace/<slug>/<slug>.json`
  and `workspace_sidebar/<slug>.json`.
- Workspace Sidebar fixtures need `app`, `module`, and `standard: 1`.
- Sidebar entries need valid Lucide icon names from
  `apps/frappe/frappe/public/icons/lucide/icons.svg`.
- If DB sidebar data is correct but Desk boot is stale, run
  `bench --site development16.localhost clear-cache`.

## Commands

Run from `/workspace/development/frappe-bench` unless an app-local guide says
otherwise.

```bash
bench --site development16.localhost migrate
bench --site development16.localhost run-tests --app <app_name>
bench --site development16.localhost run-tests --module <app>.tests.<test_module>
bench --site development16.localhost execute <dotted.path>
```

Do not run multiple `bench run-tests` commands against the same site in
parallel.

## Linting

Run from an app directory.

```bash
ruff check <app_package>/
ruff format <app_package>/
pre-commit run --all-files
```

Use `pre-commit run prettier --all-files` for prettier. Do not use
`npx prettier` directly because the pinned pre-commit prettier version may
differ from latest npm.

## Goodvantage Bench Gotchas

- Portal endpoints often use JWT/API-password auth instead of Frappe sessions.
- App-scoped task and file endpoints must enforce app context.
- Portal uploads use `File.attached_to_field = "portal_upload"`; generated
  files are read-only from the portal.
- Miki legacy payloads can place JSON under `data`; parse before dispatch.
- Swiss date/money formatting depends on runtime defaults and cache, not only
  Single rows.
- Desk users that need list views must be `System User` accounts and have roles
  with `desk_access = 1`.
