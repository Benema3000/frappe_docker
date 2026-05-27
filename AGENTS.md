# AGENTS.md - workspace root

Guidance for coding agents launched anywhere under `/workspace`.

## Agent Skills

- Project opencode skills live at `/workspace/.opencode/skills/`.
- Codex-visible symlinks live at `/home/frappe/.codex/skills/`.
- Claude-visible symlinks live at `/home/frappe/.claude/skills/`.
- Use `/workspace/.opencode/skills/frappe-bench/SKILL.md` for this bench's
  local app map, off-limits apps, commands, and Goodvantage-specific gotchas.
- Use `/workspace/.opencode/skills/frappe-dev/SKILL.md` for general Frappe
  app-development workflows and focused references.
- Additional downloaded Frappe skills from
  `Impertio-Studio/Frappe_Claude_Skill_Package` live under
  `/workspace/.opencode/skills/frappe-claude-skill-package/skills/source/`.
- Use `/workspace/.opencode/skills/frappe-taste/SKILL.md` for Frappe coding
  taste guidance from `frappe/bench-cli/taste.md`.
- Keep reusable, triggerable workflow guidance in opencode skills. Keep durable
  repository and app-specific rules in `AGENTS.md` files.

## Bench Guidance

- For work in the bench, read `/workspace/development/AGENTS.md`.
- For custom app work, also read the app-local `AGENTS.md` before editing.
- Never modify upstream/off-limits apps directly unless explicitly instructed.
