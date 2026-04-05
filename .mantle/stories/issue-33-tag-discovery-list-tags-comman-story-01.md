---
issue: 33
title: Core tag collection — collect_all_tags with source merging
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As an LLM, I want a core function that collects all tags from both the taxonomy file and vault skill frontmatter so that I can discover the full tag landscape.

## Depends On

None — independent.

## Approach

Extend `core/tags.py` with a `TagSummary` dataclass and `collect_all_tags()` function. Follows the pattern of existing `load_tags()` — reads from filesystem, returns structured data. Uses `skills.list_skills()` and `skills.load_skill()` for vault scanning, and existing `_section_for_tag()` for prefix grouping.

## Implementation

### `src/mantle/core/tags.py` (modify)

Add a `TagSummary` dataclass:

```python
@dataclasses.dataclass(frozen=True)
class TagSummary:
    """Result of collecting tags from all sources.

    Attributes:
        taxonomy: Tags declared in .mantle/tags.md.
        vault: Tags found in vault skill frontmatter.
        undeclared: Tags in vault but not in taxonomy.
        by_prefix: All tags grouped by prefix (e.g. "Topic" -> ["topic/python"]).
    """
    taxonomy: frozenset[str]
    vault: frozenset[str]
    undeclared: frozenset[str]
    by_prefix: dict[str, tuple[str, ...]]
```

Add `collect_all_tags()`:

```python
def collect_all_tags(project_dir: Path) -> TagSummary:
    """Collect tags from taxonomy file and vault skill frontmatter.

    Merges tags from `.mantle/tags.md` (the declared taxonomy) with
    tags extracted from all vault skill frontmatter. Computes which
    vault tags are undeclared (present in skills but not in taxonomy)
    and groups all tags by prefix.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        TagSummary with taxonomy, vault, undeclared, and grouped tags.
    """
```

Implementation:
1. Call `load_tags(project_dir)` for taxonomy tags
2. Import `skills` module at function level to avoid circular imports: `from mantle.core import skills`
3. Try `skills.list_skills(project_dir)` — if `VaultNotConfiguredError`, use empty set for vault tags
4. For each skill path, call `skills.load_skill(path)` and collect `note.tags`, silently skip `NoteParseError`/`NoteValidationError`
5. Compute `undeclared = vault_tags - taxonomy_tags`
6. Merge all tags (`taxonomy | vault`), group by prefix using `_section_for_tag()`
7. Sort tags within each group alphabetically, sort groups alphabetically
8. Return `TagSummary`

#### Design decisions

- **`frozenset` for immutable collections.** TagSummary is a read-only result — immutable types prevent accidental mutation.
- **Function-level import for skills.** Avoids circular import since `skills.py` already imports from other core modules. The import happens once per call, which is fine for a CLI command.
- **Silent skip on parse errors.** Matches existing `list_skills(tag=...)` behaviour — unparseable skills don't block tag discovery.

## Tests

### `tests/core/test_tags.py` (modify)

Add a `vault_project` fixture that creates `.mantle/tags.md` + a `config.yaml` with `personal_vault` pointing to a temp vault dir + skill files with various tags.

- **test_collect_all_tags_merges_sources**: Taxonomy has `type/skill`, `domain/web`; vault skill has `topic/python`, `domain/web`. Result includes all tags, `undeclared` contains `topic/python`.
- **test_collect_all_tags_groups_by_prefix**: Tags are grouped correctly — `topic/python` under "Topic", `domain/web` under "Domain", `type/skill` under "Type".
- **test_collect_all_tags_no_vault**: No personal vault configured — returns taxonomy tags only, empty vault set.
- **test_collect_all_tags_no_taxonomy_file**: No tags.md — returns vault tags only, all vault tags are undeclared.
- **test_collect_all_tags_empty**: No tags.md and no vault — returns empty TagSummary.
- **test_collect_all_tags_skips_unparseable_skills**: Malformed skill file in vault is silently skipped, other skills are still collected.