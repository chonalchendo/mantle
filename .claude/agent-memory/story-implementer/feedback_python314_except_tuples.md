---
name: Python 3.14 bare except tuples
description: ruff format strips parens from `except (A, B):` on Py3.14 per PEP 758 — this is valid, not a bug
type: feedback
---

On Python 3.14+, `ruff format` will rewrite `except (KeyError, ValueError):` to `except KeyError, ValueError:` thanks to PEP 758 (parenthesis-free except). This looks like old Python 2 syntax but it IS valid on 3.14.

**Why:** Initially I assumed the formatter had introduced a bug by stripping the tuple parens. Actually this is a modern Python feature and the code runs correctly.

**How to apply:** If you see `except A, B:` after running `ruff format` on Py3.14+, do NOT "fix" it by wrapping in parens again — the formatter will undo it. Run the tests; if they pass, it's fine.
