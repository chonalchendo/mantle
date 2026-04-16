---
issue: 51
title: 'story-1: errors module import style'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-16'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

Call sites should use 'from mantle.cli import errors' then errors.exit_with_error(...) / errors.print_error(...). The module-level _stderr Console is private — don't reference it directly. Rich markup difference: new module uses '[red]Error:[/]' shorthand; existing sites use '[red]Error:[/red]' explicit-close. Both render identically.