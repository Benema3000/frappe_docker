# E2E Test Status

Date: 2026-04-25
Site used for local verification: `development16.localhost`
Hosted hub base URL: `https://selfservice.goodvanta.ge`

## NGO mapping used

- Miki: NGO `11`
- Barakah: NGO `2`
- MoPi: NGO `9`

The Playwright suites now set `Good Connector Settings.org_id` to the
respective app NGO before hosted/browser validation and restore the original
value afterward.

## Local browser E2E status

The maintained Playwright suites pass locally on `development16.localhost`:

- `bench --site development16.localhost execute miki_app.tests.test_e2e_playwright.run`
- `bench --site development16.localhost execute barakah_app.tests.test_e2e_playwright.run`
- `bench --site development16.localhost execute mopi_app.tests.test_e2e_playwright.run`

## Hosted hub visibility summary

Initial hosted `rest/tasklist` visibility is working for all three NGO mappings.

- Miki NGO `11`: declaration appears in the hosted hub tasklist
- Barakah NGO `2`: confirm tasks appear in the hosted hub tasklist
- MoPi NGO `9`: single task, task campaign task, and self-study task appear in the hosted hub tasklist

## Endpoint validation summary

### Barakah

Tested against:

- `https://unimmunized-melodi-subministrant.ngrok-free.dev/api/method/barakah_app.api.goodApi_webhook_BarakahAction_legacy`

Verified flows:

- Aqeeqa confirm
  - `GetProcessList` shows the confirm task with `type = "1"` and `status = "open"`
  - `GetData` returns the expected donor/order details in `gc_description`
  - `StoreData` with `gc_taskcomplete = true` marks the task completed and moves the parent `Barakah Aqeeqa` to `Confirmed`
- Aqeeqa complete
  - a new completion task is created after confirm
  - a fresh hosted tasklist fetch shows the completion task
  - `GetData` returns the completion description
  - `StoreData` with `gc_taskcomplete = true` marks the task completed and moves the parent `Barakah Aqeeqa` to `Done`
- Well confirm
  - `GetProcessList` shows the confirm task with `type = "2"` and `status = "open"`
  - `GetData` returns the expected well/shield details in `gc_description`
  - `StoreData` with `gc_taskcomplete = true` marks the task completed and moves the parent `Barakah Well` to `Confirmed`
- Well complete
  - a new completion task is created after confirm
  - a fresh hosted tasklist fetch shows the completion task
  - `GetData` returns the completion description
  - `StoreData` with `gc_taskcomplete = true` marks the task completed and moves the parent `Barakah Well` to `Done`

Observed Barakah result:

- after both completion tasks are finished, all four Barakah tasks disappear from `GetProcessList` as expected

### MoPi

Tested against:

- `https://unimmunized-melodi-subministrant.ngrok-free.dev/api/method/mopi_app.api.goodApi_webhook_MoPiAction_legacy`

Verified flows:

- Single task
  - appears in hosted hub tasklist
  - `GetProcessList` returns it as `mandatory = "true"` and `status = "open"`
  - `GetData` returns `gc_description`, `gc_comment`, `gc_taskcomplete`
  - `StoreData` updates `description`, `gc_comment`, and closes the task
- Task campaign task
  - appears in hosted hub tasklist
  - `GetProcessList` returns it as `mandatory = "false"` and `status = "open"`
  - `GetData` returns the generated campaign description plus campaign detail lines
  - `StoreData` closes the task and the task later shows as `status = "closed"` in `GetProcessList`
- Self-study task
  - appears in hosted hub tasklist
  - `GetProcessList` returns it as `mandatory = "false"` and `status = "open"`
  - `GetData` returns the generated self-study description, training detail lines, and the `content_link`
  - `StoreData` closes the task
  - Frappe side updates `Training Module Participant.self_study_task_status = "Completed"` and `certificate_eligible = 1`

Observed MoPi result:

- the hosted hub tasklist is now correct after the NGO 9 endpoint was fixed to the exact method path

MoPi contract note:

- `StartProcess` is now intentionally unsupported on the MoPi endpoint
- `GetStartableProcesses` should return an empty list
- supported live MoPi flows remain task retrieval, task update, and related file handling

### Miki

Tested against:

- `https://unimmunized-melodi-subministrant.ngrok-free.dev/api/method/miki_app.api.goodApi_webhook_MikiAction_legacy`

Verified flows:

- Declaration visibility
  - appears in hosted hub tasklist for NGO `11`
  - `GetProcessList` returns the declaration with `processDefinitionName = "deklaration"` and `status = "open"`
- Declaration read
  - `GetData` returns the flat declaration fields at the root
  - `GetData` returns `Accounts` rows with stable `internal_Id` values
- Declaration intermediate save
  - `StoreData` correctly writes declaration fields such as:
    - `organization_comment`
    - `business_name_declared`
    - `billing_use_separate_declared`
    - `billing_name_declared`
  - `StoreData` also updates `Accounts` rows correctly by row `internal_Id`
  - intermediate save does not mutate the linked `Customer` master record
  - read-after-write via `GetData` reflects the updated declaration values

Observed Miki issue:

- declaration final submit is not reliable right now
- repeated live calls hit:
  - `frappe.exceptions.PermissionError`
  - `User Guest does not have doctype access ... Contact`
- the error occurs during `doc.sync_master_data()` when `Customer.on_update` reaches ERPNext contact handling

Practical interpretation for Miki:

- hosted hub routing is correct
- declaration listing and intermediate save are working
- the current blocker is app-side final-submit/master-sync behavior, not hub routing

## What to fix in the hub

For initial task visibility, nothing else needs changing in the hub right now.

Important note for MoPi:

- the working method path is:
  - `mopi_app.api.goodApi_webhook_MoPiAction_legacy`
- the earlier mixed-case variant with `MopiAction` does not work

## What to fix in the apps

### Miki

- make portal final submit run the master-data/contact sync in a permission-safe context
- the current portal request can fail inside ERPNext customer/contact hooks even though the declaration endpoint itself is reached correctly

### MoPi

- no app-side create flow is required right now
- keep MoPi as a task/update-only connector surface until a real start-process use case is needed
