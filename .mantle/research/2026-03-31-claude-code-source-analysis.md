---
date: 2026-03-31
focus: general
confidence: 7/10
tags:
  - type/research
---

# Claude Code Source Analysis — Patterns Applicable to Mantle

**Source:** https://github.com/nirholas/claude-code (official Anthropic source, ~1,900 files, 512K+ lines TypeScript)

## Summary

Investigated the full Claude Code source code (made public 2026-03-31) to identify internal patterns that Mantle could adopt. The codebase reveals several sophisticated systems — particularly around memory, context management, agent orchestration, and skill loading — that go well beyond what the public documentation describes.

## High-Impact Findings

### 1. Typed Memory System with LLM-Based Recall

Claude Code uses a structured memory system (`src/memdir/`) that goes far beyond flat MEMORY.md files:

- **MEMORY.md as index, not storage** — 200-line-capped index of one-line pointers. Actual content lives in individual topic files with YAML frontmatter (name, description, type).
- **Four memory types**: user, feedback, project, reference. Content derivable from code is explicitly excluded.
- **LLM-based recall at query time** — `findRelevantMemories.ts` scans all memory file headers, then asks Sonnet to select up to 5 relevant ones. Uses a `sideQuery` (separate cheap API call) to avoid polluting the main context.
- **Auto-extraction at session end** — `extractMemories.ts` runs via post-sampling hook after each turn, using a forked agent to identify durable memories.
- **Byte AND line caps** — Truncation at both 200 lines and 25KB prevents bloated indexes.

**Mantle application:** Session logs and skill nodes could adopt this pattern. Instead of loading all context into the system prompt, maintain a lightweight index and use a cheap LLM call to select relevant context per query.

### 2. Forked Agent Pattern for Side-Operations

`forkedAgent.ts` is Claude Code's core pattern for background AI operations:

- Forks share the parent's prompt cache (identical system prompt, tools, model, messages prefix) for zero incremental cache cost.
- Used for: auto-compaction, memory extraction, session memory, prompt suggestions.
- Each fork has isolated mutable state.

**Mantle application:** Validates Mantle's existing agent-per-story approach. Key insight: when possible, share context prefix for cache hits.

### 3. Auto-Compaction with Circuit Breaker

The compaction system (`src/services/compact/`) is extremely sophisticated:

- Threshold-based auto-compaction at ~(effective context window - 13K buffer tokens).
- **Circuit breaker** — after 3 consecutive failures, stops retrying (previously wasted ~250K API calls/day).
- Two-stage: session memory compaction first, full summarization as fallback.
- **Analysis scratchpad** — uses `<analysis>` tags as drafting scratchpad that gets stripped from final summary.
- Partial compaction — can compact only older messages while preserving recent ones.

**Mantle application:** The `<analysis>` scratchpad pattern is directly applicable to challenge, research, and design commands. Circuit breaker pattern is relevant for implementation retries.

### 4. Skill Loading: Frontmatter-First with Lazy Content

Skills loaded in two phases: frontmatter scanned at startup, full content loaded on invocation.

Key fields Mantle could adopt:
- `allowedTools` — restricts tool access per skill (already in v0.7.12)
- `context: 'inline' | 'fork'` — run in current context or spawn new agent
- `hooks` — per-skill hook definitions
- `whenToUse` — trigger conditions for auto-invocation (separate from description)

### 5. Hooks Architecture: Per-Event, Per-Skill, Async-Capable

The hooks system is far richer than documented:

- **Hook types**: PreToolUse, PostToolUse, Stop, PreCompact, PostCompact, SessionStart, PostSampling
- **Execution modes**: shell commands, agent hooks, HTTP hooks, prompt hooks
- **Per-skill hooks** — only active when that skill is running
- **Async flag** — hooks can run without blocking
- SSRF guard and file-changed watcher

**Mantle application:** Per-skill hooks are particularly interesting — `/mantle:implement` could register a PostToolUse hook for auto-formatting only during implementation.

### 6. Session Memory Compaction

Distinct from auto-compaction, `SessionMemory/` maintains a running summary:

- Key facts extracted into session memory after each compaction
- Session memory checked first on next compaction — can replace full re-summarization
- `lastSummarizedMessageId` tracks what has been summarized

## Medium-Impact Findings

### 7. Description vs whenToUse

Claude Code explicitly separates `description` (what it does) from `whenToUse` (trigger conditions for auto-invocation). Confirms the previous research gap finding (2026-03-30) with source evidence.

### 8. Coordinator Mode

The coordinator (`src/coordinator/`) is surprisingly thin — mainly a mode flag plus specialized tools. Actual orchestration is prompt-driven, not code-driven. Validates Mantle's prompt-based orchestration approach.

### 9. Auto-Dream Background Ideation

`src/services/autoDream/` runs background "dreaming" — autonomous ideation between user interactions. Interesting for future exploration.

## Patterns Mantle Already Gets Right

- Prompt-based orchestration (implement.md mirrors coordinator approach)
- Fresh context per agent (story-implementer = LocalAgentTask)
- State in filesystem (.mantle/ = ~/.claude/projects/)
- Skill loading from directories
- Permission allowlists

## Actionable Recommendations (Priority Order)

1. **Add `whenToUse` field to skill/agent definitions** — separate trigger conditions from descriptions. Estimated effort: small.
2. **Implement `<analysis>` scratchpad pattern** in challenge, research, and design commands. Estimated effort: small (prompt change only).
3. **Adopt memory index pattern** — make `.mantle/state.md` a lightweight index pointing to topic files. Estimated effort: medium.
4. **Add PostToolUse hook for auto-formatting** — confirmed production-proven. Estimated effort: small (settings.json change).
5. **Implement per-skill hooks** — allow skills to register hooks only active during execution. Estimated effort: medium.
6. **Add circuit breaker to implementation retries**. Estimated effort: small (prompt logic change).
