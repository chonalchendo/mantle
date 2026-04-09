---
issue: 31
title: Core inbox module + init integration
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want inbox items persisted to .mantle/inbox/ with structured metadata so that feature ideas are preserved for later triage.

## Depends On

None — independent (foundational module).

## Approach

Follow the bugs.py pattern exactly: pydantic model for frontmatter, CRUD functions using vault.write_note/read_note, status tracking with update function. Add 'inbox' to SUBDIRS in core/project.py so mantle init creates the directory.

## Implementation

### src/mantle/core/inbox.py (new file)

Create a new module following the pattern of core/bugs.py:

**Constants:**
- \`VALID_SOURCES: frozenset[str] = frozenset({"user", "ai"})\`
- \`VALID_STATUSES: frozenset[str] = frozenset({"open", "promoted", "dismissed"})\`

**Data model:**
- \`InboxItem(pydantic.BaseModel, frozen=True)\` with fields:
  - \`date: date\`
  - \`author: str\`
  - \`title: str\`
  - \`source: str\` (default "user")
  - \`status: str\` (default "open")
  - \`tags: tuple[str, ...]\` (default ("type/inbox", "status/open"))

**Public functions:**
- \`save_inbox_item(project_dir, *, title, description="", source="user") -> tuple[InboxItem, Path]\`
  - Validates source against VALID_SOURCES
  - Uses state.resolve_git_identity() for author
  - Computes path as .mantle/inbox/{date}-{slug}.md
  - Writes via vault.write_note with description as body
  - Returns (InboxItem, path)

- \`load_inbox_item(path) -> tuple[InboxItem, str]\`
  - Reads via vault.read_note(path, InboxItem)
  - Returns (frontmatter, body)

- \`list_inbox_items(project_dir, *, status=None) -> list[Path]\`
  - Globs .mantle/inbox/*.md, sorted oldest-first
  - Optional status filter (loads each item to check)

- \`update_inbox_status(project_dir, item_filename, *, status) -> tuple[InboxItem, str]\`
  - Validates status against VALID_STATUSES
  - Reads existing note, updates status and status tag
  - Returns (updated InboxItem, old_status)

**Private helpers:**
- \`_inbox_path(project_dir, date_str, slug) -> Path\`
- \`_slugify(title) -> str\` — same logic as bugs._slugify
- \`_validate_choice(value, valid, label)\` — same as bugs._validate_choice

#### Design decisions

- **No InboxExistsError**: Unlike bugs, same-title items on same day get auto-incremented paths (like challenges). Users may capture similar ideas at different times.
- **Description as body, not frontmatter**: Keeps frontmatter lean. Description is optional free text.
- **No state.md update**: Inbox is fire-and-forget. No state transitions or Current Focus updates.

### src/mantle/core/project.py (modify)

Add \`"inbox"\` to the SUBDIRS tuple (alphabetical order, after "issues").

## Tests

### tests/core/test_inbox.py (new file)

- **test_save_inbox_item_creates_file**: saves item, asserts file exists in .mantle/inbox/ with correct frontmatter
- **test_save_inbox_item_default_source**: source defaults to "user" when not specified
- **test_save_inbox_item_ai_source**: source="ai" is accepted and saved
- **test_save_inbox_item_invalid_source**: raises ValueError for source="web"
- **test_save_inbox_item_with_description**: description appears as body text
- **test_save_inbox_item_empty_description**: empty description produces empty body
- **test_load_inbox_item**: saves then loads, verifies roundtrip
- **test_list_inbox_items_empty**: returns empty list when no items exist
- **test_list_inbox_items_sorted**: multiple items returned oldest-first
- **test_list_inbox_items_status_filter**: status=open filters correctly
- **test_update_inbox_status_promoted**: updates status from open to promoted
- **test_update_inbox_status_dismissed**: updates status from open to dismissed
- **test_update_inbox_status_invalid**: raises ValueError for invalid status
- **test_update_inbox_status_updates_tag**: status tag in tags tuple is updated
- **test_slugify**: title slugified for filename (spaces to hyphens, truncated)
- **test_inbox_subdir_in_subdirs**: "inbox" is in project.SUBDIRS

Fixtures: use tmp_path, create .mantle/inbox/ directory, mock git identity via monkeypatch on state.resolve_git_identity.