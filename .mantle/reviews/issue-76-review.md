---
issue: 76
title: init-vault silently skips linking when vault directory already exists
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-19'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 76

**init-vault silently skips linking when vault directory already exists**

## Criteria

- ✓ **Running mantle init-vault PATH when PATH already contains all four subdirs records personal_vault: PATH in the current project's .mantle/config.md without raising.** [approved] — passed: true
- ✓ **CLI prints a message indicating the existing vault was linked (e.g., Linked existing vault at PATH), not Nothing to do.** [approved] — passed: true
- ✓ **Creating a brand-new vault (fresh path) still creates the four subdirs and links the project — no regression.** [approved] — passed: true
- ✓ **Regression test covers the multi-project share flow: Project A creates + links, Project B re-links to the same path, and Project B's config.md ends up populated.** [approved] — passed: true
