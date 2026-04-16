---
issue: 49
title: tag-migration-stale-indexes
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-10'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Shaped approach was accurate** — taxonomy-aware prompt (approach C) was the right call. No scoring engine, no CLI migration command, just prompt rewrite + manual migration. Two stories, both completed first try with sonnet.
- **Tag consolidation produced real value** — 49 tags down to 41, with visible clustering: 3 scraping skills share `topic/scraping`, 8 finance skills share `domain/finance`, 2 pydantic skills share `topic/pydantic`. Indexes now show meaningful groups.
- **Model selection was correct** — sonnet handled both stories cleanly. Well-specified, single-file prompt changes and frontmatter edits don't need opus.

## Harder than expected

- **Stale index files in vault**: `mantle compile` generates new index notes but does not delete orphaned ones. After migrating tags, 9 stale index files remained in `test-vault/indexes/` for tags that no longer existed on any skill. User spotted them in Obsidian during human review. Verification didn't catch this because it checked `mantle list-tags` (which reads skill frontmatter) but not the index filesystem.

## Wrong assumptions

- **Assumed compile handles full index lifecycle**: the migration story said "run `mantle compile` to regenerate index notes" — but compile only creates/updates, never deletes. The cleanup path for removed tags was not traced.
- **Vault files outside git**: story 2's changes to vault skills couldn't be git-committed (vault lives at `~/test-vault/`, outside the repo). The build pipeline's commit step silently had nothing to commit. Not a bug, but the pipeline should note when vault-only changes don't produce a commit.

## Recommendations

1. **When migrating tags, explicitly delete orphaned index files.** Add a step to migration stories: "after compile, check `indexes/` for files matching old tag names and delete them." The human review caught this; verification should too.
2. **Consider adding `mantle compile --clean`** — a flag that auto-removes index files for tags no longer present on any skill. This is the systematic fix. Candidate for a future issue.
3. **Verification for vault changes should check the index directory**, not just `mantle list-tags`. Tags can be correct in frontmatter while stale indexes linger in the filesystem.