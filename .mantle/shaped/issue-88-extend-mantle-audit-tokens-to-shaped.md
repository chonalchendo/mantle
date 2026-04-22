---
issue: 88
title: Extend mantle audit-tokens to sweep all commands and skills in the vault
approaches:
- A — Extend audit-tokens in place (multi-path, recursive glob)
- B — Separate audit-skills command
- C — Config-driven sweep (.mantle/audit-config.yaml)
chosen_approach: A — Extend audit-tokens in place (multi-path, recursive glob)
appetite: medium batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-22'
updated: '2026-04-22'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

# Shaping — Issue 88: Extend mantle audit-tokens to sweep all commands + skills

## Approaches evaluated

### A — Extend audit-tokens in place (multi-path, recursive glob) — *chosen*
- **Description:** Modify `core/token_audit.audit_directory` into a path-list-aware `audit_paths`, using `rglob("*.md")` per path; `format_report` emits one sub-table per surface; `append_after_section` learns per-surface Before tables. CLI gains repeatable `--path` and optional `--label` flags. Prose work follows: top-3 commands + top-3 skills get concrete cuts, and every output-emitting `/mantle:*` command gets an Output Format section with a one-line-per-item template + anti-pattern list.
- **Appetite:** medium batch (CLI ≈ 0.5d, prose rewrites + Output-Format sweep ≈ 1d, measure+verify ≈ 0.5d).
- **Tradeoffs:** Re-uses existing shape (AuditEntry, format/append functions); cheap incremental change. Downside: `format_report` and `append_after_section` need to learn the per-surface grouping — modest parser update.
- **Rabbit holes:** (1) `--append` parser must handle per-surface Before tables without confusing entries across surfaces. Mitigate with surface-scoped section headings (`## Before — commands`, `## Before — skills`). (2) Vault path is user-specific (see `config.md:personal_vault`); CLI must accept absolute paths, not assume `claude/commands/mantle`. (3) Output-Format template is already proven on issue 74 — reuse that exact pattern.
- **No-gos:** No config-driven sweep list; no output-token estimation; no migration of old single-surface reports.

### B — Separate `audit-skills` command
- **Description:** Leave `audit-tokens` alone; add a parallel `mantle audit-skills` command; combine into one report via a shell pipeline or third command.
- **Appetite:** medium batch.
- **Tradeoff:** Two near-identical CLIs; combined report requires a third orchestrator or manual concat. Ships more surface, loses the single-invocation requirement from ac-01.
- **Why rejected:** ac-01 explicitly requires "one invocation covers commands + skills in a single combined report".

### C — Config-driven sweep (`.mantle/audit-config.yaml`)
- **Description:** YAML file lists surfaces → paths; CLI reads it and runs the sweep.
- **Appetite:** large batch (new file format, omegaconf integration, docs).
- **Why rejected:** Two surfaces doesn't justify a config format. YAGNI (software-design-principles, simplification checklist). Can be added later if/when surface count grows.

## Chosen approach — A (Extend in place, multi-path)
Appetite: **medium batch**.

Rationale: reuses existing module boundary (deep-module principle from `software-design-principles`), keeps core pure, CLI thin (cli-design-best-practices "flags over positional; `--long-form` always"), no new dependencies, and produces exactly the combined report ac-01 describes. The prose rewrite pass is the bulk of the work — separating it from the CLI extension into its own story keeps each story session-sized.

## Code design

### Strategy

1. **`src/mantle/core/token_audit.py`:**
   - Add `audit_paths(paths: list[Path], encoding: str) -> dict[str, list[AuditEntry]]`. Each path is audited via `rglob("*.md")`; surface label defaults to `path.name` (basename). Returns a dict so `format_report` can emit sub-tables in a stable order.
   - Update `format_report(per_surface: dict[str, list[AuditEntry]], heading: str, encoding: str) -> str`. For each surface, render `### <surface>` with the ranked table; top-3 candidates per surface; overall total across all surfaces.
   - Update `append_after_section(report_path: Path, per_surface: dict[str, list[AuditEntry]])` — parse surface-scoped Before tables (section markers `### <surface>` under `## Before`), compute per-surface Saved/Saved-pct + overall totals.
   - Keep `audit_directory` as a thin backwards-compatible wrapper (`audit_paths([dir])["default"]`) to preserve any single-path callers and tests.
2. **`src/mantle/cli/audit_tokens.py`:**
   - Change signature: `paths: list[Path]` (repeatable `--path`). If empty, default to `[Path("claude/commands/mantle")]` (preserves pre-88 default).
   - Optional `--label LABEL=PATH` is out of scope; use basename. Simpler.
   - Call `token_audit.audit_paths`; pass `dict[surface, entries]` to `format_report` / `append_after_section`.
3. **Tests (`tests/core/test_token_audit.py`, `tests/cli/test_audit_tokens.py`):**
   - Unit: `audit_paths` with two tmp_path roots — verify per-surface grouping, recursive glob.
   - Snapshot: `format_report` multi-surface output via `inline_snapshot`.
   - Snapshot: `append_after_section` with per-surface Before tables.
   - CLI: integration via `uv run mantle audit-tokens --path ... --path ...` against fixtures in tmp; assert report file shape via `inline_snapshot`.
4. **Prose rewrite pass (story 2):**
   - Run the new audit against `claude/commands/mantle` + `/Users/conal/test-vault/skills`.
   - Identify top-3 commands (already known from issue 74: build, shape-issue, implement) and top-3 skills (from report — likely `production-project-readiness`, `software-design-principles`, `designing-architecture`).
   - Apply Output Format templates + imperative fragments to all 6. Preserve Iron Laws, Red Flags tables, numbered steps, CLI invocations, `$MANTLE_DIR`/`.mantle/` paths.
   - Add Output Format section to every other `/mantle:*` command that emits output. Not every command emits output — purely state-mutating commands (e.g., `bug.md`, `idea.md`) are exempt.
5. **Measure + verify (story 3):**
   - Run audit with `--append` → produce Delta summary.
   - Run `/mantle:build` against a trivial throwaway issue to confirm no regression.
   - `just check`.

### Fits architecture by

- Preserves core-never-imports-cli (import-linter contract in `pyproject.toml`).
- `audit_paths` is a deep module — simple input/output, rich implementation (glob + counting + grouping).
- Follows cli-design-best-practices: long-form flag (`--path`), repeatable for multiple values, default preserves prior behaviour, help text lists what each flag does, stdout = data, stderr = status messages (the `print("Report written to ...")` line is already stdout — acceptable since it names the artifact path).
- Follows `python-project-conventions` — Google docstrings, 80-char lines, absolute imports, import modules not names.
- Reuses `tiktoken` (already a project dependency). No new deps.

### Does not

- Does not touch `CLAUDE.md` or `.mantle/` artifact prose — that is issue 79's surface.
- Does not estimate output-token savings via live `claude -p` runs — issue 74 approach C.
- Does not add a config-driven sweep file — YAGNI for two surfaces.
- Does not migrate existing single-surface reports — they remain readable as before.
- Does not rewrite commands that never emit output (pure state-mutation commands like `bug.md`, `idea.md` — if they don't render user-facing reports, the Output Format template does not apply).
- Does not change the skill-compile pipeline (`mantle compile`) — trimming happens at vault source.

## Open questions

- None — the vault path is already discoverable via `mantle where` + `config.md:personal_vault`. Surface labeling by basename is sufficient.