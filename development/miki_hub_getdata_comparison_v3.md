# Miki Declaration `GetData` — v3 (new hub data model)

Third iteration. Wire format now fully aligned with the **current** hub
screen-config bindings (Frappe field names, strings for visibility and
slot/hour values, list Accounts keyed by `id`).

Generated 2026-04-20, declaration `110s35dtjh`.

## Hub contract (new data model)

### Screen config
```json
[
  {"type": "control", "binding": "organization_comment"},
  {"type": "control", "binding": "deviation_justification"},
  {"type": "control", "binding": "completeness_confirmed"},
  {"type": "ComponentList", "binding": "Accounts", "children": [
      {"type": "control", "binding": "Accounts[$id]['business_name']"},
      {"type": "control", "binding": "Accounts[$id]['kita_slots_declared']"},
      {"type": "control", "binding": "Accounts[$id]['seb_slots_declared']"},
      {"type": "control", "binding": "Accounts[$id]['tfo_hours_declared']"}
  ]}
]
```

### Live miki response — relevant slice

```json
{
  "id": "110s35dtjh",
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

  "Accounts": [
    {
      "id": "1109g96tdi",
      "business_name": "Test",
      "kita_visible": "visible",
      "seb_visible": "visible",
      "tfo_visible": "visible",
      "kita_slots_declared": "1.00",
      "seb_slots_declared": "2.00",
      "tfo_hours_declared": "3"
    }
  ]
}
```

## Binding → response alignment

| Hub binding | Response path | Present? | Value example |
|---|---|---|---|
| `organization_comment` | top-level | ✅ | `null` |
| `deviation_justification` | top-level | ✅ | `null` |
| `completeness_confirmed` | top-level | ✅ | `0` (truthy-false, matches `!$completeness_confirmed`) |
| `Accounts` | top-level | ✅ | `list` of 1 |
| `Accounts[$id]['business_name']` | per-item | ✅ | `"Test"` |
| `Accounts[$id]['kita_slots_declared']` | per-item | ✅ | `"1.00"` |
| `Accounts[$id]['seb_slots_declared']` | per-item | ✅ | `"2.00"` |
| `Accounts[$id]['tfo_hours_declared']` | per-item | ✅ | `"3"` |
| `$Accounts[$id]['kita_visible'] == 'visible'` (visibilityCondition, if present) | per-item | ✅ | `"visible"` / `""` |

**Every binding resolves to a value.** Nothing in the response contradicts the
model.

## Accounts item — final wire shape

```json
{
  "id":                   "<Declaration Item row name>",
  "business_name":        "<sub-customer display name>",
  "kita_visible":         "visible" | "",
  "seb_visible":          "visible" | "",
  "tfo_visible":          "visible" | "",
  "kita_slots_declared":  "XX.XX",
  "seb_slots_declared":   "XX.XX",
  "tfo_hours_declared":   "XX"
}
```

- Identity: `id`
- Visibility: string (`"visible"` / `""`)
- Slots: 2-decimal string
- TFO hours: integer string

## Evolution from earlier versions

| Version | Accounts shape | Issues |
|---|---|---|
| v1 | `Accounts: [{id, name, business, business_name, kita_visible: bool, kita_slots_declared: float, …}]` | Duplicate `business`/`business_name`; booleans where strings expected |
| v2 | `Accounts: [{internal_Id, name, kita_visible: "visible"/"", kita_slots_declared: "X.XX", …}]` | Wrong identity key (`internal_Id` uppercase is legacy-only); field names partly Dataverse-ish |
| **v3 (now)** | `Accounts: [{id, business_name, kita_visible: "visible"/"", kita_slots_declared: "X.XX", …}]` | All 7 new-model bindings resolve; no duplicates; native string types |

## StoreData

Still accepts both forms for robustness:
- Key lookup order: `id` → `internal_id` → `internal_Id` → `name`
- `kita_slots_declared` / `seb_slots_declared` / `tfo_hours_declared` values
  are coerced via `float()`, so the hub can post back either a string
  (`"77.00"`) or a number and either lands correctly.

## Tests

`miki_app/tests/test_miki_app.py::TestHubSerialization` asserts:
- `Accounts` is a list
- Each item has non-empty `id` and a `business_name`
- Visibility values are in `{"visible", ""}`
- Slot / hour values are strings
- Top-level `organization_comment` present, no `fields` wrapper

Round-trip test `test_accounts_matched_by_row_name_not_row_order` sends a
reversed Accounts list with string values (`"77.00"`) and confirms the
correct row updates. All 45 miki_app tests pass.

## If the hub still renders empty

The server side now matches the new model exactly. Remaining possibilities
are all client-side:

1. **Cached response** — hard reload (⇧⌘R / Ctrl+F5).
2. **Wrong declaration id** in the hub — confirm it's calling GetData on
   `110s35dtjh` (the test one with populated values), not an earlier one.
3. **Wrong endpoint** — should be `miki_app.api.goodApi_webhook_MikiAction_legacy`
   (returns bare JSON, no Frappe `{"message": ...}` wrapper).
4. **Token identity** — JWT `sub` must be in `Customer.<business>.portal_users`
   or the server silently returns `{}`.
