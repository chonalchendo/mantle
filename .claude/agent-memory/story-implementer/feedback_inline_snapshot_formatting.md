---
name: inline-snapshot formatting warning is harmless
description: "inline-snapshot is not able to format your code" on --inline-snapshot=create is fine; ruff reformats on `just fix`
type: feedback
---

Running `uv run pytest --inline-snapshot=create` emits "inline-snapshot is not able to format your code" and suggests installing `inline-snapshot[black]`. This is harmless in Mantle.

**Why:** The snapshot literal gets inserted unformatted, but Mantle's toolchain is ruff (not black). Running `just fix` formats the file consistently with the rest of the suite afterwards.

**How to apply:** Ignore the warning after running `--inline-snapshot=create`; always follow up with `just fix` (or `just check` to catch the reformat) before reporting DONE. Do NOT add `inline-snapshot[black]` just to silence it.
