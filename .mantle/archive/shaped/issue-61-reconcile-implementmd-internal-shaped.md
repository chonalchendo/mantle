---
issue: 61
title: Reconcile implement.md internal inconsistency on skill-file injection
approaches:
- direction A — keep refs, clarify Step 5 paragraph
- direction B — drop skill refs from Step 3 & Step 4, keep clarifying paragraph
- direction C — mixed (orchestrator consults, implementer doesn't)
chosen_approach: direction B — drop skill refs from Step 3 & Step 4
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-17'
updated: '2026-04-17'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Investigation

**The contradiction in `claude/commands/mantle/implement.md`:**

- **Step 3, line 106** lists `.claude/skills/*/SKILL.md` as a required
  context file the orchestrator must read: "compiled vault skills (these
  provide domain-specific knowledge to story agents)."
- **Step 4, lines 145-147** tells the orchestrator to scan compiled skill
  summaries and pick ones matching each story's work, then fold them into
  the per-story context brief.
- **Step 4, lines 180-183** tells the orchestrator the opposite: "Skill
  knowledge is embedded in the shaped issue's code design and flows into
  stories via their implementation sections. Do not separately inject skill
  files — the story spec already carries the relevant domain knowledge."
- **Step 5, line 226** instructs the orchestrator to pass "the context brief
  from Step 4 (selected learnings, decisions, and skills relevant to this
  specific story)" verbatim into the story-implementer prompt — so if Step 4
  scans skills, they reach the implementer through the brief, defeating the
  180-183 injunction.

**Root cause:** two authors with opposing philosophies (context-maximalism
vs. shape-is-the-channel) edited the file at different times and their
edits never reconciled. Today the runtime behaviour is ambiguous — past
issues have seen story-implementer agents receive skill excerpts via the
brief, and others have not.

**Upstream context that disambiguates which philosophy is canonical:**

- Issue 60 (just shipped) removed redundant skill-loading from
  `plan-stories.md`. The stated rationale: skills are loaded once during
  shaping; re-injecting them downstream is waste.
- `shape-issue.md` is the step with an Iron Law (build.md #5) requiring
  explicit `Read` evidence on skill files. Shape is where skill patterns
  get baked into the code design.
- `plan-stories.md` no longer loads skills (issue 60).
- After issue 60, only `implement.md` still routes skill files into the
  implementer prompt — and it does so via a path its own text tells the
  orchestrator not to use.

**Therefore:** the canonical flow is already "skills load once during
shaping, then propagate via the shaped doc." `implement.md`'s Steps 3/4
skill references are residue from before issue 60's decision crystallised.

## Approaches considered

### (a) Direction A — keep refs, rewrite the Step 5 paragraph to disambiguate

- Keep `.claude/skills/*/SKILL.md` in Step 3's context list and keep the
  scan bullet in Step 4.
- Rewrite lines 180-183 so it is clear the orchestrator *distills* skill
  knowledge into the brief (selected by judgement) rather than dumping raw
  skill files wholesale into the implementer prompt.
- **Appetite:** small batch.
- **Pros:** preserves the orchestrator's ability to cite skills when
  composing the brief; minimal behavioural change from today's ambiguous
  baseline.
- **Cons:** keeps the volume-maximalist path alive, contradicts the
  direction set by issue 60, and the "distillation" distinction is subtle
  enough that a future editor will re-break it.
- **Rejected because:** issue 60 just ruled that skills do not need to
  load again after shaping. Direction A re-litigates that decision.

### (b) Direction B — drop skill refs from Step 3 & Step 4 *(chosen)*

- Remove the `.claude/skills/*/SKILL.md` entry from Step 3's context list.
- Remove the skill-scan bullet from Step 4's per-story context selection.
- Keep lines 180-183 intact — with A and the scan gone, the paragraph now
  accurately describes the flow (shape bakes skills in; implementer reads
  the shaped doc, not skill files).
- **Appetite:** small batch.
- **Pros:**
  - Smallest coherent diff (two deletions, no rewrites).
  - Extends issue 60's decision (skills load once at shape) to the only
    remaining command where the contradiction still lives.
  - The surviving paragraph (180-183) now matches behaviour with zero
    ambiguity — no subtle orchestrator-vs-implementer rule.
  - Aligns with `design-review` red flag #14 (Non-Obvious Code): today's
    text forces readers to trace which branch "really" runs. Deletion
    removes that burden rather than papering over it.
- **Cons:** the orchestrator loses the documented cue to consult skill
  files when building its own brief. In practice this cue was
  inconsistent anyway, and the shaped doc already surfaces the relevant
  patterns for each story.

### (c) Direction C — mixed (orchestrator consults, implementer doesn't)

- Clarify in Step 5 that the story-implementer agent relies on the shaped
  doc + story + orchestrator-curated brief, and that raw skill files are
  not re-injected after the brief is composed.
- Keep Step 3/4 references so the orchestrator can "consult" skills for
  its own reasoning.
- **Appetite:** small batch.
- **Pros:** accommodates the view that the orchestrator may benefit from
  reading skills even if the implementer does not.
- **Cons:** creates a subtle two-tier rule that is exactly the kind of
  thing issue 60 was written to eliminate. A future edit that says "the
  brief carries skill excerpts" would once again route raw skill content
  to the implementer without violating the literal text.
- **Rejected because:** Direction B already captures the intended
  behaviour with no rule-maintenance cost. C introduces a distinction
  that is easy to collapse back into the original contradiction.

## Strategy

Single-file documentation edit to `claude/commands/mantle/implement.md`:

1. In Step 3, remove the `.claude/skills/*/SKILL.md` line (currently
   line 106) from the context-file bullet list. Leave every other line
   unchanged.
2. In Step 4, remove the `.claude/skills/*/SKILL.md` scan bullet
   (currently lines 145-147) from the per-story context-selection list.
   Leave the surrounding bullets (`learnings/`, `decisions/`) unchanged.
3. Leave lines 180-183 intact — with the two deletions above, the
   paragraph now correctly and unambiguously describes the flow.
4. Do not renumber steps, do not touch Step 5's context-brief
   instruction, do not modify `shape-issue.md`, `plan-stories.md`, or
   `build.md`.

Commit message: `docs(issue-61): reconcile implement.md skill-file injection contradiction`.

## Fits architecture by

- Respects the `core/` ↔ `cli/` ↔ `claude/` separation — change is
  strictly in the Claude Code prompt layer.
- Reinforces the single-owner principle for skill loading: shape is the
  place skills are read; downstream stages consume the shaped doc.
- Consistent with issue 60's just-shipped decision — this is the same
  cleanup applied to the next command in the pipeline.
- Aligns with `design-review` guidance on Non-Obvious Code (red flag
  #14): contradictory instructions force readers to trace runtime
  behaviour to resolve intent. Deletion removes that burden at source.

## Does not

- Does not modify `shape-issue.md`, `plan-stories.md`, or `build.md`.
- Does not change any Python source or test.
- Does not change the CLI surface of `mantle update-skills`,
  `mantle compile`, or any other command.
- Does not remove the `mantle update-skills --issue {NN}` /
  `mantle compile --issue {NN}` calls at the top of Step 3 — those
  ensure skill definitions exist on disk for other consumers
  (status/resume templates), even though the implementer will not read
  them.
- Does not add a new acceptance criterion about runtime flow —
  behaviour is unchanged for any issue whose shaped doc already
  carries skill patterns (i.e., every shaped issue going forward).
