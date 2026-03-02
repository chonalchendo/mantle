---
issue: 17
title: Skill gap detection and skill loading for context
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Add gap detection and skill loading functions to `core/skills.py`. Gap detection compares `skills_required` in `state.md` against existing skill nodes in the personal vault. Skill loading returns the full skill content (metadata + authored knowledge) for inclusion in compiled context.

### Research context

Research confirms that skill content loaded into Claude's context should be dense, imperative, and written for Claude's consumption. The `description` field is the primary matching mechanism — `detect_gaps` and `load_relevant_skills` both use it alongside slug matching. When `load_relevant_skills` returns content, that content gets injected into Claude's working context, so quality directly impacts implementation quality.

### src/mantle/core/skills.py (modify)

#### Functions (add to existing module)

- `detect_gaps(project_dir) -> list[str]` — Read `skills_required` from `state.load_state(project_dir)`. List existing skill slugs from `list_skills(project_dir)`. Return skill names from `skills_required` that have no matching slug in the vault. Matching is case-insensitive, slug-normalized: `"Python asyncio"` matches `python-asyncio.md`. Returns empty list if all skills are tracked or if `skills_required` is empty. Raises `VaultNotConfiguredError` if vault not configured.

- `suggest_gap_message(gaps) -> str` — Format a human-readable message listing untracked skills with a suggestion to create them. Returns empty string if `gaps` is empty. Format:

  ```
  Untracked skills detected:
    - Python asyncio
    - WebSocket protocol

  Run /mantle:add-skill to create skill nodes for these.
  ```

- `load_relevant_skills(project_dir) -> list[tuple[SkillNote, str]]` — Read `skills_required` from `state.load_state(project_dir)`. For each required skill that has a matching node in the vault, load the full note (frontmatter + body) via `load_skill()`. Returns list of `(frontmatter, body)` tuples — the body contains the authored skill knowledge that's been written for Claude's consumption (patterns, decision criteria, examples, anti-patterns). This is the payoff of the skill graph: implementation context gets enriched with relevant domain knowledge. Skips missing skills silently (those are gaps, not errors). Returns empty list if no skills matched or `skills_required` is empty. Raises `VaultNotConfiguredError` if vault not configured.

#### Internal helpers (add)

- `_match_skill_slug(name, existing_paths) -> Path | None` — Given a skill name and list of existing paths, find the matching file by slug comparison. `_slugify(name)` compared against `path.stem` for each path. Returns the path if found, None if no match.

#### Design decisions

- **Slug-based matching**. `skills_required` stores human-readable names like `"Python asyncio"`. Matching normalizes both sides to slugs. This means `"Python Asyncio"`, `"python asyncio"`, and `"python-asyncio"` all match `python-asyncio.md`.
- **Silent skip on load**. `load_relevant_skills()` doesn't raise on missing skills — it returns what it can find. The gap detection API is the explicit way to surface missing skills.
- **Full content loading**. `load_relevant_skills()` returns the complete body. Research confirms that the authored content — written in imperative form for Claude — is what makes skills useful during implementation. A proficiency number alone tells Claude nothing; the patterns, examples, and decision criteria are the value.
- **Separation of detection and messaging**. `detect_gaps()` returns data, `suggest_gap_message()` formats it. This keeps gap detection testable and composable — CLI and Claude commands can format differently if needed.
- **No automatic creation**. Gap detection reports; it never creates skill nodes. The user decides via `/mantle:add-skill`.

## Tests

### tests/core/test_skills.py (modify — add tests)

Same fixture setup as story 01. Additionally, create `state.md` with `skills_required` populated. Create skill nodes with real authored content (not placeholder text) to verify the full body round-trips through loading.

- **detect_gaps**: returns empty list when skills_required is empty
- **detect_gaps**: returns empty list when all skills have matching nodes
- **detect_gaps**: returns unmatched skill names
- **detect_gaps**: matching is case-insensitive
- **detect_gaps**: matching normalizes spaces to hyphens
- **detect_gaps**: raises `VaultNotConfiguredError` when vault not configured
- **suggest_gap_message**: returns empty string for empty gaps
- **suggest_gap_message**: lists each gap skill
- **suggest_gap_message**: includes suggestion to run /mantle:add-skill
- **load_relevant_skills**: returns empty list when skills_required is empty
- **load_relevant_skills**: loads matching skill notes with full body content
- **load_relevant_skills**: body content includes authored knowledge (not just wikilink header)
- **load_relevant_skills**: skips skills that don't have nodes (no error)
- **load_relevant_skills**: returns all matched skills
- **load_relevant_skills**: raises `VaultNotConfiguredError` when vault not configured
- **_match_skill_slug**: finds matching path by slug
- **_match_skill_slug**: returns None when no match
