# Frappe Fleet Update Pipeline Plan

## 1. Purpose

Build a controlled monthly update pipeline for the five Goodvantage Frappe
stacks running on Hetzner Cloud, including their custom customer apps, shared
Goodvantage apps, and compatibility with the separately hosted selfservice hub,
declaration workflows, file exchange, payment integration, and bank-facing
functionality.

The pipeline must:

1. Detect normal upstream and dependency updates once per month, while checking
   regularly for relevant Frappe security updates.
2. Produce a reproducible release candidate containing exact source revisions.
3. Build the same software artifact that will later be deployed.
4. Test clean installation and upgrades from production-shaped data.
5. Run server, integration, browser, selfservice, and external-boundary tests.
6. Attempt tightly constrained automated repairs when appropriate.
7. Open draft pull requests and publish one consolidated release report.
8. Require human approval before merging or deploying.
9. Roll out an approved release through a canary and controlled deployment waves.
10. Preserve a tested recovery path for every production deployment.

This document is the implementation plan. It does not authorize unattended
production deployments.

## 2. Scope

### 2.1 Included

- Frappe Framework and ERPNext v16 updates.
- Upstream extension apps used by the five stacks, such as `payments`, `wiki`,
  `builder`, and the `non_profit` fork where installed.
- All Goodvantage shared and product apps installed in production.
- Customer-specific Frappe apps.
- Compatibility between candidate Frappe stacks and the currently deployed
  selfservice hub version.
- Manually triggered compatibility tests for the selfservice hub's independent
  deployment cycle.
- Declaration, task, file, email, PDF, payment, and bank-interface regressions.
- Fresh installation, `bench migrate`, app tests, Playwright tests, and hosted
  staging UAT.
- Container or deployable artifact construction.
- Release manifests, reports, notifications, and production runbooks.
- Sanitized production-shaped database migration tests.

### 2.2 Excluded From The Initial Version

- Automatic merge of bot-created pull requests.
- Unattended production deployment.
- Automatic database rollback after a migration.
- Real production payments or bank transactions from CI.
- Real customer email delivery from ordinary CI runs.
- Unbounded AI changes across repositories.
- Building or deploying the selfservice hub from the monthly Frappe pipeline.
- Frappe major-version upgrades. Those require a separate migration project.

## 3. Core Decisions

### 3.1 Monthly Cadence And Security Trigger

The normal pipeline runs once per month, preferably on the first Monday at a
fixed time. It batches available maintenance and security fixes into one release
candidate.

In addition, a lightweight security monitor checks official Frappe security
advisories and supported-branch security releases regularly, with daily polling
as the recommended default. When a new advisory or security release affects a
component/version installed in the fleet, it starts the same complete build,
migration, test, review, and approval process without waiting for the next
monthly cycle.

There is also a manually triggered workflow for an operator to run the same
pipeline at any time. No trigger can deploy automatically to production.

Suggested calendar:

| Day                                 | Activity                                    |
| ----------------------------------- | ------------------------------------------- |
| Daily                               | Lightweight security advisory/release check |
| First Monday                        | Discover updates and open candidate         |
| Monday-Tuesday                      | Build, migrate, and run automated tests     |
| Wednesday                           | Review failures and bot-created draft fixes |
| Thursday                            | Hosted staging UAT and release approval     |
| Friday or agreed maintenance window | Canary and production waves                 |

The exact rollout date remains operator-controlled. A failed candidate can be
deferred to the next cycle without changing production.

### 3.2 Exact Stack Replicas, Not Only One Superset Site

The test environment must contain:

1. One superset integration site with all mutually compatible custom apps.
2. One isolated replica for each of the five production stack topologies.
3. Controlled test tenants/connections through the separately hosted
   selfservice hub, using its currently deployed production version.

The superset site catches cross-app conflicts. It cannot replace exact stack
replicas because extra installed apps can register hooks, fields, permissions,
assets, and behavior that do not exist on an individual customer stack.

### 3.3 Immutable Versions

Every source repository must be pinned to a full Git commit SHA in a release
manifest. Branch names such as `version-16`, `main`, `develop`, `miki-dev`, and
`version-3` describe update channels but are not deployable version locks.

The production artifact must be identified by an immutable image digest or an
equivalent immutable release bundle. A branch checkout performed directly on a
production server is not a reproducible release.

### 3.4 Deterministic Test Policy

Mandatory test selection is rule-based. An AI agent may recommend or add tests,
but it may never remove a mandatory gate or mark a skipped test as passed.

Every Frappe or ERPNext update requires the full five-stack regression matrix.
Dependency-aware selection is used only for focused custom-app changes before
the final full release gate.

The process must also assess whether the predefined Playwright smoke suite still
covers the changed routes, workflows, permissions, and integrations. Required
test changes are made and reviewed during pre-production, then run against the
test environments. The approved Playwright revision is frozen with the Frappe
release and reused unchanged for production verification.

### 3.5 Human Production Approval

The bot may prepare and explain a release. It cannot merge its own changes,
approve its own changes, or access production deployment credentials.

### 3.6 Independent Selfservice Release Cycle

The selfservice hub is hosted outside Hetzner and has its own build, approval,
and deployment process. The monthly Frappe pipeline does not update or deploy
it.

During a Frappe update, the candidate Frappe stacks are tested against the
currently deployed selfservice production version. When a new selfservice
version is being prepared, its deployment process manually triggers the same
Frappe API-contract and browser compatibility tests before the selfservice
release is approved.

## 4. Current Starting Point

The bench already provides a strong base:

- Custom apps have individual GitHub Actions server-test workflows.
- The app dependency graph is documented in `AGENTS.md`.
- Browser and end-to-end suites are inventoried in `E2E_TESTING.md`.
- Python Playwright suites exist for MoPi, Barakah, MiKi, Good Event, Good Demo,
  and Good NPO.
- A TypeScript Playwright project exists for Payrexx Integration.
- Shared portal browser helpers live in `good_connector`.
- Hosted hub tenant mappings and environment restoration rules are documented.

Important gaps that must be closed before autonomous release decisions:

- Current app CI commonly fetches dependency branches without pinning commits.
- Per-app CI does not prove that one exact combination works across all stacks.
- Most custom Playwright suites run through `bench execute`, not a unified CI
  result adapter.
- Some runners can exit successfully while returning an internal failure,
  blocked result, or skip object.
- Hosted hub checks intentionally classify external failures separately, but
  those classifications are not yet aggregated into a release gate.
- The current browser suites are not all equivalent CI gates.
- Mutating Frappe and browser suites cannot safely run in parallel on one site.
- Clean-install tests do not prove that migrations work on production-shaped
  databases.

## 5. Information Required Before Implementation

Create and approve a fleet inventory containing the following for each of the
five production stacks:

| Field                   | Required information                                      |
| ----------------------- | --------------------------------------------------------- |
| Stack ID                | Stable non-customer-sensitive identifier                  |
| Production hostname     | Frappe site hostname                                      |
| Hetzner project/server  | Current hosting location                                  |
| Deployment model        | Docker Compose, Kubernetes, or traditional bench          |
| Frappe site name        | Exact site directory/database identity                    |
| Installed apps          | Output equivalent to `bench --site <site> list-apps`      |
| App source              | Repository URL and tracked branch                         |
| Current revision        | Exact deployed commit for every app                       |
| Custom app dependencies | Required installation order and optional hooks            |
| Selfservice tenant      | Hub tenant/NGO mapping, API route, and safe test identity |
| External services       | Email, Payrexx, bank, storage, CAPTCHA, webhooks          |
| Data size               | Database and public/private files size                    |
| Maintenance window      | Permitted rollout time                                    |
| Recovery objective      | Maximum acceptable downtime/data loss                     |
| Technical owner         | Person approving application behavior                     |
| Deployment approver     | Person approving production rollout                       |

The existing hosted hub mappings currently documented on this bench include:

| App           | Hosted hub NGO |
| ------------- | -------------: |
| `barakah_app` |              2 |
| `mopi_app`    |              9 |
| `miki_app`    |             11 |

These values must be confirmed for the fleet manifests rather than assumed for
all customer installations.

## 6. Required Accounts And Access

### 6.1 Git Hosting

- A private GitHub repository for fleet orchestration.
- Read access to every upstream, shared, and customer Frappe repository.
- A GitHub App owned by the organization.
- Permission for the GitHub App to create branches, draft pull requests,
  comments, checks, and artifacts in approved custom repositories.
- Protected default branches requiring tests and human review.
- A container registry, such as GitHub Container Registry or an existing
  private registry.

The GitHub App must not have permission to merge pull requests or modify branch
protection.

### 6.2 Hetzner

- A separate Hetzner project or clearly isolated network for integration tests.
- A test runner/build server or autoscaled ephemeral runner.
- Private networking between test databases and Frappe replicas.
- DNS names and TLS certificates for Frappe staging endpoints.
- Object storage for encrypted sanitized backups and test artifacts.
- Production access available only to the deployment workflow or operator, not
  the repair bot.

### 6.3 Notifications

Choose one primary operational channel:

- Microsoft Teams, Slack, Mattermost, or email.
- Optional GitHub issue/dashboard for durable monthly status.

The notification target must identify an accountable person or team. Reports
without an owner are not an operational process.

## 7. Infrastructure

### 7.1 Initial Sizing

A practical initial integration runner is:

- 8-16 vCPU.
- 32 GB RAM.
- At least 250 GB fast storage.
- Additional object storage for snapshots and artifacts.

The five stack tests should run in isolated environments. They may run in
parallel only when each has its own database, Redis services, Frappe site, and
browser test data. Tests against the same site must remain sequential.

Sizing must be adjusted after recording build, migration, browser, and storage
metrics from the first two monthly candidates.

### 7.2 Environment Layout

Recommended persistent services:

```text
GitHub Actions / scheduler
          |
Fleet controller runner
          |
Private container registry
          |
Hetzner integration network
  |-- stack-1 candidate environment
  |-- stack-2 candidate environment
  |-- stack-3 candidate environment
  |-- stack-4 candidate environment
  |-- stack-5 candidate environment
  |-- superset integration environment
  |-- mail capture service
  |-- provider mocks/sandboxes
  `-- artifact and log collector

Separately hosted selfservice (current production version)
          |
          `-- controlled test tenants call candidate Frappe endpoints
```

Candidate Frappe environments should be disposable. Persistent state belongs in
the encrypted snapshot store and release records, not in an indefinitely reused
test database.

### 7.3 Deployment Model Decision

During Phase 0, confirm whether production is Docker-based or traditional
bench. The recommended target is a custom immutable Frappe Docker image built
from the manifest. Existing traditional benches can still consume a generated
release bundle initially, but image-based deployment provides stronger
reproducibility and should be the long-term target.

Do not migrate all five production stacks to a new deployment model in the same
change that introduces the update pipeline. First make the current deployment
method reproducible, then migrate infrastructure separately.

## 8. Fleet Repository

Create a private repository named, for example, `goodvantage-fleet`:

```text
goodvantage-fleet/
|-- stacks/
|   |-- stack-1.yml
|   |-- stack-2.yml
|   |-- stack-3.yml
|   |-- stack-4.yml
|   `-- stack-5.yml
|-- releases/
|   |-- current.yml
|   `-- candidates/
|-- policy/
|   |-- test-policy.yml
|   |-- update-policy.yml
|   `-- repair-policy.yml
|-- tests/
|   |-- contracts/
|   `-- smoke/
|-- scripts/
|   |-- discover-updates
|   |-- resolve-manifest
|   |-- build-release
|   |-- provision-candidate
|   |-- restore-sanitized-site
|   |-- run-suite
|   |-- aggregate-results
|   `-- publish-report
|-- docker/
|-- schemas/
|   |-- fleet-manifest.schema.json
|   `-- test-result.schema.json
|-- runbooks/
|   |-- monthly-update.md
|   |-- production-rollout.md
|   |-- failed-migration.md
|   |-- rollback.md
|   `-- credential-rotation.md
`-- .github/workflows/
    |-- monthly-update.yml
    |-- security-update.yml
    |-- test-candidate.yml
    |-- manual-candidate.yml
    `-- promote-release.yml
```

This repository owns composition and deployment metadata. Business logic stays
inside the app repositories.

## 9. Release Manifest

The release manifest is the authoritative bill of materials for a candidate.

Example:

```yaml
schema_version: 1
release: 2026.08-rc1
created_at: "2026-08-03T06:00:00Z"
base_release: 2026.07

runtime:
  python: "3.14"
  node: "24"
  mariadb: "11.8"

apps:
  frappe:
    repository: https://github.com/frappe/frappe
    channel: version-16
    commit: <full-sha>
  erpnext:
    repository: https://github.com/frappe/erpnext
    channel: version-16
    commit: <full-sha>
  payments:
    repository: https://github.com/frappe/payments
    channel: develop
    commit: <full-sha>
  good_connector:
    repository: https://github.com/SpendeDirekt/good_connector
    channel: main
    commit: <full-sha>
stacks:
  stack-1:
    apps:
      - frappe
      - erpnext
      - good_connector
      - wiki
      - good_help
      - mopi_app
    selfservice_profile: mopi
    hosted_hub_ngo: 9
    migration_snapshot: stack-1-latest

external_integrations:
  selfservice:
    deployed_version: <externally-reported-version>
    test_profile: production-version-test-tenant

artifacts:
  frappe_image: <registry>/<image>@sha256:<digest>
  sbom: artifacts/sbom.spdx.json

verification:
  playwright_suite_commit: <full-sha>
```

The real manifest must list every direct and transitive application needed to
build and install each stack. Installation order is derived from the documented
dependency graph and validated during clean-install tests.

## 10. Monthly And Security-Triggered Update Workflow

### 10.1 Discovery

The monthly workflow performs the following for all configured update channels.
The regular security monitor performs steps 1-4 against official security
sources and continues with the same candidate workflow only when a relevant
security update is found:

1. Load the currently deployed release manifest.
2. Fetch the latest commits from every configured update channel.
3. Read release notes and security advisories published since the prior run.
4. Run dependency audits for the Frappe fleet's Python, Node, and container
   packages.
5. Calculate which source revisions differ.
6. Produce a machine-readable update inventory.
7. Stop without opening a PR if no relevant revision or dependency changed.

The security monitor records the advisory identifier, affected version range,
source URL, detection time, and reason each stack is considered affected. It
must deduplicate advisories so the same event does not create repeated
candidates.

Security relevance starts with deterministic checks:

- Is the component installed in any stack?
- Does the affected version range include the current revision/package?
- Is the vulnerable dependency included in the built artifact?
- Which stacks contain the component?

AI may summarize impact but must not override these checks silently.

### 10.2 Candidate Creation

When updates exist:

1. Create `releases/candidates/YYYY.MM-rc1.yml`.
2. Pin proposed upstream commits.
3. Keep custom apps on their currently approved SHAs initially.
4. Record the currently deployed selfservice version used for compatibility
   testing without including it in the Frappe update.
5. Assess the changed behavior against the predefined Playwright smoke suite
   and update its specifications where coverage must change.
6. Open one draft fleet pull request.
7. Attach release notes, advisories, changed components, affected stacks, and
   the proposed Playwright suite revision.

Do not open empty update PRs in every custom repository. A custom-app PR is
created only when that app needs a compatibility fix or intentional update.

### 10.3 Build

The build job must:

1. Clone every repository at the manifest SHA.
2. Refuse dirty trees, unresolved branches, or unpinned sources.
3. Install locked Python and Node dependencies.
4. Build Frappe assets.
5. Build immutable candidate images or release bundles.
6. Generate an SBOM.
7. Scan images and dependencies.
8. Push candidate artifacts to a private registry.
9. Record image digests back into the candidate report.

The artifact tested in staging must be the artifact promoted to production.
Rebuilding after approval would create an untested release.

## 11. Test Result Contract

Before browser suites become release gates, every test entrypoint must produce a
strict result conforming to one schema:

```json
{
  "schema_version": 1,
  "suite": "miki-local-browser",
  "stack": "stack-3",
  "target": "local",
  "status": "passed",
  "started_at": "2026-08-03T08:30:00Z",
  "duration_seconds": 412,
  "scenarios": {
    "passed": 17,
    "failed": 0,
    "blocked": 0,
    "not_executed": 0
  },
  "artifacts": [],
  "external_boundaries": []
}
```

Allowed suite statuses:

| Status         | Meaning                                                | Release effect          |
| -------------- | ------------------------------------------------------ | ----------------------- |
| `passed`       | All mandatory assertions passed                        | Gate passes             |
| `failed`       | Application or test assertion failed                   | Gate fails              |
| `blocked`      | Explicit external/environment prerequisite unavailable | Human decision required |
| `not_executed` | Suite did not run                                      | Gate fails if mandatory |

Requirements:

- A failed mandatory scenario must produce a non-zero command exit.
- Returning `{"ok": false}`, `{"error": ...}`, or a failed step with exit 0
  must be converted into a failed process.
- A blocked hosted provider is not reported as an application pass.
- A skipped mandatory suite is never counted as successful.
- Test artifacts must be attached to the matching suite result.
- Secrets, cookies, JWTs, login URLs, CAPTCHA values, and provider credentials
  must be redacted before artifact upload.

## 12. Test Matrix

### 12.1 Gate A: Static And Supply Chain

- Manifest schema validation.
- Commit existence and repository allowlist validation.
- App dependency graph validation.
- Python lint and formatting checks for changed custom apps.
- JavaScript lint/format checks for changed hub/apps.
- Frappe semgrep rules.
- `pip-audit` for Python packages.
- Node dependency audit for the hub and Playwright projects.
- Container scan.
- Secret scan.
- SBOM generation.

### 12.2 Gate B: Clean Installation

For each unique stack topology:

1. Create a new empty site.
2. Install apps in dependency order.
3. Complete the ERPNext setup needed by tests.
4. Run `bench migrate` a second time to prove idempotency.
5. Build assets.
6. Start web, scheduler, workers, Redis, and websocket services.
7. Verify login, Desk boot, background jobs, and static assets.
8. Verify installation does not modify tracked fixture files.

Also run this gate on the superset site.

### 12.3 Gate C: Production-Shaped Migration

For each stack:

1. Provision an isolated database and file volume.
2. Restore the latest approved sanitized snapshot.
3. Install the candidate artifact without changing the snapshot baseline.
4. Record pre-migration schema and row-count checksums for selected critical
   doctypes.
5. Run `bench migrate` once.
6. Fail on patch, schema, hook, fixture, or background-job errors.
7. Validate installed app versions and patch log state.
8. Run stack-specific data integrity checks.
9. Start all services and execute smoke tests.
10. Record migration duration and storage growth.

Migration tests must never send real email, webhooks, payments, SMS, or bank
traffic.

### 12.4 Gate D: Server Tests

- Run full custom-app tests for every app installed in the candidate stacks.
- Run tests sequentially per site.
- Use separate sites when running stack jobs in parallel.
- Capture JUnit or equivalent structured results.
- Capture Frappe site logs, worker logs, and Error Log records on failure.
- Treat setup/bootstrap failures separately from test assertion failures.

For a Frappe or ERPNext update, run the complete custom-app server suite even if
the upstream diff appears unrelated.

### 12.5 Gate E: Local Browser Regression

Run the applicable Playwright suites documented in `E2E_TESTING.md`, including:

- MoPi Desk, tasks, training, certificates, portal contracts, and files.
- Barakah public forms, Aqeeqa/Well lifecycle, portal contracts, and files.
- MiKi declaration, billing, dunning, correspondence, portal contracts, and
  files.
- Good Event registration, organization cases, coupons, persistence, email,
  and mobile behavior where installed.
- Good Demo/Good NPO signup, membership, donation, checkout, email, and mobile
  flows where installed.
- Payrexx settings and signed payment URL behavior where installed.

Each mutating suite runs with one worker against its own site. Desktop and
mobile-specific assertions remain explicit; the pipeline does not simply rerun
all desktop cases at a narrow width.

On failure, retain:

- Screenshot.
- Playwright trace.
- Video when configured.
- Browser console errors.
- Relevant network responses.
- Frappe traceback and worker logs.
- Redacted test result JSON.

### 12.6 Gate F: Selfservice Contract Tests

Test the boundary between each Frappe stack and the selfservice hub separately
from the browser UI:

- Login token creation and validation.
- Correct tenant/NGO routing.
- Process list visibility and terminal-state handling.
- Declaration/task data reads and writes.
- Final submission and idempotency.
- File list, URL resolution, upload, and permitted deletion.
- App-context isolation between portal endpoints.
- Archived/closed process visibility.
- API response compatibility for legacy hosted payloads.
- Authentication failure behavior.
- Rate-limit and permission failure behavior.

Contract fixtures must contain no production credentials or personal data.

### 12.7 Gate G: Hosted Staging UAT

Deploy candidate Frappe images into the Hetzner staging environment, then run
browser tests through the separately hosted, currently deployed selfservice
version using controlled test tenants.

When the selfservice team prepares its own release, that deployment pipeline
manually invokes this gate against approved Frappe test endpoints. The
selfservice release remains owned and deployed by its independent process.

Hosted outcomes must distinguish:

- Passed in the browser.
- Failed in the Frappe application.
- Failed in the selfservice hub.
- Failed at an external provider boundary.
- Blocked by credentials, CAPTCHA, unavailable sandbox, or missing test data.
- Not executed.

A direct Frappe API success does not prove the hub wrapper works. A hosted hub
failure does not automatically prove a Frappe regression. The report must show
which boundary failed.

### 12.8 Gate H: Payment And Bank Interfaces

Ordinary CI uses provider mocks or official sandboxes.

Required checks:

- Signed payment URL generation and tamper rejection.
- Webhook signature verification.
- Duplicate webhook idempotency.
- Success, failure, waiting, chargeback, and unknown status handling as
  applicable.
- No real provider action from local tests.
- Bank export/import schema validation with synthetic fixtures.
- Duplicate bank message protection.
- Partial failure and retry behavior.
- Correct accounting/document links without real settlement.
- Redaction of IBANs, API keys, and customer identity in logs.

Any real provider or bank test must be a separately approved staging UAT step
with a clearly identified sandbox account.

## 13. Sanitized Production Snapshots

### 13.1 Purpose

Fresh sites do not reveal failures caused by old patches, large child tables,
historical workflows, custom fields, unexpected configuration, or production
data shape. Each stack therefore needs a sanitized migration snapshot.

### 13.2 Snapshot Process

1. Create a normal encrypted production backup.
2. Restore it only inside an isolated sanitization environment.
3. Replace names, addresses, emails, phone numbers, notes, and other personal
   data.
4. Remove API keys, OAuth tokens, SMTP credentials, webhook secrets, encryption
   secrets not needed for the test, bank credentials, and stored sessions.
5. Replace payment and bank identifiers with valid synthetic values where tests
   require their format.
6. Disable schedulers and all external delivery.
7. Remove or replace private file contents containing personal data.
8. Verify anonymization with automated checks.
9. Encrypt and upload the sanitized artifact to restricted object storage.
10. Delete the temporary unsanitized restore.

The sanitization job should be operator-controlled initially. It can become
scheduled only after the deletion and privacy controls have been reviewed.

### 13.3 Snapshot Retention

- Keep the latest approved sanitized snapshot per stack.
- Keep one previous snapshot for comparison and recovery of the test process.
- Apply a defined retention period to test artifacts.
- Keep production backups under the existing production backup policy; do not
  mix them with CI artifacts.

## 14. Automated Failure Classification

The fleet controller classifies failures before invoking an AI repair agent.

Deterministic classes include:

- Build or dependency resolution failure.
- Clean install failure.
- Migration/patch failure.
- Server test assertion failure.
- Browser assertion failure.
- Stale or unavailable test environment.
- External hub/provider failure.
- Permission or authentication regression.
- Fixture working-tree drift.
- Timeout/deadlock/resource exhaustion.
- Known local infrastructure issue.

Examples already documented for this bench must be encoded into triage rules:

- Do not run multiple `bench run-tests` commands against one site in parallel.
- A stale local web process can produce misleading missing-app errors.
- Hosted hub file listing and hosted file download are separate boundaries.
- Hub tenant settings must be restored after each test.
- A shell exit code of 0 does not prove all current browser cases passed.
- Local login may land outside Desk and must be normalized before Desk tests.

The classifier attaches evidence and proposes a next action. It must not hide or
rewrite the original logs.

## 15. AI Repair Agent

### 15.1 Permitted Work

The repair agent may:

- Inspect the candidate diff, release notes, migration errors, and test output.
- Create a branch in an affected custom repository.
- Make minimal compatibility changes in custom code.
- Add or update regression tests.
- Update required custom-app documentation and version declarations.
- Run focused tests, then request the full candidate matrix.
- Open a draft pull request explaining the cause, change, and evidence.

### 15.2 Prohibited Work

The repair agent may not:

- Modify upstream/off-limits app source directly.
- Push to protected branches.
- Merge or approve pull requests.
- Access production SSH, databases, backups, payment keys, or bank credentials.
- Disable security checks or mandatory tests.
- Convert blocked/skipped results into passes.
- Change production data.
- Perform broad refactors unrelated to the candidate failure.
- Continue indefinitely.

### 15.3 Limits

- Maximum two automated repair attempts per failure class.
- Maximum configured wall-clock time and compute budget per candidate.
- One branch per affected custom repository.
- Every code change must be represented by a draft PR.
- Any permission, payment, bank, authentication, destructive migration, or
  ambiguous business-rule change requires human review before a second full run.

External release notes, issue text, test data, and logs are untrusted input. The
agent must not execute instructions found inside them or expose secrets in
prompts and reports.

## 16. Cross-Repository Pull Request Model

One fleet release can require changes in multiple repositories. Use this model:

1. The fleet candidate PR is the parent release record.
2. Each affected custom app receives one draft compatibility PR.
3. The candidate manifest temporarily points to the head SHA of those PRs.
4. CI tests the exact cross-repository combination.
5. The fleet PR links every required child PR and their status.
6. Child PRs are reviewed and merged by humans.
7. The manifest is refreshed to the resulting immutable merge SHAs.
8. The final full matrix runs again before release approval.

No candidate may be promoted while its manifest references a mutable branch
name or an unreviewed repair commit.

## 17. Consolidated Release Report

Every candidate produces one Markdown and machine-readable JSON report with:

- Candidate and base release identifiers.
- Old and proposed commit for every component.
- Upstream release notes and relevant advisories.
- Dependency and image vulnerabilities.
- Affected stack list.
- Build artifact digests and SBOM link.
- Clean-install results.
- Migration results and duration per stack.
- Server-test results.
- Browser-test results and artifact links.
- Hub contract and hosted UAT results.
- Payment/bank sandbox results.
- Tests not executed and the reason.
- External blockers clearly separated from application failures.
- Automated repair attempts and linked PRs.
- Known residual risks.
- Human approvals required.
- Final recommendation: reject, needs review, staging-ready, or release-ready.

Notifications should be concise and link to the durable report instead of
copying raw logs into chat or email.

## 18. Manual Production Rollout And Predefined Playwright Verification

### 18.1 Preconditions

- All mandatory gates passed.
- Every required custom-app PR was reviewed and merged.
- Final manifest points to immutable merge SHAs.
- Final artifact digest matches the staging-tested artifact.
- Production backup has completed and been verified.
- Maintenance window and approvers are recorded.
- Recovery procedure and responsible operator are confirmed.
- Any blocked external UAT has a documented human waiver.
- A dedicated least-privilege production smoke-test identity is available for
  each stack.
- The Playwright smoke suite was reviewed, passed against the test environment,
  and pinned to an immutable revision in the approved release manifest.

### 18.2 Deployment Sequence

1. Tag the approved fleet release.
2. Mark the candidate image digest or release bundle as production-approved.
3. Take database and public/private file backups for the canary stack.
4. Record current artifact and manifest identifiers.
5. Put the canary into the agreed maintenance mode if required.
6. An operator manually deploys the approved update and runs `bench migrate`.
7. The operator confirms that services have started and triggers the predefined
   production Playwright smoke suite with the stack and expected release
   identifiers and pinned Playwright suite revision.
8. The Playwright workflow validates the target against its production
   allowlist and runs the reviewed, safe stack-specific tests without an LLM.
9. The workflow publishes a pass/fail report for that stack.
10. Observe logs, queues, scheduler, and external callbacks for an agreed period.
11. Continue manually with the next stack only after the previous stack's
    Playwright smoke suite passes.
12. Stop the rollout immediately if a production smoke gate fails.
13. Publish the actual deployed manifest and smoke result per stack.

The canary should be the lowest-risk representative stack, not necessarily the
smallest database. It should exercise the shared infrastructure most likely to
be affected by the update.

### 18.3 Predefined Production Playwright Smoke Checks

Production smoke tests are read-only and non-destructive by default. They run
through public HTTPS endpoints and dedicated least-privilege test identities;
the Playwright runner receives no production SSH, database, payment, bank, or
administrator credentials. The suite is defined, reviewed, and approved before
the production rollout. It does not use an LLM to generate, select, modify, or
interpret tests during the production run. Any explicitly approved synthetic
transaction must use a durable test marker and guaranteed cleanup, and is
outside the default smoke suite.

The suite may be changed earlier in the monthly process when the proposed
Frappe update changes behavior. Those changes follow the normal pull-request
review and test process. Once the release is approved, the suite is frozen; the
production run may not edit or regenerate it.

- HTTPS, login page, static assets, and API availability.
- Authenticated Desk boot using the dedicated smoke-test identity.
- Expected release/version identifiers exposed by the deployment record.
- Read-only permission checks for critical stack-specific doctypes.
- Selfservice login with a dedicated test identity and read-only process calls.
- Existing marked test-file download through Frappe and the hub wrapper where
  applicable.
- Payment/bank endpoint availability without creating a transaction.
- No unexpected HTTP errors in the tested browser/API journeys.
- Error rate and latency within expected bounds during the observation window.

Scheduler, worker, queue, migration, and import health remain part of the
operator's deployment verification and monitoring because externally granting
the Playwright runner enough production access to inspect them would violate
least privilege.

## 19. Recovery And Rollback

Frappe migrations and patches are frequently not reversible. Reverting only the
application image can leave a database on a newer schema and patch state.

The recovery unit is therefore:

- Previous application artifact.
- Matching database backup.
- Matching public/private files backup.
- Matching site configuration and secret references.

Recovery procedure:

1. Stop incoming writes or enable maintenance mode.
2. Preserve failed-state logs and database metadata for diagnosis.
3. Restore the pre-deployment database and files together.
4. Deploy the previous approved artifact digest.
5. Restore the previous manifest/configuration references.
6. Start services.
7. Run recovery smoke tests.
8. Reconcile any external transactions received during the failed window.
9. Document whether the candidate requires a forward fix instead of another
   rollback attempt.

The rollback procedure must be rehearsed on staging before the first production
rollout driven by this pipeline.

## 20. Security And Secret Management

- Store secrets in GitHub Environments, an existing secrets manager, or
  encrypted Hetzner deployment configuration.
- Separate build/test, staging, and production credentials.
- Give CI only staging/sandbox provider credentials.
- Use OIDC or short-lived credentials where supported.
- Prefer a GitHub App over personal access tokens.
- Do not embed tokens in clone URLs in logs or generated manifests.
- Protect production deployment with a GitHub Environment approval gate or an
  equivalent approval system.
- Restrict sanitized snapshots and test artifacts by role.
- Redact all reports before upload.
- Retain an audit trail of candidate creation, approvals, deployment, and
  recovery operations.
- Rotate bot and staging credentials on a defined schedule.

## 21. Observability

Collect at least:

- Build duration and failure rate.
- Migration duration per stack.
- Test duration and flake rate per suite.
- Candidate-to-approval lead time.
- Number of automated repair attempts and acceptance rate.
- Image and database size changes.
- Worker, scheduler, queue, and web health after deployment.
- Post-release application errors for the observation window.
- Number and age of deferred updates.

Use these measurements to improve the pipeline. Do not respond to slow tests by
silently removing release coverage.

## 22. Roles And Responsibilities

| Role                 | Responsibility                                                                |
| -------------------- | ----------------------------------------------------------------------------- |
| Fleet owner          | Owns manifests, policy, monthly schedule, and final status                    |
| Application owner    | Reviews behavior and compatibility changes                                    |
| Infrastructure owner | Owns Hetzner, registry, backups, networking, and deployment                   |
| Security reviewer    | Reviews advisories, scans, and security-sensitive fixes                       |
| Release approver     | Authorizes the manual production rollout                                      |
| Bot/agent            | Discovers, builds, tests, classifies, proposes, and reports before production |
| Playwright runner    | Runs only the predefined production smoke suite after manual deployment       |

One person may hold several roles, but the bot cannot hold a human approval
role.

## 23. Implementation Phases

### Phase 0: Inventory And Decisions

Estimated effort: 2-4 working days.

Deliverables:

- Five-stack inventory.
- Exact current production revisions.
- Confirmed production deployment model.
- Selfservice and bank-interface repository inventory.
- Chosen GitHub organization/repository locations.
- Chosen notification channel.
- Named owners and approvers.
- Agreed maintenance and recovery objectives.

Acceptance criteria:

- Every deployed component maps to a repository and exact revision.
- Every stack has an authoritative installed-app list.
- No production dependency is undocumented.

### Phase 1: Fleet Repository And Reproducible Build

Estimated effort: 4-7 working days.

Deliverables:

- `goodvantage-fleet` repository.
- Manifest and JSON schemas.
- Stack manifests.
- Current release import.
- Candidate image/release build.
- Registry publishing.
- SBOM and vulnerability scan.
- Manual candidate workflow.

Acceptance criteria:

- Two builds from one manifest produce functionally identical artifacts.
- Every source revision is immutable and recorded.
- A candidate can be provisioned without reading branch heads during deploy.

### Phase 2: Strict Test Result Layer

Estimated effort: 1-2 weeks.

Deliverables:

- Common test-result schema.
- Adapters for `bench run-tests` and `bench execute` browser suites.
- Strict exit behavior for false/error/skipped result objects.
- JUnit/result aggregation.
- Artifact redaction and upload.
- Site-level execution locks.
- Updated `E2E_TESTING.md` commands where required.

Acceptance criteria:

- An intentionally failing scenario always fails its CI job.
- A blocked hosted boundary is visible and never counted as passed.
- Every mandatory suite produces a result record.

### Phase 3: Isolated Stack Environments

Estimated effort: 1-2 weeks.

Deliverables:

- Disposable environment template.
- Five exact stack definitions.
- Superset integration site.
- Connection from controlled selfservice test tenants to candidate Frappe
  environments.
- Mail capture and provider mocks/sandboxes.
- Clean-install matrix.
- Local browser matrix.

Acceptance criteria:

- All five stack topologies install from scratch.
- Tests can run concurrently across isolated stacks without collisions.
- No environment can send unintended real email/payment/bank traffic.

### Phase 4: Production-Shaped Migration Tests

Estimated effort: 1-2 weeks, depending on data and privacy review.

Deliverables:

- Snapshot sanitization procedure.
- One approved sanitized snapshot per stack.
- Restore and migration automation.
- Data integrity smoke checks.
- Snapshot retention and access policy.

Acceptance criteria:

- Every candidate migrates all five snapshots in isolation.
- Automated checks find no retained production secrets or direct identities.
- Migration failure evidence is retained without exposing customer data.

### Phase 5: Monthly Discovery, Security Monitoring, And Reporting

Estimated effort: 4-7 working days.

Deliverables:

- Monthly schedule.
- Regular Frappe security advisory/release monitor.
- Security-triggered candidate workflow with advisory deduplication.
- Manual dispatch workflow.
- Upstream/dependency discovery.
- Candidate manifest PR creation.
- Playwright smoke-suite impact review and required test updates.
- Consolidated Markdown/JSON report.
- Operational notifications.

Acceptance criteria:

- A dry run identifies changes since the current release correctly.
- A relevant simulated security advisory triggers the normal candidate process
  without deploying anything.
- An irrelevant or already-processed advisory creates no duplicate candidate.
- No-change months close cleanly without creating noise.
- One report shows the status of all stacks and test layers.
- The approved release records the exact Playwright revision that passed
  pre-production testing.

### Phase 6: Constrained AI Repair

Estimated effort: 1-2 weeks after deterministic CI is stable.

Deliverables:

- Repair-agent sandbox.
- Repository allowlist and permission boundaries.
- Attempt/time limits.
- Failure-class prompts and evidence package.
- Cross-repository draft PR linking.
- Audit logs.

Acceptance criteria:

- The agent cannot merge, deploy, or access production.
- Every change is reviewable in a draft PR.
- Failed repair attempts leave the original failure visible.

### Phase 7: Manual Production Rollout, Playwright Verification, And Recovery

Estimated effort: 1-2 weeks.

Deliverables:

- Approval-gated manual rollout procedure.
- Manually triggered predefined Playwright production smoke workflow.
- Reviewed production Playwright specifications, least-privilege test
  identities, and target allowlist.
- Canary selection and wave strategy.
- Pre-deployment backup verification.
- Post-deployment smoke tests.
- Recovery runbook.
- Staging rollback rehearsal.

Acceptance criteria:

- The exact staging-tested digest is deployed.
- Manual deployment cannot start without approval and backup confirmation.
- Every deployed stack must pass its predefined Playwright smoke suite before the next rollout
  wave begins.
- A staging rollback restores code, database, and files consistently.

### Overall Estimate

An initial trustworthy version is approximately 6-10 weeks of focused work,
depending mainly on:

- How uniform the five current deployments are.
- Whether immutable images are already used.
- How much work is needed to make browser suites strict and repeatable.
- The complexity of sanitizing customer databases and files.
- Availability of controlled selfservice test tenants and payment/bank
  sandboxes.

The pipeline should begin operating without AI repair after Phase 5. AI repair
is an enhancement, not a prerequisite for monthly automated testing.

## 24. First Implementation Backlog

Execute these items in order:

1. Export the installed-app and current-commit inventory from all five stacks.
2. Document the selfservice endpoint, deployed-version identification, tenant
   mapping, safe test identities, and manual compatibility-test trigger.
3. Document the bank-interface boundaries and available sandbox/mock format.
4. Decide whether the first release artifact is a Docker image or a traditional
   bench release bundle.
5. Create the private fleet repository.
6. Define and validate the release-manifest schema.
7. Import the currently deployed fleet as the baseline manifest.
8. Build the baseline artifact from pinned SHAs.
9. Create one exact clean-install environment for the simplest stack.
10. Add the strict test-result adapter around one existing Playwright suite.
11. Prove that an intentional browser failure fails CI and retains artifacts.
12. Expand the environment and adapter pattern to the remaining stacks.
13. Create and review the first sanitized migration snapshot.
14. Run a complete baseline matrix without proposing any updates.
15. Implement monthly update discovery, regular Frappe security monitoring, and
    candidate PR creation.
16. Run one monthly candidate fully manually and refine the runbooks.
17. Add approval-gated staging promotion.
18. Rehearse backup restoration and rollback in staging.
19. Add the constrained repair agent only after test results are trusted.
20. Enable production canary promotion after two successful non-production
    monthly rehearsals.

## 25. Definition Of Done

The update pipeline is operational when:

- All five production stacks have reviewed manifests with immutable revisions.
- One command or workflow creates a monthly candidate.
- Relevant Frappe security updates trigger the same candidate process between
  monthly cycles.
- The candidate builds an immutable artifact and SBOM.
- Every exact stack passes clean installation.
- Every sanitized production-shaped stack passes migration.
- Every mandatory server and browser suite produces strict structured results.
- Required production Playwright smoke tests are updated during pre-production,
  reviewed, passed, and pinned before deployment.
- The currently deployed selfservice version is tested against candidate
  Frappe stacks through controlled test tenants.
- The selfservice deployment process can manually trigger the compatibility
  suite without joining the monthly Frappe release cycle.
- Payment and bank boundaries are tested without production transactions.
- Reports distinguish application, hub, provider, environment, blocked, and
  not-executed outcomes.
- Compatibility changes are represented by linked draft PRs.
- Human approval is required for merge and manual production rollout.
- Every manual production update triggers the predefined, non-LLM Playwright
  production smoke suite and records its result before rollout continues.
- The exact tested artifact is deployed by digest/release ID.
- Canary and wave rollouts are implemented.
- Backup verification and recovery runbooks have been rehearsed.
- Production credentials are unavailable to the discovery and repair agents.
- Two consecutive monthly rehearsals complete successfully before unattended
  candidate creation is enabled.

## 26. Decisions To Confirm During Phase 0

The following do not block this plan but must be resolved before implementation:

1. Exact app composition of each of the five stacks.
2. Current production deployment method for each stack.
3. Whether all stacks can consume one shared Frappe image or require separate
   images because their app sets or private dependencies differ.
4. Selfservice test tenant/endpoint, deployed-version identifier, and manual
   trigger contract.
5. Bank-interface protocol and available non-production test facilities.
6. Preferred private container registry.
7. Preferred secret manager and approval mechanism.
8. Notification channel and named release owner.
9. Which stack is the production canary.
10. Required retention periods for sanitized snapshots and test evidence.

These decisions should be recorded in the fleet repository rather than left as
pipeline configuration known only to one operator.
