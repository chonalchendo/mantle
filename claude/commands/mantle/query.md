---
description: Search your accumulated vault knowledge and synthesize a grounded answer to a question
argument-hint: [question]
allowed-tools: Read, Bash(mantle *), Glob, Grep
---

Search your accumulated vault knowledge and synthesize a grounded answer to a
question.

All operations are user-triggered — do not run searches or synthesis in the
background.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Get the question"
2. "Step 2 — Check for existing distillations"
3. "Step 3 — Search vault content"
4. "Step 4 — Synthesize an answer"
5. "Step 5 — Offer to save as distillation"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

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

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Search broadly, then narrow. Start with directory listings and keyword grep,
then read the most relevant files.

Search across these locations:

- `$MANTLE_DIR/learnings/` — past issue learnings
- `$MANTLE_DIR/decisions.md` — recorded project decisions
- `$MANTLE_DIR/sessions/` — session logs
- `$MANTLE_DIR/brainstorms/` — brainstorm outputs
- `$MANTLE_DIR/research/` — research reports
- `$MANTLE_DIR/scouts/` — scout reports from external repo analysis
- `$MANTLE_DIR/shaped/` — shaped issue documents
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

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "query"

Keep the log under ~200 words following the session log format (Summary, What
Was Done, Decisions Made, What's Next, Open Questions).
