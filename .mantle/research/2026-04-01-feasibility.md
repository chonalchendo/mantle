---
date: '2026-04-01'
author: 110059232+chonalchendo@users.noreply.github.com
focus: feasibility
confidence: 8/10
idea_ref: AI-generated code optimizes for task completion, not design coherence. As
  projects grow, structural debt accumulates — tightly coupled modules, missing abstractions,
  inconsistent patterns — blocking new features. Existing cleanup tools handle local
  mess but can't address large-scale architectural redesign.
tags:
- type/research
- phase/research
---

# Refactor Command — Building Block Viability Research

Research into the five building blocks needed for a `/mantle:refactor` command that diagnoses architectural debt and proposes design strategies.

## Building Block 1: Codebase Analysis at Scale (8/10)

**Verdict: Viable.** The proven pattern is static analysis first, then token-budget-aware selection, then LLM analysis.

### Key Findings
- **Aider's repo map** is the reference implementation: tree-sitter extracts definitions/references, NetworkX PageRank ranks files, binary-search budget algorithm fits results into configurable token limits. Output is signatures + key lines, not full code bodies. (Apache 2.0)
- **CodePlan (Microsoft Research, ACM 2024)** proves repository-level LLM tasks require a dependency graph as first-class input. Incremental dependency graph + change may-impact analysis selects files per LLM call. 5/7 repos pass validity vs 0/7 without planning.
- **Python static analysis is mature:** ast (stdlib), pydeps (bytecode import graphs, MIT), networkx (graph algorithms), libcst (transforms). All cover extraction without LLM involvement.
- **Context rot is empirically documented** (Chroma Research): performance degrades non-uniformly as input grows. More irrelevant code causes errors beyond length scaling. Careful curation matters more than large windows.
- **Lost in the middle validated:** LLMs retrieve info at start/end of context but miss middle content.
- **JetBrains 2025:** Observation masking beat LLM summarization in 4/5 scenarios at 52% lower cost.

### What LLMs Need for Architecture Analysis
Module-level import graph with in/out-degree, file-level summaries from hierarchical summarization, explicit coupling metrics (cyclomatic complexity, efferent/afferent coupling). Full function bodies are NOT required — signatures and metrics suffice.

### Design Implication
Pre-processing phase using ast/pydeps/networkx produces structured JSON, then separate LLM analysis phase. Token budget calculation must be dynamic. Multi-pass for large codebases: (1) import graph, (2) coupling metrics per subsystem, (3) synthesis with prior-pass summaries.

---

## Building Block 2: Skill-Based Evaluation Lenses (7/10)

**Verdict: Viable with sequential pass mitigation.**

### Key Findings
- **Multi-lens composition from SonarQube, ATAM, fitness functions:** Independent-lens evaluation followed by aggregation beats joint reasoning over all lenses at once.
- **ATAM four-prompt sequential strategy (2025 arxiv):** One prompt per concern outperformed single-prompt combined evaluation. LLM identified more tradeoffs than novice architects.
- **Curse of Instructions (OpenReview 2025):** LLM instruction-following degrades as instruction count rises. Per-instruction performance falls monotonically.
- **ConInstruct (Nov 2025):** Inter-constraint conflicts silently dropped 55%+ of the time even by top models.
- **Existing Mantle skills map directly:** design-review = Ousterhout quality attributes, designing-architecture = SOLID/DDD, designing-tests = test architecture.

### Skill Selection
Current detect_skills_from_content uses exact string matching — misses semantic relevance. For small skill sets, an LLM-based selection pass is cheap and effective.

### Design Implication
Run each skill as a focused diagnostic pass, then synthesize. Do NOT load all skills into one monolithic prompt. Token budget: 6 skills at 150 lines = 3,600 tokens — fine individually, problematic combined.

---

## Building Block 3: Meaningfully Different Strategy Generation (7/10)

**Verdict: Viable with explicit divergence techniques.**

### Key Findings
- **LLM convergence is real and measured.** GPT-4o produces ~2 distinct algorithms where humans find 3. Degeneration-of-Thought named in EMNLP 2024.
- **Diverge-then-converge prompting works (CreativeDC, Dec 2025):** Separates creative exploration from constraint satisfaction. Significantly higher diversity while maintaining utility.
- **ATAM quality attribute scenario scoring:** Structure each strategy around explicit quality attributes. Force scoring on each attribute. Validated — LLMs identified more tradeoffs than human reviewers.
- **Multi-agent debate does NOT reliably outperform single-agent prompting** (ICLR 2025). But persona prompting helps for subjective tasks like architecture selection.

### Critical Risk: Anchoring from Diagnosis
If diagnosis produces a single root cause framing, the strategy phase anchors to it. Diagnosis output must expose MULTIPLE problem framings.

### Design Implication
Two-phase prompt: (1) divergent ideation without evaluating, (2) convergent elaboration of most distinct approaches. Add validation sub-prompt checking strategy distinctness on quality attributes. Use ATAM scoring for tradeoff articulation.

---

## Building Block 4: Scope Definition and Targeting (8/10)

**Verdict: Viable. Primitives already exist in Mantle.**

### Key Findings
- **Declarative scope outperforms agent-inferred scope** (ICSE 2025): Explicitly specifying refactoring type raises identification from 15.6% to 86.7%.
- **Python ast stdlib** can parse imports in ~15 lines. Mantle's absolute-import convention maps directly to filesystem paths.
- **Reverse dependency lookup:** Search all files for imports of a target module. Zero-dependency using ast.
- **Git log hotspot detection:** Already used in Mantle's simplify.py.

### Four Scope Types
- Module-local: Single file cleanup (AST of single file)
- Interface redesign: Change public API + update callers (reverse dependency graph)
- Cross-cutting extraction: Pull concern from multiple files (grep across codebase)
- Layer reorganization: Move modules between packages (full import graph + tests)

### Design Implication
Two-phase: (1) User declares scope type + root path, Claude proposes file set, (2) User confirms, Claude proceeds. CLI: --focus description --root path_or_module.

---

## Building Block 5: Implement Pipeline Integration (8/10)

**Verdict: Viable. No new schema types needed.**

### Key Findings
- **Big-bang refactors universally discouraged.** Strangler Fig pattern: each step independently committable.
- **IssueNote.blocked_by is the load-bearing field.** Already exists. Refactoring decomposition maps directly to blocked_by chains.
- **Refactoring stories are chores, not user stories.** Template: characterization tests, mechanical transformation, verify regressions, clean up.
- **Characterization tests before structural changes** (Feathers): Write tests documenting current behaviour, then refactor under those tests.
- **No new schema required.** IssueNote, ShapedIssueNote, StoryNote all work as-is. Add type/refactor tag.

### Design Implication
Output set of IssueNote files with blocked_by chains, tagged type/refactor. Flow through normal shape-plan-implement pipeline. Prepend characterization test steps when coverage is absent.

---

## Cross-Cutting Synthesis

### Recommended Command Architecture
1. **Scope Declaration** (user input): Type + root path/module
2. **Static Analysis** (deterministic): ast/pydeps dependency graph, git log hotspots, coupling metrics to structured JSON
3. **Per-Lens Diagnosis** (LLM, sequential): Run each relevant skill as a focused diagnostic pass
4. **Diagnosis Aggregation** (LLM): Synthesize across lenses into multi-framing diagnosis
5. **Strategy Generation** (LLM, diverge-then-converge): 2-3 distinct strategies with ATAM quality attribute scoring
6. **Output**: IssueNote files with blocked_by chains, type/refactor tag, ready for pipeline

### Highest-Risk Areas
1. Strategy divergence quality (7/10) — prototype needed
2. Multi-skill diagnostic quality (7/10) — prototype needed

### Key Design Decisions Needed
- Should diagnosis and strategy generation be one command or two?
- How to handle no StoryNote.blocked_by for intra-issue story ordering?
- Which static analysis dependencies (zero-dep ast-only vs pydeps/networkx)?

### Sources
- Aider repo map: aider.chat/2023/10/22/repomap.html
- CodePlan (Microsoft): arxiv.org/abs/2309.12499
- pydeps: github.com/thebjorn/pydeps
- Chroma context rot: trychroma.com/research/context-rot
- JetBrains context management: blog.jetbrains.com/research/2025/12/efficient-context-management
- ATAM with LLMs: arxiv.org/html/2506.00150
- Curse of Instructions: openreview.net/forum?id=R6q67CDBCH
- ConInstruct: arxiv.org/html/2511.14342
- CreativeDC divergent thinking: arxiv.org/html/2512.23601v1
- LLM algorithmic diversity: arxiv.org/html/2503.00691v2
- ICSE 2025 refactoring: conf.researchr.org/details/icse-2025/ide-2025-papers/12
- Strangler Fig: learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
- Characterization testing (Feathers): michaelfeathers.silvrback.com/characterization-testing
- Fitness functions: thoughtworks.com/en-us/insights/articles/fitness-function-driven-development