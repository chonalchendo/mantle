"""Save-decision command — persist a structured decision record."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import decisions

console = Console()


def run_save_decision(
    *,
    topic: str,
    decision: str,
    alternatives: tuple[str, ...],
    rationale: str,
    reversal_trigger: str,
    confidence: str,
    reversible: str,
    scope: str,
    project_dir: Path | None = None,
) -> None:
    """Save a decision record and print confirmation.

    Args:
        topic: Decision topic (slugified for filename).
        decision: The decision text.
        alternatives: Alternatives considered.
        rationale: Why this was chosen.
        reversal_trigger: What would change this decision.
        confidence: Confidence rating as "N/10".
        reversible: Reversibility (high / medium / low).
        scope: Decision scope.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    note, path = decisions.save_decision(
        project_dir,
        topic=topic,
        decision=decision,
        alternatives=list(alternatives),
        rationale=rationale,
        reversal_trigger=reversal_trigger,
        confidence=confidence,
        reversible=reversible,
        scope=scope,
    )

    console.print()
    console.print(f"[green]Decision saved to {path.name}[/green]")
    console.print()
    console.print(f"  Topic:      {note.topic}")
    console.print(f"  Scope:      {note.scope}")
    console.print(f"  Confidence: {note.confidence}")
    console.print(f"  Reversible: {note.reversible}")
