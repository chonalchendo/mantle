---
issue: 78
title: Mechanical enforcement of core/ → cli/api import-direction invariant
approaches:
- import-linter contracts in pyproject.toml (data-driven)
- Custom pytest using ast to walk src/mantle/core/
- Ruff custom rule plugin
chosen_approach: import-linter contracts in pyproject.toml (data-driven)
appetite: small batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-20'
updated: '2026-04-20'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches considered

### A — import-linter contracts in pyproject.toml (data-driven) — **chosen**

Add `import-linter` as a dev dependency. Declare a `forbidden` contract in `[tool.importlinter]` inside `pyproject.toml`: `mantle.core` cannot import from `mantle.cli` or `mantle.api`. Wire `lint-imports` into `just check`. Test the guard by spinning up a mock package via `tmp_path` + `monkeypatch.syspath_prepend`, programmatically running import-linter against it with a violating import, and asserting failure.

- **Appetite:** small batch.
- **Tradeoffs:** off-the-shelf tool, declarative config, designed exactly for this job, extensible to future contracts (layers, independence, custom types) without new infrastructure. Costs one new dev dependency.
- **Rabbit holes:** subprocess-vs-API for the test (resolved: use `lint_imports()` API). Configuring the contract to also cover `mantle.api` even though that package does not yet exist (resolved: contract module specs may reference future packages — they are inert until the package exists, per the import-linter skill).
- **No-gos:** does not add new architectural rules beyond core→cli/api; does not block tests; does not customise `lint-imports` output formatting yet.

### B — Custom pytest using ast to walk src/mantle/core/

Write a new pytest that walks `src/mantle/core/**/*.py`, parses each file with `ast`, and fails on any `ImportFrom` whose module starts with `mantle.cli` or `mantle.api`.

- **Appetite:** small batch.
- **Tradeoffs:** zero new dependencies. Easy to read. But every future invariant (layers, independence, no-skills-imports-core) requires hand-rolled ast code — directly contradicts AC4 (\"data-driven so additional invariants can be added later without new infrastructure\").
- **Rejected:** AC4 is load-bearing — the issue body explicitly says \"more invariants will likely follow.\"

### C — Ruff custom rule plugin

Build a ruff plugin (or use a banned-imports lint rule) that fires when `core/` files contain forbidden imports.

- **Appetite:** medium batch.
- **Tradeoffs:** runs in the same pass as ruff. Ruff plugin authoring is non-trivial (Rust or external Python plugin tooling). Banned-imports rules are file-pattern based, not architectural — express badly when the rule depends on which directory the file lives in.
- **Rejected:** out of proportion to the work; not data-driven in the architectural sense (Approach A wins on the same criterion at lower cost).

## Comparison

| | A: import-linter | B: ast pytest | C: ruff plugin |
|---|---|---|---|
| Appetite | small | small | medium |
| Key benefit | declarative, extensible | zero new deps | single-pass with ruff |
| Key risk | contract config drift (low) | re-implement for every new invariant | plugin authoring overhead |
| Complexity | low | medium (per invariant) | high |

## Chosen — A: import-linter

Smallest viable approach that satisfies AC4 (data-driven, extensible). Off-the-shelf, well-supported, exactly the right shape for this problem. The remaining ACs are mechanical wiring around it.

## Strategy

Three files change, one is added.

**`pyproject.toml`** — add to `[dependency-groups].lint`:
```toml
\"import-linter>=2.0\",
```
And add a top-level config block:
```toml
[tool.importlinter]
root_package = \"mantle\"
include_external_packages = false
exclude_type_checking_imports = true

[[tool.importlinter.contracts]]
name = \"core never imports from cli or api\"
type = \"forbidden\"
source_modules = [\"mantle.core\"]
forbidden_modules = [\"mantle.cli\", \"mantle.api\"]
```
The contract `name` is editorial (per the import-linter skill anti-pattern: don't ship `forbidden_1`-style names — the name appears in the failure header that agents will consume).

**`justfile`** — extend the `check` recipe so `lint-imports` runs alongside ruff/ty/pytest, and the `ci` recipe identically:
```makefile
check: lint type test
    uv run ruff format src/ tests/ --check
    uv run lint-imports
    @echo \"All checks passed.\"
```
Position after `lint type test` so the cheap fail-fast checks run first.

**`tests/test_import_contracts.py`** (new) — one test that uses the import-linter Python API to verify the guard catches violations:
```python
def test_forbidden_contract_catches_violation(tmp_path, monkeypatch):
    # Build a mock package on disk: mock_pkg/{core,cli}/__init__.py
    # core/__init__.py contains: from mock_pkg import cli  (the violation)
    # Write a temporary import-linter config targeting mock_pkg with the
    # forbidden contract: source mock_pkg.core, forbidden mock_pkg.cli.
    # monkeypatch.syspath_prepend(tmp_path) so grimp can resolve the package.
    # Call importlinter.application.use_cases.lint_imports(config_filename=...)
    # Assert the return code indicates failure (non-zero).
```
A second test that calls `lint_imports` against the real `pyproject.toml` and asserts a clean tree passes is redundant with `just check` itself, so skip it — `just check` already exercises the live config end-to-end.

**`CLAUDE.md`** — extend the existing Architecture section. Today it says: \"`core/` never imports from `cli/` or `api/`\". Append:
> Enforced mechanically by `import-linter` — see `[tool.importlinter]` in `pyproject.toml`. To add another architectural invariant, append a new contract to that block. Failures appear in `just check` output naming the file, the offending import, and the contract violated.

## Fits architecture by

- Honours the system-design rule `core/ never imports from cli/ or api/`. This issue installs the mechanical guard for that rule.
- Reuses the existing `just check` gate — same entry point for humans, CI, and `/mantle:build` agents. No new orchestration surface.
- Lives entirely in project metadata (`pyproject.toml`, `justfile`, `CLAUDE.md`, one new test). Zero changes to `src/mantle/` shipped code.
- Per the import-linter skill: contract `name` is editorial (will appear in agent-consumed failure output); contracts that include `tests.*` as sources are an anti-pattern (tests legitimately import everything) — our contract correctly scopes to `mantle.core` only.

## Does not

- **Does not introduce new architectural rules** beyond `core → cli/api forbidden`. The issue is about enforcement, not new boundaries.
- **Does not enforce a layered contract** (`cli` may depend on `core`, `core` may depend on nothing else inside mantle). That's already implicit and not in the ACs; can be added later by appending a `layers` contract.
- **Does not block tests from importing freely.** Tests are not in `source_modules`. Per the import-linter skill anti-pattern, scoping contracts over `tests.*` is wrong.
- **Does not customise `lint-imports`'s default failure output.** AC2 requires \"file, forbidden import, remediation steps formatted for agent injection.\" The default output already names the offending module, the imported module, and the contract name. If verification surfaces that this is insufficient for agent self-correction, a follow-up issue can add a custom contract type with `render_broken_contract` (per the import-linter skill custom-contract reference). Not in scope here — adding a custom type now would be tactical over-engineering.
- **Does not retrofit historical violations.** Codebase is assumed clean today (CLAUDE.md states the convention has been followed); the linter run in Step 8 will verify.
- **Does not create a separate CONTRIBUTING.md.** CLAUDE.md is the existing canonical contributor doc and is auto-loaded by Claude Code, so the doc lives where agents will actually read it.
- **Does not configure `import-linter` at module-graph depth (layers, independence, custom contracts).** Single `forbidden` contract is exactly what the ACs require; future contracts will append.