# Claude Code Best Practices Gap Analysis

**Date:** 2026-03-30
**Focus:** general
**Confidence:** 7/10
**Source:** https://github.com/shanraisshan/claude-code-best-practice (104 markdown files)

Sources include tips from Boris Cherny, Thariq Shihipar (Anthropic), and community patterns.

## What Mantle Already Does Well

- Multi-agent orchestration with fresh context per stage (build pipeline)
- TaskCreate/TaskUpdate for persistent progress tracking
- State machine in .mantle/ for workflow context
- Build-mode overrides for automated vs interactive flows
- Permission enforcement in .claude/settings.json
- Session logging and vault compilation on SessionStart
- Agent specialization (story-implementer, researcher, codebase-analyst, domain-researcher)

## High-Impact Gaps

### 1. Hooks — Largely Untapped

Mantle only has a SessionStart hook. Recommended additions:

- **PostToolUse + Write|Edit matcher** — auto-run `just fix` after file edits (handles lint/format, prevents CI failures)
- **Stop hook** — nudge Claude to verify work at end-of-turn (e.g., run tests)
- **PreToolUse logging** — audit trail of all bash commands
- **async: true** — for notifications/logging that shouldn't block Claude
- **On-demand safety hooks** — /careful pattern blocks rm -rf, DROP TABLE, force-push via PreToolUse matcher

### 2. Agent Memory Not Prompted

Best practice: tell agents "review your memory before starting, update it after completing." Mantle's story-implementer has `memory: project` but commands don't prompt agents to use it.

### 3. Skills Are Flat Files, Not Folders

Best practice: skills are folders with SKILL.md, references/, scripts/, examples/, config.json. Mantle vault skills are single markdown files. Progressive disclosure (Claude reads deeper files as needed) is lost.

### 4. No `<important if="...">` Tags in CLAUDE.md

These prevent Claude from ignoring critical rules as context grows. Useful for import rules, exception handling, test conventions.

### 5. Context Management Settings Missing

- No `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` set (recommended: 80% in settings.json env field)
- No guidance on manual `/compact` at ~50% context usage in long-running commands

### 6. Description Fields Should Be Triggers

Agent and skill descriptions should be written as "when should I fire?" (trigger conditions) not "what does this do?" (summary). Affects auto-invocation accuracy.

### 7. Settings Schema Reference

Add `"$schema": "https://json.schemastore.org/claude-code-settings.json"` to settings.json for IDE autocompletion.

## Medium-Impact Gaps

- No `.claude/settings.local.json` template for personal overrides (with disableAllHooks example)
- Agent tool allowlists not explicitly defined in agent frontmatter (`tools` field)
- No agent `maxTurns` caps to prevent runaway agents
- No `--bare` flag usage for non-interactive/SDK calls (10x faster startup)

## Recommended Priority Order

1. Add PostToolUse hook for auto-formatting (highest leverage, prevents CI failures)
2. Add Stop hook for end-of-turn verification
3. Set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=80` in settings.json env
4. Add `<important>` tags to CLAUDE.md critical rules
5. Prompt agents to review/update memory explicitly in commands
6. Rewrite agent descriptions as trigger conditions
7. Add settings.json schema reference
8. Add `maxTurns` and `tools` allowlists to agent definitions

## Key Insight

The single highest-leverage practice from the research: "Give Claude a way to verify its output — if Claude has a feedback loop, it 2-3x the quality of the final result." This aligns with Mantle's verify step in the build pipeline but could be extended to smaller feedback loops via Stop hooks.
