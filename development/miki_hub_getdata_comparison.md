# Miki Declaration `GetData` — Wire Format vs Archive

Side-by-side comparison of the hub `GetData` response shape returned by the
current miki implementation against the legacy (Dataverse / Power Automate)
format reconstructed from archive flow logs.

Generated from live HTTP response against `development16.localhost` on
`2026-04-20`.

## Archive (legacy Dataverse) — reconstructed

Reconstructed from:
- `archived/Archive02/flow-3445bddf-...csv` → `Select_DeklarationsJSON` output (Accounts rows)
- Same CSV → `Parse_JSON_2 - input` (top-level declaration fields for StoreData; mirror shape on GetData)

```json
{
  "name": "",
  "cr2da_betriebnamedeklaration": "Krippeverein Albisrieden",
  "cr2da_cheuiddeklaration": "",
  "cr2da_betriebnamezusatzdeklaration": "",
  "cr2da_betriebstrassedeklaration": "Langgrütstrasse 134",
  "cr2da_betriebpostfachdeklaration": "",
  "cr2da_betriebplzdeklaration": "8047",
  "cr2da_betriebortdeklaration": "Zürich",
  "cr2da_betriebtelefondeklaration": "+41 44 406 87 87",
  "cr2da_betriebemaildeklaration": "info@kka.ch",
  "cr2da_kontaktpersonvornamedeklaration": "Manuela",
  "cr2da_kontaktpersonnachnamedeklaration": "Surenmann",
  "cr2da_kontaktpersontelefondeklaration": "",
  "cr2da_kontaktpersonemaildeklaration": "manuela.surenmann@kka.ch",
  "cr2da_rechnungsadresseverwenden": null,
  "cr2da_rechnungsadressenamedeklaration": "Krippeverein Albisrieden",
  "cr2da_rechnungsadressezusatzdeklaration": "",
  "cr2da_rechnungsadressestrassedeklaration": "Langgrütstrasse 134",
  "cr2da_rechnungsadressepostfachdeklaration": "",
  "cr2da_rechnungsadresseplzdeklaration": "8047",
  "cr2da_rechnungsadresseortdeklaration": "Zürich",
  "cr2da_rechnungsadresseemaildeklaration": "Info@kka.ch",
  "cr2da_begruendungabweichung": "",
  "gvme_kommentartragerschaft": "",
  "gv_bestaetigungvollstaendigkeit": true,
  "titelAbgabe": "",

  "Accounts": [
    {
      "internal_Id": "0EF44CA4-1E13-F111-8342-7CED8D42BECA",
      "kitaVisibility": "visible",
      "sebVisibility": "visible",
      "tfoVisibility": "",
      "name": "Kinderkrippe Albisrieden: ",
      "betreuungsplaetzeKITA": "50.00",
      "betreuungsplaetzeSEB": "14.00",
      "betreuungsstundenTFO": "0"
    }
  ]
}
```

## Current miki — live response

```
POST /api/method/miki_app.api.goodApi_webhook_MikiAction_legacy
body: { token, action: "GetData", processDefinitionName: "deklaration", id: "110s35dtjh" }
```

```json
{
  "Accounts": [
    {
      "business": "Test",
      "business_name": "Test",
      "id": "1109g96tdi",
      "kita_slots_declared": 1.0,
      "kita_visible": true,
      "name": "1109g96tdi",
      "seb_slots_declared": 2.0,
      "seb_visible": true,
      "tfo_hours_declared": 3.0,
      "tfo_visible": true
    }
  ],
  "billing_city_declared": null,
  "billing_country_declared": null,
  "billing_email_declared": null,
  "billing_name_declared": null,
  "billing_pob_declared": null,
  "billing_postal_code_declared": null,
  "billing_street_declared": null,
  "billing_use_separate_declared": 0,
  "business_city_declared": null,
  "business_country_declared": null,
  "business_email_declared": null,
  "business_name_declared": "Test",
  "business_phone_declared": null,
  "business_pob_declared": null,
  "business_postal_code_declared": null,
  "business_street_declared": null,
  "business_uid_declared": "",
  "completeness_confirmed": 0,
  "contact_email_declared": null,
  "contact_first_name_declared": null,
  "contact_language_declared": null,
  "contact_last_name_declared": null,
  "contact_phone_declared": null,
  "contact_role_declared": null,
  "contact_salutation_declared": null,
  "contact_will_be_updated": 0,
  "deviation_justification": null,
  "id": "110s35dtjh",
  "language": "en",
  "name": "D-000057",
  "organization_comment": null,
  "processDefinitionName": "deklaration",
  "status": "Requested"
}
```

## Structural comparison

| Feature | Archive (Dataverse) | Miki (current) | Equivalent? |
|---|---|---|---|
| **Top-level fields** | Flat, directly at root | Flat, directly at root | ✅ |
| **Field naming** | Dataverse logical names (`cr2da_*`, `gvme_*`) | Frappe/miki field names (`*_declared`, `organization_comment`) | Intentional — hub schema was updated |
| **Extra envelope keys** | — | `id`, `name`, `processDefinitionName`, `status`, `language` | Added; harmless for hub bindings |
| **`Accounts` type** | `list` of dicts | `list` of dicts | ✅ |
| **Account identity field** | `internal_Id` (UUID, uppercase I) | `id` (Frappe docname) | Renamed per hub schema (`key_variable_name: "id"`) |
| **Account visibility values** | String `"visible"` / `""` | Bool `true` / `false` | Differs — matches hub schema's `Boolean` type declaration |
| **Account slot values** | String `"50.00"` / `"14.00"` / `"0"` | Number `1.0` / `2.0` / `3.0` | Differs — matches hub schema's `Number` type declaration |
| **Account display name** | `"Kinderkrippe Albisrieden: "` | `"Test"` (business_name) | Differs — miki just emits bare `business_name` field |

## Hub schema mapping (current)

The hub's current screen schema (pasted in chat) expects fields with Frappe-style
names, so the wire format differences from the archive are intentional:

- `organization_comment` (Text)
- `deviation_justification` (Text)
- `completeness_confirmed` (Boolean)
- `business_uid_declared` (ChUid), `business_*_declared` (Text)
- `contact_*_declared`, `billing_*_declared`
- `Accounts` (ComponentList, `key_variable_name: "id"`)
  - `id`, `name`, `business_name`
  - `kita_visible`, `seb_visible`, `tfo_visible` (Boolean)
  - `kita_slots_declared`, `seb_slots_declared` (Number, step 0.01)
  - `tfo_hours_declared` (Number, step 1)

All of these are present in the miki response at the paths the bindings target.

## Known-good identity flow

- Each `Declaration Item` row is a distinct `Account` entry.
- Row docname (e.g. `1109g96tdi`) is emitted twice: once as `id` (what the hub
  binds via `Accounts[$id]['field']`) and once as `name` (legacy alias, also
  used by StoreData for round-trip matching).
- `StoreData` accepts both dict-keyed (`{"<id>": {...}}`) and list-of-dicts
  forms so the hub's POST back lands on the right row regardless of payload
  shape.

## If the hub still renders empty

Things to verify client-side (DevTools → Network → the POST to
`/api/method/miki_app.api.goodApi_webhook_MikiAction_legacy`):

1. **Request URL** — confirm it's the `_legacy` endpoint (returns bare JSON).
   The non-legacy endpoint returns `{"message": {...}}` and would need
   `response.message.Accounts` on the hub side.
2. **Response body** — should match the "Current miki" block above byte for
   byte (minus the dynamic id / name values).
3. **Hard reload** — ⇧⌘R / Ctrl+F5 to drop any cached empty payload from an
   earlier failing call.
4. **Token identity** — the JWT `sub` must be a user in
   `Customer.<declaration.business>.portal_users`; otherwise the server
   silently returns `{}`.

## Related source

- Server serializer: `miki_app/miki_app/declaration_service.py:get_declaration_data`
- Webhook dispatcher: `miki_app/miki_app/portal.py:miki_webhook`
- HTTP endpoint: `miki_app/miki_app/api.py:goodApi_webhook_MikiAction_legacy`
- Archive flow CSV: `archived/Archive02/flow-3445bddf-cfc9-41d7-a007-4ba3762dd095-20260410t021325z (1).csv`
