# Custom Frappe Apps Audit — 2026-06-12

Read-only audit of all 12 custom apps in this bench (~127k LOC Python), against
`/workspace/development/AGENTS.md`, the `frappe-bench` / `frappe-dev` /
`frappe-taste` skills, and `SECURITY_AUDIT_PROMPT.md`. Audited per-app plus one
cross-app redundancy pass. The three highest-severity findings were
independently re-verified against the code.

Apps: good_connector, good_event, miki_app, mopi_app, barakah_app, good_demo,
good_npo, non_profit, payrexx_integration, good_help, ilanga_app,
workflow_visualizer.

> **Scope note (2026-06-12):** `ilanga_app` is a proof-of-concept only — its
> findings are recorded for completeness but are explicitly **out of scope for
> remediation**. Do not invest in ilanga fixes or refactors. (Exception: when a
> substrate change in non_profit would outright break ilanga's pages, the
> minimal consumer update is fine — e.g. the donate_confirm key redirect.)

---

## Executive Summary

**Overall: this estate is in unusually good shape for its size.** Across all
12 apps: zero raw-SQL injection vectors, zero bare excepts, zero
`frappe.db.commit()` in doc-event or install hooks, type hints on all ~170
whitelisted endpoints, `frappe.parse_json` used consistently, real controllers
for every DocType, idempotent seeds, and timing-safe credential comparisons
(`hmac.compare_digest`) where they matter. Guest endpoints consistently
implement real auth (JWT / API password / HMAC / CAPTCHA + rate limit).
Escaping discipline in both Python-built HTML and Desk JS is consistently good.

The debt is concentrated in three places:

1. **A handful of real security bugs** — one High in barakah (login-token
   leak), one payment-routing bug in good_npo (Sandbox-first), guest PII
   enumeration in non_profit, and a cluster of Mediums (below).
2. **Cross-app copy-paste** — install boilerplate ×7–9 apps, Playwright
   harness ×3–5, PDF helpers ×3 byte-identical, a stale dashboard fork, and
   inconsistent hub-webhook contracts across mopi/barakah/miki.
3. **File/function size** — ~15 files are 4–9× over the taste guideline
   (100–300 lines), concentrated in good_event, miki_app, good_npo, good_demo.

**Top 3 security risks:** barakah reminder token leak; good_npo Sandbox-first
payment routing; non_profit `donate_confirm` donor-PII enumeration.

**Top 3 redundancy problems:** setup.py install boilerplate (7–9 copies);
hub-webhook handler drift (3 different auth/error contracts); Playwright
harness (~600–900 duplicated lines).

**Top 3 simplicity problems:** good_event `public_pages.py` (2,789 lines,
incl. a 590-line function); miki `correspondence_defaults.py` (2,192) +
`setup.py` (1,979); good_npo `fundraising.py` (1,771) mixing 5 concerns.

---

> **Remediation log (2026-06-12):** All five "fix immediately" items below are
> **FIXED** (targeted tests green, `bench migrate` run for the Donation schema
> change):
> 1.1 reminder runner now renders per recipient (`recipient_contexts`
> contract); barakah **and miki** hooks supply personal login URLs per
> recipient only. 1.2 `resolve_payrexx_settings` is now explicit-choice
> (`good_npo_payrexx_gateway` site config; throws on ambiguity). 1.3
> `donate_confirm` is key-gated via `Donation.confirmation_key` +
> `donation_confirm_query()` (ilanga wrappers updated minimally so the PoC
> keeps working). 1.4 chapter.html escapes member values; `chapter.join`
> validates http(s) URLs. 2.x payrexx webhook now binds the verifying key to
> the IR's own gateway (`payrexx_settings` stored at creation), and
> `payment_success` derives credentials from the IR, not the caller.
> The 30-day login-token window is intentionally retained (user decision —
> the JWT-expiry recommendation in §2 is declined).

> **Remediation log — pass 2 (2026-06-12):** All remaining findings were
> implemented except the agreed structural follow-up pass (file splits,
> non_profit PaymentEntry minimal-delta rewrite, good_npo→good_demo demo
> content extraction, miki receivables/correspondence consolidation) and
> everything ilanga-related (PoC, out of scope). Highlights: good_connector
> login hardening (per-email throttle, no outbound mail to unknown addresses)
> + atomic rate limiter + response-metadata logging with 90-day retention +
> closed-task 409 on StoreData/StoreFiles + client app_context never honored;
> shared install_utils/pdf_utils/browser-harness/visibility helpers consumed
> by mopi/barakah/miki/good_event/good_npo/good_demo; mopi ptype-aware task
> permissions (Desk writes assignment-scoped for regular MoPi Users);
> payrexx least-privilege pay_invoice + exported shared HMAC signer;
> non_profit permission guards on payment helpers/doc methods, donor-rename
> stopped, certification module removed (with drop patch), chapter web pages
> deleted, shared ruff/pre-commit adopted with one-time reformat; good_demo
> conversion refusal for real accounts (repeat demo logins explicitly tested),
> marker-strict + docstatus-bound checkout tokens, Buzz role dropped,
> weekly account purge, reset pinned to the long queue; good_npo guest
> mutation stopped (comments instead), branding/footer ownership guards,
> dashboard chart fix, post-submit invoice writes removed, membership
> confirmation enqueued + resend-throttled, template surgery → one-time
> patches; good_event dead code/orphan dirs removed, esc()/provider-resolver
> consolidated, before_uninstall added (also miki, good_connector); bench
> AGENTS.md factual fixes. Decisions honored: no token-lifetime reductions
> anywhere; hub-visible response shapes pinned by contract tests, not unified.
> See AUDIT_REMEDIATION_WORKLIST.md for the item-by-item ledger.

## 1. Security — Fix Immediately

### 1.1 [HIGH] barakah_app: reminder emails leak one user's login token to all supplier portal users — VERIFIED
- `barakah_app/reminders.py:41` → `workflow_content.py:151-156`:
  `_get_supplier_login_url()` returns the **first** portal user's personal JWT
  login URL. `good_connector/reminder_runner.py:168-191` renders the template
  **once** with that shared context and sends the identical body to every
  recipient.
- Impact: with ≥2 portal users on a Supplier, users 2..n receive a working
  30-day login token for user 1 → portal account impersonation (task writes,
  file uploads).
- Fix: per-recipient rendering in the reminder runner (mirror the
  `recipient_contexts` mechanism `task_delivery.py:261-270` already uses), or
  drop the personal login URL from the shared reminder context. Effort M.

### 1.2 [HIGH/payment] good_npo: Payrexx gateway resolution prefers "Sandbox" over "Live" — VERIFIED
- `good_npo/checkout.py:133-135`: `for preferred in ("Sandbox", "Live"): ...`.
  On any site with both gateways configured, all guest donations silently
  route to the sandbox — money never collected. Also a demo assumption inside
  the "reusable" app.
- Fix: make the default gateway an explicit setting; never hardcode
  Sandbox-first. Effort S.

### 1.3 [HIGH] non_profit: guest PII disclosure via enumerable `donate_confirm` — VERIFIED
- `non_profit/www/donate_confirm.py:17-37`: `?donation=<name>` loads **any**
  Donation for guests with no ownership/token check and renders donor name +
  amount. Donation uses a sequential naming series → trivially enumerable.
  ilanga_app re-exposes the same page under its own routes
  (`ilanga_app/www/ilanga/en/donate_confirm.py`).
- Fix: random token param stored on the Donation, or session binding. Effort S–M.
- (New code, team-added fundraising flow — not legacy.)

### 1.4 [HIGH, conditional] non_profit: stored XSS in public Chapter page (legacy)
- `non_profit/.../chapter/templates/chapter.html:26,34`: `user.website_url`
  and `user.introduction` render unescaped (Frappe Jinja has no autoescape);
  any logged-in user can inject via `chapter.join()`. Only exploitable if a
  Chapter page is published — nothing in this bench uses Chapters.
- Fix: escape with `| e` + validate URL scheme, or delete the whole Chapter
  web layer (it's unused legacy; see Dead Code). Effort S.

---

## 2. Security — Medium (clean up soon)

### good_connector (the auth substrate — strongest app overall)
- **Login endpoint is an email relay / bomb vector** (`api/endpoints.py:66-77`):
  unknown emails get a "no account" email sent *to the attacker-supplied
  address*; known users can be inbox-bombed with login links. Only a 20/min/IP
  limit, no CAPTCHA (the app already ships one). Fix: CAPTCHA-gate + per-email
  throttle; drop the "not found" email.
- **PII at rest in Integration Request logs** (`api/helpers.py:184-218`):
  full request payloads and `doc.as_dict()` responses (names, phones, emails)
  logged on every portal action; only secret-shaped keys are redacted.
  GDPR-relevant. Fix: log metadata only, or restrict read perms + retention.
- **30-day JWT carried in URL query string** (`api/auth.py:13,101-103`):
  leaks via history/Referer/proxy logs; no revocation. Fix: shorter expiry or
  short-lived exchange token.
- **Rate limiter is non-atomic** (`api/helpers.py:162-177`): read-then-write
  race; use Redis `INCR` or `frappe.rate_limiter`. Effort S.
- **`app_context` is client-supplied** (`api/endpoints.py:372`): app scoping
  on the shared guest endpoint trusts the caller's claimed app (bounded by
  per-task access checks, but the bench's app-isolation rule is enforced only
  by the proxy apps).

### payrexx_integration (small and mostly excellent)
- **Webhook doesn't bind signing key to the target IR's gateway**
  (`payrexx_settings.py:192-261`): attacker with the *Sandbox* signing key can
  craft a confirmed webhook with `?gateway_name=Sandbox` against a *Live*
  Integration Request → invoice marked paid. Fix: assert the IR's stored
  gateway matches the settings row used for verification. Effort M.
- **`payment_success` lets the caller choose which credentials confirm**
  (`api.py:134-152`): `gateway_name` is attacker-controlled; settings should
  derive from the IR's own stored gateway. (Mitigated: creating a Settings row
  needs desk access.) Effort M.
- **Pay-by-email HMAC token never expires** (`api.py:44-58`): deterministic,
  no nonce/expiry; a forwarded link works forever. Documented accepted risk —
  consider folding an expiry window into the signed payload.
- `pay_invoice` runs guests as hardcoded `Administrator` (`api.py:126-128`)
  while the webhook path uses the configurable least-privilege user — align.

### non_profit
- **`payment_entry.py` whitelisted helpers read arbitrary docs without
  permission checks** (`custom_doctype/payment_entry.py:183,447`):
  `get_doc(dt, dn)` with caller-controlled doctype, returns financial fields.
  Fix: pin `dt == "Donation"` + `has_permission(throw=True)`. Effort S.
- **Write-action doc methods rely on framework read-check only**:
  `donation.send_thank_you`, `membership.generate_invoice` (creates+submits a
  Sales Invoice), `recurring_donation.create_next_donation` (inserts with
  `ignore_permissions`). Siblings (`mark_thank_you_sent`, receipt send)
  correctly call `self.check_permission("write")` — apply consistently. Effort S.
- **Guest can rename any Donor via the public donate form**
  (`www/donate.py:107-110`): existing donor matched by email gets
  `donor_name` overwritten from guest input (flows into receipts). Same
  pattern in good_npo: `fundraising.py:774-784,583-590,806-844` mutates
  existing Member/Donor name/language/address from unauthenticated input and
  re-sends invoice email (with login link) on every call. Fix in both: don't
  mutate existing master records from guest input. Effort M.
- `chapter.leave` allows state change over GET (add `methods=["POST"]`).
- Hardcoded personal email + manual commit in committed smoke script
  (`test_email_e2e.py:6`).

### mopi_app (+ good_connector shared path)
- **Completed history tasks remain mutable via StoreData/StoreFiles**
  (`good_connector/api/portal.py:144-154,974-1026`, mopi context): GetData
  correctly 409s on closed tasks, but the edit paths don't check
  `_is_closed_task` — violates the documented "completed history rows are
  read-only" rule; certificate eligibility derives from task state. Fix: add
  the closed-task guard in good_connector. Effort S.
- **`has_task_permission` ignores `ptype`** (`mopi_app/permission.py:36-44` +
  Task write grant in `setup.py:259`): every MoPi User can *write* every
  MoPi-parented task → can mark colleagues' trainings complete. Decide the
  trust model; restrict write to assigned tasks if unintended. Effort M.
- **Unauthenticated short-circuit actions write log rows**
  (`mopi_app/api.py:35-42`): `GetStartableProcesses`/`StartProcess` answer
  before token check and rate limit, inserting an Integration Request per
  anonymous request → log flooding. Effort S.
- `_file_url_to_data_uri` (`training.py:618-635`) inlines any `File` by URL
  without permission check → private-file exfiltration via certificate HTML
  for desk users; certificate wkhtmltopdf runs with
  `--enable-local-file-access` over non-autoescaped Jinja (`training.py:701-749`).
  miki's equivalent uses `--disable-local-file-access` — copy that. Effort S–M.

### good_demo
- **Pre-existing real accounts irreversibly converted to demo users**
  (`api.py:392-411`): anything but System Managers / NPO managers gets
  `good_demo_user = 1` + demo roles; next reset disables them and their new
  records get demo-marked → deleted. HOW_TO.md already documents a manual
  repair procedure, i.e. this bites in practice. Fix: refuse to convert
  existing non-demo accounts. Effort S.
- **Dummy-checkout HMAC token over-broad and non-expiring**
  (`checkout.py:252-259,366-370`): validity check accepts any donation with
  the GoodNPO company/campaign (demo marker only third fallback); token has no
  expiry/docstatus binding. On a mixed site guests could mark real donations
  paid. Fix: require the demo marker; bind docstatus/date into the HMAC. Effort S.
- `confirm_demo_access` has no rate limit (token is 48-char secrets-based, so
  brute force impractical — DoS hygiene only); demo users/signups accumulate
  forever (add a purge job); demo role set includes `Buzz User` which is
  outside all three containment layers (privacy/marker/reset) — drop or extend
  coverage; `_can_issue_demo_login_link` is a stub returning True.

### Cross-cutting security/process
- **SEMGREP_OVERRIDES.md drift in 4 apps**: good_npo documents an annotation
  that doesn't exist and omits two that do; ilanga is missing the
  `help_articles.py` traversal entry and references a renamed function;
  miki documents a geo.py override that moved to good_connector;
  good_connector's geo.py annotations aren't documented at all. The bench rule
  is "every nosemgrep documented" — resync all four. (mopi, barakah,
  good_event, good_demo, non_profit, payrexx verified accurate.)
- **Hub webhook auth inconsistency**: unauthenticated `GetStartableProcesses`
  returns a token-gated response in barakah, the process name in miki
  (`miki_app/portal.py:112-113`), and `[]` in mopi; unauthorized responses are
  HTTP 400 "Wrong Token" (barakah) vs HTTP 200 `{}`/plain-string (miki).
  Pick one contract, pin it with API-contract tests.

---

## 3. Redundancy (cross-app)

| # | Duplication | Where | Size | Recommendation |
|---|---|---|---|---|
| 1 | Install boilerplate: `before_uninstall` sidebar clear, `_ensure_doctype_permission`, `ensure_desk_role`, system-user repair, `_sync_desk_records`, `_set_system_setting` | 7–9 apps' `setup.py` | ~15–60 lines each ×N, **with behavioral drift** (barakah's `_ensure_doctype_permission` writes perms on every migrate; mopi/barakah `_drop_doctype_permission` strategies differ, one risks dev-mode doctype re-export) | Ship `good_connector/install_utils.py`; adopt the miki/good_event variant as canonical. Effort M, risk low |
| 2 | **Missing `before_uninstall`** in miki_app, good_event, good_connector despite shipping Workspace Sidebar fixtures | `miki_app/hooks.py` (none), `good_event/hooks.py:133` (commented out), `good_connector/hooks.py` (none) | — | Add the standard 15-line hook. Dev-mode uninstall currently deletes the sidebar JSON from the working tree — exactly the failure the bench docs warn about. **AGENTS.md:456 wrongly claims miki has it.** Effort S |
| 3 | Playwright E2E harness (~18 helper functions: bench-exec, site-config, hub token, login, fields) | mopi/barakah/miki `tests/test_e2e_playwright.py` (+partial good_event/good_demo) | ~600–900 duplicated lines, 65–95% identical | `good_connector/tests/browser_harness.py`, parameterized by NGO id. Effort M, test-only risk |
| 4 | `_merge_pdf_bytes` + `_pdf_page_has_content` | good_event `booking_confirmation.py:151`, miki `correspondence.py:463`, good_npo `pdf_utils.py:182` | ~30 lines, **byte-identical ×3** | Move to good_connector; re-export. Effort S |
| 5 | ilanga `dashboard.py` is a stale fork of good_npo's | `ilanga_app/dashboard.py` vs `good_npo/dashboard.py` | 8 shared functions; drift: ilanga's `mark_thank_you_sent` doesn't stamp `thank_you_sent_on/by` | Move the donation-dashboard data layer into non_profit (owns Donation + the now-standard `thank_you_sent` field); thin wrappers in both apps. Effort M |
| 6 | Hub webhook local handlers: 3 patterns for token resolution, error shapes, logging | barakah/miki `portal.py` vs mopi (fully delegated) | ~200 lines each | Extract a `dispatch()` skeleton in good_connector that standardizes auth/error/logging; app handlers plug in. Needs hub contract tests first (miki's HTTP-200 `{}` responses may be load-bearing for the legacy hub). Effort M, risk med |
| 7 | Substrate knows its consumers: good_connector hardcodes mopi/barakah/miki doctypes | `good_connector/api/portal.py:42-58,311-321` (14 mopi refs incl. a `MoPi Training Module` query) | — | Extend the existing `good_connector_portal_file_targets` hook pattern to a per-app context config hook. Effort M, security-relevant — keep contract tests green |
| 8 | Email Account footer + Switzerland Address Template fought over by two apps | `good_npo/email_branding.py:29-47` vs `miki_app/correspondence_defaults.py:2091-2115`; `good_npo/setup.py:878` vs `miki_app/setup.py:1962` | both overwrite every outgoing account's footer on every migrate; migrate order decides the winner | Make footer application opt-in/targeted; Switzerland template belongs in non_profit. Effort S–M |
| 9 | HMAC link-signer cloned | `payrexx_integration/api.py:31-58` vs `good_demo/checkout.py:366-391` | byte-identical `_signing_key` | Export `sign_reference`/`verify_reference`; keep payload composition identical for in-flight links. Effort S |
| 10 | Two Swiss QR-bill engines | good_connector `qr_bill.py` (chqr, QRR/SCOR check digits) vs non_profit `swiss_qrbill.py` (qrbill lib, no reference handling) | — | Structurally constrained (non_profit can't import good_connector). Minimum: add a payload-parity test. Effort S |
| 11 | miki `_log_failed_integration_request` re-implements good_connector `_log_request` | `miki_app/api.py:125-138` | 14/16 lines | Add `status=`/`error=` params upstream; delete the copy. Effort S |
| 12 | good_npo demo-bank machinery (~160 lines) used only by its own tests | `good_npo/setup.py:407-568` | — | Move to good_demo. Effort S |

**Notable intra-app duplication:**
- good_connector: 3 near-duplicate Email-Template render helpers
  (`portal_helpers.py:263`, `task_delivery.py:203`, inline in `api/auth.py`);
  two byte-identical `set_user` context managers (`workflow_support.py:61-86`);
  JWT decoded twice per app action (`api/portal.py:655,683`).
- good_event: `esc()` ×4, three divergent confirmed-attendee-count
  implementations + one dead one; 5 dead helpers; 6 orphan empty doctype dirs;
  one unregistered patch; duplicate `backfill_event_booking_titles()` call
  (`setup.py:55-56`); provider-hook resolution boilerplate repeated 6×.
- miki: `receivables.py` duplicates `correspondence.py`'s render/email/QR
  helper layer (drift risk between declaration and generic invoice paths).
- good_demo: `_is_demo_user` ×5, `_has_field` ×6 — the security-critical
  predicate should exist once; two `escapeHtml` declarations in the desk JS
  where the **weaker one wins** by hoisting.
- good_npo: dead helpers (`_link_member_contact_to_record`,
  `ensure_goodnpo_address_metadata` no-op, `_ensure_docfield_property`,
  boot video plumbing), verbatim address-linker pair, `boot_session` +
  `extend_bootinfo` registered to the same fn → runs twice per boot (same bug
  in good_demo `hooks.py:38-39`).
- barakah: dead `on_task_update` duplicate of the substrate hook; dead
  unauthenticated `update_barakah_process` (`services.py:665` — delete it);
  Aqeeqa/Well copy-paste pairs; local visibility pre-filter re-implements
  `portal_email_can_access_task` (the exact drift AGENTS.md warns about).
- ilanga: second, undocumented help pipeline (`help_articles.py`) duplicating
  good_help's sync into the legacy `Help Article` doctype — same markdown gets
  published twice when good_help is installed; pick one channel.

**Dead code worth deleting (high confidence):**
- non_profit: Certification module + 2 public web forms (unused by any
  dependent app), join/leave_chapter template pages, broken `Chapter.enable`,
  `hooks.py:38` doctype_js → nonexistent file, `config/docs.py`. Caveat:
  other deployments of the fork might use Certification — gate on a release note.
- good_event: the 6 empty doctype dirs, `migrate_event_master_care_forms.py`,
  the 5 dead helpers.
- good_help: `_creation_from_order`/`installed_on_from_order` kept alive only
  by their own tests.

---

## 4. Simplicity / taste

Worst offenders vs. the 100–300-line file / ~10-line function guidance:

| File | Lines | Worst function |
|---|---|---|
| good_event `services/public_pages.py` | 2,789 | `_ui_text_json` 590 (translation blob → move to JSON data files), `_registration_script_html` 493 (inline JS → static asset) |
| good_demo `www/demo.html` | 2,576 | ~700-line inline JS |
| miki `correspondence_defaults.py` | 2,192 | three 140–172-line HTML builders |
| miki `setup.py` | 1,979 | — |
| good_npo `fundraising.py` | 1,771 | `_get_or_create_membership_invoice` ~99 |
| good_event `api.py` | 1,773 | — |
| good_demo `reset.py` | 1,643 | `seed_demo_data` ~234 |
| good_connector `api/portal.py` | 1,045 | `_handle_app_action_impl` ~365 — the security-critical dispatcher; extract a per-action handler registry so every branch's auth is verifiable |
| non_profit `custom_doctype/payment_entry.py` | 542 | wholesale ERPNext fork incl. dead Fees/Student/Gratuity branches and a latent `NameError` for `party_type="Member"`; reduce to a Donor-only delta + `super()` |

**String-surgery migrations running forever in setup** (convert to one-time
patches, keep setup create-if-missing):
- good_npo `setup.py:1370-1445` (~15 chained `str.replace` on a live Email
  Template every migrate) and `fundraising.py:1636-1665` (regex-rewrites
  rendered email HTML).
- good_demo `setup.py:363-490` (color/wording replacements on the German
  confirmation template).
- non_profit `fundraising_setup.py:203-213` unconditionally overwrites the
  thank-you template every migrate — operators lose edits (bench pattern is
  "never overwritten on re-install").

**Hidden/heavy work in hooks:**
- barakah `setup.ensure_setup()` force-reloads 3 DocTypes with
  `reset_permissions=True` on every migrate (the documented deadlock cause)
  plus a full-table `get_doc`-per-task N+1 rescan; split cheap idempotent core
  from one-time reconciliation. Also runs up to 3× per migrate (two patches
  call it + after_migrate).
- good_demo `after_migrate` runs the full demo seed (creates/submits
  invoices); a failed seed aborts migrate — enqueue or flag-gate.
- good_npo setup rebrands the whole site (Website Settings, every Email
  Account's footer) unconditionally on every migrate.
- good_npo `_queue_membership_confirmation` doesn't queue — it runs 2–3
  wkhtmltopdf renders + invoice submit + sendmail inline in the guest request
  (`fundraising.py:1580`). The donation path does this correctly via enqueue.

**Correctness bugs found along the way (not security):**
- good_npo dashboard monthly chart aggregates only `limit_rows` (≤30) rows
  for the whole year → wrong totals (`dashboard.py:171-177`); use the
  existing permission-aware SUM helpers.
- good_npo mutates a **submitted** Sales Invoice via `db.set_value`
  (currency/conversion_rate/cost_center) without GL re-posting
  (`fundraising.py:1136-1164`).
- good_npo `_insert_doc_with_retry` rolls back the whole request transaction
  then retries only the Donation insert → retry can never succeed
  (`fundraising.py:299-303`); use savepoints.
- ilanga guest donate routes copy non_profit's POST flow but drop the captcha
  wiring → forms break for guests whenever a captcha site key is configured
  (`www/ilanga/en/donate.py`).
- ilanga has an undeclared hard runtime dependency on good_connector
  (`dashboard.py:9-27` raises plain ImportError in a whitelisted endpoint;
  `hooks.py` requires only non_profit).

---

## 5. Frappe-way conformance

**Clean across the board (verified per app):** no `pypika` imports; no
`json.loads` on request data; no `frappe.db.commit()` in doc-event or
install/migrate hooks (commits confined to documented scheduler/migration
scripts); `cint`/`cstr`/`flt` mostly used; `frappe.throw + frappe._()`
standard; all whitelisted functions type-hinted; every doctype has a real
controller; `create_custom_fields` in both install hooks with exists guards.

**Drift items:**
- **non_profit is the tooling outlier**: no `pyproject.toml`/ruff at all,
  4-space indents, stale pre-commit (v4.0.1, no ruff/prettier hooks).
  AGENTS.md's "all custom apps share the same ruff config" is false for it.
  workflow_visualizer has no `.prettierrc` (required per AGENTS.md);
  good_help's drifts (`trailingComma`).
- mopi: `bool(int(...))` instead of `cint` across ~10 whitelisted signatures;
  `enqueue_after_commit=True` hardcoded instead of `not frappe.flags.in_test`
  (`mopi_training_module.py:190`); deadlock-retry loop copied 3×.
- ~30 `except Exception: pass` silent swallows in miki (and 13 in
  good_event) — add `frappe.log_error` or a comment where intentional.
- barakah/payrexx/good_demo import underscore-private symbols across app
  boundaries (`_check_token_contract`, `_parse_payload`, `_as_automation_user`,
  `_get_or_create_membership_invoice`) — export public wrappers.
- good_npo donation path re-implements local Contact creation instead of
  `good_connector.identity_matching` (the membership path does it right).
- good_help `sync.py:189` file opened without context manager; N+1
  `get_doc`-per-article in `api.get_help` (3 queries per article).
- ilanga `mark_thank_you_sent` writes the field its own AGENTS.md forbids
  writing directly.

**Docs drift (bench AGENTS.md + app docs):**
- AGENTS.md:456 claims miki_app ships the `before_uninstall` sidebar guard —
  it doesn't (finding 3.2).
- AGENTS.md:84 says workflow_visualizer has no app-local AGENTS.md — it does
  (and it's good).
- Dependency graph omits miki_app's `payrexx_integration` requirement
  (`miki_app/hooks.py:10`).
- ilanga AGENTS.md/DOCUMENTATION.md describe a demo seeder that doesn't
  exist, claim "no test suite" (one exists), and don't mention
  `help_articles.py` or `mark_thank_you_sent`.

---

## 6. What's done well (keep doing this)

- **good_connector JWT/auth**: algorithm pinned to HS256 on encode *and*
  decode, exp/nbf/iat set, secret from site config/password field,
  `hmac.compare_digest` for the API password, `set_user` always in
  try/finally. Strong 668-line API/security contract test suite.
- **good_event guest surface**: server-authoritative pricing with row locks
  on coupons, published/visibility/capacity checks, escaping discipline,
  path-traversal and open-redirect guards all verified correct, plus a
  regression test enforcing miki/buzz independence.
- **good_demo containment engineering**: hashed tokens at rest, secrets-based
  passwords never emailed, strictly marker-filtered reset with regression
  tests asserting unmarked data is never claimed.
- **payrexx**: raw-body HMAC verification with compare_digest, Password
  fieldtypes + `get_password`, server-side payment confirmation before
  completing IRs, same-origin redirect guard.
- **non_profit rehabilitation**: Razorpay stack and 80G/PAN PII fully
  removed, raw SQL eliminated, donate flow hardened (CAPTCHA, rate limit,
  consent, double-gated mock pay).
- Exceptional test volume for apps of this kind (Playwright e2e + API
  contract suites in mopi/barakah/miki/good_demo/good_event).

---

## 7. Quick wins (low-risk, do anytime)

1. Add `before_uninstall` to miki_app / good_event / good_connector; fix the
   two AGENTS.md factual errors. (S)
2. good_npo: flip Sandbox/Live preference to a setting. (S)
3. non_profit: token-gate `donate_confirm`; pin `dt` + add `has_permission`
   in `payment_entry.py`; `check_permission("write")` on the four write-action
   doc methods; `methods=["POST"]` on `chapter.leave`. (S each)
4. good_connector: CAPTCHA the login endpoint; atomic rate limiter; merge the
   two `set_user` context managers; decode the JWT once. (S)
5. mopi: closed-task guard for StoreData/StoreFiles in good_connector. (S)
6. good_demo: refuse demo-conversion of existing accounts; require the demo
   marker in `_is_good_demo_checkout_donation`. (S)
7. Move `_merge_pdf_bytes` to good_connector; parameterize `_log_request`;
   delete the dead code lists in §3. (S)
8. Resync the four stale SEMGREP_OVERRIDES.md files. (S)
9. Fix barakah `_ensure_doctype_permission` (skip-if-unchanged) now, ahead of
   any consolidation. (S)
10. Tooling: pyproject+ruff for non_profit, `.prettierrc` for
    workflow_visualizer. (S)

## 8. Roadmap

**Fix immediately:** §1 (barakah token leak, Sandbox-first, donate_confirm,
chapter XSS-or-delete), payrexx webhook gateway binding.

**Clean up soon:** §2 mediums (good_connector login relay + log PII, mopi
permission model + closed-task edits, good_demo conversion/token scope, guest
mutation of Member/Donor, payment_entry.py perms); SEMGREP/docs resync;
quick-wins list.

**Improve later (structural):** install_utils consolidation; shared Playwright
harness; hub-webhook dispatch skeleton + one auth/error contract (contract
tests first); good_npo demo-content extraction into good_demo; splitting the
2k-line files (public_pages, correspondence_defaults, fundraising, reset);
converting string-surgery setups to patches; non_profit PaymentEntry fork →
minimal delta. (~~ilanga dashboard/help-pipeline dedup~~ — out of scope, PoC.)

---

*Method note: 10 per-app agents + 1 cross-app agent, all read-only; every
finding cites file:line evidence read from the code. The barakah token leak,
Sandbox-first routing, and donate_confirm enumeration were re-verified
directly. Confidence levels are preserved from the per-app reports where
findings were marked uncertain.*
