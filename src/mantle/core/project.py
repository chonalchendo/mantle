"""Project initialization and structure constants."""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
from importlib import resources
from typing import TYPE_CHECKING, Any

import pydantic
import yaml

from mantle.core import state, vault

if TYPE_CHECKING:
    from pathlib import Path

# ── Structure constants ──────────────────────────────────────────

MANTLE_DIR = ".mantle"
GLOBAL_MANTLE_ROOT = ".mantle/projects"
COST_POLICY_FILENAME = "cost-policy.md"

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
    "telemetry",
)

# ── File template data ───────────────────────────────────────────


class _ConfigFrontmatter(pydantic.BaseModel):
    """Config.md frontmatter schema (internal)."""

    personal_vault: str | None = None
    verification_strategy: str | None = None
    auto_push: bool = False
    storage_mode: str | None = None
    hooks_env: dict[str, str] | None = None
    diff_paths: dict[str, list[str]] | None = None
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

    In local storage mode, ``.mantle/`` lives at the primary git
    worktree's root.  If ``project_dir`` is inside a linked worktree,
    this function resolves up to the primary so every worktree of the
    same repo shares one ``.mantle/``.  For non-git directories the
    path is returned unchanged.

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
    primary = _primary_worktree_root(project_dir)
    root = primary if primary is not None else project_dir
    return root / MANTLE_DIR


def _primary_worktree_root(project_dir: Path) -> Path | None:
    """Return the primary git worktree root for ``project_dir``.

    The primary worktree is the main checkout of a repository — linked
    worktrees created via ``git worktree add`` share its ``.git``
    metadata.  ``git worktree list --porcelain`` always lists the
    primary first, so the first ``worktree <path>`` line identifies it.

    Args:
        project_dir: Directory inside the worktree to query.

    Returns:
        Absolute path to the primary worktree root, or ``None`` if
        ``project_dir`` is not inside a git repository.
    """
    result = subprocess.run(
        ["git", "-C", str(project_dir), "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            return pathlib.Path(line[len("worktree ") :])
    return None


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
    (mantle_path / COST_POLICY_FILENAME).write_text(
        _read_bundled_template(COST_POLICY_FILENAME),
        encoding="utf-8",
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
    config_path = resolve_mantle_dir(project_root) / "config.md"
    frontmatter, _ = read_frontmatter_and_body(config_path)
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
    config_path = resolve_mantle_dir(project_root) / "config.md"
    frontmatter, body = read_frontmatter_and_body(config_path)
    frontmatter.update(kwargs)
    _write_frontmatter_and_body(config_path, frontmatter, body)


_STAGE_NAMES: tuple[str, ...] = (
    "shape",
    "plan_stories",
    "implement",
    "simplify",
    "verify",
    "review",
    "retrospective",
)


class StageModels(pydantic.BaseModel, frozen=True):
    """Per-stage model tier for /mantle:build.

    One field per build stage; each field holds the model name
    (e.g. ``"opus"``, ``"sonnet"``, ``"haiku"``) to use for that
    stage. Frozen — build consumers should treat the value as
    immutable.
    """

    shape: str
    plan_stories: str
    implement: str
    simplify: str
    verify: str
    review: str
    retrospective: str


FALLBACK_STAGE_MODELS: StageModels = StageModels(
    shape="opus",
    plan_stories="sonnet",
    implement="sonnet",
    simplify="sonnet",
    verify="sonnet",
    review="haiku",
    retrospective="haiku",
)


class Pricing(pydantic.BaseModel, frozen=True):
    """Per-model token pricing in USD per million tokens.

    All four fields are required and must be positive floats.
    Frozen — callers should treat a ``Pricing`` instance as immutable.

    Attributes:
        input: Cost per million input tokens.
        output: Cost per million output tokens.
        cache_read: Cost per million cache-read tokens.
        cache_write: Cost per million cache-write tokens.
    """

    input: float
    output: float
    cache_read: float
    cache_write: float


def load_prices(project_root: Path) -> dict[str, Pricing]:
    """Read per-model token prices from .mantle/cost-policy.md.

    The ``prices:`` block in the frontmatter must contain one entry per
    model name (e.g. ``opus``, ``sonnet``, ``haiku``), each with four
    sub-fields: ``input``, ``output``, ``cache_read``, ``cache_write``
    (USD per million tokens).

    Args:
        project_root: Directory containing ``.mantle/``.

    Returns:
        Mapping from model name to a validated, frozen ``Pricing``
        instance.

    Raises:
        FileNotFoundError: If ``.mantle/cost-policy.md`` does not
            exist.
        KeyError: If the frontmatter has no ``prices`` block.
        pydantic.ValidationError: If a per-model entry fails schema
            validation (e.g. a field value is not a number).
    """
    cost_policy_path = resolve_mantle_dir(project_root) / COST_POLICY_FILENAME
    frontmatter, _ = read_frontmatter_and_body(cost_policy_path)
    if "prices" not in frontmatter:
        msg = "cost-policy.md has no 'prices' block"
        raise KeyError(msg)
    raw: dict[str, Any] = frontmatter["prices"]
    return {
        name: Pricing.model_validate(fields) for name, fields in raw.items()
    }


def load_model_tier(project_root: Path) -> StageModels:
    """Resolve the per-stage model tier for this project.

    Precedence: config.md ``models`` block → cost-policy.md preset
    → hardcoded balanced fallback.  When ``config.md`` is missing the
    hardcoded fallback is returned directly; malformed config or
    cost-policy files propagate their errors.

    Args:
        project_root: Directory containing .mantle/.

    Returns:
        Frozen ``StageModels`` with one model name per build stage.

    Raises:
        pydantic.ValidationError: If the ``models`` block in config.md
            contains unknown stage names in ``overrides``.
        KeyError: If the selected preset is not defined in
            cost-policy.md.
    """
    try:
        config = read_config(project_root)
    except FileNotFoundError:
        return FALLBACK_STAGE_MODELS

    models_cfg = _ModelsConfig.model_validate(config.get("models") or {})
    presets = _load_presets(project_root)
    if models_cfg.preset not in presets:
        msg = (
            f"Unknown preset {models_cfg.preset!r}. "
            f"Defined presets: {sorted(presets)}."
        )
        raise KeyError(msg)
    merged = {**presets[models_cfg.preset], **models_cfg.overrides}
    return StageModels(**merged)


def init_vault(vault_path: Path, project_root: Path) -> bool:
    """Create or link a personal vault, then record it in this project's config.

    If all four vault subdirectories already exist at ``vault_path``, the
    existing vault is linked without creating anything. Otherwise the
    subdirectories are created. Either way, the resolved vault path is
    written to ``.mantle/config.md``.

    Args:
        vault_path: Path for the personal vault (expanded and resolved).
        project_root: Directory containing .mantle/.

    Returns:
        True if the vault was newly created, False if linked to an
        existing one.

    Raises:
        FileNotFoundError: If .mantle/ does not exist at project_root.
    """
    mantle_path = project_root / MANTLE_DIR
    if not mantle_path.is_dir():
        msg = f"{MANTLE_DIR}/ does not exist at {project_root}"
        raise FileNotFoundError(msg)

    resolved = vault_path.expanduser().resolve()
    subdirs = ("skills", "knowledge", "inbox", "projects")

    created = not all((resolved / d).is_dir() for d in subdirs)

    if created:
        for d in subdirs:
            (resolved / d).mkdir(parents=True, exist_ok=True)

    update_config(project_root, personal_vault=str(resolved))

    return created


# ── Internal helpers ─────────────────────────────────────────────

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _read_bundled_template(filename: str) -> str:
    """Read a bundled vault-template file as text.

    In an installed wheel, ``vault-templates/`` is force-included
    under ``mantle/`` by ``pyproject.toml``.  During editable /
    development installs, the directory lives at the project root.
    This helper checks both locations.

    Args:
        filename: Name of a file under ``vault-templates/``.

    Returns:
        File contents as UTF-8 text.

    Raises:
        FileNotFoundError: If the template cannot be located in
            either the installed package or the development tree.
    """
    pkg_ref = resources.files("mantle").joinpath("vault-templates", filename)
    pkg_path = pathlib.Path(str(pkg_ref))
    if pkg_path.is_file():
        return pkg_path.read_text(encoding="utf-8")

    dev_path = pathlib.Path(str(resources.files("mantle"))).parent.parent
    dev_path = dev_path / "vault-templates" / filename
    return dev_path.read_text(encoding="utf-8")


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


class _ModelsConfig(pydantic.BaseModel):
    """Schema for the ``models`` block in config.md (internal)."""

    preset: str = "balanced"
    overrides: dict[str, str] = pydantic.Field(default_factory=dict)

    @pydantic.field_validator("overrides")
    @classmethod
    def _validate_override_keys(cls, v: dict[str, str]) -> dict[str, str]:
        unknown = set(v) - set(_STAGE_NAMES)
        if unknown:
            msg = (
                f"Unknown stage(s) in models.overrides: "
                f"{sorted(unknown)}. "
                f"Valid stages: {list(_STAGE_NAMES)}."
            )
            raise ValueError(msg)
        return v


def _load_presets(project_root: Path) -> dict[str, dict[str, str]]:
    """Read presets from .mantle/cost-policy.md.

    Args:
        project_root: Directory containing .mantle/.

    Returns:
        Mapping from preset name to ``{stage: model}`` dict. Returns
        ``{"balanced": FALLBACK_STAGE_MODELS.model_dump()}`` when
        cost-policy.md is missing.

    Raises:
        yaml.YAMLError: If the frontmatter is malformed.
        KeyError: If the frontmatter has no ``presets`` field.
    """
    cost_policy_path = resolve_mantle_dir(project_root) / COST_POLICY_FILENAME
    try:
        frontmatter, _ = read_frontmatter_and_body(cost_policy_path)
    except FileNotFoundError:
        return {"balanced": FALLBACK_STAGE_MODELS.model_dump()}
    return frontmatter["presets"]


def read_frontmatter_and_body(path: Path) -> tuple[dict[str, Any], str]:
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
