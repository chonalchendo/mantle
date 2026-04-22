---
issue: 88
title: 'Core + CLI: multi-path audit with per-surface report'
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user paying for tokens on every AI invocation, I want `mantle audit-tokens` to audit commands and skills in one invocation with per-surface sub-tables so that I can see where token cost concentrates across the full vault surface.

## Depends On

None — independent.

## Approach

Extend the existing single-path `core/token_audit.py` into a multi-path audit that groups results by surface and emits one sub-table per surface in the report. The CLI gains a repeatable `--path` flag (with a back-compat default). Builds directly on the existing `AuditEntry` dataclass, `audit_directory`, `format_report`, and `append_after_section` public API — no new modules, no new dependencies.

## Implementation

### src/mantle/core/token_audit.py (modify)

1. Change `audit_directory(commands_dir: Path, encoding_name: str) -> list[AuditEntry]` to traverse `rglob("*.md")` instead of `glob("*.md")`. This lets it audit nested directories (commands live under `claude/commands/mantle/`, skills under `/Users/conal/test-vault/skills/` flat — both work with rglob). Keep the signature to preserve callers.

2. Add a new public function:

   ```python
   def audit_paths(
       paths: list[Path],
       encoding_name: str = DEFAULT_ENCODING,
   ) -> dict[str, list[AuditEntry]]:
       """Audit each root path and group results by surface label.

       Surface label is the basename of each path (e.g., 'mantle' for
       claude/commands/mantle, 'skills' for /Users/conal/test-vault/skills).
       Returns an insertion-ordered dict so report ordering is stable.

       Percent-of-total within each surface is computed against that
       surface's total, not the overall total, so sub-tables rank
       intra-surface cost.
       """
   ```

   Implementation: for each path, call `audit_directory(path, encoding_name)`; key the result by `path.name` (falls back to `str(path)` if empty). If two paths share a basename, disambiguate with the full path string.

3. Update `format_report` to accept the new per-surface shape:

   ```python
   def format_report(
       per_surface: dict[str, list[AuditEntry]],
       heading: str = "Before",
       encoding_name: str = DEFAULT_ENCODING,
   ) -> str:
   ```

   - Emits one `### <surface>` sub-section under `## <heading>` per surface.
   - Each sub-section has its own ranked table, per-surface total, and per-surface top-3.
   - End with an overall `**Total (all surfaces):** N tokens across M files.` line.
   - Title stays a single top-level H1 (`# Mantle token audit — <date>`; drop "command" since now multi-surface).

4. Update `append_after_section` to consume the same per-surface dict:

   ```python
   def append_after_section(
       report_path: Path,
       per_surface_after: dict[str, list[AuditEntry]],
   ) -> None:
   ```

   - Parse Before tables per surface via surface-scoped section markers (`### <surface>` under `## Before`).
   - Emit `## After` with one sub-section per surface; each sub-section shows Before / After / Saved / % saved rows.
   - Emit `## Delta summary` with per-surface bullets (top-3 saved, total saved) and an overall total.

5. Update `_parse_before_tokens` (or introduce `_parse_before_tokens_per_surface`) to scope parsing to a specific surface section.

#### Design decisions

- **rglob not glob**: skills live flat at `/Users/conal/test-vault/skills/*.md` and rglob works identically; commands in `claude/commands/mantle/*.md` also work. Generalising the traversal costs one character and unblocks both surfaces.
- **Keep `audit_directory` as public**: existing tests and callers keep working; `audit_paths` is the new multi-surface entrypoint built on top of it. Deep module: thin orchestrator over a proven unit.
- **Surface label = basename**: simplest unambiguous default. No need for `--label` flag yet; if two paths collide on basename later we can add it.
- **Per-surface percent-of-total**: intra-surface ranking is what tells you which file in that surface to trim. Cross-surface ranking is misleading (a 5000-token skill is "worse" than a 2000-token command in percent terms, but they're different surfaces with different cut techniques).

### src/mantle/cli/audit_tokens.py (modify)

1. Change signature:

   ```python
   def run_audit_tokens(
       *,
       path: list[Path] | None = None,
       out: Path | None = None,
       heading: str = "Before",
       encoding: str = "cl100k_base",
       append: bool = False,
   ) -> None:
   ```

   - If `path` is None or empty, default to `[Path("claude/commands/mantle")]` (preserves prior default behaviour for single-surface callers).
   - Cyclopts renders repeatable `--path` via `list[Path]` type hint.

2. Call `token_audit.audit_paths(path, encoding)`; pass the dict to `format_report` / `append_after_section`.

3. Update help text on the `--path` flag to mention repeatability: `"Path to audit (repeatable for multi-surface audits)."`. Other flags unchanged.

#### Design decisions

- **Repeatable flag vs positional nargs**: flag is self-documenting, order-independent, and matches `cli-design-best-practices` guidance ("prefer flags over positional").
- **Preserve single-path default**: existing users + tests see no behaviour change when invoking `mantle audit-tokens` bare.

### src/mantle/cli/app.py (verify, no code change expected)

Check that the cyclopts `@app.command` wiring already flows `list[Path]` through correctly. If not, adjust the type hint on the command registration side.

## Tests

### tests/core/test_token_audit.py (modify)

- **test_audit_paths_groups_by_surface_basename**: two tmp_path roots with distinct basenames ("cmds" with 2 .md files, "skills" with 3 .md files). Assert result keys == {"cmds", "skills"}; assert token counts sum correctly per surface.
- **test_audit_paths_uses_rglob**: nested dirs (`root/a.md`, `root/sub/b.md`) both audited.
- **test_audit_paths_empty_surface**: root with no .md files returns empty list under that key (not KeyError).
- **test_format_report_multi_surface**: use `inline_snapshot` to assert the full rendered Markdown for two-surface input — H1, per-surface `###` headings, per-surface tables, per-surface top-3, overall total line.
- **test_format_report_single_surface_back_compat**: one-surface dict still renders readable report (no regression).
- **test_append_after_section_multi_surface**: write a Before report via `format_report` to tmp_path, call `append_after_section` with After entries reflecting trims on two surfaces, assert resulting file contains `## After` per surface and a `## Delta summary` with per-surface + overall totals. Use `inline_snapshot` for the appended block.
- **test_append_after_section_rejects_rerun**: existing ValueError behaviour preserved when `## After` is already present.

### tests/cli/test_audit_tokens.py (new file if absent, otherwise modify)

- **test_cli_single_path_default**: `uv run mantle audit-tokens` with CWD pointing at a tmp fixture — writes report to expected default path under `.mantle/audits/`. Use `inline_snapshot` on the report body.
- **test_cli_multi_path**: `uv run mantle audit-tokens --path <dir1> --path <dir2> --out <tmp>` — report contains both surfaces. Assert report file shape via `inline_snapshot`.
- **test_cli_append_requires_out**: `--append` without `--out` exits non-zero with actionable stderr.

#### Test fixture requirements

- Use `tmp_path` throughout. Write a handful of small `.md` files with known content so token counts are deterministic under `cl100k_base`.
- No mocking of tiktoken — it's a direct dependency and cheap to call.
- For CLI tests, prefer calling the `run_audit_tokens` function directly over spawning a subprocess unless asserting help-text output.

## Verification against issue ACs

- ac-01 (partial): structure for per-surface sub-tables is in place; the ranked report over real paths is produced in story 2.
- ac-04 (partial): `--append` supports per-surface delta; real delta report produced in story 2.
- ac-06: `just check` must pass (mypy, ruff, pytest).