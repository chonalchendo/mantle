---
issue: 33
title: CLI list-tags command and claude-code help update
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As an LLM, I want a `mantle list-tags` CLI command that prints grouped tags so that I can discover available tags and then filter skills by tag.

## Depends On

Story 1 — uses `collect_all_tags()` from `core/tags.py`.

## Approach

Add a `list-tags` CLI command to `cli/main.py` following the pattern of existing `list-skills` command. Calls `tags.collect_all_tags()`, formats output grouped by prefix with undeclared tags flagged. Update `claude/commands/mantle/help.md` to reference the `list-tags` → `list-skills --tag` workflow.

## Implementation

### `src/mantle/cli/main.py` (modify)

Add a `list_tags_command` function registered as `list-tags` on the app:

```python
@app.command(name="list-tags")
def list_tags_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """List all tags from taxonomy and vault skills."""
```

Implementation:
1. Default `path` to `Path.cwd()` if None
2. Import `tags` from `mantle.core`
3. Call `tags.collect_all_tags(path)` to get `TagSummary`
4. If no tags at all, print "No tags found." and return
5. Print total count: `"{N} tag(s) found:"` 
6. For each prefix group in `by_prefix` (alphabetically):
   - Print `"\n  {Group}:"` as the section header
   - For each tag in the group:
     - If tag is in `undeclared`, print `"    - {tag}  (undeclared)"` 
     - Else print `"    - {tag}"`
7. If undeclared tags exist, print a footer: `"\n{N} undeclared tag(s) — consider adding to .mantle/tags.md"`

### `claude/commands/mantle/help.md` (modify)

Add `list-tags` to the skill/knowledge section of the help command. Add a note about the discovery workflow:

```
| `mantle list-tags` | Discover available tags grouped by prefix |
```

Add a tip in the skills section:
```
**Tip:** Run `mantle list-tags` to discover tags, then `mantle list-skills --tag <tag>` to filter.
```

#### Design decisions

- **No `--prefix` filter flag.** Keep it simple — the grouped output already serves filtering needs. Add later if warranted.
- **"(undeclared)" suffix, not a separate section.** Keeps undeclared tags in context with their group rather than isolated. The footer summary gives the count.
- **Follows list-skills output style.** Consistent CLI experience — indented list under a count header.

## Tests

### `tests/cli/test_main.py` (modify)

Add tests for `list_tags_command`. Use `tmp_path` with `.mantle/tags.md` and mock vault setup (same fixture pattern as `vault_project` from story 1).

- **test_list_tags_prints_grouped**: Tags from taxonomy and vault are printed grouped by prefix.
- **test_list_tags_flags_undeclared**: Undeclared vault tags show "(undeclared)" suffix.
- **test_list_tags_no_tags**: No tags.md and no vault — prints "No tags found."
- **test_list_tags_undeclared_footer**: When undeclared tags exist, footer shows count and suggestion.