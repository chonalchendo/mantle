# Mantle — System Design

## Vision

Python library (`core/`) with thin CLI and future UI layers. Core never imports from delivery layers. Static markdown commands mounted into `~/.claude/`, compiled commands rendered from vault state via Jinja2. Obsidian CLI with filesystem fallback. `.mantle/` in-repo for collaboration via git; personal vault (`~/vault/`) optional for cross-project skills. Implementation loop: deterministic Python orchestrates story-by-story Claude Code invocations in worktrees with test retries and atomic commits.

---

## Implementation Decisions

### Architecture

- **Core as library**: All logic lives in `mantle/core/` which knows nothing about Claude Code, CLIs, or web servers. The CLI (`mantle/cli/`) is a thin consumer. Future UI (`mantle/api/`) would be another thin consumer.
- **Python orchestrates, AI implements**: The implementation loop is deterministic Python code that invokes Claude Code as a subprocess per story. Zero token cost for orchestration logic.
- **Compiled + static commands**: Most commands are static markdown files. Compiled commands (`status`, `resume`) are rendered from vault state via Jinja2 templates. Compilation runs automatically via SessionStart hook.
- **Obsidian CLI primary, filesystem fallback**: Official Obsidian CLI (v1.12+) for template application, property management, search, and queries. Direct filesystem read/write as fallback when CLI is unavailable.
- **In-repo project context**: `.mantle/` lives in the project's git repo. Collaboration via git (PRs, branches, diffs). Personal vault (`~/vault/`) is separate and syncs via iCloud.
- **Git identity tagging**: Every note stamped with `git config user.email`. No custom identity system.
- **One command, one job**: Each command does one focused thing. Separate commands for create vs update (e.g., `design-product` vs `revise-product`) to keep AI context tight.

### Modules

Deep modules (complex internals, simple interfaces):

| Module | Interface | Complexity Hidden |
|---|---|---|
| `core/vault.py` | `read_note()`, `write_note()`, `search()`, `update_properties()` | Obsidian CLI vs filesystem fallback, YAML frontmatter parsing, path resolution between `.mantle/` and `~/vault/` |
| `core/compiler.py` | `compile(project_path)`, `compile_if_stale(project_path)` | Jinja2 rendering, content hashing manifest, staleness detection, context budgeting |
| `core/orchestrator.py` | `implement(issue_id)`, `resume(issue_id)` | Story iteration, Claude Code subprocess invocation, test execution, retry-with-feedback, git commits, worktree management, state updates |
| `core/state.py` | `load()`, `update()`, `transition()` | State machine validation, multi-author conflict handling, git identity resolution |

Thin modules (straightforward wiring):

| Module | What It Does |
|---|---|
| `core/session.py` | Read/write session logs, compile briefings |
| `core/decisions.py` | Create decision log entries with structured metadata |
| `core/skills.py` | CRUD on skill nodes in personal vault, link detection, gap suggestion |
| `core/verify.py` | Load verification strategy (project-level + per-issue), run checks, build report |
| `core/review.py` | Build checklist from acceptance criteria + verification results |
| `core/adopt.py` | Adoption orchestration: parallel agent dispatch, artifact generation, state updates |
| `core/challenge.py` | Save/load/list challenge transcripts with auto-increment filenames, state.md updates |
| `core/manifest.py` | File hash tracking for staleness detection |
| `core/templates.py` | Jinja2 template rendering |

### Key Interactions

- `cli/` calls `core/` functions. Never the reverse.
- `core/` never imports from `cli/` or `api/`.
- Claude Code commands (markdown files) invoke `mantle` CLI commands via Bash tool when they need runtime operations.
- The SessionStart hook calls `mantle compile --if-stale` to refresh compiled commands, then the compiled `resume.md` auto-displays the project briefing.

### Project Status vs Issue/Story Status

The project has a single lifecycle status in `state.md` (idea → ... → completed). Issues and stories have their own independent statuses.

**Relationship**: Project status represents the *current workflow phase*, not a rollup of issue statuses. During `implementing`, multiple issues may exist in different states — some `implemented`, some `planned`, one `implementing`. The project status advances manually (or via command) when the user moves to a new phase, not automatically when all issues reach a threshold.

**Why not automatic**: A project in `implementing` may have Issue-3 verified while Issue-4 is mid-implementation. The user decides when to transition to `verifying` (perhaps after all planned issues are done, or after a subset). This keeps the state machine simple and avoids complex rollup logic that would need to handle partial completion, deferred issues, and priority changes.

**Tracking fields**: `current_issue` and `current_story` in `state.md` track what's actively being worked on. These are updated by the orchestrator and cleared between implementation sessions.

### Error Handling

- **Implementation failure**: On test failure, the orchestrator feeds error output back to Claude Code for one retry attempt. If the retry also fails, the story is marked "blocked" with failure details and the loop stops.
- **Obsidian CLI unavailable**: All vault operations fall back to direct filesystem read/write. A warning is logged but nothing breaks.
- **State conflicts**: `state.md` uses git identity to track `updated_by`. Merge conflicts in `.mantle/` are resolved via git's normal merge flow.

## Testing Decisions

### What Makes a Good Test

Tests should verify external behaviour through the module's public interface, not implementation details. If you can refactor the internals without breaking tests, the tests are well-written. If changing a private method breaks a test, the test is too coupled.

### Modules Under Test

Every module in `core/` gets tests:

| Module | Test Strategy |
|---|---|
| `core/vault.py` | Unit tests with a temporary directory as a mock vault. Test Obsidian CLI calls via subprocess mocking. Test filesystem fallback by simulating CLI absence. |
| `core/compiler.py` | Unit tests: provide vault state fixtures, verify rendered command output matches expected markdown. Test staleness detection with hash manifest fixtures. |
| `core/orchestrator.py` | Integration-style tests: mock `subprocess.run` for Claude Code and pytest invocations. Verify story state transitions, retry logic, git commit calls, and worktree management. |
| `core/state.py` | Unit tests: load/save state from fixture files. Test state machine transitions (e.g., `idea` → `challenge` is valid, `idea` → `implementing` is not). |
| `core/session.py` | Unit tests: verify session log format, briefing compilation, author filtering. |
| `core/decisions.py` | Unit tests: verify decision log entry format, frontmatter structure, file naming. |
| `core/skills.py` | Unit tests: CRUD operations on skill node fixtures. Test link detection and gap suggestion logic. |
| `core/verify.py` | Unit tests: verify strategy loading from config.md and per-issue overrides. Test report generation. |
| `core/review.py` | Unit tests: verify checklist construction from acceptance criteria + verification results. |
| `core/challenge.py` | Unit tests: save/load round-trip, auto-increment filenames, IdeaNotFoundError, state.md updates, list/exists queries. |
| `core/manifest.py` | Unit tests: hash computation, staleness comparison, manifest read/write. |
| `core/templates.py` | Unit tests: Jinja2 rendering with fixture contexts. |

### Test Tooling

- **Framework**: pytest
- **Fixtures**: Temporary vault directories with pre-built `.mantle/` structures
- **Mocking**: `subprocess.run` mocked for Obsidian CLI, Claude Code, and git operations
- **No LLM calls in tests**: The orchestrator tests mock Claude Code invocations. Tests verify the loop logic, not AI output quality.

## Distribution & Installation

Single install via pip/uv with an installer that mounts files into Claude Code's directory structure.

```bash
uv tool install mantle-ai       # Install package + CLI
mantle install --global          # Mount commands, agents, hooks into ~/.claude/
```

Update:

```bash
uv tool upgrade mantle-ai && mantle install --global
```

Published to PyPI as `mantle-ai`. No Claude Code marketplace, no separate installs, no version sync issues.

### What `mantle install` Does

Copies files into Claude Code's directory structure (GSD pattern):

```
~/.claude/
├── commands/mantle/       # Slash commands (/mantle:idea, /mantle:challenge, etc.)
├── agents/                # Subagent definitions (researcher, implementer)
├── hooks/                 # Session hooks (context compilation, auto-briefing)
└── settings.json          # Hook registrations (merged, not overwritten)
```

Also writes a manifest (`mantle-file-manifest.json`) tracking installed file hashes to detect user modifications on upgrade.

### What `mantle init` Does

Initializes Mantle in a project repo:

```bash
cd my-project
mantle init                # Creates .mantle/ in current repo
```

After creation, prints an interactive onboarding message:

```
Mantle initialized in .mantle/

  Your project is ready. Next steps:
  - New project? Run /mantle:idea to log your first idea
  - Existing project? Run /mantle:adopt to generate design docs from your codebase
  - Run /mantle:help to see all commands

  Would you like to set up a personal vault for cross-project skills?
  Run: mantle init-vault ~/vault
```

```
my-project/
├── src/                   # Existing code
├── .mantle/               # Project context (committed to git)
│   ├── state.md
│   ├── config.md          # Project-level settings (includes verification strategy)
│   ├── tags.md            # Tag taxonomy reference
│   ├── decisions/
│   ├── sessions/
│   └── .gitignore         # Ignores compiled/temp files
└── ...
```

### Personal Vault Setup

For cross-project knowledge (skills, patterns, inbox). Optional but prompted during `mantle init`.

```bash
mantle init-vault ~/vault          # Creates personal vault structure
mantle config set personal-vault ~/vault
```

```
~/vault/                           # Personal vault (iCloud-synced)
├── skills/                        # Skill graph (cross-project)
├── knowledge/                     # Learnings and patterns
└── inbox/                         # Quick captures from mobile
```

The personal vault syncs via iCloud (or any file sync). Project context lives in the repo. Everything works without a personal vault — skill linking and cross-project knowledge are bonus features.

## Package Structure

```
mantle/
├── pyproject.toml
├── src/
│   └── mantle/
│       ├── core/                          # Universal engine (library)
│       │   ├── adopt.py                   # Adoption orchestration (codebase + domain → artifacts)
│       │   ├── vault.py                   # Obsidian vault read/write (CLI + filesystem)
│       │   ├── compiler.py                # Compile vault context into commands
│       │   ├── orchestrator.py            # Implementation loop (stories, worktrees, retries)
│       │   ├── state.py                   # Project state management
│       │   ├── session.py                 # Session logging & briefing compilation
│       │   ├── challenge.py               # Challenge session prompts & logic
│       │   ├── decisions.py               # Decision logging
│       │   ├── skills.py                  # Skill graph CRUD & gap detection
│       │   ├── verify.py                  # Verification strategy & execution
│       │   ├── review.py                  # Review checklist construction
│       │   ├── manifest.py                # Dependency tracking & staleness detection
│       │   └── templates.py               # Template rendering (Jinja2)
│       │
│       ├── cli/                           # Developer delivery (thin layer)
│       │   ├── main.py                    # Cyclopts entry point
│       │   ├── install.py                 # Mount files into ~/.claude/
│       │   ├── init.py                    # Initialize .mantle/ in project repo
│       │   ├── compile.py                 # Compile vault state into commands
│       │   └── status.py                  # Show project states
│       │
│       └── api/                           # Future: UI delivery (thin layer)
│           └── (empty for now)
│
├── claude/                                # Files mounted into ~/.claude/
│   ├── commands/
│   │   └── mantle/
│   │       ├── adopt.md                   # Static — onboard existing project
│   │       ├── idea.md                    # Static — log an idea
│   │       ├── challenge.md               # Static — interactive challenge session
│   │       ├── design-product.md          # Static — create product design
│   │       ├── design-system.md           # Static — create system design
│   │       ├── revise-product.md          # Static — revise product design + decision log
│   │       ├── revise-system.md           # Static — revise system design + decision log
│   │       ├── plan-issues.md             # Static — plan issues one at a time
│   │       ├── plan-stories.md            # Static — plan stories with test specs
│   │       ├── implement.md               # Static — triggers Python orchestration loop
│   │       ├── verify.md                  # Static — run project-specific verification
│   │       ├── review.md                  # Static — checklist-based human review
│   │       ├── add-skill.md               # Static — create skill node in personal vault
│   │       ├── status.md.j2               # Compiled — renders vault state
│   │       ├── resume.md.j2               # Compiled — project briefing (auto-displayed)
│   │       └── help.md                    # Static — list all commands by phase
│   ├── agents/
│   │   ├── codebase-analyst.md            # Codebase exploration for /mantle:adopt
│   │   ├── domain-researcher.md           # Domain landscape research for /mantle:adopt
│   │   ├── researcher.md                  # Research subagent
│   │   └── implementer.md                # Implementation subagent
│   └── hooks/
│       └── session-start.sh               # Compiles context + auto-displays briefing
│
├── vault-templates/                       # Obsidian note templates
│   ├── idea.md
│   ├── product-design.md
│   ├── system-design.md
│   ├── issue.md
│   ├── story.md
│   ├── decision.md
│   ├── session-log.md
│   └── skill.md
│
└── tests/
    ├── test_adopt.py
    ├── test_vault.py
    ├── test_compiler.py
    ├── test_orchestrator.py
    ├── test_state.py
    ├── test_session.py
    ├── test_decisions.py
    ├── test_skills.py
    ├── test_verify.py
    ├── test_review.py
    ├── test_challenge.py
    ├── test_manifest.py
    └── test_templates.py
```

### Architecture Rule

`core/` is a pure Python library. It never imports from `cli/` or `api/`. Everything flows downward.

```python
# This works without Claude Code, without CLI, without any UI
from mantle.core import vault, state, challenge

current = state.load_state(project_dir)
note, path = challenge.save_challenge(project_dir, transcript)
challenges = challenge.list_challenges(project_dir)
```

A future web UI calls the same `core/` functions. The CLI and UI are thin delivery layers.

## Directory Structures

### Project Context (In-Repo)

Lives in `.mantle/` inside the project's git repo. Shared with the team via git.

```
my-project/
├── src/
├── tests/
├── .mantle/                               # Project context (committed to git)
│   ├── state.md                           # Current status + metadata (REQUIRED)
│   ├── config.md                          # Project-level settings + verification strategy
│   ├── tags.md                            # Tag taxonomy reference
│   ├── idea.md                            # Original idea + hypothesis
│   ├── product-design.md                  # The what and why
│   ├── system-design.md                   # The how
│   ├── decisions/                         # Decision log entries (REQUIRED)
│   │   └── <date>-<topic>.md
│   ├── challenges/                        # Challenge session transcripts
│   │   └── <date>-challenge.md            # Auto-increments: -2, -3 on collision
│   ├── issues/                            # Vertical slice issues
│   │   └── issue-<nn>.md
│   ├── stories/                           # Stories per issue (with test specs)
│   │   └── issue-<nn>-story-<nn>.md
│   ├── sessions/                          # Session logs (auto-written, author-tagged)
│   │   └── <date>-<HHMM>.md
│   └── .gitignore                         # Ignores compiled/temp files
├── .claude/
├── .gitignore
└── README.md
```

### Personal Vault (iCloud-Synced)

Cross-project knowledge. Syncs across your devices via iCloud. Not shared with team.

```
~/vault/
├── skills/                                # Skill graph (cross-project)
│   └── <skill-name>.md                    # Skill nodes with frontmatter + wikilinks
├── knowledge/                             # Cross-project learnings
│   ├── patterns.md
│   └── lessons-learned.md
└── inbox/                                 # Quick captures from mobile
```

### How They Connect

Mantle reads from both locations:
- `mantle status` reads `.mantle/state.md` from the current repo
- `/mantle:implement` loads project context from `.mantle/` AND relevant skills from the personal vault
- `/mantle:resume` filters session logs to the current user's `git config user.email`
- The personal vault's skill nodes can reference projects: `projects: [[my-project]]` (display links for Obsidian, not file paths)

### Collaboration via Git

`.mantle/` is committed to the repo like any other directory:

```bash
git add .mantle/decisions/2026-02-22-caching.md
git commit -m "docs(mantle): log caching architecture decision"
git push
```

PR reviews can include `.mantle/` changes — reviewers see design rationale alongside code changes. New team members clone the repo and get full project context immediately.

### Viewing in Obsidian

The `.mantle/` directory can be opened as an Obsidian vault for graph view and backlink navigation:

```bash
# Optional — for visual exploration
obsidian open .mantle/
```

Not required. Files are plain markdown, readable in any editor or GitHub's web UI.

## Note Schemas

### State File (Session Entry Point)

Every command reads this first to understand context.

```yaml
---
schema_version: 1
project: my-project
status: idea | adopted | challenge | product-design | system-design | planning | implementing | verifying | reviewing
confidence: 7/10
created: 2026-02-22
created_by: conal@company.com
updated: 2026-02-22
updated_by: conal@company.com
current_issue: null
current_story: null
skills_required:
  - python
  - fastapi
tags:
  - status/active
---

## Summary
One-paragraph description of the project.

## Current Focus
What's being worked on right now.

## Blockers
> [!warning] Blockers
> - [ ] Open blockers listed here

## Recent Decisions (last 3)
- 2026-02-22: Chose X — [[decisions/2026-02-22-topic]]

## Next Steps
1. What to do next
```

### Decision Log Entry

```yaml
---
date: 2026-02-22
author: conal@company.com
topic: framework-selection
scope: product-design | system-design | architecture | implementation | tooling
confidence: 8/10
reversible: high | medium | low
tags:
  - type/decision
  - phase/system-design
---

## Decision
FastAPI over Flask.

## Alternatives Considered
- Flask: simpler but lacks async, validation
- Django: too heavy for this use case

## Rationale
FastAPI's built-in validation and async support match our requirements.

## Reversal Trigger
If performance testing shows <100 req/sec throughput.
```

### Skill Graph Node

```yaml
---
type: skill
proficiency: 8/10
related: [[fastapi]], [[pytest]], [[async-programming]]
projects: [[my-project]], [[other-project]]
last_used: 2026-02-22
tags:
  - type/skill
---

# Python
Key patterns, gotchas, and lessons learned specific to this skill.
```

### Session Log (Auto-Written)

```yaml
---
project: my-project
author: conal@company.com
date: 2026-02-22T14:30
commands_used: [challenge, design-product]
tags:
  - type/session-log
---

## Summary
Completed challenge rounds and began product design.

## What Was Done
- Devil's advocate challenge: idea survived with revised positioning
- Started product design: defined v1 feature set

## Decisions Made
- Position as structlog plugin, not standalone library

## What's Next
- Complete product design (success metrics undefined)

## Open Questions
- Should we support create_task in v1 or defer to v2?
```

### Issue (Vertical Slice)

```yaml
---
title: Context propagates across TaskGroup
status: planned | implementing | implemented | verified | approved
slice: [core-propagation, structlog-processor, tests, example]
story_count: 4
verification: null  # Per-issue override, or null to use project default
tags:
  - type/issue
  - status/planned
---

## Acceptance Criteria
- User creates a ContextTaskGroup, binds structlog context, spawns 3 tasks
- All 3 tasks emit logs with the bound context
- Example script demonstrates this end-to-end

## Verification Override
(Optional: per-issue verification instructions that override project default)
```

### Story (with Test Specs)

```yaml
---
issue: 1
title: Implement ContextTaskGroup with contextvars copy
status: planned | in-progress | completed | blocked
failure_log: null  # Populated on block with error details
tags:
  - type/story
  - status/planned
---

## Implementation
Create `ContextTaskGroup` class that copies current contextvars context
into child tasks. Single file: `src/structlog_context/taskgroup.py`.

## Tests
- Test that context dict is available in child task
- Test that context changes in child don't leak to parent
- Test that multiple child tasks get independent copies
```

### Config File

```yaml
---
tags:
  - type/config
---

## Verification Strategy

How this project should be verified when /mantle:verify runs:

- Run: `python -m pytest tests/ -v`
- Run: `python examples/basic_usage.py` and verify output matches expected
- Check: all acceptance criteria from the issue are covered by passing tests

## Personal Vault
path: ~/vault
```

## Obsidian Integration

Primary interface: Official Obsidian CLI (v1.12+).

| Operation | Method |
|---|---|
| Apply note templates | `obsidian templates apply` |
| Read frontmatter | `obsidian properties read` |
| Update frontmatter | `obsidian properties set` |
| Search vault content | `obsidian search content` |
| Query pending tasks | `obsidian tasks pending` |
| Write/create notes | `obsidian files write` |
| List files | `obsidian files list` |
| Run complex queries | `obsidian dev:eval` (JavaScript execution) |
| Get all tags | `obsidian tags all` |

Fallback: Direct filesystem read/write for operations where the CLI is unavailable or Obsidian isn't running. Since notes are plain markdown with YAML frontmatter, all operations can be done via file I/O + PyYAML + Pydantic.

Requirement: Obsidian >= 1.12 installed, CLI added to PATH. `mantle install` verifies this and warns (not errors) if missing. Note: The Obsidian CLI requires a **Catalyst license** ($25 USD one-time). This should be documented in installation/setup guides. The filesystem fallback ensures Mantle works fully without it.

## Obsidian Features Leveraged

| Layer | Feature | Purpose |
|---|---|---|
| **Storage** | Plain markdown files | Everything readable/writable by AI and humans |
| **Structure** | YAML frontmatter (Properties) | Typed, queryable metadata on every note |
| **Connections** | Wikilinks + backlinks | Skill graph, decision-to-design links, cross-project references |
| **Categorisation** | Nested tags | Cross-cutting queries across folders and projects |
| **Sections** | Callouts (`[!warning]`, `[!question]`, `[!danger]`) | Structured, parseable sections for blockers, decisions, risks |
| **Composition** | Transclusion (`![[note#heading]]`) | Dashboard notes that compose from other notes |
| **Querying** | Dataview plugin + Obsidian CLI search | Dynamic views for humans, programmatic queries for AI |
| **Visualisation** | Graph View | Relationship graphs for skill nodes and decision links |
| **Templates** | Obsidian Templates / Templater | Consistent note creation for ideas, issues, decisions, sessions |

### Tag Taxonomy

Stored in `.mantle/tags.md` (in-repo) for reference by both humans and AI:

```
#type/idea
#type/challenge
#type/product-design
#type/system-design
#type/decision
#type/issue
#type/story
#type/session-log
#type/skill
#type/config

#phase/idea
#phase/adopted
#phase/challenge
#phase/design
#phase/planning
#phase/implementing
#phase/verifying
#phase/reviewing

#status/active
#status/completed
#status/blocked
#status/archived

#confidence/high       (7-10)
#confidence/medium     (4-6)
#confidence/low        (1-3)
```

## Context Engineering

### Command Inventory (v1)

| Command | Type | Focus |
|---|---|---|
| `/mantle:adopt` | Static | Onboard existing project — codebase analysis, domain research, interactive artifact generation |
| `/mantle:idea` | Static | Log an idea with structured metadata |
| `/mantle:challenge` | Static | Interactive five-lens challenge session (persona inlined, no subagent) |
| `/mantle:design-product` | Static | Create product design |
| `/mantle:design-system` | Static | Create system design with decision logging |
| `/mantle:revise-product` | Static | Revise product design + create decision log entry |
| `/mantle:revise-system` | Static | Revise system design + create decision log entry |
| `/mantle:plan-issues` | Static | Plan vertical slice issues one at a time |
| `/mantle:plan-stories` | Static | Plan stories with test specs (TDD) |
| `/mantle:implement` | Static | Trigger Python orchestration loop |
| `/mantle:verify` | Static | Run project-specific verification |
| `/mantle:review` | Static | Checklist-based human review |
| `/mantle:add-skill` | Static | Create/update skill node in personal vault |
| `/mantle:status` | **Compiled** | Bakes current vault state into the prompt |
| `/mantle:resume` | **Compiled** | Project briefing: state + last session + blockers + next actions |
| `/mantle:help` | Static | Lists available commands by workflow phase |

### Compilation

```bash
mantle compile              # Render .j2 templates with current vault state
mantle compile --if-stale   # Only recompile if vault files changed (hash-based)
```

Compilation reads vault state, renders Jinja2 templates, and writes concrete markdown commands to `~/.claude/commands/mantle/`. A manifest tracks source file content hashes for staleness detection.

Triggered automatically via SessionStart hook. The hook also triggers auto-display of the compiled briefing so context is restored before the user types anything.

### Context Budget

| Content | When Loaded | Token Budget |
|---|---|---|
| `state.md` | Always (via compiled commands or direct read) | ~2K |
| `product-design.md` | When in design/planning phases | ~5K |
| `system-design.md` | When implementing | ~5K |
| Current issue + stories | When implementing (loaded per story) | ~3K |
| Relevant skill nodes | Matched by `skills_required` in state.md | ~2K each |
| Decision log entries | On demand ("what did we decide about X?") | ~1K each |
| Compiled briefing | Auto-displayed on session start | ~3K |

Baseline: ~10-15K tokens. Leaves 185K+ for actual work.

### Session Logging

Session logs are written automatically at the end of every session. Implementation:

1. Each `/mantle:*` command includes closing instructions: "Write a session log to `sessions/`"
2. A `.claude/rules/session-logging.md` rule provides a standing instruction for sessions where commands aren't used
3. Format is structured (summary, what was done, decisions, what's next, open questions) and capped at ~200 words

The compiled briefing reads only the latest session log for the current user (filtered by `git config user.email`). Older logs are available for reference but don't consume context budget unless explicitly queried.

## Implementation Loop

The `/mantle:implement` command triggers a Python orchestration loop:

```python
# Pseudocode of mantle implement --issue N

for story in get_stories(issue=N):
    if story.status == "completed":
        continue

    # 1. Compile context for this story (budgeted)
    update_story_status(story, "in-progress")
    context = compile_story_context(project, issue, story)

    # 2. Invoke Claude Code with pre-loaded context (fresh window)
    result = subprocess.run([
        "claude", "--print",
        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
        "--no-session-persistence",
        context
    ])

    # 3. Run tests
    test_result = subprocess.run(["python", "-m", "pytest", ...])

    if test_result.returncode != 0:
        # 4. Retry once with error feedback
        retry_context = compile_retry_context(context, test_result.stderr)
        retry_result = subprocess.run([
            "claude", "--print",
            "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
            "--no-session-persistence",
            retry_context
        ])
        retest = subprocess.run(["python", "-m", "pytest", ...])

        if retest.returncode != 0:
            update_story_status(story, "blocked", failure_log=retest.stderr)
            print(f"Story {story.id} blocked after retry. See .mantle/stories/ for details.")
            break

    # 5. Atomic git commit
    git_commit(f"feat(issue-{issue.id}): {story.title}")

    # 6. Update vault state
    update_story_status(story, "completed")
    update_project_state(project)
    write_session_log(project, story)
```

### Resumability Contract

The orchestrator is designed to be safely re-run at any point:

- **Completed stories are skipped**: The loop checks `story.status == "completed"` and advances past them. Re-running `mantle implement --issue N` after a partial run resumes from the first non-completed story.
- **Blocked stories stop the loop**: A `blocked` story halts the loop. The user fixes the issue manually, sets the story status back to `planned` (via editing the frontmatter or a future `mantle unblock` command), and re-runs.
- **Crash mid-story (Ctrl+C, power failure)**: The story remains `in-progress`. On re-run, the orchestrator treats `in-progress` the same as `planned` — it re-invokes Claude Code for that story from scratch. Since each story targets a small, focused change, re-doing work is cheap. The previous partial changes are in the working tree and Claude Code can see them.
- **Claude Code non-zero exit (not test failure)**: Treated as a story failure. The story is marked `blocked` with the stderr output. The orchestrator does not retry Claude Code crashes — only test failures get the retry-with-feedback loop.
- **Git commit failure**: If `git commit` fails after a successful story (e.g., pre-commit hook failure), the story is not marked `completed`. On re-run, Claude Code sees the already-written code and the orchestrator re-attempts the commit.

The invariant: a story is only marked `completed` after both its tests pass AND its git commit succeeds. This makes the loop idempotent.

### Worktree Support

When implementing an issue, Mantle leverages Claude Code's native worktree support (`--worktree` / `-w` flag). Claude Code creates worktrees at `.claude/worktrees/<name>/` with a `worktree-<name>` branch, handles cleanup automatically, and tracks sessions per worktree.

```python
# mantle implement --issue 3

# Each story's Claude Code invocation uses the same worktree
result = subprocess.run([
    "claude", "--worktree", f"mantle-issue-{issue_id}",
    "--print",
    "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
    "--no-session-persistence",
    context
])

# On successful verify + review:
# Merge the worktree branch back to main
git_merge(f"worktree-mantle-issue-{issue_id}", target="main")
# Claude Code handles worktree cleanup on session exit
```

This enables parallel implementation of multiple issues in separate terminal sessions without conflicts. Each issue gets its own branch and working directory. Add `.claude/worktrees/` to `.gitignore`.

### Why Python, Not Bash or Markdown-Driven

- Deterministic orchestration (Python controls flow, not AI)
- Proper error handling (try/except, explicit recovery, retry logic)
- Zero token cost for loop logic
- Resumable (skips completed stories on re-run)
- Testable (unit test the loop without LLM calls)
- Clean vault updates (YAML parsing, frontmatter manipulation)
- Worktree management (subprocess calls to git)

Each story gets a fresh Claude Code invocation with compiled context, preventing context window degradation across stories.

### Claude Code Flags Reference

Flags available for orchestrator subprocess invocations (verified against `claude --help`):

| Flag | Purpose | Usage |
|---|---|---|
| `--print` | Non-interactive mode, print response and exit | Required for all orchestrator calls |
| `--allowedTools` | Whitelist of tools (e.g. `"Read,Write,Edit,Bash,Glob,Grep"`) | Restrict per story type |
| `--worktree <name>` | Create/reuse git worktree for isolation | Per-issue branch isolation |
| `--system-prompt <prompt>` | Inject system-level context separately from story prompt | Project state, skills, conventions |
| `--max-budget-usd <amount>` | Cost ceiling per invocation (only with `--print`) | Prevent runaway token usage |
| `--output-format json` | Structured JSON output (only with `--print`) | Parse completion signals |
| `--no-session-persistence` | Don't persist session to disk (only with `--print`) | Keep `~/.claude/` clean |
| `--model <model>` | Override model (e.g. `sonnet`, `opus`) | Configurable per project via config.md |
| `--permission-mode <mode>` | Permission level (`default`, `acceptEdits`, `bypassPermissions`) | Autonomous execution |
| `--tools <tools>` | Specify available built-in tools | Alternative to `--allowedTools` |
| `--tmux` | Create tmux session for worktree (requires `--worktree`) | Parallel issue visibility |

Note: The prompt is a **positional argument**, not a flag. Invocation pattern: `claude --print [flags] <prompt>`.

## Technology Choices

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.14+ | Obsidian ecosystem, uv/pip distribution, Jinja2, YAML parsing |
| CLI framework | Cyclopts | Type-hint driven, auto-generated help, Pydantic-style validation |
| Template engine | Jinja2 | Compiled command rendering |
| YAML parsing | PyYAML | Lightweight YAML parsing for frontmatter (yaml.safe_load/dump) |
| Validation | Pydantic | Schema validation for YAML configs, note frontmatter, and state files |
| Terminal output | Rich | Formatted logging, progress bars, tables for CLI output |
| Package build | Hatchling | Modern, supports artifacts for command files |
| Distribution | PyPI via `uv tool install mantle-ai` | Isolated environment, single command |
| Commands format | Markdown files | Mounted into `~/.claude/commands/mantle/` |
| Vault interaction | Obsidian CLI + filesystem fallback | Native template/property support with resilience |
| Version control | Git | Atomic commits per story, worktrees for parallelism |
| Testing | pytest | Standard, fixtures for vault mocking |

## Build Order

1. Package skeleton — `pyproject.toml`, CLI entry point, `mantle install`
2. Project init — `mantle init` creates `.mantle/` with templates + interactive onboarding
3. Personal vault init — `mantle init-vault ~/vault` (optional, prompted during init)
4. State management — `core/state.py`, state.md read/write, git identity tagging
5. Vault operations — `core/vault.py`, Obsidian CLI + filesystem fallback
6. `/mantle:idea` — First command, creates idea from template
7. `/mantle:challenge` — Interactive multi-angle challenge session
8. `/mantle:design-product` — Interactive product design
9. `/mantle:design-system` — Interactive system design with decision logging
10. `/mantle:revise-product` and `/mantle:revise-system` — Revision commands + decision log entries
10b. `/mantle:adopt` — Codebase analysis + domain research → reverse-engineered design docs (requires 8, 9 schemas)
11. Context compilation — `mantle compile`, manifest, SessionStart hook
12. `/mantle:status` and `/mantle:resume` — Compiled commands, auto-briefing on session start
13. `/mantle:plan-issues` — One-at-a-time issue planning
14. `/mantle:plan-stories` — Story planning with test specs (TDD)
15. `/mantle:implement` — Python orchestration loop with retry-with-feedback
16. Worktree support — Auto-create worktree/branch per issue, merge on completion
17. `/mantle:verify` — Project-specific verification strategy (config on first use)
18. `/mantle:review` — Checklist-based human review
19. `/mantle:add-skill` — Skill node creation + AI gap suggestion
20. Session log auto-writing — Standing rules + command closing instructions
21. `/mantle:help` — Command listing by workflow phase
