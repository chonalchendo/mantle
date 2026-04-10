---
date: '2026-04-10'
author: 110059232+chonalchendo@users.noreply.github.com
repo_url: https://github.com/addyosmani/agent-skills
repo_name: agent-skills
dimensions:
- architecture
- patterns
- testing
- cli-design
- domain
tags:
- type/scout
---

# Scout Report: agent-skills

**Repository**: https://github.com/addyosmani/agent-skills
**Analyzed**: 2026-04-10
**Project context**: AI workflow engine giving coding agents persistent memory, idea validation, and structured product development

---

## Executive Summary

Agent-skills is a collection of production-grade engineering skills for AI coding agents, packaged as markdown files with slash commands, hooks, and agent personas. It covers the full development lifecycle (spec → plan → build → test → review → ship) through composable skill modules. **Signal quality: HIGH** — this repo solves several problems directly relevant to Mantle's current backlog, particularly around skill structure, agent discipline, and context management. The single most important takeaway: skills should be structured as executable workflows with anti-rationalization guardrails and verification gates, not reference documentation.

---

## Findings by Dimension

### Architecture

- **Pattern name**: Workflow Encapsulation via Skills
  - **What they do**: Decompose complex engineering workflows into discrete, reusable skill modules with explicit activation conditions and verification gates.
  - **Why it's relevant**: Mantle skills lack standardized anatomy — this shows how to make workflows explicitly discoverable by agents.
  - **Recommendation**: Adopt — Formalize Mantle's skill system with explicit trigger metadata and standardized section templates.

- **Pattern name**: Thin CLI Router with Skill Binding
  - **What they do**: Commands are thin markdown stubs that route to named skills, decoupling entry points from implementation logic.
  - **Why it's relevant**: Similar to Mantle's cli/core separation — validates the pattern and shows how to extend it to slash commands.
  - **Recommendation**: Adapt — Keep Cyclopts routing but ensure commands invoke composed skills rather than containing workflow logic inline.

- **Pattern name**: Anti-Rationalization Defense System
  - **What they do**: Each skill includes a "Common Rationalizations" table pairing agent excuses with factual rebuttals, preventing agents from skipping required steps.
  - **Why it's relevant**: Mantle has no explicit mechanism to prevent agents from rationalizing away structured workflows.
  - **Recommendation**: Adopt — Add "Common Rationalizations" sections to Mantle's skill format and story templates.
  - **Example** (from their TDD skill):
    ```
    | Rationalization | Reality |
    | "I'll add tests later" | You won't. Tests written after the fact test implementation, not behavior. |
    | "This is too simple to test" | Simple code breaks. A 2-line test catches a 2-minute bug. |
    ```
    Mantle equivalent for `implement.md`: `"I can implement all stories in one pass" → "Each story gets a fresh context window for a reason — monolithic passes degrade with context length."`

- **Pattern name**: Hierarchical Context Injection
  - **What they do**: Define context loading as five layers (Rules → Specs → Source → Errors → Conversation) with explicit guidance on what loads when.
  - **Why it's relevant**: Mantle's vault is relatively flat; layering context by persistence/scope would improve agent focus and reduce context bloat.
  - **Recommendation**: Adapt — Layer Mantle knowledge by persistence: project-level rules, feature-level specs, task-level patterns, transient outputs.
  - **Example** (their 5-layer hierarchy mapped to Mantle):
    ```
    Layer 1 (always loaded):  CLAUDE.md, .mantle/state.md
    Layer 2 (per-issue):      .mantle/shaped/<issue>.md, acceptance criteria
    Layer 3 (per-story):      relevant skills from .claude/skills/
    Layer 4 (per-iteration):  test failures, lint errors
    Layer 5 (transient):      conversation history
    ```

- **Pattern name**: Phase-Mapped Skill Sets
  - **What they do**: Explicitly group skills by lifecycle phase and wire commands to the skill set for that phase, enabling auto-selection.
  - **Why it's relevant**: Mantle doesn't formally map skills to workflow phases — this would improve skill injection (issue 52).
  - **Recommendation**: Adopt — Create phase-to-skill mappings so agents discover applicable skills by workflow phase.
  - **Example** (how agent-skills maps `/build` → skills):
    ```
    /build → incremental-implementation + test-driven-development
    /review → code-review-and-quality + security-and-hardening
    ```
    Mantle equivalent: `/mantle:shape-issue` → `software-design-principles` + `designing-architecture`; `/mantle:implement` → `python-project-conventions` + issue-specific skills from `skills_required`.

- **Pattern name**: Specialized Agent Personas
  - **What they do**: Define reusable agent personas (code-reviewer, security-auditor, test-engineer) with explicit frameworks and output schemas.
  - **Why it's relevant**: Mantle spawns subagents but doesn't formalize their personas or review frameworks.
  - **Recommendation**: Adopt — Define Mantle's subagent personas with explicit review frameworks and output schemas.
  - **Example** (their code-reviewer persona uses a 5-axis framework):
    ```
    Review axes: correctness, readability, architecture, security, performance
    Severity: Critical (request changes) | Important (should fix) | Suggestion (nice-to-have)
    ```
    Mantle equivalent: story-implementer persona could have axes like `correctness, test coverage, convention compliance, commit atomicity` with the same severity grading.

### Coding Patterns

- **Pattern name**: Anti-Rationalization Tables
  - **What they do**: Embed excuse/rebuttal pairs in every skill to prevent agents from skipping steps.
  - **Why it's relevant**: Directly improves skill injection effectiveness and agent compliance for issue 52.
  - **Recommendation**: Adopt — Add to all Mantle skills to shift from prescriptive to defensive guidance.

- **Pattern name**: Progressive Disclosure
  - **What they do**: Keep SKILL.md files minimal (~150 lines) with supporting reference files loaded on-demand via links.
  - **Why it's relevant**: Reduces context bloat during skill discovery while preserving full detail when needed.
  - **Recommendation**: Adopt — Separate triggering metadata from detailed process flows in Mantle skills.
  - **Example** (their structure): `skills/security-and-hardening/SKILL.md` (~120 lines, overview + workflow) references `references/security-checklist.md` (~200 lines, detailed checklist) loaded only when the agent reaches the security verification step. Mantle equivalent: `cyclopts/SKILL.md` keeps trigger + key patterns; a separate `cyclopts/reference-api.md` holds the full Cyclopts API surface.

- **Pattern name**: Process Over Prose
  - **What they do**: Structure skills as numbered, verifiable workflow steps with exit criteria, not advisory prose.
  - **Why it's relevant**: AI agents follow process more reliably than principles — steps have checkpoints, principles have loopholes.
  - **Recommendation**: Adopt — Audit Mantle skills and replace narrative guidance with numbered, sequenced steps.
  - **Example** (their spec-driven-development skill):
    ```
    1. SPECIFY: Write functional spec with acceptance criteria → human approves
    2. PLAN: Break spec into tasks ≤100 lines each → human approves
    3. TASKS: Create task list with dependencies → human approves
    4. IMPLEMENT: Build one task at a time, test after each
    ```
    vs. prose approach: "Make sure you have a good spec before building." The numbered version has four checkpoints an agent can't skip; the prose version has zero.

- **Pattern name**: Always/Ask-First/Never Boundaries
  - **What they do**: Use a three-tier decision system for agent autonomy: always-allowed, requires-approval, and forbidden actions.
  - **Why it's relevant**: Provides governance structure for skill injection (issue 52) and contextual errors (issue 51).
  - **Recommendation**: Adopt — Introduce boundary system in skill frontmatter with CLI enforcement.
  - **Example** (from their security skill):
    ```
    Always: validate input, use parameterized queries, hash passwords
    Ask First: change auth logic, store PII, modify access controls
    Never: commit secrets, disable security headers, log credentials
    ```
    Mantle equivalent for implementation skill: `Always: run tests after each story, commit atomically` / `Ask First: skip a blocked story, modify shared fixtures` / `Never: amend previous story commits, skip test retries`.

- **Pattern name**: Change Sizing Discipline
  - **What they do**: Enforce ~100-line change targets with vertical slicing and explicit splitting strategies for oversized changes.
  - **Why it's relevant**: Prevents monolithic commits and bounds the scope of skill-injected implementations.
  - **Recommendation**: Adopt — Add change-sizing guidance to implementation and review skills.

- **Pattern name**: Evidence-Based Verification
  - **What they do**: Every skill ends with a verification checklist requiring observable evidence (test output, build logs), not assertions.
  - **Why it's relevant**: Makes verification non-negotiable and gives contextual errors (issue 51) concrete hooks.
  - **Recommendation**: Adopt — Extend Mantle's skill system to include mandatory verification sections with evidence types.
  - **Example** (from their TDD skill verification section):
    ```
    ## Verification
    - [ ] All tests pass (paste test output)
    - [ ] No skipped or pending tests
    - [ ] Coverage ≥ threshold (paste coverage report)
    - [ ] Edge cases have dedicated tests
    ```
    "Seems right" is explicitly banned — every checkbox requires pasted evidence. Mantle equivalent for `/mantle:verify`: require `just check` output, not a self-assessment.

### Testing

- **Pattern name**: Test-Driven Development with Bug Reproduction
  - **What they do**: Every feature starts with a failing test; every bug starts with a reproduction test before the fix (Prove-It Pattern).
  - **Why it's relevant**: Directly supports issue 50 (staleness detection test suite) — prevents fix-before-proof behavior.
  - **Recommendation**: Adopt — Use the Prove-It Pattern framework for staleness regression tests.

- **Pattern name**: Test Stratification by Size
  - **What they do**: Classify tests as Small (ms, single-process), Medium (seconds, localhost), Large (minutes, external), with 80/15/5 distribution.
  - **Why it's relevant**: Mantle doesn't explicitly codify test sizing — this prevents slow CI pipelines.
  - **Recommendation**: Adapt — Adopt size classification; mark staleness regression tests appropriately.

- **Pattern name**: DAMP Tests + Minimal Mocking
  - **What they do**: Prefer real implementations over mocks, use Descriptive And Meaningful Phrases in test names, assert on specific values not snapshots.
  - **Why it's relevant**: Aligns with Mantle's "mock boundaries, not internals" philosophy; strengthens test readability.
  - **Recommendation**: Adopt — Document DAMP patterns explicitly in Mantle's test conventions.

- **Pattern name**: CI Quality Gates Pipeline
  - **What they do**: Enforce sequential lint → typecheck → tests → build → integration → E2E → security with no gate skippable.
  - **Why it's relevant**: Mantle lacks a formal CI pipeline definition — this provides a template.
  - **Recommendation**: Adopt — Implement CI workflow with explicit gates; run staleness regression tests on schedule.

- **Pattern name**: Test Engineer Agent Persona
  - **What they do**: Define a dedicated test-engineering agent with explicit responsibilities for edge case identification and test design.
  - **Why it's relevant**: Provides a template for systematic test thinking for new Mantle features.
  - **Recommendation**: Adopt — Create a test-engineering checklist for staleness detection tests.

### CLI Design

- **Pattern name**: Lifecycle-Driven Command Grouping
  - **What they do**: Organize commands around development lifecycle phases (DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP), not alphabetically.
  - **Why it's relevant**: Directly addresses issue 48 (CLI help grouping) — grouping by workflow phase creates intuitive mental models.
  - **Recommendation**: Adopt — Reorganize Mantle's --help around workflow phases using Cyclopts help panels.

- **Pattern name**: Declarative Command Registry with Frontmatter
  - **What they do**: Each command is a markdown file with YAML frontmatter declaring its description, making discoverability automatic.
  - **Why it's relevant**: Could feed descriptions directly to Cyclopts' help system from command metadata.
  - **Recommendation**: Adapt — Use YAML frontmatter in Mantle's slash commands for automatic help generation.

- **Pattern name**: Command-to-Skill Invocation
  - **What they do**: Commands don't implement logic — they invoke named skills, enabling composable error recovery chains.
  - **Why it's relevant**: When commands fail, the error handler can recommend the recovery skill (addresses issue 51).
  - **Recommendation**: Adapt — Make error handling composable by routing failures to recovery skills.

- **Pattern name**: Session Hook for Context Injection
  - **What they do**: A session-start hook automatically injects the meta-skill into every session, providing skill discovery without manual invocation.
  - **Why it's relevant**: Mantle already uses SessionStart hooks for compilation — this validates the pattern and suggests expanding it.
  - **Recommendation**: Adopt — Expand Mantle's session hook to inject available skills and contextual help.

- **Pattern name**: Minimal Command Bodies
  - **What they do**: Slash commands are 5-20 lines, linking to skills for detailed steps — keeps token usage low.
  - **Why it's relevant**: Prevents help text bloat; keeps --help scannable while linking to deeper context.
  - **Recommendation**: Adopt — Structure Mantle's help with one-line summaries linking to deeper docs.

### Domain-Specific Features

- **Pattern name**: Skill Anatomy as Executable Workflow
  - **What they do**: Skills are structured as step-by-step workflows with gated phases (SPECIFY→PLAN→TASKS→IMPLEMENT), each requiring human review before advancing.
  - **Why it's relevant**: Directly applicable to issue 52 (skill injection into planning) — skills become execution flows, not reference docs.
  - **Recommendation**: Adopt — Reframe Mantle skills as execution flows with explicit gates.
  - **Example** (their standardized SKILL.md anatomy):
    ```markdown
    # Skill Name
    description: "TRIGGER when <condition>..."   ← agent discovery
    ## When to Use / When NOT to Use              ← scoping
    ## Process (numbered steps with gates)        ← executable workflow
    ## Common Rationalizations (table)            ← anti-skip guardrails
    ## Red Flags (checklist)                      ← early warning signs
    ## Verification (evidence checklist)          ← exit criteria
    ```
    Every section serves a specific function in the agent's decision loop. Compare to Mantle's current skills which are dense knowledge dumps without this structure.

- **Pattern name**: Specialist Agent Personas with Review Frameworks
  - **What they do**: Three agent personas (code-reviewer, test-engineer, security-auditor) with role-specific five-axis review frameworks and severity labeling.
  - **Why it's relevant**: Mantle's agent orchestration could benefit from formalized personas with consistent output templates.
  - **Recommendation**: Adapt — Create Mantle agent personas for each domain phase (design review, implementation, verification, retrospective).

- **Pattern name**: Session Hooks for Crash Recovery
  - **What they do**: The simplify-ignore hook protects performance-critical code during refactoring via temporary backups and hashed placeholders.
  - **Why it's relevant**: Demonstrates how to protect domain-critical code from over-simplification during AI refactoring.
  - **Recommendation**: Adapt — Implement simplify-ignore zones for Mantle's vault compilation and agent spawning logic.

- **Pattern name**: Reference Checklists as Lightweight Knowledge
  - **What they do**: Four lightweight checklists (testing, security, performance, accessibility) under 250 lines each, loaded on-demand by skills.
  - **Why it's relevant**: Maps to issue 41 (querying learnings for patterns) — extractable, queryable knowledge artifacts.
  - **Recommendation**: Adapt — Extract Mantle's vault into skill layer (workflows) and reference layer (patterns, checklists, templates).

---

## Actionable Recommendations

### Adopt
> High confidence — bring this in directly with minimal adaptation.

- **Anti-Rationalization Tables** (from Architecture/Patterns): Add "Common Rationalizations" sections to all Mantle skills to prevent agents from skipping required steps
- **Process Over Prose** (from Patterns): Restructure skills as numbered, verifiable workflow steps with exit criteria
- **Lifecycle-Driven Command Grouping** (from CLI): Organize --help around workflow phases for issue 48
- **Evidence-Based Verification** (from Patterns): Add mandatory verification checklists with evidence types to skills
- **Test-Driven Bug Reproduction** (from Testing): Use the Prove-It Pattern for issue 50's staleness regression tests

### Adapt
> Worth doing but needs adjustment for our context.

- **Hierarchical Context Injection** (from Architecture): Layer Mantle knowledge by persistence/scope instead of flat vault — adapt to work with Jinja2 compilation
- **Specialist Agent Personas** (from Domain): Create Mantle-specific personas for each workflow phase — adapt agent-skills' generic roles to our domain
- **Progressive Disclosure** (from Patterns): Separate skill metadata from detail — adapt to Obsidian vault structure with wikilinks
- **Reference Checklists** (from Domain): Extract queryable reference layer from vault — adapt to support issue 41's learnings query system

### Skip
> Not relevant or not worth the cost for us right now.

- **Browser Testing via DevTools** (from Testing): Not applicable — Mantle has no browser runtime
- **Thin CLI Router** (from Architecture): We already have this pattern via Cyclopts — no change needed

---

## Backlog Implications

- **Issue 52 (Skill injection)**: Strongly reinforced. Agent-skills demonstrates that skills should be executable workflows with phase gates and anti-rationalization guardrails — not passive reference docs. The phase-to-skill mapping pattern gives issue 52 a concrete implementation model.
- **Issue 48 (CLI help grouping)**: Directly informed. Lifecycle-driven grouping (DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP) provides the organizing principle for Cyclopts help panels.
- **Issue 50 (Staleness test suite)**: The Prove-It Pattern and test size stratification offer a testing methodology to adopt. Write reproduction tests before fixes, classify staleness tests by size.
- **New issue candidate**: "Skill anatomy standardization" — define a standard SKILL.md format with required sections (trigger conditions, numbered workflow steps, verification checklist, common rationalizations). This would be a prerequisite for issue 52 and improve all existing skills.