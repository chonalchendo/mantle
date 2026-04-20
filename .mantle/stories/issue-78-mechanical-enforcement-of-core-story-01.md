---
issue: 78
title: Wire import-linter into pyproject + just check, with self-test and doc update
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a maintainer of mantle, I want the `core/ → cli/api` boundary mechanically enforced via `just check` so that any agent or human who tries to violate it gets a precise, actionable failure naming the file, the import, and the contract — making architectural drift impossible rather than merely discouraged.

## Depends On

None — independent.

## Approach

Use `import-linter`'s declarative `forbidden` contract (per the chosen shape, Approach A). The contract lives in `pyproject.toml` so future invariants append without new infrastructure. The guard runs in `just check` and `just ci`. Test the guard end-to-end by spinning up a mock package via `tmp_path` + `monkeypatch.syspath_prepend` and invoking `import-linter`'s Python API — proving the contract type catches the violation we care about, not just that the tool runs.

Order of edits inside the implementation session: write the failing test first (TDD), watch it fail with `ModuleNotFoundError: import-linter` to confirm the dep wiring is needed, then add the dependency, then add the config, then wire `justfile`, then update CLAUDE.md.

## Implementation

### `pyproject.toml` (modify)

Two changes.

**1. Add to `[dependency-groups].lint`:**

```toml
lint = [\"ruff>=0.11\", \"import-linter>=2.0\"]
```

**2. Append a top-level config block** (place after `[tool.pytest.ini_options]`, the current last section):

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

Notes:
- `name` is editorial — it appears in the failure header agents will read. Do not rename it to a code-style identifier.
- `mantle.api` is referenced even though the package does not currently exist. `import-linter` treats absent forbidden modules as inert (nothing imports from them, so no contract failure). This future-proofs without a follow-up edit.
- `exclude_type_checking_imports = true` is recommended (per the import-linter skill) so `if TYPE_CHECKING:` imports can cross boundaries without breaking the build.

### `justfile` (modify)

Modify the `check` recipe and the `ci` recipe to run `lint-imports` after the existing checks:

```makefile
# Run all checks (lint, format check, type, test)
check: lint type test
    uv run ruff format src/ tests/ --check
    uv run lint-imports
    @echo \"All checks passed.\"

# CI mode (non-destructive, used in GitHub Actions)
ci:
    uv run ruff check src/ tests/
    uv run ruff format src/ tests/ --check
    uv run ty check src/
    uv run lint-imports
    uv run pytest
```

Position: after the cheap fast checks (ruff/ty), before/around tests. `lint-imports` parses the module graph; it's fast but not as fast as ruff.

### `CLAUDE.md` (modify)

In the existing `## Architecture` section, the current bullet reads:

> - `core/` never imports from `cli/` or `api/`

Append two bullets so the section reads:

```markdown
## Architecture

- `core/` never imports from `cli/` or `api/`
  - Enforced by `import-linter` — see `[tool.importlinter]` in `pyproject.toml`. The check runs as part of `just check` and CI.
  - To add another architectural invariant (e.g., `cli/` may not import `tests.fixtures`), append a new contract under `[[tool.importlinter.contracts]]`. No new tooling required.
- `cli/` depends on `core/`, never the reverse
- All state lives in `.mantle/` (local) or the Obsidian vault
```

(Preserve the two existing follow-on bullets `cli/ depends on core/...` and `All state lives in...` — the change is *insertion* of two sub-bullets under the first invariant, not replacement.)

### `tests/test_import_contracts.py` (new file)

```python
\"\"\"End-to-end test that the import-linter contract catches a violation.\"\"\"

import textwrap
from pathlib import Path

import pytest


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).lstrip())


def test_forbidden_contract_catches_core_to_cli_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    \"\"\"A mock package whose core/ imports cli/ must fail the forbidden contract.\"\"\"
    pkg = tmp_path / \"mock_mantle\"
    _write(pkg / \"__init__.py\", \"\")
    _write(pkg / \"cli\" / \"__init__.py\", \"VALUE = 1\\n\")
    _write(
        pkg / \"core\" / \"__init__.py\",
        \"from mock_mantle.cli import VALUE  # the violation\\n\",
    )

    config = tmp_path / \"importlinter.ini\"
    config.write_text(
        textwrap.dedent(
            \"\"\"\\
            [importlinter]
            root_package = mock_mantle

            [importlinter:contract:core-forbidden]
            name = mock core never imports from cli
            type = forbidden
            source_modules =
                mock_mantle.core
            forbidden_modules =
                mock_mantle.cli
            \"\"\"
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    from importlinter.application import use_cases

    exit_code = use_cases.lint_imports(config_filename=str(config))
    assert exit_code != 0, \"Forbidden contract should have failed on the violation.\"
```

#### Design decisions

- **Use the Python API (`use_cases.lint_imports`), not subprocess.** Faster, no shell quoting, exit code is a clean int. Per the import-linter skill, this is the supported integration entry point.
- **Mock package, not the real `mantle` package.** Testing against `mantle.core` would either pass trivially (real code is clean) or require deliberately polluting the codebase. A throwaway `mock_mantle` package is the standard pattern.
- **`monkeypatch.syspath_prepend` instead of installing the mock package.** `import-linter` uses `grimp`, which discovers modules via `sys.path`. Adding `tmp_path` to `sys.path` is the lightest-weight way to make the mock importable for the duration of the test.
- **INI config format, not TOML.** `importlinter.ini` is `import-linter`'s native flat-config format — no `[tool.importlinter]` prefix needed. Simpler than embedding a TOML fragment for one test.
- **Skip the \"clean tree passes\" companion test.** `just check` itself exercises the live `pyproject.toml` config end-to-end every time it runs, so a redundant in-test assertion adds maintenance cost for no signal. AC3 explicitly asks for the violation-catch test, not both directions.
- **No assertion on stderr/stdout content.** Output formatting belongs to `import-linter` and may change across versions — the contract behaviour we own is the exit code. AC2 (\"failure message names file, import, remediation\") is exercised by `lint-imports` itself when run as part of `just check`; verifying its output is stable in a unit test would couple us to upstream formatting decisions.

#### Import requirements

- `import-linter` must be present in the test environment. Adding it to `[dependency-groups].lint` (which is included in `[dependency-groups].check`, which is what `uv sync --group check` installs) makes it available to pytest. No separate test dependency needed.

## Tests

### `tests/test_import_contracts.py` (new file)

- **test_forbidden_contract_catches_core_to_cli_import**: writes a mock package where `mock_mantle.core` imports from `mock_mantle.cli`, configures an `import-linter` `forbidden` contract over the mock package via a temp `.ini` file, prepends `tmp_path` onto `sys.path`, calls `importlinter.application.use_cases.lint_imports(config_filename=...)`, and asserts the returned exit code is non-zero — proving the contract type we use catches the violation pattern this issue exists to prevent.

#### Test fixture requirements

- `tmp_path` (pytest builtin) for the mock package and the config file.
- `monkeypatch` (pytest builtin) for `syspath_prepend`.
- No mocks of `import-linter` internals — the test's purpose is to exercise the real contract type end-to-end.