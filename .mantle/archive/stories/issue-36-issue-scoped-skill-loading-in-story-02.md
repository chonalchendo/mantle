---
issue: 36
title: CLI --issue flag for compile and --skills-required for save-issue
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer using the mantle CLI, I want to compile skills scoped to a specific issue and declare skills when saving issues so that the build pipeline can target skill compilation.

## Depends On

Story 1 — requires the skills_required field on IssueNote and the issue parameter on compile_skills.

## Approach

Add --issue N flag to the compile CLI command and --skills-required flag to save-issue. These are thin CLI wrappers that pass through to the core functions modified in Story 1. Follow existing CLI patterns in main.py using cyclopts Parameter annotations.

## Implementation

### src/mantle/cli/main.py (modify)

1. Update compile_command to accept --issue:

\`\`\`python
@app.command(name="compile")
def compile_command(
    if_stale: Annotated[...] = False,
    issue: Annotated[
        int | None,
        Parameter(
            name="--issue",
            help="Compile only skills relevant to this issue number.",
        ),
    ] = None,
    path: Annotated[...] = None,
    target: Annotated[...] = None,
) -> None:
\`\`\`

Pass issue to compile_cmd.run_compile().

2. Update save_issue_command to accept --skills-required:

\`\`\`python
skills_required: Annotated[
    tuple[str, ...],
    Parameter(
        name="--skills-required",
        help="Required skill name (repeatable).",
    ),
] = (),
\`\`\`

Pass skills_required through to issues.run_save_issue().

### src/mantle/cli/compile_cmd.py (modify)

Update run_compile to accept and pass issue parameter:

\`\`\`python
def run_compile(
    if_stale: bool = False,
    project_dir: Path | None = None,
    target_dir: Path | None = None,
    issue: int | None = None,
) -> None:
\`\`\`

Pass issue to compiler.compile() and compiler.compile_if_stale().

### src/mantle/cli/issues.py (modify)

Update run_save_issue to accept and pass skills_required parameter.

### src/mantle/core/compiler.py (modify)

Thread issue parameter through compile() and compile_if_stale():

\`\`\`python
def compile(
    project_dir: Path,
    target_dir: Path | None = None,
    issue: int | None = None,
) -> list[str]:
    # ... existing code ...
    skills.compile_skills(project_dir, issue=issue)
    # ...

def compile_if_stale(
    project_dir: Path,
    target_dir: Path | None = None,
    issue: int | None = None,
) -> list[str] | None:
    # ... existing code ...
    return compile(project_dir, target_dir, issue=issue)
\`\`\`

#### Design decisions

- **--issue on compile**: Mirrors the existing --issue pattern on other commands (update-skills, transition-issue-implementing, etc.)
- **--skills-required on save-issue**: Follows the repeatable tuple pattern of --slice and --blocked-by

## Tests

### tests/cli/test_compile_cmd.py (modify or create)

- **test_compile_passes_issue_to_core**: Call run_compile with issue=5. Assert compiler.compile is called with issue=5.

### tests/cli/test_issues.py (modify)

- **test_save_issue_with_skills_required**: Call run_save_issue with skills_required. Assert the saved issue has skills_required in frontmatter.