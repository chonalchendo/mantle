---
date: '2026-04-20'
author: 110059232+chonalchendo@users.noreply.github.com
title: 'collect-issue-diff-stats: make source/test paths configurable for non-src/tests
  projects (e.g. dbt)'
source: user
status: promoted
tags:
- type/inbox
- status/promoted
---

Currently hardcoded to src/ and tests/ folders, which breaks for dbt projects (models/, tests/, seeds/, macros/) and other layouts. Needs a configurable way to declare which paths count as source vs test so diff stats work across project types.