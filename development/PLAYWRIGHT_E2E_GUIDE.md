# Playwright E2E Test Guide

This guide is for agents who need to create new end-to-end browser tests. It is intentionally
framework-neutral: the examples use Playwright concepts that apply whether the app is Frappe,
React, Vue, Rails, Django, Laravel, a static site, or something else.

## What E2E Tests Are Good For

Use an E2E test when the important behavior depends on the real browser and several layers working
together:

- Login and permissions.
- Multi-step user journeys.
- Form validation and submission.
- File upload/download.
- Email or payment flows where the UI triggers server work.
- Routing, redirects, browser storage, cookies, or cross-page state.
- Visual/interactive behavior that unit tests cannot see.

Avoid E2E tests for small pure functions, simple data transformations, or every validation rule.
Those belong in unit/integration tests. E2E tests should cover critical paths and regressions with
high business value.

## Basic Shape

A good E2E test has three phases:

1. Arrange: create the data and authenticate the browser.
2. Act: drive the UI like a user.
3. Assert: verify visible results and, when needed, backend side effects.

```ts
import { test, expect } from "@playwright/test";

test("user can submit contact form", async ({ page }) => {
	await page.goto("/contact");

	await page.getByLabel("Name").fill("Ada Lovelace");
	await page.getByLabel("Email").fill("ada@example.com");
	await page.getByLabel("Message").fill("Hello from Playwright");
	await page.getByRole("button", { name: "Send" }).click();

	await expect(page.getByText("Thanks, we received your message")).toBeVisible();
});
```

## Browser Concepts

Playwright gives you three main objects:

- `browser`: the Chromium/Firefox/WebKit process.
- `context`: an isolated browser profile with its own cookies, local storage, permissions, viewport,
  locale, and downloads.
- `page`: a tab inside a context.

Use a fresh context when you need a clean user/session. Use a second context to simulate another
browser/user.

```ts
test("anonymous and logged-in users see different nav", async ({ browser }) => {
	const anonymous = await browser.newContext();
	const anonPage = await anonymous.newPage();
	await anonPage.goto("/");
	await expect(anonPage.getByRole("button", { name: "Log in" })).toBeVisible();
	await anonymous.close();

	const loggedIn = await browser.newContext({ storageState: "auth.json" });
	const userPage = await loggedIn.newPage();
	await userPage.goto("/");
	await expect(userPage.getByRole("link", { name: "Dashboard" })).toBeVisible();
	await loggedIn.close();
});
```

## Project Setup

For a TypeScript/JavaScript project:

```bash
npm install --save-dev @playwright/test
npx playwright install chromium
npx playwright test
```

Minimal `playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
	testDir: "./e2e/tests",
	fullyParallel: false,
	workers: 1,
	retries: process.env.CI ? 2 : 0,
	reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "html",
	timeout: 60_000,
	expect: { timeout: 10_000 },
	use: {
		baseURL: process.env.BASE_URL || "http://localhost:8000",
		trace: "retain-on-failure",
		screenshot: "only-on-failure",
		video: "retain-on-failure",
		...devices["Desktop Chrome"],
	},
});
```

Useful package scripts:

```json
{
	"scripts": {
		"test:e2e": "playwright test",
		"test:e2e:headed": "playwright test --headed",
		"test:e2e:ui": "playwright test --ui",
		"test:e2e:debug": "playwright test --debug",
		"test:e2e:report": "playwright show-report"
	}
}
```

Python Playwright is useful for standalone smoke scripts inside Python-heavy systems:

```bash
python -m pip install playwright
playwright install chromium
```

```py
from playwright.sync_api import sync_playwright, expect

def run():
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=True)
		page = browser.new_page()
		page.goto("http://localhost:8000")
		expect(page.get_by_role("heading", name="Home")).to_be_visible()
		browser.close()
```

## Locators

Prefer user-facing locators. They are more stable and encourage accessible UI.

Best:

```ts
page.getByRole("button", { name: "Save" });
page.getByLabel("Email");
page.getByText("Payment confirmed");
page.getByTestId("invoice-total");
```

Use CSS selectors when the element has no accessible identity or when you are testing layout-specific
markup:

```ts
page.locator(".invoice-row").filter({ hasText: "Subtotal" });
```

Avoid brittle selectors:

```ts
// Avoid these when possible.
page.locator("div > div:nth-child(3) > button");
page.locator(".btn-primary").nth(2);
```

If you control the frontend, add stable `data-testid` attributes for elements that have no natural
role or label.

## Waiting

Playwright auto-waits for most actions. Do not add arbitrary sleeps unless there is no better signal.

Good waits:

```ts
await expect(page.getByText("Saved")).toBeVisible();
await page.waitForURL("**/dashboard");
await page.waitForResponse((res) => res.url().includes("/api/orders") && res.ok());
```

Less good:

```ts
await page.waitForTimeout(3000);
```

Use `networkidle` carefully. Modern apps often keep background requests open. Prefer waiting for a
specific element, URL, or API response.

## Authentication

There are three common patterns.

### UI Login

Best when you need to verify login itself:

```ts
await page.goto("/login");
await page.getByLabel("Email").fill(process.env.TEST_USER!);
await page.getByLabel("Password").fill(process.env.TEST_PASSWORD!);
await page.getByRole("button", { name: "Log in" }).click();
await page.waitForURL("**/dashboard");
```

### Setup Project With Stored Auth

Best for most suites. Login once, save cookies/local storage, reuse it.

```ts
// e2e/tests/auth.setup.ts
import { test as setup, expect } from "@playwright/test";

setup("authenticate", async ({ page }) => {
	await page.goto("/login");
	await page.getByLabel("Email").fill(process.env.TEST_USER || "admin@example.com");
	await page.getByLabel("Password").fill(process.env.TEST_PASSWORD || "admin");
	await page.getByRole("button", { name: "Log in" }).click();
	await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();
	await page.context().storageState({ path: "e2e/.auth/user.json" });
});
```

```ts
// playwright.config.ts
projects: [
	{ name: "setup", testMatch: /auth\.setup\.ts/ },
	{
		name: "chromium",
		use: { storageState: "e2e/.auth/user.json" },
		dependencies: ["setup"],
	},
];
```

### API Login

Best when login UI is unrelated to the test. Use the app's login endpoint, then save the state.

```ts
const response = await page.request.post("/api/login", {
	data: { email: "admin@example.com", password: "admin" },
});
expect(response.ok()).toBeTruthy();
await page.context().storageState({ path: "e2e/.auth/user.json" });
```

## Test Data

Create deterministic data before the browser journey. Good options:

- API calls through Playwright's `request` fixture.
- Backend helper command/script.
- Database fixtures in a test-only environment.
- UI setup only when the setup UI itself is part of the behavior.

Use unique names to avoid clashes:

```ts
const tag = Date.now();
const email = `playwright-${tag}@example.com`;
```

Clean up if the data is expensive, noisy, or affects future tests. It is often acceptable to leave
timestamped test records in disposable dev/CI environments.

## Assertions

Assert what users can see first:

```ts
await expect(page.getByText("Invoice created")).toBeVisible();
```

Then assert backend side effects only when visible UI is not enough:

```ts
const order = await page.request.get(`/api/orders/${orderId}`);
expect((await order.json()).status).toBe("paid");
```

Do not assert every implementation detail. E2E tests should be resilient to harmless UI refactors.

## Forms

Use labels where possible:

```ts
await page.getByLabel("First name").fill("Grace");
await page.getByLabel("I accept the terms").check();
await page.getByRole("combobox", { name: "Country" }).selectOption("CH");
```

For custom select components:

```ts
await page.getByRole("combobox", { name: "Country" }).click();
await page.getByRole("option", { name: "Switzerland" }).click();
```

For dynamic forms, wait for the field to exist before filling:

```ts
await expect(page.getByLabel("Company name")).toBeVisible();
await page.getByLabel("Company name").fill("Goodvantage");
```

## Files

Upload:

```ts
await page.getByLabel("Upload receipt").setInputFiles("fixtures/receipt.pdf");
await expect(page.getByText("receipt.pdf")).toBeVisible();
```

Download:

```ts
const downloadPromise = page.waitForEvent("download");
await page.getByRole("link", { name: "Download invoice" }).click();
const download = await downloadPromise;
expect(download.suggestedFilename()).toContain("invoice");
```

## Network And APIs

Use `page.request` for setup and verification:

```ts
const created = await page.request.post("/api/test/orders", {
	data: { total: 100 },
});
expect(created.ok()).toBeTruthy();
```

Mock external services when the point of the test is your app, not the provider:

```ts
await page.route("**/payment-provider/**", async (route) => {
	await route.fulfill({
		status: 200,
		contentType: "application/json",
		body: JSON.stringify({ status: "confirmed" }),
	});
});
```

Do not mock your own app's critical API in an E2E test unless you are deliberately writing a frontend-only
smoke test.

## Multi-User And Multi-Tab Flows

Use multiple contexts for different users:

```ts
const admin = await browser.newContext({ storageState: "admin.json" });
const customer = await browser.newContext({ storageState: "customer.json" });

const adminPage = await admin.newPage();
const customerPage = await customer.newPage();
```

Use multiple pages in one context for same-user tabs:

```ts
const firstTab = await context.newPage();
const secondTab = await context.newPage();
```

## Mobile And Viewports

Add a mobile project when mobile layout is important:

```ts
import { devices } from "@playwright/test";

projects: [
	{ name: "desktop", use: { ...devices["Desktop Chrome"] } },
	{ name: "mobile", use: { ...devices["Pixel 5"] } },
];
```

Mobile tests should assert actual mobile behavior, not merely rerun every desktop test.

## Debugging

Useful commands:

```bash
npx playwright test --headed
npx playwright test --debug
npx playwright test path/to/spec.ts:42
npx playwright show-report
```

Use traces and screenshots:

```ts
use: {
	trace: "retain-on-failure",
	screenshot: "only-on-failure",
	video: "retain-on-failure",
}
```

You can pause a test during debugging:

```ts
await page.pause();
```

For Python scripts, capture screenshots near failures:

```py
try:
    # test steps
    pass
except Exception:
    page.screenshot(path="ERROR.png", full_page=True)
    raise
```

## CI Advice

Use one worker at first:

```ts
workers: process.env.CI ? 1 : 1;
```

Increase workers only after test data isolation is proven.

Start the app before the tests:

```ts
webServer: {
	command: "npm run start:test",
	url: "http://localhost:3000",
	reuseExistingServer: !process.env.CI,
	timeout: 120_000,
}
```

Store artifacts on failure: Playwright report, traces, screenshots, videos, and server logs.

## Stability Rules

- Prefer role/label/test-id locators over CSS chains.
- Wait for user-visible outcomes, not arbitrary time.
- Make data unique per run.
- Keep tests independent; one test should not depend on another test's output unless it is an explicit
  setup project.
- Keep external services mocked or opt-in unless the test is specifically about that integration.
- Test critical paths deeply, edge cases selectively.
- Do not hide real failures with broad try/except blocks. If you skip a third-party/hub assertion, first
  verify the local app API still passed and log why the external part was skipped.

## Example Suite Layout

```text
e2e/
  .auth/
    user.json              # generated, gitignored
  fixtures/
    receipt.pdf
  helpers/
    api.ts
    auth.ts
    data.ts
  pages/
    checkout.page.ts
  tests/
    auth.setup.ts
    checkout.spec.ts
    invoice-download.spec.ts
playwright.config.ts
package.json
```

Page object example:

```ts
import { expect, Page } from "@playwright/test";

export class CheckoutPage {
	constructor(private page: Page) {}

	async goto(orderId: string) {
		await this.page.goto(`/checkout/${orderId}`);
		await expect(this.page.getByRole("heading", { name: "Checkout" })).toBeVisible();
	}

	async payByCard() {
		await this.page.getByRole("button", { name: "Pay by card" }).click();
	}
}
```

Use page objects for repeated workflows, not for every single selector. If a selector is used once,
keeping it in the spec is often clearer.

## Handover Checklist For New E2E Tests

When adding a new E2E test, leave the next agent these notes:

- Command to run the test locally.
- Required environment variables.
- Whether the test starts its own server.
- What data it creates and whether it cleans it up.
- Whether it sends real emails, payments, SMS, or external API calls.
- Where screenshots/traces/reports are written.
- Known flaky external dependencies and how to distinguish them from app regressions.
