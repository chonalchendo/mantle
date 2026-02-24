---
issue: 3
title: Claude Code command + vault template
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create the static Claude Code command prompt and Obsidian vault template for idea capture. No code tests — static markdown files.

### claude/commands/mantle/idea.md

Static prompt guiding Claude through the `/mantle:idea` workflow:

1. **Check existing** — Read `.mantle/idea.md`. If exists, warn user and ask whether to overwrite. If `.mantle/` missing, tell user to run `mantle init` first.
2. **Gather idea** — Conversational capture of hypothesis (1–2 sentences), target user (specific role/context/skill), and success criteria (2–5 measurable outcomes). Ask each in turn, reflect back and confirm.
3. **Confirm and save** — Show summary, then run `mantle save-idea` with `--hypothesis`, `--target-user`, and repeatable `--success-criteria` flags. Add `--overwrite` if confirmed in step 1.
4. **Next steps** — Suggest `/mantle:challenge` to stress-test the idea.

### vault-templates/idea.md

Obsidian template with empty YAML frontmatter fields matching `IdeaNote` schema and body sections matching `_IDEA_BODY`:

```yaml
---
hypothesis:
target_user:
success_criteria: []
author:
created:
updated:
updated_by:
tags:
  - type/idea
  - phase/idea
---
```

Body sections: `## Hypothesis`, `## Target User`, `## Success Criteria`, `## Open Questions`.

Replaces the `.gitkeep` placeholder in `vault-templates/`.

## Tests

No tests — static markdown files only.
