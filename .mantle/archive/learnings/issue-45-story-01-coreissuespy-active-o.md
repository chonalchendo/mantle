---
issue: 45
title: 'story-01: core/issues.py active-only vs archive-inclusive split'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-09'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## Pattern: active-only vs archive-inclusive scans must stay separate

`list_issues()` in `core/issues.py` is intentionally active-only because `count_issues()` uses it for an "active backlog count" shown in status displays. Any future function that needs to span both active and archive must bypass `list_issues()` and glob the archive dir separately — do NOT extend `list_issues()` with an include_archive flag.

## Gotcha: `_save` helper requires the git-identity @patch

In `tests/core/test_issues.py`, the `_save()` helper routes through `save_issue()` which calls `state.resolve_git_identity()`. Any test using `_save()` needs the `@patch("mantle.core.issues.state.resolve_git_identity", side_effect=_mock_git_identity)` decorator. Tests that write files directly (like the new `_create_archived_issue` helper) do NOT need the patch.

## Recommendation for future issues touching issue-numbering

If `find_issue_path` or `issue_exists` ever need to see archived issues too, apply the same "bypass list_issues, glob both dirs" approach. Watch out for the regex `re.compile(r"issue-(\d+)-.*\.md")` which requires a slug suffix — old numeric-only files like `issue-01.md` are invisible to it. If that ever becomes a problem, it is a separate bug fix.