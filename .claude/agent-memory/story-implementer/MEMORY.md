# Story Implementer Memory

- [CLI test patterns](feedback_cli_test_patterns.md) — list-skills/list-tags tests live in tests/cli/test_skills.py and tests/cli/test_main.py, imported directly from mantle.cli.main
- [Run just fix before done](feedback_ruff_formatting.md) — ruff reformats multi-line path assemblies; always run `just check` before reporting DONE
- [Story internal inconsistencies](feedback_story_inconsistencies.md) — if a "keep unchanged" test asserts behavior the story's production edit removed, delete it symmetrically
- [pytest under TYPE_CHECKING](feedback_pytest_type_checking.md) — if a test file only uses pytest for type annotations (no @pytest.fixture), ruff TC002 requires moving the import under TYPE_CHECKING
- [Py3.14 except tuple-parens stripped](feedback_python314_except_tuples.md) — ruff format rewrites `except (A, B):` to `except A, B:` per PEP 758; valid, don't "fix"
- [Cyclopts app iteration yields strings](feedback_cyclopts_app_iteration.md) — `for x in app` yields name strings (incl --help/-h/--version); use `app[name]` to get sub-App with .group
- [inline-snapshot formatting warning](feedback_inline_snapshot_formatting.md) — "not able to format your code" on --inline-snapshot=create is harmless; `just fix` handles reformat
