---
issue: 45
title: Add archive scan to next_issue_number
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle user who archives completed issues, I want new issue numbers to be globally unique across active and archived so that my history and git log stay unambiguous.

## Depends On

None — independent (single-story issue).

## Approach

Modify `next_issue_number` in `src/mantle/core/issues.py` to also scan `.mantle/archive/issues/` when computing the highest existing issue number. Follow the existing glob + regex pattern used for the active directory. Leave `list_issues` and `count_issues` untouched because they serve the "active backlog" semantics used by status displays. Add 3 unit tests to the existing `TestNextIssueNumber` class in `tests/core/test_issues.py`.

## Implementation

### src/mantle/core/issues.py (modify)

Update the `next_issue_number(project_dir: Path) -> int` function (currently lines 172-190):

1. Keep the existing active-directory scan via `list_issues(project_dir)` intact.
2. After the active scan, also glob `.mantle/archive/issues/issue-*.md` and update `highest = max(highest, ...)` for each match.
3. Resolve the archive directory as:
   ```python
   archive_dir = project.resolve_mantle_dir(project_dir) / "archive" / "issues"
   ```
4. If `archive_dir` does not exist, skip the archive scan silently (projects without archives must still work).
5. Use the same `re.compile(r"issue-(\d+)-.*\.md")` pattern that the active scan already uses. A single compiled regex shared across both scans is cleanest.
6. Update the Google-style docstring to mention that both active and archived issues are considered when computing the max.

Pseudocode of the final function:

```python
def next_issue_number(project_dir: Path) -> int:
    \"\"\"Return the next issue number (highest existing + 1).

    Scans both .mantle/issues/ and .mantle/archive/issues/ for
    issue-NN-*.md files and returns max(NN) + 1 across both. This
    ensures archived issue numbers are never reused.

    Returns 1 if no issues exist in either directory.
    \"\"\"
    pattern = re.compile(r\"issue-(\\d+)-.*\\.md\")
    highest = 0

    # Active issues
    for path in list_issues(project_dir):
        match = pattern.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))

    # Archived issues
    archive_dir = (
        project.resolve_mantle_dir(project_dir) / \"archive\" / \"issues\"
    )
    if archive_dir.is_dir():
        for path in sorted(archive_dir.glob(\"issue-*.md\")):
            match = pattern.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))

    return highest + 1
```

#### Design decisions

- **Inline archive scan, not a new helper**: there is exactly one caller (`next_issue_number`). Introducing a helper for one caller is YAGNI. If a second caller ever needs archive-inclusive numbering, extract at that point.
- **Do NOT modify `list_issues`**: it has a second caller (`count_issues` at line 215) which powers "active issue count" in status displays. Changing `list_issues` would corrupt that meaning.
- **Silent skip if archive dir missing**: projects without any archived issues must still work. `is_dir()` guard mirrors the existing `is_dir()` check in `list_issues` (line 167).
- **Reuse the existing regex**: single compiled `re.compile(r\"issue-(\\d+)-.*\\.md\")` shared across both passes. This intentionally preserves the pre-existing behaviour of ignoring old numeric-only files like `issue-01.md` (no slug) — fixing that regex is out of scope.
- **Imports**: `project` is already imported at the top of `issues.py` (used at line 166). No new imports needed.

## Tests

### tests/core/test_issues.py (modify)

Add 3 new test methods to the existing `TestNextIssueNumber` class (currently ends at line 398). A small helper should be added to the test module (or inline in each test) to create archived issue files without routing through `save_issue`:

```python
def _create_archived_issue(project_dir: Path, number: int, slug: str = \"archived-work\") -> None:
    \"\"\"Create a fake archived issue file directly.\"\"\"
    archive_dir = project_dir / \".mantle\" / \"archive\" / \"issues\"
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / f\"issue-{number:02d}-{slug}.md\").write_text(\"---\\ntitle: x\\n---\\n\")
```

New test cases in `TestNextIssueNumber`:

- **test_scans_archive_when_computing_max**: Setup — active issues [40, 41] (via `_save`) and an archived issue-43 (via helper). Assertion — `next_issue_number(project) == 44`. This is the primary regression test and matches the exact scenario from the issue description.

- **test_returns_max_plus_1_when_only_archive_has_issues**: Setup — no active issues, archive has issues [1, 2, 3]. Assertion — `next_issue_number(project) == 4`. Covers the edge case where the active directory is empty but the archive is not.

- **test_works_when_archive_dir_missing**: Setup — only active issues [1, 2], no archive directory on disk at all. Assertion — `next_issue_number(project) == 3`. Regression test ensuring existing behaviour is preserved for projects that never archived anything.

### Test fixture requirements

- Use the existing `project` fixture (already creates `tmp_path/.mantle/issues/`).
- The `_create_archived_issue` helper handles archive directory creation lazily via `mkdir(parents=True, exist_ok=True)`.
- Use the existing `@patch(\"mantle.core.issues.state.resolve_git_identity\", side_effect=_mock_git_identity)` decorator for tests that call `_save` (the first two tests — the third doesn't call `_save` only indirectly via helper that writes files directly).
- No mocks for filesystem — real `tmp_path` only, per project test conventions (CLAUDE.md).