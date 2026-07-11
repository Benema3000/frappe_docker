# Playwright E2E Handover

This is the handover for browser-style E2E tests in this workspace. It is written for another
agent who needs to know what exists, how to run it, and which local gotchas matter.

## Big Picture

There are two families of Playwright tests here:

- Python standalone runners inside Frappe apps. These use `playwright.sync_api`,
  `bench execute`, Desk login as `Administrator/admin`, and direct browser `fetch()` calls.
- TypeScript Playwright projects. These use `@playwright/test`, `playwright.config.ts`,
  setup projects, and cached browser auth state.

Do not run several suites against the same Frappe site in parallel. They mutate shared rows such
as `Good Connector Settings`, create test tasks/bookings/users, and can trip over each other.

## Shared Prerequisites

From `frappe-bench` unless a section says otherwise:

```bash
bench --site development16.localhost serve --port 8000
python -m pip install playwright
playwright install chromium
```

Common environment variables:

```bash
export FRAPPE_URL=http://localhost:8000
export FRAPPE_SITE=development16.localhost
export BENCH_PATH=/workspace/development/frappe-bench
export PLAYWRIGHT_LOCALE=en-US
export GOOD_CONNECTOR_LOGIN_BASE_URL=https://selfservice.goodvanta.ge
```

The hosted hub NGO mapping used by the Good Connector consumers is:

| App | NGO |
|---|---:|
| `barakah_app` | `2` |
| `mopi_app` | `9` |
| `miki_app` | `11` |

The Python Good Connector consumer suites usually save the original `Good Connector Settings.org_id`
and `api_base_url`, set the app-specific values for the run, and restore in `finally`. They also
mute emails by default unless `PLAYWRIGHT_REAL_EMAIL=1`.

## Python Browser Runners

### MoPi

File: `apps/mopi_app/mopi_app/tests/test_e2e_playwright.py`

Run:

```bash
bench --site development16.localhost execute mopi_app.tests.test_e2e_playwright.run
```

What it covers:

- Creates/updates test portal users for school transport, patient transport, and both.
- Task Campaign bulk task creation.
- Single task request flow.
- Training module workflow and certificate generation.
- Transport-filtered news and links.
- Portal `GetProcessList`, `GetData`, `StoreData`.
- Certificate file visibility and direct `GetFileList` / `GetFileUrls` download.
- Hosted hub news/links checks, with graceful skips when the hosted hub cannot reach local APIs.
- `Fuhrerscheinkontrolle` campaign type.
- Portal `StoreFiles`, `GetFileList`, `GetFileUrls`, and `DeleteFiles`.

Useful env overrides:

```bash
MOPI_SCHOOL_USER=mopi-school@example.com
MOPI_PATIENT_USER=mopi-patient@example.com
MOPI_BOTH_USER=mopi-both@example.com
PLAYWRIGHT_REAL_EMAIL=1
```

Gotchas:

- MoPi is the exception where `GetProcessList` may include completed assignment history. Open/editable
  tasks must still sort first. File upload tests must choose a non-closed task.
- Screenshots go to `apps/mopi_app/screenshots/mopi/`.
- There is also a server-side E2E-style integration module:

```bash
bench --site development16.localhost run-tests --module mopi_app.tests.test_e2e_major_processes
```

That one is not Playwright; it exercises Good Connector/MoPi portal APIs with JWTs in
`IntegrationTestCase`.

### Barakah

File: `apps/barakah_app/barakah_app/tests/test_e2e_playwright.py`

Run:

```bash
bench --site development16.localhost execute barakah_app.tests.test_e2e_playwright.run
```

What `run()` currently calls:

- Hosted hub Aqeeqa lifecycle.
- Hosted hub Well lifecycle.
- Direct portal file access.
- News and links.

The file also contains older Desk-facing helper tests for Aqeeqa/Well creation, cancellation,
dashboard, and email queue checks. They are useful when debugging, but they are not currently called
from `run()`.

Useful env overrides:

```bash
BARAKAH_PORTAL_USER_EMAIL=benediktmathis+playwright@gmail.com
PLAYWRIGHT_REAL_EMAIL=1
```

Gotchas:

- Direct Frappe API file checks can pass while the hosted hub file page times out or loops on loading.
  Treat that as a hosted hub/session wrapper issue unless direct `GetFileList` / `GetFileUrls` fails.
- Screenshots go to `apps/barakah_app/screenshots/`.

### Miki

File: `apps/miki_app/miki_app/tests/test_e2e_playwright.py`

Run:

```bash
bench --site development16.localhost execute miki_app.tests.test_e2e_playwright.run
```

What it covers:

- Dashboard.
- Declaration lifecycle.
- Snapshot/change log.
- Conditional skip behavior.
- Tiered pricing.
- Dunning single mechanism.
- QR bill embedding.
- Legacy Dataverse id round trip.
- Master-data sync on portal final submit.
- Account/internal id mapping.
- Hosted hub declaration lifecycle.
- Miki webhook delegation.
- Portal file visibility.
- Manual correspondence sending.
- Start campaign button.
- Email queue checks.

Useful env overrides:

```bash
MIKI_PORTAL_USER_EMAIL=miki-portal@example.com
MIKI_PORTAL_USER_FIRST=Miki
MIKI_PORTAL_USER_LAST=Portal
PLAYWRIGHT_REAL_EMAIL=1
```

Gotchas:

- The suite has both shared declaration setup and fresh declaration setup. Reusing the fresh helper too
  early can delete the declaration needed by later invoice/dunning/QR-bill checks.
- Hosted legacy Miki payloads differ from newer portal test payloads. Any webhook path should parse
  payloads before dispatch.
- Portal final submit can create operations ToDos; if you touch that path, keep assignment/email side
  effects in mind.
- Screenshots go to `apps/miki_app/screenshots/miki/`.

### Event App

File: `apps/event_app/event_app/tests/test_e2e_playwright.py`

Full smoke:

```bash
bench --site development16.localhost execute event_app.tests.test_e2e_playwright.run
```

Focused public booking form smoke:

```bash
FRAPPE_URL=http://127.0.0.1:8001 \
bench --site development16.localhost execute event_app.tests.test_e2e_playwright.run_public_booking_form
```

What it covers:

- Starts `bench serve` on the port from `FRAPPE_URL` if no server responds.
- Event App Desk home and workspace/sidebar expectations.
- Public event detail and event list pages.
- Filters: region, text search, date ranges, embed mode.
- Public `/anmelden/<slug>` pre-step.
- Booking intent cookie/server state.
- Pay-later registration path through Buzz `process_booking`.
- Booking form layout and localized labels.

Gotchas:

- Uses `X-Frappe-Site-Name` in the browser context so `127.0.0.1` can route to the target site.
- The focused smoke exists for fast registration-template checks.

### Good Demo / Good NPO

Files:

- `apps/good_demo/good_demo/tests/test_e2e_playwright.py`
- `apps/good_npo/good_npo/tests/test_e2e_playwright.py`

Run:

```bash
bench --site development16.localhost execute good_demo.tests.test_e2e_playwright.run
bench --site development16.localhost execute good_npo.tests.test_e2e_playwright.run
```

`good_npo` delegates to the `good_demo` browser flow because the public shell is owned by
`good_demo`.

What it covers:

- Public bilingual demo access form.
- CAPTCHA-backed demo signup and email queueing.
- Public membership form and membership email fallback.
- Public donation checkout with local dummy card/TWINT UI.
- Donation success/failure return states.
- Donation thank-you email queue.
- Logged-in demo user's GoodNPO home/help surface.

Useful env:

```bash
GOOD_DEMO_E2E_CAPTCHA_TIMEOUT=120000
```

Gotchas:

- This runner starts `bench serve` if needed.
- It temporarily edits a membership Email Template to force the fallback behavior, then restores it in
  `finally`.

### Good Connector Real-Email Hub Smoke

File: `apps/good_connector/good_connector/tests/real_hub_user_flow.py`

Run:

```bash
bench --site development16.localhost execute good_connector.tests.real_hub_user_flow.run
```

What it does:

- Intentionally does not mute email.
- Sends real login emails for MoPi, Barakah, and Miki users.
- Extracts hosted hub login URLs from `Email Queue`.
- Opens the hosted hub with Playwright and then reuses the extracted JWTs for portal submissions.

Useful env:

```bash
MOPI_SCHOOL_USER=benediktmathis+playwright-school@gmail.com
MOPI_PATIENT_USER=benediktmathis+playwright-patient@gmail.com
MOPI_BOTH_USER=benediktmathis+playwright-both@gmail.com
BARAKAH_PORTAL_USER_EMAIL=benediktmathis+playwright@gmail.com
MIKI_PORTAL_USER_EMAIL=benediktmathis+playwright-miki@gmail.com
GOOD_CONNECTOR_LOGIN_BASE_URL=https://selfservice.goodvanta.ge
```

Gotchas:

- This is the suite to use when the question is "what does a real email + hosted hub login do?"
- If the email sends immediately and the MIME body is not retained, the helper can fall back to building
  a token for browser driving; do not confuse that fallback with proof of email body content.

## TypeScript Playwright Projects

### Payrexx Integration

Directory: `apps/payrexx_integration/playwright`

Run:

```bash
cd apps/payrexx_integration/playwright
npm install
npx playwright install chromium
npm test
```

Useful env:

```bash
PLAYWRIGHT_BASE_URL=http://localhost:8000
FRAPPE_USERNAME=Administrator
FRAPPE_PASSWORD=admin
TEST_BOOKING_NAME=<existing Event Booking>
RUN_PAYREXX_SANDBOX_PAYMENT=1
```

What it covers:

- `Payrexx Settings` Desk flow and installed `Payment Gateway`.
- `pay_invoice` endpoint auth/error handling.
- Booking invoice email generation and Payrexx URL in Email Queue.
- Guest pay-later browser flow.
- `/anmelden` picker UX.
- Event App correspondence/workflow pieces.
- Sandbox hosted payment flow when explicitly enabled.

Gotchas:

- `tests/helpers/global-setup.ts` logs in once and writes `auth.json`.
- Some specs need seeded Event App data, especially `TEST_BOOKING_NAME`.
- The sandbox payment test is opt-in because it talks to external Payrexx.

### Buzz

Directory: `apps/buzz`

Run:

```bash
cd apps/buzz
npm install
BASE_URL=http://buzz.test:8000 FRAPPE_USER=Administrator FRAPPE_PASSWORD=admin npm run test:e2e
```

What it covers:

- Auth and login modal behavior.
- Event booking page.
- Guest booking and OTP flows.
- Custom forms.
- Event proposal form.
- Tax-inclusive pricing.
- Offline payment flow.

Gotchas:

- `buzz` is upstream in this bench. Do not patch it unless explicitly told to.
- Config uses setup projects and `e2e/.auth/user.json`.
- `fullyParallel=false` and `workers=1` are intentional for Frappe state consistency.

### Wiki

Directory: `apps/wiki`

Run:

```bash
cd apps/wiki
npm install
BASE_URL=http://wiki.test:8000 FRAPPE_USER=Administrator FRAPPE_PASSWORD=admin npm run test:e2e
```

What it covers:

- Auth setup.
- Wiki editor.
- Change request flow.
- Public pages and sidebar.
- Ordering.
- Markdown line breaks.
- Callout rich text.
- Image viewer.
- Link persistence and external links.
- Iframe embeds.
- TOC navigation.
- Mobile view.

Gotchas:

- `wiki` is not one of the custom Goodvantage apps. Treat it like upstream-style code.
- Config uses one setup project plus a single chromium project with cached auth state.

## Running Notes

- For Python suites, prefer `bench execute <module>.run` over importing and calling directly. The helper
  functions often shell back into `bench execute` and expect the configured site context.
- Browser login helpers assume `Administrator/admin` unless overridden by the suite.
- If local `/login` fails with missing dependencies while the source exists, check for a stale `bench serve`
  process before changing code.
- Hosted selfservice checks can fail even when local Frappe APIs are correct. Check direct
  `GetProcessList`, `GetFileList`, `GetFileUrls`, and webhook responses before blaming app logic.
- Screenshots are usually written under each app's `screenshots/` directory. Failed Python runs often write
  an `ERROR.png`.
- Use real-email runs sparingly. Most app-specific Python runners mute emails by default; the
  Good Connector real-email smoke intentionally does not.

## Safe Agent Workflow

1. Identify the owning app and read that app's `AGENTS.md`.
2. Start or verify the local bench server.
3. Run the smallest relevant suite first:
   - MoPi portal/task/file issue: `mopi_app.tests.test_e2e_playwright.run`
   - Barakah hosted hub/file issue: `barakah_app.tests.test_e2e_playwright.run`
   - Miki declaration/hub issue: `miki_app.tests.test_e2e_playwright.run`
   - Event registration form issue: `event_app.tests.test_e2e_playwright.run_public_booking_form`
   - Payrexx email/payment issue: the focused spec in `apps/payrexx_integration/playwright/tests`
4. Preserve shared settings in `finally` if you add new test helpers.
5. Do not make hosted hub failures look like app regressions until direct local API checks also fail.
