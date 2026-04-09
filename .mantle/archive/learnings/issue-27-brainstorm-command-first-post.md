---
issue: 27
title: Brainstorm command — first post-setup feature
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-04'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Design-first approach**: The critical-thinking session before any code made implementation smooth. By the time stories were written, the design was clear and well-validated.
- **Pattern reuse**: Modelling core/brainstorm.py after core/challenge.py and core/research.py meant implementing agents could follow existing patterns and complete first-try with no retries.
- **Story specificity**: Stories included exact file paths, function signatures, and test cases. All 3 story agents completed with STATUS: DONE on first attempt — 19 new tests, 856 total passing.

## Harder Than Expected

- **Vault/compile infrastructure**: The vault wasn't linked to the project (init-vault bug: won't re-link existing vault directories). The status.md.j2 template had a pre-existing bug (undefined recent_decisions variable). Both blocked compilation and required manual fixes across 3 file locations (source, .venv, installed package).
- **Status transitions**: Issue status had to be manually transitioned (planned → implementing → verified) because the implement command doesn't manage the issue status machine. Felt like unnecessary ceremony.

## Wrong Assumptions

- **brainstorms/ directory**: Assumed it would be pre-created by mantle init. It's not in SUBDIRS — gets lazily created by vault.write_note. Should be added to SUBDIRS for consistency with other directories (issues/, challenges/, research/).

## Recommendations

1. **File a bug for init-vault not re-linking existing vaults** — will hit every user who creates a vault before linking it. The fix: if vault exists but config.md doesn't have the path, just link it.
2. **Add brainstorms/ to project.py SUBDIRS** — consistency with other artifact directories.
3. **Automate status transitions in implement command** — the planned → implementing transition should happen automatically when implementation starts, not require manual CLI calls.
4. **Keep the pattern-reuse approach** — when a new module follows an existing module's exact pattern, implementation agents are significantly more reliable. Always identify the reference module in story specs.