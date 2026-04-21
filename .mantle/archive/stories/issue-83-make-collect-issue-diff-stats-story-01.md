---
issue: 83
title: Categorised diff stats — configurable source/test/other buckets
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user adopting the tool on a dbt-layout project, I want `mantle collect-issue-diff-stats` to classify my `models/`, `tests/`, and `macros/` folders correctly, so the build pipeline's mechanical-vs-logic skip heuristic still works on my repo.

## Depends On

None — independent (first and only story for issue 83).

## Approach

Additive extension of the existing `collect_issue_diff_stats` API in `src/mantle/core/simplify.py`: keep today's `DiffStats` aggregate function unchanged, add a new `collect_issue_diff_stats_categorised` function returning per-category stats, and surface both through the existing CLI command as additive key=value output lines. A new optional `diff_paths` frontmatter field in `.mantle/config.md` drives categorisation; when absent (or when config.md itself is missing), defaults to `{source: [src/], test: [tests/]}` so current behaviour is preserved. This follows the Shaped doc's Approach A and respects the cli-design-best-practices \"additive output\" rule.

## Implementation

### src/mantle/core/project.py (modify)

Extend `_ConfigFrontmatter` Pydantic model with one new field:

```python
class _ConfigFrontmatter(pydantic.BaseModel):
    \"\"\"Config.md frontmatter schema (internal).\"\"\"

    personal_vault: str | None = None
    verification_strategy: str | None = None
    auto_push: bool = False
    storage_mode: str | None = None
    hooks_env: dict[str, str] | None = None
    diff_paths: dict[str, list[str]] | None = None
    tags: tuple[str, ...] = (\"type/config\",)
```

Keeps the existing `type | None = None` convention used by sibling fields. No migration needed — `read_config` already returns a plain dict, so a missing key becomes `None`.

### src/mantle/core/simplify.py (modify)

Add constants and two new public functions; keep existing `collect_issue_diff_stats` signature unchanged but re-implement it as a thin wrapper.

```python
from mantle.core import issues, project  # add 'project' import

DEFAULT_DIFF_PATHS: dict[str, tuple[str, ...]] = {
    \"source\": (\"src/\",),
    \"test\": (\"tests/\",),
}
PRIMARY_CATEGORIES: frozenset[str] = frozenset({\"source\", \"test\"})


def load_diff_paths(
    project_root: Path,
) -> tuple[dict[str, tuple[str, ...]], bool]:
    \"\"\"Load diff_paths from .mantle/config.md or return defaults.

    When ``.mantle/config.md`` is missing, the file cannot be read, or the
    ``diff_paths`` field is absent/empty, returns ``(DEFAULT_DIFF_PATHS, False)``.

    Returns:
        (mapping, is_custom). is_custom is True when the config field
        is present (enables the \"other\" bucket in categorised stats).
    \"\"\"
    try:
        config = project.read_config(project_root)
    except FileNotFoundError:
        return DEFAULT_DIFF_PATHS, False
    raw = config.get(\"diff_paths\")
    if not raw:
        return DEFAULT_DIFF_PATHS, False
    return {k: tuple(v) for k, v in raw.items()}, True


def collect_issue_diff_stats_categorised(
    project_root: Path,
    issue: int,
) -> dict[str, DiffStats]:
    \"\"\"Per-category diff stats for an issue.

    Categories come from ``.mantle/config.md`` ``diff_paths`` frontmatter,
    or default to ``source=src/``, ``test=tests/``. When ``diff_paths`` is
    explicitly configured, files matching no configured category are
    reported under an ``\"other\"`` key. When defaults are in use, the
    ``\"other\"`` key is omitted (matches legacy behaviour).

    File classification uses first-matching-prefix semantics in declared
    category order; a file matches a prefix when its path string starts
    with that prefix.

    Args:
        project_root: Directory containing .mantle/.
        issue: Issue number to collect diff stats for.

    Returns:
        Mapping from category name to DiffStats. All declared categories
        are always present (with zero stats if empty). The ``\"other\"``
        key appears only when ``diff_paths`` is explicitly configured.

    Raises:
        FileNotFoundError: If the issue file does not exist.
    \"\"\"
    _verify_issue_exists(project_root, issue)
    paths, is_custom = load_diff_paths(project_root)
    commit_hashes = _grep_issue_commits(project_root, issue)

    categories: dict[str, DiffStats] = {
        name: DiffStats(0, 0, 0, 0) for name in paths
    }
    if is_custom:
        categories[\"other\"] = DiffStats(0, 0, 0, 0)

    if not commit_hashes:
        return categories

    first_commit = commit_hashes[-1]
    last_commit = commit_hashes[0]

    numstat = subprocess.run(
        [\"git\", \"diff\", \"--numstat\", f\"{first_commit}^..{last_commit}\"],
        capture_output=True,
        text=True,
        check=True,
        cwd=project_root,
    )

    for line in numstat.stdout.splitlines():
        parts = line.split(\"\\t\", 2)
        if len(parts) != 3:
            continue
        added_s, removed_s, path = parts
        # Binary files show '-' for counts; treat as zero.
        added = int(added_s) if added_s.isdigit() else 0
        removed = int(removed_s) if removed_s.isdigit() else 0
        category = _classify_path(path, paths, is_custom)
        if category is None:
            continue
        prev = categories[category]
        categories[category] = DiffStats(
            files=prev.files + 1,
            lines_added=prev.lines_added + added,
            lines_removed=prev.lines_removed + removed,
            lines_changed=prev.lines_changed + added + removed,
        )

    return categories


def _classify_path(
    path: str,
    paths: dict[str, tuple[str, ...]],
    is_custom: bool,
) -> str | None:
    \"\"\"Return the category a path belongs to, or None to drop it.

    First-matching-prefix in declared order. When no category matches:
    returns ``\"other\"`` if ``is_custom``, else None (silently dropped).
    \"\"\"
    for name, prefixes in paths.items():
        if any(path.startswith(p) for p in prefixes):
            return name
    return \"other\" if is_custom else None


def collect_issue_diff_stats(
    project_root: Path,
    issue: int,
) -> DiffStats:
    \"\"\"Aggregate diff stats for an issue, scoped to source+test categories.

    Thin wrapper over :func:`collect_issue_diff_stats_categorised` that
    sums DiffStats for the ``source`` and ``test`` categories (the
    :data:`PRIMARY_CATEGORIES` set). Matches the legacy contract used by
    ``build.md`` Step 7's simplify-skip heuristic.
    \"\"\"
    categories = collect_issue_diff_stats_categorised(project_root, issue)
    files = lines_added = lines_removed = 0
    for name in PRIMARY_CATEGORIES:
        stats = categories.get(name)
        if stats is None:
            continue
        files += stats.files
        lines_added += stats.lines_added
        lines_removed += stats.lines_removed
    return DiffStats(
        files=files,
        lines_added=lines_added,
        lines_removed=lines_removed,
        lines_changed=lines_added + lines_removed,
    )
```

Drop the old `_SHORTSTAT_RE` regex — it is no longer used. `--numstat` gives a per-file tab-separated format (`added\\tremoved\\tpath`) that is easier to categorise.

#### Design decisions

- **`dict[str, tuple[str, ...]]` for `DEFAULT_DIFF_PATHS`**: tuple is hashable/immutable and matches the module's existing `tuple[str, ...]` return type convention (see `SUBDIRS` in `project.py`).
- **`PRIMARY_CATEGORIES = frozenset({\"source\", \"test\"})`**: encodes the convention that `source` and `test` are the two category keys whose sum feeds the legacy aggregate. Future categories (`docs`, `models`, `macros`) never contribute to `files=`/`lines_changed=` aggregate — this keeps the build.md Step 7 skip heuristic semantically stable.
- **`load_diff_paths` swallows `FileNotFoundError` for config.md**: the function is called from diff-stats collection where a missing config.md should not crash the build; defaults apply. (The issue-existence check in `collect_issue_diff_stats_categorised` still raises `FileNotFoundError` on a missing issue — that's the caller's contract.)
- **`first-matching-prefix` classification**: simple, predictable, matches git pathspec semantics users already understand. User controls precedence via config key declaration order (Python dict insertion order).
- **Switch from `--shortstat` to `--numstat`**: we need per-file line counts to bucket by category. `--numstat` gives them natively; drops the regex parser entirely.
- **Always include declared categories (even if empty)**: predictable output shape for downstream consumers (CLI and tests).
- **`\"other\"` only when `is_custom`**: satisfies ac-03 (\"behaviour matches today\" = no `other` bucket emitted under defaults).
- **Binary files (`-\\t-\\tpath` in numstat)**: counted as one file with zero lines (matches `--shortstat`'s behaviour).

### src/mantle/cli/simplify.py (modify)

Replace `run_collect_issue_diff_stats` body with:

```python
def run_collect_issue_diff_stats(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    \"\"\"Print per-category and aggregate diff stats as key=value lines.\"\"\"
    if project_dir is None:
        project_dir = Path.cwd()

    categories = simplify.collect_issue_diff_stats_categorised(
        project_dir, issue
    )

    # Legacy aggregate lines — sum of primary categories only.
    aggregate_files = aggregate_added = aggregate_removed = 0
    for name in simplify.PRIMARY_CATEGORIES:
        stats = categories.get(name)
        if stats is None:
            continue
        aggregate_files += stats.files
        aggregate_added += stats.lines_added
        aggregate_removed += stats.lines_removed
    console.print(f\"files={aggregate_files}\")
    console.print(f\"lines_added={aggregate_added}\")
    console.print(f\"lines_removed={aggregate_removed}\")
    console.print(f\"lines_changed={aggregate_added + aggregate_removed}\")

    # Per-category breakdown, in declaration order.
    for name, stats in categories.items():
        console.print(f\"{name}_files={stats.files}\")
        console.print(f\"{name}_lines_added={stats.lines_added}\")
        console.print(f\"{name}_lines_removed={stats.lines_removed}\")
        console.print(f\"{name}_lines_changed={stats.lines_changed}\")
```

Keeps legacy `files=`/`lines_added=`/`lines_removed=`/`lines_changed=` lines unchanged in meaning (primary-category sum). Adds per-category lines after them.

## Tests

### tests/core/test_simplify.py (modify)

The existing `TestCollectIssueDiffStats` class (lines 180-355) must pass unchanged — those tests exercise the legacy aggregate wrapper and create a tmp_path repo *without* writing a `config.md`. `load_diff_paths` catches `FileNotFoundError` so this keeps working. Add a small helper near the top of the file:

```python
def _write_config_md(project_root: Path, diff_paths: dict[str, list[str]]) -> None:
    \"\"\"Write a minimal .mantle/config.md with a diff_paths frontmatter block.\"\"\"
    import yaml
    config_path = project_root / \".mantle\" / \"config.md\"
    yaml_str = yaml.dump(
        {\"diff_paths\": diff_paths},
        default_flow_style=False,
        sort_keys=False,
    )
    config_path.write_text(f\"---\\n{yaml_str}---\\n\\n\", encoding=\"utf-8\")
```

Then add two new classes below `TestCollectIssueDiffStats`:

- **TestLoadDiffPaths::test_defaults_when_config_missing**: `_init_git_repo` creates `.mantle/` but no `config.md`; assert `load_diff_paths(project)` returns `(DEFAULT_DIFF_PATHS, False)`.
- **TestLoadDiffPaths::test_defaults_when_field_absent**: write a `.mantle/config.md` with empty frontmatter; assert `(DEFAULT_DIFF_PATHS, False)`.
- **TestLoadDiffPaths::test_returns_custom_when_field_present**: write `_write_config_md(project, {\"source\": [\"models/\"], \"test\": [\"tests/\"], \"macros\": [\"macros/\"]})`; assert `(mapping, True)` and values are tuple-coerced.
- **TestCollectIssueDiffStatsCategorised::test_defaults_no_other_bucket**: no config.md; single `src/foo.py` commit; asserts returned dict has `source` and `test` keys only, no `other` key.
- **TestCollectIssueDiffStatsCategorised::test_defaults_drop_unclassified**: no config.md; commit touches `src/foo.py` and `claude/bar.md`; asserts `source.files == 1`, no `other` key, claude file dropped (matches legacy behaviour).
- **TestCollectIssueDiffStatsCategorised::test_custom_config_adds_other_bucket**: `_write_config_md(project, {\"source\": [\"src/\"], \"test\": [\"tests/\"]})` (explicit even if same as default); commit touches `src/x.py` and `docs/y.md`; asserts `other.files == 1` because `is_custom == True`.
- **TestCollectIssueDiffStatsCategorised::test_dbt_style_fixture**: `_write_config_md(project, {\"source\": [\"models/\"], \"test\": [\"tests/\"], \"macros\": [\"macros/\"]})`; commits add `models/stg_a.sql` (3 lines), `tests/generic_b.sql` (1 line), `macros/util.sql` (5 lines), and `.mantle/x.md` (2 lines); asserts `models.files == 1` with `lines_changed == 3`, `test.files == 1` with `lines_changed == 1`, `macros.files == 1` with `lines_changed == 5`, and `other.files == 1` (the `.mantle/x.md` file). Satisfies ac-04. Note: the key is `source` in the test, not `models` — the category NAME is chosen by the user; for dbt we pick `source: [models/]` to keep the PRIMARY_CATEGORIES aggregate semantically meaningful.
- **TestCollectIssueDiffStatsCategorised::test_first_match_wins**: `_write_config_md(project, {\"source\": [\"src/\"], \"vendor\": [\"src/vendor/\"]})`; commit touches `src/vendor/a.py`; asserts file is counted under `source` (declaration order), not `vendor`.
- **TestCollectIssueDiffStatsCategorised::test_empty_categories_always_present**: no commits matching the issue; asserts returned dict has every declared category with `DiffStats(0, 0, 0, 0)` and no `other` key (defaults mode).
- **TestCollectIssueDiffStats::test_aggregate_sums_only_primary_categories**: `_write_config_md(project, {\"source\": [\"src/\"], \"test\": [\"tests/\"], \"docs\": [\"docs/\"]})`; commits touch `src/a.py` (4 lines), `tests/t.py` (2 lines), and `docs/d.md` (10 lines); asserts the wrapper `collect_issue_diff_stats` returns aggregate `files=2, lines_changed=6` (docs excluded even though categorised).

Reuse the existing `_init_git_repo`, `_write_issue_file`, `_commit_file`, `_commit_content` helpers.

### tests/cli/test_simplify.py (modify)

Replace the existing `TestCollectIssueDiffStatsCLI::test_run_prints_key_value_lines` with a monkeypatched categorised fake, and add a second case for the custom-config output:

- **TestCollectIssueDiffStatsCLI::test_prints_aggregate_and_per_category_lines**: monkeypatch `core_simplify.collect_issue_diff_stats_categorised` to return `{\"source\": DiffStats(2, 30, 5, 35), \"test\": DiffStats(1, 12, 0, 12)}`; assert stdout contains `files=3`, `lines_added=42`, `lines_removed=5`, `lines_changed=47`, `source_files=2`, `source_lines_added=30`, `test_files=1`, `test_lines_changed=12`. No `other_*` lines.
- **TestCollectIssueDiffStatsCLI::test_prints_other_bucket_when_configured**: monkeypatched return includes an `\"other\"` entry with `DiffStats(1, 4, 0, 4)`; assert `other_files=1` and `other_lines_changed=4` appear, while `files=` aggregate still excludes other.

Use `capsys.readouterr().out` to capture; keep assertion style consistent with the current file (`assert \"files=3\" in out`).

#### Design decisions

- **Monkeypatch at the categorised function**: the CLI now consumes only `collect_issue_diff_stats_categorised`; patching that boundary isolates the CLI test from git mechanics.
- **Keep substring-in-stdout assertions rather than inline_snapshot**: CLAUDE.md recommends inline_snapshot for \"exact-string CLI output\", but these tests intentionally assert a small set of keys without pinning order or full content — substring asserts match the existing test style in this file and survive additive output changes in future stories.