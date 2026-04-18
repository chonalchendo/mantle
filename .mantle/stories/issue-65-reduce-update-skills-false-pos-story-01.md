---
issue: 65
title: Drop description-overlap rule from detect_skills_from_content
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle user running `update-skills`, I want only relevant skills selected so my compiled context is not bloated with unrelated domain knowledge.

## Depends On

None — independent (single-story issue).

## Approach

Shaped Approach A: remove the fallback description-word-overlap rule in `core.skills.detect_skills_from_content`, keeping only name / slug / tag matching. Also deletes the now-dead `_STOPWORDS` frozenset, `_tokenize` helper, and the per-call `content_tokens` precomputation. Replaces the two tests that assert the deleted rule with a single pin test asserting a skill with philosophy-style generic-token description does NOT match an unrelated CLI issue body — the concrete false-positive class from the inbox reports.

## Implementation

### src/mantle/core/skills.py (modify)

Three tightly-scoped deletions inside one file:

1. **Delete the description-overlap rule** at L775-778 inside `detect_skills_from_content`:

    ```python
    # Match by description word overlap (3+ non-stopword tokens)
    desc_tokens = _tokenize(note.description) - _STOPWORDS
    if len(desc_tokens & content_tokens) >= 3:
        matched.append(note.name)
    ```

2. **Delete the now-unused precomputation** at L749:

    ```python
    content_tokens = _tokenize(content_lower)
    ```

3. **Delete the now-dead helpers** at the top of the module:
   - `_STOPWORDS` frozenset (L24-52)
   - `_tokenize` function (L55-57)

**Do not touch** `import re` — still used at L167 (slug sanitisation), L770 (tag-suffix regex), L1238 (section split).

#### Design decisions

- **Inline deletion, no helper extraction.** The rule is a 4-line block; there is nothing to extract. Removing it is the entire change.
- **Delete `_tokenize` and `_STOPWORDS` outright.** Verified via grep that no caller exists in `src/` or `tests/`. Per CLAUDE.md avoid backwards-compat shims for removed code.
- **Keep name / slug / tag matching unchanged.** Those rules have zero observed false-positive reports; only the description-overlap rule was implicated.

### tests/core/test_skills.py (modify)

Two deletions and one addition inside `class TestDetectSkillsFromContent`:

1. **Delete** `test_detect_skills_matches_by_description` (≈L1401-1414) — its positive assertion is no longer true.
2. **Delete** `test_detect_skills_no_match_below_threshold` (≈L1416-1428) — the concept of a "threshold" is gone with the rule.
3. **Add** `test_no_false_positive_from_description_tokens` — pins the rule (satisfies AC #3). Create a skill whose description shares 3+ generic tokens with an issue body that is genuinely about something unrelated, and assert the skill is NOT in the returned list.

    Concrete setup (mirrors inbox report — "Nick Sleep on a CLI grouping issue"): create a skill named "Nick Sleep Investment Philosophy" with a long description full of generic investment vocabulary ("framework", "moat durability", "reinvestment runway", "analysis"), then pass a CLI-grouping content string like "Group mantle CLI commands in help output by topic. Analysis of current help output shows commands are listed flat, making it hard to use at scale." and assert `"Nick Sleep Investment Philosophy" not in detect_skills_from_content(project, content)`.

#### Design decisions

- **One pin test, not a matrix.** The rule is either present or absent — a single concrete false-positive case proves the absence.
- **Use `_create_skill` helper and plain pytest asserts** — matches the 10 surrounding tests in `TestDetectSkillsFromContent`. No `dirty-equals` or `inline-snapshot` needed for `not in` membership.
- **No change to auto_update_skills tests** — that function delegates to `detect_skills_from_content`, so its behaviour narrows automatically; existing tests there use fixtures that match by name/slug/tag.

## Tests

### tests/core/test_skills.py (modify)

- **test_no_false_positive_from_description_tokens (new)**: creates a skill with philosophy-style description, builds a CLI-grouping content string with 3+ generic overlapping tokens, asserts the skill is NOT returned by `detect_skills_from_content`. Pins Approach A; satisfies AC #3.
- **test_detect_skills_matches_by_description (removed)**: deleted — positive assertion no longer holds under Approach A.
- **test_detect_skills_no_match_below_threshold (removed)**: deleted — "threshold" concept removed with the rule.

All other tests in `TestDetectSkillsFromContent` and `TestAutoUpdateSkills` remain untouched — they exercise name / slug / tag matching, which this story does not alter.