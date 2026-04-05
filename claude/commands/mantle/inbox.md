---
description: Ultra-low-friction idea capture for project feature ideas
allowed-tools: Bash(mantle *)
---

Ultra-low-friction idea capture. Ask the user for:

1. **Title** — what's the idea? (one line)
2. **Description** — optional one-liner elaboration. If the user doesn't
   provide one, use empty string.

Then save via CLI:

```bash
mantle save-inbox-item --title "<title>" --description "<description>"
```

Keep it ultra-lightweight. No multi-field interviews. No structured metadata
beyond title and description. The whole interaction should take under 30
seconds.

After saving, confirm:

> Idea captured. Run `/mantle:plan-issues` to surface it during planning.
