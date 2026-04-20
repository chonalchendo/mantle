---
name: cyclopts app() always sys.exit(0) on success
description: main_module.app() calls sys.exit(0) after any None-returning command; tests must handle this
type: feedback
---

When invoking `main_module.app(...)` in-process for a command that returns `None`, cyclopts unconditionally calls `sys.exit(0)` after the function completes. This raises `SystemExit: 0`.

Tests must wrap the call:

```python
with pytest.raises(SystemExit) as exc_info:
    main_module.app("flip-ac --issue 1 --ac-id ac-01 --pass --path ...")
assert exc_info.value.code == 0
```

**Why:** cyclopts `_result_action.py` maps `None` return to `sys.exit(0)` regardless of exit action mode. Omitting the wrapper causes the test to fail with `SystemExit: 0` even though the command succeeded.

**How to apply:** Any CLI-path test that calls `main_module.app(...)` in-process (not via subprocess) for a command that returns `None` needs `pytest.raises(SystemExit)` with a `.code == 0` assertion. Error paths (sys.exit(1)) are already handled this way; success paths need the same treatment.
