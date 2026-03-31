"""Content sanitization for saved artifacts.

Strips internal drafting blocks (``<analysis>``) and other
transient markup before content is persisted to ``.mantle/``.
"""

from __future__ import annotations

import re


def strip_analysis_blocks(content: str) -> str:
    """Remove ``<analysis>...</analysis>`` scratchpad blocks.

    The ``<analysis>`` pattern is used by design commands as an
    internal drafting scratchpad that improves synthesis quality.
    These blocks have no value once the final output is written
    and should not be persisted.

    Also cleans up any resulting double-blank-line runs.

    Args:
        content: Raw content that may contain analysis blocks.

    Returns:
        Content with analysis blocks removed.
    """
    cleaned = re.sub(
        r"<analysis>[\s\S]*?</analysis>",
        "",
        content,
    )
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
