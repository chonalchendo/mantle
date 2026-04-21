---
date: '2026-04-21'
author: 110059232+chonalchendo@users.noreply.github.com
title: Slim down build pipeline + condense retrospective/review into AI-surfaced learnings
source: user
status: open
tags:
- type/inbox
- status/open
---

Get rid of sprint-style outputs (confidence delta, what-went-well, harder-than-expected, recommendations) — too token-heavy. Condense into a small concise learnings file emitted by the AI at the end of the build pipeline (like what we already have). Review whole pipeline: add-issue -> shape-issue -> plan-stories -> implement -> simplify -> verify -> review -> retrospective is too much. Keep add-issue (backlog) and shape-issue. Question whether plan-stories is needed if shaping is thorough enough. Keep implement, simplify (AI code is bloated), and verify (needs to actually work). Drop review and retrospective as mandatory steps — painful each time; the valuable part is surfaced learnings, which the AI can emit itself to inform future sessions without two extra human-driven steps. Learnings should be able to surface at any point in the pipeline.