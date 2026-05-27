---
name: frappe-taste
description: Use when making Frappe or ERPNext code-quality tradeoffs, reviewing implementation style, or applying Rushabh Mehta's taste.md coding guidelines.
---

# Frappe Taste

Use this skill as a lightweight style compass for Frappe and ERPNext work.

## Guidance

- Read `references/taste.md` before making broad implementation choices.
- Prefer clean, standard, minimal code over clever custom abstractions.
- Prefer object-oriented code where it fits Frappe's Document/controller model.
- Build the minimum working app or feature, then iterate.
- Reuse standard Frappe APIs and UI patterns wherever possible.
- Keep functions and modules small enough to understand quickly.
- Avoid abbreviations and overly broad modules; split only when it improves readability.
- Keep UI aligned with Frappe/Espresso patterns unless the app has its own design system.
- Write tests and make sure they pass.

## Source

Downloaded from `https://github.com/frappe/bench-cli/blob/main/taste.md`.
