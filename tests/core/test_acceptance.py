"""Tests for mantle.core.acceptance."""

from __future__ import annotations

import pydantic
import pytest
from inline_snapshot import snapshot

from mantle.core import acceptance
from mantle.core.acceptance import (
    AcceptanceCriterion,
    CriterionNotFoundError,
    DuplicateCriterionIdError,
)

# ── AcceptanceCriterion model ────────────────────────────────────


class TestAcceptanceCriterion:
    def test_acceptance_criterion_is_frozen(self) -> None:
        ac = AcceptanceCriterion(id="ac-01", text="does a thing")

        with pytest.raises(pydantic.ValidationError):
            ac.passes = True  # type: ignore[misc]

    def test_defaults(self) -> None:
        ac = AcceptanceCriterion(id="ac-01", text="does a thing")

        assert ac.passes is False
        assert ac.waived is False
        assert ac.waiver_reason is None


# ── render_ac_section ────────────────────────────────────────────


class TestRenderAcSection:
    def test_render_ac_section_snapshot(self) -> None:
        criteria = (
            AcceptanceCriterion(
                id="ac-01",
                text="Frontmatter supports acceptance_criteria list",
                passes=True,
            ),
            AcceptanceCriterion(
                id="ac-02",
                text="Markdown checkboxes reflect structured list",
                passes=False,
            ),
            AcceptanceCriterion(
                id="ac-03",
                text="Migration CLI backfills existing issues",
                passes=False,
                waived=True,
                waiver_reason="covered by issue 80",
            ),
        )

        rendered = acceptance.render_ac_section(criteria)

        assert rendered == snapshot("""\
## Acceptance criteria

- [x] ac-01: Frontmatter supports acceptance_criteria list
- [ ] ac-02: Markdown checkboxes reflect structured list
- [x] ac-03: Migration CLI backfills existing issues (waived)
""")

    def test_render_empty_shows_placeholder(self) -> None:
        rendered = acceptance.render_ac_section(())

        assert rendered == snapshot("""\
## Acceptance criteria

_None defined._
""")


# ── replace_ac_section ───────────────────────────────────────────


class TestReplaceAcSection:
    def test_replace_ac_section_swaps_existing(self) -> None:
        body = (
            "## Why\n\n"
            "Context.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] Old item one\n"
            "- [ ] Old item two\n\n"
            "## Appendix\n\n"
            "More details.\n"
        )
        rendered = acceptance.render_ac_section(
            (AcceptanceCriterion(id="ac-01", text="New item", passes=True),)
        )

        result = acceptance.replace_ac_section(body, rendered)

        assert "Old item" not in result
        assert "- [x] ac-01: New item" in result
        assert "## Why" in result
        assert "## Appendix" in result

    def test_replace_ac_section_appends_when_absent(self) -> None:
        body = "## Why\n\nContext.\n"
        rendered = acceptance.render_ac_section(
            (AcceptanceCriterion(id="ac-01", text="New item"),)
        )

        result = acceptance.replace_ac_section(body, rendered)

        assert result.startswith("## Why\n\nContext.\n")
        assert "## Acceptance criteria" in result
        assert "- [ ] ac-01: New item" in result


# ── parse_ac_section ─────────────────────────────────────────────


class TestParseAcSection:
    def test_parse_ac_section_assigns_ids_in_order(self) -> None:
        body = (
            "## Why\n\nContext.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] First item\n"
            "- [x] Second item\n"
            "- [ ] Third item\n"
        )

        parsed = acceptance.parse_ac_section(body)

        assert tuple(c.id for c in parsed) == ("ac-01", "ac-02", "ac-03")
        assert parsed[0].text == "First item"
        assert parsed[1].text == "Second item"
        assert parsed[2].text == "Third item"

    def test_parse_ac_section_roundtrip_preserves_ids(self) -> None:
        criteria = (
            AcceptanceCriterion(id="ac-01", text="alpha", passes=True),
            AcceptanceCriterion(id="ac-02", text="beta", passes=False),
        )
        rendered = acceptance.render_ac_section(criteria)

        parsed = acceptance.parse_ac_section(rendered)

        assert tuple(c.id for c in parsed) == ("ac-01", "ac-02")
        assert tuple(c.text for c in parsed) == ("alpha", "beta")

    def test_parse_ac_section_passes_from_checkbox_state(self) -> None:
        body = "## Acceptance criteria\n\n- [x] Done item\n- [ ] Pending item\n"

        parsed = acceptance.parse_ac_section(body)

        assert parsed[0].passes is True
        assert parsed[1].passes is False

    def test_parse_ac_section_returns_empty_when_section_missing(self) -> None:
        body = "## Why\n\nContext only, no AC section.\n"

        assert acceptance.parse_ac_section(body) == ()


# ── flip_criterion ───────────────────────────────────────────────


class TestFlipCriterion:
    def test_flip_criterion_mutates_matching_id(self) -> None:
        criteria = (
            AcceptanceCriterion(id="ac-01", text="alpha", passes=False),
            AcceptanceCriterion(id="ac-02", text="beta", passes=False),
        )

        flipped = acceptance.flip_criterion(criteria, "ac-01", passes=True)

        assert flipped[0].passes is True
        assert flipped[1].passes is False
        # Original tuple untouched (frozen).
        assert criteria[0].passes is False

    def test_flip_criterion_raises_on_missing_id(self) -> None:
        criteria = (AcceptanceCriterion(id="ac-01", text="alpha"),)

        with pytest.raises(CriterionNotFoundError):
            acceptance.flip_criterion(criteria, "ac-99", passes=True)


# ── all_pass_or_waived ───────────────────────────────────────────


class TestAllPassOrWaived:
    def test_all_pass_or_waived_true_on_empty(self) -> None:
        assert acceptance.all_pass_or_waived(()) is True

    def test_all_pass_or_waived_false_when_any_pending(self) -> None:
        criteria = (
            AcceptanceCriterion(id="ac-01", text="a", passes=True),
            AcceptanceCriterion(id="ac-02", text="b", passes=False),
        )

        assert acceptance.all_pass_or_waived(criteria) is False

    def test_all_pass_or_waived_true_when_waived_counts(self) -> None:
        criteria = (
            AcceptanceCriterion(id="ac-01", text="a", passes=True),
            AcceptanceCriterion(
                id="ac-02",
                text="b",
                passes=False,
                waived=True,
                waiver_reason="deferred",
            ),
        )

        assert acceptance.all_pass_or_waived(criteria) is True


# ── assert_unique_ids ────────────────────────────────────────────


class TestAssertUniqueIds:
    def test_assert_unique_ids_raises_on_duplicate(self) -> None:
        criteria = (
            AcceptanceCriterion(id="ac-01", text="alpha"),
            AcceptanceCriterion(id="ac-01", text="dup"),
        )

        with pytest.raises(DuplicateCriterionIdError):
            acceptance.assert_unique_ids(criteria)

    def test_assert_unique_ids_noop_on_unique(self) -> None:
        criteria = (
            AcceptanceCriterion(id="ac-01", text="alpha"),
            AcceptanceCriterion(id="ac-02", text="beta"),
        )

        acceptance.assert_unique_ids(criteria)  # no raise
