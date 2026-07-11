# Custom Frappe Apps Audit — 2026-07-11

Read-only audit of all 14 custom apps in this bench, one month after the
`CUSTOM_APPS_AUDIT_2026-06-12.md` audit + its two full remediation passes (see
that file and `AUDIT_REMEDIATION_WORKLIST.md`). Method: a mechanical cross-repo
consistency sweep (configs, docs, whitelist type hints, controllers, patches,
guest-endpoint inventory, `db.commit`/`json.loads`/`pypika`/bare-except grep,
`nosemgrep` counts) + 10 read-only sub-agents — full audits of the two
never-audited apps (`good_newsletter`, `good_analytics`), delta audits of the
12 previously-audited apps scoped to commits since 2026-06-12, and one cross-app
consistency agent. Every High/critical finding was independently re-verified
against the code (and, where relevant, live dev-site data) before landing here.

Apps: good_connector, good_event, miki_app, mopi_app, barakah_app, good_demo,
good_npo, non_profit, payrexx_integration, good_help, ilanga_app,
workflow_visualizer, **good_newsletter (new)**, **good_analytics (new)**.

> **Scope note:** `ilanga_app` remains a proof-of-concept — out of scope for
> remediation (findings noted only for completeness). Binding user decisions
> from the June remediation are honored throughout: no token-lifetime changes;
> hub webhook response shapes stay as-is; good_connector login keeps no CAPTCHA;
> demo re-login throttles stay generous.

---

## Remediation log — 2026-07-11

All actionable findings (High + Medium + Low + docs) were fixed in the same
session, at the user's direction, with **strict enforcement** on the
user-impacting gates (miki post-submit portal edits are hard-blocked; the
good_analytics Donor-read check, and the barakah/mopi closed-task guards, all
enforce rather than warn). One commit per app, committed on each app's current
branch. `ilanga_app` was left untouched (PoC); `payrexx_integration` needed no
change (its only open items are INFO notes explicitly deferred as "don't fix now
— would break in-flight links").

| App | Commit | Branch | Scope |
|---|---|---|---|
| `good_connector` | `a726ec9` | main | PEP 758 (`# fmt: skip`), `portal_user_language` from token email, closed-task file-mutation guard, GetNewsList de/fr/it, SEMGREP+docs, shared `install_utils.ensure_desktop_icon` |
| `non_profit` | `50d6259` | miki-dev | STAGE_WALK → forward-BFS, PE-flow rollup recompute + daily reconcile job, workflow-rebuild hash guard, cross-record validation, `project`→PE, PEP 758 restructure, dead-settings/doc cleanup |
| `good_event` | `aa8b1ef` | main | **2× HIGH reflected XSS** (escape + `_safe_relative_url` reject `"<>`), letterhead cache site-key, dead flow-guard, guest `search_organizations` gate, SEMGREP resync |
| `miki_app` | `669556a` | main | **STRICT** StoreData workflow-state gate, shared-contact mutation guard, cross-recipient login-link fix, close-resync gate, SEMGREP 7 sites, report perm, req-python 3.14 |
| `barakah_app` | `bad5eab` | main | closed-task StoreData 409 (regression), counter `for_update` locking read, Set-Counter task refresh, PEP 758 (`# fmt: skip`), shield `</script>` escape, guest rate-limit, audit trail |
| `good_npo` | `a08d586` | main | **HIGH** sidebar/workspace → Non Profit module (+ resync patch), route-helper doctypes, DocPerm-shadowing caveat, stale-Guide doc cleanup |
| `good_demo` | `0cf61e7` | main | **HIGH** demo-marker allowlist (canonical single source + Major Gift/Donor Interaction), reset cleanup of next-action Tasks, reseed drift guard, title_field |
| `good_analytics` | `d143d9e` | version-16 | **STRICT** Donor-read gate on email paths, N+1 batch-loader, `refresh_now`/static-copy/source-list guards, ECharts escaping, dead code, branch docs |
| `good_newsletter` | `e6c2743` | main | signup-page escaping, per-migrate DocPerm writes → `install_utils`, click dedup, SEMGREP doc, `enqueue_after_commit`, adopted shared desktop icon |
| `good_help` | `87dcc2a` | main | private-tier **fail-closed** on field-less wiki, docs |
| `mopi_app` | `e9c2769` | main | docs (write-restriction, public-attachment warning, delete-guard intent, image-migration note) |
| `workflow_visualizer` | `0b44a02` | version-16 | `patches.txt` `.execute` fix, uniform-403 no-oracle, docs, SEMGREP stub |
| bench `AGENTS.md` | (with this file) | /workspace | C2: add good_analytics, non_profit `erpnext`, email-flow line, providers, sidebar-hook list |

**Cross-cutting decisions taken during remediation:**
- **PEP 758 / `requires-python`:** `ruff format` (0.15.11, target py314) *rewrites*
  `except (A, B):` back to the unparenthesized form, so "parenthesize" is not a
  stable fix. Resolved by parenthesizing **with `# fmt: skip`** on the two real
  bug sites (good_connector, barakah), keeping each app's honest declared floor;
  non_profit restructured its site away entirely. No `requires-python` was
  downgraded; miki was bumped to `>=3.14` for consistency (internal app).
- **Desktop-icon dedup (C4) — completed in a follow-up round** (user-directed).
  Initially deferred because each app's "clone" was behaviorally divergent
  (upsert/reconcile vs create-if-missing, `standard=1` or not, cache-clear or
  not). On review those differences were accidental drift, not deliberate — the
  one real distinction is `standard` (1 only for apps that also ship a
  `desktop_icon` fixture: good_connector, good_newsletter, good_analytics,
  good_npo; 0 for code-only tiles). So `install_utils.ensure_desktop_icon` was
  rewritten as the single implementation (reconcile field-by-field,
  skip-if-unchanged, cache-clear, stale-label retire; `standard` a parameter),
  and all 8 good_connector-dependent apps now route through it
  (`good_connector` 139247b, + good_demo/mopi/barakah/good_analytics/good_npo/
  miki/good_event; good_newsletter already called it). `portal_helpers.
  upsert_desktop_icon` is now a thin delegating shim. `good_help` keeps its own
  copy — it does not declare good_connector as a dependency, so importing the
  shared helper would be an undeclared cross-app import.
- **`search_index` on Donation (the other deferred item) — done.**
  `Donation.date` and `Donation.campaign` now carry `search_index` (non_profit
  `7209d63`); the `date_index` / `campaign_index` were built and verified on the
  dev site. `paid` (low-cardinality Check) and the newer `cost_center`/`project`
  dimensions were left unindexed by choice (single-column index adds little for a
  boolean; low query frequency for the others).
- Verification: all four Highs and the load-bearing Mediums were re-read in the
  committed diffs (the good_event XSS payloads, the miki state gate, the barakah
  closed-task guard, the good_demo marker allowlist, good_connector
  `portal_user_language` against live Customer naming, non_profit STAGE_WALK).

**Validation (serial bench suites + on-push CI):**
- Local targeted suites (run serially — never parallel, per the bench deadlock
  rule): non_profit `test_major_gift` 11/11 + `test_donation` 9/9;
  good_connector `test_language_setup` 4/4 + `test_api_contract` 40/40; miki
  `test_miki_app` 163/163 + `test_writeback` 8/8. good_demo's full suite is too
  slow locally (heavy analytics/major-gift seed) — validated statically + via CI.
- On-push CI (server tests): **all 12 apps green.** good_connector and
  workflow_visualizer went green after their pre-existing test fixes; miki was
  locally green 163+8; barakah passed CI (its local `test_orders` was 14/14 at
  ≈13 min — slow seed, not a hang; the closed-task-guard `test_portal` is covered
  by that CI run since it's too slow to finish locally under the tool timeout).
- Two CI reds surfaced were **pre-existing test-vs-code drift, not audit
  regressions**, and were fixed with test-only follow-ups: good_connector
  `test_desk_workarounds` pinned a CSS cache-bust version the concurrent
  "page-title-shrink" work (`747ecfd`) had bumped (→ made version-agnostic,
  `1ad385b`); workflow_visualizer `test_forbidden_document...` still mocked
  `check_permission`, which the new uniform-403 gate no longer calls (→ mock
  `has_permission`, `60f6630`).
- One miki test (`test_shared_primary_contact_is_never_renamed`) failed on a
  setup-ordering bug in the agent-written test — it set `customer_primary_contact`
  expecting the declaration to snapshot it, but the controller resolves the
  Hauptkontakt via `get_default_contact` (which keys off `is_primary_contact`).
  The **fix was correct**; the test setup was corrected (folded into the miki
  commit) and now passes 8/8.

---

## Executive Summary

**The estate remains in strong shape, and the June remediation has held** —
zero raw-SQL injection, zero bare excepts, zero `db.commit()` in doc-event or
install hooks, type hints on all ~230 whitelisted endpoints, real controllers
for every DocType, `parse_json` throughout, idempotent guarded seeds. Tooling is
now genuinely uniform: ruff (line-length 110, `py314`, tab indent), `.prettierrc`
(printWidth 99, tabs), pre-commit hook revisions, and `.editorconfig` are
**byte-identical across all 14 apps** — the June drift (non_profit had no ruff,
workflow_visualizer no `.prettierrc`) is fully closed.

The new debt is concentrated and mostly shallow. Two genuinely new apps
(good_newsletter ~5.7k LOC, good_analytics ~2.6k LOC) were built to a high
standard — good_newsletter's SNS/token/redirect security engineering is
exemplary — but each has one real permission/escaping gap. The month's heavy
feature work (good_event 34 commits, miki_app 26) introduced a small number of
correctness/security regressions in the changed surfaces. And a single
Python-3.14-only syntax choice (PEP 758 unparenthesized `except`) has spread
inconsistently against apps that still declare a 3.11 floor.

### Top findings by severity

**High (fix immediately)**
1. **good_npo — the Good NPO sidebar is broken right now for every
   non-Administrator user.** Deleting the `Good NPO Guide` doctype (c544ee8) left
   module `Good NPO` with zero DocTypes, so it can't enter any non-admin's
   `allow_modules` and the sidebar/workspace drop out of boot; demo users get an
   empty left nav. Verified against the live DB. §good_npo.
2. **good_demo — demo-user-created Major Gifts / Donor Interactions are never
   demo-marked**, so `reset` can never claim them — a direct violation of the
   app's containment rule (the marker hook was registered but the allowlist
   wasn't extended). §good_demo.
3. **good_event — two guest-reachable reflected XSS.** `redirect_to` on
   `payment-failed.html` (+ the identical `payment_success.py` helper) and the
   `booking` URL param on `event-register.html` both render unescaped into a
   Frappe web template (autoescape off, no CSP). §good_event.

**Medium (fix soon)**
- **good_connector — PEP 758 `except` on an `after_migrate` path**
  (`setup.py:136,142`) while the app declares `requires-python >=3.11`:
  install/migrate is a hard `SyntaxError` on Python 3.11–3.13. Same class in
  **barakah_app** (`services.py:115`). §Cross-cutting.
- **good_connector — `portal_user_language` receives the tenant org_id where it
  expects a Customer docname** → the "organisation language authoritative"
  kibesuisse feature is silently dead (always falls back to German). §good_connector.
- **good_connector — closed-task read-only guard doesn't cover mopi file
  mutations** (delete / attach-move of portal uploads on completed history
  tasks). §good_connector.
- **good_analytics — donor-email extraction gated only on segment-read**, not
  on any `Donor` permission, unlike its sibling export path. §good_analytics.
- **good_newsletter — public signup page renders Audience title/description
  unescaped** (Newsletter Manager-authored, but a public unauthenticated page).
  §good_newsletter.
- **miki_app — portal `StoreData` is not workflow-state-gated** and the new
  Under Review gate never re-arms after first sync → post-review capacity edits
  can be auto-advanced and billed unreviewed. §miki_app.
- **miki_app — shared multi-customer contact mutated by one org's declaration**
  (contacts-only invariant violated in the contact phase). §miki_app.
- **miki_app — cross-recipient login-link fallback** in the new broadcast
  correspondence (recipient B can receive user A's personal JWT login URL).
  §miki_app.
- **non_profit — `advance_major_gift_to_stage` crashes for any gift past
  Qualification** (STAGE_WALK starts the walk behind the current stage → illegal
  backward transition). Exported substrate API. §non_profit.
- **non_profit — donor/major-gift rollups go stale in the real Payment Entry
  flow** (paid flag flipped via `db.set_value`, no rollup recompute; the
  "daily reconciliation job" the docstring promises doesn't exist). §non_profit.
- **non_profit — major-gift Workflow rebuilt + force-saved every migrate**
  (operator edits reverted; undocumented). §non_profit.
- **barakah_app — local `StoreData` accepts writes to closed tasks** — the
  June-remediated "completed history mutable" class re-regressed on the
  app-local path (the shared handler still guards it). Plus an order-counter
  concurrency gap and a manual-renumber that doesn't reach the open task.
  §barakah_app.
- **workflow_visualizer — `patches.txt` entry ends in `.execute`** → the patch
  handler double-appends and it has never executed anywhere; a hard crash the
  day the line looks new to a migrating site. §Cross-cutting.
- **good_newsletter — `ensure_email_group_access` rewrites Custom DocPerm on
  every migrate** (reintroduces the exact per-migrate-write antipattern the June
  `install_utils` helper was built to remove). §Cross-cutting.

**Consistency / docs (verified, cheap)**
- Bench `AGENTS.md`: `good_analytics` **missing entirely** from the app table
  and dependency graph; `non_profit` labeled "(standalone)" but requires
  `erpnext`; the per-event `disabled_email_flows` description is stale
  (good_event moved to per-flow checkboxes). §Cross-cutting.
- `SEMGREP_OVERRIDES.md` drift in **miki_app** (7 undocumented, incl. 6
  `frappe-ssti` in `receivables.py`), **good_event** (2 undocumented + 3 stale),
  **good_connector** (2 undocumented + 1 stale), and minor gaps in
  good_newsletter / good_demo / non_profit. §Cross-cutting.
- Desktop-icon setup helper cloned across ≥7 apps; a shared
  `install_utils.ensure_desktop_icon` is the obvious home. §Cross-cutting.

---

## Per-app findings

<!-- SECTION: good_event -->
### good_event — delta audit (34 commits)

**[HIGH] Reflected XSS via `redirect_to`** — `www/payment_failed.py:24,28` +
`www/payment-failed.html:156` (and the identical pair in `payment_success.py`).
`_safe_relative_url` rejects only scheme/netloc/`//` and forces a leading `/`,
so `/x"><script>…</script>` passes through and renders unescaped into
`href="{{ redirect_to }}"`. Frappe web templates render with autoescape OFF and
the site sets no CSP; the page is guest-reachable. **Verified** end-to-end
against the helper. New in-window (94758ad). Fix: `href="{{ redirect_to | e }}"`
and reject targets containing `"<>`.

**[HIGH] Reflected XSS via `booking`** — `services/public_pages.py:474` +
`www/event-register.html:22`. `registration_booking = form_dict.get("booking")`
(raw URL param) renders as unescaped `<dd>{{ registration_booking }}</dd>` on
the `?success=1` page → element-content injection. **Verified.** The vulnerable
line predates the window but sits in the in-window-reworked registration render
and shares the one-line fix (`| e`). (In scope as a current-state finding.)

**[MEDIUM] Cross-site letterhead image bleed** — `services/pdf_branding.py:87`.
`_image_data_uri` is a module-level `@lru_cache` keyed only on `src`, but
`_local_image_path` resolves `/files/…` and `/private/files/…` per-site; a
worker serving multiple sites embeds site A's logo in site B's PDFs. New
in-window (5c2c5e5/94758ad). Fix: add `frappe.local.site` to the cache key (or
drop the cache — letterhead render is not hot).

**[LOW]** Dead disable-guard `is_flow_disabled_for_event("trainer_cancellation")`
— no such field exists, so it can never return True (`doctype/good_event/good_event.py:231`).
**[LOW]** Guest `search_organizations` (`api.py:487`) doesn't gate on
`organization_booking_enabled_for_event` — any published slug lets a guest
LIKE-enumerate enabled Customers (name+city, ≤50; rate-limited 120/hr).
**[INFO]** `except TypeError, ValueError:` (`services/pre_event_packages.py:709`)
and a dead `combined_bundle` FLOW_LABELS row (`services/correspondence.py:120`).

*Invariants spot-checked and HELD:* single-dispatcher flow-key discipline;
auto-toggle + per-flow disable + `manual=True`; de/fr/it fixtures never
overwritten (managed-hash reconciliation); Closed→"Registration Closed" rename
in full lockstep with a data-migration patch; server-authoritative pricing;
`esc()` in all Python-built HTML; org-vs-participant recipient isolation;
online-payment opt-out server-side; reopen-completed lifecycle-hold; wkhtmltopdf
`disable-local-file-access`; report/export ptype via Custom DocPerm;
correspondence-log removal clean; providers stay generic.

<!-- SECTION: good_connector -->
### good_connector — delta audit (11 commits)

**[MEDIUM] PEP 758 `except` on the `after_migrate` import path** —
`setup.py:136,142` `except TypeError, ValueError:`. `good_connector` declares
`requires-python >=3.11`; this syntax is valid only on ≥3.14, so importing
`good_connector.setup` (the `after_migrate` hook) is a hard `SyntaxError` on
3.11–3.13. This bench + CI are both 3.14 so nothing catches it. **Verified.**
Fix: parenthesize (restores 3.11 compat) — see Cross-cutting for the estate-wide
picture.

**[MEDIUM] `portal_user_language` keyed on the wrong identifier** —
`api/helpers.py:326`; call sites `api/endpoints.py:135,146` and
`api/portal.py:725` pass `check["ngo"]` (the JWT `iss` claim = hosted-hub tenant
org_id, e.g. "11") as the `customer` argument, but the function does
`frappe.db.exists("Customer", customer)`. **Verified against live data:**
Customers are 5-digit series / `_Test Customer`; zero are named like an org_id,
so the `Customer.language` branch is dead and portal language always degrades to
`User.language` → "de". The "organisation language authoritative" kibesuisse
requirement is not delivered. Fix: resolve the Customer from the token email,
not from the `ngo` claim.

**[MEDIUM] Closed-task read-only guard misses mopi file mutations** —
`api/portal.py` `_action_delete_files`/`_can_delete_portal_file` and the
StoreData attach allowed-set (~144-154, ~877-881, ~1009-1031). GetData/StoreData/
StoreFiles correctly 409 on closed tasks, but `_get_assigned_task_names("mopi")`
deliberately includes completed history tasks, and that set is reused as the
*mutable* scope — so a mopi portal user can delete their portal uploads off a
completed task or move one onto an open task. Own-`portal_upload` files only →
integrity/evidence issue, not confidentiality; mopi-only. Fix: exclude terminal
tasks from the delete/attach-source scope.

**[LOW]** GetNewsList still emits `{"de": …}` only (`api/portal.py:757`) — the
same blank-render class 7afb199 fixed for GetLinkList; FR/IT portal sessions
plausibly render News blank. **[LOW]** `SEMGREP_OVERRIDES.md` out of sync (see
Cross-cutting). **[LOW]** DOCUMENTATION.md/HOW_TO.md not updated for the two July
hub-contract changes (`language` key; GetLinkList de/fr/it emission).
**[INFO]** double rate-limit increment on the proxy path (≈250/min effective);
`incrby`-then-`expire` non-atomic TTL edge; GC Integration Log records
handler-returned errors as `status="Success"`.

*Invariants HELD:* HS256 pinned encode+decode, iat/nbf/exp set (no new JWT
claim — `language` is a response key, old tokens still valid); `app_context`
popped on the raw endpoint, trusted-kwarg from proxies only; portal-upload
stamping + DeleteFiles restriction; atomic rate limiter, no mail to unknown
addresses; metadata-only logging + 90-day retention; b3ac985 absolutify uses
request-host `expand_relative_urls` and does **not** make private files public;
pdf_utils pypdf calls verified stable across the local 6.9.2 pin and CI's 6.13.

<!-- SECTION: miki_app -->
### miki_app — delta audit (26 commits)

**[MEDIUM] Portal `StoreData` not workflow-state-gated; review gate never
re-arms** — `declaration_service.py:391-452`. `store_declaration_data` applies
field + `Accounts[]` writes in any workflow state; `_writeable_field`
(`declaration_service.py:181`) is **dead code** (defined, never called — grep
confirmed), while AGENTS.md/DOCUMENTATION.md claim finalized declarations are
read-only. After final submit `master_data_synced=1` is permanent, so the new
shared Under Review blocker `has_master_data_changes and not master_data_synced`
(`workflow_support.py:90`) passes forever; a portal user can post new capacity
numbers to an Under Review declaration (within ±5/±10 thresholds) and daily
escalation auto-advances + bills them unreviewed. The capacity lock arms only
after a submitted invoice. **Verified** (unconditional writes + dead guard). Fix:
reject StoreData when `workflow_state not in PORTAL_EDITABLE_STATES`, or reset
`master_data_synced=0` on new portal changes.

**[MEDIUM] Shared multi-customer contact mutated by one org's declaration** —
`doctype/miki_declaration/miki_declaration.py:1250-1296` (`_sync_contact_phase`).
The billing write-back guards shared (Treuhand) contacts with
`_contact_customer_link_count(contact) == 1`; the contact phase has no such
guard, so one org's declaration rewrites first/last name + primary email of a
contact serving N customers and forces global `is_primary_contact=1` — renaming
it for all of them and pushing it as portal user/correspondence recipient onto
every linked Customer. Fix: apply the same link-count guard (create an
org-specific contact instead).

**[MEDIUM] Cross-recipient login-link fallback** — `correspondence.py:1044-1051`.
The new multi-recipient broadcast resolves per-recipient JWT URLs via
`get_login_url_for_user(recipient)`, but on `""` (disabled/missing User) falls
back to `render_context["portal_link"]` — the *first* portal user's personal
login URL. **Verified** the fallback expression
(`portal_url = login_url or render_context.get("portal_link")`). With Hauptkontakt
contacts now spanning multiple customers, recipient B can be emailed user A's
magic-login link. Fix: only use the `portal_link` fallback for `portal_users[0]`;
otherwise log-and-skip.

**[LOW]** `SEMGREP_OVERRIDES.md` missing 7 annotated sites (6 `frappe-ssti` in
`receivables.py`, 1 `frappe-manual-commit` in `dev_cleanup.py`) — see
Cross-cutting. **[LOW]** Close/enforcement re-sync (`miki_declaration.py:985`)
can clobber interim manual master-data fixes and double-creates ops-queue ToDos
on Debt Enforcement→Closed (same `has_master_data_changes` never-clears root
cause). **[LOW]** Doc drift: AGENTS.md/DOCUMENTATION.md invoice-recipient +
language-priority paragraphs contradict the new all-billing-contacts /
org-authoritative model. **[LOW]** Portal Login Audit report unrunnable for a
bare System Manager (Customer `report` ptype granted only to Reviewer) — exposure
is fine (no tokens).

*Invariants HELD:* `_parse_payload` before dispatch on both webhooks; legacy hub
shapes unchanged (incl. new rate-limit response wrapped); footer/Switzerland
template ownership-guarded; final-submit mutes request-local email; dunning only
on docstatus==1 with outstanding>0 (complete across escalation/dunning);
`db.commit` only in scheduler/one-shot/dev contexts. Reopen-for-correction
landed **complete** despite the "WIP" label. Gutschrift removal clean.

<!-- SECTION: non_profit -->
### non_profit — delta audit (10 commits, branch miki-dev)

**[MEDIUM] `advance_major_gift_to_stage` crashes for any gift past
Qualification** — `non_profit/major_gifts.py:278-301`, `STAGE_WALK:267`. The
walk list always begins at "Qualification" and the loop skips a state only on
exact `doc.stage == state` match, so from Cultivation/Solicitation/Stewardship
the first save sets `stage="Qualification"` — a backward move that frappe's
workflow validation rejects (runs on every save; `ignore_permissions` doesn't
bypass it). **Verified** by tracing STAGE_WALK for Cultivation→Won. Latent today
(tests/seeds only advance fresh gifts) but breaks on a good_demo reseed after any
UI move, and this is exported substrate API. Fix: start the walk at the current
stage's position (or try a direct legal transition first).

**[MEDIUM] Rollups stale in the real Payment Entry flow** —
`custom_doctype/payment_entry.py:182-193` flips `Donation.paid` via
`frappe.db.set_value` (no hooks); nothing calls `on_donation_change`, so
`Donor.total_lifetime_amount`/`is_major_donor` and `Major Gift.closed_amount`
(paid-only sums) go stale in the primary bank/PE path — they recompute only on
Donation submit/cancel/trash and gateway/mock. The `major_gifts.py:164` docstring
promises a "daily reconciliation job" that **does not exist** in
`scheduler_events` (so threshold edits also never retro-apply). Fix: recompute in
`sync_donation_paid_state` when the flag flips, and/or register the daily job.

**[MEDIUM] Major-gift Workflow rebuilt + force-saved every migrate** —
`major_gifts.py:204-261` (`ensure_major_gift_workflow`, called `after_migrate`)
does `set("states", [])`/`set("transitions", [])` and saves unconditionally, so
operator edits (roles, transitions, `is_active=0`) are reverted each migrate —
the opposite of the C7 create-if-missing pattern 100 lines up. DOCUMENTATION.md/
HOW_TO.md never mention the workflow. Fix: guard the rebuild (only-if-missing or
version-stamped) or document code-ownership + the single-role choice.

**[LOW]** `probability` editable but overwritten every save (`major_gift.py:26`;
mark read_only). **[LOW]** No "Mark Lost" from Identification/Qualification
(early disqualification must route through Cultivation). **[LOW]** Dead settings
`stale_interaction_days`/`lapsed_major_months` + phantom "stale scheduler" in
docs. **[LOW]** HOW_TO.md:211 wrongly says Non Profit Member has next-action
write access. **[LOW]** Next-action Tasks expose cultivation subjects to any
Projects User while Major Gift is manager-only (inherent to the agreed Tasks
design — document or scope). **[LOW]** No cross-record validation:
`Donation.major_gift`/`Donor Interaction.major_gift` accept a different donor's
gift; `project` dimension not propagated to the Payment Entry (`cost_center` is).
**[LOW]** PEP 758 `except` in `www/donate.py:87` (publicly installable fork; no
`requires-python` declared). **[INFO]** No `main` branch; origin default
`version-16` is 59 commits behind `miki-dev` → a stock `bench get-app` misses all
fundraising + major-gifts work. Stale Certification rows linger in `de.csv`.

*Invariants HELD:* guest surface unchanged (only `mock_pay`, double-gated);
`donate_confirm` key-gated; `payment_entry.py` dt-pinned + `has_permission`;
write-action doc methods keep `check_permission("write")`; certification removal
thorough (patches resolve, no dangling refs).

<!-- SECTION: good_newsletter -->
### good_newsletter — full audit (new app, ~5.7k LOC)

No High findings. The security-critical surfaces are correctly built and mostly
well-tested.

**[MEDIUM] Public signup page renders Audience title/description unescaped** —
`www/newsletter/subscribe.html:10,12` emit `{{ audience_title }}` / `{{ description }}`
with no `| e`, on a public unauthenticated page, in an autoescape-off
environment. **Verified** (autoescape-off env confirmed; the confirm endpoint
`api/public.py:143` escapes the same value with `escape_html`, proving it's
otherwise untrusted). `title`/`description` are Newsletter Manager-authored, so
exploitability requires that sub-superuser role — bounded, hence Medium. Fix:
`{{ audience_title | e }}` / `{{ description | e }}`.

**[LOW]** No dedup/rate-limit on open/click recording (`services/tracking.py:97`,
`api/public.py:167`) — a forwarded valid click token inflates counters + inserts
unbounded Click rows. **[LOW]** `render_blocks` SSTI overrides undocumented in
`SEMGREP_OVERRIDES.md` (editor.py:119,139). **[LOW]** `frappe.enqueue` omits
`enqueue_after_commit=not frappe.flags.in_test` (`services/dispatch.py:56`,
`api/audience.py:60`) — cosmetic here (deduplicate + re-claim guard the double
fire). **[INFO]** `tokens.py:49` `json.loads` on an already-HMAC-verified
payload (acceptable but deviates from parse_json convention); open pixel sets no
Cache-Control; `subscribe` rate-limit key is `ip:email` (mild opt-in bombing,
gated by captcha + double opt-in).

*Done well:* SNS webhook is solid — constant-time shared-secret gate, signature
verification on by default with signing-cert URL pinned to `https://*.amazonaws.com`,
optional TopicArn pinning, host-validated SubscribeURL fetch, idempotent via
unique message id → forged bounce/complaint suppression is prevented, well
tested. Open-redirect impossible (signed index into stored `tracked_urls`,
bounds-checked). Per-purpose HMAC tokens off the site key, constant-time compare,
`hash`-autonamed recipients. All 22 whitelisted functions permission-gated; PII
doctypes read-restricted to SM + Newsletter Manager; report carries the `report`
ptype. Reuses good_connector captcha + `install_utils.clear_workspace_sidebar_app`.

<!-- SECTION: good_analytics -->
### good_analytics — full audit (new app, ~2.6k LOC)

No High findings. Zero `allow_guest`, zero raw SQL, all 14 endpoints
server-side permission-gated via `_require_analytics_access()`.

**[MEDIUM] Donor-email extraction gated only on segment-read** —
`segments.py:111-135` (`create_email_group`) and `:278-294`
(`newsletter_segment_members`) resolve donor emails via permission-bypassing
`get_cached_doc`/`db.get_value` after checking only `Good Donor Segment` read (+
`Email Group` create), while the sibling `export_mailing_list:138-142` requires
`Donor` export. **Verified** the asymmetry and that `Donor` read is granted only
to Non Profit Manager — so a System Manager (no Donor read) or any future
segment-read role can bulk-extract every member's email. good_newsletter's caller
checks only audience write. Fix: add `frappe.has_permission("Donor","read",throw=True)`
to both email paths.

**[MEDIUM] Per-member N+1 will time out at the promised scale** —
`segments.py:121-126,150-171,288-293` (~5-7 queries/donor). DOCUMENTATION.md
designs for "20k+ donors", but `export_mailing_list`/`create_email_group`/
`newsletter_segment_members` run synchronously in-request → 60-100k queries. Fix:
batch-load Contacts/Addresses set-based; enqueue the XLSX export.

**[MEDIUM] Missing from bench AGENTS.md** — see Cross-cutting.

**[LOW]** `refresh_now` (`good_donor_segment.py:65`) mutates members behind a
read-only gate (add `check_permission("write")`). **[LOW]** `create_static_copy`
of a Static source re-resolves the filter instead of copying the frozen list
(`segments.py:69-84`) — a "copy" can differ from the mailed audience.
**[LOW]** `newsletter_segment_sources:262` enumerates all segments with no
permission check of its own. **[LOW]** Dimension values interpolated unescaped
into ECharts tooltip HTML (`good_analytics_dashboard.js:443,214`).
**[INFO]** No `search_index` on the Donation dimensions aggregated; Pareto
includes the negative-amount NULL band; value-band filter window has no upper
date bound; dead `filter_state.is_empty`/`describe`; `by_year` query duplicated.

*Done well:* uniform server-side gating (direct `/api/method` hits the same
gate); recompute not whitelisted (scheduler + SM/NPM-only trigger, deduplicated);
every SUM/COUNT in SQL over the full set (June good_npo lesson respected);
fixed-threshold RFM, boundary-tested, leap-safe windows; batch-shaped rebuilds.

<!-- SECTION: barakah_mopi -->
### barakah_app + mopi_app — delta audits

**barakah_app**

**[MEDIUM] Local `StoreData` accepts writes to closed tasks** —
`portal.py:162-176`. The GetData branch 12 lines up correctly 409s via
`services.is_closed_barakah_task(task_doc)`, but the StoreData branch goes
straight from `portal_email_can_access_task` to `services.store_barakah_task_data`
with no such guard. **Verified** (the guard function is used for reads, absent
for writes). `portal_email_can_access_task`'s supplier-membership layer still
matches completed tasks, so any current supplier portal user can rewrite
`description`/`gc_comment` on historical tasks and re-trigger completion — exactly
the June-remediated "completed history tasks remain mutable" class, which
4650df7 left un-guarded on the barakah-local path (the shared good_connector
handler was fixed in June). Fix: add the same closed-task 409 before
`store_barakah_task_data`.

**[MEDIUM] Order-counter uniqueness not guaranteed under concurrency** —
`services.py:310-336`. `_lock_country_counter` takes `SELECT … FOR UPDATE` on the
Barakah Country row, but the max-counter read that follows (`frappe.get_all`,
:324) is a plain consistent read; under InnoDB REPEATABLE-READ (confirmed on this
bench) a waiter's snapshot predates the winner's commit, so two overlapping
`create_*_order` sends for the same country can both compute `max+1` identically.
DOCUMENTATION.md overstates the guarantee. Fix: make the max read a locking read
(`.for_update()`) or keep the counter on the locked Barakah Country row.

**[MEDIUM] Manual Set Counter doesn't propagate to the open supplier task** —
`services.py:470-499`. `set_order_counter` writes only `counter`/`order_name` via
`db.set_value` (no hooks), while the supplier's task embeds the old number in
`subject` and `gc_payload_json` (`workflow_content.py:40,46`), so the correction
isn't visible in the hub until an unrelated resend/save. Fix: refresh the open
task's subject/`gc_payload_json` in `set_order_counter` (reuse `_sync_task_payload`).

**[LOW]** PEP 758 `except UnidentifiedImageError, OSError:` (`services.py:115`,
declared floor >=3.11) — see Cross-cutting. **[LOW]** Donor-controlled
`text_for_shield` reaches an inline `<script>` via `frappe.as_json` (which
doesn't escape `</script>`) in `templates/well_shield.html:77`; no Desk XSS
(`.html` private files force-download) but the file travels to suppliers/hub —
`.replace("</","<\\/")`. **[LOW]** `get_order_form_dropdown_options` (guest,
`api.py:54`) is the only guest endpoint with no `apply_rate_limit` (response is
bounded + non-sensitive: country/company labels + captcha key). **[LOW]** Renumber
leaves no audit trail (`update_modified=False`, no comment/Version). **[LOW]**
Private-symbol imports survived the June E11 sweep in `services.py:15,27`
(`_is_truthy`, `_as_automation_user`). **[INFO]** Set Counter action shown to all
form users but server-enforced to SM/Barakah Manager (UX-only).

*Invariants HELD:* Overdue non-terminal/editable; cancelled ToDos grant no
visibility; `portal_email_can_access_task` reused not re-implemented; retargeting
explicit + tested; Barakah Viewer DocPerm is read/report-only via skip-if-unchanged
install_utils, desk_access + System-User repair correct, no Task perm; draft
exclusion NULL-safe; patches no longer re-run `ensure_setup`; hub shape 400
unchanged.

**mopi_app** — no security regressions; the June permission model held.

**[LOW]** aa9f497's write restriction (assigned-only for regular MoPi Users) is
in code/tests but not `DOCUMENTATION.md:68-71` (bench rule: same-change doc
update). **[LOW]** HOW_TO §2 doesn't warn operators that *all* Task Campaign
attachments (not just inline images) become world-readable under `/files/`.
**[LOW]** 1b3d2be sets the `make_attachments_public` flag but no patch migrates
pre-existing `/private/files/...` campaign images → old campaigns stay broken in
the hub. **[LOW]** The delete-deadlock fix (831b71a) covers only the campaign↔task
pair; `MoPi Training Module Participant.self_study_task` → Task is still a mutual
delete block (possibly intentional — training-history deletion is destructive —
but confirm + document). **[INFO]** No patch for dropped `Training Type.is_active`
(correctly — was write-only, orphan column harmless); 1b3d2be removed
`test_file_uploads.py` without replacement (see Test gaps).

*Invariants HELD:* ptype-aware `has_task_permission` matches the agreed June D1
model exactly (writes narrowed, nothing widened), shared SQL builders reused;
`make_attachments_public` set only on MoPi Task Campaign (certificates + portal
uploads stay private); `on_trash` link-guard ordering safe, no permission bypass;
guest short-circuits log-free + rate-limited; contract shapes `[]`/400 pinned;
list-view search sections match JSON.

*Done well (both):* reminder login URLs per-recipient (June HIGH token-leak class
closed, strong regression test decoding every token); 1b3d2be is a model
correction (reverts the fragile `upload_file` override for the native flag);
counter work well-reasoned + documented; shared substrate consumed as intended.

<!-- SECTION: good_npo_demo -->
### good_npo + good_demo — delta audits

**good_npo**

**[HIGH] Deleting `Good NPO Guide` orphaned the Good NPO sidebar for every
non-Administrator user** — commit c544ee8. It removed the module's *only*
DocType, and Frappe derives a user's `allow_modules` exclusively from DocTypes
they can read (`frappe/utils/user.py:170-174`). **Verified against the live dev
DB:** `tabDocType` has **zero** rows with `module='Good NPO'`, while the
`Good NPO` Workspace Sidebar row (and the Workspace) is gated on
`module='Good NPO'`, `standard=1`. So the module can never enter any non-admin's
allowed set → the sidebar is dropped from boot (`frappe/boot.py`) for Non Profit
Manager / Good NPO User / demo users, and the Workspace raises `PermissionError`.
Because good_demo's boot filter reduces demo users to exactly this sidebar
(`good_demo/boot.py:33-37`), **demo users get an empty left nav**. This is the
exact gotcha the bench AGENTS.md Workspace-Sidebar section warns about; it went
unnoticed because Administrator bypasses the gate and no test asserts a non-admin
boot. Fix: set `"module": "Non Profit"` on the sidebar + workspace fixtures (with
a resync patch), or reintroduce a minimal readable module-anchor DocType.

**[MEDIUM] Major Gift / Donor Interaction grants freeze non_profit's doctype-JSON
permissions (Custom DocPerm shadowing)** — `good_npo/setup.py:214-258` (4947083).
The grant path snapshot-copies the doctype-JSON DocPerms into Custom DocPerm rows,
after which Frappe ignores the JSON permissions for those doctypes
(`frappe/permissions.py:682-686`). For these two brand-new, actively-evolving
non_profit doctypes, a later JSON permission change (e.g. the documented "Major
Gifts Officer" role) silently never applies on installed sites — the exact bench
gotcha on record. The grant itself is correctly skip-if-unchanged idempotent. Fix:
document the freeze and add future role perms via an ensure-function / Custom
DocPerm write (or in the fork's JSON before first install).

**[LOW]** New doctypes missing from the route-helper set `GOOD_NPO_DOCTYPES`
(`public/js/good_npo_desk.js:21-33`) — awesomebar nav to Major Gift / Donor
Interaction won't restore the sidebar (no hijack risk). **[LOW]** Stale
`Good NPO Guide` references in DOCUMENTATION.md:32,94 + HOW_TO.md:249 (fix with
the HIGH). **[INFO]** 7c9deda facade split verified complete (AST-diff: only dead
`_link_member_contact_to_record` + `_persist_membership_invoice_values` dropped;
all string call sites + patch targets resolve; no scheduler entries).

*Invariants HELD:* guest endpoints never mutate existing Member/Donor/Address
(divergent submissions → staff Comment); membership confirmation enqueued +
throttled 3/h; branding/footer ownership-guarded; `setup.py:404` `db.commit`
behind `commit` param, hook-path caller passes `commit=False`.

**good_demo** (containment is the point)

**[HIGH] Demo-user-created Major Gifts / Donor Interactions are never
demo-marked → reset can never claim them** — commit dd0416b. It registered the
`before_insert` marker hook for both doctypes (`hooks.py:50-51`) and granted demo
roles create, but the marker function's allowlist was **never extended**:
`mark_demo_created_record` early-returns because `DEMO_CREATABLE_DOCTYPES`
(`demo_records.py:9-16`) omits Major Gift / Donor Interaction. **Verified** (hook
registered, allowlist gap, guard at `:20`). Demo users can create both (privacy
fallthrough), the record inserts unmarked, `delete_demo_records` claims only
`good_demo_seed=1` rows, and `force=True` deletion of the marked parent skips link
checks — so unmarked interactions/gifts survive every daily reset, accumulate
indefinitely, and dangle once their seeded donor is deleted. Direct violation of
the app's core containment rule. (Seeded gifts *are* marked — the gap is
demo-user-created records only.) Fix: add both to `DEMO_CREATABLE_DOCTYPES`, and
consolidate the now-triplicate allowlists (`setup.py:47-56` was updated;
`privacy.py:11-35` and `demo_records.py:9-16` weren't — the F7 duplication class).

**[MEDIUM] next-action side channel mints unmarked, unresettable Tasks + ToDos**
— demo users have write on Major Gift / Donor Interaction (4947083) and seeded
records are demo-visible, so `non_profit…next_actions.set_next_action`
(whitelisted, write-gated only) is callable by demo users; it inserts a Task with
`ignore_permissions=True` + a ToDo via assignment. Task/ToDo are in no marker
hook or reset catalog, and assignment mail can target the @example.org officers.
Reset then orphans them when it force-deletes the parent. Fix: add Task to the
marker hook + reset catalog (delete before Major Gift), or deny demo users this
endpoint.

**[MEDIUM] migrate-time re-seed crashes on a drifted workflow stage** —
`after_migrate` runs the full seed **without** a prior reset (`setup.py:146-164`);
`_ensure_major_gift` reuses the existing marked gift and calls the non_profit
`advance_major_gift_to_stage` (the STAGE_WALK crash above), so if an admin legally
moved a seeded gift between resets, the first walk step is an illegal backward
transition and frappe throws `WorkflowPermissionError`, **aborting `bench
migrate`**. The nightly reset path is safe (deletes first). Fix: reset the stored
stage via `db.set_value` before walking, or delete+recreate the seeded gift.

**[LOW]** Stale `Good Demo Guide` reference in DOCUMENTATION.md:186 (nothing
user-visible depended on it — the Good Demo sidebar is anchored by the
System-Manager-only `Good Demo Signup`, so good_demo did **not** hit good_npo's
HIGH). **[LOW]** Neither app records a "List-View Search" AGENTS.md section;
`Good Demo Signup` is serial-named with search/filter fields but **no
`title_field`** (lists show the serial). **[INFO]** As of the audit, both repos'
sidebar fixtures were modified in the working tree by concurrent WIP
(Home→Dashboard, valid icons, a Spacer) — check `git status` before committing so
it isn't mixed in.

*Invariants HELD:* reset deletes only `good_demo_seed=1`, skips markerless
doctypes, cancels submitted docs; never-claims regression tests intact; new
seeds marker-disciplined (`_ensure_major_gift`/`_ensure_donor_interaction` set +
filter by marker; reset order covers Donor Interaction before Donation, Major
Gift after; `RESETTABLE_DOCTYPES` extended); idempotent keyed re-seed (except the
stage-walk crash); 8950b4e split contract holds (facade patch targets, long-queue
daily reset, `window.goodDemoBoot`). Persistent gift-officer users deliberately
unmarked (links must survive reset), no password, welcome mail suppressed,
login-link guard refuses non-demo accounts. RFM/segment rows self-heal via the
daily analytics rebuild — no marker needed.

*Done well (both):* Guide removals ship proper `delete_doc(force=True)` patches
(both ran per Patch Log); 7c9deda is a model facade split; the Payrexx
explicit-config rewrite kills the Sandbox-first hazard; seed catalog spans every
RFM bin + one gift per stage with the closed-amount rollup exercised via a real
Donation.

<!-- SECTION: small -->
### payrexx_integration + workflow_visualizer + good_help — delta audits

**payrexx_integration** — **clean.** The pay-link gateway binding (c1b6013) is
sound end-to-end: `payrexx_pay_url` signs `si|gateway_name` and `pay_invoice`
recomputes the HMAC over the signed pair, so a swapped `gateway_name` fails
verification and 403s; legacy gateway-less tokens still verify and resolve
settings server-side. Webhook binds to the IR's own stored gateway;
`payment_success`/reconcile derive credentials from the IR. Tests added. Raw-body
HMAC `compare_digest`, Password fieldtypes + `get_password`, same-origin redirect
guard, single least-privilege automation user — all intact. Only INFO nits
(unescaped `|` HMAC join; a legacy caller-gateway fallback that ERPNext's
always-logged `payment_gateway` renders empty).

**workflow_visualizer**:
- **[MEDIUM] `patches.txt` entry ends in `.execute`** —
  `workflow_visualizer.patches.v0_0.add_workflow_visible_on_doctype_field.execute`.
  The patch handler builds `patch = f"{module}.execute"` (patch_handler.py:167)
  then `get_attr` imports everything before the last dot as a module →
  `ModuleNotFoundError` on the doubled `.execute.execute`. **Verified**:
  `get_attr(...execute.execute)` raises; the single form resolves. Every other
  app writes bare module paths. Fresh installs survive only because
  `install_app → set_all_patches_as_completed` stamps the raw line into Patch Log
  **without running it** (confirmed: the entry shipped in the app's first commit,
  so it has never executed anywhere; the field exists only via `after_install`/
  `after_migrate`). It detonates on `bench run-patch`, `run_single(force=True)`,
  or any migrating site whose Patch Log lacks the exact row. Fix: drop the
  trailing `.execute` (the rename runs the idempotent `create_custom_fields`
  once, safely).
- **[LOW]** The J2 "uniform 403" isn't uniform on the wire — missing docs
  serialize via `_server_messages`, forbidden docs via `_error_message`, so an
  authenticated user can still distinguish existing from missing docnames
  (`api.py:14-20`). **[LOW]** DOCUMENTATION.md API-contract section not updated
  for the no-oracle guard. **[INFO]** No `SEMGREP_OVERRIDES.md` (zero
  annotations, so vacuously fine; every other app ships one).

**good_help**:
- **[LOW] Private tier silently inert on wiki builds without
  `Wiki Document.is_private`** — `api.py:131-159`. ad642b0's compat shim uses
  clean meta feature-detection, but when the field is absent good_help maps no
  replacement (wiki v3 uses Wiki Space roles), so `row.get("is_private")` is
  always falsy → any published article visible to all desk users, and the only
  private-tier test self-skips in exactly that config. Not exploitable on the
  pinned wiki (still ships the field). Fix: enforce the space-role equivalent or
  fail sync loudly when the field is missing. **[LOW]** DOCUMENTATION.md private-
  tier statement not updated for that conditional.
- e10cb8c batching verified: per-user permission predicate byte-for-byte
  preserved, N+1 genuinely gone (2 queries). Desktop-icon ensure idempotent.

<!-- SECTION: ilanga -->
### ilanga_app — out of scope (PoC)

Not audited for remediation. One `frappe-security-file-traversal` annotation in
`help_articles.py:128` is undocumented; counted for completeness only.

---

## Cross-cutting findings

### C1. PEP 758 unparenthesized `except` vs declared Python floor

`except A, B:` (no parentheses, no `as`) is valid only on Python ≥3.14 (PEP 758)
and is a `SyntaxError` on 3.11–3.13. The estate is split and internally
inconsistent — a full source scan:

| App | Site(s) | `requires-python` | Verdict |
|---|---|---|---|
| **good_connector** | `setup.py:136,142` | **>=3.11** | **BUG** — `after_migrate` import path; migrate/install crashes on <3.14 |
| **barakah_app** | `services.py:115` | **>=3.11** | **BUG** — declared floor violated |
| non_profit | `www/donate.py:87` | *(none)* | Publicly installable fork; SyntaxError on <3.14 |
| good_event | `services/*.py` ×2 | >=3.14 | Internally consistent (honest floor) |
| good_newsletter | `services/*.py` ×5 | >=3.14 | Internally consistent |

This bench + CI run 3.14, so nothing catches it locally. Fix (either, applied
consistently): parenthesize every occurrence (restores 3.11 compat — zero risk,
recommended), **or** bump `requires-python` to `>=3.14` in the seven apps that
still say 3.11 (honest, matches the uniform `target-version = "py314"`). The
two BUG rows should be fixed regardless.

### C2. Bench `AGENTS.md` accuracy

- **good_analytics missing entirely** from the app table and dependency graph.
  Correct row: domain "Apteco-style fundraising analytics (RFM, segments,
  dashboards, newsletter audience provider)", depends on `non_profit`,
  `good_connector`, `good_help`, branch `version-16`; graph node under
  `non_profit`. It's documented nowhere (also absent from its own README/AGENTS).
- **non_profit labeled "(standalone)"** (table + graph) but `hooks.py:10` has
  `required_apps = ["erpnext"]`. **Verified.** All 12 other rows match their
  hooks.py. Fix: change to `erpnext`, hang non_profit off erpnext in the graph.
- **Stale per-event email override** (line ~162): `Good Event.disabled_email_flows`
  was replaced by per-flow `disable_email_*` checkboxes (patch +
  `services/email_flows.py`). Reword.
- Provider list missing three newer good_event hooks (organization_search /
  organization_membership / translation); sidebar-hook app list missing
  good_newsletter + good_analytics. (LOW.)

### C3. SEMGREP_OVERRIDES.md drift (bench rule: every `nosemgrep` documented)

| App | Verdict |
|---|---|
| **miki_app** | **7 undocumented** — `receivables.py` `frappe-ssti` ×6 (176,232,312,313,341,344) + `dev_cleanup.py:68` manual-commit |
| **good_event** | 2 undocumented (`pdf_branding.py:68`, `public_pages.py:849`) + 3 stale (renamed/moved files) |
| **good_connector** | 2 undocumented (`browser_harness.py:210,226`) + 1 stale (`api/auth.py` no longer annotated) |
| good_newsletter | 1 attribution gap (`render_blocks` not named) |
| good_demo | 1 stale pointer (checkout `_as_automation_user` now imported) |
| non_profit | 1 undocumented (`scripts/donation_slip_smoke.py:65`) |
| barakah, good_analytics, good_help, good_npo, mopi, payrexx | in sync |
| workflow_visualizer | no file, but zero annotations (vacuously fine) |

### C4. New cross-app duplication (regressions vs the June dedup)

- **[MEDIUM] good_newsletter `ensure_email_group_access` (`setup.py:48-74`)
  rewrites Custom DocPerm on every migrate** — its own comment says "re-applied
  on every migrate" — reintroducing exactly the antipattern
  `good_connector.install_utils.ensure_doctype_permission` (skip-if-unchanged)
  was built to remove in June. **Verified.** Also `ensure_newsletter_manager_role`
  (`setup.py:129-153`) is a near-twin of `install_utils.ensure_desk_role`. Fix:
  replace both with the install_utils helpers.
- **[MEDIUM] Desktop-icon setup cloned across ≥7 apps** — verbatim
  `good_analytics/setup.py:146-191` == `good_newsletter/setup.py:156-201`, both
  copies of `good_npo/setup.py:1178-1237`; identical `_clear_desktop_icon_cache`
  in ≥4 apps; older `ensure_desktop_icon` clones in good_help/good_demo/barakah.
  Fix: one `install_utils.ensure_desktop_icon(label, link, logo_url, app,
  stale_labels=())`.
- **[LOW]** `good_analytics/permission.py` == `good_newsletter/permission.py`
  (23-line role-gated `has_app_permission`, diff = names) — a
  `has_role_gated_app_permission(roles)` helper would serve the next app.

*Clean (June dedup held):* no resurrected `esc()`/`retry_on_deadlock`/
`merge_pdf_bytes`/HMAC-signer/`set_user` clones; the two donation-aggregation
stacks (good_npo permission-aware SUM vs good_analytics gate-then-aggregate) are
deliberately different, both shared-substrate-based; newsletter's per-recipient
send loop shares no code with task_delivery (documented design rule).

### C5. Clean areas (verified)

- **Tooling uniform across all 14 apps** — ruff, `.prettierrc`, pre-commit hook
  revs, `.editorconfig` byte-identical; every app ships `ci.yml` + `linter.yml`
  (non_profit has `ci.yml` only). June drift fully closed.
- **List-view search convention** — the six doctypes with no title/search field
  are all documented deliberate skips or `autoname:"prompt"` masters (Chapter,
  Volunteer Type — sweep false positives). Nothing unsearchable-and-undocumented.
- **Workspace/sidebar fixtures** — new good_analytics/good_newsletter/good_npo
  sidebars all carry `app`+`module`+`standard:1`, Section-Break children set
  `"child":1`, every named Lucide icon resolves in the sprite.
- **Guest-endpoint inventory** (43 across the estate) — all carry documented
  JWT/API-password/HMAC/captcha auth or are intentionally public reads.
- Controllers on every DocType; all ~230 whitelisted functions type-hinted;
  patches.txt resolves everywhere except workflow_visualizer (C-small).

---

## Roadmap

**Fix immediately (High):**
1. good_npo: reassign the sidebar/workspace to `module: "Non Profit"` (or add a
   readable module anchor) so non-admin users get their nav back. **Live breakage.**
2. good_demo: add Major Gift + Donor Interaction to `DEMO_CREATABLE_DOCTYPES`
   (containment) — and Task to the marker hook + reset catalog.
3. good_event: escape `redirect_to` + `booking` (`| e`) and reject `"<>` in
   `_safe_relative_url`.

**Fix soon (the Mediums), grouped by theme:**
- *Portal write-path guards:* barakah local StoreData closed-task 409; miki
  StoreData workflow-state gate; good_connector mopi file-mutation on closed
  tasks.
- *Feature silently broken:* good_connector `portal_user_language` (resolve
  Customer from email); non_profit major-gift rollups on the PE flow (register
  the reconciliation job); non_profit Workflow force-save every migrate.
- *Permission/escaping:* good_analytics `has_permission("Donor","read")` on the
  two email paths; good_newsletter escape audience title/description.
- *Data integrity:* non_profit STAGE_WALK (start at current stage); barakah
  order-counter locking read + manual-renumber task propagation; miki shared-
  contact mutation guard + cross-recipient login-link fallback.

**Quick wins (low-risk, cheap):**
1. C1: parenthesize the two `except` BUG sites (good_connector, barakah); decide
   the floor policy for the rest (parenthesize all, or bump `requires-python` to
   3.14 in the seven apps that still say 3.11).
2. workflow_visualizer: drop the trailing `.execute` in patches.txt.
3. C2: add good_analytics to bench AGENTS.md; fix non_profit "(standalone)";
   reword the stale per-event email-override line.
4. C3: resync the SEMGREP_OVERRIDES.md drift (miki first — 7 undocumented).
5. C4: extract `install_utils.ensure_desktop_icon`; swap good_newsletter's
   `ensure_email_group_access`/role to the install_utils helpers.
6. Add the regression tests that would have caught the two Highs: a non-admin
   boot-sidebar assertion (good_npo) and a demo-user-created-record marker test
   for the two new doctypes (good_demo).

---

*Method note: 1 mechanical sweep + 10 read-only sub-agents (2 full, 7 delta, 1
cross-app), all citing file:line evidence read from the code. Every High and the
load-bearing Mediums were independently re-verified against the code and, where
relevant, live dev-site data before landing here — the good_npo sidebar breakage
against `tabDocType`/`tabWorkspace Sidebar` (zero doctypes in module `Good NPO`),
the good_demo marker gap against the registered hook vs the allowlist, both
good_event XSS against the actual `_safe_relative_url` bypass, the PEP 758 estate
scan and `except`-vs-floor matrix, the workflow_visualizer `.execute` double-append
(via `frappe.get_attr`), good_connector `portal_user_language` (ngo-claim vs live
Customer naming), good_analytics email-permission asymmetry, good_newsletter
autoescape-off, miki StoreData gate + login-link fallback, barakah closed-task
StoreData, non_profit STAGE_WALK, the newsletter per-migrate DocPerm writes, and
non_profit's `required_apps` vs the "standalone" label. Nothing was executed that
mutated the site; DB access was read-only SELECTs.*
