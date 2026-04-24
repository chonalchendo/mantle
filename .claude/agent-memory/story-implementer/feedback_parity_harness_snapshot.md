---
name: Parity harness incompatible with snapshot() as baseline
description: run_prompt_parity(baseline=snapshot()) crashes — harness calls baseline.splitlines() before EqValue can intercept ==
type: feedback
---

Do NOT pass `snapshot()` directly as the `baseline=` argument to `run_prompt_parity()`. The harness calls `baseline.splitlines()` inside its function body before any `==` comparison, so an inline-snapshot `EqValue` raises `AttributeError`.

**Why:** The `run_prompt_parity` signature takes `baseline: str` and calls `baseline.splitlines()` for the unified diff. The `snapshot()` return is an `EqValue` proxy that only supports `==`, not str methods.

**How to apply:** Instead, pass `baseline=""` to `run_prompt_parity` to get the normalized `current_text`, then assert `result.current_text == snapshot()` as a separate line. The regression detection comes from the snapshot comparison, not from `result.matches`.
