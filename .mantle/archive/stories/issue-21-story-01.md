---
issue: 21
title: Validate related skill links during add-skill
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

### `src/mantle/core/skills.py`

Add a `validate_related_skills()` function that checks each name in `related_skills` against existing vault skills using the existing `skill_exists()` function.

```python
def validate_related_skills(
    project_dir: Path,
    related_skills: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Check which related skills exist in the vault.

    Returns (existing, missing) tuples of skill names.
    """
```

Add a `create_stub_skill()` function that creates a minimal skill node — just frontmatter and a Context section with a placeholder — so wikilinks resolve without requiring a full authoring session.

```python
def create_stub_skill(
    project_dir: Path,
    name: str,
) -> Path:
    """Create a minimal stub skill node in the vault.

    Stub skills have proficiency 0/10 and a placeholder context section,
    intended to be fleshed out later via /mantle:add-skill.
    """
```

### `claude/commands/mantle/add-skill.md`

Update Step 3 (gather metadata) to call validation after the user provides `related_skills`. When missing skills are detected, present options per missing skill:

1. **Create stub** — create a minimal node so the wikilink resolves
2. **Remove link** — drop it from `related_skills`
3. **Keep anyway** — leave the dangling link (Obsidian will show it as unresolved)

### Design decisions

- **Validation at workflow time, not save time.** The user should see warnings during the interactive session when they can act on them, not as a silent post-save check.
- **Stub creation is opt-in per link.** Don't batch-create stubs for all missing skills — the user may want different actions for different links.
- **Stubs use proficiency 0/10.** Signals "not yet authored" without a separate status field.

## Tests

### tests/core/test_skills.py

- **test_validate_related_skills_all_exist**: All related skills exist in vault — returns all in `existing`, empty `missing`
- **test_validate_related_skills_some_missing**: Mix of existing and non-existent — correctly partitions
- **test_validate_related_skills_empty**: Empty list — returns empty tuples
- **test_create_stub_skill**: Creates a minimal skill file with 0/10 proficiency and placeholder content
- **test_create_stub_skill_already_exists**: Raises error when skill already exists
- **test_create_stub_skill_roundtrip**: Stub can be loaded via `load_skill()` and returns valid SkillNote
