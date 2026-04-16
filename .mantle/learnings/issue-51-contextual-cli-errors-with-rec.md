---
issue: 51
title: Contextual CLI errors with recovery suggestions
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-16'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Smallest-diff approach paid off.** Shape-issue chose pure helper module (Approach A) over custom-exception-at-app-root (Approach B) explicitly because the existing pattern was already `console.print(...) + raise SystemExit(...)` — a helper that keeps the same shape made the migration diff trivially review-able. Three clean commits (`b9ec967` add module, `425e714` migrate, `a9af13e` consolidate fallback hint) with no churn.
- **Per-call-site hint literals beat a central catalogue.** Resisting an enum/registry of recovery suggestions kept hints close to the message they pair with. The one duplication that emerged (the bug-tracker fallback for generic `except Exception`) was promoted to a named constant `UNEXPECTED_BUG_HINT` in a follow-up refactor — extract-on-third-use beat extract-up-front.
- **Two-story decomposition was session-sized.** Story 1 = pure module + 6 unit tests using only `capsys`. Story 2 = mechanical migration + integration tests. Clean dependency line, no blockage between them. Matches the issue-59 pattern of foundational module → integration.
- **Mid-flight learning captured immediately.** Story 1 spawned a tiny learning about Rich markup shorthand (`[red]Error:[/]` vs `[red]Error:[/red]`) — caught during implementation rather than waiting for retrospective. Cheap to capture, prevents future agents from "fixing" the inconsistency unnecessarily.
- **Keyword-only `hint` parameter as type-checker enforcement.** Making `hint` mandatory and keyword-only forces every call site to be explicit about recovery — the acceptance criterion ("every error includes a recovery suggestion") is now enforced at the type-checker level, not via code review.

## Harder Than Expected

- **Warning-vs-error boundary required judgement.** Many CLI files have `console.print("[yellow]Warning:[/yellow] ...") + raise SystemExit(1)` patterns (`issues.py:58-63`, `system_design.py:41-52,98-104`, `product_design.py:60-65,130-135`). They exit non-zero like errors but render as yellow warnings to stdout. The plan explicitly carved them out of scope ("Do not migrate `[yellow]Warning:` paths — they are not red errors"), but a reader of the acceptance criterion ("All existing CLI error paths use the shared utility") could reasonably challenge that interpretation. Worth resolving in a follow-up issue.
- **Integration test coverage came in light.** Plan called for 4 representative tests (`compile`, `skills`, `review`, stderr-vs-stdout). Only 2 landed (`compile`, `stories`). The migration is mostly mechanical so risk is low, but "4 of 16 files covered" → "2 of 16" is a quiet scope reduction that wasn't called out.
- **Generic `except Exception` handlers needed two passes.** First pass had every site repeating the bug-tracker hint string. Second pass extracted `UNEXPECTED_BUG_HINT`. Could have been spotted in shape-issue if the survey had counted hint-string duplicates upfront.

## Wrong Assumptions

- **Assumed the migration was uniform.** It wasn't — the `[yellow]Warning:[/]` exit paths created a real category boundary that the shaping pass treated as obvious but the verification/review pass had to re-interrogate. Future shape-issue passes for "migrate all X" should explicitly enumerate the *non-X* siblings and decide their fate too, even if the answer is "leave them alone".
- **Assumed every error path needed a context-specific hint.** Generic `except Exception` catches genuinely don't have one — `UNEXPECTED_BUG_HINT` is the right answer there. The shaped issue table did include "File a bug at..." as a fallback but it was a one-line note rather than a named pattern; promoting it to a module-level constant clarified the intent.

## Recommendations

- **For migration-style issues, enumerate the non-migrated siblings in shape-issue.** When the issue is "migrate all X to use Y", the shaped doc should list the X-adjacent patterns (Y-warnings, Z-style errors, etc.) and explicitly state "in scope" / "out of scope". Avoids ambiguity at review time.
- **Separately track integration test coverage as a story-level acceptance.** "4 representative tests" in the plan slipping to 2 in implementation is the kind of quiet scope drift a story-level checklist would catch. Worth adding to story-implementer's status report.
- **Promote duplicated literal hints to named constants on the third use, not the first.** The `UNEXPECTED_BUG_HINT` extract-on-duplication pattern is right. Don't pre-design a hint catalogue; let the duplication signal where one is warranted.
- **Follow-up issue: decide what to do with `[yellow]Warning:` + `raise SystemExit(1)` paths.** They violate the spirit of the acceptance criterion ("no raw `sys.exit` for errors") even if not the letter. Either migrate them under a new `print_warning`/`exit_with_warning` API, or document them as intentionally distinct in CLAUDE.md.
- **Bug to file: `mantle save-learning` should accept archived issues.** The retrospective workflow runs *after* `/mantle:review` archives, so save-learning's "issue not in `.mantle/issues/`" check breaks the documented flow. Either fall back to scanning `.mantle/archive/issues/` or relax the check.
