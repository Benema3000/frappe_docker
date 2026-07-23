# End-to-End Testing

This is the canonical browser and end-to-end testing guide for the Frappe v16
bench under `/workspace/development`. App documentation should keep only
app-specific details and link here for shared policy.

## Recommendation

Use **Playwright as the default browser automation tool** for custom apps in
this bench.

Playwright is the best fit because it provides reliable browser contexts,
automatic action waiting, accessible locators, downloads, request/API support,
stored authentication, traces, screenshots, video, and strong desktop/mobile
coverage. Both Python Playwright and `@playwright/test` are already used here.

Playwright is not the only test layer:

| Question                                                             | Preferred test                                                    |
| -------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Pure rules, document lifecycle, permissions, APIs, jobs              | Frappe `IntegrationTestCase` / `UnitTestCase`                     |
| Critical journey through a real browser                              | Playwright                                                        |
| Layout, routing, browser storage, upload/download, responsive UI     | Playwright                                                        |
| Email/PDF workflow                                                   | Playwright trigger plus Email Queue and attachment/PDF assertions |
| Real Payrexx, inbox, hosted hub, CAPTCHA, or another external system | Explicit opt-in Playwright UAT                                    |
| Upstream Frappe or Builder browser regressions                       | Their existing Cypress suites; do not convert or patch upstream   |
| Exploratory usability, accessibility, or visual approval             | Manual review, optionally supported by Playwright evidence        |

For new standalone browser suites, prefer TypeScript and `@playwright/test` for
its fixtures, assertions, projects, retries, traces, and reports. Extend the
existing Python runners when the flow is tightly coupled to Frappe setup helpers
or is already part of a Python `bench execute` harness. Do not rewrite working
Python suites merely to standardize the language.

## Test Levels

Keep these result classes distinct:

1. **Server E2E** exercises several Frappe layers without a browser. It is fast,
   deterministic, and belongs in normal app tests.
2. **Local browser regression** drives a local disposable/dev site. It may seed
   records but should suppress external side effects by default.
3. **Hosted UAT** drives a deployed site or the hosted self-service hub. It is
   environment evidence, not a substitute for local regression coverage.
4. **External integration E2E** sends real email or reaches a payment/CAPTCHA
   provider. It must be opt-in and report exactly which external boundary was
   proven.

Do not call a direct API-only check a browser E2E. Hybrid tests are useful, but
reports must distinguish browser assertions from backend setup/verification.

## Safety Rules

- Run only one mutating browser or `bench run-tests` suite against a site at a
  time. Parallel OpenCode sessions and parallel test commands have caused data
  collisions, duplicate email, and MariaDB deadlocks.
- Use the smallest relevant suite first. Do not retry an entire journey after a
  late failure until you inspect the records already created.
- Use unique test data and explicit app markers. Never clean up broad sets of
  unmarked records.
- Preserve and restore modified site config, Single values, CAPTCHA bypasses,
  API URLs, tenant IDs, templates, and `mute_emails` in `finally`.
- Keep real email, payment, SMS, and production/hosted mutations off by default.
  Name the opt-in environment variable and target environment in the run notes.
- Put generated evidence under `/tmp/opencode/<run-name>` unless the existing
  suite has a documented artifact directory. Do not treat `.playwright-mcp/`
  snapshots as a maintained test suite.
- Never store passwords, login links, JWTs, CAPTCHA tokens, provider secrets, or
  Playwright auth state in tracked files or reports.
- New or changed helpers that return `{ok: false}`, `{"skipped": ...}`, or
  another failure object must make the test command fail unless the skip is
  explicit and valid. Some current Good Event focused runners and MiKi cases do
  not yet enforce this, so inspect their returned output; process exit 0 alone
  does not prove every advertised case ran.

## Local Setup

Run Python Playwright with the bench interpreter, not system Python:

```bash
cd /workspace/development/frappe-bench
env/bin/python -m pip install playwright
PLAYWRIGHT_BROWSERS_PATH=/home/frappe/.cache/ms-playwright \
  env/bin/python -m playwright install chromium
bench serve --port 8000
```

The Python dependency is currently an environment prerequisite rather than a
declared dependency of every consuming app. A browser package alone may not be
enough on a new machine; install the required Linux browser libraries when
Chromium reports missing shared objects.

Useful defaults:

```bash
export FRAPPE_SITE=development16.localhost
export FRAPPE_URL=http://127.0.0.1:8000
export BENCH_PATH=/workspace/development/frappe-bench
export PLAYWRIGHT_LOCALE=en-US
```

Use `127.0.0.1` when `.localhost` DNS fails. Suites that access a named site
through an IP must preserve Frappe site routing, usually with the suite's
existing `X-Frappe-Site-Name` browser-context header. Check the configured
`host_name` separately when PDF generation calls back into the site.

For TypeScript projects, install from the project's own lock file and scripts.
Payrexx uses npm:

```bash
npm ci
npx playwright install chromium
npm test
```

Buzz and Wiki use Yarn:

```bash
yarn install --frozen-lockfile
yarn playwright install chromium
yarn test:e2e
```

Use `npm ci` in CI when the project's lock file supports it. Keep each existing
project's package manager and lock file; do not replace them during an E2E fix.

## Current Suite Inventory

### Custom Python Playwright

Run these from `frappe-bench` with `bench execute`, not `bench run-tests`:

| Owner          | Entrypoint                                    | Main scope                                                                                                                                                                            |
| -------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MoPi           | `mopi_app.tests.test_e2e_playwright.run`      | Desk, tasks, training, certificates, portal/hub, files, news/links                                                                                                                    |
| Barakah        | `barakah_app.tests.test_e2e_playwright.run`   | Public order forms, local Aqeeqa/Well portal contracts, direct file APIs, news/links, and optional hosted file-page evidence; hosted failures may be reported without failing the run |
| MiKi           | `miki_app.tests.test_e2e_playwright.run`      | Declaration, billing/dunning, Desk, local portal/hub contracts, files, correspondence; not the separate hosted-browser drive                                                          |
| Good Event     | `good_event.tests.test_e2e_playwright.run`    | Native registration, private/organization cases, coupon, mobile, persistence, pre-event package                                                                                       |
| Good Demo      | `good_demo.tests.test_e2e_playwright.run`     | Signup, membership, donation, dummy checkout, email queue, mobile Desk/help                                                                                                           |
| Good NPO       | `good_npo.tests.test_e2e_playwright.run`      | Delegates to the Good Demo flow                                                                                                                                                       |
| Good Connector | `good_connector.tests.real_hub_user_flow.run` | Legacy real-email navigation and direct portal submissions across MoPi, Barakah, and MiKi; it does not assert authenticated hub content and is not release evidence                 |
| Good Connector | `python -m good_connector.tests.hosted_auth_qa --mode full` | Strict real-email, Frappe token-contract, and identity-bound hosted `/rest/session` proof; run with the bench virtualenv and protected environment variables                         |

Good Event and Good Demo can start a local server when needed. The other
consumer runners expect `FRAPPE_URL` to be reachable. Existing MoPi, Barakah,
and MiKi suites write screenshots under their app directories; new ad hoc
evidence should use `/tmp/opencode/<run-name>`.

Examples:

```bash
FRAPPE_URL=http://127.0.0.1:8000 \
  bench --site development16.localhost execute \
  good_event.tests.test_e2e_playwright.run

bench --site development16.localhost execute \
  mopi_app.tests.test_e2e_playwright.run

BARAKAH_PLAYWRIGHT_ONLY_PUBLIC_FORMS=1 \
  bench --site development16.localhost execute \
  barakah_app.tests.test_e2e_playwright.run
```

`MIKI_SKIP_HUB_TESTS=1` removes cases whose suite name contains `hub`; it is not
a local-versus-hosted selector. The main MiKi `run()` does not call the separate
hosted Chromium driver. Invoke that explicitly when needed and inspect the
returned `error`/`steps` object because it does not currently fail every blocked
stage:

```bash
bench --site development16.localhost execute \
  miki_app.tests.test_e2e_playwright.hub_e2e_drive
```

Additional Good Event entrypoints are:

```text
good_event.tests.test_e2e_playwright.run_theme_color_test
good_event.tests.test_e2e_playwright.run_desk_field_key_filter
good_event.tests.test_e2e_playwright.run_translation_unit_layout
good_event.tests.test_e2e_playwright.run_primary_attendee_remove_button
```

`run_public_booking_form` is currently only an alias for the complete `run()`
suite, not a focused smoke.

Good Demo also exposes
`good_demo.tests.test_e2e_playwright.run_signup_flow`.

`PLAYWRIGHT_REAL_EMAIL=1` enables real email in the consumer suites that honor
it. The Good Connector real-hub runner intentionally does not mute email. Its
fallback can synthesize a login token when sent-message MIME is unavailable,
and its browser helper records only URL/title/screenshot after navigation. A
green run is therefore not proof of delivered email body content or an
authenticated hosted-hub session.

Use `good_connector.tests.hosted_auth_qa` for strict authentication evidence.
`--mode full` signs into the deployed Frappe site, requests the normal guest
login endpoint, and accepts only a newly retained `Sent` Email Queue addressed
to the controlled identity. `--mode authenticate` accepts a magic link copied
from the operator-controlled inbox and does not require Frappe Desk credentials.
Both modes validate the exact HTTPS Frappe/portal host allowlists, link query
shape, NGO, Frappe token response, and identity returned by the hosted
`/rest/session`; HTTP 200 without the expected identity fails. The result file
contains only a recipient hash and redacted booleans/record names, uses mode
`0600`, and rejects credentials, JWTs, magic links, cookies, and query-bearing
URLs before persistence.

Run from `frappe-bench` with its virtualenv. Supply values through a protected
process environment, never command arguments or tracked files:

```bash
set +x

GOOD_CONNECTOR_HOSTED_QA_FRAPPE_URL=https://<frappe-host> \
GOOD_CONNECTOR_HOSTED_QA_FRAPPE_ALLOWED_HOSTS=<frappe-host> \
GOOD_CONNECTOR_HOSTED_QA_PORTAL_URL=https://<portal-host> \
GOOD_CONNECTOR_HOSTED_QA_PORTAL_ALLOWED_HOSTS=<portal-host> \
GOOD_CONNECTOR_HOSTED_QA_RUN_ID=GC-AUTH-E2E-YYYYMMDD-<random> \
GOOD_CONNECTOR_HOSTED_QA_EMAIL="${GOOD_CONNECTOR_CONTROLLED_EMAIL}" \
GOOD_CONNECTOR_HOSTED_QA_NGO=<ngo-id> \
GOOD_CONNECTOR_HOSTED_QA_USER="${GOOD_CONNECTOR_HOSTED_USER}" \
GOOD_CONNECTOR_HOSTED_QA_PASSWORD="${GOOD_CONNECTOR_HOSTED_PASSWORD}" \
./env/bin/python -m good_connector.tests.hosted_auth_qa --mode full

GOOD_CONNECTOR_HOSTED_QA_FRAPPE_URL=https://<frappe-host> \
GOOD_CONNECTOR_HOSTED_QA_FRAPPE_ALLOWED_HOSTS=<frappe-host> \
GOOD_CONNECTOR_HOSTED_QA_PORTAL_URL=https://<portal-host> \
GOOD_CONNECTOR_HOSTED_QA_PORTAL_ALLOWED_HOSTS=<portal-host> \
GOOD_CONNECTOR_HOSTED_QA_RUN_ID=GC-AUTH-E2E-YYYYMMDD-<random> \
GOOD_CONNECTOR_HOSTED_QA_EMAIL="${GOOD_CONNECTOR_CONTROLLED_EMAIL}" \
GOOD_CONNECTOR_HOSTED_QA_NGO=<ngo-id> \
GOOD_CONNECTOR_HOSTED_QA_LOGIN_URL="${GOOD_CONNECTOR_INBOX_LOGIN_URL}" \
./env/bin/python -m good_connector.tests.hosted_auth_qa --mode authenticate
```

Keep shell tracing disabled for the whole invocation. The runner removes
Playwright's `DEBUG` and `PWDEBUG` variables inside its process before opening
the secret-bearing URL, so API debug logging cannot print the magic link.

MoPi, Barakah, and MiKi share
`apps/good_connector/good_connector/tests/browser_harness.py`. Add shared Desk,
hub, settings, or restoration behavior there rather than copying helpers into
all three apps.

### TypeScript Playwright

| Project             | Directory                             | Command         | Notes                                                                                               |
| ------------------- | ------------------------------------- | --------------- | --------------------------------------------------------------------------------------------------- |
| Payrexx Integration | `apps/payrexx_integration/playwright` | `npm test`      | Chromium, one worker, optional existing Good Event booking email check; no real provider round trip |
| Buzz                | `apps/buzz`                           | `yarn test:e2e` | Upstream/off-limits; setup projects and stored auth; one worker                                     |
| Wiki                | `apps/wiki`                           | `yarn test:e2e` | Upstream-style app; setup project and stored auth                                                   |

Payrexx example:

```bash
cd /workspace/development/frappe-bench/apps/payrexx_integration/playwright
npm install
npx playwright install chromium
PLAYWRIGHT_BASE_URL=http://127.0.0.1:8000 npm test

TEST_BOOKING_NAME=<existing-good-event-booking> \
  TEST_PAYREXX_SETTINGS=<existing-payrexx-settings-name> \
  PLAYWRIGHT_BASE_URL=http://127.0.0.1:8000 npm test
```

The settings spec defaults to a `Payrexx Settings` row named `Sandbox`; set
`TEST_PAYREXX_SETTINGS` when the configured row has another name.

Delete the generated `auth.json` when a cached Payrexx Desk session is stale.
Buzz and Wiki have browser CI. The custom Python suites and Payrexx project are
not currently equivalent CI gates.

### Non-Playwright E2E

- `mopi_app.tests.test_e2e_major_processes` is server-side portal/task/file
  lifecycle coverage.
- `miki_app.tests.test_end_to_end` is server-side MiKi lifecycle coverage.
- Frappe and Builder contain upstream Cypress suites. Keep using their native
  commands when validating upstream behavior; both apps are off-limits here.
- Files named `test_email_e2e.py` are manual/real-email helpers, not safe default
  browser regression suites. Read their side effects before running them.

## Production Readiness Coverage

The archived UAT workbooks are requirement sources, not current execution
reports. Reusable cases were taken from
[`good_event_UserTesting_FRAPPE.xlsx`](archived/testfeedback/good_event_UserTesting_FRAPPE.xlsx),
[`miki_app_UserTesting_FRAPPE.xlsx`](archived/testfeedback/miki_app_UserTesting_FRAPPE.xlsx),
and [`TODO_GV_AUDIT.md`](archived/testfeedback/TODO_GV_AUDIT.md). Historical
pass/fail cells describe the system tested at that time and must not be copied
into a current release report without a new run.

| Product area                                                                                     | Automated local evidence                                                                                                                                                                                 | Current classification                                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Good Event registration, localized validation, input limits, coupon, mobile, persistence         | [`test_e2e_playwright.py`](frappe-bench/apps/good_event/good_event/tests/test_e2e_playwright.py), [`test_good_event.py`](frappe-bench/apps/good_event/good_event/tests/test_good_event.py)               | Hosted DE/FR/IT matrix, CAPTCHA success/failure UI, validation, catalogue, mobile, and transient organization intent passed by 2026-07-21. Controlled-recipient ticket PDF opening/ICS import and an exact event-scoped valid-coupon browser preview passed on 2026-07-22; the coupon/template fixtures were fully removed. |
| Good Event capacity overflow and real Waitlisted draft creation                                  | [`test_e2e_playwright.py`](frappe-bench/apps/good_event/good_event/tests/test_e2e_playwright.py), [`test_event_status.py`](frappe-bench/apps/good_event/good_event/tests/test_event_status.py)           | Hosted five-confirmed/two-waitlisted, cancellation, capacity release, and promotion matrix passed by 2026-07-21. |
| Good Event linked venue translation on detail/registration/list rendering                        | [`test_language_contract.py`](frappe-bench/apps/good_event/good_event/tests/test_language_contract.py), [`test_e2e_playwright.py`](frappe-bench/apps/good_event/good_event/tests/test_e2e_playwright.py) | Hosted DE/FR/IT catalogue/detail/registration visual and route checks passed by 2026-07-21. |
| Good Event organization invoice, external delivery, private PDF/QR, and least privilege           | [`test_good_event.py`](frappe-bench/apps/good_event/good_event/tests/test_good_event.py), [`test_event_permissions.py`](frappe-bench/apps/good_event/good_event/tests/test_event_permissions.py), [`test_invoice_billing_address.py`](frappe-bench/apps/good_event/good_event/tests/test_invoice_billing_address.py) | Hosted run `GE-FIN-E2E-20260723-b72e4f19` passed with a Good Event Manager-only operator: confirmed/submitted Booking, submitted positive/outstanding Good Event Sales Invoice, sent Email Queue and real Mailinator delivery containing the Payrexx link, persisted private two-page invoice/Swiss-QR PDF, run-owned invoice read, submitted-invoice write denial, unrelated-invoice read denial, and Payment Entry access denial. Exact teardown completed with no User, Customer, Contact, Address, Booking, Attendee, Sales Invoice, Email Queue, or public-inbox residue; mode-`0600` evidence contains only hashed recipient identity. The temporary finance recovery API used for this one acceptance campaign was removed in Good Event `16.3.9`; the pre-existing organization QA gate was reset to `0` and verified fail-closed with HTTP `403`. |
| MiKi canonical portal fields, archived field limits, normalization, non-persistence on rejection | [`test_portal_field_contract.py`](frappe-bench/apps/miki_app/miki_app/tests/test_portal_field_contract.py), [`test_e2e_playwright.py`](frappe-bench/apps/miki_app/miki_app/tests/test_e2e_playwright.py) | Hosted 12-positive plus three expected-negative matrix complete by 2026-07-21. Fix `b092307`/16.5.4 passed all 39 hosted-QA server tests and all 11 portal-user synchronization tests locally. Post-deploy shared-role run `KIBE-E2E-20260722-5c29198f` passed the complete lifecycle and exact cleanup with fixture stabilization disabled. |
| MiKi workflow, correspondence queue, invoice, QR SVG, Dunning, portal files                      | [`test_end_to_end.py`](frappe-bench/apps/miki_app/miki_app/tests/test_end_to_end.py), [`test_e2e_playwright.py`](frappe-bench/apps/miki_app/miki_app/tests/test_e2e_playwright.py)                       | All 12 positive hosted scenarios completed portal, review, invoice, Reminder/Dunning 1/Dunning 2, payment, closure, and exact cleanup. Identity-preserving run `KIBE-E2E-20260722-828480dd` additionally passed direct and hosted-wrapper PDF downloads after invoice and again after payment in one portal session, then deleted 37 exact records. `/rest/filelist` remained stale at both checkpoints because of its 20-minute token cache; direct `GetFileList` and all exact-file/download paths passed. |
| Good Event Payrexx checkout                                                                     | [`test_payrexx_settings.py`](frappe-bench/apps/payrexx_integration/payrexx_integration/payrexx_integration/doctype/payrexx_settings/test_payrexx_settings.py), [`test_hosted_qa.py`](frappe-bench/apps/payrexx_integration/payrexx_integration/tests/test_hosted_qa.py)                                           | Sandbox checkout preflight on 2026-07-22 exposed a GET transaction defect after the provider Gateway was created but local submission and checkout metadata rolled back. Fix `cad3f76` / 16.0.2 passed all 49 integration tests and the deployed checkout retest returned HTTP 200 from `spendedirekt.payrexx.com`. Version 16.1.0 added a guarded read-only hosted settlement runner; hosted preflight then exposed an ERPNext rounded-total edge fixed in 16.1.1. Run `PRX-SBX-E2E-20260723-deadbeef` passed preflight and Payrexx confirmed the CHF 356.75 TEST payment, but its stale `gateway_name=Sandbox` webhook was rejected and the normal success fallback exposed a second GET transaction rollback. Version 16.1.2 fixed terminal fallback commits; version 16.1.3 normalized Gateway-retrieval currency from the exact transaction's parent invoice. The deployed final inspection passed every provider/accounting check for that fallback settlement. Fresh run `PRX-SBX-E2E-20260723-feedface` then proved the corrected `gateway_name=spendedirekt` webhook without invoking fallback: confirmed TEST mode, exact CHF 1.10 amount/currency/reference, Completed Integration Request, Paid request/invoice, zero outstanding, and one exact submitted Payment Entry. The first provider Gateway remains documented sandbox residue because the rolled-back local request retained no provider identifier for safe deletion. |
| Good Connector delivered magic link and identity-bound hosted session                            | [`hosted_auth_qa.py`](frappe-bench/apps/good_connector/good_connector/tests/hosted_auth_qa.py), [`test_hosted_auth_qa.py`](frappe-bench/apps/good_connector/good_connector/good_connector/tests/test_hosted_auth_qa.py) | Strict runner safety/origin/session contract passed 13 focused local tests. Hosted run `GC-AUTH-E2E-20260723-b0ccfa04` then passed with a real link delivered to the established public Mailinator test identity: Frappe `checktokenlogin` returned the exact identity/NGO plus language/elements, the browser remained on the exact allowlisted portal origin, `/rest/session` returned `200` with the matching identity, and no login form remained. The mode-`0600` result contains only hashed/redacted evidence. Cleanup disabled the temporary Website User (deletion fell back to disabling), closed the browser context, and emptied the public Mailinator inbox so the delivered links are no longer exposed; no synthetic token was accepted. |
| Good Newsletter personalized external delivery and SES/SNS correlation                           | [`test_dispatch.py`](frappe-bench/apps/good_newsletter/good_newsletter/tests/test_dispatch.py) | All 12 focused local dispatch tests passed on 2026-07-23, covering per-recipient queue rows, merge rendering, RFC 8058/correlation headers, PDF attachments, cancellation, and status fallback. A read-only hosted preflight confirmed deployed `16.1.1`, an enabled authenticated TLS/SSL outgoing Email Account, signature verification enabled, and open/click tracking enabled. External acceptance remains blocked: `ses_configuration_set` and `sns_topic_arn` are unset, the available bot also has System Manager and cannot prove Newsletter Manager least privilege, and no run-scoped hosted cleanup exists for a Sent campaign. Do not run the broad local `_GNL` cleanup against the shared site. |
| Good NPO hosted donation and membership                                                           | [`test_good_npo.py`](frappe-bench/apps/good_npo/good_npo/tests/test_good_npo.py), [`test_e2e_playwright.py`](frappe-bench/apps/good_npo/good_npo/tests/test_e2e_playwright.py) | Kibe development cannot host this acceptance: its installed-app inventory contains neither `good_npo` nor `good_demo`, and `/demo` returns `404`. The existing browser entrypoint delegates to the broad Good Demo local suite and has no run-scoped hosted cleanup. Local compatibility inspection also found that current Payrexx settlement requires an active Payment Request backed by a submitted Sales Invoice, while Good NPO donation checkout still references `Donation` directly; callback and success-reconciliation tests therefore fail closed instead of marking the Donation paid. Choose a Good NPO deployment target and resolve that cross-app settlement contract before hosted mutation testing. |
| MiKi per-declaration escalation rollback when correspondence fails                               | [`test_end_to_end.py`](frappe-bench/apps/miki_app/miki_app/tests/test_end_to_end.py)                                                                                                                     | Focused server regression and record-scoped hosted request/reminder progression passed; failed correspondence remains atomic by server contract. |

### Hosted Follow-up Waves

The remaining hosted work is intentionally sequenced rather than run as one
cross-app mutation campaign:

| Wave | Scope | Current intent |
|---|---|---|
| Wave 1 | Payrexx corrected-webhook delivery, Good Connector authenticated-session proof, remaining Good Event finance/operations, Good Newsletter external delivery, Good NPO hosted donation/membership, Workflow Visualizer, and least-privilege checks | Continue now; preserve each app's own guarded runner and evidence boundary. |
| Wave 2 | MoPi, Barakah, Good Demo, and Good Analytics | Deferred. Harden hosted-wrapper assertions and remove false-green skips before execution. |
| Excluded | Good MEL and Barakah MEL | Not part of this hosted campaign. |

The local browser commands represented above are:

```bash
FRAPPE_URL=http://127.0.0.1:8001 \
  bench --site development16.localhost execute \
  good_event.tests.test_e2e_playwright.run

FRAPPE_URL=http://127.0.0.1:8000 \
  bench --site development16.localhost execute \
  miki_app.tests.test_e2e_playwright.run
```

Before release sign-off, record hosted Good Event CAPTCHA and waitlist behavior,
the guarded MiKi declaration matrix, real Email Queue delivery, private PDF/file
downloads through the hosted wrappers, and Payrexx/provider outcomes separately.
None of those external checks is implied by a passing local browser run.

## Hosted Hub Rules

The current Good Connector tenant mapping is:

| App           |  NGO |
| ------------- | ---: |
| `barakah_app` |  `2` |
| `mopi_app`    |  `9` |
| `miki_app`    | `11` |

Set `Good Connector Settings.org_id` for the owning app before hosted login and
restore it in `finally`. The shared harness already provides this pattern.

Treat the local app API and hosted hub as separate boundaries. A direct
`GetProcessList`, `GetData`, `GetFileList`, or `GetFileUrls` success proves the
Frappe side, not the hub wrapper. Conversely, a hosted `/rest/session` 401,
`/rest/file-urls` returning `200 null`, edge-service 403, or broken hosted i18n
does not by itself prove an app regression.

Record hosted outcomes as one of:

- Passed in the browser.
- Failed in the application.
- Failed at the external hub/provider boundary.
- Blocked by credentials, CAPTCHA, permissions, environment, or unavailable
  test data.
- Not executed and requiring manual review.

Do not report every classified UAT row as executed. Local fixes remain pending
hosted retest until deployed and verified in the browser.

## MiKi Hosted Declaration UAT

MiKi has two different browser suites. Keep them separate:

- `miki_app.tests.test_e2e_playwright.run` is the local Desk/API/browser
  regression suite.
- `miki_app.tests.hosted_browser_qa` is the guarded runner for the deployed
  Frappe site and hosted self-service portal. Its unit/safety coverage lives in
  `miki_app.tests.test_hosted_browser_qa`; those tests do not execute live UAT.

### Current Portal Contract

As of `miki_app` 16.2, the self-service portal binds writable values through
canonical Frappe variable names. Captured hosted browser traffic showed names
such as `business_name_declared`, `completeness_confirmed`, and
`Accounts[].kita_slots_declared`. Live retesting also proved two narrow response
adapters remain necessary in front of those canonical bindings.

- Open `GetData` emits canonical declaration fields and canonical writable
  `Accounts[]` values. Account writes are keyed by `Accounts[].id`.
- The hosted `ChUid` component accepts and emits nine digits. MiKi adapts that
  value to and from canonical storage as `CHE-xxx.xxx.xxx`.
- The deployed process still evaluates the response-only account conditions
  `kitaVisibility`, `sebVisibility`, and `tfoVisibility`. Emit those three
  metadata keys alongside canonical `*_visible` and capacity fields and ignore
  them if the hub echoes its complete account scope; do not restore retired
  account identity or capacity aliases.
- `StoreData` maps and persists canonical variables only. Retired root names are
  not mapped to declaration fields; unsupported account fields fail validation.
- The declaration has 27 root bindings: 26 writable values plus derived,
  read-only `contact_will_be_updated`. Account rows have the three writable
  capacity values `kita_slots_declared`, `seb_slots_declared`, and
  `tfo_hours_declared`.
- The deployed hosted form has no `business_legal_form_declared` control. Keep
  that canonical API field covered by server tests rather than claiming the
  browser exercised it; adding it to the visible form requires a portal-process
  model change.
- The legacy compatibility that remains is the endpoint envelope, not legacy
  business variables. Keep both `goodApi_webhook_MikiAction` and
  `goodApi_webhook_MikiAction_legacy`, their response shapes, and
  `_parse_payload(...)` message unwrapping.
- A legacy endpoint request may put the canonical declaration object under
  `data` as a JSON string. The hosted final step may omit `finalSubmit`; after
  unwrapping, truthy canonical `completeness_confirmed` is the fallback final
  submission signal.
- Closed declarations use the canonical read-only archive shape. Do not put
  retired Dataverse bindings or a nested `Accounts` value back into that shape.

Do not infer what the browser sends from compatibility code or server `GetData`
alone. Capture the actual `StoreData` POST body and inspect its decoded envelope.
When asserting a field failure, match the exact `StoreData` request, field,
submitted value, and account row identity; unrelated requests must not satisfy
the assertion.

Malformed emails, phone numbers, UID values, Countries, Swiss postal codes,
booleans, capacities, unknown account identities, and unsupported account fields
used by the suite are deliberate regression probes. Do not report them as values
observed from real portal users unless live evidence independently shows that.

### Required Test Layers

Run server tests before live browser UAT. Relevant commands include:

```bash
cd /workspace/development/frappe-bench

bench --site development16.localhost run-tests \
  --module miki_app.tests.test_portal_field_contract
bench --site development16.localhost run-tests \
  --module miki_app.tests.test_writeback
bench --site development16.localhost run-tests \
  --module miki_app.tests.test_end_to_end
bench --site development16.localhost run-tests \
  --module miki_app.tests.test_hosted_qa
bench --site development16.localhost run-tests \
  --module miki_app.tests.test_hosted_browser_qa
```

Run these serially. In particular, do not run multiple `bench run-tests`
commands against one site in parallel; setup hooks can reload DocTypes and
deadlock on shared metadata.

The server-side contract suite must prove every writable canonical root and
account field, normalization, invalid-value non-persistence, final required
fields, exact account identity matching, and workflow failure propagation. The
write-back and lifecycle suites must prove Customer, Contact, Address, billing,
recipient, workflow, and invoice behavior. Hosted QA safety tests must pass
before enabling mutations against a deployed site.

### Hosted Safety And Inputs

Live MiKi hosted QA is explicit and fail-closed. Supply secrets through the
protected process environment, never command arguments, tracked files, state
JSON, screenshots, traces, or reports:

```text
MIKI_HOSTED_QA_USER
MIKI_HOSTED_QA_PASSWORD
MIKI_HOSTED_QA_EMAILS_JSON
MIKI_HOSTED_QA_ALLOW_MUTATIONS
MIKI_HOSTED_QA_PORTAL_LOGIN_URL
MIKI_HOSTED_QA_PORTAL_ALLOWED_HOSTS
MIKI_HOSTED_QA_PRESERVE_PORTAL_IDENTITY
MIKI_HOSTED_QA_VERIFY_FILE_BOUNDARY
```

The runner defaults to the exact allowlisted HTTPS target
`kibe-dev.goodvantage.cloud`. After loading `MIKI_HOSTED_QA_USER` and
`MIKI_HOSTED_QA_PASSWORD` from the protected secret source, start with the
read-only preflight:

```bash
cd /workspace/development/frappe-bench
env/bin/python -m miki_app.tests.hosted_browser_qa --mode preflight
```

- The deployed site must have `developer_mode = 1`,
  `miki_hosted_qa_enabled = 1`, explicit mutation approval, a System Manager
  caller, and controlled role addresses from `MIKI_HOSTED_QA_EMAILS_JSON`.
- Set `Good Connector Settings.org_id` to MiKi NGO `11` for hosted login-token
  generation and restore the previous value in `finally`.
- Portal login URLs are one-time secrets. Require a fresh HTTPS URL and a
  separately explicit host allowlist; redact the full query string in every
  artifact and event.
- Use only exact run-owned records and guarded endpoints. Never run the global
  declaration or receivables daily jobs to accelerate a shared hosted site.
- Keep hosted campaign automation disabled to avoid scheduler races. Advance
  only the exact declaration, invoice, payment schedule, or receivable action
  owned by the current run.
- Persist exact inventory before mutation and resume from it after a lost
  response. Never provision or start the same campaign twice merely because the
  client did not receive the committed response.
- Cleanup validates ownership before mutation, cancels accounting records in
  reverse order, removes only run-owned side effects, and preserves reused
  Users. A broad developer cleanup helper is not acceptable on shared UAT.
- Set both file-boundary flags to `1` only for a single runner invocation that
  contains `portal`, `invoice`, and `payment`. This keeps the declaration Contact
  email unchanged, retains the authenticated self-service browser page, and
  verifies direct `GetFileList` / `GetFiles` / `GetFileUrls` plus the hosted
  file metadata, file-URL, and byte-download wrappers immediately after invoice
  creation and again after normal payment closure. Record `/rest/filelist`
  separately because the hub caches it for 20 minutes by portal token and can
  remain stale after a generated invoice becomes visible through direct APIs.

The exhaustive matrix has 12 positive scenarios across DE/FR/IT and one, two,
or three account rows, plus three negative scenarios with no declaration
Contact. Keep contact-role permutations explicit: declaration Contact,
Hauptkontakt, billing Contacts, shared roles, and unrelated portal users are not
interchangeable.

### Assertions That Matter

A visible portal success state is only the start of the proof:

1. Exercise every applicable canonical control exposed by the real hosted
   process. Cover canonical API fields omitted by that process, currently legal
   form, in the server contract suite.
2. Prove intermediate save, reload, and exact normalized persistence.
3. Prove invalid browser/server submissions return an explicit failed response
   and do not persist, even when native control validation also blocks input.
4. On final submit, prove completeness, Customer/Contact/Address write-back,
   applied Change Logs, exact account capacities, and workflow state `Under
Review` or the expected immediate auto-advance state.
5. Prove the declaration timeline contains a normal `MiKi portal submission`
   Comment with normalized declaration and account values. It is an ordinary
   timeline Comment, not a custom permission or naming subsystem.
6. Prove the explicit review-received confirmation queue and recipient. A daily
   escalation transition to `Under Review` must not send that portal-specific
   confirmation.
7. Continue through normal `Calculate Fee` and `Invoice` workflow actions. Prove
   a submitted positive invoice, exact declaration/Customer links, selected
   invoice address, private PDF, QR content, and exact recipients.
8. For receivables, require each Email Queue row to reach `Sent` before advancing
   the next stage. Queue creation alone is not delivery evidence.
9. For identity-preserving file acceptance, use the same portal browser session
   before and after accounting transitions. Require the exact private invoice
   PDF from the direct Frappe actions and `/rest/files`, `/rest/file-urls`, and
   the returned `download=1` proxy both after invoice creation and after payment
   closes the declaration. Record a stale `/rest/filelist` response as a hub
   cache condition rather than treating it as direct Frappe visibility failure.

Request/reminder correspondence uses the original declaration Contact. Final
confirmation uses the synchronized declaration Contact. Invoice, reminder, and
dunning correspondence uses all linked billing Contacts and falls back to the
declaration Contact only when no billing Contact exists. Hauptkontakt and
unrelated portal users are forbidden recipients. Preserve both the pre-submit
and post-submit recipient history when a Contact email changes during write-back.

The separate-billing choice has two meanings over time:
`billing_use_separate_current` is the immutable creation snapshot, while
successful sync makes `billing_use_separate_declared` the accepted choice used
for subsequent invoice routing. Browser evidence must verify the resulting
Sales Invoice address, PDF, and QR debtor, not only the declaration checkbox.

If endpoint dispatch raises after any write, `_dispatch_miki_action` rolls back
request writes before creating the failed `Integration Request` and returning
the error response. Tests must not accept a 500 response accompanied by partial
Customer, Contact, Address, declaration, Change Log, or ToDo persistence.

Email Queue workers on hosted environments can take several minutes. Poll the
exact run-owned queue with a bounded timeout; do not resend or advance a stage
just because delivery was not immediate.

### Evidence And External Boundaries

The hosted runner should retain redacted screenshots, traces, request-failure
events, response summaries, and exact-run backend evidence. Redaction must cover
credentials, cookies, JWTs, CAPTCHA tokens, magic links, raw recipient addresses
where required, and every URL query value, including values embedded in trace
ZIP content.

Classify these separately from MiKi application failures:

- hosted `/rest/session` returning 401 after token login;
- hosted `/rest/startableprocesslist` returning 500;
- labels rendered as placeholders such as `[Label:business_name]`;
- Socket.IO `Invalid origin` warnings when the tested HTTP flow otherwise works;
- a hosted wrapper returning `200 null` after direct Frappe file APIs succeeded.

Do not weaken MiKi code to hide an external hub/session/translation/socket
failure. Record the browser evidence and verify the Frappe boundary independently.
Likewise, local code and tests are not live UAT evidence until the target is
deployed at the tested revision.

## Reliable Browser Patterns

### Authentication

- Test the login UI only when login is the behavior under test.
- Otherwise use the existing setup project, stored auth, or API login helper.
- Frappe's login endpoint is `POST /api/method/login`.
- Local login can return `home_page="dashboard"`; navigate explicitly to
  `/desk` before exercising Desk forms.
- API cookies alone are not proof that Desk rendered. Assert a Desk-owned DOM
  element or route after authentication.

### Locators And Waiting

- Prefer role, label, visible text, and stable test IDs over CSS position.
- Wait for a specific URL, attached/visible element, Frappe form object, or API
  response.
- Do not use fixed sleeps as the primary synchronization mechanism.
- Do not rely on `networkidle` for Frappe Desk. Realtime/background requests can
  keep the page active indefinitely. Existing sleeps/network-idle waits are
  technical debt, not a pattern to copy.
- Separate browser-extension console noise and websocket-origin warnings from
  application failures.

### Data And Side Effects

- Prefer backend/API setup to UI setup unless the setup UI is under test.
- Clone a valid complex record when that preserves required linked
  configuration, then rename and isolate it. Disable inherited scheduled
  correspondence, trainer rows, publication, or automation that the scenario
  does not require.
- After a failure, resume from the exact record created when safe. Blind retries
  can duplicate bookings, invoices, events, and email.
- CAPTCHA may be bypassed only on a local test site through the app's existing
  guarded helper. Always restore it. Hosted CAPTCHA is an external UAT step.

### Email, Files, And PDFs

A visible success message is insufficient for correspondence tests. Assert the
relevant layers:

1. Business document and workflow state.
2. Email Queue status, recipient, subject/language, and body.
3. Attachment metadata and business-document linkage.
4. Downloaded binary content and filename.
5. Extracted PDF text or rendered pages when document content/layout matters.

`wkhtmltopdf` can fail after the business action succeeds because its callback
URL or local server is unavailable. Retry only failed queues after fixing the
environment; do not resend every successful flow. Use a real Chrome-rendered
PDF check when visual layout is the requirement because page-count assertions
do not catch clipping or overlap.

### Mobile And Evidence

- Cover the critical journey at desktop and a narrow viewport such as 390 px.
- Assert mobile-specific behavior rather than rerunning every desktop case.
- On failure retain screenshot, trace, relevant console/network output, and
  server traceback. Redact secrets before sharing evidence.
- Give each run a unique artifact directory, for example
  `/tmp/opencode/good-event-registration-20260717`.

## Troubleshooting

| Symptom                                              | Check first                                                                                                                                                                                                                                        |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: playwright`                    | The command is using `frappe-bench/env/bin/python`                                                                                                                                                                                                 |
| Chromium executable missing/version mismatch         | Install Chromium through the same Playwright package/interpreter                                                                                                                                                                                   |
| Browser launch reports shared libraries              | Install Playwright/Linux browser dependencies                                                                                                                                                                                                      |
| `.localhost` does not resolve                        | Use `127.0.0.1`, correct port, and preserve Frappe site routing                                                                                                                                                                                    |
| Login reports a missing installed app                | Restart a stale `bench serve` before changing code                                                                                                                                                                                                 |
| Desk hangs on `networkidle`                          | Wait for route/form/DOM state instead                                                                                                                                                                                                              |
| Browser says success but email is `Not Sent`         | Inspect Email Queue error and PDF callback/server availability                                                                                                                                                                                     |
| Hosted file list works but click/download fails      | Compare direct Frappe file APIs with the hub `/rest/file-urls` wrapper                                                                                                                                                                             |
| Duplicate/unexpected emails                          | Check inherited automation and other concurrent sessions before retrying                                                                                                                                                                           |
| Shell exits 0 with failed scenario                   | Make the runner raise on false/skipped result                                                                                                                                                                                                      |
| External site returns 403/429/CAPTCHA                | Classify as external boundary; do not weaken app security to bypass it                                                                                                                                                                             |
| A bot reports `except A, B:` as Python-2 syntax      | Check the declared interpreter first. Python 3.14 permits unparenthesized exception tuples through PEP 758; this bench declares Python `>=3.14`. Use multiline parenthesized tuples when external static validators do not understand 3.14 syntax. |
| MiKi final submit returns 500                        | Inspect the failed Integration Request and confirm request writes rolled back before retrying; do not assume Customer/Contact/Address changes committed.                                                                                           |
| MiKi browser traffic appears to use legacy variables | Inspect the decoded `StoreData` POST body. Current self-service uses canonical fields; legacy endpoint message unwrapping is not legacy field support.                                                                                             |

## New Suite Checklist

Document these items with every new or materially changed E2E suite:

- Exact command and owning app.
- Local, hosted, or external target.
- Required environment variables and credentials source.
- Whether the runner starts its own server.
- Test data created, reused, and cleaned up.
- Settings changed and guaranteed restoration path.
- Real email/payment/SMS/provider side effects.
- Browser assertions versus backend-only assertions.
- Desktop/mobile scope.
- Artifact directory and CI status.
- Known external blockers and how to distinguish them from app failures.

## Audit Basis

This guide consolidates repository Markdown, active test/config files, and the
OpenCode session history available on this machine as of 2026-07-19. The session
audit covered the original 291 sessions from 2026-06-05 through 2026-07-17 plus
the MiKi 16.2 hosted field-contract and release-verification work, and excluded
generic instruction-text matches. Repeated findings included interpreter and
Chromium mismatches, missing Linux libraries, stale local servers, `.localhost`
DNS failures, `networkidle` hangs, CAPTCHA and hosted-session blockers,
wkhtmltopdf callback failures, inherited correspondence automation, legacy
envelope-versus-field confusion, incomplete rollback assumptions, and collisions
from concurrent sessions on one site.
