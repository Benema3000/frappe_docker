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

| Question | Preferred test |
|---|---|
| Pure rules, document lifecycle, permissions, APIs, jobs | Frappe `IntegrationTestCase` / `UnitTestCase` |
| Critical journey through a real browser | Playwright |
| Layout, routing, browser storage, upload/download, responsive UI | Playwright |
| Email/PDF workflow | Playwright trigger plus Email Queue and attachment/PDF assertions |
| Real Payrexx, inbox, hosted hub, CAPTCHA, or another external system | Explicit opt-in Playwright UAT |
| Upstream Frappe or Builder browser regressions | Their existing Cypress suites; do not convert or patch upstream |
| Exploratory usability, accessibility, or visual approval | Manual review, optionally supported by Playwright evidence |

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

| Owner | Entrypoint | Main scope |
|---|---|---|
| MoPi | `mopi_app.tests.test_e2e_playwright.run` | Desk, tasks, training, certificates, portal/hub, files, news/links |
| Barakah | `barakah_app.tests.test_e2e_playwright.run` | Public order forms, local Aqeeqa/Well portal contracts, direct file APIs, news/links, and optional hosted file-page evidence; hosted failures may be reported without failing the run |
| MiKi | `miki_app.tests.test_e2e_playwright.run` | Declaration, billing/dunning, Desk, local portal/hub contracts, files, correspondence; not the separate hosted-browser drive |
| Good Event | `good_event.tests.test_e2e_playwright.run` | Native registration, private/organization cases, coupon, mobile, persistence, pre-event package |
| Good Demo | `good_demo.tests.test_e2e_playwright.run` | Signup, membership, donation, dummy checkout, email queue, mobile Desk/help |
| Good NPO | `good_npo.tests.test_e2e_playwright.run` | Delegates to the Good Demo flow |
| Good Connector | `good_connector.tests.real_hub_user_flow.run` | Real email, hub navigation evidence, and direct portal submissions across MoPi, Barakah, and MiKi; it does not assert authenticated hub content |

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

MoPi, Barakah, and MiKi share
`apps/good_connector/good_connector/tests/browser_harness.py`. Add shared Desk,
hub, settings, or restoration behavior there rather than copying helpers into
all three apps.

### TypeScript Playwright

| Project | Directory | Command | Notes |
|---|---|---|---|
| Payrexx Integration | `apps/payrexx_integration/playwright` | `npm test` | Chromium, one worker, optional existing Good Event booking email check; no real provider round trip |
| Buzz | `apps/buzz` | `yarn test:e2e` | Upstream/off-limits; setup projects and stored auth; one worker |
| Wiki | `apps/wiki` | `yarn test:e2e` | Upstream-style app; setup project and stored auth |

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

## Hosted Hub Rules

The current Good Connector tenant mapping is:

| App | NGO |
|---|---:|
| `barakah_app` | `2` |
| `mopi_app` | `9` |
| `miki_app` | `11` |

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

| Symptom | Check first |
|---|---|
| `ModuleNotFoundError: playwright` | The command is using `frappe-bench/env/bin/python` |
| Chromium executable missing/version mismatch | Install Chromium through the same Playwright package/interpreter |
| Browser launch reports shared libraries | Install Playwright/Linux browser dependencies |
| `.localhost` does not resolve | Use `127.0.0.1`, correct port, and preserve Frappe site routing |
| Login reports a missing installed app | Restart a stale `bench serve` before changing code |
| Desk hangs on `networkidle` | Wait for route/form/DOM state instead |
| Browser says success but email is `Not Sent` | Inspect Email Queue error and PDF callback/server availability |
| Hosted file list works but click/download fails | Compare direct Frappe file APIs with the hub `/rest/file-urls` wrapper |
| Duplicate/unexpected emails | Check inherited automation and other concurrent sessions before retrying |
| Shell exits 0 with failed scenario | Make the runner raise on false/skipped result |
| External site returns 403/429/CAPTCHA | Classify as external boundary; do not weaken app security to bypass it |

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
OpenCode session history available on this machine as of 2026-07-17. The session
audit covered 291 sessions from 2026-06-05 through 2026-07-17 and excluded
generic instruction-text matches. Repeated findings included interpreter and
Chromium mismatches, missing Linux libraries, stale local servers, `.localhost`
DNS failures, `networkidle` hangs, CAPTCHA and hosted-session blockers,
wkhtmltopdf callback failures, inherited correspondence automation, and
collisions from concurrent sessions on one site.
