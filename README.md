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

Once initialized, `.mantle/` is created in your project. Start a Claude Code session and use `/mantle:help` to see available commands.

**Already have an existing project?** Run `mantle init` then `/mantle:adopt` — AI agents analyze your codebase and domain, then interactively generate product and system design documents from what already exists.

## How It Works

Mantle is a Python CLI (`mantle`) that also installs slash commands into Claude Code (`/mantle:*`). The core library handles all state and vault operations. The CLI is a thin wrapper. Claude Code commands compile context from your vault and orchestrate AI-assisted workflows.

All state lives in plain markdown files with YAML frontmatter — versioned in git, readable by any tool, editable by hand.

## Status

**v0.4.0** — Context & Continuity. Persistent context across sessions with auto-briefing, session logging, context compilation, and a cross-project skill graph. Design, planning, and implementation commands are in progress.

## License

MIT
