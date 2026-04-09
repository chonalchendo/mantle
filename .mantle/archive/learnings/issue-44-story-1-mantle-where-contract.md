---
issue: 44
title: 'story-1: mantle where contract for prompt sweeps'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-09'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

**Pattern:** `mantle where` is the foundation of the prompt sweep. Stories 2-5 must use exactly the contract `MANTLE_DIR=$(mantle where)`. Output is one ANSI-free line, guaranteed absolute via explicit `.resolve()` in the wrapper (the core `resolve_mantle_dir` does NOT call resolve itself). Pure resolver — no side effects, no existence check, falls back to project-local even when no `.mantle/` exists. Each prompt must still handle missing-state messaging itself. Pre-existing ruff format issue in `src/mantle/core/issues.py` will trip `just check` for subsequent stories — run `just fix` if it surfaces.