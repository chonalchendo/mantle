"""Tests for /mantle:build prompt file."""

from pathlib import Path

COMMANDS_DIR = (
    Path(__file__).resolve().parents[2] / "claude" / "commands" / "mantle"
)
BUILD_PROMPT = COMMANDS_DIR / "build.md"


def test_build_md_contains_transition_implementing():
    """build.md Step 6 section contains transition-issue-implementing command."""
    content = BUILD_PROMPT.read_text()
    assert "transition-issue-implementing" in content


def test_build_md_contains_transition_implemented():
    """build.md Step 6 section contains transition-issue-implemented command."""
    content = BUILD_PROMPT.read_text()
    assert "transition-issue-implemented" in content


def test_build_prompt_references_mantle_model_tier():
    """build.md Step 3 invokes `mantle model-tier` for tier resolution."""
    content = BUILD_PROMPT.read_text()
    assert "mantle model-tier" in content


def test_build_prompt_references_stage_models_placeholder():
    """STAGE_MODELS appears at setup, implement, simplify, and verify spawns."""
    content = BUILD_PROMPT.read_text()
    assert content.count("STAGE_MODELS") >= 4


def test_build_prompt_step3_header_updated():
    """Step 3 header renamed to include model tier."""
    content = BUILD_PROMPT.read_text()
    assert "Step 3 — Load skills and model tier" in content


def test_build_prompt_simplify_and_verify_pass_model():
    """Per-stage STAGE_MODELS references for the four spawn-consuming stages."""
    content = BUILD_PROMPT.read_text()
    assert "STAGE_MODELS.simplify" in content
    assert "STAGE_MODELS.verify" in content
    assert "STAGE_MODELS.implement" in content
    assert "STAGE_MODELS.plan_stories" in content
