---
title: Report-to-GitHub command — file issues against the Mantle repo from any project
status: planned
slice:
- cli
- core
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

When users encounter bugs, missing features, or friction points while using Mantle in their own projects, there's no easy way to report them back to the Mantle repository. They have to context-switch to GitHub, remember the details, and manually file an issue. A /mantle:report command would capture structured feedback from any Mantle-powered project and file it directly to the mantle-ai GitHub issues list.

## What to build

A /mantle:report command that:

1. Captures a structured bug report or feature request (title, description, reproduction steps, severity)
2. Includes relevant context (Mantle version, Python version, OS)
3. Files it as a GitHub issue on the mantle-ai/mantle repository via the gh CLI

## Acceptance criteria

- As a user, I can run /mantle:report from any Mantle project to file a GitHub issue
- The command captures title, description, and category (bug/feature/friction)
- System context (Mantle version, Python version) is automatically included
- The issue is created on GitHub via gh CLI with appropriate labels
- Works without requiring the user to leave their terminal