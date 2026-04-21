---
issue: 84
title: build.md reads tier and passes per-stage model to every agent spawn
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a Mantle user on API billing, I want `/mantle:build` to route each stage to its configured model, so mechanical stages use cheap models while reasoning-heavy stages use Opus — cutting run cost without me editing seven prompts.

## Depends On

Story 3 — calls `mantle model-tier` at orchestration time.

## Approach

Prompt-only change to `claude/commands/mantle/build.md`. Insert a tier-resolution step early (before the first Agent spawn) that runs `mantle model-tier` and records the resolved JSON in the conversation. Every downstream `Agent(subagent_type=..., ...)` call then passes `model: <stage-model>` alongside the existing `prompt:` parameter. Build-mode skips to `implement.md`, `simplify.md`, `verify.md` already exist — the models flow through because those commands spawn their own inner agents which inherit the orchestrator-passed model when build.md spawns them. Inner-command model wiring is out of scope for this story (no `claude/commands/mantle/implement.md` edits).

## Implementation

### claude/commands/mantle/build.md (modify)

1. **Rename Step 3 header** from `## Step 3 — Load skills` to `## Step 3 — Load skills and model tier`. Update the step list in the intro (line 39 area) to match.

2. **Append a new sub-step** at the end of Step 3, after the existing `Report:` block (currently reporting skills loaded/created):

   ```markdown
   5. Run `mantle model-tier` and record the resulting JSON in this
      conversation as `STAGE_MODELS`. Every Agent spawn later in this
      pipeline passes the relevant stage's model via the Agent tool's
      `model:` parameter — e.g. Step 7 (Simplify) uses
      `STAGE_MODELS.simplify`, Step 8 (Verify) uses `STAGE_MODELS.verify`.
      If a stage's resolved value is unknown to the Agent tool, drop the
      `model:` parameter for that spawn (Claude Code will default to the
      session model) and surface a warning in the Step 9 summary.

   Report:
   > **Model tier:** {preset from config.md or "balanced (fallback)"} —
   > shape={shape}, plan_stories={plan_stories}, implement={implement},
   > simplify={simplify}, verify={verify}, review={review},
   > retrospective={retrospective}
   ```

3. **Extend the existing Performance note in Step 4** (Shape) by appending this parenthetical to the note's last sentence:

   > (Model tier only applies when an agent is spawned — `STAGE_MODELS.shape` is reserved for future out-of-process shape agents.)

   Do NOT add a second Performance note — the existing one is preserved and only the parenthetical tail is new.

4. **Extend the existing Performance note in Step 5** (Plan stories) by appending the parallel parenthetical:

   > (Model tier only applies when an agent is spawned — `STAGE_MODELS.plan_stories` is reserved for future out-of-process plan-stories agents.)

   Do NOT add a second Performance note.

5. **Update the Implement step** (Step 6, Branch B "Agent-path") by adding a new bullet to the "build-mode overrides" list (the list currently containing "Skip user confirmation on issue selection" and "Don't recommend next steps"):

   > - Pass `STAGE_MODELS.implement` to every per-story Agent spawn inside
   >   implement.md's Step 4 loop (the `smart` subagent spawns). Other Agent
   >   spawns inside implement.md (e.g. retry agents) use the same value.

6. **Update the Simplify step** (Step 7): the existing prompt reads

   > Record the file list. Then spawn an Agent (`subagent_type: "refactorer"`)
   > with this prompt:

   Add a line right after that sentence, before the blockquoted prompt:

   > Use model `STAGE_MODELS.simplify` for this agent spawn.

7. **Update the Verify step** (Step 8): the existing prompt reads

   > Spawn an Agent (`subagent_type: "general-purpose"`) with this prompt:

   Add a line right after that sentence, before the blockquoted prompt:

   > Use model `STAGE_MODELS.verify` for this agent spawn.

8. **Update the skill-creation agent spawn in Step 3** (the existing sub-step 3 that creates missing skills by spawning a `general-purpose` Agent). After the existing prompt block, add:

   > Use model `STAGE_MODELS.plan_stories` for this agent spawn.

   (If `STAGE_MODELS` has not yet been resolved at that point — because this sub-step runs BEFORE the new tier-resolution sub-step 5 — re-order: move the tier-resolution step to be sub-step 3 in Step 3, and the skill-creation step to sub-step 4. Ordering: `list-skills` → `update-skills` → `model-tier` → skill-creation agent → `compile`.)

9. **Add a summary-only Step 9 line** noting the tier used:

   > | Model tier | {preset} |

   in the summary table (between the existing "Shape" and "Skills" rows).

#### Design decisions

- **Build.md is the only file touched.** Inner commands (`implement.md`, `simplify.md`, `verify.md`) keep their prompts intact. This story only changes how `build.md` parameterises its Agent spawns — no cascading prompt edits.
- **Resolved JSON is recorded in-conversation, not re-queried.** `mantle model-tier` runs once at Step 3 and the JSON is held in `STAGE_MODELS`. Avoids seven subprocess calls in one pipeline run.
- **Inline steps (Shape, Plan stories) don't consume STAGE_MODELS.** They execute in the orchestrator's session — no agent to route. The corresponding entries in `STAGE_MODELS` are reserved for future out-of-process variants.
- **Order the tier-resolution step BEFORE skill-creation.** The skill-creation agent needs a model too (`STAGE_MODELS.plan_stories`) — so tier resolution must happen first. The reordering described in point 8 ensures this.
- **Unknown-model fallback.** If Claude Code's Agent tool rejects a resolved model string, drop `model:` and surface the warning in Step 9 rather than failing the pipeline. This lets the pipeline survive typos in `cost-policy.md` without blocking the user.

## Tests

### tests/prompts/test_build_prompt.py (new file or modify existing)

If `tests/prompts/` doesn't contain a build-prompt test, create one. Use `inline_snapshot` for full-body snapshotting of specific sections to catch regressions; simpler substring asserts are fine for the initial pass.

- **test_build_prompt_references_mantle_model_tier**: Read `claude/commands/mantle/build.md` and assert the substring `mantle model-tier` appears (content evidence the tier is resolved).
- **test_build_prompt_references_stage_models_placeholder**: Assert `STAGE_MODELS` appears at least 4 times in `build.md` (once for setup + at least implement/simplify/verify references).
- **test_build_prompt_step3_header_updated**: Assert the substring `Step 3 — Load skills and model tier` appears.
- **test_build_prompt_simplify_and_verify_pass_model**: Assert each of the strings `STAGE_MODELS.simplify`, `STAGE_MODELS.verify`, `STAGE_MODELS.implement`, `STAGE_MODELS.plan_stories` appears in the prompt (proves all four agent-spawning steps are wired).

Fixtures: none — reads the installed `claude/commands/mantle/build.md` file via a path relative to the repo root (look at existing `tests/prompts/` for the path-resolution helper; reuse it).

### tests/test_workflows.py (check for regression only — no changes expected)

Read-only scan: confirm no existing workflow test asserts on the exact Step 3 header; if one does, update it. Otherwise no change.
