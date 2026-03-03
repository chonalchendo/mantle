---
issue: 13
title: Claude Code CLI invocation builder with story factory
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer building the implementation orchestrator, I want a structured invocation builder for Claude Code CLI so that subprocess commands are built from typed data with sensible defaults for story implementation.

## Approach

Create `core/claude_cli.py` as a leaf module (no mantle.core imports) using a frozen stdlib dataclass for the invocation spec and a `for_story()` factory that hardwires the standard story-implementation flags. The orchestrator calls `for_story()` for both initial and retry invocations — they differ only in prompt content. This is story 1 of 4: the foundation the orchestrator depends on.

## Implementation

### src/mantle/core/claude_cli.py (new file)

```python
"""Build subprocess command lists for Claude Code CLI."""
```

#### Constants

```python
CLAUDE_BIN: str = "claude"
"""Path or name of the Claude Code CLI binary."""

DEFAULT_TOOLS: tuple[str, ...] = (
    "Read", "Write", "Edit", "Bash", "Glob", "Grep",
)
"""Default tool allowlist for story implementation."""
```

#### Data model

```python
@dataclasses.dataclass(frozen=True, slots=True)
class Invocation:
    """Immutable Claude Code CLI invocation specification.

    Attributes:
        prompt: The user prompt (positional arg, always last).
        system_prompt: Injected system-level context.
        allowed_tools: Tool allowlist (comma-joined in output).
        worktree: Git worktree name for branch isolation.
        max_budget_usd: Cost ceiling per invocation.
        output_format: Output format (e.g. "json").
        no_session_persistence: Suppress session persistence.
        model: Model override (e.g. "sonnet", "opus").
        permission_mode: Permission level for tool execution.
    """

    prompt: str
    system_prompt: str | None = None
    allowed_tools: tuple[str, ...] = DEFAULT_TOOLS
    worktree: str | None = None
    max_budget_usd: float | None = None
    output_format: str | None = None
    no_session_persistence: bool = False
    model: str | None = None
    permission_mode: str | None = None
```

#### Method

- `to_args(self) -> list[str]` — Build a subprocess argument list. Always starts with `[CLAUDE_BIN, "--print"]`. Appends flags only when set (non-None / True). The prompt is always the final positional argument. `allowed_tools` is comma-joined. Boolean flags (`no_session_persistence`) are included when `True`.

#### Factory

- `for_story(prompt, *, system_prompt, worktree=None, max_budget_usd=None, model=None, permission_mode=None) -> Invocation` — Build an invocation preset for story implementation. Hardwires `no_session_persistence=True`, `output_format="json"`, and `DEFAULT_TOOLS`. Works for both initial implementation and retry-with-feedback — the only difference is the prompt content.

#### Imports

```python
import dataclasses
```

No imports from `mantle.core` — true leaf module with zero internal dependencies.

#### Design decisions

- **`dataclasses.dataclass`, not Pydantic.** This is a transient command builder, never serialized to YAML or disk. `frozen=True, slots=True` for immutability and memory efficiency. Matches `vault.Note` for in-memory-only data.
- **`for_story()` as a module-level factory, not a classmethod.** Follows Google Python Style Guide preference for module-level functions over classmethods when no `cls` access is needed. Separates construction policy from data definition.
- **`DEFAULT_TOOLS` and `CLAUDE_BIN` as module constants.** Single source of truth. Future config overrides thread through `for_story()` kwargs without changing the constant.
- **No `for_retry()` factory.** Retry is the same invocation with a different prompt. A separate factory would imply structural differences that don't exist.
- **`allowed_tools` defaults to `DEFAULT_TOOLS` on `Invocation`, not empty tuple.** The default is the standard set from the system design pseudocode.

## Tests

### tests/core/test_claude_cli.py (new file)

No fixtures needed — pure data construction.

- **Invocation**: frozen (cannot assign to attributes)
- **Invocation**: default `allowed_tools` is `DEFAULT_TOOLS`
- **Invocation**: default `no_session_persistence` is False
- **Invocation**: default `output_format` is None
- **to_args**: starts with `[CLAUDE_BIN, "--print"]`
- **to_args**: prompt is the last element
- **to_args**: includes `--allowedTools` with comma-joined tools
- **to_args**: includes `--no-session-persistence` when True
- **to_args**: omits `--no-session-persistence` when False
- **to_args**: includes `--worktree` when set
- **to_args**: omits `--worktree` when None
- **to_args**: includes `--system-prompt` when set
- **to_args**: includes `--max-budget-usd` with string representation
- **to_args**: includes `--output-format` when set
- **to_args**: includes `--model` when set
- **to_args**: includes `--permission-mode` when set
- **to_args**: minimal invocation (only prompt, no optional flags except default tools)
- **for_story**: returns Invocation with `no_session_persistence=True`
- **for_story**: returns Invocation with `output_format="json"`
- **for_story**: returns Invocation with `DEFAULT_TOOLS` as `allowed_tools`
- **for_story**: passes `system_prompt` through
- **for_story**: passes optional `worktree` through
- **for_story**: passes optional `model` through
- **for_story**: passes optional `max_budget_usd` through
- **for_story**: passes optional `permission_mode` through