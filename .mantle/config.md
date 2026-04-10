---
personal_vault: /Users/conal/test-vault
verification_strategy: 'Run uv run pytest for the full test suite. Then verify each
  acceptance criterion independently by reading implementation code, checking file
  existence, and confirming behaviour matches the specification. For any criterion
  involving CLI behaviour changes, also run a live E2E test: build a throwaway fixture
  in /tmp/, invoke the real mantle CLI via uv run mantle against it, and inspect the
  filesystem to confirm the expected outcome — this catches prompt-flow regressions
  and ordering bugs that unit tests cannot see.'
auto_push: false
tags:
- type/config
---

## Verification Strategy

_Define how you verify that each issue is complete before moving on._

## Personal Vault

_Set via `mantle init-vault <path>`. Cross-project skills and knowledge._
