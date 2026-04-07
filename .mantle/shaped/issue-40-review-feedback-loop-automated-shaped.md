---
issue: 40
title: Review feedback loop — automated fix and re-verify after review
approaches:
- Review persistence + fix command (minimal)
- Full build integration (save + fix + build --resume)
chosen_approach: Review persistence + fix command (minimal)
appetite: small batch
open_questions:
- Should fix.md spawn one agent per needs-changes criterion, or one agent for all
  fixes?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-07'
updated: '2026-04-07'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### Approach A: Review persistence + fix command (minimal)
- Add save/load review results to core/review.py (persist ReviewChecklist to .mantle/reviews/)
- Add mantle save-review-result and mantle load-review-result CLI commands
- Update review.md Step 6 to save results when needs-changes items exist
- Create fix.md prompt that reads saved review, spawns implementation agents, re-verifies
- **Appetite:** small batch (1-2 days)
- **Key benefit:** Smallest change that satisfies all ACs
- **Key risk:** fix.md prompt quality — spawning agents with review feedback context
- **Rabbit holes:** Over-engineering the review storage format; trying to auto-detect which files to fix
- **No-gos:** No build.md integration (separate issue), no re-review automation (human step)

### Approach B: Full build integration
- Everything in A plus build.md --resume flag for post-review re-entry
- **Appetite:** medium batch (3-5 days)
- **Key benefit:** Seamless build pipeline re-entry
- **Key risk:** build.md is already complex; adding re-entry logic increases maintenance
- **No-gos:** Not chosen — build integration can be a follow-up issue

## Chosen: Approach A — Review persistence + fix command

### Strategy

**core/review.py** — extend with save/load functions:
- `save_review_result(project_root: Path, checklist: ReviewChecklist) -> Path` — serialize ReviewChecklist to `.mantle/reviews/issue-{NN}-review.md` with YAML frontmatter (issue, title, overall_status) and markdown body listing each criterion with status and comment
- `load_review_result(project_root: Path, issue_number: int) -> ReviewChecklist` — read and deserialize back

**cli/review.py** — add CLI wrappers:
- `run_save_review_result(issue, criteria_feedback, project_dir)` — parse --feedback args into ReviewChecklist and save
- `run_load_review_result(issue, project_dir)` — load and print formatted result

**cli/main.py** — register new commands:
- `mantle save-review-result --issue N --feedback "criterion|status|comment" ...`
- `mantle load-review-result --issue N`

**review.md** — update Step 6 "needs changes" path to call `mantle save-review-result` after collecting feedback

**fix.md** — new prompt file:
1. Read saved review result via `mantle load-review-result --issue N`
2. Read issue and stories for context
3. Transition issue to implementing via `mantle transition-issue-implementing --issue N`
4. For each needs-changes criterion, spawn an implementation agent with the criterion + comment as context
5. After all fixes, transition to implemented via `mantle transition-issue-implemented --issue N`
6. Auto-run verification (invoke verify.md logic inline or spawn verify agent)
7. Report results

### Fits architecture by

- Extends existing core/review.py module (ReviewChecklist model already exists)
- Follows core-never-imports-cli boundary
- CLI commands are thin wrappers over core functions (consistent with review.py pattern)
- fix.md follows the prompt-orchestrates-AI-implements pattern from implement.md
- Uses existing status transitions (implemented → implementing already works)
- .mantle/reviews/ follows the .mantle/{artifact}/ directory pattern (like .mantle/shaped/, .mantle/learnings/)

### Does not

- Does not modify build.md (separate issue for build pipeline re-entry)
- Does not auto-re-review after fixing (review is a human checkpoint)
- Does not handle partial fixes (all needs-changes items are addressed in one pass)
- Does not add new status transitions (uses existing implemented → implementing → implemented)
- Does not persist verification results to disk (verify.md handles that in conversation)