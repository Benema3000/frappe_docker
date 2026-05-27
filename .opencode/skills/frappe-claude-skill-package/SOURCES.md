# SOURCES - ERPNext Skills Package

> Approved documentation sources for skill development and research.
> All skills must reference ONLY these verified sources.

---

## Primary Sources

### Frappe Framework Documentation

| Source | URL | Coverage | Last Verified |
|--------|-----|----------|---------------|
| Frappe Framework Docs | https://docs.frappe.io/framework | Core framework API, hooks, controllers | 2026-01-17 |
| Database API | https://docs.frappe.io/framework/user/en/api/database | frappe.db methods, query builder | 2026-01-17 |
| Document API | https://docs.frappe.io/framework/user/en/api/document | frappe.get_doc, document lifecycle | 2026-01-17 |
| Form API | https://docs.frappe.io/framework/user/en/api/form | Client-side form manipulation | 2026-01-17 |
| JS Utils | https://docs.frappe.io/framework/user/en/api/js-utils | JavaScript utility functions | 2026-01-17 |
| Query Builder | https://docs.frappe.io/framework/user/en/api/query-builder | pypika-based query builder | 2026-01-17 |
| Users & Permissions | https://docs.frappe.io/framework/user/en/basics/users-and-permissions | Permission system, roles | 2026-01-17 |
| Client Scripts | https://docs.frappe.io/framework/user/en/desk/scripting/client-script | Client script API | 2026-01-17 |
| Caching | https://docs.frappe.io/framework/user/en/guides/caching | Redis caching patterns | 2026-01-17 |
| REST API | https://docs.frappe.io/framework/user/en/guides/integration/rest_api | REST API integration | 2026-01-17 |
| OAuth 2 | https://docs.frappe.io/framework/user/en/guides/integration/rest_api/oauth-2 | OAuth2 authentication | 2026-01-17 |
| Token Auth | https://docs.frappe.io/framework/user/en/guides/integration/rest_api/token_based_authentication | Token-based auth | 2026-01-17 |
| Webhooks | https://docs.frappe.io/framework/user/en/guides/integration/webhooks | Webhook configuration | 2026-01-17 |
| Python Hooks | https://docs.frappe.io/framework/user/en/python-api/hooks | hooks.py configuration | 2026-01-17 |
| Permission Types | https://docs.frappe.io/framework/permission-types | Permission system types | 2026-01-17 |

### Version-Specific Documentation

| Source | URL | Version | Last Verified |
|--------|-----|---------|---------------|
| Server Calls (v14) | https://docs.frappe.io/framework/v14/user/en/api/server-calls | v14 | 2026-01-17 |
| Rate Limiting (v14) | https://docs.frappe.io/framework/v14/user/en/rate-limiting | v14 | 2026-01-17 |
| Form API (v15) | https://docs.frappe.io/framework/v15/user/en/api/form | v15 | 2026-01-17 |
| Database API (v14) | https://frappeframework.com/docs/v14/user/en/api/database | v14 | 2026-01-17 |
| Document API (v14) | https://frappeframework.com/docs/v14/user/en/api/document | v14 | 2026-01-17 |
| Query Builder (v14) | https://frappeframework.com/docs/v14/user/en/api/query-builder | v14 | 2026-01-17 |
| Controllers (v15) | https://frappeframework.com/docs/v15/user/en/basics/doctypes/controllers | v15 | 2026-01-17 |

### ERPNext Documentation

| Source | URL | Coverage | Last Verified |
|--------|-----|----------|---------------|
| ERPNext Docs | https://docs.erpnext.com | ERPNext user manual | 2026-01-17 |
| User Permissions | https://docs.frappe.io/erpnext/user/manual/en/user-permissions | ERPNext permission config | 2026-01-17 |

---

## Secondary Sources

### GitHub Repositories

| Source | URL | Purpose | Last Verified |
|--------|-----|---------|---------------|
| Frappe Source | https://github.com/frappe/frappe | Source code verification | 2026-01-17 |
| ERPNext Releases | https://github.com/frappe/erpnext/releases | Version change tracking | 2026-01-17 |
| Frappe Permissions | https://github.com/frappe/frappe/blob/develop/frappe/permissions.py | Permission internals | 2026-01-17 |
| Document Model | https://github.com/frappe/frappe/blob/develop/frappe/model/document.py | Document lifecycle | 2026-01-17 |
| Client Scripting Wiki | https://github.com/frappe/frappe/wiki/Client-Side-Scripting-Index | Client script reference | 2026-01-17 |
| Query Builder Migration | https://github.com/frappe/frappe/wiki/query-builder-migration | Migration guide | 2026-01-17 |

### Agent Skills & Anthropic

| Source | URL | Purpose | Last Verified |
|--------|-----|---------|---------------|
| Agent Skills Spec | https://agentskills.io/specification | Skill format specification | 2026-01-17 |
| Anthropic Skills | https://github.com/anthropics/skills | Official skill examples | 2026-01-17 |
| Claude Code Docs | https://docs.anthropic.com/claude-code/ | Claude Code integration | 2026-01-17 |

---

## Source Usage Rules

1. **Primary sources** are the authoritative reference for all skill content
2. **Secondary sources** may be used for verification and edge cases
3. All code examples must be verifiable against at least one primary source
4. Version-specific claims must reference the corresponding version documentation
5. When primary and secondary sources conflict, primary takes precedence
