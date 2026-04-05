---
issue: 31
title: Inbox prompt + plan-issues integration
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer, I want a /mantle:inbox command for quick idea capture and inbox items surfaced during planning so that ideas flow from capture to triage naturally.

## Depends On

Story 2 — the prompt invokes CLI commands created in story 2.

## Approach

Create a static markdown prompt for /mantle:inbox that asks for title + optional description and saves via CLI. Modify the existing plan-issues.md prompt to surface open inbox items alongside bugs when starting a planning session.

## Implementation

### claude/commands/mantle/inbox.md (new file)

Static Claude Code command prompt:

\`\`\`markdown
---
allowed-tools: Bash(mantle *)
---

Ultra-low-friction idea capture. Ask the user for:

1. **Title** — what's the idea? (one line)
2. **Description** — optional one-liner elaboration. If the user doesn't provide one, use empty string.

Then save via CLI:

\\\`\\\`\\\`bash
mantle save-inbox-item --title "<title>" --description "<description>"
\\\`\\\`\\\`

Keep it ultra-lightweight. No multi-field interviews. No structured metadata beyond title and description. The whole interaction should take under 30 seconds.

After saving, confirm:

> Idea captured. Run /mantle:plan-issues to surface it during planning.
\`\`\`

### claude/commands/mantle/plan-issues.md (modify)

Find the section where open bugs are surfaced (search for "bugs" or "bug" in the file). Add a parallel block for inbox items:

After the bugs surfacing block, add:

\`\`\`
### Inbox items

Run \`mantle list-inbox-items --status open\` (use Bash tool). If there are open items, display them:

> **Open inbox items:**
> - {title} ({date})

Ask the user if any should be promoted to issues or dismissed before continuing.
\`\`\`

This follows the same pattern as bug surfacing — read from CLI, display, let user decide.

#### Design decisions

- **No --source flag in prompt**: The prompt always uses source=user (default). AI source is used during build pipelines where the AI calls the CLI directly.
- **Minimal prompt**: The inbox command should feel faster than filing an issue. Two questions max.

## Tests

No automated tests for this story — prompt files (.md) are tested via live usage. The CLI commands they invoke are tested in Story 2.

Acceptance criteria verification:
- AC 2 (/mantle:inbox prompt): covered by inbox.md
- AC 4 (plan-issues surfaces items): covered by plan-issues.md modification
- AC 5 (build pipeline reports): Not modified here — build.md already has a Step 9 summary section. After implementation, the build orchestrator naturally reports via CLI output. No prompt change needed.