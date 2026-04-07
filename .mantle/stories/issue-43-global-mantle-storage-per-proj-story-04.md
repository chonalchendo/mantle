---
issue: 43
title: CLI commands — mantle storage and mantle migrate-storage
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want CLI commands to configure storage mode and migrate between local and global so that I can manage my storage preference easily.

## Depends On

Story 1 and Story 3 — needs resolver functions and migration logic.

## Approach

New \`cli/storage.py\` module with two cyclopts subcommands registered on the main app. Follows the thin CLI pattern: validate inputs, call core functions, format output. Register commands in \`cli/main.py\`.

## Implementation

### src/mantle/cli/storage.py (new file)

1. **\`storage(mode: str, *, project_dir: Path | None = None) -> None\`**
   - Validate mode is "global" or "local"
   - Read current config, check current mode
   - If already in requested mode, print message and return
   - Update config \`storage_mode\` via \`project.update_config()\`
   - Print confirmation: "Storage mode set to {mode}. Run \`mantle migrate-storage\` to move existing files."

2. **\`migrate_storage(direction: str, *, project_dir: Path | None = None) -> None\`**
   - Validate direction is "global" or "local"
   - Call \`migration.migrate_to_global()\` or \`migration.migrate_to_local()\`
   - Print result with path: "Migrated to {direction} storage: {path}"
   - On error, print error message and exit with code 1

### src/mantle/cli/main.py (modify)

- Import and register the storage subcommands from \`cli/storage.py\`
- Add \`storage\` and \`migrate-storage\` to the app

#### Design decisions

- **Two separate commands**: \`storage\` configures, \`migrate-storage\` moves files. Separation prevents accidental data movement when just checking/setting config.
- **Direction parameter**: Uses "global"/"local" as the argument value, matching the config values for consistency.

## Tests

### tests/cli/test_storage.py (new file)

- **test_storage_set_global**: Verify config updated to global mode.
- **test_storage_set_local**: Verify config updated to local mode.
- **test_storage_already_set**: Verify idempotent message when mode matches.
- **test_migrate_storage_global**: Verify migration runs and prints success.
- **test_migrate_storage_local**: Verify reverse migration works.
- **test_migrate_storage_error**: Verify error handling when migration fails.