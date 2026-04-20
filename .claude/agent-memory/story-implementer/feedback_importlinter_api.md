---
name: import-linter Python API surface (v2.x)
description: importlinter.application.use_cases.lint_imports returns bool and lacks bootstrap; use importlinter.cli.lint_imports for int exit codes
type: feedback
---

When invoking import-linter as a Python API (e.g. inside a pytest test against a mock package), use `importlinter.cli.lint_imports`, not `importlinter.application.use_cases.lint_imports`.

**Why:** As of import-linter 2.11, the lower-level `use_cases.lint_imports` returns a `bool` (True=passed, False=failed), AND requires `importlinter.configuration.configure()` to be called first — otherwise it raises `KeyError: 'USER_OPTION_READERS'` at config-read time. The cli wrapper bootstraps configuration at import time and converts the bool to a 0/1 exit code. Older story specs may still reference `use_cases.lint_imports` returning an int; that signature is gone.

**How to apply:** In tests doing `from importlinter import cli; cli.lint_imports(config_filename=...)`, assert `exit_code != 0` for an expected violation. The INI flat-config format is still supported (`[importlinter]` + `[importlinter:contract:<id>]` sections). Do not try to migrate it to TOML for the test — INI is simpler and still the documented format for standalone config files.
