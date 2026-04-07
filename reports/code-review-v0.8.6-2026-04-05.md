# Code Review: v0.8.6 — Issue 30 (Stories 1–3)

**Date:** 2026-04-05
**Files Changed:** 4 (core/skills.py, cli/main.py, tests/core/test_skills.py, tests/cli/test_skills.py)

## Summary

- Critical: 1 | Warnings: 2 | Minor: 2

---

## Issues Found

### Critical

| Location | Issue | Fix |
|----------|-------|-----|
| `skills.py:846` | `generate_index_notes()` places the HTML comment marker before the YAML frontmatter. Obsidian (and any YAML-frontmatter parser) requires `---` to be the very first line of the file. The current output is `<!-- mantle:generated -->\n---\n...` which means the frontmatter is never parsed — the index notes land in the vault as plain markdown with a broken frontmatter block. | Move `_GENERATED_MARKER` inside the body, after the closing `---`. Place it on the first line of the markdown body. The existence check at line 839 already just does `_GENERATED_MARKER not in existing`, so the position does not matter for that logic. |

### Warnings

| Location | Issue | Fix |
|----------|-------|-----|
| `skills.py:709–711` | Tag suffix matching in `detect_skills_from_content()` uses bare substring search (`suffix in content_lower`). A short suffix like `web` or `data` or `python` will match anywhere in the content, producing false positives. E.g. a skill tagged `topic/python` will match any content containing the word "python" even when the name, slug, and description checks have already been bypassed. The earlier name/slug match already handles the clean cases; this layer adds noise. | Either require a whole-word match (`re.search(rf"\b{re.escape(suffix)}\b", content_lower)`), or raise the threshold to require the full tag (not just the suffix), or remove the suffix step entirely given the description-overlap check that follows already covers semantic relevance. |
| `tests/core/test_skills.py:18,628–637` | Tests import and directly test the private helper `_match_skill_slug`. The project standard is "test external behaviour, not internal implementation details". `_match_skill_slug` is a one-line slug comparison that is already implicitly covered by `TestDetectGaps`, `TestLoadRelevantSkills`, and `TestDetectStubs`. The dedicated class adds coupling to an implementation detail with no coverage benefit. | Remove `TestMatchSkillSlug` and the `_match_skill_slug` import. The behaviour is exercised through the public API. |

### Minor

| Location | Issue | Fix |
|----------|-------|-----|
| `tests/cli/test_skills.py:225–249` | `TestListSkillsCommand.test_tag_flag_filters_output` calls `core_skills.list_skills()` directly instead of going through `list_skills_command`. The test is named and classed as a CLI test but does not exercise the CLI layer at all — it is a duplicate of the core unit test. | Call `list_skills_command(tag="topic/python", path=project)` and assert on `capsys` output, which is what the other two tests in the class do. |
| `skills.py:921–926` | `compile_skills()` catches a bare `Exception` when calling `generate_index_notes()`. The docstring for `generate_index_notes` only declares `VaultNotConfiguredError`, and any genuine bug (e.g. a permissions error, an `AttributeError`) would be silently swallowed as a warning. | Catch a specific set of expected exceptions (`OSError`, `VaultNotConfiguredError`), or let it propagate. If silent degradation is intentional, at minimum log the full traceback so it is diagnosable. |

---

### Critical Thinking

| Aspect | Observation | Alternative/Note |
|--------|-------------|------------------|
| Non-obvious concern | `generate_index_notes()` calls `list_skills()` (which calls `_resolve_vault_skills_dir`) and then calls `_resolve_vault_skills_dir` a second time independently to derive the vault root (line 828). This is two config reads for one function call, and the vault root is derived by `.parent` from the skills dir, so it is fragile if the directory structure changes. | Pass the vault root as a parameter, or derive it once and thread it through. Alternatively, expose a `_resolve_vault_root` helper. |
| Convention followed | The description-overlap threshold of 3 tokens (line 716) is an unconstrained magic number chosen without reference to any statistical baseline. It happens to work for the test fixture because the test description was written to have exactly 3 tokens overlapping. | A first-principles approach would measure false-positive rate against a sample of real issue/story content, or make the threshold configurable. As-is, it is invisible to callers and untestable without white-box knowledge of the constant. |

---

## Recommendations

### Must Fix Before Release

1. **Fix the generated marker position in index notes.** The `_GENERATED_MARKER` comment must appear after the closing `---` of the frontmatter, not before the opening `---`. Without this fix, index notes written to the vault will have malformed frontmatter and will not be processed correctly by Obsidian or any vault tooling.

### Should Fix

2. **Tighten tag suffix matching to whole-word.** Short suffixes (`web`, `data`, `python`, `go`) will produce false-positive skill detections on common English words. Use `re.search(rf"\b{re.escape(suffix)}\b", content_lower)` or drop this matching step in favour of the description-overlap step that already follows it.

3. **Replace the direct core call in `test_tag_flag_filters_output` with a CLI call.** The test is in the CLI test suite and should test the CLI layer.

### Technical Debt (Future)

4. **Remove `TestMatchSkillSlug` or promote `_match_skill_slug` to a documented utility.** Testing private helpers breaks the test/implementation boundary. If the function is worth testing directly, it is worth exposing.

5. **Replace bare `except Exception` in `compile_skills()` with a specific exception set.** Silent swallowing of unexpected errors makes debugging index generation failures very difficult in production.
