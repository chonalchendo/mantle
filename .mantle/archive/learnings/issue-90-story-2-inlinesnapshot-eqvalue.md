---
issue: 90
title: 'story-2: inline_snapshot EqValue vs harness signature'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-24'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## Gotcha

`run_prompt_parity(command, fixture, baseline=snapshot())` doesn't work directly — the harness calls `baseline.splitlines()` before comparison, which fails on inline_snapshot's `EqValue` proxy. Workaround: `baseline=""` + `assert result.current_text == snapshot()` as a separate line.

## Why

`inline_snapshot.snapshot()` returns a proxy that only supports `__eq__`, not string methods. The harness signature assumes `baseline: str`.

## Recommendation

Either change the harness to accept an `EqValue` OR fold the normalization into a returned `current_text` attribute and assert that against `snapshot()` — the latter is what ended up shipping. Future harness users will copy this two-line pattern; worth a simplifier pass to make it one line.