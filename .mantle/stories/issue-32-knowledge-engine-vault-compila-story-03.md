---
issue: 32
title: Query and distill prompt files
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want /mantle:query and /mantle:distill slash commands so that I can search my accumulated vault knowledge and synthesize topic summaries.

## Depends On

Story 2 (prompts invoke CLI commands: save-distillation, list-distillations, load-distillation).

## Approach

Create two new Claude Code prompt files that orchestrate vault search and distillation using existing mantle CLI tools. Follow the pattern of brainstorm.md (Skill tool triggers these prompts). Query searches vault content and synthesizes answers; distill creates persistent knowledge notes. Both are user-triggered (AC 7).

## Implementation

### claude/commands/mantle/query.md (new file)

Create a prompt file for /mantle:query:

**Frontmatter:**
\`\`\`yaml
---
argument-hint: [question]
allowed-tools: Read, Bash(mantle *), Glob, Grep
---
\`\`\`

**Prompt structure:**
1. Accept user's natural language question (from $ARGUMENTS or ask)
2. Check for existing distillations on the topic:
   - Run \`mantle list-distillations --topic "<extracted topic>"\`
   - If found, run \`mantle load-distillation --path "<path>"\` and incorporate into answer
3. Search vault content across multiple directories:
   - \`.mantle/learnings/\` — past implementation learnings
   - \`.mantle/decisions.md\` — architectural decisions
   - \`.mantle/sessions/\` — session logs
   - \`.mantle/brainstorms/\` — brainstorm sessions
   - \`.mantle/research/\` — research notes
   - \`.mantle/shaped/\` — shaped issue approaches
   - Personal vault skills via \`mantle list-skills\` then reading matched skills
4. Use Grep to search content within matched files for relevant keywords
5. Synthesize answer grounded in retrieved content
6. **Cite sources**: Every factual claim must include the source file path in parentheses, e.g., "(source: .mantle/learnings/issue-27.md)"
7. Offer to save the answer as a distillation note if the synthesis is substantial

**Key instructions in prompt:**
- "Search broadly, then narrow. Start with directory listings and keyword grep, then read the most relevant files."
- "Every answer must cite source notes with file paths (AC 2). Never state facts without a source."
- "If an existing distillation covers the topic, start with it and note any new sources since it was created (staleness check: compare source_count and source_paths against current vault content)."
- "All operations are user-triggered — do not run searches or synthesis in the background."

### claude/commands/mantle/distill.md (new file)

Create a prompt file for /mantle:distill:

**Frontmatter:**
\`\`\`yaml
---
argument-hint: [topic]
allowed-tools: Read, Bash(mantle *), Glob, Grep
---
\`\`\`

**Prompt structure:**
1. Accept topic from $ARGUMENTS or ask
2. Check for existing distillation on this topic:
   - Run \`mantle list-distillations --topic "<topic>"\`
   - If found, load it and note which sources it already covers (for incremental distillation)
3. Search vault for all content related to the topic:
   - Same search strategy as query.md (learnings, decisions, sessions, brainstorms, research, shaped, skills)
   - Track every source file path discovered
4. Read the most relevant source files (up to 10-15 to stay within context)
5. Synthesize into 1-2 concise paragraphs:
   - Dense, factual summary
   - Include wikilinks to every source note: \`[[source-note-name]]\` (AC 4)
   - Format: synthesis paragraphs followed by a "Sources" section listing all source paths
6. Save via CLI:
   \`\`\`
   mantle save-distillation \
     --topic "<topic>" \
     --source-paths "<path1>" --source-paths "<path2>" ... \
     --content "<synthesized content with wikilinks and sources section>"
   \`\`\`
7. Report what was distilled and how many sources were synthesized

**Key instructions in prompt:**
- "Include wikilinks ([[note-name]]) to every source note used in the synthesis body (AC 4)."
- "The saved distillation must include staleness metadata via the CLI's source_count and source_paths fields (AC 5)."
- "If re-distilling an existing topic, incorporate new sources found since the last distillation — distillations compound over time."
- "Keep the synthesis to 1-2 paragraphs. Dense and factual, not verbose."
- "All operations are user-triggered (AC 7)."

#### Design decisions

- **Prompt-only, no Python**: Query and distill are orchestration problems — the AI reads files, searches, and synthesizes. No Python code needed beyond the CLI commands in story 2.
- **Grep for search**: The vault is small enough that grep-based search across .mantle/ directories is fast and sufficient. No indexing needed.
- **Wikilinks in body**: Obsidian wikilinks ([[note]]) in the distillation body create clickable graph connections in the user's vault.
- **Staleness via source comparison**: On re-distill, compare current sources vs stored source_paths to detect new material.

## Tests

### tests/prompts/test_query_distill_prompts.py (new file)

Since these are prompt files (not Python), tests verify the files exist and have correct structure:

- **test_query_prompt_exists**: claude/commands/mantle/query.md exists
- **test_query_prompt_has_frontmatter**: contains argument-hint and allowed-tools
- **test_query_prompt_mentions_citations**: body contains "cite" or "source" instruction
- **test_query_prompt_mentions_distillations**: body references checking existing distillations
- **test_distill_prompt_exists**: claude/commands/mantle/distill.md exists
- **test_distill_prompt_has_frontmatter**: contains argument-hint and allowed-tools
- **test_distill_prompt_mentions_wikilinks**: body contains "wikilink" or "[[" instruction
- **test_distill_prompt_mentions_staleness**: body references staleness or source tracking
- **test_distill_prompt_invokes_save**: body contains "mantle save-distillation" CLI call

Fixtures: read files from the project's claude/commands/mantle/ directory using Path resolution.