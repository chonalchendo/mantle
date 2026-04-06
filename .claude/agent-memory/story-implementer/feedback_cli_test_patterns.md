---
name: CLI test patterns for main.py commands
description: How CLI command tests are structured in this project (imports, fixtures, capsys)
type: feedback
---

CLI command tests import functions directly from `mantle.cli.main` (e.g., `from mantle.cli.main import list_tags_command`) and call them with explicit `path=` arguments rather than using `monkeypatch.chdir`. Fixtures use `_ConfigFrontmatter` + `vault.write_note` for config setup.

**Why:** Keeps tests isolated and avoids side effects from changing cwd. Explicit path args are more readable.

**How to apply:** When adding new CLI command tests, always pass `path=project` explicitly. Use `capsys.readouterr()` to capture output. Mirror the fixture pattern in tests/cli/test_skills.py.
