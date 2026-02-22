# Mantle — Key Decisions

Decisions made during design and implementation.

## 1. Obsidian-Native, Not Multi-Backend

**Decision**: Build deep Obsidian integration. Do not abstract the storage backend to support Notion or other tools.

**Alternatives Considered**:
- Abstract storage backend with Obsidian and Notion implementations
- MCP server exposing generic operations with swappable backends

**Rationale**: The Obsidian-specific features ARE the product — wikilinks for the skill graph, local-first with no auth, CLI with 100+ commands, plain markdown that Claude Code reads natively. Abstracting these away to support Notion would remove every differentiator. Notion has a fundamentally different data model (blocks vs files, relations vs wikilinks, cloud API vs local filesystem). A "thin abstraction" covering both would be either useless or leaky.

**Future Option**: One-way Notion export (`/mantle:sync-notion`) for team visibility. Not a core concern.

**Confidence**: High
**Reversible**: Low (architecture would need significant rework)

---

## 2. Single Install via pip/uv (GSD Pattern)

**Decision**: Distribute as a Python package via PyPI (`mantle-ai`). The install command mounts markdown files into `~/.claude/commands/mantle/`. No Claude Code marketplace, no separate installs.

**Alternatives Considered**:
- Two installs: Claude Code plugin marketplace + pip for CLI companion
- npm distribution (like GSD)
- Claude Code plugin only

**Rationale**: GSD proved the pattern works — single install, copy files into Claude Code's directory structure. Using pip/uv instead of npm because the companion CLI needs Python (vault manipulation, YAML parsing, template rendering). One install means no version sync issues between the plugin and CLI.

**Confidence**: High
**Reversible**: High (could switch to plugin marketplace later)

---

## 3. Python Orchestration Loop, Not Bash or Markdown-Driven

**Decision**: The implementation loop (`/mantle:implement`) is orchestrated by Python code that invokes Claude Code as a subprocess per story. Not a bash script, and not Claude Code interpreting markdown instructions (GSD approach).

**Alternatives Considered**:
- GSD approach: loop logic written as markdown instructions, Claude Code orchestrates
- Bash script calling Claude CLI in a loop

**Rationale**: Python gives deterministic orchestration (no AI decisions about flow control), proper error handling (try/except vs set -e), zero token cost for loop logic, resumability (skip completed stories), and testability (unit test the loop without LLM calls). GSD's approach is elegant but expensive — every orchestration decision is an LLM inference call. The Python loop is boring but predictable.

**Confidence**: High
**Reversible**: Medium (would require rewriting implementation loop)

---

## 4. Compiled + Static Commands (Colin Pattern for Context)

**Decision**: Most commands are static markdown files. Some commands (status, resume) are compiled from vault state via Jinja2 templates. Compilation runs automatically via SessionStart hook (`mantle compile --if-stale`).

**Alternatives Considered**:
- All commands static, with vault querying at runtime
- Use Colin as a dependency for compilation
- All commands compiled

**Rationale**: Static commands are simpler and sufficient for interactive workflows (challenge, design). Compiled commands solve the context loading problem — expensive vault reads happen once at compile time, AI gets pre-baked context instantly. Colin as a dependency was rejected because it's overkill (3000+ lines for what is 200 lines of Jinja2 + YAML + file hashing). Templates are Colin-compatible (Jinja2 + frontmatter) so migration is possible later.

**Confidence**: Medium (the line between static and compiled may shift)
**Reversible**: High (easy to make more commands compiled or fewer)

---

## 5. Skip MCP Server for v1

**Decision**: No MCP server. Commands use Claude Code's native tools (Read, Write, Edit, Glob, Grep) and the Obsidian CLI via Bash.

**Alternatives Considered**:
- Build an MCP server exposing structured vault operations
- Bundle an existing Obsidian MCP server

**Rationale**: Claude Code's built-in tools + Obsidian CLI via Bash cover all vault operations. An MCP server would add operational complexity (another process to run) for marginal benefit. The core architecture supports adding MCP later because `core/vault.py` encapsulates all vault operations — MCP becomes a thin wrapper when needed.

**Revisit When**:
- Vault operations via Bash become unreliable (Claude gets CLI syntax wrong frequently)
- Cross-tool support needed (Cursor, Windsurf, Gemini CLI)
- Complex vault queries become too painful as sequential CLI calls

**Confidence**: High
**Reversible**: High (50-line wrapper over existing core functions)

---

## 6. Core as Library, CLI as Thin Layer

**Decision**: All logic lives in `mantle/core/` which knows nothing about Claude Code, CLIs, or web servers. The CLI (`mantle/cli/`) is a thin consumer. Future UI (`mantle/api/`) would be another thin consumer.

**Alternatives Considered**:
- CLI-first with logic embedded in command handlers
- Build for CLI only, refactor for UI later

**Rationale**: If `core/` functions are callable without any CLI context, adding a web UI is a delivery layer swap, not a rewrite. The universal parts (vault operations, skill graph, challenge logic, state management, context compilation) are the majority of the work. Developer-specific parts (Claude Code commands, terminal workflows) are a thin shell.

**Confidence**: High
**Reversible**: N/A (this is a structural decision, not easily reversed)

---

## 7. Challenge Phase is Optional, Not a Gate

**Decision**: The challenge phase (`/mantle:challenge`) is available but not mandatory. Users can go directly from idea to product design.

**Alternatives Considered**:
- Mandatory challenge gate: design commands refuse to run without completed challenges
- No challenge feature at all

**Rationale**: Initially considered making challenge mandatory (the "challenge-first philosophy"). Revised because the tool's core identity is the workflow + context engine, not the challenge system. Making it mandatory would add friction for users who already have validated ideas. The challenge system is a powerful feature, not the product's identity.

**Confidence**: Medium (may revisit if users consistently skip validation and regret it)
**Reversible**: High (add/remove the gate easily)

---

## 8. Session Logs Written Automatically

**Decision**: Session logs are written at the end of every session, not just sessions where `/mantle:*` commands are used. Implemented via command closing instructions + a standing `.claude/rules/` instruction.

**Alternatives Considered**:
- Explicit command (`/mantle:pause` like GSD)
- SessionEnd hook (but hooks can't access conversation transcript)
- Only log when commands are used

**Rationale**: Every session has signal, even casual ones. A user chatting about architecture might surface a valuable insight worth capturing. Auto-logging removes the friction of remembering to save context. Logs are capped at ~200 words to prevent bloat.

**Confidence**: High
**Reversible**: High (remove the standing rule)

---

## 9. Project Name: Mantle

**Decision**: The project is called Mantle (PyPI: `mantle-ai`, CLI: `mantle`).

**Alternatives Considered**:
- obsidian-workflow (too generic)
- Forge, Crucible, Lattice (generic abstract nouns)
- Temper (too focused on challenge aspect)
- Spar, Vet, Strop (too focused on validation)
- Strata (already used by another of the user's projects)
- Various vault-adjacent names (vaultkey, deepvault — sounded like security products)
- Lore, Weave, Conduct (interesting but didn't click)

**Rationale**: Mantle is the geological layer beneath the earth's surface — the deep context layer that powers everything above it. Adjacent to obsidian (volcanic glass originates from the mantle). Six letters, works as a CLI command, not overloaded in the dev tool space. `mantle-ai` is available on PyPI.

**Confidence**: High
**Reversible**: Low (renaming a published package is painful)

---

## 10. Obsidian CLI as Primary Vault Interface

**Decision**: Use the official Obsidian CLI (v1.12+) as the primary interface for vault operations, with direct filesystem read/write as fallback.

**Alternatives Considered**:
- Filesystem only (skip the CLI entirely)
- Community CLI tools (notesmd-cli, etc.)
- Obsidian Local REST API plugin

**Rationale**: The official CLI provides template application, property management, search, task queries, and JavaScript execution natively. This is more reliable than parsing YAML and constructing markdown manually. Filesystem fallback ensures the tool works even when Obsidian isn't running. Community CLI tools are fragmented and unreliable. REST API plugin requires Obsidian to be running.

**Risk**: The CLI is new (v1.12, early 2026) and may have rough edges. Mitigated by filesystem fallback for critical operations.

**Confidence**: Medium (depends on CLI stability)
**Reversible**: High (switch to filesystem-only if CLI proves unreliable)

---

## 11. Project Context Lives In the Repo, Not a Separate Vault

**Decision**: Project-specific context (`.mantle/`) lives in the project's git repo alongside the code. Personal cross-project knowledge (skills, patterns, inbox) lives in a personal Obsidian vault synced via iCloud.

**Alternatives Considered**:
- Separate shared vault synced via obsidian-git plugin
- S3 as shared storage backend
- Obsidian Sync ($8-10/month) for shared vaults

**Rationale**: Context should travel with the code. Same git workflow, same PRs, same branching, same history. New team members clone the repo and get full project context immediately. PR reviews can include `.mantle/decisions/` changes — reviewers see the *why* alongside the *what*. No separate sync infrastructure needed. S3 was rejected because it's an object store, not a collaboration tool — no merge resolution, no diff, no version history without building custom tooling. Git is purpose-built for collaborating on text files.

**Structure**:
```
project-repo/
├── src/                       # Code
├── tests/
├── .mantle/                   # Project context (shared, in repo)
│   ├── state.md
│   ├── product-design.md
│   ├── system-design.md
│   ├── decisions/
│   ├── issues/
│   ├── stories/
│   ├── sessions/
│   └── board.md
└── ...

~/vault/                       # Personal vault (iCloud, your devices only)
├── skills/                    # Your skill graph (cross-project)
├── knowledge/                 # Your learnings
└── inbox/                     # Mobile quick captures
```

**Mantle implications**:
- `mantle compile` output goes to `~/.claude/commands/mantle/` (gitignored from project repo)
- `mantle init` creates `.mantle/` in the current project repo
- `mantle config set personal-vault ~/vault` configures the personal vault path
- `.mantle/` can be opened as an Obsidian vault for graph view and visual navigation (optional)
- `.gitignore` template included in `mantle init`

**Confidence**: High
**Reversible**: Medium (moving from in-repo to separate vault requires restructuring)

---

## 12. Notes Tagged with Git Identity

**Decision**: Every note Mantle creates is stamped with the author's `git config user.email`. No custom identity system.

**Alternatives Considered**:
- Custom user profile in Mantle config
- OS-level username
- No attribution

**Rationale**: Git identity is already configured on every developer's machine. It automatically differs between personal (`conal@gmail.com`) and work (`conal@company.com`) contexts because developers set different git configs per repo or globally. Requires zero setup from the user. Enables filtering session logs by author, attributing decisions, and knowing who worked on what.

**Usage in note frontmatter**:
```yaml
---
author: conal@company.com
date: 2026-02-22
---
```

**What this enables**:
- `git log --author="conal" .mantle/` — see all your context contributions
- `/mantle:resume` filters to your latest session log, not a coworker's
- Decision attribution: "who decided on Redis and why?"
- Filter session logs: "show me what Alice worked on this week"

**Confidence**: High
**Reversible**: High (just a frontmatter field)

---

## 13. Interactive Onboarding After Init

**Decision**: `mantle init` prints an interactive onboarding message with next steps and prompts the user about setting up a personal vault.

**Alternatives Considered**:
- Silent init (just create files)
- Guided first run (auto-launch idea → challenge → design in one go)

**Rationale**: Users need to know what to do next without being forced into a specific flow. A brief message with next steps respects the user's autonomy while ensuring they aren't lost after install.

**Confidence**: High
**Reversible**: High (change the output message)

---

## 14. Auto-Briefing on Session Start

**Decision**: The SessionStart hook compiles context AND auto-displays a project briefing (state + last session log + blockers + next actions). Every Claude Code session in a Mantle project starts with full context.

**Alternatives Considered**:
- Compile only, user manually runs `/mantle:resume`
- Smart detection: only auto-display if last session was recent

**Rationale**: The #1 pain point is re-establishing context. Auto-display eliminates this entirely. If a user opens Claude Code in a Mantle project, they should never start from zero. The token cost (~3K for the briefing) is negligible vs the productivity gain.

**Confidence**: High
**Reversible**: High (remove the auto-display from the hook)

---

## 15. Challenge as Single Interactive Session

**Decision**: `/mantle:challenge` runs a single interactive session that weaves through devil's advocate, pre-mortem, and competitive analysis based on conversation flow. Not three separate sub-commands.

**Alternatives Considered**:
- Three separate sub-commands (`challenge-devils-advocate`, `challenge-premortem`, `challenge-competitive`)
- Single command with mode picker

**Rationale**: A good challenge session is adaptive — it follows the conversation where it needs to go. Rigid separation into modes would feel artificial. The AI should challenge the idea from whatever angles are most relevant, not mechanically run through three checklists.

**Confidence**: High
**Reversible**: High (could split into separate commands later)

---

## 16. Separate Create and Revise Commands for Designs

**Decision**: Separate commands for creating vs updating designs. `/mantle:design-product` creates. `/mantle:revise-product` updates. Each revision also creates a decision log entry.

**Alternatives Considered**:
- Single command that detects existing files and switches mode
- Same command with append/revision history in the document

**Rationale**: One command, one job. Each command loads only the context it needs. A create command needs different prompting than an update command. Keeping them separate gives the AI tighter context and better output quality. The automatic decision log entry on revision means design evolution is always traceable.

**Confidence**: High
**Reversible**: High (could merge commands if the separation proves unnecessary)

---

## 17. Issue Planning One at a Time

**Decision**: `/mantle:plan-issues` proposes issues one at a time. User approves or adjusts each before the next is proposed.

**Alternatives Considered**:
- Generate all issues at once, review as a batch
- Generate all, write to vault, user edits files directly

**Rationale**: Fine-grained control over issue decomposition is worth the slower pace. Each issue builds on the previous ones, so early feedback shapes later proposals. Batch generation risks the user rubber-stamping a list they don't fully agree with.

**Confidence**: Medium (may revisit if the one-at-a-time flow feels too slow in practice)
**Reversible**: High (easy to add a `--batch` flag)

---

## 18. Project-Specific Verification Strategy

**Decision**: `/mantle:verify` prompts the user to define a project-specific verification strategy on first use. Strategy stored in `.mantle/config.md` with per-issue overrides in acceptance criteria.

**Alternatives Considered**:
- Generic "run tests and check criteria" for all projects
- AI reviews code against criteria without test execution
- Both tests and AI review as a fixed pipeline

**Rationale**: Verification is fundamentally project-specific. A library needs to run against example projects. A frontend needs localhost testing. An API needs integration tests. A generic strategy would be either too narrow (only pytest) or too vague (AI opinion). Let the user define what "verified" means for their project.

**Confidence**: High
**Reversible**: High (could add default strategies as templates)

---

## 19. Review as Checklist Presentation

**Decision**: `/mantle:review` presents acceptance criteria as a checklist with pass/fail status from verification. Human marks each as approved/needs-changes with comments.

**Alternatives Considered**:
- Conversational review (AI walks through changes)
- Diff-based review (git diffs grouped by story)

**Rationale**: A checklist is objective and complete. Conversational review risks missing criteria. Diff-based review is too code-focused (misses whether requirements are actually met). The checklist ensures every acceptance criterion gets a human judgement.

**Confidence**: High
**Reversible**: High (could add conversational mode as an alternative)

---

## 20. Retry with Feedback on Implementation Failure

**Decision**: When tests fail during the implementation loop, the orchestrator feeds error output back to Claude Code for one retry attempt. If the retry also fails, the story is marked "blocked" with failure details.

**Alternatives Considered**:
- No retry: fail immediately, mark as blocked
- Rollback + block: git reset changes, then mark as blocked
- Unlimited retries with backoff

**Rationale**: Many test failures are caused by minor AI mistakes (wrong import, off-by-one, missing edge case) that are trivially fixable when the error is visible. One retry catches these. More than one retry risks wasting tokens on fundamentally wrong approaches. No rollback because the failed code is useful diagnostic information.

**Confidence**: High
**Reversible**: High (configurable retry count)

---

## 21. Worktree-Based Parallel Implementation

**Decision**: `mantle implement --issue N` automatically creates a git worktree and branch. Merges back on successful verify + review. Enables parallel issue implementation in separate terminal sessions.

**Alternatives Considered**:
- Single-issue only (one `current_issue` in state.md)
- Parallel allowed but user manages worktrees manually
- v2 feature

**Rationale**: Claude Code has native worktree support. Parallel implementation is a natural workflow when issues are independent. Automating worktree creation removes friction and prevents accidental conflicts. The implementation loop already uses `subprocess.run` for git operations, so worktree management is a natural extension.

**Confidence**: Medium (depends on worktree management complexity in practice)
**Reversible**: High (can fall back to single-issue mode)

---

## 22. TDD: Tests as Natural Extension of Stories

**Decision**: Each story includes both implementation tasks and test expectations. Tests are planned alongside features, not as separate test stories.

**Alternatives Considered**:
- Separate test stories that reference implementation counterparts
- Tests only specified at the issue level in acceptance criteria
- No test specs in stories (tests handled during verify)

**Rationale**: TDD treats tests as the definition of "how the feature should work." Planning tests alongside implementation ensures they're scoped correctly, prevents untested code from being committed (the orchestrator runs tests after each story), and keeps stories self-contained. Separate test stories would create coordination overhead.

**Confidence**: High
**Reversible**: High (could split test specs out of stories)

---

## 23. Personal Vault Optional but Prompted

**Decision**: The personal vault (`~/vault/`) is optional. Everything works without it. `mantle init` prompts the user about setting one up but doesn't require it.

**Alternatives Considered**:
- Fully optional with no prompting
- Required (core to the product experience)

**Rationale**: The personal vault (skill graph, cross-project knowledge) is a powerful feature but not essential for the core workflow. A user who only works on one project gets full value from `.mantle/` alone. Prompting ensures awareness without gatekeeping. The prompt during `mantle init` is the right moment — the user is already in setup mode.

**Confidence**: High
**Reversible**: High (change prompting behaviour)

---

## 24. Manifest Interface: Two Functions, Not Many

**Decision**: The manifest module (`core/manifest.py`) exposes two public functions: `plan_install(source_dir, target_dir) -> InstallPlan` and `record_install(source_dir, target_dir, installed)`. All comparison logic is internal.

**Alternatives Considered** (via "design it twice" with three parallel contrarian analyses):
- Design A (chosen): Two functions — plan then record. Caller decides what to do with the plan.
- Design B: Eight composable functions (Unix philosophy) — `hash_file`, `hash_directory`, `read_manifest`, `write_manifest`, `compare_manifests`, etc.
- Design C: Stateful `Installer` class that accumulates state across method calls.

**Rationale**: Design A has the smallest API surface while keeping all policy decisions (what to prompt, what to skip) in the caller. Design B exposed too many internal details as public API. Design C coupled state management to the manifest module. The `InstallPlan` frozen Pydantic model with computed properties (`safe_to_write`, `needs_prompt`) gives the caller everything it needs in one object. `CONFLICT` status (from Design B) was added to handle files where both source and user have changed.

**Confidence**: High
**Reversible**: High (internal refactoring, public API is small)

---

## 25. Wheel-Only for Bundled Files, Not Editable Installs

**Decision**: The `force-include` mechanism (bundling `claude/` and `vault-templates/` into the wheel) only works in built wheels, not in editable dev installs. This is by design — `mantle install` is tested via a wheel install script (`scripts/test_wheel_install.sh`), not from the dev environment.

**Alternatives Considered**:
- Fallback to repo-root `claude/` directory in editable installs
- Use `uv tool install .` for local dev testing

**Rationale**: Adding editable-install fallback paths introduces code that only exists for dev convenience and never runs in production. The wheel install test script provides full end-to-end verification: build wheel, install in isolated venv, run `mantle install` with fake HOME, verify files land correctly. This tests the real user experience.

**Confidence**: High
**Reversible**: High (could add fallback if needed)

---

## 26. `--install-global` Flag Dropped from Install Command

**Decision**: `mantle install` copies to `~/.claude/` directly. The `--global` flag from the original PRD was dropped.

**Alternatives Considered**:
- `mantle install --global` (per original PRD)
- `mantle install --target <path>` for flexibility

**Rationale**: There's only one target (`~/.claude/`). A `--global` flag implies there's a non-global option, but there isn't one yet. Adding flags for nonexistent alternatives is premature. When project-level install is needed (issue #02+), a `--project` flag or separate command can be added.

**Confidence**: High
**Reversible**: High (add flags later)
