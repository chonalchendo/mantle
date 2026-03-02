"""Mantle CLI entry point."""

from pathlib import Path  # noqa: TC003 — needed at runtime for cyclopts
from typing import Annotated

from cyclopts import App, Parameter

from mantle.cli import (
    adopt,
    challenge,
    decisions,
    idea,
    init,
    init_vault,
    install,
    learning,
    product_design,
    research,
    session,
    shaping,
    skills,
    system_design,
)
from mantle.cli import (
    compile as compile_cmd,
)

app = App(name="mantle", help="AI workflow engine with persistent context.")


@app.command(name="init")
def init_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory to initialize. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Initialize .mantle/ in the current project repository."""
    init.run_init(path)


@app.command(name="init-vault")
def init_vault_command(
    path: Annotated[
        Path,
        Parameter(
            name="--path",
            help="Directory for the personal vault (e.g. ~/vault).",
        ),
    ],
) -> None:
    """Create personal vault and link it to this project."""
    init_vault.run_init_vault(path)


@app.command(name="save-idea")
def save_idea_command(
    problem: Annotated[
        str,
        Parameter(
            name="--problem",
            help="The specific pain or friction that exists.",
        ),
    ],
    insight: Annotated[
        str,
        Parameter(
            name="--insight",
            help="What makes a new solution possible.",
        ),
    ],
    target_user: Annotated[
        str,
        Parameter(
            name="--target-user",
            help="Who this idea is for.",
        ),
    ],
    success_criteria: Annotated[
        tuple[str, ...],
        Parameter(
            name="--success-criteria",
            help="Measurable outcome (repeatable).",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing idea.md.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Capture a structured idea in .mantle/idea.md."""
    idea.run_save_idea(
        problem=problem,
        insight=insight,
        target_user=target_user,
        success_criteria=success_criteria,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-challenge")
def save_challenge_command(
    transcript: Annotated[
        str,
        Parameter(
            name="--transcript",
            help="Full challenge session transcript.",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a challenge session transcript to .mantle/challenges/."""
    challenge.run_save_challenge(
        transcript=transcript,
        project_dir=path,
    )


@app.command(name="save-research")
def save_research_command(
    focus: Annotated[
        str,
        Parameter(
            name="--focus",
            help="Research focus angle.",
        ),
    ],
    confidence: Annotated[
        str,
        Parameter(
            name="--confidence",
            help="Confidence rating (e.g. '7/10').",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Research note content.",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a research note to .mantle/research/."""
    research.run_save_research(
        focus=focus,
        confidence=confidence,
        content=content,
        project_dir=path,
    )


@app.command(name="save-product-design")
def save_product_design_command(
    vision: Annotated[
        str,
        Parameter(
            name="--vision",
            help="One-sentence product vision.",
        ),
    ],
    principles: Annotated[
        tuple[str, ...],
        Parameter(
            name="--principles",
            help="Non-negotiable truth / constraint (repeatable).",
        ),
    ],
    building_blocks: Annotated[
        tuple[str, ...],
        Parameter(
            name="--building-blocks",
            help="Essential primitive (repeatable).",
        ),
    ],
    prior_art: Annotated[
        tuple[str, ...],
        Parameter(
            name="--prior-art",
            help="Existing piece to combine or adopt (repeatable).",
        ),
    ],
    composition: Annotated[
        str,
        Parameter(
            name="--composition",
            help="How the building blocks assemble into a product.",
        ),
    ],
    target_users: Annotated[
        str,
        Parameter(
            name="--target-users",
            help="Specific user profile and context.",
        ),
    ],
    success_metrics: Annotated[
        tuple[str, ...],
        Parameter(
            name="--success-metrics",
            help="Measurable outcome (repeatable).",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing product-design.md.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a product design to .mantle/product-design.md."""
    product_design.run_save_product_design(
        vision=vision,
        principles=principles,
        building_blocks=building_blocks,
        prior_art=prior_art,
        composition=composition,
        target_users=target_users,
        success_metrics=success_metrics,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-revised-product-design")
def save_revised_product_design_command(
    vision: Annotated[
        str,
        Parameter(
            name="--vision",
            help="Updated product vision.",
        ),
    ],
    principles: Annotated[
        tuple[str, ...],
        Parameter(
            name="--principles",
            help="Updated non-negotiable truth (repeatable).",
        ),
    ],
    building_blocks: Annotated[
        tuple[str, ...],
        Parameter(
            name="--building-blocks",
            help="Updated essential primitive (repeatable).",
        ),
    ],
    prior_art: Annotated[
        tuple[str, ...],
        Parameter(
            name="--prior-art",
            help="Updated prior art (repeatable).",
        ),
    ],
    composition: Annotated[
        str,
        Parameter(
            name="--composition",
            help="Updated assembly description.",
        ),
    ],
    target_users: Annotated[
        str,
        Parameter(
            name="--target-users",
            help="Updated user profile.",
        ),
    ],
    success_metrics: Annotated[
        tuple[str, ...],
        Parameter(
            name="--success-metrics",
            help="Updated measurable outcome (repeatable).",
        ),
    ],
    change_topic: Annotated[
        str,
        Parameter(
            name="--change-topic",
            help="Short slug for the decision log.",
        ),
    ],
    change_summary: Annotated[
        str,
        Parameter(
            name="--change-summary",
            help="What changed (1-2 sentences).",
        ),
    ],
    change_rationale: Annotated[
        str,
        Parameter(
            name="--change-rationale",
            help="Why it changed (1-2 sentences).",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Revise product design and log the change."""
    product_design.run_revise_product_design(
        vision=vision,
        principles=principles,
        building_blocks=building_blocks,
        prior_art=prior_art,
        composition=composition,
        target_users=target_users,
        success_metrics=success_metrics,
        change_topic=change_topic,
        change_summary=change_summary,
        change_rationale=change_rationale,
        project_dir=path,
    )


@app.command(name="save-system-design")
def save_system_design_command(
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full system design document body.",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing system-design.md.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a system design document to .mantle/system-design.md."""
    system_design.run_save_system_design(
        content=content,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-revised-system-design")
def save_revised_system_design_command(
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full revised system design document body.",
        ),
    ],
    change_topic: Annotated[
        str,
        Parameter(
            name="--change-topic",
            help="Short slug for the decision log.",
        ),
    ],
    change_summary: Annotated[
        str,
        Parameter(
            name="--change-summary",
            help="What changed (1-2 sentences).",
        ),
    ],
    change_rationale: Annotated[
        str,
        Parameter(
            name="--change-rationale",
            help="Why it changed (1-2 sentences).",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Revise system design and log the change."""
    system_design.run_revise_system_design(
        content=content,
        change_topic=change_topic,
        change_summary=change_summary,
        change_rationale=change_rationale,
        project_dir=path,
    )


@app.command(name="save-decision")
def save_decision_command(
    topic: Annotated[
        str,
        Parameter(
            name="--topic",
            help="Decision topic (used in filename).",
        ),
    ],
    decision: Annotated[
        str,
        Parameter(
            name="--decision",
            help="The decision text.",
        ),
    ],
    alternatives: Annotated[
        tuple[str, ...],
        Parameter(
            name="--alternatives",
            help="Alternative considered (repeatable).",
        ),
    ],
    rationale: Annotated[
        str,
        Parameter(
            name="--rationale",
            help="Why this option was chosen.",
        ),
    ],
    reversal_trigger: Annotated[
        str,
        Parameter(
            name="--reversal-trigger",
            help="What would change this decision.",
        ),
    ],
    confidence: Annotated[
        str,
        Parameter(
            name="--confidence",
            help='Confidence rating (e.g. "8/10").',
        ),
    ],
    reversible: Annotated[
        str,
        Parameter(
            name="--reversible",
            help="Reversibility: high / medium / low.",
        ),
    ],
    scope: Annotated[
        str,
        Parameter(
            name="--scope",
            help="Decision scope.",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a decision record to .mantle/decisions/."""
    decisions.run_save_decision(
        topic=topic,
        decision=decision,
        alternatives=alternatives,
        rationale=rationale,
        reversal_trigger=reversal_trigger,
        confidence=confidence,
        reversible=reversible,
        scope=scope,
        project_dir=path,
    )


@app.command(name="save-adoption")
def save_adoption_command(
    vision: Annotated[
        str,
        Parameter(
            name="--vision",
            help="One-sentence product vision.",
        ),
    ],
    principles: Annotated[
        tuple[str, ...],
        Parameter(
            name="--principles",
            help="Non-negotiable truth (repeatable).",
        ),
    ],
    building_blocks: Annotated[
        tuple[str, ...],
        Parameter(
            name="--building-blocks",
            help="Essential primitive (repeatable).",
        ),
    ],
    prior_art: Annotated[
        tuple[str, ...],
        Parameter(
            name="--prior-art",
            help="Existing piece to adopt (repeatable).",
        ),
    ],
    composition: Annotated[
        str,
        Parameter(
            name="--composition",
            help="How the building blocks assemble.",
        ),
    ],
    target_users: Annotated[
        str,
        Parameter(
            name="--target-users",
            help="Inferred user profile.",
        ),
    ],
    success_metrics: Annotated[
        tuple[str, ...],
        Parameter(
            name="--success-metrics",
            help="Measurable outcome (repeatable).",
        ),
    ],
    system_design_content: Annotated[
        str,
        Parameter(
            name="--system-design-content",
            help="Full system design document body.",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing design documents.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save adopted design artifacts to .mantle/."""
    adopt.run_save_adoption(
        vision=vision,
        principles=principles,
        building_blocks=building_blocks,
        prior_art=prior_art,
        composition=composition,
        target_users=target_users,
        success_metrics=success_metrics,
        system_design_content=system_design_content,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-shaped-issue")
def save_shaped_issue_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number being shaped.",
        ),
    ],
    title: Annotated[
        str,
        Parameter(
            name="--title",
            help="Short title for the shaped issue.",
        ),
    ],
    approaches: Annotated[
        tuple[str, ...],
        Parameter(
            name="--approaches",
            help="Approach evaluated (repeatable).",
        ),
    ],
    chosen_approach: Annotated[
        str,
        Parameter(
            name="--chosen-approach",
            help="The selected approach name.",
        ),
    ],
    appetite: Annotated[
        str,
        Parameter(
            name="--appetite",
            help="Time/effort budget for this work.",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full shaping write-up body.",
        ),
    ],
    open_questions: Annotated[
        tuple[str, ...],
        Parameter(
            name="--open-questions",
            help="Unresolved question (repeatable).",
        ),
    ] = (),
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing shaped issue.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a shaped issue to .mantle/shaped/."""
    shaping.run_save_shaped_issue(
        issue=issue,
        title=title,
        approaches=approaches,
        chosen_approach=chosen_approach,
        appetite=appetite,
        content=content,
        open_questions=open_questions,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-learning")
def save_learning_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number this learning relates to.",
        ),
    ],
    title: Annotated[
        str,
        Parameter(
            name="--title",
            help="Short title for the learning.",
        ),
    ],
    confidence_delta: Annotated[
        str,
        Parameter(
            name="--confidence-delta",
            help="Confidence change (e.g. '+2', '-1').",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Structured reflection body.",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing learning.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a learning note to .mantle/learnings/."""
    learning.run_save_learning(
        issue=issue,
        title=title,
        confidence_delta=confidence_delta,
        content=content,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-session")
def save_session_command(
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Session log body (markdown).",
        ),
    ],
    commands_used: Annotated[
        tuple[str, ...],
        Parameter(
            name="--command",
            help="Command used during session (repeatable).",
        ),
    ] = (),
    project_dir: Annotated[
        Path | None,
        Parameter(
            name="--project-dir",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a session log to .mantle/sessions/."""
    session.run_save_session(
        content=content,
        commands_used=commands_used,
        project_dir=project_dir,
    )


@app.command(name="save-skill")
def save_skill_command(
    name: Annotated[
        str,
        Parameter(
            name="--name",
            help="Skill name (e.g. 'Python asyncio').",
        ),
    ],
    description: Annotated[
        str,
        Parameter(
            name="--description",
            help="What this skill covers and when it's relevant.",
        ),
    ],
    proficiency: Annotated[
        str,
        Parameter(
            name="--proficiency",
            help="Self-assessment (e.g. '7/10').",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Authored skill knowledge (markdown).",
        ),
    ],
    related_skills: Annotated[
        tuple[str, ...],
        Parameter(
            name="--related-skills",
            help="Related skill name (repeatable).",
        ),
    ] = (),
    projects: Annotated[
        tuple[str, ...],
        Parameter(
            name="--projects",
            help="Project using this skill (repeatable).",
        ),
    ] = (),
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing skill node.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a skill node to the personal vault."""
    skills.run_save_skill(
        name=name,
        description=description,
        proficiency=proficiency,
        content=content,
        related_skills=related_skills,
        projects=projects,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="compile")
def compile_command(
    if_stale: Annotated[
        bool,
        Parameter(
            name="--if-stale",
            help="Only recompile when source files have changed.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
    target: Annotated[
        Path | None,
        Parameter(
            name="--target",
            help="Output directory. Defaults to ~/.claude/commands/mantle/.",
        ),
    ] = None,
) -> None:
    """Compile vault context into Claude Code commands."""
    compile_cmd.run_compile(
        if_stale=if_stale,
        project_dir=path,
        target_dir=target,
    )


@app.command(name="install")
def install_command() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    install.run_install()


if __name__ == "__main__":
    app()
