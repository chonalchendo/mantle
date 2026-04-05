---
date: '2026-04-05'
author: 110059232+chonalchendo@users.noreply.github.com
title: fastmcp-patterns-for-mantle
verdict: scrap
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Adopt FastMCP patterns to enhance Mantle
**Problem**: Exploring whether FastMCP's architecture (MCP server framework, middleware, providers, server composition) could improve Mantle's UX across command discovery, session continuity, implementation orchestration, knowledge retrieval, or token management.
**Vision alignment**: Weak

## Exploration

**What is FastMCP?** A Python framework for building MCP servers — decorator-based tool/resource/prompt registration, server composition via mounting, middleware pipelines, provider pattern for extensible components, multi-transport support (stdio, HTTP, SSE).

**Core question**: Does FastMCP unlock anything for Mantle, or is it a solution looking for a problem?

**User's assessment**: CLI-over-Bash works well today. No specific pain point. Interest was in scanning for opportunities rather than solving a known problem. Token/model management surfaced as a genuine side-discovery but is orthogonal to FastMCP.

**Scope**: Small — cherry-pick patterns, not a rearchitecture.

## Challenges Explored

**Assumption surfacing** (3 assumptions, small feature depth):

1. "FastMCP patterns are the best source for these improvements" — CRACKED. The transferable patterns (middleware, providers) are general software engineering patterns, not MCP-specific. Better to design from first principles against Mantle's own architecture.
2. "Token/model management belongs in Mantle" — OPEN. Genuine need but unclear if it's Mantle's job or infrastructure monitoring. Not FastMCP-related.
3. "CLI-over-Bash will keep working well" — HELD. True today, worth revisiting if Claude Code adds native MCP tool support with better UX.

## Approaches Considered

None — verdict is scrap for the FastMCP adoption angle.

## Verdict

**Verdict**: scrap
**Reasoning**: FastMCP is a well-built framework that solves a problem Mantle doesn't have. The CLI-over-Bash integration works well, there's no cross-tool requirement yet, and the transferable patterns (middleware, providers) are general patterns better designed from first principles against Mantle's architecture. Token management surfaced as a real need but is unrelated to FastMCP.
**If scrapping**: Focus on the existing backlog — issue 32 (knowledge engine) is the most impactful planned work. Token management could become a future issue if it keeps surfacing as a pain point. Revisit MCP adoption if/when Claude Code native MCP support offers meaningfully better UX than Bash tool calls, or when cross-tool support (Cursor/Windsurf) becomes a priority.

**Side discovery**: Token/model management is a real unmet need. Consider capturing as a separate idea if it keeps coming up.