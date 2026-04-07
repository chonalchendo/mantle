"""Tests for mantle.core.freshness."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.freshness import (
    age_days,
    age_label,
    freshness_caveat,
)


def _set_mtime_days_ago(path: Path, days: int) -> None:
    """Set file mtime to N days ago."""
    t = time.time() - (days * 86_400)
    os.utime(path, (t, t))


class TestAgeDays:
    """Tests for age_days()."""

    def test_today(self, tmp_path: Path) -> None:
        f = tmp_path / "fresh.md"
        f.write_text("content")

        assert age_days(f) == 0

    def test_yesterday(self, tmp_path: Path) -> None:
        f = tmp_path / "old.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 1)

        assert age_days(f) == 1

    def test_many_days(self, tmp_path: Path) -> None:
        f = tmp_path / "ancient.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 30)

        assert age_days(f) == 30


class TestAgeLabel:
    """Tests for age_label()."""

    def test_today(self, tmp_path: Path) -> None:
        f = tmp_path / "fresh.md"
        f.write_text("content")

        assert age_label(f) == "today"

    def test_yesterday(self, tmp_path: Path) -> None:
        f = tmp_path / "old.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 1)

        assert age_label(f) == "yesterday"

    def test_plural_days(self, tmp_path: Path) -> None:
        f = tmp_path / "old.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 5)

        assert age_label(f) == "5 days ago"


class TestFreshnessCaveat:
    """Tests for freshness_caveat()."""

    def test_fresh_file_no_caveat(self, tmp_path: Path) -> None:
        f = tmp_path / "fresh.md"
        f.write_text("content")

        assert freshness_caveat(f) == ""

    def test_yesterday_no_caveat(self, tmp_path: Path) -> None:
        f = tmp_path / "yesterday.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 1)

        assert freshness_caveat(f) == ""

    def test_two_days_has_caveat(self, tmp_path: Path) -> None:
        f = tmp_path / "stale.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 2)

        result = freshness_caveat(f)

        assert "2 days ago" in result
        assert "Verify" in result

    def test_custom_threshold(self, tmp_path: Path) -> None:
        f = tmp_path / "stale.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 5)

        assert freshness_caveat(f, threshold_days=7) == ""
        assert freshness_caveat(f, threshold_days=3) != ""

    def test_old_file_mentions_age(self, tmp_path: Path) -> None:
        f = tmp_path / "ancient.md"
        f.write_text("content")
        _set_mtime_days_ago(f, 47)

        result = freshness_caveat(f)

        assert "47 days ago" in result
