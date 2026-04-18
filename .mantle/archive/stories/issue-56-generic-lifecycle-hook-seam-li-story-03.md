---
issue: 56
title: Ship example hook scripts (linear/jira/slack) + show-hook-example CLI + README
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a mantle user who wants to integrate with Linear, Jira, or Slack, I want
to run `mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh`
to get a working starter script with documented setup (install, auth, env
vars), and I want the README to point me at the hook authoring convention,
so that I can stand up an integration in minutes without reading source
code.

## Depends On

Story 01 (the hook contract must exist so scripts can rely on positional
args and env vars) — story 02 is not a hard dep but makes end-to-end
manual testing possible.

## Approach

Ship three reference shell scripts as **package data** so they survive a
`uv tool install mantle-ai`:

```
src/mantle/assets/__init__.py              (empty — makes it a subpackage)
src/mantle/assets/hook_examples/__init__.py (empty)
src/mantle/assets/hook_examples/linear.sh
src/mantle/assets/hook_examples/jira.sh
src/mantle/assets/hook_examples/slack.sh
```

Each script has a header comment block documenting: install CLI,
authenticate, required env vars, and a suggested event binding. The script
bodies use the positional args / env vars contract from story 01.

Add a new CLI command `mantle show-hook-example NAME` that prints the named
script's contents to stdout. Users redirect the output into their
`<mantle-dir>/hooks/` directory themselves — mantle does not prescribe
which event the script should bind to (the header comment suggests one).

Add a **"Lifecycle hooks"** section to `README.md` documenting the
authoring convention: hook script path pattern, positional args, env
passthrough, failure semantics, and a quick-start using `show-hook-example`.

## Implementation

### `src/mantle/assets/__init__.py` (new, empty)

Single empty file so `src.mantle.assets` is a package.

### `src/mantle/assets/hook_examples/__init__.py` (new, empty)

Same — empty. Makes scripts accessible via `importlib.resources`.

### `src/mantle/assets/hook_examples/linear.sh` (new)

```bash
#!/usr/bin/env bash
# Mantle lifecycle hook — Linear integration.
#
# SETUP
# -----
# 1. Create a Linear API key: https://linear.app/settings/api
# 2. Add to your .mantle/config.md frontmatter:
#
#    hooks_env:
#      LINEAR_API_KEY: lin_api_xxx
#      LINEAR_TEAM_ID: team-uuid
#
# 3. Copy this script and bind it to the event you care about, e.g.:
#
#      mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh
#      chmod +x .mantle/hooks/on-issue-shaped.sh
#
# Suggested binding: on-issue-shaped.sh (creates/updates a Linear ticket
# when you finish shaping).
#
# CONTRACT (from mantle)
# ----------------------
#   $1 = issue number
#   $2 = new status (e.g. "shaped", "implementing", "verified", "approved")
#   $3 = issue title
#
# Env: LINEAR_API_KEY, LINEAR_TEAM_ID (from hooks_env in config.md).

set -euo pipefail

ISSUE_NUMBER="$1"
NEW_STATUS="$2"
ISSUE_TITLE="$3"

: "${LINEAR_API_KEY:?LINEAR_API_KEY must be set via hooks_env in config.md}"
: "${LINEAR_TEAM_ID:?LINEAR_TEAM_ID must be set via hooks_env in config.md}"

# GraphQL mutation: create an issue in the configured team.
curl -sS -X POST https://api.linear.app/graphql \
  -H "Authorization: ${LINEAR_API_KEY}" \
  -H "Content-Type: application/json" \
  --data @- <<EOF
{
  "query": "mutation IssueCreate(\$input: IssueCreateInput!) { issueCreate(input: \$input) { success issue { id identifier } } }",
  "variables": {
    "input": {
      "teamId": "${LINEAR_TEAM_ID}",
      "title": "[mantle #${ISSUE_NUMBER}] ${ISSUE_TITLE}",
      "description": "Mantle status: ${NEW_STATUS}"
    }
  }
}
EOF
```

### `src/mantle/assets/hook_examples/jira.sh` (new)

```bash
#!/usr/bin/env bash
# Mantle lifecycle hook — Jira integration via Atlassian CLI (acli).
#
# SETUP
# -----
# 1. Install acli: https://developer.atlassian.com/cloud/acli/
# 2. Authenticate once: `acli jira auth login`
#    (acli stores tokens in your OS keychain — mantle never sees them.)
# 3. Add to your .mantle/config.md frontmatter:
#
#    hooks_env:
#      JIRA_PROJECT_KEY: PLAT
#
# 4. Bind to an event:
#
#      mantle show-hook-example jira > .mantle/hooks/on-issue-shaped.sh
#      chmod +x .mantle/hooks/on-issue-shaped.sh
#
# Suggested binding: on-issue-shaped.sh.
#
# CONTRACT (from mantle)
# ----------------------
#   $1 = issue number
#   $2 = new status
#   $3 = issue title
#
# Env: JIRA_PROJECT_KEY (from hooks_env in config.md).

set -euo pipefail

ISSUE_NUMBER="$1"
NEW_STATUS="$2"
ISSUE_TITLE="$3"

: "${JIRA_PROJECT_KEY:?JIRA_PROJECT_KEY must be set via hooks_env in config.md}"

# Create or update a Jira work item for this mantle issue.
acli jira work-item create \
  --project "${JIRA_PROJECT_KEY}" \
  --type Task \
  --summary "[mantle #${ISSUE_NUMBER}] ${ISSUE_TITLE}" \
  --description "Mantle status: ${NEW_STATUS}"
```

### `src/mantle/assets/hook_examples/slack.sh` (new)

```bash
#!/usr/bin/env bash
# Mantle lifecycle hook — Slack incoming webhook notification.
#
# SETUP
# -----
# 1. Create a Slack incoming webhook:
#    https://api.slack.com/messaging/webhooks
# 2. Add to your .mantle/config.md frontmatter:
#
#    hooks_env:
#      SLACK_WEBHOOK_URL: https://hooks.slack.com/services/XXX/YYY/ZZZ
#
# 3. Bind to whichever events you want visibility on, e.g.:
#
#      mantle show-hook-example slack > .mantle/hooks/on-issue-review-approved.sh
#      chmod +x .mantle/hooks/on-issue-review-approved.sh
#
# Suggested binding: on-issue-review-approved.sh.
#
# CONTRACT (from mantle)
# ----------------------
#   $1 = issue number
#   $2 = new status
#   $3 = issue title
#
# Env: SLACK_WEBHOOK_URL (from hooks_env in config.md).

set -euo pipefail

ISSUE_NUMBER="$1"
NEW_STATUS="$2"
ISSUE_TITLE="$3"

: "${SLACK_WEBHOOK_URL:?SLACK_WEBHOOK_URL must be set via hooks_env in config.md}"

curl -sS -X POST "${SLACK_WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  --data "$(printf '{"text":"*Mantle issue #%s* (%s) — %s"}' \
    "${ISSUE_NUMBER}" "${NEW_STATUS}" "${ISSUE_TITLE}")"
```

### `src/mantle/cli/hooks.py` (new)

```python
"""CLI wrappers for lifecycle hook examples."""

from __future__ import annotations

import sys
from importlib import resources

from rich.console import Console

console = Console()

_EXAMPLES_PACKAGE = "mantle.assets.hook_examples"


def run_show_hook_example(*, name: str) -> None:
    """Print a shipped example hook script to stdout.

    Args:
        name: Example name (e.g. "linear", "jira", "slack").

    Raises:
        SystemExit: If the named example does not exist.
    """
    filename = f"{name}.sh"
    try:
        traversable = resources.files(_EXAMPLES_PACKAGE) / filename
        content = traversable.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        console.print(
            f"[red]No hook example named '{name}'. "
            "Available: linear, jira, slack.[/red]",
            highlight=False,
        )
        sys.exit(1)
    sys.stdout.write(content)
```

Actually — reading a missing package file via `importlib.resources` raises
`FileNotFoundError` only on some versions; on others it may raise
`ValueError` or return a non-readable path. Safer: enumerate names first,
then read. Prefer this pattern:

```python
_AVAILABLE = ("linear", "jira", "slack")


def run_show_hook_example(*, name: str) -> None:
    if name not in _AVAILABLE:
        console.print(
            f"[red]No hook example named '{name}'. "
            f"Available: {', '.join(_AVAILABLE)}.[/red]",
            highlight=False,
        )
        sys.exit(1)
    content = (resources.files(_EXAMPLES_PACKAGE) / f"{name}.sh").read_text(
        encoding="utf-8",
    )
    sys.stdout.write(content)
```

### `src/mantle/cli/main.py` (modify)

Import the new wrapper at the top alongside existing `from mantle.cli import
... hooks ...`:

```python
from mantle.cli import (
    ...,
    hooks,
    ...,
)
```

Then add a new command **in the "Setup & plumbing" group** (use
`GROUPS["setup"]` — check existing commands in that group like `compile`,
`where`, `init` for the exact key):

```python
@app.command(name="show-hook-example", group=GROUPS["setup"])
def show_hook_example_command(
    name: Annotated[
        str,
        Parameter(
            help="Example name: linear, jira, or slack.",
        ),
    ],
) -> None:
    """Print a shipped lifecycle hook example to stdout.

    Usage: mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh
    """
    hooks.run_show_hook_example(name=name)
```

### `pyproject.toml` (modify if needed)

Verify that the build backend already includes `*.sh` under
`src/mantle/assets/`. This project likely uses Hatch — check the existing
`[tool.hatch.build.targets.wheel]` section. If the package discovery is
already automatic under `src/mantle/`, the new files ship for free. If not,
add:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/mantle"]
# Include non-Python assets shipped with the package
include = ["src/mantle/assets/**/*"]
```

The implementer should:
1. Read the existing `pyproject.toml` section for build config.
2. Run `uv build --wheel` and `unzip -l dist/mantle_ai-*.whl | grep hook_examples`
   locally to confirm the `.sh` files are in the wheel.
3. Only add explicit `include` rules if the check shows the scripts missing.

### `README.md` (modify)

Add a new top-level section titled `## Lifecycle hooks`. Place it after the
main feature list (the existing structure under `## Status` ends; insert
the new section there). Suggested content:

```markdown
## Lifecycle hooks

Mantle invokes user-supplied shell scripts on issue lifecycle events so you
can push status updates to Linear, Jira, Slack, or any other tracker —
without mantle ever importing a tracker library or holding credentials.

### Convention

Drop an executable script at `<mantle-dir>/hooks/on-<event>.sh`:

| Event | Fires after |
|---|---|
| `issue-shaped` | `/mantle:shape-issue` saves a shaped issue |
| `issue-implement-start` | issue transitions to `implementing` |
| `issue-verify-done` | issue transitions to `verified` |
| `issue-review-approved` | issue transitions to `approved` |

Your script is invoked with:

- `$1` — issue number
- `$2` — new status
- `$3` — issue title

Missing scripts are a silent no-op. Non-zero exits log a warning and the
workflow continues (hook failures never block mantle).

### Config passthrough

Any dict under `hooks_env:` in `<mantle-dir>/config.md` frontmatter is
exported as environment variables to the hook process. Keys are opaque —
mantle never interprets them.

```yaml
---
hooks_env:
  LINEAR_API_KEY: lin_api_xxx
  JIRA_PROJECT_KEY: PLAT
---
```

### Quick start with shipped examples

```bash
mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh
chmod +x .mantle/hooks/on-issue-shaped.sh
```

Available examples: `linear`, `jira`, `slack`. Each contains a setup
header documenting the CLI/API install, auth steps, and required env vars.
```

### Design decisions

- **Package data, not `examples/` in repo root**: PyPI users need the
  scripts; a repo-only `examples/` wouldn't ship.
- **Stdout print, not auto-copy**: mantle doesn't know *which* event the
  user wants each script bound to. Let the user choose via the redirect.
- **`hooks_env:` as the only mantle-readable config key**: preserves the
  seam principle — mantle reads the dict but never introspects its
  contents.
- **Setup headers as comment blocks in each script**: AC#10 requires this.
  Documenting in-script means the user can read the setup even when they
  can't run mantle (e.g. pasting the script into a fresh repo).

## Tests

### `tests/cli/test_hooks.py` (new)

```python
from mantle.cli import hooks as cli_hooks


def test_show_hook_example_prints_linear(capsys):
    cli_hooks.run_show_hook_example(name="linear")
    out = capsys.readouterr().out
    assert out.startswith("#!/usr/bin/env bash")
    assert "linear" in out.lower()


def test_show_hook_example_prints_jira(capsys):
    cli_hooks.run_show_hook_example(name="jira")
    out = capsys.readouterr().out
    assert "acli" in out  # setup header mentions acli


def test_show_hook_example_prints_slack(capsys):
    cli_hooks.run_show_hook_example(name="slack")
    out = capsys.readouterr().out
    assert "SLACK_WEBHOOK_URL" in out


def test_show_hook_example_unknown_exits_non_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli_hooks.run_show_hook_example(name="bogus")
    assert exc.value.code == 1
    err = capsys.readouterr().out
    assert "linear" in err  # lists available names
```

### `tests/integration/test_hook_examples.py` (new)

Integration test that runs each shipped example end-to-end against a
stubbed external CLI, proving the script is syntactically valid and reaches
its commit point:

```python
import os
import stat
import subprocess
from importlib import resources
from pathlib import Path

import pytest


EXAMPLES = ["linear", "jira", "slack"]


def _write_example_to(tmp_path: Path, name: str) -> Path:
    content = (
        resources.files("mantle.assets.hook_examples") / f"{name}.sh"
    ).read_text(encoding="utf-8")
    script = tmp_path / f"on-issue-shaped.sh"
    script.write_text(content)
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _stub_binary(tmp_path: Path, name: str) -> None:
    """Create a no-op shim on PATH so the example's external CLI/curl
    succeeds without hitting the network."""
    stub = tmp_path / name
    stub.write_text("#!/usr/bin/env bash\necho STUB $@\nexit 0\n")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)


def test_linear_example_runs_structurally(tmp_path, monkeypatch):
    _write_example_to(tmp_path, "linear")
    _stub_binary(tmp_path, "curl")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("LINEAR_API_KEY", "test-key")
    monkeypatch.setenv("LINEAR_TEAM_ID", "test-team")
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_jira_example_runs_structurally(tmp_path, monkeypatch):
    _write_example_to(tmp_path, "jira")
    _stub_binary(tmp_path, "acli")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "PLAT")
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_slack_example_runs_structurally(tmp_path, monkeypatch):
    _write_example_to(tmp_path, "slack")
    _stub_binary(tmp_path, "curl")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.invalid/hook")
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_unset_required_env_fails(tmp_path, monkeypatch):
    # Without LINEAR_API_KEY, the `:` parameter expansion exits non-zero.
    _write_example_to(tmp_path, "linear")
    _stub_binary(tmp_path, "curl")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    # Intentionally don't set LINEAR_API_KEY.
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "LINEAR_API_KEY" in result.stderr
```

If the project doesn't have a `tests/integration/` tree yet, put the file
at `tests/test_hook_examples.py` or `tests/assets/test_hook_examples.py`
— wherever fits the existing layout. Check the existing test tree first.

### `tests/cli/test_main.py` (modify — if it exists)

If there's a test that snapshots the top-level `mantle --help` output,
that snapshot will need updating to include `show-hook-example`. Re-run
`uv run pytest --inline-snapshot=create` on that test only and inspect
the diff before committing. Do not hand-edit the snapshot.

## Acceptance criteria covered by this story

- AC7 (shipped `linear.sh` works end-to-end) — structural test above; live
  E2E is human-verified in `/mantle:review`
- AC8 (shipped `jira.sh` works end-to-end) — same, structural test +
  manual review
- AC9 (shipped `slack.sh` works end-to-end) — same
- AC10 (each example has a setup header) — enforced by test that scripts
  start with `#!/usr/bin/env bash` and contain setup keywords
- AC11 (README documents hook authoring) — via the new `## Lifecycle
  hooks` README section
- AC12 partial (tests cover example invocation) — via
  `tests/integration/test_hook_examples.py`
