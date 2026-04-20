---
date: '2026-04-20'
author: 110059232+chonalchendo@users.noreply.github.com
title: flip-ac --pass flag errors; default-true works
source: ai
status: promoted
tags:
- type/inbox
- status/promoted
---

verify.md instructs agents to run 'mantle flip-ac --issue N --ac-id X --pass', but that currently errors with 'Unknown option: "--pass"'. The default is already passes=True, so running without --pass works, and --fail works. Two fixes possible: (a) make cyclopts accept --pass explicitly (investigate --pass/--fail negation syntax), or (b) update verify.md to drop the --pass form and just say 'mantle flip-ac --issue N --ac-id X' for pass. Surfaced during /mantle:build 77 verify step.