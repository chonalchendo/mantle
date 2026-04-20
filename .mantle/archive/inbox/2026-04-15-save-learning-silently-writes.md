---
date: '2026-04-15'
author: 110059232+chonalchendo@users.noreply.github.com
title: save-learning silently writes after issue archived
source: ai
status: promoted
tags:
- type/inbox
- status/promoted
---

save_learning (core + CLI) does not call find_issue_path/issue_exists — after transition-issue-approved archives an issue, save-learning --issue NN still succeeds silently and drops a learning into .mantle/learnings/ even though nothing remains to link to. Surfaced by tests/test_staleness_regressions.py::TestArchiveSideEffects::test_save_learning_after_archive_fails_clearly (currently xfail). Fix: have save_learning check issues.find_issue_path first and fail loudly, or explicitly look up archive/issues/ and annotate the learning.