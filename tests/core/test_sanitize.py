"""Tests for mantle.core.sanitize."""

from __future__ import annotations

from mantle.core.sanitize import strip_analysis_blocks


class TestStripAnalysisBlocks:
    """Tests for strip_analysis_blocks()."""

    def test_removes_analysis_block(self) -> None:
        content = (
            "Before.\n\n"
            "<analysis>\nInternal thinking here.\n</analysis>\n\n"
            "After."
        )

        result = strip_analysis_blocks(content)

        assert "<analysis>" not in result
        assert "Internal thinking" not in result
        assert "Before." in result
        assert "After." in result

    def test_removes_multiple_blocks(self) -> None:
        content = (
            "<analysis>First.</analysis>\n"
            "Middle.\n"
            "<analysis>Second.</analysis>\n"
            "End."
        )

        result = strip_analysis_blocks(content)

        assert "First." not in result
        assert "Second." not in result
        assert "Middle." in result
        assert "End." in result

    def test_preserves_content_without_blocks(self) -> None:
        content = "No analysis blocks here.\n\nJust normal content."

        result = strip_analysis_blocks(content)

        assert result == content.strip()

    def test_handles_multiline_analysis(self) -> None:
        content = (
            "Before.\n\n"
            "<analysis>\n"
            "- Point 1\n"
            "- Point 2\n"
            "- Point 3\n"
            "</analysis>\n\n"
            "After."
        )

        result = strip_analysis_blocks(content)

        assert "Point 1" not in result
        assert "Before." in result
        assert "After." in result

    def test_collapses_extra_blank_lines(self) -> None:
        content = "Before.\n\n\n<analysis>X</analysis>\n\n\nAfter."

        result = strip_analysis_blocks(content)

        assert "\n\n\n" not in result

    def test_empty_string(self) -> None:
        assert strip_analysis_blocks("") == ""

    def test_only_analysis_block(self) -> None:
        content = "<analysis>All scratchpad.</analysis>"

        result = strip_analysis_blocks(content)

        assert result == ""
