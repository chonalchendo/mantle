---
name: Flag story internal inconsistencies before blindly following
description: Stories sometimes say "keep X unchanged" while also specifying a production change that invalidates X — apply the story's own rationale symmetrically
type: feedback
---

When a story lists both "drop this dead write" and "keep these tests unchanged", check whether any of the kept tests actually exercise the dropped write. If they do, the story has an internal contradiction — delete the test in line with the story's own rationale, not the literal list.

**Why:** Issue 47 story 1 said to drop `_update_config_at(local, storage_mode='local')` as a dead write and explicitly said to keep `TestMigrateToLocal` unchanged — but `TestMigrateToLocal::test_updates_config` asserted `"storage_mode: local"` appeared in config after migration, exercising exactly the dropped write. The story's rationale ("symmetric cleanup") applied to the test too; the author overlooked it.

**How to apply:** When a test fails *only because the story's own production change removed the behavior it asserted*, the test is obsolete. Delete it, note it in the concerns, and move on. Don't try to preserve a test whose target behavior the story itself eliminated.
