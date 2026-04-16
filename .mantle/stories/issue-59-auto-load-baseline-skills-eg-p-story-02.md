---
issue: 59
title: Wire baseline skills into auto_update_skills, compile_skills, and CLI reporting
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle contributor, I want baseline skills to be unioned into `skills_required` and compiled into `.claude/skills/` automatically, with a clear two-group report, so agents always see the language-baseline knowledge without depending on issue wording.

## Depends On

Story 1 — needs `core/baseline.py::resolve_baseline_skills()` to exist.

## Approach

Thread `baseline.resolve_baseline_skills()` through the two integration points in `core/skills.py` (auto-update and compile) so baselines are unioned with detected skills. The CLI command splits its report into baseline vs issue-matched groups, writing to stderr per `cli-design-best-practices` (stdout kept clean for piping). Docs note added to CLAUDE.md so the baseline concept is discoverable.

## Implementation

### src/mantle/core/skills.py (modify)

Modify `auto_update_skills` (around line 783):

```python
def auto_update_skills(
    project_dir: Path,
    issue_number: int,
) -> list[str]:
    """Auto-detect and update skills_required from issue and story content.

    Unions baseline skills (from project constraints) with detected
    matches (from issue body). Both are merged additively into
    state.md and the issue file.

    Returns:
        List of newly added skill names (not previously in
        skills_required). Includes baseline additions.
    """
    from mantle.core import baseline

    mantle_dir = project.resolve_mantle_dir(project_dir)

    # ... existing content gathering unchanged ...

    detected = detect_skills_from_content(project_dir, combined) if content_parts else []
    baseline_skills = list(baseline.resolve_baseline_skills(project_dir))

    effective = tuple(sorted(set(baseline_skills) | set(detected)))
    if not effective:
        return []

    current_state = state.load_state(project_dir)
    existing = set(current_state.skills_required)
    new_skills = [s for s in effective if s not in existing]

    if new_skills:
        state.update_skills_required(project_dir, effective, additive=True)

    # Also update issue frontmatter with the unioned set
    # (existing logic, but use `effective` instead of `detected`)
    ...

    return new_skills
```

Modify `compile_skills` (around line 974):

```python
def compile_skills(
    project_dir: Path,
    issue: int | None = None,
) -> list[str]:
    """Compile vault skills to .claude/skills/ for Claude Code.

    Unions baseline skills into the effective filter so language
    baselines are always compiled, even when an issue frontmatter
    predates baseline support.
    """
    from mantle.core import baseline

    skills_target = project_dir / ".claude" / "skills"
    compiled_slugs: list[str] = []

    skills_filter: tuple[str, ...] = ()
    baseline_skills = baseline.resolve_baseline_skills(project_dir)

    if issue is not None:
        from mantle.core import issues as issues_mod
        issue_path = issues_mod.find_issue_path(project_dir, issue)
        if issue_path is not None:
            note, _ = issues_mod.load_issue(issue_path)
            if note.skills_required:
                skills_filter = note.skills_required

    if baseline_skills and skills_filter:
        skills_filter = tuple(sorted(set(skills_filter) | set(baseline_skills)))
    elif baseline_skills and not skills_filter:
        # No issue filter: union baseline with state.md skills_required
        state_required = state.load_state(project_dir).skills_required
        skills_filter = tuple(sorted(set(state_required) | set(baseline_skills)))

    # ... rest unchanged ...
```

#### Design decisions

- **Local import of `baseline`**: avoid circular imports (baseline imports skills, skills imports baseline only at call-site).
- **Soft failure preserved**: `resolve_baseline_skills` returns `()` on any problem, so the wrap keeps skills.py resilient.
- **Union semantics**: baseline is additive, never overrides detection — matches the issue ACs.
- **`sorted(...)` for stability**: deterministic ordering in state.md and issue frontmatter.

### src/mantle/cli/main.py (modify)

Modify `update_skills_command` around line 968:

```python
@app.command(name="update-skills", group=GROUPS["planning"])
def update_skills_command(
    issue: ...,
    path: ... = None,
) -> None:
    """Auto-detect and update skills_required from issue content."""
    if path is None:
        path = Path.cwd()

    import sys
    from mantle.core import baseline, skills

    baseline_names = baseline.resolve_baseline_skills(path)
    new_skills = skills.auto_update_skills(path, issue)

    baseline_set = set(baseline_names)
    issue_matched_new = [s for s in new_skills if s not in baseline_set]

    if baseline_names:
        print(file=sys.stderr)
        print(
            f"Baseline skills (always loaded): {\", \".join(baseline_names)}",
            file=sys.stderr,
        )

    if issue_matched_new:
        print(file=sys.stderr)
        print(
            f"Issue-matched skills (from body scan): "
            f"{\", \".join(issue_matched_new)}",
            file=sys.stderr,
        )
        print("Updated skills_required in state.md.", file=sys.stderr)
    elif new_skills:
        # Only baseline-new, no body-scan matches
        print("Updated skills_required in state.md.", file=sys.stderr)
    elif not baseline_names:
        print(file=sys.stderr)
        print("No new skills detected.", file=sys.stderr)
```

#### Design decisions

- **Stderr for status**: follows cli-design-best-practices Output Contract. Stdout stays empty so piping works.
- **Two-group split**: clear separation matches the report format named in the issue.
- **Graceful silent path**: nothing printed if no baseline, no detected, no new — keeps CI output clean.

### CLAUDE.md (modify)

Add a short note in the skills/compilation section mentioning baselines:

```markdown
### Baseline skills

Some vault skills are auto-loaded based on project-level constraints,
independent of issue body matching. For example, any project with
`requires-python >= 3.14` in `pyproject.toml` gets the `python-314`
vault skill (when present) added to `skills_required` by
`mantle update-skills` and compiled by `mantle compile`. This ensures
agents working on 3.14+ code never misdiagnose valid PEP 758 syntax.
Baseline resolution lives in `core/baseline.py` — the mapping is a
flat function, not a plug-in registry.
```

## Tests

### tests/core/test_skills.py (modify)

Add to `TestAutoUpdateSkills`:

- **test_baseline_unioned_with_detected**: write a `pyproject.toml` with `requires-python = ">=3.14"`, vault has `python-314` skill; issue mentions an unrelated skill. Assert both `python-314` and the detected skill are in `skills_required` after the call.
- **test_baseline_added_when_no_issue_matches**: same setup but issue body mentions nothing matchable. Assert `python-314` is in `skills_required`.
- **test_baseline_not_added_if_missing_from_vault**: pyproject `>=3.14` but no `python-314` in vault. Assert warning emitted, `python-314` NOT in `skills_required`.

Add to a new test class `TestCompileSkillsBaseline`:

- **test_baseline_compiled_even_when_issue_frontmatter_omits_it**: pyproject `>=3.14`, vault has `python-314`, issue frontmatter `skills_required = ["cyclopts"]`. Assert both `python-314` and `cyclopts` directories appear under `.claude/skills/`.

### tests/cli/ CLI test (modify if present, else new `tests/cli/test_update_skills.py`)

- **test_reports_baseline_group_on_stderr**: invoke the CLI command; capture stderr; assert it contains `"Baseline skills (always loaded): python-314"` when baseline is active.
- **test_reports_issue_matched_group_on_stderr**: assert `"Issue-matched skills (from body scan):"` line when detected skills are present.
- **test_stdout_stays_empty**: assert `capsys.readouterr().out == ""` — piping contract.

Fixture requirements: `tmp_path` with `.mantle/` initialised, `.mantle/config.md` pointing to a vault, vault containing a `python-314.md` skill via `skills.create_skill`, `pyproject.toml` with `[project] requires-python = ">=3.14"`, and an issue file + state.md.