# Custom Frappe Apps Audit - 2026-07-14

Read-only security, correctness, accounting, permission, efficiency,
redundancy, and code-bloat audit of the custom Frappe v16 applications in this
bench. This report consolidates the findings produced by the parallel audit and
validation agents used on 2026-07-14.

No application source files were changed by this audit.

## Scope

Included applications:

- `good_connector`
- `good_help`
- `mopi_app`
- `barakah_app`
- `non_profit`
- `good_npo`
- `good_demo`
- `miki_app`
- `workflow_visualizer`
- `good_event`
- `payrexx_integration`
- `good_newsletter`
- `good_analytics`

Excluded by instruction:

- `ilanga_app`
- Upstream/off-limits applications: `frappe`, `erpnext`, `payments`,
  `builder`, `buzz`, and `Commit`

Paths in this report are relative to `/workspace/development/frappe-bench`
unless stated otherwise.

## Method

The audit used separate agents for these areas:

1. Accounting and payment validation in `payrexx_integration` and
   `non_profit`.
2. Portal authorization validation in `good_connector`, `mopi_app`, and
   `barakah_app`.
3. Template rendering, SNS, file, and public-surface validation in
   `good_event`, `good_newsletter`, and `good_help`.
4. Analytics, demo isolation, MiKi permissions, and Workflow Visualizer
   validation.
5. Portal-app efficiency and bloat.
6. Event, Newsletter, Analytics, and Help efficiency and bloat.
7. Fundraising, demo, payment, and non-profit efficiency and bloat.
8. MiKi and Workflow Visualizer efficiency and bloat.

High-severity claims were traced through callers, permissions, hooks, and tests
rather than classified from pattern searches alone. Whitelisted APIs were
treated as compatibility-sensitive when repository-local callers were absent.

Agent validation records retained by the current conversation:

| Area | Task ID |
|---|---|
| Accounting and payments | `ses_09ef2cc52ffeAXO5o3MgJ1ZapH` |
| Portal authorization | `ses_09ef2cb7dffewPqxCCBybFvUpq` |
| Rendering, SNS, and files | `ses_09ef2cb62ffe1sMYYTR2SEeim3` |
| Analytics, demo, MiKi, workflow | `ses_09ef2ca9bffePjK2rvgfdSRNY4` |
| Portal-app bloat | `ses_09ec5013effeTI4Wocnm5ziFpA` |
| Campaign-app bloat | `ses_09ec500e6ffeDD7TbLjMAYPfTQ` |
| Fundraising-app bloat | `ses_09ec500ccffe5UNtMt8VCkglOn` |
| MiKi and workflow bloat | `ses_09ec500abffe9qVo9v6hLld3UB` |

## Executive Summary

The audit confirmed three release-blocking Critical issues:

1. Manager-authored Good Event and Good Newsletter content executes in
   Frappe's privileged Jinja environment.
2. Sites with `good_demo` installed can route public fundraising through a
   dummy provider and create apparently paid records without real settlement.
3. Payrexx invoice callbacks mark Integration Requests successful but do not
   settle the Payment Request or Sales Invoice.

The next most material risks are Donation over-allocation, forged MoPi
certificates, demo cleanup of real Good NPO records, unrestricted Good
Analytics aggregates, MiKi billing permission escalation, MiKi readiness data
and identity side effects, private-file exposure, and several Payrexx
settlement lifecycle defects.

The largest measured efficiency and bloat problems are:

- O(N^2) Good Connector duplicate scanning with query fan-out.
- Several drifting implementations of portal Task visibility.
- MiKi campaign readiness and status-refresh N+1 behavior.
- Repeated MoPi participant, Task, and certificate reconciliation.
- Newsletter provider double execution and subscriber N+1 writes.
- Non Profit Donation Receipt and major-gift batch N+1 behavior.
- Repeated global Good Help synchronization during migrations.
- Duplicate Good Event dispatch idempotency and trainer resolution.
- Workflow Visualizer duplicate requests, renders, and unused response work.
- Demo and customer-specific behavior embedded in generic `good_npo`.

## Severity Definitions

| Severity | Meaning |
|---|---|
| Critical | Direct privilege escalation, fake settlement, or material accounting failure requiring immediate remediation |
| High | Significant authorization, financial-integrity, data-exposure, or production-data-loss risk |
| Medium | Constrained exploit, latent authorization issue, partial transaction, or operational reliability problem |
| Low | Growth-related denial-of-service risk or bounded maintainability concern |
| P1 bloat | Measured hot-path cost, authorization drift, or major maintenance risk |
| P2 bloat | Significant recurring duplication, N+1 behavior, or setup/migration cost |
| P3 bloat | Compatibility isolation, cleanup candidate, or cohesion improvement |

---

## Critical Findings

### C1. Privileged Jinja execution in Good Event and Good Newsletter

Good Event accepts manager-authored subject and body templates and evaluates
them with `frappe.render_template()`:

- `apps/good_event/good_event/services/email_composer.py:84-106`
- `apps/good_event/good_event/services/email_composer.py:109-124`
- `apps/good_event/good_event/services/email_composer.py:269-275`
- `apps/good_event/good_event/services/email_composer.py:395-399`

Good Newsletter uses the same environment for previews and dispatch:

- `apps/good_newsletter/good_newsletter/api/editor.py:71-92`
- `apps/good_newsletter/good_newsletter/services/dispatch.py:194-200`

Frappe injects its safe-exec globals into Jinja at:

- `apps/frappe/frappe/utils/jinja.py:7-28`
- `apps/frappe/frappe/utils/safe_exec.py:199-267`

Those globals expose data reads, document access, database mutation, email,
transactions, and outbound HTTP methods. Runtime validation confirmed that the
template environment could read the system User count and access
`frappe.db.set_value` and `frappe.make_get_request`.

#### Preconditions

- Good Event: write permission on the event/custom correspondence content.
- Good Newsletter: Newsletter Manager access to preview or dispatch a design.

The development snapshot did not have enabled manager-only users, but the
product explicitly provisions these manager roles. The vulnerability exists in
the shipped authorization model even if the current development users are all
more privileged.

#### Impact

- Read records outside the manager's normal permissions.
- Modify database rows and potentially role assignments.
- Exfiltrate data through outbound HTTP.
- Trigger privileged side effects during preview or dispatch.

#### Remediation

Use one restricted renderer with no `frappe` global and only documented scalar
merge fields. Prefer explicit token replacement. Preview and dispatch must use
the same renderer. A string blacklist is not a sufficient boundary.

### C2. Dummy checkout can authorize production-facing fundraising records

The public Donation endpoint accepts caller-controlled provider and gateway
selection:

- `apps/good_npo/good_npo/fundraising/donations.py:41-58`
- `apps/good_npo/good_npo/fundraising/donations.py:110-118`

`good_demo` globally registers its dummy provider:

- `apps/good_demo/good_demo/hooks.py:79-90`

The provider returns a signed dummy URL, and its guest confirmation endpoint
runs payment authorization under the automation user:

- `apps/good_demo/good_demo/checkout.py:60-86`
- `apps/good_demo/good_demo/checkout.py:165-185`

The Good NPO Donation override sets `paid=1`, attempts Payment Entry creation,
and suppresses the accounting failure rather than reverting paid state:

- `apps/good_npo/good_npo/overrides.py:18-38`

The membership path is also affected. Good NPO marks generic public
memberships as demo, generates invoices, and the registered provider returns a
dummy checkout for marked invoices:

- `apps/good_npo/good_npo/fundraising/__init__.py:236-270`
- `apps/good_demo/good_demo/checkout.py:89-117`

Configuration selection compounds the risk:

- Good NPO provisions a sample company/campaign at
  `apps/good_npo/good_npo/setup.py:158-169,305-317,1050-1067`.
- `_resolve_company()` prefers `GoodNPO` over the configured Non Profit company
  at `apps/good_npo/good_npo/fundraising/common.py:93-97`.
- A known Payrexx Settings name supplied by the guest can override site
  configuration at `apps/good_npo/good_npo/checkout.py:140-157`.
- Good Demo reseeding rewrites global accounting settings at
  `apps/good_demo/good_demo/seeding.py:469-526`.

#### Preconditions

- `good_demo` is installed on the same site as production or mixed data.
- The caller passes the public endpoint's normal CAPTCHA/authentication gate.

#### Impact

- Donations and membership invoices can appear paid without real settlement.
- Valid accounting defaults can produce submitted Payment Entries and GL
  postings for dummy transactions.
- A real checkout can be routed through an unintended sandbox or merchant
  gateway.

#### Remediation

Remove provider and gateway selection from guest input. Resolve both from
trusted site configuration. Require an explicit demo-site flag and
`developer_mode` for the dummy provider and confirmation endpoint. Move demo
campaign/company/provenance behavior into `good_demo`.

### C3. Payrexx invoice callbacks do not settle Payment Requests or invoices

The invoice link creates and submits a Payment Request and opens Payrexx:

- `apps/payrexx_integration/payrexx_integration/api.py:110-147`
- `apps/payrexx_integration/payrexx_integration/api.py:186-217`

ERPNext identifies the Payment Request as the payment gateway reference:

- `apps/erpnext/erpnext/accounts/doctype/payment_request/payment_request.py:304-334`

The callback completes the Integration Request and calls
`on_payment_authorized` on that Payment Request:

- `apps/payrexx_integration/payrexx_integration/payrexx_integration/doctype/payrexx_settings/payrexx_settings.py:206-263`
- `apps/payrexx_integration/payrexx_integration/payrexx_integration/doctype/payrexx_settings/payrexx_settings.py:385-418`

The v16 Payment Request controller has `set_as_paid()` but no
`on_payment_authorized()` method:

- `apps/erpnext/erpnext/accounts/doctype/payment_request/payment_request.py:336-422`

Frappe's `run_method()` returns without error when a method is absent:

- `apps/frappe/frappe/model/document.py:1169-1187`

The success endpoint sees the completed Integration Request and redirects the
customer to success:

- `apps/payrexx_integration/payrexx_integration/payrexx_integration/doctype/payrexx_settings/payrexx_settings.py:339-343`
- `apps/payrexx_integration/payrexx_integration/api.py:162-170`

#### Impact

- No Payment Entry is created.
- The Payment Request remains `Requested`.
- Sales Invoice outstanding remains unchanged.
- The open Payment Request is reused, allowing repeated checkout creation and
  possible repeated charges while ERPNext still shows the invoice unpaid.

#### Remediation

Add an upgrade-safe, idempotent v16 Payment Request authorization handler that
invokes `set_as_paid()` under an appropriate lock. Add an end-to-end callback
test asserting one submitted Payment Entry, Payment Request `Paid`, and zero
Sales Invoice outstanding. Reconcile historical completed Payrexx Integration
Requests against Payment Entries and provider transactions.

---

## High Findings

### H1. Donation Payment Entries permit cumulative over-allocation

Every validation reports the Donation's full amount as outstanding regardless
of existing submitted Payment Entries:

- `apps/non_profit/non_profit/non_profit/custom_doctype/payment_entry.py:49-96`
- `apps/non_profit/non_profit/non_profit/custom_doctype/payment_entry.py:327-353`

Existing allocations are only summed after submission to set a Boolean paid
state, and totals greater than the Donation amount are accepted:

- `apps/non_profit/non_profit/non_profit/custom_doctype/payment_entry.py:183-222`

The helper has no fully-paid or existing-allocation guard:

- `apps/non_profit/non_profit/non_profit/custom_doctype/payment_entry.py:99-169`

#### Impact

Two operators or callbacks can post multiple full settlements for one Donation.
Fundraising rollups retain one Donation amount while the ledger contains two or
more settlements.

#### Remediation

Calculate outstanding from submitted allocations, excluding the current
Payment Entry as appropriate. Lock or validate atomically during submission and
reject fully paid references.

### H2. Donation Payment Entries do not enforce Donation company/account

Inherited reference validation checks Donation existence, donor, and docstatus,
but not Donation company. ERPNext's expected-party-account validation does not
include Donation:

- `apps/erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.py:648-713`
- `apps/erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.py:680-702`
- `apps/erpnext/erpnext/hooks.py:520`

An accounting user can therefore submit a company-B Payment Entry using valid
company-B accounts against a company-A Donation for the same donor. An
unintended same-company Receivable account is also accepted.

#### Remediation

Require Payment Entry company to equal Donation company and party account to
equal the configured or derived Donation receivable account.

### H3. Portal users can forge MoPi training certificates

The raw Good Connector endpoint forces generic scope and remains callable:

- `apps/good_connector/good_connector/api/endpoints.py:381-393`

Generic `Aufgabe` processes are startable and caller data becomes a parentless,
self-assigned Task:

- `apps/good_connector/good_connector/api/portal.py:302-312`
- `apps/good_connector/good_connector/api/portal.py:948-975`

Parentless Tasks are accepted by generic and MoPi contexts, and StoreData can
merge the caller payload and complete the Task:

- `apps/good_connector/good_connector/api/portal.py:193-232`
- `apps/good_connector/good_connector/api/portal.py:890-942`

MoPi's global Task hook trusts `gc_payload_json.training_module`, derives the
holder from `_assign`, and creates the certificate/PDF:

- `apps/mopi_app/mopi_app/hooks.py:12-16`
- `apps/mopi_app/mopi_app/training.py:959-988`
- `apps/mopi_app/mopi_app/training.py:214-278`

#### Preconditions

- A valid Good Connector JWT for an enabled User.
- Knowledge or guessing of an existing MoPi Training Module name.
- Working PDF rendering.

#### Impact

A portal user can obtain a real downloadable certificate without assignment,
participation, attendance, or eligible completion.

#### Remediation

Disable generic StartProcess unless a server-owned process definition permits
it. Certificate issuance must verify canonical parent/task linkage, module
participation, matching assignee, and eligible completed self-study Task inside
the certificate service itself.

### H4. Ordinary MoPi Users can directly issue certificates

Setup grants `MoPi User` create/read/write permission over all MoPi doctypes,
including certificates:

- `apps/mopi_app/mopi_app/setup.py:16-22`
- `apps/mopi_app/mopi_app/setup.py:241-260`

The certificate controller checks only normal write permission before
generation:

- `apps/mopi_app/mopi_app/mopiapp/doctype/mopi_training_certificate/mopi_training_certificate.py:10-20`

This is High unless every ordinary MoPi operator is intentionally trusted as a
certificate authority.

#### Remediation

Restrict creation/generation to `MoPi Manager` or a dedicated issuer role and
enforce eligibility server-side. Provide an explicit audited manager override
for legitimate manual issuance.

### H5. Revoked MoPi assignees retain file access

Closed and Cancelled ToDos are added to MoPi assignment history without
checking whether the referenced Task is terminal:

- `apps/good_connector/good_connector/api/portal.py:145-155`

Those Task names become file scope:

- `apps/good_connector/good_connector/api/portal.py:400-423`
- `apps/good_connector/good_connector/api/portal.py:464-484`
- `apps/good_connector/good_connector/api/portal.py:989-1083`

The normal Task authorization helper correctly excludes cancelled assignments:

- `apps/good_connector/good_connector/portal_helpers.py:29-63`

#### Impact

A revoked user can list/read private portal files for an open Task and can
delete portal uploads. Current development data had no matching revoked/open
pairs, so this is a latent code-path vulnerability.

#### Remediation

Use completed history only for process-list presentation. Recompute current
assignment/target authorization for every file read and delete.

### H6. Generic Good NPO records become eligible for demo deletion

`good_demo` adds provenance fields to financial and master doctypes:

- `apps/good_demo/good_demo/custom_fields.py:12-30`
- `apps/good_demo/good_demo/custom_fields.py:54-74`

Generic Good NPO code sets the marker whenever the field exists, without a
trusted demo context:

- `apps/good_npo/good_npo/fundraising/common.py:169-182`
- `apps/good_npo/good_npo/fundraising/donations.py:86-104`
- `apps/good_npo/good_npo/fundraising/membership.py:90-102`
- `apps/good_npo/good_npo/fundraising/__init__.py:236-257`
- `apps/good_npo/good_npo/fundraising/erp_linking.py:88-101,203-257,381-408`

The daily reset selects marked records and attempts to cancel and force-delete
them:

- `apps/good_demo/good_demo/hooks.py:59-65`
- `apps/good_demo/good_demo/reset.py:137-146`
- `apps/good_demo/good_demo/reset.py:294-327`

Donation Payment Entries do not inherit the marker, so cleanup can leave fake
accounting rows behind or fail to delete their source Donation.

#### Remediation

Move provenance ownership into `good_demo` and require a trusted site/request
demo context. Propagate the marker consistently to generated accounting records
only after demo provenance is established.

### H7. Good Analytics bypasses demo and row-level Donation boundaries

Every analytics endpoint gates only on coarse Donation read permission:

- `apps/good_analytics/good_analytics/analytics/api.py:36-37`

It then performs explicitly system-wide query-builder aggregation:

- `apps/good_analytics/good_analytics/analytics/api.py:4-10`
- `apps/good_analytics/good_analytics/analytics/api.py:40-55`
- `apps/good_analytics/good_analytics/analytics/api.py:85-458`

Good Demo users receive Donation read permission, while their data boundary is
implemented only through permission-query conditions:

- `apps/good_demo/good_demo/setup.py:50-55,276-280`
- `apps/good_demo/good_demo/api.py:437-458`
- `apps/good_demo/good_demo/privacy.py:52-62`

The manager-only dashboard Page protects navigation, not direct whitelisted
RPC calls.

#### Impact

A restricted user can obtain system-wide donation counts, revenue, cohorts,
RFM distributions, campaigns, cost centers, and projects. The endpoints expose
aggregates/dimensions rather than individual donor rows, but still disclose
organization-wide financial information.

#### Remediation

Require an allowed analytics role and reject demo users, or build an explicitly
permission-scoped Donation universe before aggregation.

### H8. Issue write permission escalates to submitted Sales Invoices

`accept_case()` requires only Issue write permission:

- `apps/miki_app/miki_app/cases.py:196-206`

Standard Support Team users have Issue create/read/write permission. MiKi's
Customer, Item, quantity, rate, and tax fields are editable at permlevel 0:

- `apps/miki_app/miki_app/setup.py:724-764`

Defaults only fill missing values:

- `apps/miki_app/miki_app/cases.py:119-138`

The caller-controlled values are copied to a Sales Invoice and inserted and
submitted with ignored permissions:

- `apps/miki_app/miki_app/cases.py:224-278`

#### Impact

A Support Team-only user can create, submit, link, and email an invoice despite
lacking Sales Invoice create/submit permission.

#### Remediation

Require an explicit billing/accounting role server-side. Protect override fields
with an elevated permlevel or derive values from trusted Issue Type
configuration.

### H9. MiKi readiness bypasses record permissions and mutates identities

The dashboard admits users with read permission on either Declaration or
Campaign:

- `apps/miki_app/miki_app/dashboard.py:18-26`

Readiness then uses unrestricted `frappe.get_all()` across both doctypes and
related records:

- `apps/miki_app/miki_app/campaign_readiness.py:141-209`
- `apps/miki_app/miki_app/campaign_readiness.py:278-300`
- `apps/miki_app/miki_app/campaign_readiness.py:905-951`

The MiKi Billing Manager can read declarations but has no Campaign permission,
yet is admitted by the OR gate. The report also declares
`apply_user_permissions=1` but directly invokes the unrestricted helper.

Readiness calls portal-user repair:

- `apps/miki_app/miki_app/campaign_readiness.py:614`

That helper creates Customer Portal User rows and enabled Website Users with
ignored permissions:

- `apps/miki_app/miki_app/portal_user_sync.py:194-220`
- `apps/miki_app/miki_app/portal_user_sync.py:254-281`

#### Impact

- Records from doctypes or User Permission scopes the caller cannot normally
  read are disclosed.
- A nominally read-only dashboard/report can create enabled identities and
  grant Customer portal access.

#### Remediation

Make readiness pure and permission-aware. Use permission-preserving queries and
per-document checks. Move portal-user repair into an explicit POST action that
requires Customer write permission and an operations role.

### H10. Newsletter designs can make arbitrary known private files public

`publicize_design_images()` resolves referenced `/private/files/...` URLs,
changes `is_private` to zero, and saves with ignored permissions without a File
read check:

- `apps/good_newsletter/good_newsletter/services/blocks.py:155-202`

The scan includes image fields, links, and inline HTML URLs. Newsletter Managers
can trigger it by saving a campaign/template:

- `apps/good_newsletter/good_newsletter/api/editor.py:54-68`

#### Preconditions

The manager knows or obtains a private file URL.

#### Impact

The file moves into `/files/` and becomes anonymously accessible even when the
manager cannot read the attached document.

#### Remediation

Require File read permission, restrict conversion to validated image MIME types,
and preferably allow only files uploaded by the current user for that design.
Do not publicize arbitrary link targets.

### H11. Persisted Good Event attachments bypass File permissions

Manual composer attachments correctly check File read permission:

- `apps/good_event/good_event/services/email_composer.py:709-724`

Persisted Good Event attachment rows have no equivalent validation, and the
resolved URL is forwarded directly:

- `apps/good_event/good_event/services/email_customization.py:138-150`

Frappe Email Queue loads the File content without a user authorization check:

- `apps/frappe/frappe/email/doctype/email_queue/email_queue.py:436-456`

#### Impact

A Good Event Manager who knows a private URL can cause its contents to be
emailed.

#### Remediation

Validate File read permission when configuring the attachment and immediately
before staff-triggered sends. Prefer event-owned approved attachments over
arbitrary retained URLs.

### H12. First Payrexx invoice-link click creates two checkouts

Payment Request submission already calls `set_payment_request_url()` and creates
a Gateway/Integration Request:

- `apps/erpnext/erpnext/accounts/doctype/payment_request/payment_request.py:203-236`
- `apps/erpnext/erpnext/accounts/doctype/payment_request/payment_request.py:300-334`

`pay_invoice` then calls `get_payment_url()` again:

- `apps/payrexx_integration/payrexx_integration/api.py:144-147`
- `apps/payrexx_integration/payrexx_integration/api.py:206-217`

#### Impact

The Payment Request stores checkout A while the browser receives checkout B.
Both are active and can produce duplicate charges.

#### Remediation

Create the checkout once and redirect to the submitted Payment Request's stored
URL. Test for exactly one provider call and Integration Request.

### H13. Payrexx chargebacks do not reverse accounting

A signed chargeback callback changes only the Integration Request status:

- `apps/payrexx_integration/payrexx_integration/payrexx_integration/doctype/payrexx_settings/payrexx_settings.py:258-269`

It does not reverse or flag the original Payment Entry, reopen the source, or
update Donation/invoice state.

#### Remediation

Add an idempotent accounting reversal or mandatory exception workflow linked to
the original settlement.

### H14. Payrexx deadlock retry can split settlement from callback state

Completion first saves transaction data/status. On deadlock, rollback removes
those writes, but the retry invokes only the downstream authorization hook:

- `apps/payrexx_integration/payrexx_integration/payrexx_integration/doctype/payrexx_settings/payrexx_settings.py:385-407`

#### Impact

A retry can commit a Payment Entry while the Integration Request remains
Queued/Authorized. A provider retry may process it again, which combines badly
with Donation over-allocation.

#### Remediation

Retry the entire atomic completion unit: reload, save transaction/status, and
run settlement together.

---

## Medium and Low Findings

### M1. Staged portal uploads are bearer-ID claimable

Taskless uploads do not persist portal identity ownership:

- `apps/good_connector/good_connector/api/portal.py:1086-1155`

Attachment later accepts any supplied unattached portal-upload File ID:

- `apps/good_connector/good_connector/api/portal.py:649-681`

Random 10-character File IDs and the lack of a listing endpoint constrain the
risk, but File ID secrecy is not authorization.

#### Remediation

Persist token-subject ownership and require the same identity when attaching.

### M2. Barakah Task completion can commit partial workflow state

Barakah saves the terminal Task before parent workflow advancement:

- `apps/barakah_app/barakah_app/services.py:763-787`
- `apps/barakah_app/barakah_app/portal.py:162-181`

Parent transition errors are broadly caught and suppressed:

- `apps/good_connector/good_connector/workflow_support.py:103-117`

The hook normally attempts advancement only on the nonterminal-to-terminal
edge, so a later save does not naturally retry.

#### Remediation

Use a savepoint around the transition and follow-up creation or enqueue a
durable retry. Do not report portal success while the parent workflow is
inconsistent.

### M3. SNS verification trusts attacker-controlled AWS-hosted certificates

Certificate and subscription URLs accept any HTTPS host ending in
`.amazonaws.com`:

- `apps/good_newsletter/good_newsletter/services/sns.py:50-59`
- `apps/good_newsletter/good_newsletter/services/sns.py:253-276`

The downloaded PEM is used without trust-chain, issuer, validity, or key-usage
validation:

- `apps/good_newsletter/good_newsletter/services/sns.py:218-250`

Requests follow redirects. Public S3/API Gateway endpoints satisfy the hostname
test and can be AWS-customer-controlled.

#### Preconditions

The attacker also knows the webhook secret.

#### Remediation

Restrict to the documented SNS hostname and certificate path pattern, disable
redirects, require Topic ARN pinning, and validate the certificate chain or use
an AWS-supported verifier.

### M4. Good Help private content is reachable through direct Wiki routes

Good Help restricts private content to Wiki/System roles:

- `apps/good_help/good_help/api.py:151-219`

The pinned Wiki renderer denies only Guest and does not enforce Wiki Document
DocPerm for published private pages:

- `apps/wiki/wiki/frappe_wiki/doctype/wiki_document/wiki_document.py:235-245`
- `apps/wiki/wiki/frappe_wiki/doctype/wiki_document/wiki_document.py:316-319`
- `apps/wiki/wiki/frappe_wiki/doctype/wiki_document/wiki_document.py:426-484`

The current development database had no enabled private mappings, so this is
latent until private content is configured.

#### Remediation

Add an upgrade-safe route guard matching Good Help's role policy, or explicitly
redefine private as any authenticated user. Confidential attachments must remain
private and use File authorization.

### L1. Public Good Event catalogues perform unbounded uncached rendering

Event lists fetch all matching events and separately fetch full facet data:

- `apps/good_event/good_event/services/event_lists.py:642-656`
- `apps/good_event/good_event/services/event_lists.py:984-995`

Master lists use unlimited reads and per-master processing:

- `apps/good_event/good_event/services/event_master_catalog.py:390-412`

Website controllers disable caching and the guest embed API exposes equivalent
rendering:

- `apps/good_event/good_event/embed_api.py:52-77`

Current scale is modest. Cost grows linearly and is unauthenticated.

#### Remediation

Add pagination, bounded facets, short-lived caching, bulk translation loading,
and a rate limit for fragment endpoints.

---

## Detailed Bloat and Efficiency Findings

### Portal applications

#### P1. Good Connector identity scanning is quadratic

The daily hook invokes a full duplicate scan:

- `apps/good_connector/good_connector/hooks.py:61-65`

The scan iterates every supported record and compares it with every other
Contact, Address, or organization:

- `apps/good_connector/good_connector/identity_matching.py:332-430`

Candidate identity construction performs child-table and Dynamic Link queries
per candidate:

- `apps/good_connector/good_connector/identity_matching.py:573-663`

This is O(N^2) comparison work with O(N^2) query fan-out.

**Consolidation boundary:** load base records, emails, phones, addresses, and
Dynamic Links once into an identity index. Preserve existing scoring and
suppression persistence. Differential-test old and new candidate sets before
removing the scanner.

#### P1. Task visibility has several drifting implementations

Canonical shared visibility exists at:

- `apps/good_connector/good_connector/portal_helpers.py:166-219`

Independent implementations remain at:

- `apps/good_connector/good_connector/api/portal.py:82-169`
- `apps/barakah_app/barakah_app/portal.py:49-70`
- `apps/barakah_app/barakah_app/services.py:686-720`
- `apps/barakah_app/barakah_app/services.py:799-808`
- `apps/barakah_app/barakah_app/permission.py:76-86`

Barakah loads open Tasks globally, then performs per-Task authorization checks.
The list path can recheck up to 500 Tasks, with repeated User, ToDo, and Portal
User queries.

**Consolidation boundary:** one `visible_task_rows_for_email()` helper accepting
base filters, fields, app context, and explicit completed-history behavior.
Retain per-document checks for direct mutation APIs.

#### P1. MoPi certificate reconciliation repeats complete data passes

Examples:

- One User existence query per participant at
  `apps/mopi_app/mopi_app/training.py:97-107`.
- Per-user Task, certificate, participant, status, and sent-certificate lookups
  at `apps/mopi_app/mopi_app/training.py:149-334`.
- Repeated certificate/tracking work at
  `apps/mopi_app/mopi_app/training.py:427-440`.
- Per-participant latest Task/status reads at
  `apps/mopi_app/mopi_app/training.py:529-587`.
- Deduplication invoked repeatedly during sending at
  `apps/mopi_app/mopi_app/training.py:901-946`.

**Consolidation boundary:** build one module-scoped read model containing valid
Users, participant rows, latest Tasks/statuses, and grouped certificates. Split
the module into orchestration, reconciliation, PDF generation, and delivery,
while retaining `mopi_app.training` as a compatibility facade.

#### P2. Portal collection reads are unbounded or post-process too much data

- Good Link and Good News reads are unbounded at
  `apps/good_connector/good_connector/api/user.py:134-159`.
- News performs one User lookup per row at
  `apps/good_connector/good_connector/api/portal.py:802-818`.
- File collection loads all accessible File rows, resolves target fields, sorts
  everything in Python, then retains 100 at
  `apps/good_connector/good_connector/api/portal.py:520-619,821-837`.
- DeleteFiles accepts an unbounded ID list and performs per-ID lookups at
  `apps/good_connector/good_connector/api/portal.py:1057-1083`.

**Consolidation boundary:** explicit pagination/caps, database ordering, bulk
author/File lookups, and a separate exact-ID path for download/delete.

#### P2. App proxy layers duplicate dispatch and rate limiting

MoPi and Barakah apply the app-action limiter before delegating to a shared
handler that applies it again:

- `apps/mopi_app/mopi_app/api.py:35-50`
- `apps/barakah_app/barakah_app/api.py:88-110`
- `apps/good_connector/good_connector/api/endpoints.py:399-415`

Barakah's token/action/log dispatcher duplicates Good Connector's structure:

- `apps/barakah_app/barakah_app/portal.py:81-205`
- `apps/good_connector/good_connector/api/portal.py:702-757,840-945`

**Consolidation boundary:** preserve every branded/legacy whitelisted URL but
route them through one shared dispatcher with registered app-specific handlers
and serializers.

#### P2. Barakah services.py mixes unrelated domains

`apps/barakah_app/barakah_app/services.py` contains:

- Public form, CAPTCHA, and shield logic at `:55-205`.
- Task retargeting at `:208-291`.
- Counters, order submission, and resend at `:294-653`.
- Portal serialization and mutation at `:656-808`.
- Repair/backfill routines at `:790-858`.

**Consolidation boundary:** extract `public_orders`, `shield`, `task_targets`,
`order_workflow`, `portal_tasks`, and `backfill`. Keep a re-exporting facade
until imports and test patch paths migrate.

#### P3. Related Task synchronization runs twice

Good Connector's Task hook already calls the shared synchronization:

- `apps/good_connector/good_connector/hooks.py:41-43`
- `apps/good_connector/good_connector/workflow_support.py:176-183`

MoPi's Task hook calls it again:

- `apps/mopi_app/mopi_app/hooks.py:12-16`
- `apps/mopi_app/mopi_app/training.py:992-994`

**Consolidation boundary:** keep the MoPi certificate hook and remove its second
related-row synchronization.

#### P3. Setup helpers remain duplicated

Canonical role, System User repair, permission, and uninstall helpers exist in:

- `apps/good_connector/good_connector/install_utils.py:17-139`

Local copies remain in:

- `apps/mopi_app/mopi_app/setup.py:60-73,195-238,285-329`
- `apps/barakah_app/barakah_app/setup.py:446-459,543-586,639-652`

Keep public orchestration functions but route them through the shared helpers.

### Event, Newsletter, Analytics, and Help

#### P1. Global Good Help reconciliation runs repeatedly per migration

Good Help performs a global scan itself:

- `apps/good_help/good_help/setup.py:10-22`
- `apps/good_help/good_help/sync.py:28-39,73-88`

Consumers invoke it again:

- `apps/good_event/good_event/setup.py:72-75`
- `apps/good_newsletter/good_newsletter/setup.py:38-52,77-84`
- `apps/good_analytics/good_analytics/setup.py:64-71`

Source discovery is repeated again for sidebars:

- `apps/good_help/good_help/sync.py:312-323`

**Consolidation boundary:** retain the global scan in `good_help.after_migrate`.
Expose `ensure_app_help(app_name)` for consumer installation and test setup.

#### P1. Good Event correspondence dispatch idempotency has three owners

- Pre-event implementation:
  `apps/good_event/good_event/services/pre_event_packages.py:733-814`.
- Survey/trainer scheduler copies:
  `apps/good_event/good_event/services/scheduler.py:102-134,218-253`.
- Invoice scheduler copy:
  `apps/good_event/good_event/services/invoice_scheduler.py:119-150`.

These paths also perform per-recipient existence queries.

**Consolidation boundary:** a `correspondence_dispatch.py` service with
`existing_keys`, `exists`, and `record`, while keeping flow-specific sending in
the current modules.

#### P1. Newsletter imports execute providers twice and query per subscriber

`import_from_source` materializes provider members, then `run_import` invokes
the provider again:

- `apps/good_newsletter/good_newsletter/api/audience.py:51-84`

The import then performs existence/document operations per member:

- `apps/good_newsletter/good_newsletter/api/audience.py:89-132`

**Consolidation boundary:** pass the first provider result into a shared import
worker, preload subscribers by audience/email, and provide a count contract for
large providers.

#### P1. Good Event trainer recipient resolution is implemented four times

- Composer: `apps/good_event/good_event/services/email_composer.py:568-624,740-778`.
- Pre-event packages: `apps/good_event/good_event/services/pre_event_packages.py:655-730`.
- Short-notice scheduler: `apps/good_event/good_event/services/scheduler.py:160-199`.
- Cancellation hook: `apps/good_event/good_event/good_event/doctype/good_event/good_event.py:220-266`.

The composer also recomputes attendee count twice per trainer.

**Consolidation boundary:** a set-based `trainer_recipients(event)` returning
the trainer row, Contact, email, and language. Keep flow-specific context local.

#### P2. Good Event recurring setup performs historical full-table backfills

Every install/migrate runs translation repair, translation-unit backfill, and
booking-title backfill:

- `apps/good_event/good_event/setup.py:62-70,102-121,384-396`
- `apps/good_event/good_event/services/translation_units.py:162-193`

Runtime controllers/hooks already maintain these values.

**Consolidation boundary:** versioned migration patches for each historical
repair; leave runtime hooks as invariant owners.

#### P2. Newsletter queue lifecycle performs row-wise updates

- Campaign cancellation updates each unsent Email Queue separately at
  `apps/good_newsletter/good_newsletter/services/dispatch.py:275-291`.
- Tracking refresh updates each recipient separately at
  `apps/good_newsletter/good_newsletter/services/tracking.py:249-277`.

**Consolidation boundary:** query-builder updates for common statuses; batch only
rows requiring distinct error text.

#### P2. Good Analytics campaign performance has segment N+1 queries

The endpoint queries members and titles per target row:

- `apps/good_analytics/good_analytics/analytics/api.py:531-566`

It runs on Donation Campaign form refresh.

**Consolidation boundary:** fetch all members and segment titles in two batched
queries and group in Python.

#### P2. Good Event email-template migration ladder is stale

Setup invokes eight historical normalization passes after a general managed
reconciliation already rewrites untouched templates:

- `apps/good_event/good_event/services/email_templates.py:1187-1223`
- `apps/good_event/good_event/services/email_templates.py:1226-1349`

Two invoked functions are literal no-ops:

- `apps/good_event/good_event/services/email_templates.py:1245-1250`

**Consolidation boundary:** retain missing-row insertion plus one managed
reconciliation; remove dominated historical sweeps after characterization tests
for old unstamped, untouched stamped, and admin-edited templates.

#### P3. Good Event permission helpers duplicate shared helpers

- Local copies: `apps/good_event/good_event/setup.py:339-381`.
- Canonical helpers: `apps/good_connector/good_connector/install_utils.py:83-139`.

Import the shared implementations under the existing private names.

#### P3. Good Event Print Formats have duplicate ownership

Three similar code-owned upsert pipelines exist at:

- `apps/good_event/good_event/print_formats.py:28-150`

The ticket format is both a standard fixture and manually upserted with a
different `standard` value:

- `apps/good_event/good_event/print_formats.py:153-195`

**Consolidation boundary:** one parameterized helper for code-owned formats and
fixture-only ownership for the ticket format.

### Fundraising and payment applications

#### P1. Donation payment and thank-you state has multiple owners

Base Donation authorization reverts `paid` and raises on Payment Entry failure,
then refreshes rollups:

- `apps/non_profit/non_profit/non_profit/doctype/donation/donation.py:64-85`

Good NPO replaces the method, retains `paid`, suppresses the accounting error,
and omits rollup refresh:

- `apps/good_npo/good_npo/overrides.py:18-38`

Thank-you audit writes are repeated in:

- `apps/non_profit/non_profit/non_profit/doctype/donation/donation.py:127-138`
- `apps/good_npo/good_npo/thank_you.py:195-207`
- `apps/good_npo/good_npo/dashboard.py:124-141`

**Consolidation boundary:** keep `Donation.on_payment_authorized()` authoritative
and expose narrow hooks for failure policy and thank-you dispatch.

#### P1. Demo and customer-specific concerns are embedded in Good NPO

Examples:

- Default campaign `GOODNPO-DEMO` at
  `apps/good_npo/good_npo/constants.py:3-6` and seed at
  `apps/good_npo/good_npo/setup.py:1050-1067`.
- Generic code writes `good_demo_*` fields at
  `apps/good_npo/good_npo/fundraising/common.py:169-182`.
- QR fallback hard-codes `Miki Settings` at
  `apps/good_npo/good_npo/qr_bill.py:80-95`.
- Desk home contains demo copy and `/demo` at
  `apps/good_npo/good_npo/good_npo/page/good_npo_home/good_npo_home.js:63-75,352-355`.
- Dashboard returns an Ilanga-owned print-format name at
  `apps/good_npo/good_npo/dashboard.py:19,85`.

**Consolidation boundary:** downstream site-profile providers for demo metadata,
CTA/campaign, QR fallback, and optional presentation settings.

#### P1. Payrexx gateway selection has three conflicting policies

- Pay-by-email silently prefers Live, then Sandbox, then the first row at
  `apps/payrexx_integration/payrexx_integration/api.py:176-183`.
- Webhooks require explicit or unique settings at
  `apps/payrexx_integration/payrexx_integration/payrexx_integration/doctype/payrexx_settings/payrexx_settings.py:282-289`.
- Good NPO honors site config and rejects ambiguity at
  `apps/good_npo/good_npo/checkout.py:140-174`.

**Consolidation boundary:** one resolver in `payrexx_integration` accepting an
explicit name and configured default. Retain old helpers as compatibility shims.

#### P1. Donor and Customer identity resolution is implemented three times

- Canonical Member-aware resolution:
  `apps/non_profit/non_profit/non_profit/doctype/donor/donor.py:185-216,265-299,343-406`.
- Good NPO copies:
  `apps/good_npo/good_npo/fundraising/donations.py:183-253` and
  `apps/good_npo/good_npo/fundraising/erp_linking.py:39-101`.
- Good Demo copy:
  `apps/good_demo/good_demo/seeding.py:706-779`.

**Consolidation boundary:** one policy-capable helper in `non_profit`; callers
supply presentation defaults and optional demo-marker callbacks.

#### P1. Donation Receipt generation has several queries per Donation

- Validation queries Donation per row at
  `apps/non_profit/non_profit/non_profit/doctype/donation_receipt/donation_receipt.py:25-98`.
- Yearly generation repeats active-receipt and Donation reads at
  `apps/non_profit/non_profit/non_profit/doctype/donation_receipt/donation_receipt.py:131-179,224-284`.

**Consolidation boundary:** one bulk loader returning Donation fields and active
receipt mappings for validation and generation.

#### P1. Daily major-gift reconciliation performs several queries per record

Each Donor performs existence, aggregate, last-gift, level/threshold, and update
queries; each Major Gift performs another aggregate/update:

- `apps/non_profit/non_profit/non_profit/major_gifts.py:50-119`
- `apps/non_profit/non_profit/non_profit/major_gifts.py:164-192`

**Consolidation boundary:** optimize the batch job with grouped aggregates and
prefetched levels/thresholds while preserving single-record hook APIs.

#### P2. Good NPO dashboard loads all annual Donations into Python

- `apps/good_npo/good_npo/dashboard.py:171-209`

**Consolidation boundary:** replace `_monthly_donation_totals()` with a
permission-aware grouped query retaining the same 12-month response.

#### P2. Good Demo setup and reset are tightly coupled to full seeding

- Every install/migrate runs dependency setup and the full seed at
  `apps/good_demo/good_demo/setup.py:135-163`.
- Reset imports many private seeding helpers at
  `apps/good_demo/good_demo/reset.py:31-82`.
- `seeding.py` mixes organization/accounting, fundraising, membership/invoices,
  and major gifts across `apps/good_demo/good_demo/seeding.py:295-1654`.
- Ensuring one example receipt can trigger the full seed at
  `apps/good_demo/good_demo/donation_receipts.py:98-107`.

**Consolidation boundary:** public prerequisite, full-seed, and receipt-pool
operations guarded by a seed-version stamp.

#### P2. Good NPO fundraising package is an oversized compatibility barrel

The package re-exports a large private surface because tests patch module
globals, and still owns membership email/PDF orchestration:

- `apps/good_npo/good_npo/fundraising/__init__.py:3-15`
- `apps/good_npo/good_npo/fundraising/__init__.py:63-167`
- `apps/good_npo/good_npo/fundraising/__init__.py:170-408`

**Consolidation boundary:** keep `create_membership`,
`create_donation_checkout`, and queued-job aliases in the facade; move internal
imports/tests to actual owners.

#### P3. Legacy payment APIs remain inside active controllers

Current Membership metadata has no invoice field, but the controller retains
legacy invoice and Payment Entry methods:

- `apps/non_profit/non_profit/non_profit/doctype/membership/membership.py:73-172,236-259`

Donation retains legacy gateway-object helpers:

- `apps/non_profit/non_profit/non_profit/doctype/donation/donation.py:218-316`

These are compatibility-sensitive, not proven dead.

**Consolidation boundary:** move implementations to `legacy_payments.py`, retain
thin wrappers at old dotted paths, log usage, and remove only after a published
compatibility window.

### MiKi and Workflow Visualizer

#### P1. Campaign readiness and campaign start are not batched

Each selected member runs separate membership/declaration/member/customer
queries. Population and start call source resolution explicitly, then `save()`
invokes it again through validation:

- `apps/miki_app/miki_app/miki_app/doctype/miki_declaration_campaign/miki_declaration_campaign.py:20-21,58-80,105-160,201-225,255-263,313`
- `apps/miki_app/miki_app/membership_selection.py:76-93,140-161,212-261`
- `apps/miki_app/miki_app/campaign_readiness.py:57-68,389-525,586-785,954-976`

Readiness checks declarations more than once and deduplicates only after queries
and portal-user repair calls.

**Consolidation boundary:** one `CampaignReadinessContext` with selected members,
memberships, declarations, Customers, Contacts, Users, portal rows, and billing
addresses. Reuse it through start.

#### P1. MiKi Home performs two full dashboard loads on first display

The constructor refreshes, then the page `show` event refreshes again:

- `apps/miki_app/miki_app/miki_app/page/miki_home/miki_home.js:3-15,29-36,164-178`

Each request executes readiness, automation, lists, sums, and counts in:

- `apps/miki_app/miki_app/dashboard.py:19-106`

**Consolidation boundary:** constructor builds/binds only; `on_page_show` owns
automatic refresh. Add request sequencing against stale responses.

#### P1. Campaign updates trigger N+1 declaration-status rebuilds

Every campaign update lists declarations and refreshes each individually. Each
refresh reloads declaration, invoice, campaign, dunning, and sometimes Customer
review state:

- `apps/miki_app/miki_app/hooks.py:51-54`
- `apps/miki_app/miki_app/declaration_status.py:23-28,53-75,100-105,127-155,240-247`
- `apps/miki_app/miki_app/workflow_support.py:78-125`

**Consolidation boundary:** batch status service with prefetched
invoices/dunnings/Customers and targeted updates. Retain the single-document
facade for hooks.

#### P1. Workflow Visualizer issues duplicate API and render work

The globally included script calls the API before checking loaded Workflow
metadata and binds router change, form-refresh, and document-ready render
sources:

- `apps/workflow_visualizer/workflow_visualizer/hooks.py:12-13`
- `apps/workflow_visualizer/workflow_visualizer/public/js/workflow_visualizer.js:5-25,546-563`

Frappe already loads Workflow metadata and emits form refresh.

**Consolidation boundary:** make form-refresh the lifecycle owner, prefilter from
loaded metadata, and add an in-flight/stale-response guard keyed by
doctype/docname.

#### P2. MiKi runtime email sends repeatedly scan setup templates

Invoice and dunning entry points call `ensure_receivable_email_templates()`,
then the shared send helper calls it again:

- `apps/miki_app/miki_app/receivables.py:79-98,156-180,462-486`
- `apps/miki_app/miki_app/correspondence_seeds.py:43-50,91-124`
- `apps/miki_app/miki_app/correspondence_templates.py:318-443`

Each scan checks all language/flow templates individually.

**Consolidation boundary:** setup/versioned migrations own seeding; runtime
resolves only requested language and German fallback. Define whether templates
are source-owned or operator-editable.

#### P2. MiKi recurring setup contains a stale workspace resync

`_reimport_workspace()` checks paths where the shipped fixtures do not exist,
then clears sidebar/site/boot caches on every setup:

- `apps/miki_app/miki_app/setup_desk.py:210-265`

Frappe model sync already imports the app-level fixture.

**Consolidation boundary:** rely on model sync and use an explicit one-time
migration only for forced DB resync.

#### P2. Workflow Visualizer API computes and returns unused data

The endpoint performs existence, visibility, state-style, history, depth, and
graph work:

- `apps/workflow_visualizer/workflow_visualizer/api.py:19-45,63-185,307-382`

The bundled client does not consume depth, position, style, top-level
transitions, or returned history:

- `apps/workflow_visualizer/workflow_visualizer/public/js/workflow_visualizer.js:28-39,98-128`

**Consolidation boundary:** add a typed `compact=False` mode used by the bundled
client while preserving the documented default response. Construct one reusable
graph index.

#### P2. MiKi legacy portal compatibility is spread through canonical paths

Modern and legacy endpoints duplicate rate limiting, parsing, dispatch, logging,
and response handling:

- `apps/miki_app/miki_app/api.py:102-137`
- `apps/miki_app/miki_app/portal.py:87-151`
- `apps/miki_app/miki_app/declaration_service.py:28-108,278-360,507-574`

The canonical serializer always emits modern fields plus legacy aliases.

**Consolidation boundary:** preserve both whitelisted functions as adapters over
one dispatcher. Isolate legacy normalization/serialization around a canonical
internal DTO. Do not remove fields without hosted-hub telemetry.

#### P3. Workflow states and actions have duplicate definitions

- `apps/miki_app/miki_app/setup.py:130-156`
- `apps/miki_app/miki_app/workflow_definition.py:10-177`

Derive seed masters from the workflow definition when next changing that area.

---

## Large-Module Cohesion Findings

Large files are not defects by themselves. These files have identifiable
responsibility boundaries that align with the duplication above:

| App | File | Approximate size | Natural boundaries |
|---|---|---:|---|
| `miki_app` | `correspondence_templates.py` | 1,600 lines | Static templates, ownership, migration |
| `miki_app` | `correspondence.py` | 1,570 lines | Context, rendering, dispatch, attachments |
| `miki_app` | MiKi Declaration controller | 1,570 lines | Snapshot/diff, workflow, master-data writeback |
| `miki_app` | `data_quality.py` | 1,560 lines | Per-report queries and repair actions |
| `miki_app` | `setup.py` | 1,400 lines | Roles, fields, workflows, seeds, migrations |
| `good_event` | `email_composer.py` | 860 lines | Recipients, context, preview, dispatch |
| `good_event` | `pre_event_packages.py` | 840 lines | Eligibility, PDF generation, dispatch tracking |
| `barakah_app` | `services.py` | 850 lines | Public orders, workflows, portal tasks, backfills |
| `workflow_visualizer` | `api.py` | 580 lines | Permission adapter and pure graph calculation |
| `workflow_visualizer` | Desk JavaScript | 560 lines | Fetch lifecycle and rail rendering/actions |

Splits should follow these boundaries rather than arbitrary file-size targets.

## Removal and Deprecation Candidates

The following non-whitelisted helpers had no in-repository callers. External
imports must be checked before removal:

| App | Candidate | Reference |
|---|---|---|
| `miki_app` | `previous_year_window` | `membership_selection.py:40-42` |
| `miki_app` | `list_declaration_candidate_customers` | `membership_selection.py:164-187` |
| `miki_app` | `billing_contact_email` | `contact_roles.py:65-68` |
| `miki_app` | `sync_invoice_dispatch_email_signoffs` | `correspondence_seeds.py:86-88` |
| `good_connector` | Deprecated portal-helper import shim | `portal_helpers.py:416-431` |
| `good_event` | Two no-op template migration functions | `services/email_templates.py:1245-1250` |

No whitelisted endpoint was classified as dead solely because internal callers
were absent. Public payment, portal, and hosted-hub dotted paths need route
telemetry and a compatibility window before deletion.

## Validated Controls and Dismissed Claims

The following concerns were investigated and did not support a broader finding:

- Workflow Visualizer does not bypass workflow permissions. Its API checks
  document read access, and client actions use Frappe's native
  `apply_workflow`, which rechecks role, condition, self-approval, and save/
  submit permissions.
- Donation party mismatch is rejected by inherited Payment Entry validation.
  Wrong doctype, nonexistent Donation, and draft/cancelled Donation references
  are also rejected. The confirmed gaps are cumulative allocation,
  Donation-company equality, and expected receivable account.
- Payrexx direct Donation authorization does call a real
  `on_payment_authorized`; the missing settlement is specifically the v16
  Payment Request/Sales Invoice path.
- Good Event `custom_message` is a context value and is not recursively
  evaluated as a template.
- Core Email Template write permission remains System Manager-only. The Jinja
  issue is manager-controlled event/newsletter content, not ordinary core Email
  Template permissions.
- Good Newsletter deduplicates SNS Notification replay through unique
  `sns_message_id`. The confirmed SNS issue is certificate/URL trust.
- Good Help's own API requires login, applies its private-role gate, and
  sanitizes Markdown. The bypass is the direct Wiki website route.
- Portal target membership uses exact Supplier/Customer equality; no wildcard
  target semantics were confirmed.
- Current development data had no affected revoked/open MoPi assignment/file
  pairs and no staged unattached portal uploads. Those findings are latent code
  paths rather than evidence of current exposure.

## Per-App Assessment

| App | Security/correctness | Primary bloat/efficiency findings |
|---|---|---|
| `good_connector` | Forged-certificate substrate, revoked file history, staged uploads | Quadratic identity scan, visibility duplication, unbounded portal collections, proxy duplication |
| `good_help` | Direct Wiki route bypasses private role tier | Repeated global migration reconciliation |
| `mopi_app` | Certificate forgery and broad issuer permissions | Repeated participant/task/certificate passes, duplicate Task sync, setup-helper copies |
| `barakah_app` | Partial Task/parent-workflow commit | Visibility N+1, duplicate dispatcher, oversized mixed service module |
| `non_profit` | Donation over-allocation and company/account mismatch | Donation Receipt N+1, major-gift batch N+1, legacy payment paths |
| `good_npo` | Dummy provider exposure, demo deletion provenance, divergent Donation authorization | Demo/customer coupling, identity duplication, unbounded dashboard aggregation, compatibility barrel |
| `good_demo` | Dummy settlement can affect mixed/production sites | Full reseed/setup coupling and duplicate identity creation |
| `miki_app` | Issue-to-invoice privilege escalation; readiness permission and identity side effects | Campaign/readiness/status N+1, duplicate dashboard load, runtime template scans, legacy protocol spread |
| `workflow_visualizer` | No permission bypass confirmed | Duplicate lifecycle calls/renders and unused API work |
| `good_event` | Privileged Jinja and private attachment exfiltration | Dispatch/recipient duplication, recurring backfills, template/print-format ownership, unbounded catalogue |
| `payrexx_integration` | Missing invoice settlement, duplicate checkouts, no chargeback reversal, broken deadlock retry | Three gateway-selection policies |
| `good_newsletter` | Privileged Jinja, private-file publicization, SNS certificate trust | Double provider fetch, subscriber N+1, row-wise queue lifecycle updates |
| `good_analytics` | System-wide aggregate disclosure | Campaign-segment N+1 |

## Verification

Completed targeted test results reported by the validation agents:

- Good Connector API contract: 40 passed.
- Good Connector workflow support: 11 passed.
- MoPi API contract: 33 passed, 1 skipped.
- MoPi self-study workflow: 4 passed.
- MoPi permission tests: 2 passed.
- Barakah portal: 11 tests passed before the command timeout.
- SNS signature tests passed.
- Newsletter block rendering/private-file publicization tests passed before
  later classes encountered shared-site locks.
- Good Help completed 18 of 28 tests without assertion failures before timeout.

Several agents ran tests against the same development site concurrently. This
caused MariaDB lock/deadlock timeouts, so incomplete suites are environmental
and are not a pass or fail result for the remaining tests. Future remediation
must run bench suites sequentially.

Earlier in the audit, Ruff checks were reported as passing for all included
repositories. At final verification, `ruff` was no longer available on the
shell PATH. `git diff --check` passed for the dirty `good_connector`,
`miki_app`, and `good_event` repositories.

## Working-Tree Qualification

At final verification, these repositories contained concurrent uncommitted
changes not made by the audit:

- `good_connector`
- `miki_app`
- `good_event`

The audit left them untouched. Critical findings are in unaffected paths, but
Good Event template/Print Format bloat findings overlap current work and should
be revalidated after that work is committed.

## Test Gaps

- No Payrexx callback test asserts Payment Entry submission, Payment Request
  Paid, or zero Sales Invoice outstanding.
- No Payrexx test asserts one checkout/Integration Request per initial click.
- The deadlock test starts from a completed Integration Request and does not
  verify persisted status plus exactly-once settlement.
- No chargeback accounting-reversal test exists.
- Donation tests do not cover second allocation, concurrent drafts, fully-paid
  reference, company mismatch, or account mismatch.
- MoPi wrapper tests block branded StartProcess but do not call the raw Good
  Connector endpoint used by the certificate-forgery path.
- No analytics test runs as a demo/restricted user or under User Permissions.
- MiKi case tests run as Administrator and do not prove a Support Team-only user
  is denied invoice submission.
- MiKi readiness tests run as Administrator and do not cover Billing Manager,
  Campaign denial, User Permissions, or read-path identity creation.
- Newsletter private-file tests confirm publicization but do not test the
  manager's authorization to the source File.
- Good Event lacks a persisted-attachment authorization test.
- Workflow Visualizer lacks a client lifecycle/call-count test and a complete
  browser transition denial test, although the native server permission path is
  preserved.

## Complete Remediation Register

This register is the authoritative backlog for this audit. A finding is not
considered closed until it is implemented and tested, or explicitly recorded as
an accepted risk/intentional behavior. Lower-priority bloat items must not be
silently dropped when the security work is complete.

Disposition meanings:

| Disposition | Meaning |
|---|---|
| Fix | Confirmed and worth implementing |
| Fix before scale | Confirmed growth problem; implement before material production volume |
| Decision required | Technically confirmed, but the intended role/product policy must be recorded |
| Revalidate then fix | Concurrent work overlaps the area; recheck current HEAD before editing |
| Telemetry then remove | Compatibility-sensitive cleanup; instrument/check usage first |
| Intentional/no action | Investigated and should not be changed unless requirements change |

### Security, accounting, and correctness register

| ID | App(s) | Finding | Disposition | Required completion evidence |
|---|---|---|---|---|
| C1 | `good_event`, `good_newsletter` | Privileged manager-authored Jinja | Fix | Restricted renderer tests proving unavailable `frappe`/DB/HTTP globals in preview and dispatch |
| C2 | `good_npo`, `good_demo` | Dummy provider can authorize production-facing records | Fix | Production-mode rejection tests; trusted provider/gateway configuration tests |
| C3 | `payrexx_integration` | Invoice callback does not settle Payment Request/Sales Invoice | Fix | End-to-end callback creates exactly one submitted Payment Entry and clears outstanding |
| H1 | `non_profit` | Donation cumulative over-allocation | Fix | Second/concurrent allocation is rejected using current submitted outstanding |
| H2 | `non_profit` | Donation company and receivable account mismatch | Fix | Cross-company and wrong-account Payment Entries are rejected |
| H3 | `good_connector`, `mopi_app` | Generic portal Task can forge a certificate | Fix | Raw shared endpoint regression test cannot issue without canonical assignment/participation |
| H4 | `mopi_app` | Ordinary MoPi User can directly issue certificates | Decision required | Record issuer policy; restrict role and test denial unless all MoPi Users are intentionally issuers |
| H5 | `good_connector`, `mopi_app` | Revoked assignment history grants current file access | Fix | Open-Task files require current assignment/target; completed history remains list-visible only |
| H6 | `good_npo`, `good_demo` | Real records acquire demo-deletion provenance | Fix | Real Payrexx/public records remain unmarked and survive reset; demo records still reset |
| H7 | `good_analytics`, `good_demo` | Restricted users can query system-wide aggregates | Fix | Demo/restricted user tests enforce role or scoped aggregation |
| H8 | `miki_app` | Issue writer can submit Sales Invoice | Fix | Support Team-only user denied; configured billing role succeeds |
| H9 | `miki_app` | Readiness bypasses permissions and creates identities | Fix | Restricted/User Permission tests plus assertion that read APIs perform no writes |
| H10 | `good_newsletter` | Known private File can be made public | Fix | Unauthorized File is rejected; authorized design-owned image behavior remains covered |
| H11 | `good_event` | Persisted attachment bypasses File permission | Fix | Configuration and send-time read checks reject unauthorized private Files |
| H12 | `payrexx_integration` | First invoice click creates two checkouts | Fix | Exactly one provider request and Integration Request per first click |
| H13 | `payrexx_integration` | Chargeback does not reverse/flag accounting | Fix | Idempotent reversal or exception-workflow test tied to original settlement |
| H14 | `payrexx_integration` | Deadlock retry splits callback state from settlement | Fix | Deadlock retry ends Completed with exactly one settlement |
| M1 | `good_connector` | Staged uploads are bearer-ID claimable | Fix | Upload owner identity persisted and enforced on attachment |
| M2 | `barakah_app`, `good_connector` | Task completion can commit without parent workflow | Fix | Failure rolls back or creates durable retry; portal cannot report false success |
| M3 | `good_newsletter` | SNS trusts customer-controlled AWS certificate URLs | Fix | Canonical host/path, no redirects, Topic ARN, trust-chain tests |
| M4 | `good_help` | Direct Wiki route bypasses private role tier | Fix | Direct-route tests match Good Help role policy and preserve private attachments |
| L1 | `good_event` | Public catalogues are unbounded and uncached | Fix before scale | Pagination/cap/cache/rate-limit tests and bounded query-count test |

### Performance, redundancy, and bloat register

| ID | App(s) | Finding | Disposition | Required completion evidence |
|---|---|---|---|---|
| B01 | `good_connector` | Quadratic identity scan and query fan-out | Fix | Differential candidate tests plus bounded query/performance measurement |
| B02 | `good_connector`, `barakah_app`, `mopi_app` | Drifting Task visibility implementations | Fix | One shared query path; authorization/history regression suites pass |
| B03 | `mopi_app` | Repeated participant/Task/certificate passes | Fix | One module-scoped state load; idempotency and selection-policy tests pass |
| B04 | `good_connector` | Unbounded/post-processed portal collections | Fix | Explicit paging/caps, stable ordering, bulk author/File lookup tests |
| B05 | `good_connector`, `mopi_app`, `barakah_app` | Duplicate proxy dispatch and double rate limiting | Fix | One limiter/log/auth pass while all existing public response contracts remain pinned |
| B06 | `barakah_app` | Multi-domain `services.py` | Fix with related work | Compatibility facade retained; domain services extracted without behavior changes |
| B07 | `good_connector`, `mopi_app` | Related Task synchronization executes twice | Fix | One sync invocation per Task update |
| B08 | `mopi_app`, `barakah_app` | Local setup helpers duplicate `install_utils` | Fix | Shared helper adoption plus install/migrate permission tests |
| B09 | `good_help` and consumers | Global help reconciliation repeats per migration | Fix | One global pass plus app-scoped install helper tests |
| B10 | `good_event` | Correspondence dispatch idempotency has three implementations | Revalidate then fix | Shared identity/recording service and all flow idempotency tests |
| B11 | `good_newsletter` | Audience provider executes twice and subscribers query per row | Fix | Provider called once; batched subscriber lookup; consent/projection tests preserved |
| B12 | `good_event` | Trainer recipient resolution has four implementations | Fix | Shared set-based resolver with preserved fallback/language ordering |
| B13 | `good_event` | Historical backfills run on every migration | Fix | Versioned one-time patches; runtime hooks maintain invariants |
| B14 | `good_newsletter` | Queue cancellation/tracking updates rows individually | Fix | Set-based updates with unchanged status/error outcomes |
| B15 | `good_analytics` | Campaign performance queries per segment | Fix | Batched member/title reads with query-count regression test |
| B16 | `good_event` | Stale email-template migration ladder and no-ops | Revalidate then fix | Old/admin-edited template characterization tests and one reconciliation owner |
| B17 | `good_event` | Permission helpers duplicate `install_utils` | Fix | Shared helper adoption; customized-site behavior verified |
| B18 | `good_event` | Print Formats have duplicate code/fixture ownership | Revalidate then fix | One owner per format and no developer-mode fixture drift |
| B19 | `non_profit`, `good_npo` | Donation payment/thank-you state has multiple owners | Fix | Base state machine authoritative; downstream hook tests cover policy differences |
| B20 | `good_npo`, `good_demo`, `miki_app` | Demo/client-specific behavior embedded in generic Good NPO | Fix | Site-profile/provider boundary; generic app has no demo/MiKi/Ilanga assumptions |
| B21 | `payrexx_integration`, `good_npo` | Three conflicting gateway-selection policies | Fix | One resolver; ambiguity and legacy-link characterization tests |
| B22 | `non_profit`, `good_npo`, `good_demo` | Donor/Customer identity resolution implemented three times | Fix | One policy-capable identity service; ambiguous-email behavior pinned |
| B23 | `non_profit` | Donation Receipt N+1 queries | Fix | Bulk loader and query-count test for annual generation |
| B24 | `non_profit` | Major-gift daily reconciliation N+1 queries | Fix | Grouped batch aggregates; single-record hook APIs unchanged |
| B25 | `good_npo` | Dashboard loads every annual Donation into Python | Fix | Permission-aware grouped query with identical 12-month payload |
| B26 | `good_demo` | Install/migrate/reset tightly coupled to full seed | Fix | Versioned seed operations; reset preserves marked-only contract |
| B27 | `good_npo` | Oversized fundraising compatibility barrel | Fix with related work | Stable public/queued dotted paths remain; internal imports target real owners |
| B28 | `non_profit` | Legacy payment APIs mixed into active controllers | Telemetry then remove | Thin compatibility wrappers, usage logging, documented deprecation window |
| B29 | `miki_app` | Campaign readiness/start repeatedly resolves the same graph | Fix | Shared readiness context and query-count test at realistic campaign size |
| B30 | `miki_app` | MiKi Home loads full dashboard twice initially | Fix | Browser/client test asserts one initial request and protects stale responses |
| B31 | `miki_app` | Campaign update rebuilds declaration statuses N+1 | Fix | Batch service with prefetched invoices/dunnings/customers and behavior tests |
| B32 | `workflow_visualizer` | Global script triggers duplicate API/render cycles | Fix | Client test asserts one fetch/render per relevant refresh and none for non-opted workflows |
| B33 | `miki_app` | Runtime receivable sends repeatedly scan setup templates | Revalidate then fix | Setup owns seeding; runtime resolves requested language/fallback only |
| B34 | `miki_app` | Recurring setup performs ineffective workspace resync/cache clears | Fix | Remove stale path scan; fixture/model-sync and cache behavior verified |
| B35 | `workflow_visualizer` | API computes/returns data unused by bundled client | Fix | Backward-compatible compact mode and response/query-count tests |
| B36 | `miki_app` | Legacy and modern portal envelopes duplicate dispatch logic | Fix with related work | Two thin public adapters over one dispatcher; hosted-hub contracts unchanged |
| B37 | `miki_app` | Workflow state/action definitions duplicated | Fix with related work | Setup masters derive from one workflow definition source |
| B38 | `workflow_visualizer` | Setup patch and install/migrate path can invoke the same custom-field helper twice | Fix | First relevant migration invokes one effective setup path; idempotency retained |
| B39 | `good_npo` | Unused Ilanga-owned `thank_you_print_format` dashboard response key | Telemetry then remove | Confirm no external consumer, deprecate response key, then remove cross-app assumption |
| B40 | Multiple | Zero-caller private helpers, deprecated shim, and literal no-op functions | Telemetry then remove | External-import search/telemetry, deprecation where needed, focused cleanup commit |

### Structural cohesion register

These are worth addressing when the corresponding functional duplication is
changed. They should not trigger arbitrary file splitting by themselves.

| ID | App | Area | Disposition | Preferred boundary |
|---|---|---|---|---|
| S01 | `miki_app` | `correspondence_templates.py` | Fix with B33 | Static assets, ownership, migration |
| S02 | `miki_app` | `correspondence.py` | Fix with correspondence work | Context, rendering, dispatch, attachments |
| S03 | `miki_app` | MiKi Declaration controller | Fix with affected behavior | Snapshot/diff, workflow, master-data writeback |
| S04 | `miki_app` | `data_quality.py` | Fix with affected reports | Per-report query and repair services |
| S05 | `miki_app` | `setup.py` | Fix with B08/B34/B37 | Roles, fields, workflows, seeds, migrations |
| S06 | `good_event` | `email_composer.py` | Fix with C1/B12 | Recipients, context, restricted rendering, dispatch |
| S07 | `good_event` | `pre_event_packages.py` | Fix with B10/B12 | Eligibility, PDF generation, dispatch tracking |
| S08 | `barakah_app` | `services.py` | Fix with B06 | Public orders, workflows, portal tasks, backfills |
| S09 | `workflow_visualizer` | Python API and Desk JS | Fix with B32/B35 | Server adapter/graph logic and client lifecycle/rendering |

### Operational checks and intentional non-actions

| ID | Item | Disposition |
|---|---|---|
| O01 | Development Good Newsletter settings had SNS verification disabled and no Topic ARN after test setup | Verify operationally; production-like sites must restore verification and pin the Topic ARN |
| O02 | One Email Queue row per Newsletter recipient | Intentional/no action; per-recipient headers and merge data require it |
| O03 | Workflow Visualizer uses native `apply_workflow` for mutations | Intentional/no action; preserve this permission boundary |
| O04 | MoPi completed assignment history appears in process lists | Intentional/no action; only current file/mutation authorization must be separated |
| O05 | Good Connector legacy/branded public endpoint names | Intentional compatibility surface until external usage proves removable |
| O06 | Donation party/docstatus/type validation | Intentional/no action; preserve while adding company/account/outstanding checks |

### Removal candidates covered by B40

| App | Candidate | Required check before removal |
|---|---|---|
| `miki_app` | `previous_year_window` | External Python imports |
| `miki_app` | `list_declaration_candidate_customers` | External Python imports and operator scripts |
| `miki_app` | `billing_contact_email` | External Python imports |
| `miki_app` | `sync_invoice_dispatch_email_signoffs` | Re-export and patch/import users |
| `good_connector` | Deprecated portal-helper import shim | External consumer imports |
| `good_event` | Two literal no-op template migration functions | Confirm current concurrent template work does not repurpose them |

## Completion Standard

The remediation program is complete only when:

1. Every `Fix` and `Fix before scale` row is implemented and verified, or an
   explicit accepted-risk decision is recorded in this report.
2. Every `Decision required` row has a documented product/role decision and
   matching tests.
3. Every `Revalidate then fix` row is reassessed against the post-concurrent-work
   commit and either fixed or explicitly closed with evidence.
4. Every `Telemetry then remove` row has usage evidence and a compatibility
   decision; absence of repository-local callers alone is insufficient.
5. App documentation and operator help are updated alongside behavior changes.
6. Security/accounting regression tests and realistic query-count tests are run
   sequentially on the shared Frappe site.
7. Historical Payrexx/Donation/accounting data is reconciled, not only future
   code paths repaired.

## Recommended Remediation Order

### Phase 1: Immediate containment

1. Replace privileged manager-authored Jinja rendering.
2. Disable dummy providers outside explicit isolated demo mode.
3. Remove guest provider/gateway selection.
4. Block generic Task creation from issuing MoPi certificates.
5. Restrict direct certificate issuance roles.

### Phase 2: Accounting integrity

1. Implement idempotent Payrexx Payment Request settlement.
2. Prevent duplicate checkout creation.
3. Validate cumulative Donation outstanding and company/account equality.
4. Implement chargeback reversal/exception handling.
5. Repair the deadlock retry boundary.
6. Reconcile historical provider transactions, Integration Requests, Payment
   Requests, Payment Entries, Donations, and Sales Invoices.

### Phase 3: Authorization and data boundaries

1. Enforce analytics roles or scoped aggregation.
2. Add MiKi billing-role checks and server-owned pricing.
3. Make MiKi readiness permission-aware and side-effect-free.
4. Enforce File authorization for Newsletter and Good Event attachments.
5. Separate MoPi history display from current file access.
6. Add staged-upload ownership.
7. Align direct Wiki routes with Good Help private roles.

### Phase 4: Transactions and reliability

1. Make Barakah Task and parent workflow transition atomic or durably retried.
2. Harden SNS certificate and URL validation.
3. Add catalogue pagination, caching, and limits.

### Phase 5: Measured performance work

1. Batch Good Connector identity matching.
2. Centralize Task visibility.
3. Build MiKi campaign/readiness and declaration-status batch contexts.
4. Batch MoPi certificate reconciliation.
5. Batch Newsletter imports and queue updates.
6. Batch Donation Receipt and major-gift reconciliation.
7. Remove repeated global Good Help synchronization.
8. Eliminate duplicate Workflow Visualizer requests/renders.

### Phase 6: Structural cleanup

1. Move recurring historical backfills into versioned patches.
2. Extract demo/site-profile behavior from Good NPO.
3. Centralize Payrexx settings resolution.
4. Isolate legacy portal/payment compatibility behind thin facades.
5. Split large modules only along the demonstrated responsibility boundaries.
6. Use production route/import telemetry before deleting public APIs or shims.
