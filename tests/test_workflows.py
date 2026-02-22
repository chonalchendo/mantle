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
        assert wf["permissions"]["id-token"] == "write"

    def test_uses_pypi_publish_action(self):
        wf = _load_workflow("publish.yml")
        steps = wf["jobs"]["publish"]["steps"]
        uses = [s.get("uses", "") for s in steps]
        assert any("pypa/gh-action-pypi-publish" in u for u in uses)
