# Hosted Browser E2E Report

Date: 2026-04-25
Site used for backend verification: `development16.localhost`
Hosted hub base URL: `https://selfservice.goodvanta.ge`

## NGO mapping used

- Miki: NGO `11`
- Barakah: NGO `2`
- MoPi: NGO `9`

Hosted/browser test note:

- the Playwright suites now switch `Good Connector Settings.org_id` to the
  respective app NGO before the hosted/browser flow
- they restore the previous connector org id afterward

## Summary

- `mopi_app`: hosted browser flow works end to end
- `miki_app`: hosted browser tasklist and process steps load, but the final hosted submit did not persist the declaration into Frappe
- `barakah_app`: hosted process page loads after the Barakah payload normalization fix, but the hosted tasklist still does not render the returned rows and the hosted submit action is still blocked

## What was browser-tested

All checks below were done with Playwright against the hosted selfservice UI, not only with direct endpoint calls.

### MoPi

Hosted browser result: passed

Tested flows:

- single task
- task campaign task
- self-study task

What worked:

- the hosted tasklist rendered all three MoPi tasks
- opening `/selfservice/tasklist/process/Aufgabe/<task>` loaded the correct task form
- submitting each task through the hosted UI completed the task
- the submitted `gc_comment` values landed in Frappe correctly
- the self-study participant row updated correctly in Frappe

Backend verification after browser submit:

- single task: `Completed`
- task campaign task: `Completed`
- self-study task: `Completed`
- self-study participant: `self_study_task_status = Completed`
- self-study participant: `certificate_eligible = 1`

### Miki

Hosted browser result: partial

Tested flow:

- declaration

What worked:

- the hosted tasklist rendered the Miki declaration row
- opening `/selfservice/tasklist/process/deklaration/<id>` loaded the declaration
- intro step loaded
- capacity/comments step loaded
- address step loaded

What did not work cleanly through the hosted UI:

- after the hosted browser flow, the declaration in Frappe stayed in `workflow_state = Selected`
- `master_data_synced` stayed `0`
- edited declaration fields were not written back to Frappe from the hosted UI flow

Important app-side note:

- the Miki backend final-submit permission issue was already fixed in [declaration_service.py](/workspace/development/frappe-bench/apps/miki_app/miki_app/declaration_service.py)
- the regression test for guest final submit passes in [test_end_to_end.py](/workspace/development/frappe-bench/apps/miki_app/miki_app/tests/test_end_to_end.py)

Practical interpretation:

- the remaining blocker is in the hosted hub/process flow, not the Miki backend store/sync code

### Barakah

Hosted browser result: partial after app normalization fix

Tested flows:

- Aqeeqa confirm
- Aqeeqa complete
- Well confirm
- Well complete

What changed in the app during this pass:

- Barakah was returning a custom task `type` field in its portal responses
- I removed that field from the Barakah portal task/process payloads in [services.py](/workspace/development/frappe-bench/apps/barakah_app/barakah_app/services.py) so the response shape is closer to the working generic MoPi task flow
- Barakah portal tests were updated accordingly in [test_portal.py](/workspace/development/frappe-bench/apps/barakah_app/barakah_app/tests/test_portal.py)

Backend verification after that fix:

- `bench --site development16.localhost run-tests --module barakah_app.tests.test_portal`
- result: passed

What improved:

- before the fix, opening a Barakah hosted process route could immediately return a false \"process already finished earlier\" error
- after the fix, the hosted process route loads the real Barakah task content again

What is still broken in the hosted UI:

- the hosted tasklist still shows `Keine Aufgaben gefunden` / `No tasks found` even though `/rest/tasklist` returns the Barakah rows
- the hosted submit action is still not usable/reliable for Barakah after the page loads

Practical interpretation:

- the Barakah app payload shape is now closer to the working MoPi generic-task contract
- the remaining blocker is in the hosted hub rendering/action layer

## Hub-side issues to fix

### 1. Barakah tasklist rendering

Observed:

- `/rest/tasklist` returns Barakah rows with real `displayName`, `dynamicsId`, `status`, and dates
- the hosted tasklist table still renders `Keine Aufgaben gefunden` / `No tasks found`

What to fix in the hub:

- fix the tasklist table so it actually renders the rows returned by `/rest/tasklist` for Barakah
- this is now reproducible even after removing Barakah’s custom `type` field

### 2. Barakah hosted submit action

Observed:

- the hosted process route now loads the real Barakah task content
- the checkbox state round-trips through `/rest/updateprocess`
- the final submit action is still not exposed/handled correctly in the hosted UI

What to fix in the hub:

- make sure the submit action rendered from `/rest/updateprocess` is actually clickable/executable for Barakah tasks
- also add/fix the missing translation for the submit label if the UI depends on it

### 3. Miki final hosted submit

Observed:

- the hosted Miki declaration process loads and advances through steps
- the hosted flow did not persist the final declaration changes into Frappe

What to fix in the hub:

- make sure the hosted declaration flow triggers the real final submit/write-back step instead of only finishing local UI progress
- if the hub needs an explicit final action or `finalSubmit=true`-style flag for the last step, that mapping is currently missing in the hosted flow

## Current recommendation

- keep using the hosted browser flow for MoPi now
- for Barakah, the app-side payload normalization is in place, but the hosted hub still needs tasklist + submit fixes
- for Miki, the backend is in better shape, but the hosted final-submit flow still needs hub-side wiring
