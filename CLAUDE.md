# CLAUDE.md - workspace root

Guidance for Claude Code launched anywhere under `/workspace`.

## Frappe Skills

- Shared source skills live at `/workspace/.opencode/skills/`.
- Claude-visible symlinks live at `/home/frappe/.claude/skills/`.
- Use `frappe-bench` for this bench's local app map, off-limits apps,
  commands, and Goodvantage-specific gotchas.
- Use `frappe-dev` for general Frappe app-development workflows and focused
  references.
- Use `frappe-taste` for Frappe coding taste guidance from
  `frappe/bench-cli/taste.md`.
- Additional Frappe skills from `Impertio-Studio/Frappe_Claude_Skill_Package`
  are linked individually into `/home/frappe/.claude/skills/` and sourced from
  `/workspace/.opencode/skills/frappe-claude-skill-package/skills/source/`.

## Bench Guidance

- Read `/workspace/AGENTS.md` and `/workspace/development/AGENTS.md` before
  working in the bench.
- For custom app work, also read the app-local `AGENTS.md` before editing.
- Never modify upstream/off-limits apps directly unless explicitly instructed.
