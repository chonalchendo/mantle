---
issue: 21
title: Add content-based tags to skill nodes
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

### `claude/commands/mantle/add-skill.md`

Add a tagging step to the workflow (between research synthesis and final save). The AI:

1. Reads `.mantle/tags.md` to see the existing tag taxonomy
2. Suggests content-based tags for the skill — `topic/` and `domain/` tags based on the skill's name, description, and research content
3. Reuses existing tags where appropriate (e.g., if `topic/python` already exists, use it rather than creating `topic/python-3`)
4. Proposes new tags when no existing tag fits, with a brief description
5. Presents the suggested tags to the user for confirmation (add/remove/edit)
6. After confirmation, passes the full tag list (including `type/skill`) to `mantle save-skill`

The AI is best placed to choose tags because it has the full research context and can make semantic judgements (e.g., knowing that "FastAPI" belongs in `domain/web` without a hardcoded lookup).

### `src/mantle/core/skills.py`

No `derive_skill_tags()` function needed — tag selection happens in the AI workflow, not in code.

Update `create_skill()` and `update_skill()` to accept an optional `tags` parameter that overrides the default `("type/skill",)`. Ensure `type/skill` is always present regardless of what's passed in.

```python
def create_skill(
    project_dir: Path,
    name: str,
    description: str,
    proficiency: str,
    content: str,
    related_skills: Sequence[str] = (),
    projects: Sequence[str] = (),
    tags: Sequence[str] = (),  # NEW — merged with type/skill
    overwrite: bool = False,
) -> Path:
```

### `src/mantle/cli/skills.py`

Update the `save-skill` CLI command to accept a `--tag` option (repeatable) for passing content tags from the AI workflow.

```
mantle save-skill --name "Python asyncio" ... --tag topic/python-asyncio --tag domain/concurrency
```

### `src/mantle/core/tags.py`

New module. Reads and updates the project's `tags.md` file.

```python
def load_tags(project_dir: Path) -> set[str]:
    """Read all tags from .mantle/tags.md."""

def add_tags(project_dir: Path, new_tags: Sequence[str]) -> list[str]:
    """Append new tags to the appropriate section in .mantle/tags.md.

    Returns list of tags that were actually new (not already present).
    Infers section from prefix: topic/ → Topic Tags, domain/ → Domain Tags.
    Creates the section if it doesn't exist.
    """
```

### `.mantle/tags.md` (via `mantle init`)

Add new sections to the initial tag taxonomy created by `mantle init`:

```markdown
#topic/<skill-slug>        # Content topic, one per skill

#domain/web                # Web frameworks, HTTP, frontend
#domain/database           # SQL, NoSQL, caching
#domain/devops             # Containers, CI/CD, infrastructure
#domain/testing            # Test frameworks and strategies
#domain/concurrency        # Async, threading, parallelism
```

These are seed entries. The AI adds new ones as skills are created.

### `vault-templates/skill.md`

Update the template's `tags` field to show content tags as examples:

```yaml
tags:
  - type/skill
  - topic/skill-name
  - domain/relevant-domain
```

### Design decisions

- **AI-driven tagging, not code-driven.** The AI has full context from the research phase and can make better semantic tag choices than any static lookup. Tags are a creative decision, not a mechanical derivation.
- **`tags.md` is the source of truth.** Existing tags are reused when they fit, new tags are appended. This keeps the taxonomy growing organically without a hardcoded dictionary in code.
- **User confirms tags before save.** The AI suggests, the user approves. Prevents tag sprawl from unchecked AI suggestions.
- **`type/skill` is always enforced in code.** Even if the AI or user omits it, `create_skill()` ensures it's present. Content tags are additive.
- **`core/tags.py` is a thin module.** Just load and append — no complex logic. The intelligence is in the AI workflow prompt, not the code.

## Tests

### tests/core/test_tags.py

- **test_load_tags**: Reads tags from a well-formed tags.md
- **test_load_tags_empty**: Empty tags.md returns empty set
- **test_add_tags_new**: Adding new tags appends them to the correct section
- **test_add_tags_existing**: Adding already-existing tags returns empty list (no duplicates)
- **test_add_tags_creates_section**: Adding a `topic/` tag when no Topic Tags section exists creates it

### tests/core/test_skills.py

- **test_create_skill_with_custom_tags**: Passing tags includes them in frontmatter alongside `type/skill`
- **test_create_skill_always_includes_type_skill**: Even without passing tags, `type/skill` is present
- **test_create_skill_enforces_type_skill**: Passing tags without `type/skill` still includes it
- **test_update_skill_with_tags**: Updating tags replaces previous content tags

### tests/cli/test_skills.py

- **test_save_skill_with_tags**: `--tag` options are passed through to `create_skill()`
