# Testing

## File location

Tests live alongside the code they test:
```
apps/<app>/<app>/<module>/doctype/<doctype>/test_<doctype>.py
```

For feature-wise tests, place in the tests directory:
```
apps/<app>/<app>/tests/test_<feature>.py
```

## Writing tests

```python
import frappe
from frappe.tests import IntegrationTestCase

class TestExpense(IntegrationTestCase):
    def test_expense_creation(self):
        doc = frappe.get_doc(doctype="Expense", title="Test", amount=100)
        doc.insert()
        self.assertEqual(doc.amount, 100)

    def test_validation(self):
        doc = frappe.get_doc(doctype="Expense", title="Test", amount=-1)
        self.assertRaises(frappe.ValidationError, doc.insert)
```

Key patterns:
- Prefer `frappe.tests.IntegrationTestCase` for database-backed tests and `UnitTestCase` for pure logic. Existing app suites may still use `frappe.tests.utils.FrappeTestCase`; do not churn them unless you are already touching the tests.
- Tests run inside a transaction that rolls back — no manual cleanup needed
- Use `frappe.get_doc(...)` to create test documents
- Each test method starts with `test_`

## Unit tests (no database)

For pure logic that doesn't need Frappe context or database:

```python
from frappe.tests import UnitTestCase

class TestExpenseUtils(UnitTestCase):
    def test_calculate_tax(self):
        self.assertEqual(calculate_tax(100, 0.1), 10)
```

`UnitTestCase` is faster — no DB setup/teardown. Use for utility functions, calculations, parsing logic.

## Test fixtures

For test data that multiple tests need, create `test_records` or use `setUp`:

```python
class TestExpense(IntegrationTestCase):
    def setUp(self):
        self.category = frappe.get_doc(doctype="Expense Category", category_name="Travel").insert()
```

## Test site

Prefer a **separate site** from the one the user is actively working on. Tests create, modify, and delete data. If bench-local guidance names an accepted dev/test site, follow that local guidance.

Convention: if the dev site is `expense.localhost`, create `expense-test.localhost` for tests:
```bash
bench new-site expense-test.localhost --admin-password admin
bench --site expense-test.localhost install-app <app-name>
```

Run tests against the selected test site:
```bash
bench --site expense-test.localhost run-tests --app <app-name>
```

## Running tests

```bash
# All tests for an app
bench --site <site> run-tests --app <app-name>

# Specific DocType
bench --site <site> run-tests --doctype "Expense"

# Specific test file
bench --site <site> run-tests --module <app>.<module>.doctype.<doctype>.test_<doctype>

# Specific test method
bench --site <site> run-tests --module <app>.<module>.doctype.<doctype>.test_<doctype> --test test_expense_creation

# With verbose output
bench --site <site> run-tests --app <app-name> -v
```

## Common pitfalls

- Always pass `--site`. Never run bare `bench run-tests`.
- If tests fail with "DocType not found", run `bench --site <site> migrate` first.
- Test files must be named `test_*.py` to be discovered.
