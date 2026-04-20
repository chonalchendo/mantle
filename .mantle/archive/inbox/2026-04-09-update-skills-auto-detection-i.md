---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: update-skills auto-detection is noisy / irrelevant matches
source: ai
status: promoted
tags:
- type/inbox
- status/promoted
---

For issue-45 (a one-function fix in core/issues.py for issue numbering), mantle update-skills --issue 45 matched DuckLake, cyclopts, CLI design best practices, and Python package structure. DuckLake has zero relevance. The matcher likely over-weights slug token similarity over semantic relevance. Consider: (a) add a confidence threshold, (b) have the matcher read the issue description not just title/slug, (c) or have the build pipeline filter matches by domain.