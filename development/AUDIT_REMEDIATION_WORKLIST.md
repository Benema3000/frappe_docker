# Audit Remediation Worklist — pass 2 (2026-06-12)

Tracking file for implementing all remaining findings from
`CUSTOM_APPS_AUDIT_2026-06-12.md`. Update checkboxes as items land.
Phase 1 (5 immediate fixes) is DONE — see the audit file's remediation log.

## User decisions (binding)

- Do NOT inhibit user access: demo users may log in / re-request access
  repeatedly; throttles must be generous.
- Do NOT reduce any token lifetimes (30-day portal JWT stays; payrexx
  pay-by-email links stay non-expiring — documented accepted risk).
- MoPi: restrict Desk-side task writes to assigned tasks for regular MoPi
  Users; MoPi Managers keep full write. Portal already assignment-scoped.
- good_demo: DROP the Buzz User role from demo roles (no containment).
- Structural follow-up pass (NOT now): file splits (good_event public_pages,
  miki correspondence_defaults/setup, good_npo fundraising, good_demo reset,
  good_connector portal dispatcher), non_profit PaymentEntry minimal-delta
  rewrite, good_npo→good_demo demo-content extraction.
- non_profit: adopt shared ruff config + one-time full reformat (LAST step in
  non_profit so it doesn't fight other edits).
- ilanga_app: PoC — out of scope entirely.
- Hub-visible webhook response shapes stay AS-IS (miki legacy {} / barakah
  400 / mopi []); pin with contract tests + document, do not unify.
- good_connector login: no CAPTCHA (hub calls it programmatically);
  per-email throttle + drop the "no account" outbound email; HTTP response
  stays byte-identical.
- Email footer / Switzerland address template: ownership-guarded writes
  (only set when unset or replacing own previous value), not unconditional.

## A. good_connector (substrate first)

- [x] A1 Login endpoint: per-email throttle (generous) + stop sending
      "account not found" email; response unchanged
- [x] A2 Integration Request logs: metadata-only for data-returning actions
      (no doc.as_dict PII at rest)
- [x] A3 Atomic rate limiter (Redis INCR + expiry, not get/set race)
- [x] A4 HTTP appAction must not honor client-supplied app_context (pop);
      proxy apps keep passing it as a kwarg
- [x] A5 Closed-task guard on StoreData/StoreFiles edit paths (fixes mopi
      completed-history mutability); GetData 409 behavior unchanged
- [x] A6 SKIPPED (decision): getdata field allowlist — hub-compat risk,
      documented instead
- [x] A7 Dedup: single set_user context manager; single email-template render
      helper (auth.py + task_delivery reuse portal_helpers); decode JWT once
      per app action
- [x] A8 _log_request(status=, error=) params (lets miki delete its copy)
- [x] A9 install_utils.py (clear_workspace_sidebar_app, ensure_doctype_permission
      [skip-if-unchanged variant], drop_doctype_permission, ensure_desk_role,
      ensure_role_users_are_system_users, resync_desk_records,
      set_system_setting) + adopt in good_connector's own setup +
      before_uninstall hook for good_connector itself
- [x] A10 pdf_utils.py: _merge_pdf_bytes + _pdf_page_has_content (canonical)
- [x] A11 Public wrappers for symbols other apps import privately
      (check_token_contract, parse_payload, log_request, error_response,
      unauthorized_response) — consumers switched in their sections
- [x] A12 SEMGREP_OVERRIDES.md: document geo.py file-traversal annotations
- [x] A13 tests/browser_harness.py (shared Playwright helpers; consumers
      adopt in their sections)
- [x] A14 Shared "visible task names for email" helper next to
      portal_email_can_access_task (for barakah/mopi dedup)

## B. payrexx_integration

- [x] B1 pay_invoice runs as configured least-privilege automation user
      (same resolution as webhook path), not hardcoded Administrator
- [x] B2 Single as_automation_user helper (currently 2 copies)
- [x] B3 Export sign_reference/verify_reference (good_demo reuses)
- [x] B4 Verify frappe.get_traceback() does NOT serialize locals → if so,
      close PII-in-traceback finding as no-change with note
- [x] B5 cint(flt(amount, 2) * 100) explicitness for minor units

## C. non_profit

- [x] C1 payment_entry.py: pin dt == "Donation" + has_permission(throw) in
      get_donation_payment_entry AND get_payment_reference_details
- [x] C2 check_permission("write") on Donation.send_thank_you,
      Membership.generate_invoice, Membership.send_acknowlement,
      RecurringDonation.create_next_donation
- [x] C3 www/donate.py: never overwrite existing Donor.donor_name from guest
      input (use submitted name on the Donation only)
- [x] C4 chapter.leave → methods=["POST"] (check template-page callers first)
- [x] C5 Dead code: Certification Application + Certified Consultant doctypes
      + 2 web forms + portal/global-search hooks (with delete_doc patch);
      join/leave_chapter template pages; Chapter.enable; hooks doctype_js
      ghost entry; config/docs.py; trim hooks boilerplate
- [x] C6 Root test_email_e2e.py / test_donate.py: move smoke script to
      scripts/, parameterize hardcoded personal email
- [x] C7 fundraising_setup.py: stop overwriting Donation Thank You DE template
      every migrate (create-if-missing / ownership guard)
- [x] C8 Donation.validate error message "Member" → "Donor"
- [x] C9 RESOLVED differently: non_profit has no Address Template writer, so no
      third writer was added — the collision fix is the miki ownership guard (K9);
      miki/good_npo writes become ownership-guarded (see G/K)
- [x] C10 LAST: pyproject + shared ruff + refreshed pre-commit + one-time
      reformat (+ .prettierrc)

## D. mopi_app

- [x] D1 permission.py: ptype-aware has_task_permission (write/submit/cancel/
      delete → assigned-only unless MoPi Manager); read unchanged
- [x] D2 api.py: rate-limit GetStartableProcesses/StartProcess; no
      Integration Request insert for unauthenticated short-circuit calls
- [x] D3 training.py _file_url_to_data_uri: no arbitrary private-file
      inlining (restrict to public or attached-to-module/certificate +
      permission check)
- [x] D4 certificate wkhtmltopdf: --disable-local-file-access (mirror miki)
      + escape interpolated user fields
- [x] D5 cint() instead of bool(int(...)) in whitelisted signatures;
      enqueue_after_commit=not frappe.flags.in_test
- [x] D6 Single retry_on_deadlock helper (3 copies)
- [x] D7 Drop 3 duplicate get_*_users whitelist wrappers (JS → one endpoint)
- [x] D8 dashboard.get_home_dashboard: extract helpers (light)
- [x] D9 count_expiring_qualification_certificates: count query, not
      limit=9999 materialization
- [x] D10 permission.py assignment predicate → shared good_connector builder
- [x] D11 Adopt shared Playwright harness
- [x] D12 Hub contract test pinning GetStartableProcesses/[] + unauthorized
      shapes (no behavior change)

## E. barakah_app

- [x] E1 Rate limit at top of goodApi_webhook_BarakahAction
- [x] E2 payload.pop("app_context") before delegating (guest 500 fix)
- [x] E3 Delete dead update_barakah_process (adapt test)
- [x] E4 Local visibility pre-filter → consume good_connector shared helper (A14)
- [x] E5 Delete dead services.on_task_update (adapt test)
- [x] E6 Remove ensure_setup() calls from one-shot patches (after_migrate
      already runs it)
- [x] E7 Parametrize Aqeeqa/Well order-send path (~60 dup lines)
- [x] E8 _is_truthy ×2 → frappe.utils.sbool/cint
- [x] E9 portal.py dead fragments (unreachable fallback, dead delegate entry,
      unused param, double form_dict merge) + if-chain → dispatch dict
- [x] E10 Untranslated frappe.throw f-strings → frappe._()
- [x] E11 Private good_connector imports → public wrappers (A11)
- [x] E12 run_reminders endpoint → frappe.enqueue (check Desk JS caller)
- [x] E13 _ensure_doctype_permission → install_utils variant
      (skip-if-unchanged; stops per-migrate writes)
- [x] E14 Adopt shared Playwright harness
- [x] E15 Hub contract test pinning current response shapes
- [x] E16 SKIPPED (documented) (follow-up): ensure_setup split (L), shield HTML →
      template file, lifecycle-hook enqueue — documented only

## F. good_demo

- [x] F1 Refuse converting pre-existing real (non-demo) accounts; existing
      demo users keep re-login/re-request flows (add explicit test)
- [x] F2 Checkout token requires demo marker + docstatus binding (in-flight
      demo links may break — acceptable, daily reset wipes them); reuse
      payrexx sign_reference (B3)
- [x] F3 confirm_demo_access: generous rate limit (e.g. 60/h/IP)
- [x] F4 Weekly purge job: disabled demo users + signups older than 30 days
      (marker-disciplined)
- [x] F5 Drop Buzz User from DEMO_ROLE_CANDIDATES (user decision)
- [x] F6 Implement _can_issue_demo_login_link guard: deny pre-existing
      non-demo accounts (consistent with F1)
- [x] F7 Single is_demo_user()/has_field() in utils module (5×/6× copies)
- [x] F8 Dead code: as_automation_user ImportError fallback; Sponsor/
      Volunteer double registration; double boot hook; weaker escapeHtml
      duplicate (keep stricter)
- [x] F9 Template string-surgery (setup.py:363-490) → one-time patch
- [x] F10 extractServerMessage XSS sink → textContent/DOMParser
- [x] F11 Daily reset → scheduler dict form pinned to long queue

## G. good_npo

- [x] G1 Guest endpoints stop mutating existing Member/Donor master data
      (name/language/address) — record submitted values as Comment for staff;
      throttle membership-confirmation re-send per membership (generous)
- [x] G2 Escape user values in PDF/email Jinja contexts (| e)
- [x] G3 SEMGREP_OVERRIDES.md resync (remove ghost, add missing 2, fix name)
- [x] G4 _queue_membership_confirmation actually enqueues after commit
- [x] G5 Dashboard monthly chart: permission-aware SUM aggregation (fixes
      wrong totals with >limit rows)
- [x] G6 Membership invoice: set defaults so values survive submit; drop
      post-submit db.set_value on submitted invoice (careful, has tests)
- [x] G7 _insert_doc_with_retry: savepoint-based retry (current full rollback
      can never succeed)
- [x] G8 Donor contact creation → good_connector.identity_matching (mirror
      membership path)
- [x] G9 Dead code: ensure_goodnpo_address_metadata stub +
      _ensure_docfield_property; boot video plumbing; _link_member_contact_
      to_record; parametrize duplicate address-linkers; single
      _runs_mail_jobs_inline; drop duplicate boot hook registration
- [x] G10 ensure_membership_email_template string surgery → one-time patch +
      create-if-missing
- [x] G11 Branding/email-footer writes ownership-guarded (no unconditional
      site rebrand per migrate); Switzerland template defers to non_profit
- [x] G12 Demo-bank machinery (~160 lines) → good_demo (tests adapted)
- [x] G13 preferred_language double-write cleanup
- [x] G14 RESOLVED as documentation: payload parity test would require decoding rendered SVGs (brittle); both engines documented instead

## H. good_event

- [x] H1 Delete 6 orphan empty doctype dirs + unregistered patch
      migrate_event_master_care_forms.py
- [x] H2 Delete 5 dead helpers (api.py ×3, coupons.py ×2)
- [x] H3 esc() ×4 → services/utils.py
- [x] H4 Confirmed-attendee-count: consolidate on waitlist helper; delete
      unused api.py copy
- [x] H5 Shared resolve_provider(hook_name) helper (6+ copies)
- [x] H6 Remove duplicate backfill_event_booking_titles() call (setup.py:55-56)
- [x] H7 before_uninstall hook (currently commented out) — sidebar fixture
      protection
- [x] H8 registration_received manual=True: comment/dedicated path (S)
- [x] H9 Comment intent on email-sending lifecycle hooks
- [x] H10 SKIPPED (follow-up pass) (follow-up): public_pages split, _ui_text_json → data
      files, _registration_script_html → asset

## I. good_help

- [x] I1 get_help N+1 → batch visibility fetch (one get_all, reuse loaded doc)
- [x] I2 Delete dead _creation_from_order/installed_on_from_order + their
      tests + now_datetime import
- [x] I3 with open(...) context manager (sync.py:189)
- [x] I4 Specific exception (ImportError) instead of broad swallow (sync.py:92)
- [x] I5 .prettierrc aligned with shared config

## J. workflow_visualizer

- [x] J1 .prettierrc (required by bench standard)
- [x] J2 Uniform PermissionError (no exists-oracle before permission check)
- [x] J3 console.warn on xcall failure in client
- [x] J4 Delete empty scaffold dirs (config/, templates/pages/) after
      reference check
- [x] J5 after_migrate named alias in setup.py (greppability)

## K. miki_app

- [x] K1 before_uninstall hook (sidebar fixture protection)
- [x] K2 Non-legacy webhook success logging parity (_log_request on success)
- [x] K3 SEMGREP_OVERRIDES.md: drop stale geo.py entry
- [~] K4 DEFERRED to structural pass: the receivables/correspondence stacks are parallel-but-divergent (different lang/BCC/button semantics) — true consolidation changes email output. receivables.py ↔ correspondence.py shared helper layer (intra-app
      dedup; letter-head/email/QR helpers single module)
- [~] K5 PARTIAL: add_comment failure now logged; phase extraction deferred to the structural pass
- [x] K6 Remove unused import (campaign_readiness nowdate)
- [x] K7 Silent `except Exception: pass` pass: add frappe.log_error or
      intent comment (~30 sites, judgment per site)
- [x] K8 _log_failed_integration_request → shared _log_request(status=,error=)
- [x] K9 Email footer / Switzerland template writes ownership-guarded
- [x] K10 GetStartableProcesses pre-auth response: documented as accepted
      (process name only, hub-compat) — no behavior change
- [x] K11 Adopt shared Playwright harness
- [x] K12 Hub contract test pinning current legacy response shapes
- [x] K13 _file_url data-uri/PDF paths already safe (disable-local-file-access)
      — no change
- [x] K14 SKIPPED (medium-confidence) (medium-confidence): _advance_workflow_to_under_review
      graph-walk rewrite

## L. Cross-cutting / docs / tooling

- [x] L1 Bench AGENTS.md: fix miki before_uninstall claim (true after K1),
      add miki_app → payrexx_integration to dependency graph, fix
      workflow_visualizer AGENTS.md note, note ilanga PoC status
- [x] L2 good_demo/good_npo double boot-hook registration (also F8/G9)
- [x] L3 Audit file: keep remediation log updated per section

## Phase 3 (after implementation)

- [x] P1 Test audit DONE (3 review agents). Outcomes implemented:
      fixed 2 stale good_npo tests (chart limit, enqueue assertions); added
      gap tests — good_demo purge job (4 tests incl. never-claims-real-
      accounts), good_npo (footer guard negative, invoice drift logger,
      guest no-mutation), non_profit (write-permission negatives, dt pin,
      donor-comment), mopi (private-file inlining, wkhtmltopdf flags pinned
      in mock, asset path confinement), payrexx (IR records owning settings,
      reconcile prefers IR gateway), workflow_visualizer (no existence
      oracle, transition access gates), miki (footer ownership guard ×2),
      barakah (order savepoint), good_connector (rate limiter unit tests);
      efficiency — qr_bill suite on shared class Company (~6-8 min saved),
      task_delivery setUpClass, barakah/miki ensure_setup memoized per
      process (barakah was quadratic via task rescan), _apply_rate_limit
      in_test bypass (cross-suite 429 flake). Deferred (noted): reminder-
      runner-level recipient_contexts unit test (covered end-to-end by
      barakah token-isolation test), good_connector permissions.py SQL dup,
      pdf_utils canonical-home tests (covered by 3 consumer suites).
- [x] P2 first sweep stopped intentionally after good_connector/payrexx/mopi
      (user requested the structural pass; full sweep repeats after it).
      Two failures found = bugs in my new tests, both fixed (flags patching,
      link-validated fixture). qr_bill batch dropped 489s -> 152s.

## Phase 4 — structural follow-up pass (user-approved start)

- [x] S1 good_connector: portal dispatcher -> per-action handler registry
      (_ACTION_HANDLERS, 13 handlers); permissions.py delegates to
      portal_helpers.assigned_task_sql_condition. Validated green (contract
      36 / logging 6 / permissions 3 / ops 4).
- [x] S2 good_event: ui_texts.json data file (lru_cache), event_registration.js
      static asset, public_pages split into event_detail_render.py +
      registration_form.py (facade re-exports incl. _status_chip_label).
      test_event_lists green (36); full app suite validation in progress.
- [x] S3 good_npo: fundraising.py -> package (common/donations/membership/
      erp_linking/emails + facade keeping all patch targets); demo content
      extracted to good_demo/npo_demo.py behind the new
      good_npo_demo_decorators hook (clean defaults without good_demo).
      Suite green after fixes: footer-ownership test, boot-hook assertion,
      and the recycled-name invoice adoption bug (see fallout section).
- [x] S4 miki: implemented (correspondence_templates/seeds, setup_desk/
      _permissions/_defaults, sync_master_data phases; facades keep patch
      targets, ruff clean). Suite green (note: frappe's v16 runner prints
      one "Ran N tests" line per category — judge by exit code + ✖ count,
      not the last summary line).
- [x] S5 good_demo: reset.py -> seeding.py + seed_catalog.py (facade keeps
      thank-you refill cluster); demo.html JS -> public/js/demo_page.js with
      window.goodDemoBoot config; template-content tests updated. Suite
      green (64) after the fallout fixes below.
- [x] S6 non_profit: implemented (payment_entry.py 509->340; 5 overridden
      methods; forked validator replaced by get_valid_reference_doctypes
      hook — verified present in installed ERPNext; dead Fees/Student/
      Member-NameError paths removed; session permission gates preserved;
      ruff clean). Suite green (30 reported, OK).
- [x] S7 barakah: implemented (ensure_setup = ensure_core_setup every call +
      reconcile_setup gated on barakah_setup_reconciled_version default vs
      app __version__; hooks unchanged; test memo preserved. Well-shield
      HTML -> templates/well_shield.html via frappe.render_template, proven
      byte-identical across 6 cases; escaping kept in Python).
      Validated green across runs: setup/dashboard/workflow_transitions/
      task_sync/legacy_migration/portal (full-app runs), reminders 17/17,
      api_contract 2/2, orders 11/11. test_e2e_playwright contains
      module-level pytest-style functions run via the browser harness —
      frappe's unittest runner collects 0 tests from it by design.
      MySQL (2006) "Server has gone away" hit twice, both ~45+ min into
      long multi-module sessions, never in isolation; MariaDB uptime
      uninterrupted (no restart), session timeouts sane (wait 8h,
      max_allowed_packet 16MB), shield images small (~35KB). Verdict:
      sporadic containerized-DB connection drop (environment), not a
      code/test bug. If it recurs in the final sweep, rerun the affected
      module in isolation.
- [x] S8 Final full serial sweep after the structural pass — GREEN. Ran all
      requested custom-app suites serially against `development16.localhost`,
      with `barakah_app` last and `ilanga_app` skipped by user decision. Initial
      red suites were rerun after one `clear-cache`; deterministic test-side
      fallout was fixed and full app reruns finished green.

      | App | Tests seen | ✖ count | Exit code | Fixes applied |
      |---|---:|---:|---:|---|
      | `good_connector` | 127 | 0 | 0 | None; initial lock/deadlock fallout reran green. |
      | `good_event` | 373 | 0 | 0 | `good_event/tests/test_correspondence.py:596,600` timezone-stabilized schedule-row ICS assertion to UTC output. |
      | `good_npo` | 61 | 0 | 0 | None. |
      | `good_demo` | 64 | 0 | 0 | None; initial naming-series deadlock fallout reran green. |
      | `miki_app` | 208 | 0 | 0 | None. |
      | `mopi_app` | 101 | 0 | 0 | `mopi_app/tests/test_training.py:687-692` completed the private-file inlining test fixture with required module fields. |
      | `barakah_app` | 105 | 0 | 0 | `barakah_app/tests/test_portal.py:118-124,915-921` avoids invoking country-retarget hooks for generic setup-only fixture rewrites; dedicated retarget tests still exercise hooks. |
      | `non_profit` | 93 | 0 | 0 | `test_donate.py:141-142` clears the inserted Donation's `ignore_permissions` flag before asserting write-permission enforcement. |
      | `payrexx_integration` | 30 | 0 | 0 | None. |
      | `good_help` | 54 | 0 | 0 | `good_help/tests/test_good_help.py:279` explicitly grants `Desk User` in the app-permission test. |
      | `good_analytics` | 32 | 0 | 0 | None. |

      Still red: none. Lint for touched files passed with
      `/workspace/development/frappe-bench/env/bin/ruff check` and
      `/workspace/development/frappe-bench/env/bin/ruff format --check`.

      CI follow-up: `good_npo` and `good_demo` had stale clean-install test
      expectations after the local sweep. Fixed in app repos with test-only
      commits and final head runs are green: `good_npo` `330fcc5` / Actions
      `27443806703`; `good_demo` `8f933c4` / Actions `27443337531`.

### Fallout fixed during structural validation (good_npo suite)
- test_setup_records_are_available footer assertion now honors the
  session's footer ownership guard (kibesuisse footer owned by miki on the
  shared bench is left intact; goodvantage branding asserted only when
  goodvantage owns the footer).
- Real find — membership invoice adoption by recycled name:
  _get_or_create_membership_invoice matched Sales Invoices by
  good_npo_membership name only. The Membership naming series rolls back
  in tests (and on restores) while submitted invoices persist, so a new
  membership reusing a name adopted a foreign orphaned invoice (different
  customer; the "drifted" null cost_center came from these orphans, not
  from ERPNext defaulting). Fix: _invoice_belongs_to_member ownership
  check (contact_email, then customer) before adopting; create fresh
  otherwise. Test query also filters by customer now. Observation: test
  runs leak committed Sales Invoices past rollback (orphans 00546+,
  series at 90 vs orphan names up to 00202) — likely an explicit commit
  in the flow; not chased further.
- boot_session -> extend_bootinfo assertion staleness (same dedupe as
  good_demo).

### Fallout fixed during structural validation (good_demo suite)
- confirm_demo_access rate-limit (session-added) throws "Either key or IP
  flag is required" when tests fake frappe.local.request without request_ip
  -> both confirmation tests now save/set/restore request_ip = 127.0.0.1.
- "Certified Consultant" references removed from good_demo (hooks.py,
  privacy.py, good_demo_desk.js, 2 test tuples) — doctype was deleted with
  non_profit's certification module earlier this session.
- Site data fix: Role "Wiki User" had desk_access=1 (auto-created when the
  wiki app was installed 2026-05-20); flipped every new portal user to
  System User via wiki's add_wiki_user_role after_insert hook. Set
  desk_access=0 (stock wiki only gives Wiki Approver desk access).
- retention.py purge: `cint(conf.get(...) or PURGE_AFTER_DAYS)` swallowed
  the documented 0=disabled value -> explicit None check.
- seeding._ensure_member_receivable_invoice returned an already-paid
  invoice (seed contract: preview member shows an OPEN receivable) ->
  now requires outstanding > 0, else creates a fresh marked invoice.
