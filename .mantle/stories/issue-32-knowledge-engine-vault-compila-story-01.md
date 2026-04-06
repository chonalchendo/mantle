---
issue: 32
title: Core knowledge module — DistillationNote, save, load, list
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want distillation notes persisted to .mantle/distillations/ with structured metadata so that synthesized knowledge is retrievable and trackable for staleness.

## Depends On

None — independent (foundational module).

## Approach

Follow the brainstorm.py pattern exactly: Pydantic model for frontmatter, CRUD functions using vault.write_note/read_note, auto-increment paths for same-day collisions. Add 'distillations' to SUBDIRS in core/project.py so mantle init creates the directory.

## Implementation

### src/mantle/core/knowledge.py (new file)

Create a new module following the pattern of core/brainstorm.py:

**Imports (module-level, not individual names):**
- \`from mantle.core import sanitize, state, vault\`
- Standard library: \`re\`, \`datetime.date\`, \`pydantic\`, \`typing.TYPE_CHECKING\`

**Data model:**
- \`DistillationNote(pydantic.BaseModel, frozen=True)\` with fields:
  - \`topic: str\` — the distillation subject
  - \`date: date\` — date saved
  - \`author: str\` — git email
  - \`source_count: int\` — number of source notes synthesized
  - \`source_paths: tuple[str, ...]\` — relative paths to source notes
  - \`tags: tuple[str, ...]\` (default ("type/distillation",))

**Public functions:**
- \`save_distillation(project_dir, content, *, topic, source_paths) -> tuple[DistillationNote, Path]\`
  - Uses state.resolve_git_identity() for author
  - Computes source_count from len(source_paths)
  - Computes path as .mantle/distillations/{date}-{slug}.md
  - Auto-increments filename on same-day same-slug collision (-2, -3, ...)
  - Writes via vault.write_note with content as body
  - Returns (DistillationNote, path)

- \`load_distillation(path) -> tuple[DistillationNote, str]\`
  - Reads via vault.read_note(path, DistillationNote)
  - Returns (frontmatter, body)

- \`list_distillations(project_dir, *, topic=None) -> list[Path]\`
  - Globs .mantle/distillations/*.md, sorted oldest-first
  - Optional topic filter (loads each item to check, case-insensitive substring match)

- \`find_distillation_by_topic(project_dir, topic) -> Path | None\`
  - Returns most recent distillation matching topic (exact match, case-insensitive), or None
  - Used by query prompt to check for existing distillation before searching raw content

**Private helpers:**
- \`_slugify(title: str) -> str\` — lowercase, non-alphanumeric to hyphens, truncate to 40 chars (same logic as brainstorm._slugify)
- \`_resolve_distillation_path(project_dir, topic) -> Path\` — auto-increment on collision

#### Design decisions

- **source_paths as tuple[str, ...]**: Relative paths (e.g., ".mantle/learnings/issue-27.md") stored in frontmatter. The distill prompt builds wikilinks from these in the body.
- **source_count in frontmatter**: Enables staleness detection — future distillation can check if source count changed since last run.
- **No state.md update**: Distillations are reference artifacts, not workflow state transitions.
- **Topic filter on list**: Supports query prompt checking "do I have a distillation on X already?"

### src/mantle/core/project.py (modify)

Add \`"distillations"\` to the SUBDIRS tuple (alphabetical order, after "decisions").

## Tests

### tests/core/test_knowledge.py (new file)

- **test_save_distillation_creates_file**: saves distillation, asserts file exists in .mantle/distillations/ with correct frontmatter
- **test_save_distillation_source_count**: source_count equals len(source_paths)
- **test_save_distillation_source_paths_stored**: source_paths roundtrips correctly in frontmatter
- **test_save_distillation_auto_increment**: two saves with same topic on same day produce -2 suffix
- **test_load_distillation**: saves then loads, verifies roundtrip of frontmatter and body
- **test_list_distillations_empty**: returns empty list when no distillations exist
- **test_list_distillations_sorted**: multiple distillations returned oldest-first
- **test_list_distillations_topic_filter**: topic filter matches case-insensitively
- **test_find_distillation_by_topic_found**: returns most recent matching path
- **test_find_distillation_by_topic_not_found**: returns None when no match
- **test_slugify**: topic slugified for filename
- **test_distillations_subdir_in_subdirs**: "distillations" is in project.SUBDIRS

Fixtures: use tmp_path, create .mantle/distillations/ directory, mock git identity via monkeypatch on state.resolve_git_identity.