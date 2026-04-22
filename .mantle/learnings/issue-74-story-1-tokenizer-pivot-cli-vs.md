---
issue: 74
title: 'story-1: tokenizer pivot + cli-vs-script'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-22'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

Two pivots mid-build on issue 74:

1. Anthropic's count_tokens API requires a funded account to access, even though the endpoint itself is nominally free. Claude Code's OAuth does not grant API access. For any local tokenization need, default to tiktoken cl100k_base (community-cited ~97% accuracy against Claude BPE, sufficient for rank/delta work).

2. Scripts under `scripts/` for recurring tooling are an anti-pattern in this codebase. Default to `src/mantle/core/` + `src/mantle/cli/` split. The extra ~50 lines buys tests, discoverability, and reuse — pays back on first re-invocation.

Apply when: any future feature tempted to live as a one-shot script. Challenge the framing at shape time — is this truly one-shot, or will the capability be re-invoked?