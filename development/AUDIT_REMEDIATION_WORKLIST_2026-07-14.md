# Audit Remediation Worklist - 2026-07-14

Progress tracker for implementing `CUSTOM_APPS_AUDIT_2026-07-14.md`.

The audit report's Complete Remediation Register remains the authoritative
finding inventory. This file records implementation order, commits, tests,
compatibility risks, and deferred decisions while the ten waves are executed.

## Rules

- Preserve existing public endpoint names and response contracts unless the
  audit explicitly requires a security rejection.
- Add regression coverage before or with each behavior change.
- Run Frappe test commands sequentially on `development16.localhost`.
- Commit only files changed for the current wave; never include unrelated dirty
  worktree changes.
- Update each custom app's `HOW_TO.md` and `DOCUMENTATION.md` when behavior or
  operational procedure changes.
- Record functionality risks and migration/reconciliation needs before marking
  a wave complete.

## Wave Status

| Wave | Scope | Status | App commits | Verification | Compatibility / operational notes |
|---|---|---|---|---|---|
| 1 | Payrexx settlement, duplicate checkout, deadlock atomicity, chargeback exception | Complete | `payrexx_integration` `82682d6` | 35 tests passed | Signed links/callback response preserved; unrecoverable legacy active checkout fails closed; historical reconciliation required |
| 2 | Donation allocation, company, and account invariants | Complete | `non_profit` `4221bca` | Focused 15 passed; full app suites passed | Existing over-allocation reported for manual review; stricter validation intentionally rejects stale drafts and alternate accounts |
| 3 | Newsletter Jinja, private files, and SNS | Complete | `good_newsletter` `ad537d5` | 8 unit + 119 integration tests passed | Undocumented/privileged templates now fail; raster images only; SNS requires configured Topic ARN |
| 4 | Good Demo payment/provenance isolation | Complete | `good_npo` `6e49e03`; `good_demo` `6a9cb1f` | Migrate passed; Good NPO 66 passed/1 skipped; Good Demo 72 passed | Existing demo sites must set both flags; disabled mode preserves 631 marked records for review |
| 5 | Portal certificate, assignment file, and staged-upload authorization | Complete | `good_connector` `88a8740`; `mopi_app` `77aed76` | Migrate passed; Good Connector 149 passed; MoPi 109 passed/1 skipped | Completed process history and endpoint payloads preserved; generic StartProcess now requires an explicit allowlist |
| 6 | Good Event Jinja and attachment authorization | Complete | `good_event` `f8f6d3d` | 11 unit + 36 integration + 470 legacy tests passed (517 total) | Staff-authored template extensions are intentionally restricted; persisted attachment URLs must resolve to approved Files |
| 7 | Analytics, MiKi, and Good Help permission boundaries | Complete | `good_analytics` `ddabe08`; `miki_app` `a1a7260`; `good_help` `b8acd26` | Migrate passed; Good Analytics 43 passed; MiKi 318 passed; Good Help 61 passed | System-wide analytics now requires a trusted non-demo role; case acceptance requires billing authority; readiness reads are side-effect-free; mapped private Wiki routes/files enforce the Good Help role tier |
| 8 | Barakah parent workflow completion reliability | Complete | `barakah_app` `619ef04` | Focused success/rollback tests passed; full app 111 passed | Successful response contract preserved; parent/follow-up failures now roll back the portal completion unit and return a logged HTTP 409 |
| 9 | Measured performance and deduplication fixes | Complete | `good_connector` `396282a`; `good_help` `8da50dc`; `mopi_app` `6c2000a`; `barakah_app` `ec9dc2c`; `non_profit` `04755e3`; `good_npo` `0885138`; `good_demo` `7fc6705`; `miki_app` `6c27ddb`; `workflow_visualizer` `1d1cf1d`; `good_event` `c3321ef`; `good_newsletter` `eb90505`; `good_analytics` `ea9e62e` | Query-count/contract regressions added across all affected services; MiKi 321 passed; Barakah 114 passed; Good Event full 542 passed before final review fixes, then migration and focused 17 + 7 + 4 + 6 + 128 suites passed | Stable ordering, permission checks, public response shapes, and compatibility dotted paths preserved; B08 and structural/telemetry-gated cleanup remain Wave 10 |
| 10 | Structural cleanup and compatibility-isolated removals | Complete | `mopi_app` `d6b53e3`; `barakah_app` `76daf12`, `4972c8f`; `good_event` `083e9ae`, `0002cde`, `69c1dbc` (plus dispatch fix `fae75e6`); `non_profit` `c11c65c`; `payrexx_integration` `455ca43`; `good_npo` `a70e732`; `good_demo` `de0c4f9`; `miki_app` `5f562e7` | Shared setup, domain-facade, payment/fundraising, seed-registry, MiKi cleanup, and compatibility suites passed sequentially; Ruff and diff checks passed | Public orchestration, response envelopes, queued-job aliases, and compatibility dotted paths preserved; B28/B39 instrumented; B40 removals held pending production telemetry |

## Decisions

| Finding | Decision |
|---|---|
| H4 MoPi certificate issuers | Restrict issuance to `MoPi Manager` or a dedicated issuer role; ordinary `MoPi User` is not an issuer. |
| H13 Payrexx chargebacks | Preserve submitted accounting records and create an idempotent, linked accounting exception for manual reversal rather than silently cancelling ledger entries. |
| Compatibility-sensitive APIs | Keep stable dotted paths and use thin facades until production telemetry supports removal. |

## Progress Log

### Wave 1

- Started 2026-07-14.
- Repository `payrexx_integration` was clean at start (`a476324`).
- Planned findings: C3, H12, H13, H14.
- Required regression evidence: one checkout per first click; one Payment Entry
  per confirmed Payment Request; callback state and settlement commit together;
  deadlock retries the whole completion unit; repeated chargebacks create one
  linked accounting exception.
- Completed in `payrexx_integration` commit `82682d6`.
- Full app suite: 35 tests passed in 17.287 seconds.
- Confirmed behavior: submitted Payment Request URL is reused; confirmed
  Payment Request creates one submitted Payment Entry and clears invoice
  outstanding; duplicate confirmations are no-ops; deadlock retries reload and
  replay the complete locked unit; chargebacks preserve ledger records and
  create one high-priority ToDo.
- Compatibility risk: a legacy active Integration Request with neither a
  Payment Request URL nor stored checkout URL now raises a review error instead
  of creating another potentially chargeable Payrexx checkout.
- Operational follow-up: run a read-only historical reconciliation of completed
  Payrexx Integration Requests against Payment Requests, Payment Entries, and
  Sales Invoice outstanding before repairing old data.

### Wave 2

- Started 2026-07-14.
- Planned findings: H1, H2, and the accounting-invariant part of B19.
- Completed in `non_profit` commit `4221bca`.
- Focused Donation suite: 15 tests passed.
- Full app result reported by the implementation run: 21 integration tests,
  64 legacy tests (2 skipped), and 32 unspecified tests passed.
- Final read-only audit: 142 submitted Donation references; one overallocated
  Donation; zero company mismatches; zero party-account mismatches.
- Manual review required: Donation `NPO-DTN-2026-00436`, amount 123, submitted
  allocation 369, excess 246, Payment Entries `ACC-PAY-2026-00052`,
  `ACC-PAY-2026-00053`, and `ACC-PAY-2026-00055`. No submitted records were
  changed by remediation.
- Compatibility risk: stale drafts, fully allocated Donations, cross-company
  references, and same-company alternate receivable accounts now fail instead
  of posting an inconsistent ledger entry.

### Wave 3

- Started 2026-07-14.
- Planned findings: C1 (Newsletter), H10, M3, and closely related Newsletter
  rendering/file/SNS tests.
- Completed in `good_newsletter` commit `ad537d5`.
- Full app suite: 8 unit and 119 integration tests passed (127 total).
- All manager-authored rendering now uses one scalar-only immutable sandbox;
  documented merge fields, conditions, and safe filters remain supported.
- Automatic publicization is limited to authorized PNG/JPEG/GIF/WebP image
  fields and inline image sources; links, anchors, SVG, BMP, mismatched content,
  and unreadable Files are rejected or left private.
- SNS verification requires exact Topic ARN and canonical regional SNS URLs,
  disables redirects, and records subscription idempotency before network IO.
- Persisted `verify_sns_signature` was confirmed enabled after tests.
- Compatibility risks: templates using Frappe globals, object methods,
  undocumented variables, or privileged calls now fail by design. GovCloud and
  China SNS partitions are not accepted by the standard AWS-region validator.
- Operational action: the development site has no `sns_topic_arn`; enter the
  deployment's real ARN before expecting verified SNS processing.

### Wave 4

- Started 2026-07-14.
- Planned findings: C2, H6, and the demo-isolation portion of B20.
- Completed in `good_npo` commit `6e49e03` and `good_demo` commit `6a9cb1f`.
- `bench migrate` passed. Good NPO: 66 passed, 1 skipped. Good Demo: 72
  passed.
- Guest gateway/provider parameters remain wire-compatible but are ignored and
  never forwarded; server configuration/providers select checkout behavior.
- Dummy checkout, confirmation, decoration, seeding, reset, refill, retention,
  and demo login provisioning now require both `developer_mode = 1` and
  `good_demo_mode = 1`.
- Good NPO no longer knows demo marker/email/language fields. Downstream hooks
  decorate records only inside a trusted demo creation context.
- Company resolution now starts from Non Profit Settings; ambiguous or
  cross-company default campaigns are omitted. The Good NPO Donation mixin no
  longer forces the sample company and now uses base accounting rollback.
- Disabled-mode marked inventory preserved for manual review: Donation Receipt
  5; Payment Entry 96; Sales Invoice 3; Donation 100; Sponsor 3; Donor 68;
  Major Gift 7; Donor Interaction 12; Membership 6; Subscription 3; Member 10;
  Donation Campaign 2; Volunteer 3; Customer 313 (631 records total).
- Compatibility risk: existing demo sites must explicitly enable both flags;
  disabled mode intentionally leaves prior marked records untouched. Run the
  read-only marked-record report before deliberately enabling reset.

### Wave 5

- Started 2026-07-14.
- Planned findings: H3, H4, H5, M1, plus authorization-sensitive parts of B02
  and B07 where needed to prevent drift.
- Completed in `good_connector` commit `88a8740` and `mopi_app` commit
  `77aed76`.
- `bench migrate` passed. Good Connector: 1 unit, 112 integration, 3
  unspecified, and 33 legacy tests passed (149 total). MoPi: 101 integration
  tests passed with one expected skip, plus 7 unit/unspecified and 1 legacy
  naming test (109 total).
- Shared `StartProcess` now fails closed, including `Aufgabe`, unless the exact
  process name is present in server-owned settings or site config. Existing
  endpoint names, success payloads, and authorization error shapes are
  unchanged.
- Closed/cancelled MoPi ToDos remain process-list history only. File listing,
  reading, download, deletion, upload, and attachment recompute current access
  through the shared Task authorization path and enforce app context. Terminal
  Task files remain read-only.
- Taskless portal uploads are staged against the enabled User resolved from the
  JWT subject. Only that same portal identity can attach them; legacy unattached
  File rows are not claimable.
- Self-study certificate creation/generation now requires an exact canonical
  module parent, self-study module, participant row, participant Task link,
  matching `gc_target_user`, and terminal Task status. Payload
  `training_module`, owner, and `_assign` alone are not eligibility evidence.
- ERPNext closes live assignment rows before app `on_update` hooks run, so
  terminal eligibility intentionally relies on the immutable participant Task
  link plus matching target user rather than a live ToDo after completion.
- Ordinary `MoPi User` accounts retain Training Module editing and self-study
  Task creation, but cannot create/write/generate/send certificates and can
  read only certificates whose `user` matches their account. `MoPi Manager`,
  `System Manager`, and `Administrator` remain issuers; their non-self-study
  module workflow is the explicit manual issuance path.
- Removed MoPi's duplicate related-Task synchronization call; Good Connector's
  Task hook is now the single owner and regression coverage verifies one call
  per update.
- Compatibility risk: sites that intentionally use shared generic
  `StartProcess` must configure the exact process allowlist. Existing incomplete
  self-study Draft certificates remain stored but cannot be generated or sent
  without canonical completed Task eligibility. Migration repairs stale
  `MoPi User` certificate Custom DocPerm rows.

### Wave 6

- Started and completed 2026-07-14 in `good_event` commit `f8f6d3d`.
- Full app suite passed: 11 unit, 36 integration, and 470 legacy tests (517
  total).
- Composer previews, composer sends, installed Email Template dispatch, and
  manual subject/body rendering now share one immutable restricted Jinja
  environment. It has no Frappe/Jinja globals, denies callable and arbitrary
  attribute access, and recursively accepts only scalar/date-time values plus
  frozen safe mappings/sequences. Built-in schedule-row loops remain supported.
- Trusted Print Format/PDF rendering is unchanged and remains outside this
  staff-authored email boundary.
- Good Event and Good Event Master now validate every persisted custom email
  attachment as a real File readable by the configuring user. Manual sends
  repeat the current-user permission check; automatic guest/scheduler sends use
  the save-time approval but still fail if the File was deleted.
- Removed privileged document objects from invoice/dunning email contexts and
  removed the obsolete SSTI overrides for composer/correspondence rendering.
- Compatibility risk: customized Email Templates using `frappe`, document
  attributes, method calls, private attributes, or filters other than
  `default` now fail by design. Existing missing attachment URLs block the next
  Event/Master save and send until an operator removes or replaces them.

### Wave 7

- Started and completed 2026-07-14. Planned findings: H7, H8, H9, and M4.
- Completed in `good_analytics` commit `ddabe08`, `miki_app` commit `a1a7260`,
  and `good_help` commit `b8acd26`.
- `bench migrate` passed. Good Analytics: 7 unit and 36 integration tests
  passed (43 total). MiKi: 4 unit, 33 integration, 269 unspecified, and 12
  legacy tests passed (318 total). Good Help: 61 legacy tests passed.
- Good Analytics now applies one shared authorization boundary to dashboard,
  settings, segment materialization, mailing export, and newsletter-provider
  entry points. Only `Administrator`, `System Manager`, and
  `Non Profit Manager` may run system-wide aggregates, Donation read remains
  mandatory, and demo-contained users are denied even if assigned a trusted
  role.
- MiKi case acceptance is POST-only and requires `MiKi Billing Manager` or
  `System Manager` plus document-level Issue write permission. Billability,
  Item, quantity, rate, tax template, company, currency, and Customer language
  are rebuilt from server-owned configuration; Issue payload values cannot
  change the submitted Sales Invoice.
- MiKi readiness, reporting, and dashboard queries now honor DocType and User
  Permissions and no longer create Website User or Customer portal-user rows.
  Identity repair is an explicit Customer write action for authorized reviewers
  and remains part of the already-authorized campaign-start mutation.
- Good Help applies its existing private-role tier to mapped direct Wiki routes,
  Wiki client-navigation page-data requests, Wiki Document reads, and attached
  File reads. Public mapped pages and all unmapped Wiki content retain Wiki's
  standard behavior.
- Compatibility risks: Donation readers without a trusted analytics role and
  all demo users now lose system-wide analytics access; `Support Team` alone can
  no longer accept/factor MiKi cases; readiness reads no longer repair missing
  portal identities implicitly; mapped private help links now return a
  permission error unless the user has a Wiki read role.

### Wave 8

- Started and completed 2026-07-14 for finding M2 in `barakah_app` commit
  `619ef04`.
- Focused normal-completion and forced-parent-failure tests passed. The full app
  suite passed 111 integration tests.
- Portal Task updates now run behind a savepoint. For completion requests with a
  configured `gc_next_workflow_action`, Barakah verifies that the shared Task
  hook consumed the action after advancing the parent and creating any follow-up
  Task.
- If parent validation, workflow advancement, related-row synchronization, or
  follow-up creation fails, Barakah rolls back the Task status/comment,
  assignment closure, parent state, related Task row, and partial follow-up
  records. The same open Task remains available for retry.
- Normal success still returns `Aufgabe Stored Successfully`. A rolled-back
  completion returns a logged HTTP 409 with `Task completion could not advance
  the parent workflow`, so the portal cannot report false success.
- Compatibility risk: parent documents with pre-existing invalid data now leave
  the supplier Task open and visibly fail instead of recording a completed Task
  against an unadvanced order. Operators must correct the parent/workflow error
  and retry the same Task.

### Wave 9

- Started and completed 2026-07-15. Planned findings: L1 and B01-B05, B09-B15,
  B23-B25, B29-B32, B35, and B38. B07 was already completed in Wave 5.
- Good Connector `396282a`: replaced quadratic identity candidate construction
  with a batched index, centralized bounded Task visibility, added explicit
  portal collection paging/caps and bulk author/File reads, and removed duplicate
  app/shared limiter-dispatch passes while preserving endpoint contracts.
- Good Help `8da50dc` and consumer commits `mopi_app` `6c2000a`, `barakah_app`
  `ec9dc2c`, `good_npo` `0885138`, `good_demo` `7fc6705`, `miki_app` `6c27ddb`,
  `good_event` `c3321ef`, `good_newsletter` `eb90505`, and `good_analytics`
  `ea9e62e`: global reconciliation remains owned by Good Help; consumer setup
  uses app-scoped synchronization without repeating global source discovery.
- MoPi `6c2000a`: introduced a module-scoped certificate reconciliation read
  model and shared proxy dispatch. Query-count coverage fixes a 12-participant
  module at three reconciliation reads while preserving selection and
  idempotency rules.
- Barakah `ec9dc2c`: routed normal and legacy portal actions through one
  dispatcher, reused shared task visibility, and bounded process-list pages at
  100. The 114-test app inventory passed through the full timed run and clean
  sequential reruns.
- Non Profit `04755e3`: batched Donation Receipt context loading and grouped
  major-gift reconciliation. Coverage bounds receipt loading at two SQL calls
  and full reconciliation at six while preserving unchanged timestamps.
- Good NPO `0885138`: replaced Python-side annual Donation loading with one
  permission-aware grouped monthly aggregate and preserved the 12-month payload.
- MiKi `6c27ddb`: shared one campaign-readiness graph through population/start,
  batched declaration status refreshes, and made the page-show lifecycle the
  single dashboard loader with stale-response protection. Full app suite: 321
  tests passed; Ruff passed.
- Workflow Visualizer `1d1cf1d`: made form refresh the client lifecycle owner,
  added in-flight/stale-response guards and compact API mode, and removed the
  duplicate setup owner while retaining the documented default API response.
- Good Event `c3321ef`: added stable bounded catalogue pages, capped facets,
  Guest/fragment caching and rate limiting, bulk translation loading, one
  correspondence-dispatch identity service with atomic unique reservations,
  one set-based trainer recipient resolver, app-scoped help sync, and one-time
  historical repair patches. The full 542-test app suite passed before final
  review hardening; afterward migrate passed and focused Wave 9 (17), scheduler
  (7), invoice (4), package-gate (6), and core Good Event (128) suites passed.
  Ruff lint and changed-file format checks passed. `pre-commit` was unavailable
  in the bench environment.
- Good Newsletter `eb90505`: provider results are materialized once, subscriber
  state is preloaded, and queue cancellation/tracking refresh use set-based
  updates. Query coverage fixes a 10-subscriber import at six reads and tracking
  synchronization at two.
- Good Analytics `ea9e62e`: campaign target member/title resolution uses two
  set-based reads while preserving target order, unions, and exclusions.
- Compatibility risks: public endpoint names, response envelopes, queue/job
  dotted paths, permission filtering, and completed-history behavior remain
  unchanged. Query bounds can expose callers that previously depended on
  unbounded implicit collection results; explicit paging is now required.
- Deferred to Wave 10: B06 and B08 structural/helper extraction; B16-B18 Good
  Event ownership cleanup; B19-B22 and B26-B28 fundraising/payment boundaries;
  B33-B34 and B36-B37 MiKi cleanup; B39-B40 telemetry-gated removals; and the
  structural cohesion register. No telemetry-sensitive API or shim was removed.

### Wave 10

- Started 2026-07-15 with the low-risk shared setup boundaries B08 and B17.
- MoPi `d6b53e3`: retained public `ensure_roles()` /
  `ensure_app_permissions()` orchestration while replacing copied role repair,
  assigned-user `System User` conversion, DocPerm reconciliation/removal, and
  uninstall sidebar protection with `good_connector.install_utils`. Full app
  run completed without failures; Ruff passed. Net change: 66 lines removed.
- Barakah `76daf12`: adopted the same shared role/User/uninstall helpers and
  removed its now-redundant DocPerm forwarding wrappers. The 37-test setup suite
  passed, including fresh Task permissions, read-only Viewer rights, SSO User
  repair, idempotency, Web Forms, and workflows. Ruff passed. Net change: 31
  lines removed.
- Good Event `083e9ae`: preserved the established private permission-helper
  dotted names as aliases to the shared implementations, removing local
  DocPerm mutation code without changing callers. The 129-test core suite and
  Ruff passed. Net change: 28 lines removed.
- Good Event `fae75e6`: verification exposed that a hyphenated dispatch document
  name produced an invalid SQL savepoint identifier when attaching optional
  Email Queue metadata. Savepoints now use a hashed SQL-safe identifier; the
  18-test Wave 9 service suite covers the regression.
- Good Event `0002cde` (B16): reduced Email Template setup to missing-row
  insertion plus one managed-hash reconciliation pass. Removed two literal
  no-ops and six dominated historical marker sweeps. Characterization now pins
  unstamped legacy adoption, stamped untouched reconciliation, and preservation
  of hash-mismatched administrator edits. Email customization (33) and
  correspondence (29) suites passed. Net change: 110 lines removed.
- Good Event `69c1dbc` (B18): consolidated Confirmation, Dunning, and Sales
  Invoice formats behind one parameterized code-owned upsert helper and made
  `Good Event Anmeldebestaetigung` fixture-only (`standard = Yes`). Setup no
  longer reads/recreates the ticket fixture as a custom format. Correspondence
  (29) and core Good Event (129) suites passed. Net change: 105 lines removed.
- Non Profit `c11c65c` (B19/B22/B28): made the base Donation state machine and
  donor identity service authoritative, moved legacy payment behavior behind
  logged compatibility wrappers, and retained historical dotted paths. Donor
  (15), Donation (18), and Membership (11, one skipped) suites passed.
- Payrexx `455ca43` and Good NPO `a70e732` (B19-B22/B27/B39): centralized
  gateway selection in Payrexx, delegated shared identity/payment ownership,
  narrowed the fundraising barrel, and made the deprecated dashboard key
  opt-out with usage logging. Payrexx (44), Good NPO core (62, one skipped),
  and module (12) suites passed.
- Good Demo `de0c4f9` (B20/B22/B26): introduced monotonically versioned,
  idempotent seed operations while preserving the dual-mode gate and
  marker-only deletion contract. The 81-test full run passed 79 tests and hit
  two shared-site MariaDB error-1020 conflicts; both affected tests passed on
  immediate isolated reruns.
- MiKi `5f562e7` (B33/B34/B36/B37): removed runtime template/setup scans,
  consolidated modern and hosted-legacy adapters over one dispatcher, stopped
  recurring workspace rewrites, and derived workflow masters from one
  definition. Wave 10 cleanup (10), main (185), and writeback (13) suites
  passed.
- Barakah `4972c8f` (B06/S08): split public orders, task targeting, order
  workflow, portal tasks, and backfills behind the complete historical
  `services.py` facade. Facade (3), setup (37), dashboard (1), workflow (6),
  task sync (3), portal (30 across the bounded run and isolated reruns), orders
  (14, with one shared-site error-1020 isolated rerun), legacy migration (5),
  and API contract (2) tests passed.
- B40 final disposition: repository-wide Python searches found no callers for
  MiKi `previous_year_window`, `list_declaration_candidate_customers`,
  `billing_contact_email`, or `sync_invoice_dispatch_email_signoffs`, and no
  callers for Good Connector `upsert_desktop_icon`. Repository-local absence is
  not production usage evidence, so all five compatibility surfaces remain
  until production import telemetry supports deletion. Good Event's two
  literal no-op migrations were removed safely as part of B16. B28 legacy
  payment wrappers and B39 `thank_you_print_format` now log use and remain
  available through their deprecation window.
- Wave 10 completed 2026-07-15. All structural fixes in scope are committed;
  telemetry-sensitive removals are explicit compatibility holds rather than
  unverified deletions.
