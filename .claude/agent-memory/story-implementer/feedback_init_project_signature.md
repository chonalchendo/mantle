---
name: init_project signature
description: project.init_project requires a project_name second arg, not just tmp_path
type: feedback
---

`project.init_project(tmp_path, project_name)` takes two positional args — the story spec skeleton sometimes shows `init_project(tmp_path)` which would TypeError.

**Why:** Verified by reading `src/mantle/core/project.py` — signature is `def init_project(project_dir: Path, project_name: str) -> Path`. Used throughout `tests/core/test_project.py` as `init_project(tmp_path, "test-project")`.

**How to apply:** When a story gives a test skeleton calling `project.init_project(tmp_path)` or `init_project(tmp_path)`, add a project-name string argument (any non-empty string, conventionally "test-project"). Applies to issue 56 hook tests and likely any future story that scaffolds `.mantle/` in `tmp_path`.
