---
issue: 35
title: CLI scout wiring — save-scout subcommand
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer, I want to save scout reports via the mantle CLI, so that prompt orchestrators can persist analysis results through a standard CLI interface.

## Depends On

Story 1 — needs core/scout.py module.

## Approach

Follows the thin CLI wiring pattern used by cli/brainstorm.py. Creates a cli/scout.py with a run_save_scout function, then registers save-scout as a subcommand in cli/main.py. The CLI function calls core/scout.py and prints a rich confirmation.

## Implementation

### src/mantle/cli/scout.py (new file)

Create thin CLI wiring following cli/brainstorm.py pattern:

**run_save_scout function:**
- Parameters: repo_url (str), repo_name (str), dimensions (list[str]), content (str), project_dir (Path | None = None)
- Calls scout.save_scout(project_dir, content, repo_url=repo_url, repo_name=repo_name, dimensions=tuple(dimensions))
- Catches ValueError and prints error with rich, raises SystemExit(1)
- Prints confirmation: repo_name, date, author, dimensions count, saved filename
- Suggests next step: "/mantle:query to search scout findings"

**Imports:**
- from mantle.core import scout
- from rich.console import Console
- from pathlib import Path

### src/mantle/cli/main.py (modify)

1. Add import: from mantle.cli import scout (add to existing import block, alphabetical)
2. Add save-scout command registration:

```python
@app.command(name="save-scout")
def save_scout_command(
    repo_url: Annotated[str, Parameter(name="--repo-url", help="URL of the analyzed repository.")],
    repo_name: Annotated[str, Parameter(name="--repo-name", help="Short name of the repository.")],
    dimensions: Annotated[list[str], Parameter(name="--dimensions", help="Analysis dimensions covered.")],
    content: Annotated[str, Parameter(name="--content", help="Full scout report content.")],
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory. Defaults to cwd.")] = None,
) -> None:
    """Save a scout report to .mantle/scouts/."""
    scout.run_save_scout(
        repo_url=repo_url,
        repo_name=repo_name,
        dimensions=dimensions,
        content=content,
        project_dir=path,
    )
```

#### Design decisions

- **dimensions as list[str] in CLI, tuple in core**: cyclopts handles list parameters via repeated --dimensions flags. Core converts to tuple for immutability.
- **No list-scouts or load-scout CLI commands yet**: YAGNI — the prompt reads files directly. Add CLI wrappers when needed.

## Tests

### tests/cli/test_scout.py (new file)

- **test_run_save_scout_success**: calls run_save_scout with valid args, verifies file created and output printed
- **test_run_save_scout_prints_confirmation**: captures console output, checks repo_name and dimensions count appear
- **test_run_save_scout_defaults_to_cwd**: project_dir=None uses Path.cwd()

Fixture: tmp_path with .mantle/state.md pre-created. Mock state.resolve_git_identity.