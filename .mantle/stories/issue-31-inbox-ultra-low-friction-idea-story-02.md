---
issue: 31
title: CLI commands + main.py wiring
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer, I want CLI commands to save and update inbox items so that I can capture ideas from the terminal without editing files manually.

## Depends On

Story 1 — imports core/inbox.py functions.

## Approach

Follow the cli/bugs.py pattern: thin wrapper functions with rich console output, wired into cli/main.py as cyclopts commands. Two commands: save-inbox-item and update-inbox-status.

## Implementation

### src/mantle/cli/inbox.py (new file)

Create a thin CLI wrapper module following cli/bugs.py:

**\`run_save_inbox_item(*, title, description="", source="user", project_dir=None)\`:**
- Defaults project_dir to Path.cwd()
- Calls inbox.save_inbox_item(project_dir, title=title, description=description, source=source)
- Catches ValueError (invalid source) → prints error, raises SystemExit(1)
- On success: prints confirmation with title, source, and filename

**\`run_update_inbox_status(*, item, status, project_dir=None)\`:**
- Defaults project_dir to Path.cwd()
- Calls inbox.update_inbox_status(project_dir, item, status=status)
- Catches FileNotFoundError → prints error, raises SystemExit(1)
- Catches ValueError (invalid status) → prints error, raises SystemExit(1)
- On success: prints "Item updated: {filename}" with old → new status

### src/mantle/cli/main.py (modify)

1. Add \`inbox\` to the import block (alphabetical, after \`init_vault\`):
   \`\`\`python
   from mantle.cli import (
       ...
       inbox,
       ...
   )
   \`\`\`

2. Add two new commands after the existing bug commands:

**\`@app.command(name="save-inbox-item")\`:**
- Parameters: --title (str, required), --description (str, default ""), --source (str, default "user"), --path (Path, optional)
- Calls inbox.run_save_inbox_item(...)
- Docstring: "Save an idea to .mantle/inbox/."

**\`@app.command(name="update-inbox-status")\`:**
- Parameters: --item (str, required), --status (str, required), --path (Path, optional)
- Calls inbox.run_update_inbox_status(...)
- Docstring: "Update an inbox item's status."

Follow the exact cyclopts Annotated[str, Parameter(...)] pattern used by save-bug and update-bug-status commands.

#### Design decisions

- **Two separate commands** rather than one with subcommands: matches the bug pattern (save-bug, update-bug-status)
- **--path not --project-dir**: matches existing CLI convention for project directory override

## Tests

### tests/cli/test_inbox.py (new file)

- **test_run_save_inbox_item_success**: calls run_save_inbox_item, verifies file created and console output
- **test_run_save_inbox_item_invalid_source**: raises SystemExit(1) on invalid source
- **test_run_update_inbox_status_success**: saves item, then updates status, verifies console output
- **test_run_update_inbox_status_not_found**: raises SystemExit(1) when item doesn't exist
- **test_run_update_inbox_status_invalid_status**: raises SystemExit(1) on invalid status
- **test_save_inbox_item_command_exists**: verifies "save-inbox-item" is registered in app
- **test_update_inbox_status_command_exists**: verifies "update-inbox-status" is registered in app

Fixtures: use tmp_path, create .mantle/inbox/ directory and minimal .mantle/state.md, monkeypatch git identity.