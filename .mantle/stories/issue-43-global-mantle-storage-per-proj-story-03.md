---
issue: 43
title: Migration logic — migrate between local and global storage
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer with an existing in-repo .mantle/, I want a migration command that moves my context to global storage so that I can switch without manual file shuffling.

## Depends On

Story 1 — needs resolve_mantle_dir() and project_identity().

## Approach

New \`core/migration.py\` module with two functions: \`migrate_to_global()\` copies .mantle/ contents to \`~/.mantle/projects/<identity>/\`, updates config, and optionally removes the local copy. \`migrate_to_local()\` does the reverse. Both are atomic — they verify the target before removing the source.

## Implementation

### src/mantle/core/migration.py (new file)

1. **\`migrate_to_global(project_dir: Path, *, remove_local: bool = True) -> Path\`**
   - Compute identity via \`project.project_identity(project_dir)\`
   - Target: \`Path.home() / ".mantle" / "projects" / identity\`
   - If target already exists, raise \`FileExistsError\`
   - Copy \`project_dir / ".mantle"\` to target using \`shutil.copytree\`
   - Update config in the NEW location: set \`storage_mode: global\`
   - If \`remove_local\`, remove the old \`.mantle/\` directory BUT leave a minimal \`.mantle/config.md\` with \`storage_mode: global\` so \`resolve_mantle_dir()\` can find the global path
   - Return the target path

2. **\`migrate_to_local(project_dir: Path, *, remove_global: bool = True) -> Path\`**
   - Read current config to find global path
   - Target: \`project_dir / ".mantle"\`
   - Copy global contents to local
   - Update config: set \`storage_mode: local\`
   - If \`remove_global\`, remove the global directory
   - Return the local path

#### Design decisions

- **Leave stub config.md**: After migrating to global, a minimal \`.mantle/config.md\` with \`storage_mode: global\` remains in-repo. This is the breadcrumb that \`resolve_mantle_dir()\` follows to find global storage. Without it, the resolver has no way to know global mode is active.
- **Copy-then-remove**: Not rename/move, because source and target may be on different filesystems (repo on external drive, home on internal).
- **No partial migration**: All contents move together. Mixed mode is out of scope.

## Tests

### tests/core/test_migration.py (new file)

- **test_migrate_to_global_creates_target**: Verify files are copied to global path.
- **test_migrate_to_global_updates_config**: Verify config at global path has \`storage_mode: global\`.
- **test_migrate_to_global_leaves_stub**: Verify local \`.mantle/config.md\` remains with \`storage_mode: global\`.
- **test_migrate_to_global_removes_local_contents**: Verify local .mantle/ only has config.md after migration.
- **test_migrate_to_global_target_exists_raises**: Verify FileExistsError if target already exists.
- **test_migrate_to_local_copies_back**: Verify files are restored to local path.
- **test_migrate_to_local_updates_config**: Verify config has \`storage_mode: local\` after migration.
- **test_migrate_to_local_removes_global**: Verify global directory removed after migration.
- **test_roundtrip**: Migrate to global then back to local, verify contents match.