---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: A/B test model/effort strategy across build pipeline stages
source: user
status: promoted
tags:
- type/inbox
- status/promoted
---

Currently story-implementer uses opus-high. Explore whether opus-high is only needed for shape-issue and plan-stories, while implementation uses a cheaper/faster model (haiku or sonnet). Goals: (1) reduce token cost, (2) speed up build pipeline. Want to A/B test strategies and compare output quality.