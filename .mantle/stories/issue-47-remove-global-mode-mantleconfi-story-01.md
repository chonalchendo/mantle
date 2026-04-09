---
issue: 47
title: Replace config-stub global-mode detection with global directory existence
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a mantle user working across multiple repos at work, I want no `.mantle/` footprint in my project dirs once I've migrated to global storage, so that mantle leaves no trace in repos I don't own and so that git worktrees automatically inherit the same global context with no per-worktree setup.

## Depends On

None — independent (single story for this issue).

## Approach

Two small production edits in `core/`: swap `resolve_mantle_dir`'s `.mantle/config.md` read for a `~/.mantle/projects/<identity>/` directory-existence check, and drop the stub rebuild from `migrate_to_global`. The change is backed by a test migration that rewrites existing global-mode tests to create the global dir via monkeypatched `Path.home()` instead of writing a `.mantle/config.md` stub, and adds a new worktree-scenario test that asserts two directories with the same `project_identity()` resolve to the same global dir.

This follows the shaped approach `dir-existence-as-signal` (see `shaped/issue-47-remove-global-mode-mantleconfi-shaped.md`). The resolver stays in `core/project.py`, the migration stays in `core/migration.py` — no new modules, no cli↔core coupling, no new primitives.

## Implementation

### src/mantle/core/project.py (modify)

Replace `resolve_mantle_dir` (currently lines 178–207):

```python
def resolve_mantle_dir(project_dir: Path) -> Path:
    """Resolve the .mantle/ storage directory for a project.

    Uses the existence of ``~/.mantle/projects/<identity>/`` as the
    global-mode signal — no in-repo marker required.  A git worktree
    created from a migrated project inherits the same global context
    automatically because it shares the same ``project_identity()``.

    This function does **not** create any directories.

    Args:
        project_dir: Root directory of the project.

    Returns:
        Resolved path to the .mantle directory.
    """
    identity = project_identity(project_dir)
    global_dir = pathlib.Path.home() / GLOBAL_MANTLE_ROOT / identity
    if global_dir.exists():
        return global_dir
    return project_dir / MANTLE_DIR
```

Removes the `_read_frontmatter_and_body(config_path)` call and the `FileNotFoundError` guard along the global-detection path. No other changes to this file. `_read_frontmatter_and_body` stays — still used by `read_config` and `update_config`.

### src/mantle/core/migration.py (modify)

`migrate_to_global`:
- Drop the `_update_config_at(target, storage_mode='global')` call (currently line 46). Under the new resolver that field is ignored — dead write.
- Replace the stub-rebuild block under `if remove_local:` (currently lines 48–57) with a plain `shutil.rmtree(source)`:

```python
if remove_local:
    shutil.rmtree(source)
```

- Rewrite the docstring to drop the "leaving a stub config.md" language and explain that the directory's existence at `~/.mantle/projects/<identity>/` is now the signal.

`migrate_to_local`:
- Drop the `_update_config_at(local, storage_mode='local')` call (currently line 92). Same reasoning: dead write.

### tests/core/test_project.py (modify)

- **Delete** `TestResolveMantleDir::test_explicit_local` (currently lines 370–376). It asserts that writing `storage_mode: local` in config.md routes to the local path. Under the new resolver the config field is ignored, so the test is testing a coincidence. `test_default_local` already covers "no global dir → returns local".
- **Rewrite** `TestResolveMantleDir::test_global` (currently lines 378–392) into `test_global_dir_exists_returns_global`:

```python
def test_global_dir_exists_returns_global(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Existence of ~/.mantle/projects/<identity>/ makes resolver return it."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    identity = "fixed-identity-test"
    monkeypatch.setattr(
        "mantle.core.project.project_identity", lambda _pd: identity
    )

    global_dir = fake_home / ".mantle" / "projects" / identity
    global_dir.mkdir(parents=True)

    result = resolve_mantle_dir(tmp_path)
    assert result == global_dir
```

- **Add** a new test in the same class for AC #4 (worktree scenario):

```python
def test_worktree_scenario_shares_global_dir(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two project dirs sharing the same identity resolve to the same global dir."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    shared_identity = "worktree-shared-abc123"
    monkeypatch.setattr(
        "mantle.core.project.project_identity",
        lambda _pd: shared_identity,
    )

    global_dir = fake_home / ".mantle" / "projects" / shared_identity
    global_dir.mkdir(parents=True)

    primary = tmp_path / "primary-repo"
    worktree = tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()

    assert resolve_mantle_dir(primary) == global_dir
    assert resolve_mantle_dir(worktree) == global_dir
```

- Keep `test_default_local` and `test_missing_config` unchanged — both still pass and document the "no global dir → returns local" fallback.

### tests/core/test_migration.py (modify)

- **Delete** `TestMigrateToGlobal::test_leaves_stub` (currently lines 112–135). Stub is no longer left.
- **Delete** `TestMigrateToGlobal::test_updates_config` (currently lines 88–110). It asserts the target config.md contains `storage_mode: global`, which we no longer write. `test_creates_target` already covers content preservation into the global dir.
- **Rewrite** `TestMigrateToGlobal::test_removes_local_contents` (currently lines 137–160) into `test_removes_local_dir_entirely`:

```python
@patch('subprocess.run', side_effect=_mock_subprocess_run)
def test_removes_local_dir_entirely(
    self, _mock: object, tmp_path: Path,
) -> None:
    """Verify local .mantle/ is gone entirely after migration."""
    proj = tmp_path / 'myproject'
    proj.mkdir()
    _create_mantle_dir(proj)
    fake_home = tmp_path / 'home'
    fake_home.mkdir()

    with patch.object(Path, 'home', return_value=fake_home):
        migration.migrate_to_global(proj)

    assert not (proj / '.mantle').exists()
```

- Keep `test_creates_target`, `test_target_exists_raises`, and all `TestMigrateToLocal` / `TestRoundtrip` tests unchanged. The roundtrip test still works: `migrate_to_global` removes local, `migrate_to_local` calls `resolve_mantle_dir(project_dir)` which finds the global dir and uses it as the source — all within the fake home.

### tests/cli/test_storage.py (modify)

- **Rewrite** `TestMigrateStorage::test_migrate_storage_error` (currently lines 150–178): after the first successful migration, `.mantle/` is gone in project_dir (new behaviour). Rebuild it via `_create_project(tmp_path)` (simulating a fresh init in a repo that already has a global-dir match) and call `run_migrate_storage(direction='global')` again — the global target still exists from the first migration, so it must raise FileExistsError internally and SystemExit at the CLI wrapper layer. Assertions unchanged (`"Error" in captured.out`).
- **Rewrite** `TestWhere::test_where_global_mode` (currently lines 211–228): create the global dir under fake home instead of writing a config.md stub with `storage_mode: global`:

```python
def test_where_global_mode(
    self, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _create_project(tmp_path)
    fake_home = tmp_path / 'fakehome'
    fake_home.mkdir()
    monkeypatch.setattr('pathlib.Path.home', lambda: fake_home)

    identity = project.project_identity(tmp_path)
    global_dir = fake_home / '.mantle' / 'projects' / identity
    global_dir.mkdir(parents=True)

    from mantle.cli.storage import run_where
    run_where(project_dir=tmp_path)
    captured = capsys.readouterr()

    prefix = str(fake_home / '.mantle' / 'projects') + '/'
    assert captured.out.strip().startswith(prefix)
```

- **Do not touch** `TestStorage::test_storage_set_global`, `test_storage_set_local`, `test_storage_already_set`, `test_storage_invalid_mode` — these test `run_storage`, which is explicitly out of scope per the shaped issue. They continue to test that the CLI writes `storage_mode` to config.md, which it still does.

### tests/test_global_mode_workflow.py (modify)

- **Rename + rewrite** `test_global_project_local_mantle_is_stub_only` → `test_global_project_local_mantle_is_absent`:

```python
def test_global_project_local_mantle_is_absent(
    global_project: Path,
) -> None:
    '''After migration, the project dir contains no .mantle/ folder at all.'''
    local_mantle = global_project / '.mantle'
    assert not local_mantle.exists()
```

- **Simplify** the `global_project` fixture: drop the dead `project.update_config(project_dir, storage_mode='global')` call. It's a dead write under new semantics and was only needed to make the old resolver's config-read path work.

```python
@pytest.fixture
def global_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    fake_home = tmp_path / 'fakehome'
    fake_home.mkdir()
    monkeypatch.setattr('pathlib.Path.home', lambda: fake_home)

    project_dir = tmp_path / 'workrepo'
    project_dir.mkdir()
    project.init_project(project_dir, project_name='workrepo')
    migration.migrate_to_global(project_dir)

    return project_dir
```

- Keep `test_where_returns_global_path_after_migration` and `test_global_project_state_md_readable_via_resolved_path` unchanged. Under the new resolver they still pass: both call `resolve_mantle_dir(global_project)` which finds the global dir (created by the fixture's `migrate_to_global`) and returns it.

#### Design decisions

- **Use monkeypatched `project_identity` in unit tests instead of mocking `subprocess.run`**: simpler, deterministic, keeps the test focused on the resolver's behaviour rather than the identity-computation plumbing. The identity computation has its own tests in `TestProjectIdentity`.
- **Delete `test_explicit_local` rather than rename**: renaming to "when no global dir exists" would duplicate `test_default_local`. Delete is honest.
- **Delete the dead `_update_config_at` writes from both migration functions**, not just `migrate_to_global`: symmetric cleanup, and leaving dead writes in one direction invites future confusion about whether the field is load-bearing.
- **No backward-compat shim for users with legacy stubs**: stated in the shaped issue's "Does not". Resolver silently prefers global when both exist; users can manually delete the residue.

## Tests

### tests/core/test_project.py (modify)

- **test_global_dir_exists_returns_global** (new, replaces test_global): creates global dir under fake home with monkeypatched `project_identity`, asserts resolver returns it
- **test_worktree_scenario_shares_global_dir** (new, AC #4): two project dirs with monkeypatched identical `project_identity` both resolve to the same global dir
- **test_explicit_local** (delete): obsolete assertion about `storage_mode: local` routing

### tests/core/test_migration.py (modify)

- **test_leaves_stub** (delete): stub no longer left
- **test_updates_config** (delete): `storage_mode: global` no longer written to target
- **test_removes_local_dir_entirely** (new, replaces test_removes_local_contents): asserts `proj/.mantle` does not exist after migration

### tests/cli/test_storage.py (modify)

- **test_migrate_storage_error** (rewrite): rebuilds full `.mantle/` between migrations (instead of stub), expects FileExistsError → SystemExit when global target already exists
- **test_where_global_mode** (rewrite): creates global dir under fake home instead of writing a config.md stub

### tests/test_global_mode_workflow.py (modify)

- **test_global_project_local_mantle_is_absent** (rename + rewrite from test_global_project_local_mantle_is_stub_only): asserts `.mantle/` does not exist in project dir after migration
- **global_project fixture** (simplify): drops the dead `update_config(..., storage_mode='global')` call