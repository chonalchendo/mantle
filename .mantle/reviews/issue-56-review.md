---
issue: 56
title: Generic lifecycle hook seam (Linear/Jira as first examples)
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-18'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 56

**Generic lifecycle hook seam (Linear/Jira as first examples)**

## Criteria

- ✓ **Mantle invokes <mantle-dir>/hooks/on-<event>.sh on each emitted lifecycle event with documented positional args (issue id, new status, issue title)** [approved] — passed: true
- ✓ **Lifecycle events emitted cover: issue-shaped, issue-implement-start, issue-verify-done, issue-review-approved** [approved] — passed: true
- ✓ **hooks.env: keys from config.yml are exported as environment variables to the hook process** [approved] — passed: true
- ✓ **Hooks directory resolution works for both global ~/.mantle/ and per-project .mantle/ via mantle where** [approved] — passed: true
- ✓ **Missing hook script is a no-op (no error, no warning noise)** [approved] — passed: true
- ✓ **Hook script failures log a warning but do not block mantle's workflow** [approved] — passed: true
- ✓ **Shipped example: linear.sh works end-to-end against a real Linear workspace (GraphQL via curl)** [approved] — passed: true
- ✓ **Shipped example: jira.sh works end-to-end against a real Jira instance (via acli)** [approved] — passed: true
- ✓ **Shipped example: slack.sh posts a message to a Slack incoming webhook** [approved] — passed: true
- ✓ **Each example script has a setup header documenting install + auth + required env vars** [approved] — passed: true
- ✓ **README section documents the hook authoring convention** [approved] — passed: true
- ✓ **Covered by tests (event emission, arg passing, env passthrough, missing-hook no-op, failure-does-not-block)** [approved] — passed: true
