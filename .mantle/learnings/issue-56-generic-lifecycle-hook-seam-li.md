---
issue: 56
title: Generic lifecycle hook seam (Linear/Jira as first examples)
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-18'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **First batch-appetite build ran clean end-to-end.** 3 stories, ~970 lines changed, zero retries, zero BLOCKED statuses, 1211/1211 tests green. Sonnet for the mechanical wiring story (02); opus for the net-new-module stories (01, 03). Model selection held up under a larger-than-usual spec.
- **Shape-time scoping flagged the un-verifiable ACs up front.** AC7/8/9 (linear/jira/slack against real workspaces) were explicitly carved out as "structural only — human-verified in /mantle:review" in the shaped doc. Build pipeline didn't silently promise something it couldn't deliver. Verifier echoed the same flag. This carve-out pattern is re-usable for any future ACs that need live creds.
- **Mid-build per-story learnings unblocked downstream stories.** Story 01 discovered `project.init_project(path, name)` takes two required args; Story 02 discovered shaping tests need `@patch('mantle.core.shaping.state.resolve_git_identity')`. Both were saved via `mantle save-learning` immediately after the story completed, so the next story-implementer agent surfaced them via project memory. Mid-build learning capture is cheap and eliminates rediscovery cost.
- **Issue-body → shaped-doc disagreement caught pre-implementation.** Issue body said `config.yml` with nested `hooks.env:`; actual project uses `config.md` with frontmatter `hooks_env:` (snake_case convention). I caught this in shape by reading `core/project.py` and adjusted the shape doc before plan-stories. Cheap to fix at shape-time; expensive to fix at implementation-time.

## Harder Than Expected

- **Retrospective follow-up: I biased the simplifier prompt.** I pre-flagged five patterns to the refactorer as intentional (`_AVAILABLE` tuple, bash-in-tests, fail-open bypass, setup headers, PEP 758 `except`). It returned 0/16 files changed — which might be the right answer, but the hints made the test unfair. Next run: let the simplifier see the code cold and push back on anything it finds. I can still reject its changes; pre-empting the challenge defeats the point.
- **Package data wiring needed a wheel-inspection spot-check.** Hatch's default `packages = ["src/mantle"]` shipped the `.sh` files without any explicit `include` rule, but I wasn't certain of that until `uv build --wheel && unzip -l` confirmed. Worth remembering: whenever a story introduces non-Python package data, the implementer should run a wheel inspection before committing, not just `uv run pytest`.
- **Transition-function repetition is at Rule-of-Three exactly.** The three wired transitions now share an identical 3-line body (`_transition_issue → load_issue → hooks.dispatch`). Simplifier flagged it as a future follow-up, "kept under Rule of Three threshold". Conservative call — there *are* 3 of them. If a 4th hooked transition appears, extracting `_transition_and_dispatch(target, event)` is worth doing; until then it's fine.

## Wrong Assumptions

- **Live-creds ACs can be satisfied by a structural-only pass, but approval is provisional.** The build pipeline + automated review approved AC7/8/9 on the basis of stubbed integration tests. User hasn't actually run the scripts against real Linear/Jira/Slack yet — needs to (a) sign up for Linear, (b) release a new mantle version so the installed CLI has `show-hook-example`, (c) test at work. Net: the current "approved" state is conditional. Future batch issues with live-creds ACs should make this conditional explicit in the verification report, not just in the shape doc.
- **Expected simplify to find wins the way it did in 62/63.** Those issues modified existing code, where change-shape forces awkward edges. This issue is net-new code written to tight specs. Different substrate, different bloat pattern. Don't expect every issue's simplify to produce changes.
- **Expected the 970-line diff to include some test-realignment churn (per issue-63 learning).** It didn't — this was nearly all net-new test files (`test_hooks.py`, `test_hook_examples.py`). Test-realignment churn is a modify-existing hazard; new-module issues skip it.

## Recommendations

- **Adopt the "structural-only AC" carve-out as a first-class shape-doc section.** For any AC that needs live creds, human judgment, or resources the build pipeline can't touch, the shape doc should split ACs into "automated" and "human-verifies" columns. /mantle:review should render the human-verifies column as an explicit checklist, not a generic approve/deny. Filed as follow-up candidate — worth a new issue.
- **Stop pre-hinting the simplifier.** The simplify.md prompt or the build.md Step 7 instructions should remind the orchestrator to avoid pre-flagging intentional patterns. Let the simplifier challenge everything; the orchestrator decides whether to accept its changes after the fact. Protects the signal value of the 0/N result.
- **Add a wheel-inspection step to plan-stories for any story that ships non-Python assets.** The generated story should explicitly tell the implementer to run `uv build --wheel && unzip -l dist/*.whl | grep <asset-path>` as part of the acceptance criteria for that story, not rely on pytest alone.
- **Conditional-approval rendering in /mantle:review.** When ACs are marked "structural only" in the shape doc, the review checklist should surface a different badge (e.g. "Provisional — live test required") instead of the same "approved" outcome. Prevents the user (me, just now) from clicking "Approve all" on things that aren't actually verified.
- **Mid-build `mantle save-learning` between stories is a keeper.** Project memory made story 02 immediately aware of story 01's findings. This is what the learning system is for. Continue doing it.