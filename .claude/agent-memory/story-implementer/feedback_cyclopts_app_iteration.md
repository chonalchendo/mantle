---
name: Cyclopts app iteration yields strings
description: Iterating a cyclopts App yields registered name strings (including --help/--version), not command objects; use app[name] to get the sub-App with .group
type: feedback
---

Iterating `cyclopts.App` yields registered name strings like `"--help"`, `"-h"`, `"--version"`, and each command name. It does NOT yield command objects.

**Why:** First attempt at "iterate commands and check .group" failed because the iterator gives strings, and --help/--version appear as top-level entries without a group.

**How to apply:** In tests that introspect commands:
- Filter names with `if not name.startswith("-")` to skip `--help`/`--version`/`-h`.
- Fetch the sub-App via `app[name]`, then read `.group` (which is a tuple of `Group` objects).
- Example: `for name in app: if name.startswith("-"): continue; cmd = app[name]; assert cmd.group`
