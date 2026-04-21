---
issue: 82
title: Export MANTLE_DIR via SessionStart hook + CLAUDE_ENV_FILE
approaches:
- CLAUDE_ENV_FILE export + prompt fallback (chosen)
- settings.json env field (rejected — static/global)
- hookSpecificOutput.additionalContext injection (rejected — not shell-visible)
chosen_approach: CLAUDE_ENV_FILE export + prompt fallback
appetite: small batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-21'
updated: '2026-04-21'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Context

Many /mantle:* command prompts open by asking the model to run `mantle where` and capture its output into `MANTLE_DIR`. The value is session-stable but paid for repeatedly on every command invocation — a tool call, subprocess, and LLM turn, all for a value that does not change. This issue lifts that resolution into a Claude Code SessionStart hook so the value is computed once per session and referenced via `$MANTLE_DIR` thereafter.

## Approaches evaluated

### A. CLAUDE_ENV_FILE export + prompt fallback (chosen)

Claude Code's documented mechanism for setting session-wide shell env vars from a SessionStart hook is the `CLAUDE_ENV_FILE` env var. When a SessionStart hook runs, CC provides `$CLAUDE_ENV_FILE` pointing at a file whose contents are sourced before every subsequent Bash tool call. The idiomatic pattern is:

```bash
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo "export MANTLE_DIR=$(mantle where)" >> "$CLAUDE_ENV_FILE"
fi
```

Combined with prompts that use `MANTLE_DIR="${MANTLE_DIR:-$(mantle where)}"`, the fallback (AC-03) is automatic: when the hook is installed and CC surfaced CLAUDE_ENV_FILE, the env var is already set; when not, the prompt falls back to resolving once.

### B. settings.json env field (rejected)

Claude Code's `settings.json` supports an `env` map, but values are static strings — they cannot be computed dynamically by a hook. For a project-specific `MANTLE_DIR` that varies by repo, a static setting is wrong as soon as the user opens a second project.

### C. hookSpecificOutput.additionalContext (rejected)

SessionStart hooks can emit JSON with `hookSpecificOutput.additionalContext` that injects text into the model's context. This surfaces the value to the LLM, but not to `$MANTLE_DIR` expansion inside a Bash tool call — which is what AC-02 actually needs.

## Code design

### Strategy

1. **`claude/hooks/session-start.sh`** — after the existing `.mantle/` guard and `mantle compile --if-stale`, add a block that appends `export MANTLE_DIR=<absolute path>` to `$CLAUDE_ENV_FILE` when the env var is set. Use `mantle where` to resolve the value so it respects the `mantle storage` mode (local vs global). When `CLAUDE_ENV_FILE` is unset (older CC versions, non-CC shells running the hook for tests), the block is a no-op.

2. **`claude/commands/mantle/build.md`** — Step 1 currently says:
   ```
   MANTLE_DIR=$(mantle where)
   ```
   Replace with:
   ```
   MANTLE_DIR="${MANTLE_DIR:-$(mantle where)}"
   ```
   This uses the hook-exported value when present, falls back otherwise. No change to the downstream instruction ("All subsequent `Read`/`Grep`/`Glob` calls must use `$MANTLE_DIR/...`").

3. **`tests/hooks/test_session_start.py`** — extend with two tests reusing the existing `_run_hook` helper:
   - With `.mantle/` present and `CLAUDE_ENV_FILE` pointed at a writable file, the hook writes exactly one `export MANTLE_DIR=<resolved-path>` line to that file.
   - With `CLAUDE_ENV_FILE` unset, the hook exits 0 and does not crash; no stray file is written.

   Use `inline_snapshot` for the exported-line shape if the value after `=` is stabilised (mantle where output in tmp_path equals an assertable absolute path).

### Fits architecture by

- Reuses the existing hook infrastructure — `claude/hooks/session-start.sh` is already bundled into the wheel via `[tool.hatch.build.targets.wheel.force-include]` and registered by `install.py`'s `_register_hooks`. No install flow changes.
- Respects `core never imports cli` (no Python code changes beyond tests).
- Tests live under `tests/hooks/` following the mirrored layout convention from CLAUDE.md; named scenario style per project test conventions.

### Does not

- Does not migrate every /mantle:* prompt to use `$MANTLE_DIR` — AC-02 only requires the highest-frequency command (build.md). Broader migration is a follow-up issue after the pattern is proven in production.
- Does not change `mantle install` or hook registration. The hook file is re-copied on the next `mantle install`; no users need to re-install for the new behaviour until they want the perf gain.
- Does not bake `MANTLE_DIR` into `settings.json` — that would be wrong across multi-project use (approach B).
- Does not introduce a `claude-code-hooks` vault skill — the surface area for this issue is a single documented CC pattern (CLAUDE_ENV_FILE), captured inline in this shape doc; a full skill would be speculative.

## AC coverage

- **ac-01** (SessionStart hook exports `MANTLE_DIR`): bash block in `session-start.sh`.
- **ac-02** (highest-frequency command uses `$MANTLE_DIR`): one-line edit in `build.md` Step 1.
- **ac-03** (fallback when `MANTLE_DIR` unset): the `${MANTLE_DIR:-$(mantle where)}` idiom covers the unset case inline.
- **ac-04** (test for hook generation/installation path): two new tests in `tests/hooks/test_session_start.py`.
- **ac-05** (`just check` passes): tests + formatters + ty + import-linter run in the implementation loop.