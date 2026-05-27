# Using the ERPNext Skills Package

This guide shows you how to install and use the ERPNext Skills Package across different Claude platforms.

## Quick Start

| Platform | Installation Time | Difficulty |
|----------|:-----------------:|:----------:|
| Claude Code (CLI) | 2 minutes | Easy |
| Claude.ai Web | 5 minutes | Easy |
| Claude Desktop | 5 minutes | Easy |
| Claude Mobile | ❌ Not supported | - |

## Prerequisites

- **Claude Code**: Active Claude Code installation
- **Claude.ai / Desktop**: Pro, Max, Team, or Enterprise plan with Code Execution enabled

## Platform-Specific Guides

- [Claude Code Installation](docs/usage/claude-code.md) - Recommended for developers
- [Claude.ai Web Installation](docs/usage/claude-web.md) - Browser-based usage
- [Claude Desktop Installation](docs/usage/claude-desktop.md) - Desktop app usage

## What's Included

This package contains 28 skills organized by category:

### Syntax Skills (8)
Reference guides for ERPNext/Frappe code patterns:
- `syntax-client-scripts` - Client Script syntax and events
- `syntax-server-scripts` - Server Script sandbox rules
- `syntax-controllers` - Document controller methods
- `syntax-hooks` - hooks.py configuration
- `syntax-whitelisted` - @frappe.whitelist() patterns
- `syntax-jinja` - Jinja templating in print formats
- `syntax-scheduler` - Scheduled job configuration
- `syntax-custom-app` - Custom app structure

### Core Skills (3)
Fundamental Frappe framework knowledge:
- `core-database` - Database operations and ORM
- `core-permissions` - Permission system
- `core-api-patterns` - API design patterns

### Implementation Skills (8)
Step-by-step workflows:
- `impl-client-scripts` - Client Script implementation
- `impl-server-scripts` - Server Script implementation
- `impl-controllers` - Controller implementation
- `impl-hooks` - Hooks implementation
- `impl-database` - Database operation workflows
- `impl-permissions` - Permission implementation
- `impl-api` - API implementation
- `impl-scheduler` - Scheduler implementation
- `impl-jinja` - Print format implementation

### Error Handling Skills (7)
Debugging and troubleshooting:
- `errors-client` - Client-side error handling
- `errors-server` - Server-side error handling
- `errors-database` - Database error handling
- `errors-permissions` - Permission error handling
- `errors-api` - API error handling
- `errors-scheduler` - Scheduler error handling
- `errors-print` - Print format error handling

### Agents (2)
Intelligent assistants:
- `agent-erpnext-dev` - Full-stack ERPNext development
- `agent-code-review` - ERPNext code review

## Version Compatibility

All skills support:
- **Frappe/ERPNext v14** ✅
- **Frappe/ERPNext v15** ✅
- **Frappe/ERPNext v16** ✅

Version-specific differences are documented within each skill.

## How Skills Work

When you start a conversation, Claude loads only the skill names and descriptions (~100 tokens per skill). When your request matches a skill's description, Claude loads the full instructions. This "progressive disclosure" means you can have all 28 skills available without context bloat.

### Triggering Skills

Skills activate automatically based on your request:

```
You: "Help me create a Server Script that validates Sales Orders"
Claude: [Loads syntax-server-scripts and impl-server-scripts automatically]
```

You can also reference skills explicitly:

```
You: "Using the server-scripts skill, show me the sandbox limitations"
```

### Checking Available Skills

Ask Claude:
```
You: "What ERPNext skills do you have access to?"
```

## Global Installation (Claude Code CLI)

Copy all skills to your global skills directory so they're available in every project:

```bash
cp -r skills/source/* ~/.claude/skills/
```

The skills use progressive disclosure: at startup Claude only loads the name and description (~100 tokens per skill). Full instructions are loaded only when a skill is relevant to your request.

28 skills x ~100 tokens = ~2,800 tokens startup overhead. This is negligible on a 200k token context window.

## Critical: Server Script Sandbox

The most important thing to know about ERPNext development:

**Server Scripts run in a RestrictedPython sandbox. ALL imports are blocked.**

```python
# ❌ WRONG - Will fail
from frappe.utils import nowdate
import json

# ✅ CORRECT - Use frappe namespace
date = frappe.utils.nowdate()
data = frappe.parse_json(json_string)
```

This is the #1 cause of AI-generated ERPNext code failures. All skills in this package are designed with this limitation in mind.

## Support

- **Issues**: [GitHub Issues](https://github.com/OpenAEC-Foundation/Frappe_Claude_Skill_Package/issues)
- **Documentation**: [Full Documentation](docs/)

## License

LGPL-3.0 License - See [LICENSE](LICENSE.md) for details.
