# DocTypes

DocTypes are the core data model in Frappe. Each DocType becomes a database table and gets auto-generated CRUD APIs, forms, and list views.

## Creating a DocType

Create the DocType through Desk/developer-mode export when possible. If you are
editing files directly, add the complete file set together: JSON definition,
empty `__init__.py`, and a Python controller class. Do not create partial
DocType folders that only contain JSON.

File path: `apps/<app>/<app>/<module>/doctype/<doctype_name>/<doctype_name>.json`

Minimal example:
```json
{
    "name": "Expense",
    "module": "Expense Tracker",
    "doctype": "DocType",
    "engine": "InnoDB",
    "fields": [
        {
            "fieldname": "title",
            "fieldtype": "Data",
            "label": "Title",
            "reqd": 1
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Amount",
            "reqd": 1
        },
        {
            "fieldname": "status",
            "fieldtype": "Select",
            "label": "Status",
            "options": "Draft\nApproved\nRejected",
            "default": "Draft"
        }
    ],
    "autoname": "format:EXP-{####}",
    "naming_rule": "Expression",
    "is_submittable": 0,
    "permissions": [
        {
            "role": "System Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1
        }
    ]
}
```

Also create an empty `__init__.py` alongside the JSON:
```
apps/<app>/<app>/<module>/doctype/<doctype_name>/__init__.py
```

Every custom DocType and child table must also have a controller file:
```python
# apps/<app>/<app>/<module>/doctype/<doctype_name>/<doctype_name>.py
from frappe.model.document import Document


class Expense(Document):
    pass
```

## Common field types

| fieldtype | Use for |
|-----------|---------|
| Data | Short text (140 chars) |
| Small Text | Multi-line text |
| Text Editor | Rich text (HTML) |
| Int | Integer |
| Float | Decimal |
| Currency | Money amounts |
| Date | Date only |
| Datetime | Date + time |
| Select | Dropdown (options separated by `\n`) |
| Link | Foreign key to another DocType |
| Table | Child table (one-to-many) |
| Check | Boolean (0/1) |
| Attach | File attachment |

## Naming patterns

- `autoname: "format:EXP-{####}"` — sequential (EXP-0001, EXP-0002)
- `autoname: "field:title"` — use field value as name
- `autoname: "hash"` — random hash
- `autoname: "naming_series:"` — user-configurable series
- `autoname: "prompt"` — user enters name manually

## Child DocTypes

For one-to-many relationships (e.g. Expense Items inside an Expense):

1. Create a child DocType JSON with `"istable": 1`
2. Add a `Table` field in the parent pointing to it:
```json
{
    "fieldname": "items",
    "fieldtype": "Table",
    "label": "Items",
    "options": "Expense Item"
}
```

Child DocType must have `"istable": 1` and no permissions (inherits from parent).

## After creating/modifying DocTypes

Always run:
```bash
bench --site <site> migrate
```

## Other useful JSON keys

```json
{
    "sort_field": "modified",       // default sort column for list view
    "sort_order": "DESC",           // ASC or DESC
    "track_changes": 1,             // enable version history / timeline
    "is_submittable": 1             // enables Submit → Cancel → Amend workflow
}
```

Submittable DocTypes get a `docstatus` field automatically: `0` = Draft, `1` = Submitted, `2` = Cancelled. Users cannot edit submitted documents — they must cancel and amend.

Do NOT add `creation`, `modified`, `owner`, `modified_by`, or `docstatus` as fields — Frappe creates these automatically.
