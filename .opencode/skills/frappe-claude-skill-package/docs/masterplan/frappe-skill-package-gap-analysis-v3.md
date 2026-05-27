# Frappe Skill Package — Gap Analysis v3.0

> **Doel**: Identificeer alle resterende gaps na v2.0 (53 skills)
> **Datum**: 2026-03-20
> **Huidige dekking**: ~85% van Frappe Framework surface area
> **Doeldekking v3.0**: ~95%

---

## Methodologie

Na voltooiing van v2.0 (53 skills) is een frisse gap analysis uitgevoerd tegen de volledige Frappe Framework documentatie (docs.frappe.io). Elke capability is geclassificeerd als:

- **MISSING** — Niet in enige skill, moet nieuw gecreëerd
- **PARTIAL** — Wel geraakt maar niet diep genoeg, bestaande skill uitbreiden
- **COVERED** — Adequaat gedekt, geen actie

---

## 1. Nieuwe Skills Nodig (MISSING)

### P0 — Hoge impact, frequent nodig

| # | Voorgestelde Skill | Scope | Rationale |
|---|-------------------|-------|-----------|
| 1 | `frappe-core-translation` | Translation/i18n systeem: `_()` en `__()`, CSV translation files, `bench get-untranslated`, `bench update-translations`, custom app vertalingen, string extractie regels, context parameter, RTL support | **HOOGSTE GAP**: Ieder meertalig project heeft dit nodig. Claude kent de string format regels niet (geen f-strings, geen concatenatie). |
| 2 | `frappe-core-utils` | Geconsolideerde referentie voor frappe.utils.*: 40+ Python utility functies (money_in_words, comma_and, pretty_date, format_duration, validate_email, mask_string, etc.) + frappe.utils JS utilities | Claude heruitvindt constant functies die al bestaan in frappe.utils. |

### P1 — Medium impact

| # | Voorgestelde Skill | Scope | Rationale |
|---|-------------------|-------|-----------|
| 3 | `frappe-syntax-print` | Print systeem: Print Format Builder, Jinja Print Formats, Print Designer [v15+], Letter Head, get_pdf(), Report Print Formats ({%= %}), page breaks, styling | Geen dedicated print skill ondanks dat het in elk project voorkomt |
| 4 | `frappe-syntax-query-builder` | Dedicated frappe.qb referentie: from_(), DocType(), Field(), joins, CustomFunction, ConstantColumn, ImportMapper, cross-DB compatibility, .run() vs .walk() | Te groot voor sub-sectie in database skill, eigen paradigma |
| 5 | `frappe-impl-workspace` | Workspace/Desk customization: Workspace DocType, shortcuts, charts, number cards, links, custom workspace creation, JSON format | Iedere app levert een workspace, geen guidance |

### P2 — Lage impact, specialistisch

| # | Voorgestelde Skill | Scope | Rationale |
|---|-------------------|-------|-----------|
| 6 | `frappe-core-logging` | Structured logging: frappe.logger(), log levels, log rotation, cleanup, monitoring integration, production logging patterns | Basis staat in agent-debugger maar productie patterns ontbreken |
| 7 | `frappe-core-search` | Full-text search: FullTextSearch API, global_search, search hooks, Awesomebar customization, search_fields | Volledig afwezig |

---

## 2. Bestaande Skills Uitbreiden (PARTIAL)

| # | Skill | Wat Ontbreekt | Actie |
|---|-------|--------------|-------|
| 1 | `frappe-core-database` | Query Builder (frappe.qb) te oppervlakkig | Als P1-4 gemaakt wordt: cross-ref toevoegen. Anders: expand references/query-patterns.md |
| 2 | `frappe-impl-ui-components` | Controls API (make_control standalone), dropdown_button, before_render, Tree View API | Voeg references/controls-api.md en references/tree-view.md toe |
| 3 | `frappe-impl-website` | Portal Generators (auto web pages from DocTypes), Blog systeem | Voeg references/generators.md toe |
| 4 | `frappe-impl-jinja` | Print Designer [v15+] decision tree vs Jinja | Voeg sectie toe in SKILL.md of references/ |
| 5 | `frappe-core-notifications` | Email Account setup, Email Queue, email-to-document linking, bulk email | Voeg references/email-system.md toe |
| 6 | `frappe-ops-app-lifecycle` | Module Def configuratie, Workspace JSON shipping | Voeg secties toe |
| 7 | `frappe-syntax-controllers` | Document API completeness (20+ methods verspreid over meerdere skills) | Voeg references/document-api-complete.md toe |
| 8 | `frappe-ops-bench` | Custom bench commands (via `commands` hook) | Voeg sectie toe |
| 9 | `frappe-syntax-hooks` | Router API (frappe.get_route, route events), Request lifecycle | Voeg references/request-lifecycle.md toe |
| 10 | `frappe-agent-debugger` | Frappe-specific debugging setup (VS Code DAP, bench console advanced) | Expand references/checklists.md |
| 11 | `frappe-ops-upgrades` | Frappe Packages (deployable customization bundles) | Voeg sectie toe |
| 12 | `frappe-syntax-doctypes` | Data Masking [v16+] verdieping, frappe.types module reference | Voeg references/data-masking.md en references/type-stubs.md toe |

---

## 3. Bewust Niet Gedekt (Out of Scope)

| Feature | Reden |
|---------|-------|
| Frappe HR / HRMS | Apart app, niet core framework |
| Frappe LMS | Apart app |
| Frappe Insights | Apart app |
| Frappe CRM | Apart app |
| Energy Points / Gamification | Niche feature, weinig development patterns |
| Discussions (portal) | Simpel DocType, weinig code patterns |
| Form Tours | Niche UI feature |
| Scanner API | Niche, alleen voor POS/warehouse |

---

## 4. V3.0 Scope Samenvatting

| Categorie | Nieuwe Skills | Uitbreidingen |
|-----------|:------------:|:-------------:|
| Nieuwe skills | 7 | — |
| Bestaande uitbreidingen | — | 12 |
| **Totaal na v3.0** | **60 skills** | **+ 12 enhanced** |

### Verwachte dekking na v3.0: ~95%

| Versie | Skills | Dekking |
|--------|:------:|:-------:|
| v1.2 | 28 | ~16% |
| v2.0 | 53 | ~85% |
| **v3.0** | **60** | **~95%** |

---

## 5. V3.0 Fasen (Voorgesteld)

| Fase | Beschrijving |
|------|-------------|
| V3.1 | Research: Frappe docs deep-dive voor 7 nieuwe skills |
| V3.2 | Nieuwe skills creëren (P0 eerst: translation, utils) |
| V3.3 | 12 bestaande skills uitbreiden met extra references |
| V3.4 | Validatie + INDEX.md + README.md update |
| V3.5 | Release v3.0.0 |

### V3 Prioriteit Volgorde

```
P0 (sessie 1): frappe-core-translation + frappe-core-utils
P1 (sessie 2): frappe-syntax-print + frappe-syntax-query-builder + frappe-impl-workspace
P2 (sessie 3): frappe-core-logging + frappe-core-search
Uitbreidingen (sessie 3-4): 12 bestaande skills verrijken
```
