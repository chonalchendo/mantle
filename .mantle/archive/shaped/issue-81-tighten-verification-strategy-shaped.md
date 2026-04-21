---
issue: 81
title: Tighten verification-strategy handoff to prevent agents skipping config.md
approaches:
- Directive precedence language in the two handoff sites
chosen_approach: Directive precedence language in the two handoff sites
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-21'
updated: '2026-04-21'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen approach: Directive precedence language in the two handoff sites

The issue's 'What to build' section already prescribes the exact reworded shape
— config.md first, introspect-project only as a last-resort fallback — so no
alternatives to weigh. Per shape-issue.md's meta-template carve-out, this is
editorial prose work on Mantle's own command templates; no vault skill applied.

### Survey of handoff sites

Only two places embed the loose conditional:

- `claude/commands/mantle/verify.md` Step 3 (lines 97–122): uses "If no
  strategy is found" / "If a strategy is found" branching. Reads config.md
  first but the branch labels read as parallel alternatives, not as precedence.
- `claude/commands/mantle/build.md` Step 8 (lines 383–390): the verifier
  sub-agent override bullet says "If no verification strategy is configured,
  run mantle introspect-project". This is the strongest case of the loose
  conditional — it names introspect-project before the config.md check.

`fix.md` (lines 144–145) already uses directive prose ("Read config.md for
the verification strategy") with no introspect-project fallback mentioned. Not
edited.

## Strategy

1. **verify.md Step 3**: Replace the "If no strategy is found" / "If a
   strategy is found" structure with an explicit three-step precedence:
   (1) Check config.md for a non-empty `verification_strategy`. (2) If
   present, display and use it verbatim. (3) Only if absent or empty, fall
   back to `mantle introspect-project` as a last-resort first-use flow.
   Keep the first-use flow body as-is but nest it under the "only if" branch
   so the precedence is structurally obvious.
2. **build.md Step 8 verifier-agent prompt**: Replace the "If no verification
   strategy is configured, run mantle introspect-project" bullet with a
   directive precedence bullet: "Check $MANTLE_DIR/config.md for a non-empty
   verification_strategy field. If present, use it verbatim. Only if absent or
   empty, run mantle introspect-project as a last-resort fallback, then save
   via mantle save-verification-strategy."

Both edits preserve the underlying behavior — they only tighten the prose so
agents treat config.md as the source of truth and introspect-project as a
fallback, never as a default.

## Fits architecture by

Touches only `claude/commands/mantle/*.md` prompt templates — the claude-code
slice. No Python code, no CLI surface change, no new config fields. The
precedence itself is already what mantle verify-strategy commands expect; this
issue is about communicating that precedence unambiguously to agents.

## Does not

- Change `mantle introspect-project` CLI behavior (out of AC scope).
- Touch `fix.md` (already directive — reads config.md, no loose conditional).
- Add new CLI commands or frontmatter fields.
- Rework the introspection subcommand itself.
- Rework the "Strategy evolution" step (Step 7.5 in verify.md) — that path
  intentionally starts from the current strategy, not config.md.