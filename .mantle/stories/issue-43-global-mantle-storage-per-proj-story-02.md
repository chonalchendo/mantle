---
issue: 43
title: Update core modules to use resolve_mantle_dir
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer using global storage mode, I want all existing Mantle commands to work identically so that switching storage location is transparent.

## Depends On

Story 1 — needs resolve_mantle_dir() to exist.

## Approach

Mechanical replacement across all core modules: every inline \`project_dir / ".mantle"\` becomes \`project.resolve_mantle_dir(project_dir)\`. Each module imports \`project\` from \`mantle.core\` (following the project convention of importing modules, not names). This is the bulk of the work but is straightforward pattern replacement.

## Implementation

### src/mantle/core/state.py (modify)

- Add \`from mantle.core import project\` import
- Replace \`project_dir / ".mantle"\` with \`project.resolve_mantle_dir(project_dir)\` in \`create_initial_state()\`, \`save_state()\`, \`load_state()\`, and \`transition()\`

### src/mantle/core/stories.py (modify)

- Add \`from mantle.core import project\` import
- Replace all \`project_dir / ".mantle"\` (6 occurrences) with \`project.resolve_mantle_dir(project_dir)\`

### src/mantle/core/issues.py (modify)

- Add \`from mantle.core import project\` import
- Replace all \`project_dir / ".mantle"\` (4 occurrences) with \`project.resolve_mantle_dir(project_dir)\`

### src/mantle/core/system_design.py (modify)

- Add \`from mantle.core import project\` import
- Replace all \`project_dir / ".mantle"\` (5 occurrences) with \`project.resolve_mantle_dir(project_dir)\`

### src/mantle/core/knowledge.py (modify)

- Add \`from mantle.core import project\` import
- Replace all \`project_dir / ".mantle"\` (2 occurrences) with \`project.resolve_mantle_dir(project_dir)\`

### src/mantle/core/brainstorm.py (modify)

- Add \`from mantle.core import project\` import
- Replace all \`project_dir / ".mantle"\` (3 occurrences) with \`project.resolve_mantle_dir(project_dir)\`

### Remaining core modules (modify each)

Apply the same pattern to all other core modules that reference \`".mantle"\`: \`compiler.py\`, \`shaping.py\`, \`skills.py\`, \`learning.py\`, \`product_design.py\`, \`research.py\`, \`review.py\`, \`scout.py\`, \`session.py\`, \`adopt.py\`, \`archive.py\`, \`bugs.py\`, \`challenge.py\`, \`decisions.py\`, \`idea.py\`, \`inbox.py\`.

For each: add \`from mantle.core import project\` to imports, replace inline \`project_dir / ".mantle"\` with \`project.resolve_mantle_dir(project_dir)\`.

**Important**: Also replace uses of the string literal \`".mantle"\` that are used for path construction. Do NOT replace string literals used for display/logging purposes.

#### Design decisions

- **Import module, not function**: Use \`project.resolve_mantle_dir()\` not \`from mantle.core.project import resolve_mantle_dir\` per project conventions.
- **No behavioral changes**: This story only changes path resolution. All logic, return types, and error handling remain identical.
- **tags.py special case**: The \`_TAGS_PATH = ".mantle/tags.md"\` constant should be replaced with a function call since it needs project_dir at runtime, not module load time.

## Tests

### tests/core/test_resolve_integration.py (new file)

- **test_state_uses_resolver**: Create a project with global config, verify state.md is read/written from global path.
- **test_stories_uses_resolver**: Create a project with global config, verify stories are saved to global path.
- **test_issues_uses_resolver**: Create a project with global config, verify issues are read from global path.
- **test_local_mode_unchanged**: Default config, verify all paths still resolve to project_dir/.mantle/ (regression test).