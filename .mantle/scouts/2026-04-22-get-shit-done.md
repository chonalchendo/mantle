---
date: '2026-04-22'
author: 110059232+chonalchendo@users.noreply.github.com
repo_url: https://github.com/gsd-build/get-shit-done.git
repo_name: get-shit-done
dimensions:
- architecture
- patterns
- testing
- cli-design
- domain
tags:
- type/scout
---

# Scout Report: get-shit-done

**Repository**: https://github.com/gsd-build/get-shit-done.git
**Analyzed**: 2026-04-22
**Project context**: Mantle is a Python AI-workflow engine for Claude Code with persistent context, and GSD is its named competitor.

---

## Executive Summary

GSD is a mature TypeScript/Node system (v1.38.2, 33 subagents, 103 slash commands, Anthropic SDK-based runtime) that is a direct competitor to Mantle — and one that has already shipped production solutions to most of Mantle's optimisation-focused backlog. Mantle's product-design claim that "GSD has no runtime" is **factually wrong**: GSD's `sdk/src/` contains a full TypeScript runtime (session-runner, context-engine, cli-transport, event-stream, tool-scoping) that orchestrates phase lifecycle, context resolution, model selection, and cost tracking programmatically. Signal quality is **high** for all five dimensions — many findings map directly to open issues (75, 79, 87, 88, 71/72, 70, 73, 85). The single most important takeaway: GSD has already solved model-tiering (issue 75), progressive disclosure via `@file` references (issue 79), context-manifest-driven token reduction (issue 87/88), and dynamic next-step routing (issue 71/72). Mantle can leapfrog by adapting these patterns rather than reinventing them — and should correct its product-design messaging to honestly distinguish *persistent knowledge graph* from *runtime* as the real differentiators.

---

## Findings by Dimension

### Architecture

- **SDK-Driven Session Execution** — GSD wraps Anthropic SDK `query()` in `sdk/src/session-runner.ts` + `sdk/src/index.ts` to orchestrate phase lifecycle, context, model selection, and tool permissions in TypeScript. Relevant because Mantle's "no runtime" claim is false — GSD has one, and its shape is a reference Mantle could adopt. **Recommendation: Adopt** — expose `mantle.core` as a public SDK with `run_phase()` / `execute_plan()` so programmatic composition (issue 75 A/B harness) doesn't need subprocess.
- **Phase-Type Tool Matrix** — `sdk/src/tool-scoping.ts` enforces different tool sets per phase (Research: read-only + WebSearch; Execute: full write; Verify: read-only). **Adopt** — extend Mantle CLI with `--tools` preset per phase; add `ToolMatrix` to `core/`.
- **Adaptive Context Resolution** — `sdk/src/context-engine.ts` declares a per-phase `PHASE_FILE_MANIFEST` (e.g., execute=state+config; research=state+roadmap+context; plan=all); `context-truncation.ts` truncates large files by keeping headings + first paragraph and collapsing the rest. **Adapt** — this is the direct answer to issue 87 (mantle compress) and issue 88 (sweep). Keep Mantle's `state.md` entry point but add per-command file manifests + markdown-aware truncation.
- **Hook-Driven Observability Layer** — `hooks/gsd-context-monitor.js` warns at 35%/25% remaining; `gsd-workflow-guard.js` nudges users toward state-tracked flows. Advisory only, never mutating. **Adopt selectively** — PostToolUse hook emitting token usage to `.mantle/session-metrics.json` would directly support issue 88.
- **Thin Skill Layer** — Commands in `commands/gsd/*.md` are pure prompts with YAML frontmatter that reference `@~/.claude/get-shit-done/workflows/` and `references/` rather than embedding orchestration logic. **Adopt** — consider replacing Jinja2-compiled `resume.md`/`status.md` with static markdown + `@file` references; reduces compile-time overhead and improves cache reuse.
- **Instrumented Output Layer** — `sdk/src/cli-transport.ts` + `event-stream.ts` emit structured `GSDCostUpdateEvent` events with `input_tokens`/`output_tokens`/`cache_read_input_tokens`/`cache_creation_input_tokens`. **Adopt** — build `core/telemetry/` to log per-command cost events to `.mantle/audit-tokens.jsonl`; this is the infrastructure issue 88 needs and it also supports issue 75's A/B harness.
- **Workstream Multiplexing** — `--ws <name>` flag routes `.planning/` to `.planning/workstreams/<name>/`, enabling parallel Claude instances on the same repo without collision. Session identity resolved via env vars (GSD_SESSION_KEY, CLAUDE_CODE_SSE_PORT, TTY) with legacy file fallback. **Adapt** — directly relevant to issue 85 (cross-repo project context). GSD's session-identity resolution is the prerequisite Mantle would otherwise have to design from scratch.
- **Wave-Based Parallel Execution with Runtime Fallback** — `get-shit-done/workflows/execute-phase.md` groups tasks into waves, spawns parallel Task agents, falls back to sequential inline execution where the Task tool is unreliable (Copilot). **Skip** for now — Mantle's current focus is token cost, not throughput; revisit if parallel implementation becomes a goal.

### Coding Patterns

- **Deterministic-First Prompt Ordering** — `sdk/src/phase-prompt.ts:106-109` splits prompts into cacheable stable prefix (role, purpose, process) and variable suffix (project-specific context), explicitly referencing Anthropic's prompt caching. **Adopt** — refactor Mantle's top commands to hoist stable workflow instructions above vault-injected context. Direct support for issue 87 (compression) and reduces token spend on repeated invocations.
- **Phase-Manifest Context Reduction + Markdown-Safe Truncation** — `sdk/src/context-engine.ts:42-77` declares file manifests per phase; `context-truncation.ts` truncates files >8192 chars by keeping headings + first paragraph per section with `[... N lines omitted]`. **Adapt** — implement per-command file manifests plus a Python port of the markdown truncation algorithm. Issues 87 and 88.
- **Semantic Error Classification with Exit Codes** — `sdk/src/errors.ts:20-73` classifies errors into 4 types (Validation=10, Execution=1, Blocked=11, Interruption=1) for orchestrator-aware recovery. **Adopt** — mirrors Mantle's issue-51 learning (contextual CLI errors with recovery); classified exit codes let `/mantle:build` and CI tooling distinguish recoverable vs blocking failures.
- **Typed YAML Frontmatter Manifests** — Every agent and command declares `name`/`description`/`tools`/`hooks`/`color` in frontmatter parsed via stack-based YAML parser (`sdk/src/plan-parser.ts:29-80`). **Adopt** — give every `/mantle:*` command uniform frontmatter (required_context, allowed_tools, hooks). Pre-validation scopes tools per skill and reduces prompt bloat.
- **Deviation Rules with Bounded Repair Budgets** — `get-shit-done/workflows/execute-plan.md:73-89` declares `<deviation_rules>` (bug/missing-critical/blocking/architectural) and a 2-attempt repair budget before logging failure. **Adapt** — `/mantle:implement` and `/mantle:build` should define rules that distinguish fix-inline vs report-and-skip vs report-and-pause, with a bounded retry cap.
- **Per-Session Cost Tracking with Running Totals** — `sdk/src/event-stream.ts` (getCost/updateCost) + `cli-transport.ts` emit and aggregate token costs per phase, cumulative per session. **Adopt** — emit `MantleTokenCostEvent` on every API response; aggregate per session. Direct scaffold for issue 75's A/B comparison and issue 88's sweep.

### Testing

- **Dual-Subprocess Golden Parity** — `read-only-parity.integration.test.ts` runs the same command twice (legacy CJS subprocess vs in-process SDK `registry.dispatch()`) and asserts `expect(sdk.data).toEqual(cjs)` on structured output. Verifies behavioural equivalence without byte-for-byte identity. **Adopt** — Mantle has no prompt-layer test infrastructure (known gap); this pattern lets Mantle capture prompt-layer outputs (compiled commands, Agent-subagent results) against a baseline before refactoring prompts for token cuts.
- **Strict Golden Policy Enforcement with Exception Registry** — `golden-policy.test.ts` runs `verifyGoldenPolicyComplete()` to ensure every registry command is either integrated-tested or listed in `GOLDEN_PARITY_EXCEPTIONS` with a rationale — no silent gaps. **Adopt** — create `prompt-coverage-policy.test.py` enumerating `/mantle:*` commands as `INTEGRATED`/`UNIT_ONLY`/`DEFERRED` with required rationales. CI-enforces that new commands can't skip the decision.
- **Normalized Parity Rows for Volatile Output** — Documented `strip()` transformations (remove timestamps, session IDs, installation-time values) paired with `expect(strip(a)).toEqual(strip(b))`. **Adopt** — a `normalize_prompt_output()` helper pairs well with `dirty-equals` already in the stack; pick up volatile-field handling when golden-testing prompts.
- **Mutation Sandbox with Dual-Copy Factory** — `createMutationSandbox({ git?: boolean })` makes a fresh copy of a base fixture per test; mutation tests run two copies so CJS vs SDK don't contaminate each other. **Adopt** — extend Mantle's `tmp_path` fixtures with `create_mutation_sandbox(git=False)` for multi-Agent workflow tests where one Agent's mutations must not leak to the next test run.
- **Custom Cross-Platform Test Runner** — `scripts/run-tests.cjs` uses `readdirSync()` instead of shell glob expansion to avoid Windows PowerShell breakage. **Skip** — pytest already handles this; not worth replicating.

### CLI Design

- **Progressive Command Discovery via Subcommands** — `/gsd:debug`, `/gsd:quick`, `/gsd:progress`, `/gsd:check-todos`, `/gsd:next` accept subcommands (`list`, `status <slug>`, `resume <slug>`) that show state-aware work inline without spawning agents. **Adopt** — turn `/mantle:help` into a launch pad: `/mantle:help next`, `/mantle:help status`, `/mantle:help context`. Direct relief for issues 71/72.
- **Explicit "Next Command" Handoff at Command Boundaries** — GSD commands document routing in their descriptions ("After this command: Run `/gsd:plan-phase 1`") and several programmatically invoke the next command via the `SlashCommand` tool (`/gsd:progress` → `/gsd:plan-phase` or `/gsd:execute-phase`). **Adopt** — this is issues 71/72 more or less solved; port the routing-rules-in-command-markdown pattern and optionally centralise in `.mantle/routing.yaml`.
- **State-Aware Routing with Prior-Phase Validation** — `/gsd:next` scans prior phases for incomplete work before advancing and offers three options: defer to backlog, stop and fix, or force-advance. **Adapt** — becomes `/mantle:triage` between `/mantle:build` and `/mantle:verify` (issue 70). Show incomplete tasks, warnings, token-budget breach, and present explicit advance/resolve choice.
- **Persistent Session Directories with list/resume** — `/gsd:debug` and `/gsd:quick` maintain `.planning/debug/` and `.planning/quick/` with resumable state files for ad-hoc work that isn't tracked in ROADMAP.md. **Adapt** — issue 73's lightweight bug-fix pipeline = `/mantle:quick-fix` with `.mantle/quick-fixes/` storing PLAN.md + SUMMARY.md. Keeps hotfix work out of the main issue track.
- **Explicit Subagent-Type Declarations with Rationale** — Commands declare `<available_agent_types>` upfront and explain *why* (e.g., "Investigation burns context fast"). **Adopt** — cheap clarity win on `/mantle:implement`, `/mantle:build`, `/mantle:verify`; makes token economics and agent-swap decisions transparent.
- **Actionable Error Remediation** — `bin/install.js` detects shell (fish/zsh/bash) and OS on failure and emits specific fix commands ("run: echo 'export PATH=...' >> ~/.bashrc"). **Adopt** — add environment-aware remediation to Mantle's error path; past learning 51 already points this way.
- **Installer as Multi-Runtime Abstraction Layer** — `bin/install.js` mounts GSD into Claude Code, Gemini, OpenCode, Codex, Copilot, Cursor with per-runtime tool-name and config mapping. **Skip** — Mantle is Claude Code-only by design, but worth documenting as a future extension point.
- **Interactive Dashboard Command** — `/gsd:manager` displays all phases with visual status (✓/⏳/✗) and offers quick launch actions. **Adapt** — enhance `/mantle:status` with an optional `--dashboard` flag or split out `/mantle:workspace` that combines status + next-action.

### Domain-Specific Features

- **Model Profiles (quality/balanced/budget/adaptive/inherit)** — `get-shit-done/references/model-profiles.md` defines five profiles with per-agent overrides in `.planning/config.json`, switched via `/gsd:set-profile`. **Adopt wholesale** — drops directly into issue 75. No reason to reinvent; extract the profile schema + resolution logic.
- **Progressive Disclosure via `@file` References** — Shared agent boilerplate (mandatory-initial-read, project-skills-discovery) lives in `get-shit-done/references/` and agents load via `@~/.claude/get-shit-done/references/*.md`. CHANGELOG (#2361, #2363, #2368) reports 10–30% per-agent compression with no behaviour change. **Adopt immediately** — resolves issue 79 as a near-zero-cost refactor: move repeated blocks to `.mantle/references/`, replace with `@filepath` includes.
- **Session Report with Token Audit Trail** — `/gsd:session-report` produces a structured SESSION_REPORT.md with token usage, commit count, outcomes; `.planning/config.json` declares `context_window` tiers (PEAK/GOOD/DEGRADING/POOR at 30%/50%/70%). **Adapt + extend** — issue 88 should be live instrumentation (wrap each skill invocation, aggregate in state.md, surface in `/mantle:status`) rather than post-hoc, using GSD's tier thresholds as the starting point.
- **Agent Size-Budget Enforcement** — `tests/agent-size-budget.test.cjs` enforces line-count caps (XL: 1600, Large: 1000, Default: 500) with a deliberate override process requiring PR rationale. **Adopt** — add `tests/test_skill_size_budget.py` (pytest version) wired into `just check`. Combine with issue 88's token audit to catch silent skill bloat at CI time.
- **Dynamic Next-Step Routing with Quality Gates** — `/gsd:next` reads ROADMAP + STATE to detect phase completion and route to the next logical command, gated on prior-phase verification. **Adopt** — essentially issues 71/72 pre-built. Implement `/mantle:next` reading `.mantle/state.md` + `.mantle/issues/`, offering defer/stop/force-advance.
- **Workstream-Scoped Parallel Execution** — Already listed under architecture, but worth restating as a product feature: `/gsd:new-workspace --strategy worktree|clone --repos repo1,repo2` delivers isolated multi-repo scoping. **Adapt** — the skeleton issue 85 needs. GSD punts true cross-repo merging; this is a prerequisite, not the final solution.
- **Greenfield gap — GitHub/Jira integration** — GSD has `/gsd:inbox` (GitHub issue triage) and a "ship" command for PR creation, but no Jira sync and no bidirectional GitHub automation. Issues 42 (GitHub reporter) and 67 (Jira orchestration) are genuinely unsolved in the competitive landscape; a real differentiation opportunity for Mantle beyond optimisation.
- **Product-design messaging correction** — Mantle's current positioning claims GSD has "no runtime." GSD's `sdk/src/` (session-runner, context-engine, cli-transport, event-stream, tool-scoping) contradicts this directly. **Action** — revise `.mantle/product-design.md` differentiator row to lead with *persistent cross-project knowledge graph* + *Obsidian-native* rather than runtime; those are Mantle's real edges.

---

## Actionable Recommendations

### Adopt
> High confidence — bring this in directly with minimal adaptation.

- **Model Profiles** (domain, issue 75): Extract GSD's 5-tier profile schema + `/gsd:set-profile` logic into `.mantle/config.md` and `/mantle:set-profile`.
- **Progressive Disclosure via `@file`** (domain, issue 79): Move repeated skill/agent boilerplate to `.mantle/references/` and replace with `@filepath` includes. Expect 10–30% compression on each command.
- **Explicit Next-Command Handoff** (CLI, issue 71/72): Add routing directives to every `/mantle:*` command and programmatic handoff via `SlashCommand` where appropriate.
- **Deterministic-First Prompt Ordering** (patterns, issue 87): Hoist stable workflow instructions above injected vault context in top commands so prompt caching pays off.
- **Per-Session Cost Tracking with Running Totals** (patterns + architecture, issues 88/75): Emit `MantleTokenCostEvent` per API call; aggregate into `.mantle/audit-tokens.jsonl`; use for sweep + A/B harness.
- **Dual-Subprocess Golden Parity** (testing): Build a prompt-layer integration test harness that compares baseline vs refactored prompts — unlocks safe token cuts in issues 87/88.
- **Agent/Skill Size-Budget CI Test** (domain, issue 88): Pytest enforcing tiered line-count caps on skills + agents, with documented override process.
- **Typed YAML Frontmatter Manifests** (patterns): Standardise `required_context`, `allowed_tools`, `hooks` on every command; pre-validate before dispatch.
- **Semantic Error Classification with Exit Codes** (patterns): Four-class error taxonomy + stable exit codes; aligns with learning 51.

### Adapt
> Worth doing but needs adjustment for our context.

- **Phase-Manifest Context Reduction** (architecture + patterns, issues 87/88): Per-command file manifests plus markdown-aware truncation (Python port of `context-truncation.ts`) while keeping `state.md` as the single entry point.
- **Context Budget Tiers (PEAK/GOOD/DEGRADING/POOR)** (domain, issue 88): Take GSD's 30%/50%/70% thresholds but instrument *during* execution, not only post-hoc.
- **State-Aware Routing with Quality Gates** (CLI, issue 70): Translate `/gsd:next` into `/mantle:triage` between build and verify; surface incomplete tasks + warnings and force an advance/resolve choice.
- **Persistent Session Directories** (CLI, issue 73): `/mantle:quick-fix` with `.mantle/quick-fixes/` for off-roadmap hotfixes.
- **Workstream Session-Identity Resolution** (architecture, issue 85): Reuse GSD's env-var → TTY session-key resolution as the foundation for cross-repo context tracking; Mantle still has to solve the cross-repo merge layer on top.
- **Deviation Rules with Bounded Repair Budgets** (patterns): Add explicit rules + 1–2 attempt cap to `/mantle:implement` + `/mantle:build`; log deviations in SUMMARY.md.
- **Hook-Driven Observability** (architecture, issue 88): Start with PostToolUse token-emit hook; defer full suite until there's a real use for it.
- **Interactive Dashboard** (CLI): Enhance `/mantle:status` with an optional `--dashboard` view; or split out `/mantle:workspace`.

### Skip
> Not relevant or not worth the cost for us right now.

- **Wave-Based Parallel Execution** (architecture): Throughput isn't the bottleneck; Mantle is optimising cost, not concurrency.
- **Multi-Runtime Installer** (CLI): Mantle is Claude Code-only by design; document as a future extension point, don't build it.
- **Workstream Multiplexing for single-repo parallelism** (architecture): Mantle has no same-repo multi-project use case; keep the session-identity pattern (see above) but not the workstream routing.
- **Custom Cross-Platform Test Runner** (testing): pytest already handles this well enough.

---

## Backlog Implications

- **Issues 75 and 79 can be collapsed into a single "adopt GSD patterns" sprint.** Both have near-drop-in GSD implementations (model-profiles.md and `@file` references). Low risk, high leverage.
- **Issues 87 and 88 should be re-scoped around GSD's context-engine + event-stream patterns.** The current framing ("mantle compress" + "audit-tokens sweep") is narrower than needed — the underlying pattern (per-command file manifests + live token telemetry) delivers both at once. Consider merging or tightly sequencing them.
- **Issues 71/72/70/73 (CLI workflow optimisations) cluster around a single theme: state-aware routing and lifecycle gates.** GSD's `/gsd:next`, `/gsd:progress`, `/gsd:quick`, `/gsd:debug` are four faces of the same pattern. Could ship as one connected milestone ("Workflow Routing v1") rather than four independent issues.
- **Consider a new issue: product-design messaging correction.** The "GSD has no runtime" claim in `.mantle/product-design.md` is demonstrably false and undermines Mantle's credibility. Revise to lead with the real edges — persistent cross-project Obsidian-native knowledge graph, and the cohesive idea-to-review lifecycle — rather than a runtime comparison Mantle loses.
- **New opportunity worth adding to backlog: prompt-layer golden-parity test harness.** GSD's `golden-policy.ts` + `mutation-sandbox.ts` pattern fills Mantle's biggest testing gap (no way to verify prompt refactors don't regress behaviour). Unblocks aggressive token cuts on build/implement/add-skill with confidence.
- **Reinforces existing issue 85** (cross-repo context): GSD solves *parallel-context isolation*, not true cross-repo — Mantle still has greenfield work on the merge/link layer. Scope issue 85 around "build on GSD's session-identity pattern; design the cross-repo link model ourselves."