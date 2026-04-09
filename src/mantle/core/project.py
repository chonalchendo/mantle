"""Project initialization and structure constants."""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
from typing import TYPE_CHECKING, Any

import pydantic
import yaml

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path

# ── Structure constants ──────────────────────────────────────────

MANTLE_DIR = ".mantle"
GLOBAL_MANTLE_ROOT = ".mantle/projects"

SUBDIRS: tuple[str, ...] = (
    "bugs",
    "challenges",
    "decisions",
    "distillations",
    "inbox",
    "issues",
    "learnings",
    "research",
    "sessions",
    "shaped",
    "stories",
)

# ── File template data ───────────────────────────────────────────


class _ConfigFrontmatter(pydantic.BaseModel):
    """Config.md frontmatter schema (internal)."""

    personal_vault: str | None = None
    verification_strategy: str | None = None
    auto_push: bool = False
    storage_mode: str | None = None
    tags: tuple[str, ...] = ("type/config",)


CONFIG_BODY = """\
## Verification Strategy

_Define how you verify that each issue is complete before moving on._

## Personal Vault

_Set via `mantle init-vault <path>`. Cross-project skills and knowledge._
"""


class _TagsFrontmatter(pydantic.BaseModel):
    """Tags.md frontmatter schema (internal)."""

    tags: tuple[str, ...] = ("type/config",)


TAGS_BODY = """\
## Tag Taxonomy

### Type

- `type/idea`
- `type/bug`
- `type/challenge`
- `type/product-design`
- `type/system-design`
- `type/decision`
- `type/issue`
- `type/story`
- `type/session-log`
- `type/shaped`
- `type/learning`
- `type/skill`
- `type/config`

### Phase

- `phase/idea`
- `phase/challenge`
- `phase/design`
- `phase/adopted`
- `phase/shaping`
- `phase/planning`
- `phase/implementing`
- `phase/verifying`
- `phase/reviewing`

### Status

- `status/active`
- `status/completed`
- `status/blocked`
- `status/archived`

### Confidence

- `confidence/high` (7-10)
- `confidence/medium` (4-6)
- `confidence/low` (1-3)

### Severity

- `severity/blocker`
- `severity/high`
- `severity/medium`
- `severity/low`

### Topic

- `topic/<skill-slug>` — content topic, one per skill

### Domain

- `domain/web` — web frameworks, HTTP, frontend
- `domain/database` — SQL, NoSQL, caching
- `domain/devops` — containers, CI/CD, infrastructure
- `domain/testing` — test frameworks and strategies
- `domain/concurrency` — async, threading, parallelism
"""

GITIGNORE_CONTENT = """\
# Compiled command files
*.compiled.md

# Compilation manifest
.compile-manifest.json

# Temporary files
*.tmp
*.bak
"""


# ── Public API ───────────────────────────────────────────────────


def project_identity(project_dir: Path) -> str:
    """Compute a stable identity string for a project directory.

    Uses the git remote origin URL when available, otherwise falls
    back to the resolved absolute path.  The identity is a slugified
    repo (or directory) name followed by a 12-char SHA-256 hex prefix.

    Args:
        project_dir: Root directory of the project.

    Returns:
        Identity string in the form ``<slug>-<hash12>``.
    """
    result = subprocess.run(
        ["git", "-C", str(project_dir), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        source = result.stdout.strip()
    else:
        source = str(project_dir.resolve())

    hash12 = hashlib.sha256(source.encode()).hexdigest()[:12]
    slug = _slugify_name(source)
    return f"{slug}-{hash12}"


def resolve_mantle_dir(project_dir: Path) -> Path:
    """Resolve the .mantle/ storage directory for a project.

    Uses the existence of ``~/.mantle/projects/<identity>/`` as the
    global-mode signal — no in-repo marker required.  A git worktree
    created from a migrated project inherits the same global context
    automatically because it shares the same ``project_identity()``.

    This function does **not** create any directories.

    Args:
        project_dir: Root directory of the project.

    Returns:
        Resolved path to the .mantle directory.
    """
    identity = project_identity(project_dir)
    global_dir = pathlib.Path.home() / GLOBAL_MANTLE_ROOT / identity
    if global_dir.exists():
        return global_dir
    return project_dir / MANTLE_DIR


def init_project(project_dir: Path, project_name: str) -> Path:
    """Create .mantle/ directory structure with initial files.

    Does NOT check whether .mantle/ already exists. The caller
    is responsible for idempotency checks and user-facing messaging.

    Args:
        project_dir: Root directory of the project.
        project_name: Name for the project (used in state.md).

    Returns:
        Path to the created .mantle/ directory.

    Raises:
        FileExistsError: If .mantle/ already exists (via mkdir).
    """
    mantle_path = project_dir / MANTLE_DIR
    mantle_path.mkdir()

    for subdir in SUBDIRS:
        (mantle_path / subdir).mkdir()

    vault.write_note(
        mantle_path / "config.md",
        _ConfigFrontmatter(),
        CONFIG_BODY,
    )
    vault.write_note(
        mantle_path / "tags.md",
        _TagsFrontmatter(),
        TAGS_BODY,
    )
    (mantle_path / ".gitignore").write_text(GITIGNORE_CONTENT)

    state.create_initial_state(project_dir, project_name)

    return mantle_path


def read_config(project_root: Path) -> dict[str, Any]:
    """Load config frontmatter from .mantle/config.md.

    Args:
        project_root: Directory containing .mantle/.

    Returns:
        Dictionary of frontmatter key-value pairs.

    Raises:
        FileNotFoundError: If .mantle/ or config.md does not exist.
    """
    config_path = project_root / MANTLE_DIR / "config.md"
    frontmatter, _ = _read_frontmatter_and_body(config_path)
    return frontmatter


def update_config(project_root: Path, **kwargs: Any) -> None:
    """Update specific keys in .mantle/config.md frontmatter.

    Reads existing config, merges provided keys, writes back.
    Preserves the markdown body.

    Args:
        project_root: Directory containing .mantle/.
        **kwargs: Key-value pairs to update in frontmatter.

    Raises:
        FileNotFoundError: If .mantle/ or config.md does not exist.
    """
    config_path = project_root / MANTLE_DIR / "config.md"
    frontmatter, body = _read_frontmatter_and_body(config_path)
    frontmatter.update(kwargs)
    _write_frontmatter_and_body(config_path, frontmatter, body)


def init_vault(vault_path: Path, project_root: Path) -> None:
    """Create personal vault structure and link it to this project.

    Creates skills/, knowledge/, inbox/, projects/ at vault_path.
    Records the resolved vault path in .mantle/config.md.

    Args:
        vault_path: Path for the personal vault (expanded and resolved).
        project_root: Directory containing .mantle/.

    Raises:
        FileExistsError: If all three vault subdirectories already exist.
        FileNotFoundError: If .mantle/ does not exist at project_root.
    """
    mantle_path = project_root / MANTLE_DIR
    if not mantle_path.is_dir():
        msg = f"{MANTLE_DIR}/ does not exist at {project_root}"
        raise FileNotFoundError(msg)

    resolved = vault_path.expanduser().resolve()
    subdirs = ("skills", "knowledge", "inbox", "projects")

    if all((resolved / d).is_dir() for d in subdirs):
        msg = f"Personal vault already exists at {resolved}"
        raise FileExistsError(msg)

    for d in subdirs:
        (resolved / d).mkdir(parents=True, exist_ok=True)

    update_config(project_root, personal_vault=str(resolved))


# ── Internal helpers ─────────────────────────────────────────────

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify_name(source: str) -> str:
    """Extract and slugify a repo or directory name from a source.

    For URLs like ``git@github.com:user/my-repo.git`` extracts
    ``my-repo``.  For paths like ``/home/user/my-project`` extracts
    ``my-project``.  Non-alphanumeric characters are replaced with
    hyphens, and leading/trailing hyphens are stripped.

    Args:
        source: Git remote URL or absolute path string.

    Returns:
        Lowercase slug suitable for use in directory names.
    """
    # Extract the last path/URL segment, strip .git suffix.
    basename = source.rstrip("/").rsplit("/", maxsplit=1)[-1]
    if basename.endswith(".git"):
        basename = basename[:-4]

    slug = _SLUG_RE.sub("-", basename.lower()).strip("-")
    return slug or "project"


def _read_frontmatter_and_body(path: Path) -> tuple[dict[str, Any], str]:
    """Split a markdown file into frontmatter dict and body string.

    Args:
        path: Path to the markdown file.

    Returns:
        Tuple of (frontmatter dict, body string).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    raw = text[4:end]
    rest = text[end + 4 :]

    if rest.startswith("\n\n"):
        body = rest[2:]
    elif rest.startswith("\n"):
        body = rest[1:]
    else:
        body = rest

    data = yaml.safe_load(raw)
    return (data if data else {}), body


def _write_frontmatter_and_body(
    path: Path,
    frontmatter: dict[str, Any],
    body: str,
) -> None:
    """Write frontmatter + body back to a markdown file.

    Args:
        path: Path to the markdown file.
        frontmatter: Dictionary to serialize as YAML frontmatter.
        body: Markdown body content.
    """
    yaml_str = yaml.dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    text = f"---\n{yaml_str}---\n\n{body}"
    path.write_text(text, encoding="utf-8")
