---
issue: 36
title: IssueNote skills_required field and issue-scoped skill matching
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer using /mantle:build, I want issues to declare which skills they need so that only relevant skills are compiled for implementation agents.

## Depends On

None — independent.

## Approach

Extend IssueNote frontmatter with a skills_required field following the same pattern as blocked_by and slice. Then modify _match_required_skills() to accept an optional filter list, and compile_skills() to accept an optional issue number. When an issue is provided, compile_skills reads its skills_required and compiles only those instead of the full state.md list. This is the core data model + compilation change.

## Implementation

### src/mantle/core/issues.py (modify)

Add skills_required field to IssueNote:

\`\`\`python
class IssueNote(pydantic.BaseModel, frozen=True):
    # ... existing fields ...
    skills_required: tuple[str, ...] = ()
\`\`\`

Add it after blocked_by, before tags. Default to empty tuple so existing issues fall back gracefully.

Update save_issue() to accept skills_required parameter:

\`\`\`python
def save_issue(
    project_dir: Path,
    content: str,
    *,
    title: str,
    slice: tuple[str, ...],
    blocked_by: tuple[int, ...] = (),
    skills_required: tuple[str, ...] = (),
    verification: str | None = None,
    issue: int | None = None,
    overwrite: bool = False,
) -> tuple[IssueNote, Path]:
\`\`\`

Pass skills_required to IssueNote constructor.

### src/mantle/core/skills.py (modify)

1. Modify _match_required_skills to accept an optional filter list:

\`\`\`python
def _match_required_skills(
    project_dir: Path,
    skills_filter: tuple[str, ...] = (),
) -> list[tuple[str, Path | None]]:
    if skills_filter:
        required = skills_filter
    else:
        current_state = state.load_state(project_dir)
        required = current_state.skills_required
    if not required:
        return []
    existing = list_skills(project_dir)
    return [(name, _match_skill_slug(name, existing)) for name in required]
\`\`\`

2. Modify compile_skills to accept optional issue number:

\`\`\`python
def compile_skills(
    project_dir: Path,
    issue: int | None = None,
) -> list[str]:
\`\`\`

When issue is provided, load the issue file via issues.find_issue_path + issues.load_issue, read its skills_required. If non-empty, pass it to _match_required_skills as skills_filter. If empty, fall back to state.md (current behavior).

Import issues at the top of the function body (not module level) to avoid circular imports since issues.py already imports from core.

3. Update auto_update_skills to also write detected skills into issue frontmatter:

After detecting skills and updating state.md, also update the issue file:
- Re-read the issue
- Merge detected skills into the issue's existing skills_required
- Write back using vault.write_note with updated frontmatter

#### Design decisions

- **skills_filter param on _match_required_skills**: Cleaner than threading issue everywhere — callers that don't need scoping pass nothing.
- **Late import of issues in compile_skills**: Avoids circular import (issues imports state, skills imports state — adding skills importing issues at module level risks cycles).
- **Empty tuple = fallback**: Existing issues without skills_required get the full state.md list, preserving backward compatibility.

## Tests

### tests/core/test_skills.py (modify)

- **test_compile_skills_with_issue_scoped_skills**: Create an issue with skills_required=(skill-a, skill-b), create vault skills a/b/c. Call compile_skills(project_dir, issue=N). Assert only a and b are compiled, not c.
- **test_compile_skills_issue_empty_falls_back**: Create an issue with skills_required=(). Call compile_skills with issue number. Assert it falls back to state.md skills_required.
- **test_compile_skills_no_issue_uses_state**: Call compile_skills without issue param. Assert it uses state.md skills_required (existing behavior preserved).
- **test_match_required_skills_with_filter**: Call _match_required_skills with explicit skills_filter. Assert only filtered skills are matched.
- **test_auto_update_skills_writes_to_issue**: Run auto_update_skills. Assert the issue file's skills_required frontmatter is updated with detected skills.

### tests/core/test_issues.py (modify)

- **test_issue_note_skills_required_default**: Create IssueNote without skills_required. Assert it defaults to empty tuple.
- **test_save_issue_with_skills_required**: Save an issue with skills_required=(cyclopts,). Read it back. Assert skills_required is preserved in frontmatter.