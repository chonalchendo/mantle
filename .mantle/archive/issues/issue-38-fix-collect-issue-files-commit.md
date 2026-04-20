---
title: Fix collect-issue-files commit detection for story commits
status: approved
slice:
- core
- tests
story_count: 1
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: \`collect-issue-files\` correctly finds commits from story-implementer agents
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Detection handles both \`feat(issue-N):\` and \`feat(issue-NN):\` patterns
    (zero-padded and non-padded)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Returns accurate file list when commits exist
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Returns empty/zero gracefully when no commits exist (not an error)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Covered by tests
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

\`mantle collect-issue-files --issue 30\` returned "No commits found for issue 30" even though there were 4+ story commits. The simplification step in the build pipeline relies on this command to count files changed and decide whether to run. When it fails, simplification can't determine file count automatically.

The likely cause is that commit detection looks for a specific message pattern that story-implementer agents don't reliably follow.

## What to build

Fix the commit detection logic in \`collect-issue-files\` so it correctly finds story commits. Investigate the expected commit message pattern vs what story-implementer agents actually produce, and make detection robust to both.

### Flow

1. User runs \`mantle collect-issue-files --issue N\`
2. Command searches git log for commits related to issue N
3. Returns list of files changed across those commits

## Acceptance criteria

- [ ] ac-01: \`collect-issue-files\` correctly finds commits from story-implementer agents
- [ ] ac-02: Detection handles both \`feat(issue-N):\` and \`feat(issue-NN):\` patterns (zero-padded and non-padded)
- [ ] ac-03: Returns accurate file list when commits exist
- [ ] ac-04: Returns empty/zero gracefully when no commits exist (not an error)
- [ ] ac-05: Covered by tests

## Blocked by

None

## User stories addressed

- As the build pipeline's simplification step, I need accurate file counts from story commits so I can decide whether simplification is warranted