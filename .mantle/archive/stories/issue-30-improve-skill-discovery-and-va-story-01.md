---
issue: 30
title: Tag filtering for list-skills — core function and CLI flag
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer using the build pipeline, I want to filter skills by tag so that I can quickly find skills relevant to a specific topic or domain.

## Depends On

None — independent.

## Approach

Extend the existing list_skills() function with an optional tag parameter, and add a --tag flag to the list-skills CLI command. Follows the existing pattern where core functions accept optional kwargs and CLI commands pass through parameters. The cyclopts framework handles type conversion automatically.

## Implementation

### src/mantle/core/skills.py (modify)

1. **Modify `list_skills()`** — add an optional `tag: str | None = None` keyword argument.
   - When `tag` is None, behaviour is unchanged (return all skills sorted).
   - When `tag` is provided, iterate over the glob results, read each skill's frontmatter via `load_skill()`, and filter to those where the `tag` value is in the skill's `tags` tuple.
   - Catch `NoteParseError` and `NoteValidationError` per skill (skip unparseable files, matching the pattern in `detect_skills_from_content()`).
   - Return the filtered list, still sorted alphabetically.

Signature change:
```python
def list_skills(project_dir: Path, *, tag: str | None = None) -> list[Path]:
```

#### Design decisions

- **Optional kwarg, not a separate function**: Keeps the interface simple. Callers that don't need filtering continue to work unchanged.
- **Filter in the function, not the caller**: The function already has access to vault paths; filtering is a natural extension, not a new responsibility.

### src/mantle/cli/main.py (modify)

2. **Modify `list_skills_command()`** — add a `--tag` parameter.
   - Add a `tag` parameter with `Parameter(name="--tag", help="Filter by tag (e.g., domain/web, topic/python).")`, type `str | None`, default `None`.
   - Pass `tag=tag` to `skills.list_skills()`.
   - When filtering is active and results are empty, print "No skills matching tag '{tag}'." instead of "No skills found in vault."

## Tests

### tests/core/test_skills.py (modify)

- **test_list_skills_no_filter**: Existing test should still pass — verifies all skills returned when no tag is provided.
- **test_list_skills_filter_by_tag**: Create 3 skills with different tags, filter by one tag, assert only matching skills returned.
- **test_list_skills_filter_no_matches**: Filter by a tag no skill has, assert empty list returned.
- **test_list_skills_filter_skips_invalid**: Create a valid skill and a malformed .md file, filter by the valid skill's tag, assert only the valid skill returned (malformed file skipped without error).

### tests/cli/test_main.py (modify)

- **test_list_skills_tag_flag**: Invoke CLI with --tag, verify it passes through to core function and output is filtered.