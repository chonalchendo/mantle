---
title: Contextual CLI errors with recovery suggestions
status: implementing
slice:
- cli
- tests
story_count: 2
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- DuckDB Best Practices and Optimisations
- Python 3.14
- Python package structure
- SQLMesh Best Practices
- Software Design Principles
- cyclopts
- docker-compose-python
- edgartools
- fastapi
- pydantic-discriminated-unions
- pydantic-project-conventions
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/implementing
---

## Parent PRD

product-design.md, system-design.md

## Why

When mantle CLI commands fail, errors show what went wrong but not how to fix it. Users hit a wall and have to guess the right recovery action. Colin's CLI demonstrates a better pattern: every error includes a recovery path ("Run 'colin init' to create a new project", "Use -f to confirm"). This reduces friction, especially for new users and automation pipelines.

## What to build

A shared error formatting utility and migration of all existing CLI error paths to use it.

1. **Error utility** — a module in `src/mantle/cli/` that provides a function for consistent error output: Rich `[red]Error:[/]` prefix to stderr, with a dim-styled recovery suggestion on the next line.
2. **Error path audit** — identify all existing CLI error paths (sys.exit, raised exceptions, print-based errors) and migrate them to use the shared utility with appropriate recovery suggestions.
3. **Recovery suggestion catalogue** — each error path gets a specific, actionable suggestion (e.g., "Run `mantle init` to create a project", "Check issue number with `mantle list-issues`").

### Flow

1. User runs a mantle CLI command that fails (e.g., `mantle compile` outside a project)
2. Error is printed to stderr with `[red]Error:[/]` prefix and clear message
3. Below the error, a dim-styled recovery suggestion tells the user what to do next
4. Exit code is non-zero

## Acceptance criteria

- [ ] A shared error formatting utility exists in `src/mantle/cli/` that outputs errors to stderr with Rich `[red]Error:[/]` prefix and a dim-styled recovery suggestion
- [ ] All existing CLI error paths use the shared utility (no raw `print` or `sys.exit` for errors)
- [ ] Every error includes a recovery suggestion (e.g., "Run `mantle init` to create a project", "Check the issue number with `mantle --help`")
- [ ] A test verifies error output goes to stderr and includes the recovery hint format
- [ ] `just check` passes

## Blocked by

None

## User stories addressed

- As a mantle user, I want CLI errors to tell me what to do next so that I don't have to guess the recovery action when a command fails.
- As a developer building automation around mantle, I want errors on stderr with consistent formatting so that I can parse and handle them programmatically.