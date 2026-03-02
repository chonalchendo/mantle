---
issue: 8
title: Jinja2 template rendering module (core/templates.py)
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Create `src/mantle/core/templates.py` — a thin wrapper around Jinja2 that loads `.j2` templates from a directory and renders them with a context dict. Uses `StrictUndefined` so missing variables fail loudly rather than rendering as empty strings.

### src/mantle/core/templates.py

```python
"""Jinja2 template rendering with strict variable checking."""
```

#### Functions

- `render_template(template_dir: Path, template_name: str, context: dict[str, Any]) -> str` — Load a Jinja2 environment rooted at `template_dir`, get the template by name, render with `context`, return the rendered string. Uses `jinja2.FileSystemLoader` and `jinja2.StrictUndefined`. Raises `jinja2.TemplateNotFound` if the template doesn't exist. Raises `jinja2.UndefinedError` if the context is missing a required variable.

- `find_templates(template_dir: Path) -> list[str]` — Return sorted list of `.j2` filenames in `template_dir`. Returns empty list if directory doesn't exist or contains no templates.

#### Imports

```python
from typing import Any, TYPE_CHECKING
import jinja2

if TYPE_CHECKING:
    from pathlib import Path
```

#### Design decisions

- **StrictUndefined over default Undefined.** Silent empty strings hide bugs. If a template references `{{ project }}` and the context doesn't provide it, that's a compilation error, not a graceful degradation.
- **No caching.** Compilation runs once per session (at most). Jinja2's built-in bytecode cache adds complexity without measurable benefit at this scale.
- **FileSystemLoader, not PackageLoader.** The template directory is resolved at runtime by the compiler module. Keeping the loader generic means templates can come from the package bundle or a test fixture directory.

## Tests

### tests/core/test_templates.py

All tests create a `tmp_path` fixture with `.j2` files written to it.

- **render_template**: renders `{{ name }}` with `{"name": "test"}` to `"test"`
- **render_template**: renders multi-line template with multiple variables
- **render_template**: renders Jinja2 control flow (`{% for %}`, `{% if %}`)
- **render_template**: raises `jinja2.TemplateNotFound` for missing template
- **render_template**: raises `jinja2.UndefinedError` for missing context variable
- **find_templates**: returns sorted `.j2` filenames
- **find_templates**: returns empty list when directory has no templates
- **find_templates**: returns empty list when directory doesn't exist
- **find_templates**: ignores non-`.j2` files
