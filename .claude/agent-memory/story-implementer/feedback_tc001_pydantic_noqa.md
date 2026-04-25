---
name: TC001 noqa for pydantic cross-module field types
description: When a core module defines pydantic models with fields typed as other core module types, ruff TC001 flags those imports; suppress with noqa TC001 — moving them under TYPE_CHECKING breaks pydantic at runtime.
type: feedback
---

When a `core/` module defines frozen pydantic models whose field types reference classes from other `core/` modules (e.g. `issues.IssueNote | None`, `telemetry.BuildReport`), ruff TC001 flags those imports as annotation-only and suggests moving them under TYPE_CHECKING.

**Do not move them.** With `from __future__ import annotations`, all annotations are lazy strings. Pydantic v2 resolves them via `get_type_hints()` at model-construction time — which requires the modules to be importable in the global namespace, not just under TYPE_CHECKING.

The fix is `# noqa: TC001` on the import line:
```python
from mantle.core import issues, project, stories, telemetry  # noqa: TC001
```

**Why:** Moving the imports under TYPE_CHECKING causes pydantic `ValidationError` or `NameError` at runtime when constructing model instances, because the type annotations can't be resolved.

**How to apply:** Whenever a new `core/` module defines pydantic BaseModel subclasses with cross-module field types, add `# noqa: TC001` to that import. This is expected and not a code-quality regression.
