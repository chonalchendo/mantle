"""Tests for file hash manifest module."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from mantle.core.manifest import (
    hash_file,
    plan_install,
    record_install,
)

if TYPE_CHECKING:
    from pathlib import Path

_MANIFEST = "mantle-file-manifest.json"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


# ── hash_file ────────────────────────────────────────────────────


class TestHashFile:
    def test_consistent_sha256(self, tmp_path: Path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world")
        expected = _sha256("hello world")
        assert hash_file(f) == expected

    def test_different_content_different_hash(self, tmp_path: Path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("aaa")
        b.write_text("bbb")
        assert hash_file(a) != hash_file(b)


# ── plan_install ─────────────────────────────────────────────────


class TestPlanInstallFirstInstall:
    """First install: no manifest exists."""

    def test_all_files_are_new(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        _write(source / "sub/b.txt", "bbb")
        target.mkdir()

        plan = plan_install(source, target)

        assert plan.new == {"a.txt", "sub/b.txt"}
        assert plan.unchanged == frozenset()
        assert plan.user_modified == frozenset()
        assert plan.source_changed == frozenset()
        assert plan.conflict == frozenset()
        assert plan.removed == frozenset()

    def test_safe_to_write_includes_all(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        target.mkdir()

        plan = plan_install(source, target)

        assert plan.safe_to_write == {"a.txt"}
        assert plan.needs_prompt == frozenset()


class TestPlanInstallReinstall:
    """Re-install: manifest exists from previous install."""

    def _do_first_install(self, source: Path, target: Path) -> None:
        """Helper: plan + copy + record a clean first install."""
        plan = plan_install(source, target)
        for rel in plan.new:
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((source / rel).read_bytes())
        record_install(source, target, plan.new)

    def test_no_changes_all_unchanged(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        target.mkdir()

        self._do_first_install(source, target)
        plan = plan_install(source, target)

        assert plan.unchanged == {"a.txt"}
        assert plan.new == frozenset()

    def test_user_modified_file(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        target.mkdir()

        self._do_first_install(source, target)
        (target / "a.txt").write_text("user edit")
        plan = plan_install(source, target)

        assert plan.user_modified == {"a.txt"}
        assert plan.needs_prompt == {"a.txt"}

    def test_source_changed_file(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "v1")
        target.mkdir()

        self._do_first_install(source, target)
        (source / "a.txt").write_text("v2")
        plan = plan_install(source, target)

        assert plan.source_changed == {"a.txt"}
        assert plan.safe_to_write == {"a.txt"}

    def test_conflict_both_changed(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "v1")
        target.mkdir()

        self._do_first_install(source, target)
        (source / "a.txt").write_text("v2")
        (target / "a.txt").write_text("user edit")
        plan = plan_install(source, target)

        assert plan.conflict == {"a.txt"}
        assert plan.needs_prompt == {"a.txt"}

    def test_new_source_files_detected(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        target.mkdir()

        self._do_first_install(source, target)
        _write(source / "b.txt", "bbb")
        plan = plan_install(source, target)

        assert "b.txt" in plan.new
        assert "a.txt" in plan.unchanged

    def test_removed_source_files_detected(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        _write(source / "b.txt", "bbb")
        target.mkdir()

        self._do_first_install(source, target)
        (source / "b.txt").unlink()
        plan = plan_install(source, target)

        assert plan.removed == {"b.txt"}
        assert "a.txt" in plan.unchanged


class TestPlanInstallEdgeCases:
    def test_empty_source_raises(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        try:
            plan_install(source, target)
            msg = "Expected FileNotFoundError"
            raise AssertionError(msg)
        except FileNotFoundError:
            pass

    def test_missing_source_raises(self, tmp_path: Path):
        source = tmp_path / "nonexistent"
        target = tmp_path / "target"
        target.mkdir()

        try:
            plan_install(source, target)
            msg = "Expected FileNotFoundError"
            raise AssertionError(msg)
        except FileNotFoundError:
            pass

    def test_empty_manifest_treats_all_as_new(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "x.txt", "xxx")
        target.mkdir()

        plan = plan_install(source, target)

        assert plan.new == {"x.txt"}


# ── record_install ───────────────────────────────────────────────


class TestRecordInstall:
    def test_creates_manifest_file(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        target.mkdir()

        record_install(source, target, ["a.txt"])

        assert (target / _MANIFEST).exists()

    def test_round_trip_preserves_state(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        target.mkdir()

        # Copy and record
        (target / "a.txt").write_text("aaa")
        record_install(source, target, ["a.txt"])

        # Plan again — should be unchanged
        plan = plan_install(source, target)
        assert plan.unchanged == {"a.txt"}

    def test_only_records_listed_files(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.txt", "aaa")
        _write(source / "b.txt", "bbb")
        target.mkdir()

        # Record only a.txt (without actually copying it)
        record_install(source, target, ["a.txt"])
        plan = plan_install(source, target)

        # a.txt is in manifest but missing from target → user_modified
        assert "a.txt" in plan.user_modified
        # b.txt was never recorded → new
        assert "b.txt" in plan.new
