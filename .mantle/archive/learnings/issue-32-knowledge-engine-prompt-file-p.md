---
issue: 32
title: Knowledge engine — prompt file placement, command convention alignment
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-06'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Sixth consecutive clean build**: Zero blocked stories, zero retries across all 3 stories. Build pipeline reliability continues (issues 27, 28, 30, 33, 31, 32).
- **Shaped plan held exactly**: Prompt + Thin Core approach was correct. Small batch appetite accurate. Core module followed brainstorm.py pattern for first-try completions.
- **Pattern reuse still compounding**: Stories 1 and 2 (core + CLI) completed first-try by following brainstorm.py and cli/brainstorm.py patterns.

## Harder Than Expected

- **Prompt files placed in wrong directory**: Story 3 agent created query.md and distill.md in ~/.claude/commands/mantle/ (global install location) instead of claude/commands/mantle/ (project-local, git-tracked). Required manual move + test path fix.
- **Prompt convention gaps**: Generated prompts were missing description frontmatter, session logging section, and TaskCreate/TaskUpdate step tracking that all other commands use. Required two additional fix commits.

## Wrong Assumptions

- **Story spec path ambiguity**: The story spec said "claude/commands/mantle/query.md (new file)" but also referenced ~/.claude/commands/mantle/ as the installed location. The agent chose the wrong one. Story specs for prompt files must use unambiguous project-relative paths.

## Recommendations

1. **Use explicit project-relative paths for prompt file stories**: Always specify `claude/commands/mantle/<name>.md` with a note: "This is the project source path, NOT ~/.claude/commands/mantle/". The agent will otherwise resolve to the global install location.
2. **Include command convention checklist in prompt-file stories**: Story specs for new commands should explicitly list: description frontmatter, TaskCreate step listing, session logging section. These are easy to miss because they're conventions, not functional requirements.
3. **Sonnet is sufficient for prompt-only stories**: Story 3 used sonnet and completed first-try (content was correct, just wrong location). For prompt file stories, sonnet handles the task well.