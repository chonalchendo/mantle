---
date: '2026-04-16'
author: 110059232+chonalchendo@users.noreply.github.com
title: Benchmark loop before /mantle:add-skill save
source: ai
status: open
tags:
- type/inbox
- status/open
---

Inspired by Anthropic's Skill Creator: run skill-under-construction against 3-5 sample prompts, inspect failures, refine the instructions, then save. Today /mantle:add-skill saves on author intent alone, so skills can ship vague triggers or missing anti-patterns without catching it. Revisit when an authored skill is found to have underperformed in practice (concrete failure mode, not speculation).