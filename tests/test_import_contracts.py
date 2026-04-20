"""End-to-end test that the import-linter contract catches a violation."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).lstrip())


def test_forbidden_contract_catches_core_to_cli_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock package whose core/ imports cli/ must fail forbidden contract."""
    pkg = tmp_path / "mock_mantle"
    _write(pkg / "__init__.py", "")
    _write(pkg / "cli" / "__init__.py", "VALUE = 1\n")
    _write(
        pkg / "core" / "__init__.py",
        "from mock_mantle.cli import VALUE  # the violation\n",
    )

    config = tmp_path / "importlinter.ini"
    config.write_text(
        textwrap.dedent(
            """\
            [importlinter]
            root_package = mock_mantle

            [importlinter:contract:core-forbidden]
            name = mock core never imports from cli
            type = forbidden
            source_modules =
                mock_mantle.core
            forbidden_modules =
                mock_mantle.cli
            """
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    # Use importlinter.cli.lint_imports (not application.use_cases.lint_imports)
    # because the cli wrapper bootstraps the app configuration and returns an
    # int exit code (1=failure). The lower-level use_cases function returns a
    # bool and requires manual configuration setup; the cli entrypoint is the
    # supported Python API surface as of import-linter 2.x.
    from importlinter import cli

    exit_code = cli.lint_imports(config_filename=str(config))
    assert exit_code != 0, (
        "Forbidden contract should have failed on the violation."
    )
