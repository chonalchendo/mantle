---
issue: 77
title: Machine-verifiable acceptance criteria with explicit pass/fail state
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 77

**Machine-verifiable acceptance criteria with explicit pass/fail state**

## Criteria

- ✓ **Issue frontmatter supports an `acceptance_criteria` list where each entry has `id`, `text`, and `passes: true or false`; Pydantic schema validates it.** [approved] — passed: true
- ✓ **Markdown AC checkboxes in the issue body are generated from the structured list on save, so the prose stays true to the data.** [approved] — passed: true
- ✓ **`/mantle:verify` flips `passes` per AC via a dedicated CLI operation (not raw edit) and emits a report of ACs still at `passes: false`.** [approved] — passed: true
- ✓ **`/mantle:review` refuses to approve an issue unless every AC is `passes: true` or carries an explicit waiver.** [approved] — passed: true
- ✓ **A one-time `mantle migrate-acs` CLI backfills existing planned/implemented/verified issues from their markdown checkboxes into structured frontmatter.** [approved] — passed: true
- ✓ **Unit tests cover the Pydantic schema, frontmatter round-trip, migration, body-sync rendering, and the flip-passes CLI behavior.** [approved] — passed: true
- ✓ **`just check` passes.** [approved] — passed: true
