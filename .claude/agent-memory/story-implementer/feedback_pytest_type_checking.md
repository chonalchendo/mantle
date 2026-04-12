---
name: pytest import under TYPE_CHECKING
description: When pytest types are only used in annotations (no @pytest.fixture), ruff TC002 requires moving the import under TYPE_CHECKING
type: feedback
---

If a test file only uses `pytest` for type annotations (e.g.,
`pytest.CaptureFixture[str]`, `pytest.MonkeyPatch`) and does NOT use
`@pytest.fixture` or any runtime pytest APIs, ruff's TC002 rule requires
moving `import pytest` under `if TYPE_CHECKING:` alongside other
annotation-only imports.

**Why:** ruff enforces TC002 across the project. Runtime usage of `@pytest.fixture` keeps pytest out of the TYPE_CHECKING block (see tests/cli/test_idea.py). Annotation-only usage does not.

**How to apply:** Before reporting DONE, run `just check`. If TC002 fires
on `import pytest`, check whether the module actually calls pytest at
runtime. If not, move the import under `TYPE_CHECKING`.
