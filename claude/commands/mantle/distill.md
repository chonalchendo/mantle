---
argument-hint: [topic]
allowed-tools: Read, Bash(mantle *), Glob, Grep
---

Synthesize accumulated vault knowledge on a topic into a persistent distillation
note.

All operations are user-triggered — do not run searches or synthesis in the
background.

## Step 1 — Get the topic

Use the topic from $ARGUMENTS. If no argument was provided, ask the user what
topic to distill.

## Step 2 — Check for existing distillation

Run:

```bash
mantle list-distillations --topic "<topic>"
```

If a distillation already exists, load it and note its creation date. When
re-distilling, incorporate new sources since last distillation alongside any
prior synthesis.

## Step 3 — Search vault for related content

Search across these locations:

- `.mantle/learnings/` — past issue learnings
- `.mantle/decisions.md` — recorded project decisions
- `.mantle/sessions/` — session logs
- `.mantle/brainstorms/` — brainstorm outputs
- `.mantle/research/` — research reports
- `.mantle/shaped/` — shaped issue documents
- Personal vault skills via `mantle list-skills`

Use Grep to find files that mention the topic. Read up to 10-15 of the most
relevant source files in full.

## Step 4 — Synthesize

Write a synthesis of 1-2 paragraphs. Dense and factual. No padding.

Include wikilinks ([[note-name]]) to every source note used. For example:
"The shaping process ([[issue-27-shaped]]) established..."

Keep the synthesis to 1-2 paragraphs. Dense and factual.

## Step 5 — Save the distillation

The saved distillation must include staleness metadata via the CLI's
source_count and source_paths fields.

Save by running:

```bash
mantle save-distillation \
  --topic "<topic>" \
  --source-paths "<path1>" \
  --source-paths "<path2>" \
  --content "<synthesized content>"
```

Pass one `--source-paths` flag per source file used.

## Step 6 — Report

After saving, report:

> Distilled **{topic}** from {N} sources:
> - {source 1}
> - {source 2}
> ...
>
> Saved to: {path returned by CLI}
