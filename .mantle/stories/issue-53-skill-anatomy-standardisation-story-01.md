---
issue: 53
title: Reference marker split in compiler — _split_on_reference_marker and _write_compiled_skill
  update
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer using Mantle skills during planning, I want the compiler to split vault skills at a reference marker so that SKILL.md contains the executable workflow inline while deep reference material loads on-demand.

## Depends On

None — independent

## Approach

Add a new \`<!-- mantle:reference -->\` marker constant and split function to \`core/skills.py\`, following the existing \`<!-- mantle:content -->\` pattern. Update \`_write_compiled_skill()\` to check for the marker first: content above becomes SKILL.md body, content below becomes \`references/core.md\`. When no marker is present, fall back to the existing line-count heuristic (backwards compatible).

## Implementation

### src/mantle/core/skills.py (modify)

1. Add constant: \`_REFERENCE_MARKER = "<!-- mantle:reference -->"\`

2. Add function \`_split_on_reference_marker(content: str) -> tuple[str, str | None]\`:
   - Split content on \`_REFERENCE_MARKER\`
   - Return \`(above, below)\` if marker found, \`(content, None)\` if not
   - Strip leading/trailing whitespace from both parts

3. Update \`_write_compiled_skill()\`:
   - Call \`_split_on_reference_marker(content)\` first
   - If marker was found (reference is not None):
     - SKILL.md = frontmatter + main_content (above marker)
     - references/core.md = reference content (below marker)
   - If marker not found (reference is None):
     - Fall through to existing line-count heuristic (current behaviour unchanged)
   - The existing \`_PROGRESSIVE_DISCLOSURE_THRESHOLD\` and \`_split_content_for_disclosure()\` remain as the fallback path

#### Design decisions

- **Marker-first, heuristic-fallback**: The reference marker is an explicit opt-in. Skills without it compile exactly as before — zero migration risk.
- **Single split function**: Keeps the logic simple and testable. No need for multi-marker support.

## Tests

### tests/core/test_skills.py (modify)

- **test_split_on_reference_marker_with_marker**: content with marker splits into (above, below) tuple
- **test_split_on_reference_marker_without_marker**: content without marker returns (content, None)
- **test_split_on_reference_marker_empty_below**: marker at end returns (above, empty string)
- **test_write_compiled_skill_with_reference_marker**: when content has marker, SKILL.md contains above-marker content inline (not just a pointer), references/core.md contains below-marker content
- **test_write_compiled_skill_without_marker_falls_back**: when content has no marker, behaviour matches existing line-count heuristic (regression test)
- **test_compile_skills_with_reference_marker_end_to_end**: full compile_skills() with a vault skill containing the marker — verify compiled output structure