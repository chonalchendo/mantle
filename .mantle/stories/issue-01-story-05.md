---
issue: 1
title: Install command + help.md
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Build the `mantle install` command that copies bundled files into `~/.claude/` and the `/mantle:help` command file.

### claude/commands/mantle/help.md

Static markdown listing all 15 v1 commands grouped by workflow phase:

```markdown
# Mantle Commands

## Idea & Validation
- `/mantle:idea` — Log an idea with structured metadata
- `/mantle:challenge` — Challenge your idea from multiple angles

## Design
- `/mantle:design-product` — Create product design (the what and why)
- `/mantle:design-system` — Create system design (the how) with decision logging
- `/mantle:revise-product` — Revise product design + log what changed
- `/mantle:revise-system` — Revise system design + log what changed

## Planning
- `/mantle:plan-issues` — Break work into vertical slice issues
- `/mantle:plan-stories` — Decompose issues into implementable stories

## Implementation
- `/mantle:implement` — Run the implementation orchestration loop

## Verification & Review
- `/mantle:verify` — Run project-specific verification
- `/mantle:review` — Checklist-based human review

## Context & Knowledge
- `/mantle:status` — Show current project state
- `/mantle:resume` — Project briefing and context restore
- `/mantle:add-skill` — Create or update a skill node

## Help
- `/mantle:help` — This command
```

### src/mantle/cli/install.py

Replace the placeholder in `main.py` with a real implementation:

```python
@app.command
def install() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
```

#### Logic

1. Locate bundled `claude/` directory via `importlib.resources.files("mantle").joinpath("claude")`
2. Determine target: `Path.home() / ".claude"`
3. If manifest exists at target (`mantle-file-manifest.json`):
   a. Compute source hashes from bundled files
   b. Load existing manifest
   c. Compare using `core.manifest.compare_manifests`
   d. For `user_modified` files: prompt with Rich `Confirm.ask()` per file ("File X has been modified. Overwrite?")
   e. Skip files where user declines
4. Copy all non-skipped files preserving directory structure
5. Write updated manifest
6. Print Rich-formatted summary:
   - Files installed (count)
   - Files skipped (user declined, list paths)
   - "Run /mantle:help in Claude Code to see available commands"

#### Edge cases

- First install (no manifest exists): copy everything, no prompts
- Re-install with no changes: overwrite silently, update manifest
- Target directories don't exist: create them
- Bundled directory is empty or missing: error with clear message

### Wire into cli/main.py

Import `install` from `cli/install.py` and register with the Cyclopts app. Remove the placeholder `NotImplementedError`.

## Tests

All tests use `tmp_path` for both source and target directories (never touch real `~/.claude/`). Mock `importlib.resources.files` to point to test fixtures. Mock `Path.home()` to point to tmp_path.

- **First install**: copies all files from source to target, creates manifest
- **First install**: creates intermediate directories that don't exist
- **First install**: Rich output shows file count and success message
- **Re-install no changes**: overwrites silently, no prompts, updates manifest
- **Re-install with user-modified file (user confirms)**: file is overwritten, manifest updated
- **Re-install with user-modified file (user declines)**: file is skipped, manifest reflects original hash
- **Re-install with new source files**: new files copied without prompt
- **Re-install with removed source files**: removed from target (or left in place — decide based on safety)
- **help.md content**: file exists in bundled package, references all 15 commands by name
- **help.md groups**: commands are grouped by workflow phase (Idea, Design, Planning, Implementation, Verification, Context, Help)
- **After install**: help.md is present at `{target}/commands/mantle/help.md`
- **Empty source directory**: raises clear error
- **End-to-end**: `mantle install` runs without error (subprocess, using tmp dirs via monkeypatch)
