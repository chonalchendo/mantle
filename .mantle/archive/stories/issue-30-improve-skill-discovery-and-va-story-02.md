---
issue: 30
title: Improved skill detection — match on tags and description
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer using the build pipeline, I want update-skills to find relevant skills by topic tags and description so that implementation agents get better domain knowledge even when the issue doesn't mention skills by exact name.

## Depends On

None — independent. Touches a different function (detect_skills_from_content) than story 1 (list_skills).

## Approach

Extend detect_skills_from_content() to add two additional matching strategies after the existing name/slug matching: tag-based matching and description word overlap. This follows the existing pattern in the function where multiple match strategies are tried in sequence with early continue on first match.

## Implementation

### src/mantle/core/skills.py (modify)

1. **Extend `detect_skills_from_content()`** — add two new matching branches after the existing name and slug checks:

   **Tag matching**: For each skill, check if any of its non-type tags (filter out `type/skill`) appear as substrings in the lowered content. For example, if a skill has tag `domain/concurrency` and the content contains "concurrency", it matches. Use the part after the `/` prefix for matching (e.g., `domain/concurrency` matches if `concurrency` is in content).

   **Description word overlap**: Tokenize the skill's description and the content into lowercase word sets (split on whitespace and punctuation). Remove common stopwords (a, an, the, is, are, was, were, be, been, in, on, at, to, for, of, with, and, or, not, this, that, it, by, from, as). If 3+ non-stopword tokens from the description appear in the content, the skill matches.

   The matching order becomes:
   1. Name match (existing) → continue
   2. Slug match (existing) → continue
   3. Tag match (new) → continue
   4. Description overlap (new) → continue

2. **Add `_STOPWORDS` module-level constant** — a frozenset of common English stopwords used for description matching.

3. **Add `_tokenize()` helper** — splits text into lowercase word tokens (split on non-alphanumeric characters, filter empty strings). Used by description matching.

#### Design decisions

- **Tag suffix matching, not full tag matching**: Matching `concurrency` from `domain/concurrency` is more useful than requiring the content to contain the full tag path. Content won't say "domain/concurrency" — it will say "concurrency".
- **3-word overlap threshold**: Low enough to catch relevant skills, high enough to avoid false positives from generic descriptions. This is a heuristic — can be tuned later.
- **Stopwords as a constant, not a parameter**: The list is small and stable. No need for configurability.

## Tests

### tests/core/test_skills.py (modify)

- **test_detect_skills_matches_by_tag**: Create a skill with tag `domain/web`, provide content mentioning "web development", assert skill is detected.
- **test_detect_skills_matches_by_description**: Create a skill with description "Async Python patterns using asyncio for concurrent I/O-bound services", provide content mentioning "asyncio concurrent services patterns", assert skill is detected (4+ word overlap).
- **test_detect_skills_no_match_below_threshold**: Create a skill with description "Async Python patterns using asyncio", provide content mentioning only "Python" (1 word overlap, below threshold), assert skill is NOT detected via description (though it might match by name — use a skill name not in the content).
- **test_detect_skills_ignores_type_tags**: Create a skill with only `type/skill` tag, provide content mentioning "skill", assert skill is NOT detected via tag matching (type/ tags are filtered out).
- **test_detect_skills_deduplicates**: Create a skill that matches by both name and tag, assert it appears only once in results.