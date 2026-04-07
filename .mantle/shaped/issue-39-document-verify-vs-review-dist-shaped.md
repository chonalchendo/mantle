---
issue: 39
title: Document verify vs review distinction and add convention checking to verify
approaches:
- 'Prompt-only: edit verify.md and review.md to document the distinction and add convention
  check sub-step inline'
- 'Prompt + CLI: add mantle check-conventions command called by verify.md'
- 'Prompt + core module: add core/conventions.py for structured convention parsing'
chosen_approach: Prompt-only
appetite: small batch
open_questions:
- none
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-07'
updated: '2026-04-07'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen Approach: Prompt-only

Edit verify.md and review.md command prompts directly. No Python code changes.

### Strategy

1. **verify.md** — Add a documentation block near the top explaining that verify checks functional correctness against acceptance criteria, not architectural quality. Add a new Step 6.5 (Convention Check) between Execute Verification and Report Results that instructs the AI to: read CLAUDE.md and system-design.md, scan files changed by the issue, flag convention deviations as warnings in the report.

2. **review.md** — Add a documentation block explaining that review checks architectural quality, conventions, and design consistency. This is the authoritative quality gate.

3. Convention check results appear as a separate 'Convention Warnings' section in the verification report, clearly marked as warnings (not pass/fail blockers).

### Fits architecture by

- Follows 'one command, one job' — verify still verifies, review still reviews. The convention check is a lightweight bridge, not a replacement for review.
- No core/ changes — this is prompt layer only, consistent with verify.md and review.md being static command files.
- Convention check reads existing files (CLAUDE.md, system-design.md) that are already in the project.

### Does not

- Does not make convention violations block verification (they are warnings only)
- Does not add Python code to core/ or cli/ (prompt-only change)
- Does not change the verification report pass/fail semantics
- Does not replace /mantle:review as the architectural quality gate