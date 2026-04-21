"""CLI wrapper for model-tier resolution."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mantle.core import project


def run_model_tier(
    *,
    project_dir: Path | None = None,
) -> None:
    """Resolve stage→model mapping and print as JSON.

    Prints a JSON object to stdout (for machine consumption by
    ``build.md``) and a human-readable table to stderr.

    Args:
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    stages = project.load_model_tier(project_dir)
    payload = stages.model_dump()

    print(json.dumps(payload))

    print("=== Resolved model tier ===", file=sys.stderr)
    for stage, model in payload.items():
        print(f"  {stage:<14} → {model}", file=sys.stderr)
