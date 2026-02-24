# Mantle

AI workflow engine with persistent context. Built for developers who use Claude Code.

## The Problem

AI coding agents are stateless. Every session starts from zero — context is lost, decisions are forgotten, and you end up repeating yourself or pasting notes between tools. Worse, agents rubber-stamp bad ideas instead of challenging them.

Mantle fixes this by giving your AI agent a memory, a structured workflow, and the discipline to validate ideas before building them.

## What It Does

Mantle manages the full lifecycle of AI-assisted development:

**Idea to implementation** — structured phases from idea capture and challenge through product design, system design, planning, implementation, verification, and review.

**Persistent context** — project state, decisions, session logs, and a personal knowledge vault stored as markdown with YAML frontmatter. Everything is git-tracked and human-readable.

**Compiled knowledge** — vault state is pre-compiled into Claude Code commands so your AI gets instant context, not expensive runtime file queries.

**Cross-project learning** — a personal vault links skills, patterns, and lessons learned across projects via Obsidian wikilinks.

## Quick Start

Requires Python 3.14+.

```bash
# Install
uv tool install mantle-ai

# Mount commands into Claude Code
mantle install --global

# Initialize a project
cd your-project
mantle init

# Set up a personal vault (optional)
mantle init-vault ~/vault
```

Once initialized, `.mantle/` is created in your project with:

```
.mantle/
  state.md        # Project state and metadata
  config.md       # Project configuration
  tags.md         # Tag taxonomy
  decisions/      # Decision logs with rationale
  sessions/       # Auto-generated session logs
  issues/         # Vertical slice issue specs
  stories/        # Implementable story specs
```

Start a Claude Code session in your project and use `/mantle:help` to see available commands.

## How It Works

Mantle is a Python CLI (`mantle`) that also installs slash commands into Claude Code (`/mantle:*`). The core library handles all state and vault operations. The CLI is a thin wrapper. Claude Code commands compile context from your vault and orchestrate AI-assisted workflows.

All state lives in plain markdown files with YAML frontmatter — versioned in git, readable by any tool, editable by hand.

## Status

Early development. `mantle init`, `mantle init-vault`, and `mantle install` are working. The workflow commands (`/mantle:idea`, `/mantle:challenge`, `/mantle:implement`, etc.) are in progress.

## License

MIT
