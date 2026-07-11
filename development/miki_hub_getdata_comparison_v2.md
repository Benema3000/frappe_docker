# Miki Declaration `GetData` — v2 (archive-structure + Frappe field names)

Comparison after the 2026-04-20 wire-format realignment. The goal:
**archive structure** (list, `internal_id`, string values, string visibility,
single `name` display field, no `business` duplicate) **with Frappe field
names** (so the hub's existing bindings like `Accounts[$id]['kita_visible']`
and `kita_slots_declared` still resolve).

## Accounts payload — side by side

### Archive (Dataverse-era, from flow CSV)

```json
{
  "internal_id": "0ef44ca4-1e13-f111-8342-7ced8d42beca",
  "name": "Kinderkrippe Albisrieden: ",
  "kitaVisibility": "visible",
  "sebVisibility": "visible",
  "tfoVisibility": "",
  "betreuungsplaetzeKITA": "66.00",
  "betreuungsplaetzeSEB": "0.00",
  "betreuungsstundenTFO": "0"
}
```

### Miki (current, live from `110s35dtjh`)

```json
{
  "internal_id": "1109g96tdi",
  "name": "Test",
  "kita_visible": "visible",
  "seb_visible": "visible",
  "tfo_visible": "visible",
  "kita_slots_declared": "1.00",
  "seb_slots_declared": "2.00",
  "tfo_hours_declared": "3"
}
```

### What matches, what's intentionally different

| Property | Archive | Miki | Same? |
|---|---|---|---|
| Container | `list` of dicts | `list` of dicts | ✅ |
| Item count | N (one per sub-customer) | N (one per sub-customer) | ✅ |
| Identity key | `internal_id` (lowercase) | `internal_id` | ✅ |
| Display label | single `name` (e.g. `"Krippe Albisrieden: "`) | single `name` (`business_name`) | ✅ (format) |
| Visibility wire type | `""` / `"visible"` strings | `""` / `"visible"` strings | ✅ |
| Slot values | strings `"66.00"`, 2 decimals | strings `"1.00"`, 2 decimals | ✅ |
| TFO hours | integer string `"0"` | integer string `"3"` | ✅ |
| Visibility field names | `kitaVisibility` / `sebVisibility` / `tfoVisibility` | `kita_visible` / `seb_visible` / `tfo_visible` | **Renamed (Frappe)** — intentional |
| Slot field names | `betreuungsplaetzeKITA` / `*SEB` / `betreuungsstundenTFO` | `kita_slots_declared` / `seb_slots_declared` / `tfo_hours_declared` | **Renamed (Frappe)** — intentional |
| Redundant Customer link | — | dropped | ✅ |

The only deliberate deltas are **field names** — Frappe-style per the hub
schema the team now uses. Structure, types, ordering, identity key, and
display-label semantics are 1:1 with the archive.

## Top-level declaration fields — side by side

### Archive (sample keys, from real flow)

```json
{
  "name": "",
  "cr2da_betriebnamedeklaration": "Krippeverein Albisrieden",
  "cr2da_betriebstrassedeklaration": "Langgrütstrasse 134",
  "cr2da_betriebplzdeklaration": "8047",
  "cr2da_betriebortdeklaration": "Zürich",
  "cr2da_betriebtelefondeklaration": "+41 44 406 87 87",
  "cr2da_betriebemaildeklaration": "info@kka.ch",
  "cr2da_cheuiddeklaration": "",
  "cr2da_kontaktpersonvornamedeklaration": "Manuela",
  "cr2da_kontaktpersonnachnamedeklaration": "Surenmann",
  "cr2da_kontaktpersonemaildeklaration": "manuela.surenmann@kka.ch",
  "cr2da_rechnungsadresseverwenden": null,
  "cr2da_rechnungsadressenamedeklaration": "Krippeverein Albisrieden",
  "cr2da_begruendungabweichung": "",
  "gvme_kommentartragerschaft": "",
  "gv_bestaetigungvollstaendigkeit": true,
  "kontaktpersonWirdAngepasst": false,
  "titelAbgabe": "",
  "Accounts": [...]
}
```

### Miki (current, live)

```json
{
  "id": "110s35dtjh",
  "name": "D-000057",
  "processDefinitionName": "deklaration",
  "status": "Requested",
  "language": "en",

  "organization_comment": null,
  "deviation_justification": null,
  "completeness_confirmed": 0,

  "business_uid_declared": "",
  "business_name_declared": "Test",
  "business_street_declared": null,
  "business_postal_code_declared": null,
  "business_city_declared": null,
  "business_country_declared": null,
  "business_pob_declared": null,
  "business_phone_declared": null,
  "business_email_declared": null,

  "contact_will_be_updated": 0,
  "contact_first_name_declared": null,
  "contact_last_name_declared": null,
  "contact_email_declared": null,
  "contact_phone_declared": null,
  "contact_role_declared": null,
  "contact_salutation_declared": null,
  "contact_language_declared": null,

  "billing_use_separate_declared": 0,
  "billing_name_declared": null,
  "billing_street_declared": null,
  "billing_pob_declared": null,
  "billing_postal_code_declared": null,
  "billing_city_declared": null,
  "billing_country_declared": null,
  "billing_email_declared": null,

  "Accounts": [...]
}
```

### Comparison

| Property | Archive | Miki | Same? |
|---|---|---|---|
| Wrapper | — (flat) | — (flat) | ✅ |
| Field naming | Dataverse (`cr2da_*` / `gvme_*`) | Frappe (`*_declared` / `organization_comment`) | **Renamed** (team decision — hub schema expects Frappe names) |
| Coverage | business + contact + billing + misc | business + contact + billing + misc | ✅ |
| Envelope | n/a | `id`, `name`, `processDefinitionName`, `status`, `language` | ⚠️ extra keys; harmless for hub |

## StoreData contract

`_apply_account_updates` reads each account payload's identity in this order:
`internal_id` → `id` → `name`. So **either** archive-style (`internal_id`) **or**
legacy callers sending `id`/`name` continue to work.

Slot/hour values are coerced via `float()`, so string payloads (`"77.00"`) and
numeric payloads (`77.0`) both land correctly.

## Code pointers

- `miki_app/miki_app/declaration_service.py::get_declaration_data` — serializer
- `miki_app/miki_app/declaration_service.py::_apply_account_updates` — key lookup
- Archive source: `archived/Archive02/flow-3445bddf-...(1).csv`, field `Select_DeklarationsJSON - output`

## Test coverage

- `miki_app/tests/test_miki_app.py::TestHubSerialization`
  - `test_get_declaration_data_shape` — asserts list form, `internal_id` present, visibility strings, slot strings
  - `test_accounts_matched_by_row_name_not_row_order` — submits reversed list, verifies row matched by `internal_id`

All 45 miki_app tests pass.
