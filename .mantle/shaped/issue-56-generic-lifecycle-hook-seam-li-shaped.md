---
issue: 56
title: Generic lifecycle hook seam (Linear/Jira as first examples)
approaches:
- 'A: Sync shell dispatch, package-data examples, show-hook-example CLI'
- 'B: Async/fire-and-forget dispatch, examples in repo root'
- 'C: Python entry-point plugins (rejected — violates seam principle)'
chosen_approach: 'A: Sync shell dispatch, package-data examples, show-hook-example CLI'
appetite: batch
open_questions:
- Per-script timeout — default 30s is a guess. Confirm in implementation; easy to
  tune later via `hooks.timeout:` config key (not in this issue).
- `story-status-changed` event (flagged in brainstorm as "if cheap"). Deferred;
  not in AC#2 list. Revisit when a user asks.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-18'
updated: '2026-04-18'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Shaping Context

The brainstorm (`.mantle/brainstorms/2026-04-12-jira-integration-via-hook-seam.md`)
already chose **B2 — hook + examples repo** over "pure hook dispatch" and
"typed integration config". This shaping round refines *how* to implement B2:
sync vs async, where example scripts live, what the dispatcher module looks
like.

Key constraints carried from the brainstorm and `product-design.md`:

- Mantle never imports a tracker library, never holds credentials, never
  knows which tool is on the other end (seam principle).
- Works for both global `~/.mantle/` and per-project `.mantle/` — resolution
  via `mantle where`.
- Hook failures are fail-open (warn, continue) — a broken tracker integration
  must not block mantle's workflow.
- Missing hook = silent no-op.

## Out-of-band scope flag (important)

Three of the 12 acceptance criteria require live credentials against real
external services:

- AC7: `linear.sh` works **end-to-end against a real Linear workspace**
- AC8: `jira.sh` works **end-to-end against a real Jira instance**
- AC9: `slack.sh` posts to a real **Slack incoming webhook**

The `/mantle:build` verification agent has no credentials for any of these.
It can verify **structural correctness**:

- Scripts exit 0 with sensible fake env variables matching the documented
  setup-header contract
- Scripts emit the documented tracker-specific commands (observed via `set -x`
  or by replacing the external CLI/curl with a logging stub)
- Positional args ($1 $2 $3) and exported env vars reach the script

True end-to-end verification (does `jira.sh` actually update a real Jira
ticket?) is a **manual human verification step** in `/mantle:review`. The
shaped doc flags this so the plan-stories step encodes structural tests in
the test plan and adds a "human-verifies" note to those three ACs rather
than promising the build pipeline will cover them.

This is the right scoping — mantle's seam is what this issue builds; tracker
authentication is explicitly delegated to the user's CLI tools' keychains.

## Approaches

### A: Sync shell dispatch, package-data examples, `show-hook-example` CLI  [CHOSEN]

**Shape**

- `core/hooks.py` — single deep module. Public interface:
  `dispatch(event: str, issue: int, status: str, title: str, project_dir: Path) -> None`.
  Internals: path resolution via `project.resolve_mantle_dir()`, `hooks_env:`
  parsing from `config.md` frontmatter (add the field to
  `_ConfigFrontmatter` in `core/project.py`), sync
  `subprocess.run(..., timeout=30)` with stderr captured, warn-and-continue
  on non-zero exit / timeout / OSError.

**Note on config storage**: this project stores config in `.mantle/config.md`
with YAML frontmatter (not `config.yml` as loosely worded in the issue
body). The seam principle is unchanged — mantle reads a dict of opaque
key/value pairs under `hooks_env:` (snake_case matches existing convention,
e.g. `personal_vault`, `verification_strategy`) and exports them as env
vars. The brainstorm's seam-principle language carries through.
- Call-sites in `core/issues.py` (after each transition returns success) and
  `core/shaping.py` (after `save_shaped_issue`). Four events:
  `issue-shaped`, `issue-implement-start`, `issue-verify-done`,
  `issue-review-approved`.
- Example scripts shipped as package data at
  `src/mantle/assets/hook_examples/{linear,jira,slack}.sh`. Each script has
  a setup header (install, auth, required env) as a comment block.
- New CLI subcommand `mantle show-hook-example NAME` prints the script to
  stdout. User redirects: `mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh && chmod +x ...`.
- README gets a "Lifecycle hooks" section (convention, event list, arg
  contract, env passthrough, examples pointer).

**Tradeoffs**

- Sync blocks the transition command for up to `timeout=30s`. Acceptable
  because the normal path is a sub-second curl/CLI call; pathological
  slowdowns are visible and users will fix their hook rather than live with
  a slow workflow.
- `show-hook-example` as a stdout-print command (rather than a
  copy-to-hooks-dir command) keeps mantle out of the business of deciding
  *which* event a user wants to bind each example to. The script's header
  documents suggested event bindings; the user picks.
- Package-data examples vs repo-root `examples/` dir: package-data is what
  PyPI-installed users can access. A repo-root dir wouldn't ship.

**Appetite**

- batch (not small batch). Scope is 1 new core module + 4 call-site edits +
  1 new CLI command + 3 shell scripts + 1 README section + 6+ tests. The
  new module is the centre of gravity; everything else is light wiring.

### B: Async/fire-and-forget dispatch

- `subprocess.Popen()` with `start_new_session=True`, no wait. Faster
  workflow; hook errors are invisible.
- Rejected for the default. The whole point of the seam is that users
  *want* to see when their Jira push fails — else they sync-drift and lose
  trust in the integration. Sync-with-warning is the louder signal.
- Could become a future opt-in (`hooks.async: true` in config) if users
  explicitly want fire-and-forget for slow hooks. Not in this issue.

### C: Python entry-point plugins

- `pyproject.toml` entry_points that let users register Python callables as
  hook handlers.
- **Rejected** — violates the seam principle. The whole point is that
  mantle never imports a tracker library. Shell-out is the contract;
  Python plugins drag us toward plugin-framework territory where a
  misbehaving plugin can crash the CLI process.

## Rationale for A

- B2 from the brainstorm is a "small code surface + big leverage" play.
  Approach A keeps the code surface small (one deep module) while making
  the UX first-class (cli-discoverable examples, sync errors surfaced).
- Deep module per software-design-principles skill: `core/hooks.py`
  hides subprocess wiring, env-passthrough parsing, error handling, path
  resolution. Callers get `hooks.dispatch(event, issue, status, title,
  project_dir)` — four args, no knobs.
- Fits the existing CLI-as-thin-layer pattern (system-design.md): core
  does the work; cli just routes.
- Examples as package data survives `uv tool install mantle-ai` — a
  repo-root `examples/` wouldn't.
- `show-hook-example` (stdout) avoids mantle prescribing the event binding
  — the script's header comments document "typical" use; user chooses.

## Code design

### New / changed modules

- `src/mantle/core/hooks.py` **(new)** — `dispatch()` plus private helpers
  `_resolve_hook_script()`, `_load_hooks_env()`. All filesystem and
  subprocess logic is hidden here. Logs warnings via the project's existing
  rich console (match `cli/verify.py` pattern).
- `src/mantle/core/issues.py` — after the existing transition functions
  return a written path, call `hooks.dispatch(event, issue, new_status,
  title, project_dir)`. Four insertion points (one per transition).
- `src/mantle/core/shaping.py` — after `save_shaped_issue` succeeds,
  dispatch `issue-shaped` with the shaped issue's number, status, title.
- `src/mantle/cli/main.py` — new command `show-hook-example NAME` under
  the "Setup & plumbing" group. Delegates to
  `cli/hooks.py::run_show_hook_example(name: str)`.
- `src/mantle/cli/hooks.py` **(new)** — CLI wrapper that reads the
  requested script via `importlib.resources.files("mantle.assets.hook_examples")`
  and prints to stdout.
- `src/mantle/assets/__init__.py` + `src/mantle/assets/hook_examples/__init__.py`
  **(new, empty)** — makes scripts importable as package data.
- `src/mantle/assets/hook_examples/{linear,jira,slack}.sh` **(new)** — each
  with a setup-header comment block documenting: install CLI, authenticate,
  required env vars, and the event this script is a suggested binding for.
- `pyproject.toml` — ensure `tool.hatch.build.targets.wheel` (or whatever
  the build tool uses) includes `*.sh` under `src/mantle/assets/`.
- `README.md` — new "Lifecycle hooks" section.

### Hook contract (documented in README + core docstrings)

- Script path: `<mantle-dir>/hooks/on-<event>.sh`
- Positional args: `$1=<issue-number>`, `$2=<new-status>`, `$3=<issue-title>`
- Env: user's existing env + every key/value under `hooks_env:` in the
  frontmatter of `<mantle-dir>/config.md`
- Exit: 0 = success (silent); non-zero = warn-and-continue
- Missing script = no-op (silent, not a warning)
- Timeout: 30s per script (timeouts logged as warnings)

### Events (fixed list for this issue)

| Event | Emitted after | Status at emission |
|---|---|---|
| `issue-shaped` | `save_shaped_issue` | issue's current status (`planned` → `shaped` likely) |
| `issue-implement-start` | `transition_to_implementing` | `implementing` |
| `issue-verify-done` | `transition_to_verified` | `verified` |
| `issue-review-approved` | `transition_to_approved` | `approved` |

### Fits architecture by

- `core/hooks.py` is pure library code; no CLI imports.
- CLI module only exposes `show-hook-example`; CLI never dispatches hooks
  directly — it calls `core/*` which in turn calls `core/hooks.dispatch()`.
- Uses existing `project.resolve_mantle_dir()` for path resolution (same
  mechanism `mantle where` uses), so global vs per-project works for free.
- `hooks_env:` parsing uses the existing `_ConfigFrontmatter` pydantic
  model in `core/project.py` — add one new optional field
  `hooks_env: dict[str, str] | None = None`. Mantle never interprets
  individual keys.
- Tests sit in `tests/core/test_hooks.py` (mirrors source layout per
  CLAUDE.md). CLI wrapper tests in `tests/cli/test_hooks.py`.

### Does not

- Does not add async dispatch (deferred to a future opt-in if needed).
- Does not add a Python plugin entry-point system (violates seam).
- Does not emit a `story-status-changed` event (not in AC list).
- Does not auto-copy example scripts into `<mantle-dir>/hooks/` (user opts
  in explicitly via `mantle show-hook-example …`).
- Does not read or interpret any tracker-specific config keys — only
  passes `hooks.env:` through as env vars.
- Does not attempt live-auth verification in automated tests — AC7/8/9
  "real workspace" claims are human-verified in `/mantle:review`.
- Does not wire up the Claude Code session hooks at
  `claude/hooks/*.sh` — those are a different system (Claude Code's own
  hook mechanism); mantle's lifecycle hooks are separate.

## Verification plan preview (for plan-stories to expand)

Automated (build pipeline + `just check` will cover):

- Unit tests for `core/hooks.py`: dispatch with present script (mocked
  `subprocess.run`), missing script no-op, non-zero exit warns-not-raises,
  timeout warns-not-raises, env passthrough from `hooks.env:` in fixture
  `config.yml`, positional arg order.
- Integration test: actual `.sh` script in `tmp_path` exits 0, writes a
  marker file, test asserts the marker and the env vars were visible.
- Integration test: each shipped example script executes successfully
  with a fake env matching its documented setup header and a stubbed-out
  external CLI (e.g., `acli` replaced by a no-op in `$PATH` via
  `monkeypatch`). Asserts the script reaches its commit point (exit 0)
  and emits the expected args to the stub.
- CLI test: `mantle show-hook-example linear` prints the file contents;
  unknown name exits non-zero with a useful error.
- Call-site tests: each transition function's test verifies
  `hooks.dispatch` was called once with the right event + args.

Manual (human-verifies, noted on acceptance criteria):

- AC7: user runs `linear.sh 42 verified "demo"` against their own Linear
  workspace; confirms the ticket updates.
- AC8: same for `jira.sh` against a real Jira instance.
- AC9: same for `slack.sh` against a real webhook URL.

## Open questions

- Per-script timeout — default 30s is a guess. Easy to tune later via
  a `hooks.timeout:` config key; not in this issue.
- `story-status-changed` event was flagged in the brainstorm as "if
  cheap". Deferred — not in AC#2's list and adds a fifth call-site.
- Does issue 42 (report-to-GitHub) survive as its own issue, or collapse
  into "provide a `github.sh` example"? Not decided in this shape; will
  revisit after issue 56 lands.
