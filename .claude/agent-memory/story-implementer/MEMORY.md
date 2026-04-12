# Story Implementer Memory

- [CLI test patterns](feedback_cli_test_patterns.md) — list-skills/list-tags tests live in tests/cli/test_skills.py and tests/cli/test_main.py, imported directly from mantle.cli.main
- [Run just fix before done](feedback_ruff_formatting.md) — ruff reformats multi-line path assemblies; always run `just check` before reporting DONE
- [Story internal inconsistencies](feedback_story_inconsistencies.md) — if a "keep unchanged" test asserts behavior the story's production edit removed, delete it symmetrically
