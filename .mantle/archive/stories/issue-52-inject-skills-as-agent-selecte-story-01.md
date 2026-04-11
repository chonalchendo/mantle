---
issue: 52
title: Core SkillSummary model and enriched list-skills CLI output
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer shaping an issue, I want `mantle list-skills` to show skill descriptions alongside slugs so that I can identify which skills are relevant without reading each file.

## Depends On

None — independent.

## Approach

Add a lightweight `SkillSummary` model and a `list_skill_summaries()` function to `core/skills.py`, following the existing `list_skills()` pattern. Then update the `list_skills_command` in `cli/main.py` to use the new function and print descriptions by default. This is the foundation story — prompt changes in later stories depend on this enriched output.

## Implementation

### src/mantle/core/skills.py (modify)

Add after the existing `SkillNote` class (~line 98):

```python
class SkillSummary(pydantic.BaseModel, frozen=True):
    """Lightweight skill descriptor for selection UIs."""
    slug: str
    description: str
```

Add after the existing `list_skills()` function (~line 390):

```python
def list_skill_summaries(
    project_dir: Path,
    *,
    tag: str | None = None,
) -> list[SkillSummary]:
    """Return slug and description for all vault skills.

    Args:
        project_dir: Directory containing .mantle/.
        tag: Optional tag to filter by.

    Returns:
        Alphabetically sorted list of SkillSummary.

    Raises:
        VaultNotConfiguredError: If personal vault is not configured.
    """
    paths = list_skills(project_dir, tag=tag)
    summaries: list[SkillSummary] = []
    for path in paths:
        try:
            note, _ = load_skill(path)
        except (vault.NoteParseError, vault.NoteValidationError):
            continue
        summaries.append(SkillSummary(slug=path.stem, description=note.description))
    return summaries
```

#### Design decisions

- **Reuses `list_skills()` internally**: avoids duplicating path resolution and glob logic.
- **Silently skips unparseable skills**: follows the existing pattern in `list_skills()` with tag filtering.
- **Separate function, not modifying `list_skills()`**: existing callers that need `list[Path]` are unaffected — no change amplification.

### src/mantle/cli/main.py (modify)

Update `list_skills_command` (~line 1025) to use `list_skill_summaries` instead of `list_skills`. Replace the current loop:

```python
# Before:
skill_paths = skills.list_skills(path, tag=tag)
# ...
print(f"{len(skill_paths)} skill(s) in vault:")
for p in skill_paths:
    print(f"  - {p.stem}")

# After:
summaries = skills.list_skill_summaries(path, tag=tag)
# ...
print(f"{len(summaries)} skill(s) in vault:")
for s in summaries:
    print(f"  - {s.slug} — {s.description}")
```

Keep the existing error handling for `VaultNotConfiguredError` and `FileNotFoundError`. Keep the existing empty-case handling (tag vs no-tag messages).

#### Design decisions

- **Descriptions shown by default, not behind `--verbose`**: the common case is wanting to know what a skill is. Follows "general-purpose interfaces" principle from software-design-principles skill.
- **Output format `  - {slug} — {description}`**: one line per skill, parseable, consistent with the existing indented list format.

## Tests

### tests/core/test_skills.py (modify)

Add a new test class `TestListSkillSummaries` after the existing `TestListSkills` class. Use the existing `_create_skill` helper and `project` / `project_no_vault` fixtures:

- **test_empty_when_no_skills**: `list_skill_summaries(project)` returns empty list
- **test_returns_sorted_summaries**: create two skills ("Zsh scripting", "Docker compose"), verify returned summaries are sorted alphabetically by slug (`docker-compose`, `zsh-scripting`) and descriptions match
- **test_raises_vault_not_configured**: raises `VaultNotConfiguredError` when called with `project_no_vault`
- **test_filter_by_tag**: create skills with different tags, verify tag filtering returns only matching skills with correct descriptions
- **test_skips_invalid_skill_files**: create a valid skill plus a broken .md file, verify only valid skill appears in results

### tests/cli/test_skills.py (modify)

Update or add tests in the existing CLI skills test class:

- **test_list_skills_shows_descriptions**: create a skill, run `list_skills_command`, capture stdout, verify output contains `slug — description` format
- **test_list_skills_with_tag_shows_descriptions**: verify tag filtering works with the new output format