---
issue: 21
title: Prompt to fill stub skills on demand
status: completed
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

### Problem

Story 1 creates stub skills (0/10 proficiency) when related skill links don't exist. But stubs with placeholder content are useless to Claude — they'll sit idle unless the user remembers to come back and fill them. The right moment to fill a stub is when the user is about to work on something that needs that skill, because they have immediate domain context and motivation.

### `src/mantle/core/skills.py`

Add a `detect_stubs()` function that finds required skills with 0/10 proficiency:

```python
def detect_stubs(project_dir: Path) -> list[tuple[str, Path]]:
    """Find skills_required that exist as stubs (0/10 proficiency).

    Returns list of (skill name, path) tuples for stub skills that
    are in skills_required and have proficiency "0/10".
    """
```

Add a `suggest_stub_message()` function that formats a prompt for the user:

```python
def suggest_stub_message(stubs: Sequence[tuple[str, Path]]) -> str:
    """Format a message prompting the user to fill stub skills.

    Returns a message like:
        Stub skills detected that could be fleshed out:
          - Python asyncio (0/10)
          - Docker compose (0/10)

        Run /mantle:add-skill to add your knowledge to these.
    """
```

### `claude/commands/mantle/resume.md.j2`

Add a stubs section to the resume template, shown when stub skills are detected among `skills_required`:

```jinja2
{% if skill_stubs %}
## Skill Stubs

The following required skills are stubs (0/10) — flesh them out when relevant:

{% for name in skill_stubs %}- {{ name }}
{% endfor %}
Run `/mantle:add-skill` to add your knowledge to any of these.
{% endif %}
```

### `src/mantle/core/compiler.py`

Update the resume template context to include `skill_stubs` — the list of stub skill names among `skills_required`. Uses `detect_stubs()` from the skills module.

### `claude/commands/mantle/add-skill.md`

Update Step 2 (check for gaps) to also surface stubs alongside missing skills:

```
> Stub skills that could be fleshed out:
>   - Docker compose (0/10)
>
> Want to fill one of these, or create a new skill?
```

### Design decisions

- **On-demand, not auto-generated.** Stubs are filled when the user encounters them in context, not speculatively via background research. This ensures skills contain personal patterns and conventions, not generic web knowledge.
- **Surfaced at session start, not blocking.** The resume briefing shows stubs as a suggestion, not a gate. The user can ignore them and proceed with their task.
- **Stubs are identified by proficiency.** `0/10` is the canonical marker for "not yet authored". No separate status field needed.
- **Prioritised by `skills_required`.** Only stubs that are relevant to the current project are surfaced. Stubs created for other projects' related skills stay quiet.

## Tests

### tests/core/test_skills.py

- **test_detect_stubs_finds_zero_proficiency**: Stub skill in `skills_required` is returned
- **test_detect_stubs_ignores_authored**: Skill with proficiency > 0 is not returned
- **test_detect_stubs_ignores_missing**: Skill in `skills_required` but not in vault is not returned (that's a gap, not a stub)
- **test_detect_stubs_empty_when_no_stubs**: No stubs among required skills returns empty list
- **test_suggest_stub_message_lists_stubs**: Message includes each stub name
- **test_suggest_stub_message_empty_for_no_stubs**: Empty input returns empty string
