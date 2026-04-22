---
issue: 88
title: 'story-1: append-after-section key-matching'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-22'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

append_after_section silently records 0 for 'Before' when per-surface dict keys do not match the Before report's ### headings. There is no key-mismatch error. Story 2 must pass the same path list in the same order to the Before and After runs, so basenames match. If a future caller wants to rename surfaces between runs, that is a feature gap — add an explicit mapping arg rather than tolerating silent zero-fill.