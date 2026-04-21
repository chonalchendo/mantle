---
name: Prompt sweep substring guard
description: tests/prompts/test_prompt_sweep.py asserts exact substring "MANTLE_DIR=$(mantle where)" in batch prompt files; edits changing that string break it
type: feedback
---

When editing `claude/commands/mantle/*.md` to tweak the `MANTLE_DIR=$(mantle where)` prelude, update `tests/prompts/test_prompt_sweep.py::_assert_includes_resolve_prelude` to accept the new form. The helper does a plain substring check against the accepted strings tuple — any syntactic variation (e.g., fallback `${MANTLE_DIR:-...}` form) must be added there or the batch-N tests fail.

**Why:** The sweep is a regression guard from issue 44 that every batch prompt declares the prelude. It's not scope creep to touch it when the prelude legitimately evolves; the sweep tests are co-scoped with prompt changes.

**How to apply:** When a story says "edit only build.md Step 1" but changes the prelude syntax, expect the prompt sweep test to break and fix it symmetrically — add the new form to the `accepted` tuple with a short comment noting the issue that introduced the variant.
