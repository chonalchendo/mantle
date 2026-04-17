---
title: Reconcile implement.md internal inconsistency on skill-file injection
status: implementing
slice:
- claude-code
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Python 3.14
- Python Project Conventions
- Python package structure
- SQLMesh Best Practices
- cyclopts
- dirty-equals
- docker-compose-python
- fastapi
- inline-snapshot
- omegaconf
- pydantic-project-conventions
- python-314
tags:
- type/issue
- status/implementing
---

## Parent PRD

product-design.md, system-design.md

## Why

`claude/commands/mantle/implement.md` contains two contradictory instructions about whether the orchestrator and its spawned agents should read `.claude/skills/*/SKILL.md` files:

- **Step 3 (lines 94-106)** lists `.claude/skills/*/SKILL.md` as a required context file the orchestrator should read: "read all required context files: ... `.claude/skills/*/SKILL.md` — compiled vault skills (these provide domain-specific knowledge to story agents)".
- **Step 4 (lines 145-148)** scans `.claude/skills/*/SKILL.md` when building a per-story context brief: "scan compiled skill summaries. Pick skills whose domain matches this story's work."
- **Step 5 (lines 180-183)** tells the story-implementer agent the opposite: "Skill knowledge is embedded in the shaped issue's code design and flows into stories via their implementation sections. Do not separately inject skill files — the story spec already carries the relevant domain knowledge."

Surfaced as an open question on the shaped doc for issue 60 (removal of the redundant skill-loading step in `plan-stories.md`). Out of scope there, valid for its own issue.

Concretely, this matters because:

- A future maintainer reading implement.md gets contradictory signals about whether to inject skill content into the story-implementer prompt.
- The orchestrator's own context brief (Step 4) quietly pulls skill content that Step 5 says the story-implementer doesn't want — the brief is then passed verbatim into the agent prompt anyway, which defeats the Step 5 injunction.
- The runtime behaviour is ambiguous: some past issues' story-implementer agents clearly received skill excerpts through the brief, others did not.

## What to build

Shaping decides which direction is correct, then applies a single-file edit to `implement.md`:

- **Direction A (skill files are orchestrator-only context):** Step 3/4 keep their references to `.claude/skills/*/SKILL.md` for the orchestrator's judgment. Step 5 stays as-is. Rewrite the ambiguous Step 5 paragraph so it is clear that *the brief* carries distilled skill knowledge (selected by the orchestrator), not raw skill files injected wholesale.
- **Direction B (skill files are not consulted at implement time):** Remove the `.claude/skills/*/SKILL.md` line from Step 3's context list and drop the skill-scan bullet from Step 4. Step 5's paragraph stays — it now matches the behaviour.
- **Direction C (mixed: orchestrator consults, implementer doesn't):** Clarify in Step 5 that the story-implementer agent relies on the shaped doc + story + orchestrator-curated brief, and that raw skill files are not re-injected after the brief is composed.

The chosen direction is a Shape-Up decision — the shaping agent should pick one and give the rationale. Implementation is the docs edit for that chosen direction, committed in one commit.

Do NOT modify `shape-issue.md`, `plan-stories.md`, or `build.md` as part of this issue.

## Acceptance criteria

- [ ] Shaped doc names the chosen direction (A, B, or C) and gives a one-paragraph rationale citing the two conflicting sections by line number.
- [ ] `implement.md` is edited so the Step 3/4/5 sections no longer contradict each other.
- [ ] No other `claude/commands/mantle/*.md` file is modified in this issue.
- [ ] No Python source or tests are modified in this issue.
- [ ] `just check` passes.

## Blocked by

None

## User stories addressed

- As a Mantle contributor maintaining command templates, I want `implement.md` to give a single coherent instruction about skill-file consumption so that a future edit does not compound the drift.
- As a user inspecting why story-implementer agents behave differently across issues, I want the documented orchestrator behaviour to match the runtime contract so that debugging is tractable.