"""Project initialization and structure constants."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pydantic
import yaml

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path

# ── Structure constants ──────────────────────────────────────────

MANTLE_DIR = ".mantle"

SUBDIRS: tuple[str, ...] = (
    "decisions",
    "sessions",
    "issues",
    "stories",
)

# ── File template data ───────────────────────────────────────────


class _ConfigFrontmatter(pydantic.BaseModel):
    """Config.md frontmatter schema (internal)."""

    personal_vault: str | None = None
    verification_strategy: str | None = None
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
- `type/challenge`
- `type/product-design`
- `type/system-design`
- `type/decision`
- `type/issue`
- `type/story`
- `type/session-log`
- `type/skill`
- `type/config`

### Phase

- `phase/idea`
- `phase/challenge`
- `phase/design`
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
"""

GITIGNORE_CONTENT = """\
# Compiled command files
*.compiled.md

# Temporary files
*.tmp
*.bak
"""


# ── Public API ───────────────────────────────────────────────────


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

    Creates skills/, knowledge/, inbox/ at vault_path.
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
    subdirs = ("skills", "knowledge", "inbox")

    if all((resolved / d).is_dir() for d in subdirs):
        msg = f"Personal vault already exists at {resolved}"
        raise FileExistsError(msg)

    for d in subdirs:
        (resolved / d).mkdir(parents=True, exist_ok=True)

    update_config(project_root, personal_vault=str(resolved))


# ── Internal helpers ─────────────────────────────────────────────


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
