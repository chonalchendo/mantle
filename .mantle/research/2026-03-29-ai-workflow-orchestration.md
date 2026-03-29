---
date: 2026-03-29
focus: technology
confidence: 8/10
tags:
  - type/research
---

# AI Workflow Orchestration Patterns

## Summary

AI workflow orchestration with configurable human checkpoints is a mature, well-validated pattern across major agent frameworks and commercial coding tools. The consistent finding: **checkpoints belong at phase boundaries (spec, plan, output), not at every intermediate step**. Automation within phases is the norm.

## Key Finding: The Three-Checkpoint Pattern

Every major tool converges on the same structure:

1. **Specification checkpoint** — human defines the problem
2. **Plan checkpoint** — human reviews the AI's plan before execution
3. **Output checkpoint** — human reviews the final deliverable

Everything between checkpoints runs autonomously.

**Evidence:**
- **Devin** uses exactly two checkpoints: plan approval and PR review. Everything between (code execution, iteration, testing) is fully autonomous.
- **GitHub Copilot Workspace** validates "spec → plan → implementation" with human review at each phase boundary. Downstream stages regenerate when upstream is edited.
- **GitHub Agentic Workflows** default to read-only, require explicit safe-output declarations for writes, never auto-merge PRs.

## Framework Patterns

### LangGraph (LangChain)
- Stateful graph-based orchestration with first-class interrupt/checkpoint support
- Persistent state (PostgreSQL, DynamoDB) so workflows survive restarts
- Pattern: automated nodes run uninterrupted, interrupt nodes pause for humans

### CrewAI
- Task-level `human_input=True` as a first-class feature
- Event-driven flow where human input is just another event
- Better than AutoGen for deterministic sequential pipelines

### Claude Agent SDK
- Recommends human checkpoints at decision boundaries, not every step
- Automated verification (linting, LLM-as-judge) runs first; human escalation at errors and ambiguous decisions
- Subagent pattern: orchestrator (narrow permissions, reads/routes) + specialized subagents (isolated context, single goal)

## Compound Failure Risk

The strongest argument FOR strategic checkpoints (not elimination of them):

- **Lusser's Law applied to AI**: An 85%-accurate agent fails ~80% of the time on a 10-step task (0.85^10 ≈ 0.20)
- **Multi-agent error amplification**: Up to 17.2x error amplification vs single-agent when agents are composed without structured topologies
- **Silent failures**: Wrong interpretive choices mid-chain contaminate downstream context without surfacing

This supports the three-checkpoint pattern — checkpoints exist to break long chains, not to confirm every action.

## "Quality Upstream Inputs" Principle

Validated across multiple implementations: "The rate-limiting factor for agentic coding workflow quality is what goes into the agent before execution starts." (Codegen)

Implication: human review of the specification/plan is where input actually matters. Confirming intermediate automated steps has diminishing returns.

## Automation-Complacency Risk

When users trust automation, they review less carefully at the remaining checkpoints. Mitigated by:
- Regular "invite points" for human input (not mandatory gates)
- Surfacing intermediate state so humans can inspect if they choose
- Making checkpoints substantive (not just "approve/reject" but "edit the plan")

## Integration Considerations for Mantle

1. **Mantle's `.mantle/` directory already serves as persistent state** — analogous to LangGraph's checkpointer
2. **Middle steps (research → plan-issues → shape-issue → plan-stories) map to within-phase automation** — can run as a subagent pipeline
3. **Input quality is the upstream dependency** — the problem definition step (idea + challenge) must produce a specific-enough spec before automation begins
4. **Automation level toggles require custom implementation** — no framework provides this out of the box
5. **GitHub Agentic Workflows' "safe outputs" model** is worth studying: define upfront what a workflow can produce (e.g., "can open PR but cannot merge")

## Gaps

- No direct evidence on per-invocation automation levels in any major framework
- Sparse data on AI quality for planning/scoping tasks (vs. coding tasks)
- No benchmarks for Mantle-style pipeline quality under automated vs. confirmed conditions
- Automation-complacency at remaining checkpoints is unstudied for this use case

## Sources

- LangGraph Docs: Human-in-the-loop, Checkpointing Best Practices
- CrewAI vs AutoGen analysis (ZenML, DataCamp)
- Building Agents with Claude Agent SDK (Anthropic)
- GitHub Copilot Workspace (GitHub Next)
- Devin AI Complete Guide (DigitalApplied)
- GitHub Agentic Workflows (GitHub Blog)
- "The Math That's Killing Your AI Agent" (Towards Data Science)
- Agent Failure Modes Guide (Galileo)
- UX Research: Balancing AI Automation and Human Oversight (UXmatters)
- How to Build Agentic Coding Workflows (Codegen Blog)
