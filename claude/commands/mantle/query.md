---
argument-hint: [question]
allowed-tools: Read, Bash(mantle *), Glob, Grep
---

Search your accumulated vault knowledge and synthesize a grounded answer to a
question.

All operations are user-triggered — do not run searches or synthesis in the
background.

## Step 1 — Get the question

Use the question from $ARGUMENTS. If no argument was provided, ask the user
what they want to know.

## Step 2 — Check for existing distillations

Run:

```bash
mantle list-distillations --topic "<topic>"
```

If distillations are found, load each one:

```bash
mantle load-distillation --path "<path>"
```

Start your answer with the distilled knowledge and note when it was created.
Any new sources you find below will supplement it.

If an existing distillation covers the topic, start with it and note any new
sources since it was created.

## Step 3 — Search vault content

Search broadly, then narrow. Start with directory listings and keyword grep,
then read the most relevant files.

Search across these locations:

- `.mantle/learnings/` — past issue learnings
- `.mantle/decisions.md` — recorded project decisions
- `.mantle/sessions/` — session logs
- `.mantle/brainstorms/` — brainstorm outputs
- `.mantle/research/` — research reports
- `.mantle/shaped/` — shaped issue documents
- Personal vault skills via `mantle list-skills`

Use Grep to search within matched files for keywords from the question. Read
the most relevant files in full.

## Step 4 — Synthesize an answer

Synthesize a clear, direct answer grounded entirely in the retrieved content.

Every answer must cite source notes with file paths (e.g.,
"(source: .mantle/learnings/issue-27.md)"). Never state facts without a
source.

Structure the answer as:

> **Answer**: {direct response to the question}
>
> **Supporting evidence**:
> - {finding 1} (source: {file path})
> - {finding 2} (source: {file path})
>
> **Gaps**: {what the vault doesn't cover, if anything}

## Step 5 — Offer to save as distillation

If the answer draws on three or more sources and covers a topic that is likely
to be queried again, offer:

> This answer synthesizes {N} sources. Would you like to save it as a
> distillation so future queries on this topic can start from it?

If the user agrees, suggest running `/mantle:distill` with the topic.
