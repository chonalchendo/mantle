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

> **Superseded by Decision 34.** The implementation shifted from Python subprocess orchestration to prompt-based Agent orchestration during issue 13 (story 5).

**Decision**: ~~The implementation loop (`/mantle:implement`) is orchestrated by Python code that invokes Claude Code as a subprocess per story. Not a bash script, and not Claude Code interpreting markdown instructions (GSD approach).~~

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

> **Dropped.** Issue 14 was dropped after Decision 34 replaced subprocess orchestration with prompt-based Agent orchestration. The `--worktree` flag was a subprocess concern — there is no subprocess to pass it to. Users can use Claude Code's native `/worktree` command before running `/mantle:implement`.

**Original Decision**: `mantle implement --issue N` automatically creates a git worktree and branch. Merges back on successful verify + review. Enables parallel issue implementation in separate terminal sessions.

**Why dropped**: The decision was designed around `subprocess.run(["claude", "--worktree", ...])`. With prompt-based orchestration (Decision 34), the implementation runs inside the user's existing Claude Code session. Worktree isolation is a single user action (`/worktree` or `EnterWorktree`) — automating it adds complexity without meaningful UX gain.

**User stories 27-28**: Deferred, not deleted. If automated worktree management proves needed, it would be redesigned around the Agent-based architecture.

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

---

## 27. yaml.safe_load + Pydantic for Vault Frontmatter (Drop OmegaConf)

**Decision**: Use `yaml.safe_load` (PyYAML) + Pydantic for parsing note frontmatter. Remove OmegaConf from runtime dependencies.

**Alternatives Considered** (via "design it twice" with three parallel contrarian analyses):
- OmegaConf + Pydantic (original system-design.md spec)
- PyYAML only (no schema validation)
- yaml.safe_load + Pydantic (chosen)

**Rationale**: OmegaConf's key features (variable interpolation `${key}`, config merging, structured configs) are irrelevant for note frontmatter. Notes have simple flat YAML that needs schema validation, not config composition. PyYAML handles the parsing; Pydantic handles validation and typing. One fewer runtime dependency.

**Confidence**: High
**Reversible**: High (add OmegaConf back if interpolation/merge features are needed later)

---

## 28. Typed Generic[T] Vault API

**Decision**: `vault.read_note(path, schema) -> Note[T]` uses `Generic[T]` where T is a Pydantic BaseModel. The type checker knows the frontmatter type at call sites.

**Alternatives Considered** (via "design it twice"):
- Design A: Minimal 2-function API, schema-ignorant (returns raw dict)
- Design B: Typed generics with `Note[T]` (chosen, trimmed to 2 functions)
- Design C: Two-layer split (frontmatter.py + Vault class)

**Rationale**: Design B gives type-checker coverage on frontmatter fields while keeping the API to just 2 functions (`read_note`, `write_note`). Design A loses type safety. Design C was over-structured for v1. `Note[T]` is a frozen dataclass (not Pydantic) to avoid double-validation overhead. `parse_frontmatter` and `update_frontmatter` convenience functions deferred — callers use `read_note`/`write_note`.

**Confidence**: High
**Reversible**: High (internal implementation, public API is 2 functions)

---

## 29. Atomic State Operations

**Decision**: Each state function (`transition`, `update_tracking`, `create_initial_state`) does its own load → validate → save cycle internally. No shared state, no "session" object.

**Alternatives Considered** (via "design it twice"):
- Pure/IO split: pure functions for logic, separate I/O boundary
- Atomic operations: each function is self-contained (chosen)
- Transition-centric: converged to atomic approach

**Rationale**: All three contrarian designs converged on functions + frozen data (matching the manifest.py pattern). The key choice was between a pure/IO split (caller loads, pure function transforms, caller saves) vs atomic operations. Atomic was chosen because callers should never forget to persist — the state file IS the source of truth, not in-memory objects.

**Confidence**: High
**Reversible**: Medium (changing the I/O boundary affects all callers)

---

## 30. State Machine: Forward Progression + Known Backward Steps

**Decision**: State transitions follow a linear progression with specific allowed backward steps. Revise commands (`/mantle:revise-product`, `/mantle:revise-system`) do NOT change state.

**Allowed backward steps**:
- implementing → planning (re-plan after implementation issues)
- verifying → implementing (fix issues found during verification)
- reviewing → implementing (fix issues found during review)

**Alternatives Considered**:
- Strict linear: no backward steps allowed
- Free-form: any transition allowed
- State groups: coarse-grained phases instead of fine-grained statuses

**Rationale**: Real workflows aren't purely linear. Discovery during implementation often requires re-planning. But allowing arbitrary transitions defeats the purpose of tracking progress. The specific backward steps reflect known real-world patterns. Revise commands don't change state because revising a design doesn't reset planning/implementation progress.

**Confidence**: High
**Reversible**: High (add/remove transitions from the `_TRANSITIONS` dict)

---

## 31. No Config CLI in v1 (Config as Internal API)

**Decision**: `mantle config set/get` is not a user-facing CLI command in v1. Config read/write exists as internal functions in `core/project.py` (`read_config`, `update_config`) for other commands to use programmatically.

**Alternatives Considered**:
- Full config subcommand group (`mantle config set key val` / `mantle config get key`)
- Config set only, no get
- Internal API only (chosen)

**Rationale**: Only two config keys exist (`personal_vault`, `verification_strategy`). Both are set-once by other commands — `init-vault` sets the vault path, `verify` will set the strategy. Nobody will type `mantle config set` directly. The core API supports adding a CLI later (5 lines of Cyclopts wiring), so nothing is lost by deferring.

**Confidence**: Medium (may add config CLI if users request it)
**Reversible**: High (add CLI commands later, core API already exists)

---

## 32. Init Design: core/project.py Hybrid

**Decision**: `core/project.py` contains both template constants (importable by any module) and an `init_project()` function. CLI handles idempotency check and Rich output.

**Alternatives Considered** (via "design it twice"):
- Everything in cli/init.py (templates trapped in CLI layer)
- core/templates.py for content generators + CLI orchestrator
- core/project.py with constants + init_project() (chosen)

**Rationale**: The tag taxonomy, config schema, and directory structure are domain knowledge that other core modules will need (validation, compilation, querying). Trapping them in `cli/init.py` violates the architecture rule when any core module needs them. But the init function itself is simple scaffolding (mkdir + write files), not complex logic. The hybrid puts data where it's reusable and keeps the function minimal.

**Confidence**: High
**Reversible**: High (refactor between modules is trivial)

---

## 33. init-vault Auto-Sets Config (One Command, One Intent)

**Decision**: `mantle init-vault ~/vault` creates the directory structure AND automatically records the vault path in `.mantle/config.md` frontmatter. No separate `mantle config set personal-vault` step.

**Alternatives Considered**:
- Two-step: `init-vault` creates dirs, user runs `config set` separately
- Single command with optional `--no-config` flag

**Rationale**: The user's intent is "I want to use a personal vault at this path." Making them type the path twice (once for dirs, once for config) is a UX failure. One command, one intent. The escape hatch (`read_config`/`update_config` in core) exists for programmatic access if ever needed.

**Confidence**: High
**Reversible**: High (split into two commands if users want more control)

---

## 34. Prompt-Based Agent Orchestration, Not Python Subprocess

**Decision**: The implementation loop (`/mantle:implement`) is a prompt-based orchestrator (`implement.md`) that spawns native Claude Code Agent subagents per story. Replaces the Python subprocess approach from Decision 3.

**Supersedes**: Decision 3

**Alternatives Considered**:
- Python subprocess loop via `subprocess.run(["claude", "--print", ...])` (original approach, Decision 3)
- Hybrid: Python loop that calls Agent tool via SDK (no SDK available)
- Keep subprocess for CI/CD, use Agent for interactive sessions

**Rationale**: Building the Python subprocess orchestrator (issue 13, stories 1-4) revealed fundamental limitations of the "Claude outside Claude" pattern:

1. **Cold starts**: Each `claude --print` invocation re-reads CLAUDE.md, re-discovers the project, and starts from zero. Agents inherit the session's environment instantly.
2. **No tool access**: `--print` mode has limited tool access and no interactivity. Agents get all tools (Read, Write, Edit, Bash, Glob, Grep, Agent) with full capability.
3. **No user interaction**: When a subprocess is stuck, it fails silently. An Agent can ask the user for guidance.
4. **No MCP servers**: Subprocesses don't inherit MCP server connections. Agents do.
5. **Environment mismatch**: The inner subprocess has different permissions, tools, and context than the outer session. Agents run in the same process.
6. **Simpler code**: The subprocess approach required `claude_cli.py` (invocation builder), `compile_story_context()` (context serialization), `compile_retry_context()`, and a Python implementation loop. The Agent approach passes file paths and lets agents read files themselves — the orchestration logic fits in a single markdown file.

The GSD project (23.8k stars) validated this pattern: a prompt-based orchestrator staying lean (~10-15% context) while each Agent subagent gets a fresh 200k context window. Python still handles state management (story status updates via `mantle update-story-status`) because YAML frontmatter editing is fragile in prompts.

**What changed**:
- Deleted: `core/claude_cli.py`, `cli/implement.py`, `orchestrator.implement()`, `compile_story_context()`, `compile_retry_context()`, `_run_tests()`, `_git_commit()`
- Kept: `update_story_status()` (moved to `core/stories.py`, exposed via CLI)
- Rewritten: `implement.md` is now the full orchestrator, not just a trigger for Python code

**Trade-offs accepted**:
- Orchestration logic is no longer unit-testable (lives in a prompt, not Python). Accepted because the orchestration is simple sequential logic (iterate stories, spawn agent, check tests, commit), and the complex parts (story status management) remain in tested Python.
- Token cost for orchestration is no longer zero. Accepted because the cost is small (~10-15% of one context window) and the capability gain (full tool access, user interaction, no cold starts) is substantial.

**Future option — Claude Agent SDK**: The Python Agent SDK (`claude-agent-sdk`) provides `query()` and `ClaudeSDKClient` APIs that spawn full Claude Code agents from Python with tool access, MCP servers, CLAUDE.md loading, permission callbacks, and budget controls. This would enable "Approach B": a testable Python loop (Decision 3's strength) with full agent capabilities per story (Decision 34's strength). The SDK's advantages over the current prompt approach are testable orchestration, headless/CI execution, zero token cost for loop logic, and programmatic control (`max_budget_usd` per story, `can_use_tool` callbacks). The prompt approach wins on cold start (zero — same process vs new process per `query()`), inherited session environment (MCP servers, permissions are implicit vs explicit config), and natural user interaction (agent asks user directly vs interrupt handling). For the current use case — interactive sessions with user present — Decision 34 is the better fit. Revisit the SDK approach if headless execution is needed (e.g., `mantle implement --issue 5 --headless` for CI/CD).

**Confidence**: High
**Reversible**: Medium (SDK approach is a natural evolution, not a rewrite — the loop logic and state management patterns transfer directly)
