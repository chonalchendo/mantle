# Mantle

AI workflow engine with persistent context. Built for developers who use Claude Code.

## The Problem

AI coding agents are stateless. Every session starts from zero — context is lost, decisions are forgotten, and you end up repeating yourself or pasting notes between tools. Worse, agents rubber-stamp bad ideas instead of challenging them.

Mantle fixes this by giving your AI agent a memory, a structured workflow, and the discipline to validate ideas before building them.

## What It Does

Mantle manages the full lifecycle of AI-assisted development:

**Idea to verified code in one command** — `/mantle:build` runs the full pipeline automatically: shape the issue, plan stories, implement with per-story agents, simplify, and verify against acceptance criteria.

**Persistent context** — project state, decisions, session logs, and a personal knowledge vault stored as markdown with YAML frontmatter. Everything is human-readable and lives in `.mantle/`.

**Auto-briefing** — every Claude Code session starts with a compiled briefing: project state, last session log, open blockers, next actions. You never start from zero.

**Compiled knowledge** — vault state is pre-compiled into Claude Code commands so your AI gets instant context, not expensive runtime file queries.

**Cross-project learning** — a personal vault links skills, patterns, and lessons learned across projects via Obsidian wikilinks. Learnings from past issues auto-surface in future planning.

**Global storage** — store `.mantle/` context at `~/.mantle/` instead of in-repo for workplace environments where modifying `.gitignore` isn't desirable. Project identity is derived from git remote URL, so context survives re-clones.

## Quick Start

Requires Python 3.14+.

```bash
# Install
uv tool install mantle-ai

# Mount commands into Claude Code
mantle install

# Initialize a project
cd your-project
mantle init

# Set up a personal vault (optional)
mantle init-vault ~/vault
```

Once initialized, `.mantle/` is created in your project. Start a Claude Code session and use `/mantle:help` to see available commands.

**Already have an existing project?** Run `mantle init` then `/mantle:adopt` — AI agents analyze your codebase and domain, then interactively generate product and system design documents from what already exists.

**Using this at work?** Store context outside the repo so it never shows up in git diffs:

```bash
mantle storage --mode global
mantle migrate-storage --direction global
```

Context moves to `~/.mantle/projects/<repo-identity>/`. All commands work identically — the path resolution is transparent.

## Workflow

Every phase is a `/mantle:*` slash command inside Claude Code. Run them individually for control, or use `/mantle:build` to automate the full pipeline from shaped issue to verified code.

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
| **Implement** | `/mantle:implement` | Automated build loop — spawns an Agent per story with dependency-aware wave execution, runs tests, retries once on failure, post-implementation code review, atomic git commits. |
| **Simplify** | `/mantle:simplify` | Post-implementation quality gate. Per-file agents identify and remove AI-generated code bloat. Test-gated — changes only committed if tests pass. |
| **Verify** | `/mantle:verify` | Project-specific verification against acceptance criteria. Auto-detects test/lint/check commands on first use. Per-issue overrides supported. |
| **Review** | `/mantle:review` | Human review with acceptance criteria checklist. AI presents pass/fail status from verification. You approve or request changes per criterion. |
| **Retrospective** | `/mantle:retrospective` | Capture what went well, what was harder than expected, and wrong assumptions. Learnings auto-surface in future shaping sessions. |

**Or run it all at once:** `/mantle:build` executes the full pipeline — shape, plan stories, implement, simplify, and verify — without requiring confirmation at each step.

### Available Any Time

| Command | What It Does |
|---|---|
| `/mantle:bug` | Quick structured bug capture. Open bugs surface during planning. |
| `/mantle:inbox` | Ultra-low-friction idea capture for feature ideas. |
| `/mantle:add-issue` | Add a single new issue to the backlog. |
| `/mantle:brainstorm` | Explore and validate a feature idea against your product vision. |
| `/mantle:scout` | Analyze an external repo through your project's design lens. |
| `/mantle:refactor` | Structured refactoring for architectural debt and design problems. |
| `/mantle:fix` | Read saved review feedback and fix flagged criteria. |
| `/mantle:revise-product` | Update the product design. Creates a decision log entry. |
| `/mantle:revise-system` | Update the system design. Creates a decision log entry. |
| `/mantle:status` | Show current project state compiled from vault data. |
| `/mantle:resume` | Re-display the project briefing mid-session. |
| `/mantle:add-skill` | Add a skill node to your personal vault for cross-project knowledge. |
| `/mantle:query` | Search your vault knowledge and synthesize a grounded answer. |
| `/mantle:distill` | Synthesize accumulated vault knowledge on a topic into a persistent note. |
| `/mantle:help` | List all commands grouped by phase. |

## Knowledge Engine

Every AI context window is expensive. Mantle makes each one smarter by injecting the right knowledge at the right time — domain expertise, past learnings, and project decisions that would otherwise be lost between sessions.

### How it works

Your personal vault (`~/vault/`) is a knowledge graph of interconnected skill nodes, each containing domain-specific patterns, conventions, anti-patterns, and lessons learned. When you start working on an issue, Mantle auto-detects which skills are relevant, compiles them into `.claude/skills/`, and Claude Code natively loads them. Every agent — whether it's shaping an approach, implementing a story, or reviewing code — gets pre-loaded domain knowledge without burning context on file searches.

The compounding effect: learnings from Issue 5 improve how Issue 12 is shaped. A skill you built while working on Project A informs implementation on Project B. The knowledge graph grows with you, not per-project.

### Knowledge commands

| Command | What It Does |
|---|---|
| `/mantle:add-skill` | Create a skill node in your personal vault — proficiency level, patterns, anti-patterns, related skills. Builds the graph. |
| `/mantle:query` | Search your accumulated vault knowledge and synthesize a grounded answer. Like asking your past self for advice. |
| `/mantle:distill` | Synthesize scattered vault knowledge on a topic into a single, dense reference note. Turns experience into reusable context. |
| `/mantle:retrospective` | After completing an issue, capture what went well and what was harder than expected. These learnings auto-surface in future `/mantle:shape-issue` sessions. |
| `/mantle:scout` | Analyze an external repo through your project's design lens. Extract patterns and ideas grounded in your existing architecture. |

### What gets injected into each context window

- **Session briefing** — project state, last session log, blockers, next actions (auto-loaded on session start)
- **Compiled skills** — domain-specific patterns matched to the current issue's technologies
- **Past learnings** — gotchas, recommendations, and wrong assumptions from previous issues
- **Decision log** — architectural choices with rationale, so agents honour past decisions instead of re-debating them

The result: agents that know your project's conventions, remember past mistakes, and make informed tradeoff decisions — every session, automatically.

## How It Works

Mantle is a Python CLI (`mantle`) that also installs slash commands into Claude Code (`/mantle:*`). The core library handles all state and vault operations. The CLI is a thin wrapper. Claude Code commands compile context from your vault and orchestrate AI-assisted workflows.

**Architecture:** `core/` (all business logic) → `cli/` (thin routing layer) → Claude Code commands (prompt-based orchestration). Core never imports from CLI. Each implementation story gets a fresh 200k context window via native Agent subagents.

**Storage:** All state lives in plain markdown files with YAML frontmatter — human-readable and editable by hand. By default, `.mantle/` lives in your project root (git-tracked for collaboration). For workplace environments, switch to global storage at `~/.mantle/` with `mantle storage --mode global`.

**Session continuity:** A SessionStart hook auto-compiles context and displays a project briefing. Session logs are written automatically at the end of every session, so you never lose context between conversations.

## Status

**v0.12.1** — Taxonomy-aware tag guidance in skill authoring. Vault tags now use coarse-grained names that cluster related skills; orphaned index files are auto-cleaned during compile.

## License

MIT
