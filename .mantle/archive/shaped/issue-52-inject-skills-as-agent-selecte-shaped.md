---
issue: 52
title: Inject skills as agent-selected context into shaping and story planning
approaches:
- Explicit read — prompt tells agent to Read all matched skill files after update-skills
- Agent-curated selection — enrich list-skills output with descriptions, agent picks
  2-4 to read
chosen_approach: Agent-curated selection
appetite: small batch
open_questions:
- Should plan-stories also tag stories with skills for implement to use, or is that
  a separate issue?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-11'
updated: '2026-04-11'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen Approach: Agent-curated selection

### Rationale

Skills are compiled to .claude/skills/ but agents never explicitly read them during shaping or story planning — they rely on Claude Code's trigger mechanism, which often doesn't fire because the conversation context doesn't match trigger patterns. The user has to manually tell the agent to read specific skills.

Approach A (explicit read of all matched skills) was rejected because `mantle update-skills --issue` matches too broadly — 15+ skills for a typical issue, most tangentially related. Reading all of them would bloat the context window.

Approach B enriches `mantle list-skills` to show one-line descriptions alongside slugs, giving the agent enough information to make a targeted selection (2-4 skills) before reading full content. This keeps context tight while ensuring domain knowledge is loaded.

### Approaches Considered

**A: Explicit read** — After `mantle update-skills --issue`, prompt tells agent to Read every matched skill's references/core.md.
- Appetite: Small batch
- Tradeoff: Solves "skills aren't read" but not "too many match" — risks context bloat
- Rejected because: broad matching + full reads = wasted context budget

**B: Agent-curated selection (chosen)** ��� Enrich `mantle list-skills` with descriptions. Agent scans the list, selects 2-4 most relevant, reads only those.
- Appetite: Small batch
- Tradeoff: Relies on agent judgment (flexible but variable) vs algorithmic matching (deterministic but naive)
- Chosen because: agent already has the issue in context and can judge relevance better than keyword matching. Small CLI enhancement (one new core function) enables informed selection.

**C: CLI-rendered skill brief** — New command scores skill relevance and returns a condensed brief.
- Dropped because: relevance scoring (keyword or embedding) is either naive or heavy. The agent with descriptions in front of it makes better selection decisions than any keyword algorithm.

### Rabbit Holes

- Building a relevance scoring system — agent judgment with good descriptions is sufficient
- Story-level skill tagging — valuable but separate concern, keep out of this issue
- Changing skill format/anatomy — that's issue 53

### No-Gos

- No changes to skill format or compilation pipeline
- No relevance scoring algorithm
- No story-level skills metadata field
- No changes to `mantle update-skills --issue` matching

### Side-Effect Impact Scan

- `mantle list-skills` output format changes (adds descriptions) — any scripts parsing the old format would break. No known downstream parsers beyond prompt instructions.
- Prompt changes affect agent behaviour in shape-issue, plan-stories, and implement — no CLI ordering dependencies.

## Code Design

### Strategy

**1. Deepen `core/skills.py` interface** — Add `SkillSummary` model and `list_skill_summaries()` function that returns `(slug, description)` pairs. Follows "deep modules" and "pull complexity downward" from software-design-principles skill — callers get what they need without loading full files separately.

```python
class SkillSummary(pydantic.BaseModel, frozen=True):
    slug: str
    description: str

def list_skill_summaries(project_dir: Path, *, tag: str | None = None) -> list[SkillSummary]:
    ...
```

Existing `list_skills() -> list[Path]` stays unchanged for backward compatibility.

**2. Enhance CLI output** — `list-skills` prints descriptions by default using the new core function. Output format: `  - {slug} — {description}`, one per line, parseable.

**3. Update three prompt files with agent-curated selection instructions:**

- **shape-issue.md** step 2 (Load skills): run `mantle list-skills`, select 2-4 skills by description, Read each selected skill's `.claude/skills/{slug}/references/core.md`.
- **plan-stories.md**: move skill loading from step 5c (after stories saved) to step 2 (before proposing stories). Same selection instruction.
- **implement.md** step 4 (context brief): refine "Required reading injection" so orchestrator selects per-story skills from the enriched list rather than dumping all skills_required.

### Fits Architecture By

- `core/skills.py` gains a new model and function — core stays a library, CLI stays thin.
- Dependency rule: core returns data, CLI formats, prompts consume CLI output.
- Existing `list_skills()` not modified — no change amplification.
- Follows "general-purpose interfaces" — descriptions shown by default (common case), not behind --verbose.

### Does Not

- Does not add story-level `skills` metadata field (future work)
- Does not change `mantle update-skills --issue` matching algorithm
- Does not build relevance scoring — agent judgment is the selection mechanism
- Does not modify skill format or anatomy (issue 53)
- Does not change how `mantle compile` renders skills to `.claude/skills/`
- Does not handle vault-not-configured differently (existing skip-and-warn stays)