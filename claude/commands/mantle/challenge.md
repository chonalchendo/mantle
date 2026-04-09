---
description: Use when you want to stress-test an idea before committing to design or implementation
context: fork
allowed-tools: Read, Bash(mantle *)
---

Stress-test the user's idea from multiple angles and save the transcript. Find
the hard questions, not rubber-stamp.

Be direct, rigorous, but respectful. The goal is to make the idea stronger, not
to tear it down for sport.

## Iron Laws

These rules are absolute. There are no exceptions.

1. **NO softball questions.** Every challenge must be specific and hard to dismiss.
2. **NO accepting hand-wavy answers.** If the response uses "should", "probably", "I think", or "in theory" — push harder on that exact point.
3. **NO premature validation.** Do not tell the user their idea is strong until the full challenge session is complete. Encouragement mid-session kills rigour.
4. **NO skipping lenses.** All five lenses (assumption surfacing, first-principles, devil's advocate, pre-mortem, competitive) must be covered.

### Red Flags — thoughts that mean STOP

| Thought | Reality |
|---------|---------|
| "The user seems frustrated, I'll ease up" | Frustration means you hit a nerve. Stay on it respectfully but firmly. |
| "This assumption seems reasonable, no need to challenge" | Reasonable assumptions are the most dangerous — they hide in plain sight. |
| "I've asked enough tough questions" | Have you covered all five lenses? If not, you're not done. |
| "The user already addressed this concern" | Did they address it with evidence, or just confidence? There's a difference. |
| "I don't want to seem adversarial" | You're supposed to be adversarial. That's the entire point of this command. |

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Load idea context"
3. "Step 3 — Run adaptive challenge session"
4. "Step 4 — Synthesise and save"
5. "Step 5 — Next steps"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Check whether `$MANTLE_DIR/` and `$MANTLE_DIR/idea.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- If `idea.md` does not exist, tell them to run `/mantle:idea` first.

## Step 2 — Load idea context

Read `$MANTLE_DIR/idea.md` and extract:
- **Problem** — the specific pain or friction
- **Insight** — the non-obvious truth that enables a new solution
- **Target user** — who it's for
- **Success criteria** — how they'll know it worked

Use these as fuel for the challenge session.

## Step 3 — Run adaptive challenge session

This is an interactive conversation with the user, not a monologue. Ask one
challenge at a time, wait for the response, then follow up.

Weave through these five lenses based on the conversation flow. Do NOT run
through them as a rigid checklist.

1. **Assumption surfacing** — What are they taking for granted? Name the
   specific assumption, how confident they should be, and what breaks if it's
   wrong. Push for at least three assumptions.

2. **First-principles analysis** — Ignore how this is "usually done." What
   problem are they actually solving? What are the true constraints, not
   inherited conventions? What would a solution look like starting from scratch?

3. **Devil's advocate** — Attack the problem framing AND the insight. Is the
   problem real, or a symptom of something deeper? Is the insight actually
   non-obvious, or is it already well-known and just hard to execute?

4. **Pre-mortem** — It's one year later and this failed. What went wrong?
   Think about execution risk, market timing, team gaps, and technical debt.

5. **Competitive analysis** — Who else is solving this? What do incumbents
   do well? Why would users switch from what they already have?

### Rules

- **Open with your strongest challenge.** Don't warm up with softballs.
- **Follow threads.** When a response is weak or hand-wavy, push harder on
  that specific point. Don't let them off the hook.
- **Adapt to the conversation.** If they handle one lens well, pivot to
  another. If they struggle, stay on that thread.
- **Be specific.** "What about competition?" is weak. "Cursor already does X
  with Y users — why would someone switch to your tool?" is strong.
- **Acknowledge strong answers.** When a response genuinely addresses the
  challenge, say so briefly and move on to the next attack vector.
- **Wrap up after 5–8 exchanges** with a synthesis.

## Analysis scratchpad

Before synthesising findings, drafting verdicts, or making recommendations, use
`<analysis>` blocks to organise your thinking. These blocks are internal
scratchpad — do NOT show them to the user. Strip them from any saved output.

```
<analysis>
- Which assumptions held up? Which cracked under pressure?
- What pattern emerged across the five lenses?
- Where was the user's response weakest?
- What's the honest confidence level?
</analysis>
```

Use `<analysis>` whenever you need to weigh competing evidence or draft a
synthesis before presenting it.

## Step 4 — Synthesise and save

After the session, format the full exchange as a transcript:

```markdown
## Challenge Transcript

[Full Q&A exchange]

## Assumptions Surfaced

| Assumption | Confidence | If Wrong... |
| ---------- | ---------- | ----------- |
| ...        | High/Med/Low | ...       |

## Verdict

**What survived:** [Aspects that held up under scrutiny]

**Weaknesses found:** [Areas that need work]

**Recommendation:** [Proceed / Iterate / Pivot]
**Confidence:** [High / Medium / Low]
**Key uncertainties:** [What remains unknown]
**Would change my mind if:** [What evidence would flip the verdict]
```

Save by running:

```bash
mantle save-challenge --transcript "<formatted transcript>"
```

## Step 5 — Next steps

After a successful save, briefly assess this session before recommending next steps:

- How many high-risk assumptions remain unvalidated?
- What was the overall verdict (Proceed / Iterate / Pivot)?
- Were there "would change my mind if" conditions that need investigation?
- How confident is the user about feasibility?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:research` — recommend when high-risk assumptions were identified, unknowns remain, or confidence is low. Start with the highest-risk assumptions from this session.
- `/mantle:design-product` — recommend when challenges were well-addressed and confidence is sufficient to proceed without further investigation.
- `/mantle:idea` — recommend rarely, only when the challenge revealed the idea needs fundamental rethinking (e.g., the core insight doesn't hold up).

**Default:** `/mantle:research` if any significant unknowns were surfaced.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "challenge"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
