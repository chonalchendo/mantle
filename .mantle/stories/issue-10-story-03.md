---
issue: 10
title: SessionStart hook, install integration, and auto-display
status: done
failure_log: null
tags:
  - type/story
  - status/done
---

## Implementation

Create the SessionStart hook script that compiles context and auto-displays the project briefing on session start. Update the install command to copy hooks and register the hook in Claude Code's `settings.json`. The hook is a no-op when not in a Mantle project directory.

### claude/hooks/session-start.sh (new file)

Shell script executed by Claude Code's SessionStart hook. Runs `mantle compile --if-stale` then outputs the compiled `resume.md` briefing to stdout (which Claude Code injects into the session context).

```bash
#!/usr/bin/env bash
# Mantle SessionStart hook — compile context and auto-display briefing.
# No-op when not in a Mantle project directory.

set -euo pipefail

# Only run in directories with .mantle/
if [ ! -d ".mantle" ]; then
    exit 0
fi

# Compile templates if vault state has changed (stderr for progress)
mantle compile --if-stale >/dev/null 2>&1 || true

# Auto-display the compiled briefing
RESUME_PATH="$HOME/.claude/commands/mantle/resume.md"
if [ -f "$RESUME_PATH" ]; then
    cat "$RESUME_PATH"
fi
```

#### Design decisions

- **Silent compilation.** `mantle compile --if-stale` output goes to `/dev/null`. The user doesn't need to see "Already up to date" or "Compiled 2 templates" on every session start. The briefing itself is the visible output.
- **`|| true` on compile.** If compilation fails (e.g., corrupted state.md, mantle not installed), the hook exits cleanly rather than printing an error to the session context. Fail silently — the user can run `/mantle:resume` manually to diagnose.
- **Check for `.mantle/` directory.** The hook must be a no-op when the user opens Claude Code in a non-Mantle directory (e.g., a quick script project). Only projects with `.mantle/` get auto-briefing.
- **Cat resume.md to stdout.** Claude Code captures hook stdout and injects it into the session context. This is the auto-display mechanism — no special API needed.

### src/mantle/cli/install.py (modify)

#### Modify `run_install()`

After copying files to `~/.claude/`, register the SessionStart hook in `~/.claude/settings.json`. Add a call to a new function `_register_hooks()` after the existing file copy logic.

#### New function

- `_register_hooks(target_dir: Path) -> bool` — Read `~/.claude/settings.json` (create if missing), merge Mantle's hook configuration, write back. Returns `True` if settings were modified, `False` if already registered.

The hook registration adds this structure to `settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

Implementation approach:

1. Read existing `settings.json` if it exists, otherwise start with empty dict.
2. Ensure `hooks` key exists (dict).
3. Ensure `hooks.SessionStart` key exists (list).
4. Check if Mantle's hook is already registered by looking for `session-start.sh` in existing hook commands. If found, skip (idempotent).
5. If not found, append the hook entry.
6. Write `settings.json` back with `json.dump(indent=2)`.

#### Modify `_print_summary()`

Update the summary to mention hook registration when applicable. Add a line like:

```
SessionStart hook registered in ~/.claude/settings.json
```

#### Design decisions

- **Merge, not overwrite.** `settings.json` may contain user-configured hooks, permissions, and other settings. Reading → merging → writing preserves everything. This matches the system design requirement: "Hook registrations (merged, not overwritten)."
- **Idempotent registration.** Running `mantle install --global` multiple times should not create duplicate hook entries. The check for `session-start.sh` in existing commands prevents duplicates.
- **`$HOME` not `~`.** In the hook command string, `$HOME` is used instead of `~` because `~` expansion is shell-dependent and may not work in all contexts where Claude Code executes hooks.
- **`bash` prefix.** Explicitly invoke via `bash` rather than relying on the script's shebang, since the execute permission may not be set after file copy.

### src/mantle/cli/install.py (imports)

Add `json` to imports:

```python
import json
```

## Tests

### tests/cli/test_install.py (modify)

Extend existing install tests. Use `tmp_path` as `~/.claude/` stand-in.

- **register_hooks**: creates `settings.json` when it doesn't exist
- **register_hooks**: preserves existing settings when merging hooks
- **register_hooks**: adds SessionStart hook configuration
- **register_hooks**: idempotent — running twice doesn't create duplicate hooks
- **register_hooks**: preserves other hook types (e.g., existing PreToolUse hooks)
- **register_hooks**: returns True when hook was newly registered
- **register_hooks**: returns False when hook already exists

### tests/hooks/test_session_start.sh (new file — bash test)

Simple bash tests for the hook script behaviour. These can be run via pytest using `subprocess.run`.

- **session-start.sh**: exits 0 when no `.mantle/` directory (no-op)
- **session-start.sh**: exits 0 when `.mantle/` exists (success path)
- **session-start.sh**: outputs resume.md content when file exists
- **session-start.sh**: produces no output when resume.md is missing
