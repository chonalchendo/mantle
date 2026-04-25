# Story Implementer Memory

- [CLI test patterns](feedback_cli_test_patterns.md) — list-skills/list-tags tests live in tests/cli/test_skills.py and tests/cli/test_main.py, imported directly from mantle.cli.main
- [Run just fix before done](feedback_ruff_formatting.md) — ruff reformats multi-line path assemblies; always run `just check` before reporting DONE
- [Story internal inconsistencies](feedback_story_inconsistencies.md) — if a "keep unchanged" test asserts behavior the story's production edit removed, delete it symmetrically
- [pytest under TYPE_CHECKING](feedback_pytest_type_checking.md) — if a test file only uses pytest for type annotations (no @pytest.fixture), ruff TC002 requires moving the import under TYPE_CHECKING
- [Py3.14 except tuple-parens stripped](feedback_python314_except_tuples.md) — ruff format rewrites `except (A, B):` to `except A, B:` per PEP 758; valid, don't "fix"
- [Cyclopts app iteration yields strings](feedback_cyclopts_app_iteration.md) — `for x in app` yields name strings (incl --help/-h/--version); use `app[name]` to get sub-App with .group
- [inline-snapshot formatting warning](feedback_inline_snapshot_formatting.md) — "not able to format your code" on --inline-snapshot=create is harmless; `just fix` handles reformat
- [init_project signature](feedback_init_project_signature.md) — project.init_project takes (tmp_path, project_name); story skeletons sometimes omit the name arg
- [import-linter Python API](feedback_importlinter_api.md) — use importlinter.cli.lint_imports (returns int, bootstraps config); use_cases.lint_imports returns bool and needs manual configure()
- [cyclopts app() sys.exit(0) on success](feedback_cyclopts_app_sysexit.md) — main_module.app() raises SystemExit(0) after any None-returning command; wrap with pytest.raises(SystemExit) and assert code==0
- [Prompt sweep substring guard](feedback_prompt_sweep_exact_strings.md) — tests/prompts/test_prompt_sweep.py asserts literal "MANTLE_DIR=$(mantle where)"; new prelude variants must be added to accepted tuple
- [Parity harness snapshot() incompatibility](feedback_parity_harness_snapshot.md) — pass baseline="" to run_prompt_parity, then assert result.current_text == snapshot() separately; don't pass snapshot() as baseline
- [TC001 noqa for pydantic cross-module fields](feedback_tc001_pydantic_noqa.md) — pydantic models with other-core-module field types need `# noqa: TC001`; moving under TYPE_CHECKING breaks pydantic runtime resolution
