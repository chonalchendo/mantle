---
issue: 4
title: Claude Code challenge command
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create the static Claude Code command prompt for `/mantle:challenge`. The
challenger persona and lenses are inlined in the command prompt itself — no
separate agent file needed since the session is interactive (user responds to
each challenge). No code tests — static markdown only.

### claude/commands/mantle/challenge.md

Static prompt guiding Claude through the `/mantle:challenge` workflow. Adopts
the persona of an experienced investor doing due diligence.

1. **Check prerequisites** — Read `.mantle/` and `.mantle/idea.md`. If missing, direct user to run `mantle init` or `/mantle:idea` first.
2. **Load idea context** — Extract hypothesis, target user, and success criteria from `idea.md` to fuel the session.
3. **Run adaptive challenge session** — Interactive conversation (one challenge at a time, wait for response, follow up). Weave through five lenses:
   - Assumption surfacing (with confidence/consequences)
   - First-principles analysis (ignore conventions, derive from fundamentals)
   - Devil's advocate (attack the core hypothesis)
   - Pre-mortem (one year later, this failed — what went wrong?)
   - Competitive analysis (who else, why switch?)
4. **Synthesise and save** — Format transcript with `## Challenge Transcript`, `## Assumptions Surfaced` (table), and `## Verdict` sections (what survived, weaknesses, recommendation, confidence, key uncertainties, what would change my mind). Save via `mantle save-challenge --transcript`.
5. **Next steps** — Suggest `/mantle:design-product` to define the product.

## Tests

No tests — static markdown file only.
