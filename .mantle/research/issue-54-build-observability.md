---
issue: 54
date: 2026-04-12
type: implementation-research
---

## 1. Claude Code session data

**Finding:** Claude Code already writes per-message JSONL transcripts at
`~/.claude/projects/<slug>/<session-uuid>.jsonl`. Each assistant turn carries
the fields Mantle needs — no custom LLM instrumentation required.

**Evidence (actual line from this project):**
`~/.claude/projects/-Users-conal-Development-mantle/0b112a41-....jsonl`

```
{"type":"assistant","isSidechain":false,"sessionId":"0b11...",
 "parentUuid":"65c3...","timestamp":"2026-04-10T15:20:37.809Z",
 "cwd":"/Users/conal/Development/mantle","gitBranch":"master",
 "message":{"model":"claude-opus-4-6","id":"msg_...",
   "usage":{"input_tokens":2,"cache_creation_input_tokens":13494,
     "cache_read_input_tokens":12896,"output_tokens":111,
     "service_tier":"standard"}}}
```

Subagent turns (`Agent`/`story-implementer` spawns) appear in the *same* JSONL
with `isSidechain: true` and a `parentUuid` pointing at the spawning turn.
This is the documented pattern per the Agent SDK cost-tracking docs and the
per-subagent tracking feature request
(github.com/anthropics/claude-code/issues/22625).

So per-story telemetry is fully derivable post-hoc:
- Group by `isSidechain:true` clusters sharing a parent chain → one agent run
- `message.model` → model actually used (detects routing drift)
- Sum `usage.*` across that cluster → tokens
- `max(timestamp) - min(timestamp)` → duration

**Recommendation:** Parse JSONL post-hoc. Do not ask the LLM to self-report
stats — it's fragile and duplicates data that already exists. Correlate by
spawning the agent and capturing the first sidechain uuid emitted after a
known marker (e.g., story id in the prompt).

## 2. Minimum viable build log format

Per AC: model, first-attempt pass/fail, retry outcome, relative duration,
reviewable summary. Recommend one markdown file per build under
`.mantle/builds/`, YAML frontmatter for machine-readable fields:

```
.mantle/builds/build-{NN}-{YYYYMMDD-HHMM}.md
---
issue: 54
started: 2026-04-12T14:02:11Z
finished: 2026-04-12T14:37:48Z
session_id: 0b112a41-...
stories:
  - id: 1
    title: "Add telemetry parser"
    model: claude-opus-4-6
    attempts:
      - result: pass      # pass | fail | blocked
        duration_s: 412
        input_tokens: 18240
        output_tokens: 3120
        cache_read: 94210
    final: completed
  - id: 2
    model: claude-sonnet-4-5
    attempts:
      - {result: fail, duration_s: 88}
      - {result: pass, duration_s: 201}
    final: completed
---

## Summary
2 stories, 1 first-pass, 1 retry. Total wall: 35m. Routing: 1 opus / 1 sonnet.
```

Rendered tables below the frontmatter give the "reviewable summary" the AC
asks for. Keep it to one file per build so `ls .mantle/builds/` is the index.

## 3. Capture points

Mantle layout confirmed: 33 core modules in `src/mantle/core/` (none import
`cli/`), CLI wrappers in `src/mantle/cli/`. The orchestrator lives in the
prompt `claude/commands/mantle/implement.md` — no Python control flow owns
the loop, so core modules cannot instrument stories directly.

Three options evaluated:

| Option | Quality | Notes |
|---|---|---|
| LLM self-reports stats at end of agent | Poor | Fragile, duplicates JSONL data, Iron Law #3 concerns |
| Core `telemetry.py` + CLI commands called by orchestrator | Good | Fits architecture rule — core parses JSONL, CLI is the thin wrapper the prompt already uses (`mantle update-story-status`, `mantle save-learning`) |
| Pure post-hoc parse | Good | Needs only one command: `mantle build-report --issue N` |

**Recommendation:** Hybrid — lean on post-hoc parsing, invoked from the
orchestrator.
1. New `src/mantle/core/telemetry.py` — pure parser: reads JSONL, groups
   sidechains, returns story-level records. No CLI or filesystem side effects
   beyond reading `~/.claude/projects/`.
2. New `src/mantle/cli/builds.py` — adds `mantle build-start` (records
   session id + start time to a build file) and `mantle build-finish`
   (parses JSONL, writes the full markdown report).
3. `implement.md` adds two lines: `mantle build-start --issue {N}` after
   Step 2, `mantle build-finish --issue {N}` in Step 6.

Story-id ↔ sidechain mapping: the orchestrator already emits `mantle
update-story-status --status in-progress` immediately before each spawn —
use that timestamp plus story id to window the subsequent sidechain cluster.

Refs: `src/mantle/core/session.py` (existing pattern for reading outside
files), `src/mantle/cli/storage.py` (CLI module naming).

## 4. Cost attribution manifest (Colin's pattern)

**Finding:** No practitioner named "Colin" surfaces for Claude Code cost
attribution manifests. The "Colin scout findings" referenced in session notes
appears to be an internal Mantle scout run, not an external author. The
closest external prior art:

- **Manifest (aiagentstore.ai)** — an observability product for "OpenClaw"
  agents doing per-action token/cost tracking. Product, not a pattern spec.
- **Claude Agent SDK `modelUsage`** — map of model → token counts/cost,
  explicitly designed for "Haiku for subagents + Opus for main" routing.
  This is the canonical shape Mantle should mirror.
  (platform.claude.com/docs/en/agent-sdk/cost-tracking)
- **claude-devtools** — renders each subagent as an execution tree with
  token metrics, cost, duration, per-turn attribution across 7 categories.
  (claude-dev.tools/docs)
- **GitHub issue #22625** — active Anthropic feature request proposing the
  exact schema we need: `{input_tokens, output_tokens, cache_read/write,
  timestamp, sessionId, agentId, agentType, taskDescription, duration,
  model}` persisted per-invocation.

**Recommendation:** Adopt the issue-22625 schema verbatim as the per-story
record shape. It's the shape Anthropic will likely ship natively, so Mantle's
parser becomes a thin forward-compatible wrapper. No OpenTelemetry /
LangSmith overhead warranted at this scale.

## Shaping implications

- Telemetry is a **parsing problem, not a logging problem** — the data
  already exists in `~/.claude/projects/*.jsonl`. Scope the issue to
  "read + summarise", not "instrument".
- **No prompt-side stat collection.** Keep `implement.md` changes to two
  CLI calls (`build-start`, `build-finish`); do not ask agents to report.
- **Core/CLI split is clean:** one pure parser in `core/telemetry.py`, one
  CLI surface in `cli/builds.py`. Architecture rule holds.
- **Story↔sidechain correlation is the only non-trivial design call.**
  Either (a) timestamp-window around `update-story-status in-progress`, or
  (b) have orchestrator record the spawning turn's uuid. (b) is more
  robust and cheap.
- **Forward compatibility:** mirror the Anthropic issue-22625 record shape
  so when/if Claude Code ships native per-subagent metrics, Mantle swaps
  parser for native feed without changing the build-report format.

Sources:
- [Claude Agent SDK — Track cost and usage](https://platform.claude.com/docs/en/agent-sdk/cost-tracking)
- [anthropics/claude-code #22625 — Per-Subagent Token Usage Tracking](https://github.com/anthropics/claude-code/issues/22625)
- [anthropics/claude-code #10388 — Agent Token Usage API](https://github.com/anthropics/claude-code/issues/10388)
- [Claude Code Internals Part 15: Telemetry and Metrics](https://kotrotsos.medium.com/claude-code-internals-part-15-telemetry-and-metrics-1c4fafedbda8)
- [Manifest AI Agent](https://aiagentstore.ai/ai-agent/manifest)
- [claude-devtools docs](https://www.claude-dev.tools/docs)
