"""Tests for GitHub Actions workflow files."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _load_workflow(name: str) -> dict:
    path = WORKFLOWS / name
    assert path.is_file(), f"{name} does not exist"
    return yaml.safe_load(path.read_text())


class TestCIWorkflow:
    def test_exists_and_valid_yaml(self):
        _load_workflow("ci.yml")

    def test_references_just_ci(self):
        wf = _load_workflow("ci.yml")
        steps = wf["jobs"]["check"]["steps"]
        run_steps = [s.get("run", "") for s in steps]
        assert any("just ci" in r for r in run_steps)

    def test_uses_setup_uv_with_cache(self):
        wf = _load_workflow("ci.yml")
        steps = wf["jobs"]["check"]["steps"]
        uv_steps = [
            s for s in steps if "astral-sh/setup-uv" in s.get("uses", "")
        ]
        assert len(uv_steps) == 1
        assert uv_steps[0]["with"]["enable-cache"] is True

    def test_matrix_includes_python_314(self):
        wf = _load_workflow("ci.yml")
        versions = wf["jobs"]["check"]["strategy"]["matrix"]["python-version"]
        assert "3.14" in versions


class TestPublishWorkflow:
    def test_exists_and_valid_yaml(self):
        _load_workflow("publish.yml")

    def test_triggers_on_version_tags(self):
        wf = _load_workflow("publish.yml")
        # YAML parses bare `on` as boolean True
        assert "v*" in wf[True]["push"]["tags"]

    def test_has_id_token_write_permission(self):
        wf = _load_workflow("publish.yml")
        perms = wf["jobs"]["publish"]["permissions"]
        assert perms["id-token"] == "write"

    def test_uses_uv_publish(self):
        wf = _load_workflow("publish.yml")
        steps = wf["jobs"]["publish"]["steps"]
        runs = [s.get("run", "") for s in steps]
        assert any("uv publish" in r for r in runs)


def test_implement_md_references_build_telemetry():
    """implement.md must wire in build-start and build-finish telemetry."""
    path = REPO_ROOT / "claude" / "commands" / "mantle" / "implement.md"
    text = path.read_text(encoding="utf-8")
    assert "mantle build-start --issue" in text
    assert "mantle build-finish --issue" in text


def test_build_md_fast_path_cannot_skip_verify():
    """Regression: build.md fast-path must not short-circuit Step 8 (Verify)."""
    path = REPO_ROOT / "claude" / "commands" / "mantle" / "build.md"
    text = path.read_text(encoding="utf-8")
    # Fast-path branch must exist.
    assert "Fast-path" in text or "fast-path" in text
    # Step 8 (Verify) header must appear exactly once — never inside a
    # fast-path skip block.
    assert text.count("## Step 8 — Verify") == 1
    # Fast-path branch must explicitly state Step 8 still runs.
    fast_path_note = "Step 8 (Verify) runs regardless"
    assert fast_path_note in text, (
        "Fast-path branch must contain the verbatim note: "
        f"{fast_path_note!r} — protects Iron Law #2 (no skipping verification)."
    )
