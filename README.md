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

## Workflow

Every phase is a `/mantle:*` slash command inside Claude Code. The flow runs top-to-bottom, but you can skip optional phases, revise designs at any point, and re-run implementation after fixing blocked stories.

### Project Setup (once)

| Phase | Command | What It Does |
|---|---|---|
| **Idea** | `/mantle:idea` | Capture your idea with structured metadata — hypothesis, target user, success criteria. Saved as `.mantle/idea.md`. |
| **Challenge** | `/mantle:challenge` | _Optional._ AI stress-tests your idea from multiple angles (devil's advocate, pre-mortem, competitive analysis). Produces a verdict with confidence level. |
| **Research** | `/mantle:research` | _Optional._ Web research to validate technical feasibility and explore existing solutions. Reports saved to `.mantle/research/`. |
| **Product Design** | `/mantle:design-product` | Interactive session defining the _what and why_ — features, target users, user stories, release milestones. Creates `.mantle/product-design.md`. |
| **System Design** | `/mantle:design-system` | Interactive session defining the _how_ — architecture, tech choices, data model. Every decision logged with rationale and alternatives. Creates `.mantle/system-design.md`. |

**Already have an existing project?** Run `/mantle:adopt` instead — AI agents analyze your codebase and domain, then interactively generate product and system design documents from what already exists.

### Per-Issue Cycle (repeat for each issue)

| Phase | Command | What It Does |
|---|---|---|
| **Plan Issues** | `/mantle:plan-issues` | Break work into vertical slices. AI proposes one issue at a time — you approve or adjust each before the next. |
| **Shape Issue** | `/mantle:shape-issue` | Evaluate 2-3 approaches with tradeoffs before committing to a direction. Past learnings are loaded automatically. |
| **Plan Stories** | `/mantle:plan-stories` | Decompose the issue into implementable stories sized for a single AI context window. Each story includes test expectations (TDD). |
| **Implement** | `/mantle:implement` | Automated build loop — spawns an Agent per story, runs tests, retries once on failure, creates atomic git commits. |
| **Simplify** | `/mantle:simplify` | _Optional._ Post-implementation quality gate. Spawns per-file agents to identify and remove AI-generated code bloat (unnecessary abstractions, defensive over-engineering, dead code, comment noise). Test-gated — changes only committed if tests pass. |
| **Verify** | `/mantle:verify` | Project-specific verification strategy. On first use, prompts you to define how this project should be verified. Per-issue overrides supported. |
| **Review** | `/mantle:review` | Human review with acceptance criteria checklist. AI presents pass/fail status from verification. You approve or request changes per criterion. |
| **Retrospective** | `/mantle:retrospective` | Capture what went well, what was harder than expected, and wrong assumptions. Learnings auto-surface in future shaping sessions. |

### Available Any Time

| Command | What It Does |
|---|---|
| `/mantle:bug` | Quick structured bug capture. Open bugs surface during `/mantle:plan-issues`. |
| `/mantle:revise-product` | Update the product design. Creates a decision log entry. |
| `/mantle:revise-system` | Update the system design. Creates a decision log entry. |
| `/mantle:status` | Show current project state compiled from vault data. |
| `/mantle:resume` | Re-display the project briefing mid-session. |
| `/mantle:add-skill` | Add a skill node to your personal vault for cross-project knowledge. |
| `/mantle:help` | List all commands grouped by phase. |

## How It Works

Mantle is a Python CLI (`mantle`) that also installs slash commands into Claude Code (`/mantle:*`). The core library handles all state and vault operations. The CLI is a thin wrapper. Claude Code commands compile context from your vault and orchestrate AI-assisted workflows.

All state lives in plain markdown files with YAML frontmatter — versioned in git, readable by any tool, editable by hand.

## Status

**v0.7.14** — Per-story context selection, post-story learning extraction, skill trigger conditions, analysis scratchpad, faster build pipeline.

## License

MIT
