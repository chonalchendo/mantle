---
issue: 32
title: CLI knowledge commands — save-distillation, list-distillations, load-distillation
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer, I want CLI subcommands to save, list, and load distillation notes so that prompt files can invoke them via Bash tool.

## Depends On

Story 1 (core knowledge module provides the functions this CLI wires).

## Approach

Follow the cli/brainstorm.py pattern: thin CLI wrapper that imports core/knowledge and calls its functions. Register three new commands in cli/main.py following the existing cyclopts pattern. Import the module, not individual functions (per CLAUDE.md conventions).

## Implementation

### src/mantle/cli/knowledge.py (new file)

Create a new module following the pattern of cli/brainstorm.py:

**Imports (module-level, not individual names):**
- \`from mantle.core import knowledge\`
- \`from pathlib import Path\`
- \`from rich.console import Console\`

**Functions:**

- \`run_save_distillation(*, topic, source_paths, content, project_dir=None) -> None\`
  - Calls knowledge.save_distillation(project_dir, content, topic=topic, source_paths=tuple(source_paths))
  - Prints confirmation: topic, source_count, saved path
  - Catches ValueError and exits with error message

- \`run_list_distillations(*, topic=None, project_dir=None) -> None\`
  - Calls knowledge.list_distillations(project_dir, topic=topic)
  - Prints count and list of distillation filenames with topics
  - If topic filter provided, shows "filtered by: {topic}"

- \`run_load_distillation(*, path, project_dir=None) -> None\`
  - Calls knowledge.load_distillation(Path(path))
  - Prints frontmatter fields and body content
  - Used by query/distill prompts to read existing distillations

### src/mantle/cli/main.py (modify)

**Import** (add to existing import block, alphabetical):
- Add \`knowledge\` to the import list from \`mantle.cli\`

**Register three new commands** following the save-brainstorm pattern:

- \`@app.command(name="save-distillation")\` with parameters:
  - \`--topic\`: str (required) — distillation topic
  - \`--source-paths\`: list[str] (required, multiple) — paths to source notes
  - \`--content\`: str (required) — distillation body text
  - \`--path\`: str | None = None — project directory override
  - Calls knowledge.run_save_distillation(...)

- \`@app.command(name="list-distillations")\` with parameters:
  - \`--topic\`: str | None = None — optional topic filter
  - \`--path\`: str | None = None — project directory override
  - Calls knowledge.run_list_distillations(...)

- \`@app.command(name="load-distillation")\` with parameters:
  - \`--path\`: str (required) — path to distillation file
  - Calls knowledge.run_load_distillation(...)

#### Design decisions

- **Three separate commands**: Follows "one command, one job" principle. Each has a clear purpose: save, list, load.
- **source_paths as multiple flag**: \`--source-paths ".mantle/learnings/x.md" --source-paths ".mantle/skills/y.md"\` — cyclopts handles list collection.
- **load-distillation takes --path not --topic**: Deterministic lookup by path. The prompt uses list-distillations to find the right path first.

## Tests

### tests/cli/test_knowledge.py (new file)

- **test_save_distillation_command**: invokes save-distillation with valid args, asserts file created and confirmation printed
- **test_save_distillation_command_invalid**: missing required --topic, asserts error
- **test_list_distillations_command_empty**: no distillations, prints "0 distillation(s)"
- **test_list_distillations_command_with_items**: saves two distillations, lists both
- **test_list_distillations_command_topic_filter**: filters by topic substring
- **test_load_distillation_command**: saves then loads, prints frontmatter and body

Fixtures: use tmp_path, create .mantle/distillations/ directory, mock git identity. Use capsys or rich Console capture for output assertions.