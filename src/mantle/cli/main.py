"""Mantle CLI entry point."""

from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

from mantle import __version__
from mantle.cli import (
    adopt,
    brainstorm,
    bugs,
    builds,
    challenge,
    decisions,
    hooks,
    idea,
    inbox,
    init,
    init_vault,
    install,
    issues,
    knowledge,
    learning,
    product_design,
    research,
    review,
    scout,
    session,
    shaping,
    simplify,
    skills,
    storage,
    stories,
    system_design,
    verify,
)
from mantle.cli import (
    compile as compile_cmd,
)
from mantle.cli import (
    patterns as patterns_cli,
)
from mantle.cli.groups import GROUPS

app = App(
    name="mantle",
    help="AI workflow engine with persistent context.",
    version=__version__,
)


@app.command(name="init", group=GROUPS["setup"])
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


@app.command(name="init-vault", group=GROUPS["setup"])
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


@app.command(name="save-idea", group=GROUPS["idea"])
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


@app.command(name="save-challenge", group=GROUPS["idea"])
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


@app.command(name="save-brainstorm", group=GROUPS["idea"])
def save_brainstorm_command(
    title: Annotated[
        str,
        Parameter(
            name="--title",
            help="Short title for the brainstormed idea.",
        ),
    ],
    verdict: Annotated[
        str,
        Parameter(
            name="--verdict",
            help="Outcome: proceed, research, or scrap.",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full brainstorm session content.",
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
    """Save a brainstorm session to .mantle/brainstorms/."""
    brainstorm.run_save_brainstorm(
        title=title,
        verdict=verdict,
        content=content,
        project_dir=path,
    )


@app.command(name="save-research", group=GROUPS["idea"])
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
    no_state_update: Annotated[
        bool,
        Parameter(
            name="--no-state-update",
            help="Skip updating state.md (for sub-steps of other commands).",
        ),
    ] = False,
    issue: Annotated[
        int | None,
        Parameter(
            name="--issue",
            help=(
                "Issue number — save in issue-mode (no idea.md required, "
                "filename is issue-NN-<focus>.md)."
            ),
        ),
    ] = None,
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
        update_state=not no_state_update,
        project_dir=path,
        issue=issue,
    )


@app.command(name="save-product-design", group=GROUPS["design"])
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


@app.command(name="save-revised-product-design", group=GROUPS["design"])
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


@app.command(name="save-system-design", group=GROUPS["design"])
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


@app.command(name="save-revised-system-design", group=GROUPS["design"])
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


@app.command(name="save-decision", group=GROUPS["design"])
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


@app.command(name="save-adoption", group=GROUPS["design"])
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


@app.command(name="save-shaped-issue", group=GROUPS["planning"])
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


@app.command(name="save-story", group=GROUPS["planning"])
def save_story_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Parent issue number.",
        ),
    ],
    title: Annotated[
        str,
        Parameter(
            name="--title",
            help="Story title.",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full story body (markdown).",
        ),
    ],
    story: Annotated[
        int | None,
        Parameter(
            name="--story",
            help="Explicit story number (for overwrites).",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing story.",
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
    """Save a planned story to .mantle/stories/."""
    stories.run_save_story(
        issue=issue,
        title=title,
        content=content,
        story=story,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="update-story-status", group=GROUPS["impl"])
def update_story_status_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Parent issue number.",
        ),
    ],
    story: Annotated[
        int,
        Parameter(
            name="--story",
            help="Story number within the issue.",
        ),
    ],
    status: Annotated[
        str,
        Parameter(
            name="--status",
            help="New status: planned, in-progress, completed, blocked.",
        ),
    ],
    failure_log: Annotated[
        str | None,
        Parameter(
            name="--failure-log",
            help="Error details when marking blocked.",
        ),
    ] = None,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Update a story's status."""
    stories.run_update_story_status(
        issue=issue,
        story=story,
        status=status,
        failure_log=failure_log,
        project_dir=path,
    )


@app.command(name="save-issue", group=GROUPS["planning"])
def save_issue_command(
    title: Annotated[
        str,
        Parameter(
            name="--title",
            help="Issue title.",
        ),
    ],
    slice: Annotated[
        tuple[str, ...],
        Parameter(
            name="--slice",
            help="Layer touched (repeatable).",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full issue body (markdown).",
        ),
    ],
    blocked_by: Annotated[
        tuple[int, ...],
        Parameter(
            name="--blocked-by",
            help="Blocking issue number (repeatable).",
        ),
    ] = (),
    skills_required: Annotated[
        tuple[str, ...],
        Parameter(
            name="--skills-required",
            help="Required skill name (repeatable).",
        ),
    ] = (),
    verification: Annotated[
        str | None,
        Parameter(
            name="--verification",
            help="Per-issue verification override.",
        ),
    ] = None,
    issue: Annotated[
        int | None,
        Parameter(
            name="--issue",
            help="Explicit issue number (for overwrites).",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing issue.",
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
    """Save a planned issue to .mantle/issues/."""
    issues.run_save_issue(
        title=title,
        slice=slice,
        content=content,
        blocked_by=blocked_by,
        skills_required=skills_required,
        verification=verification,
        issue=issue,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="flip-ac", group=GROUPS["planning"])
def flip_ac_command(
    *,
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number containing the criterion.",
        ),
    ],
    ac_id: Annotated[
        str,
        Parameter(
            name="--ac-id",
            help="Criterion id to flip (e.g. ac-01).",
        ),
    ],
    passes: Annotated[
        bool,
        Parameter(
            name="--pass",
            negative="--fail",
            help="Mark the criterion as passing or failing.",
        ),
    ] = True,
    waive: Annotated[
        bool,
        Parameter(
            name="--waive",
            help="Waive the criterion (requires --reason).",
        ),
    ] = False,
    reason: Annotated[
        str | None,
        Parameter(
            name="--reason",
            help="Waiver rationale — required when --waive is set.",
        ),
    ] = None,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Flip one acceptance criterion's pass/fail state."""
    issues.run_flip_ac(
        issue=issue,
        ac_id=ac_id,
        passes=passes,
        waive=waive,
        reason=reason,
        project_dir=path,
    )


@app.command(name="list-acs", group=GROUPS["planning"])
def list_acs_command(
    *,
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to list criteria for.",
        ),
    ],
    json_output: Annotated[
        bool,
        Parameter(
            name="--json",
            help="Emit a JSON array instead of a table.",
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
    """Print an issue's structured acceptance criteria."""
    issues.run_list_acs(
        issue=issue,
        json_output=json_output,
        project_dir=path,
    )


@app.command(name="migrate-acs", group=GROUPS["planning"])
def migrate_acs_command(
    *,
    dry_run: Annotated[
        bool,
        Parameter(
            name="--dry-run",
            help="Report would-be migrations without writing.",
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
    """Backfill markdown AC checkboxes into structured frontmatter."""
    issues.run_migrate_acs(dry_run=dry_run, project_dir=path)


@app.command(name="set-slices", group=GROUPS["setup"])
def set_slices_command(
    slices: Annotated[
        tuple[str, ...],
        Parameter(
            name="--slice",
            help="Architectural layer (repeatable).",
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
    """Define project architectural slices in state.md."""
    issues.run_set_slices(slices=slices, project_dir=path)


@app.command(name="update-skills", group=GROUPS["planning"])
def update_skills_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to detect skills from.",
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
    """Auto-detect and update skills_required from issue content."""
    if path is None:
        path = Path.cwd()

    import sys

    from mantle.core import baseline, skills

    baseline_names = baseline.resolve_baseline_skills(path)
    new_skills = skills.auto_update_skills(path, issue)

    baseline_set = set(baseline_names)
    issue_matched_new = [s for s in new_skills if s not in baseline_set]

    if baseline_names:
        print(file=sys.stderr)
        print(
            f"Baseline skills (always loaded): {', '.join(baseline_names)}",
            file=sys.stderr,
        )

    if issue_matched_new:
        print(file=sys.stderr)
        print(
            "Issue-matched skills (from body scan): "
            f"{', '.join(issue_matched_new)}",
            file=sys.stderr,
        )
        print("Updated skills_required in state.md.", file=sys.stderr)
    elif new_skills:
        # Only baseline-new, no body-scan matches
        print("Updated skills_required in state.md.", file=sys.stderr)
    elif not baseline_names:
        print(file=sys.stderr)
        print("No new skills detected.", file=sys.stderr)


@app.command(name="show-patterns", group=GROUPS["knowledge"])
def show_patterns_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Surface recurring themes and confidence trends from past learnings."""
    patterns_cli.run_show_patterns(project_dir=path)


@app.command(name="list-skills", group=GROUPS["knowledge"])
def list_skills_command(
    tag: Annotated[
        str | None,
        Parameter(
            name="--tag",
            help=("Filter by tag (e.g., domain/web, topic/python)."),
        ),
    ] = None,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """List all skills in the personal vault."""
    if path is None:
        path = Path.cwd()

    from mantle.core import skills

    try:
        summaries = skills.list_skill_summaries(path, tag=tag)
    except skills.VaultNotConfiguredError, FileNotFoundError:
        print("No personal vault configured.")
        print("Run `mantle init-vault` to set up your vault.")
        return

    if not summaries:
        if tag is not None:
            print(f"No skills matching tag '{tag}'.")
        else:
            print("No skills found in vault.")
        return

    print(f"{len(summaries)} skill(s) in vault:")
    for s in summaries:
        print(f"  - {s.slug} \u2014 {s.description}")


@app.command(name="list-tags", group=GROUPS["knowledge"])
def list_tags_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """List all tags from taxonomy and vault skills."""
    if path is None:
        path = Path.cwd()

    from mantle.core import tags

    summary = tags.collect_all_tags(path)

    if not summary.by_prefix:
        print("No tags found.")
        return

    total = len(summary.taxonomy | summary.vault)
    print(f"{total} tag(s) found:")

    for group, group_tags in summary.by_prefix.items():
        print(f"\n  {group}:")
        for tag in group_tags:
            if tag in summary.undeclared:
                print(f"    - {tag}  (undeclared)")
            else:
                print(f"    - {tag}")

    if summary.undeclared:
        n = len(summary.undeclared)
        print(f"\n{n} undeclared tag(s) — consider adding to .mantle/tags.md")


@app.command(name="save-bug", group=GROUPS["capture"])
def save_bug_command(
    summary: Annotated[
        str,
        Parameter(
            name="--summary",
            help="One-line bug summary.",
        ),
    ],
    severity: Annotated[
        str,
        Parameter(
            name="--severity",
            help="Bug severity: blocker, high, medium, low.",
        ),
    ],
    description: Annotated[
        str,
        Parameter(
            name="--description",
            help="What happened (paragraph).",
        ),
    ],
    reproduction: Annotated[
        str,
        Parameter(
            name="--reproduction",
            help="Steps to reproduce.",
        ),
    ],
    expected: Annotated[
        str,
        Parameter(
            name="--expected",
            help="Expected behaviour.",
        ),
    ],
    actual: Annotated[
        str,
        Parameter(
            name="--actual",
            help="Actual behaviour.",
        ),
    ],
    related_issue: Annotated[
        str | None,
        Parameter(
            name="--related-issue",
            help="Related issue (e.g. issue-08).",
        ),
    ] = None,
    related_files: Annotated[
        tuple[str, ...],
        Parameter(
            name="--related-file",
            help="Related file path (repeatable).",
        ),
    ] = (),
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Capture a bug report in .mantle/bugs/."""
    bugs.run_save_bug(
        summary=summary,
        severity=severity,
        description=description,
        reproduction=reproduction,
        expected=expected,
        actual=actual,
        related_issue=related_issue,
        related_files=related_files,
        project_dir=path,
    )


@app.command(name="update-bug-status", group=GROUPS["capture"])
def update_bug_status_command(
    bug: Annotated[
        str,
        Parameter(
            name="--bug",
            help="Bug filename (e.g. 2026-03-03-slug.md).",
        ),
    ],
    status: Annotated[
        str,
        Parameter(
            name="--status",
            help="New status: open, fixed, wont-fix.",
        ),
    ],
    fixed_by: Annotated[
        str | None,
        Parameter(
            name="--fixed-by",
            help="Issue that fixes this bug (e.g. issue-21).",
        ),
    ] = None,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Update a bug's status."""
    bugs.run_update_bug_status(
        bug=bug,
        status=status,
        fixed_by=fixed_by,
        project_dir=path,
    )


@app.command(name="save-inbox-item", group=GROUPS["capture"])
def save_inbox_item_command(
    title: Annotated[
        str,
        Parameter(
            name="--title",
            help="One-line item title.",
        ),
    ],
    description: Annotated[
        str,
        Parameter(
            name="--description",
            help="Optional free-text description (body).",
        ),
    ] = "",
    source: Annotated[
        str,
        Parameter(
            name="--source",
            help="Origin of the item: user, ai.",
        ),
    ] = "user",
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save an inbox item to .mantle/inbox/."""
    inbox.run_save_inbox_item(
        title=title,
        description=description,
        source=source,
        project_dir=path,
    )


@app.command(name="update-inbox-status", group=GROUPS["capture"])
def update_inbox_status_command(
    item: Annotated[
        str,
        Parameter(
            name="--item",
            help="Item filename (e.g. 2026-04-05-slug.md).",
        ),
    ],
    status: Annotated[
        str,
        Parameter(
            name="--status",
            help="New status: open, promoted, dismissed.",
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
    """Update an inbox item's status."""
    inbox.run_update_inbox_status(
        item=item,
        status=status,
        project_dir=path,
    )


@app.command(name="save-learning", group=GROUPS["knowledge"])
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


@app.command(name="save-session", group=GROUPS["capture"])
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


@app.command(name="save-skill", group=GROUPS["knowledge"])
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
    when_to_use: Annotated[
        str,
        Parameter(
            name="--when-to-use",
            help="Trigger conditions for auto-invocation.",
        ),
    ] = "",
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
    tags: Annotated[
        tuple[str, ...],
        Parameter(
            name="--tag",
            help="Content tag (repeatable, e.g. topic/python).",
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
        when_to_use=when_to_use,
        related_skills=related_skills,
        projects=projects,
        tags=tags,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-verification-strategy", group=GROUPS["design"])
def save_verification_strategy_command(
    strategy: Annotated[
        str,
        Parameter(
            name="--strategy",
            help="Verification strategy text to persist.",
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
    """Save a project-wide verification strategy to config.md."""
    verify.run_save_verification_strategy(
        strategy=strategy,
        project_dir=path,
    )


@app.command(name="introspect-project", group=GROUPS["setup"])
def introspect_project_command(
    path: Annotated[
        Path | None,
        Parameter("--path", help="Project directory (default: cwd)"),
    ] = None,
) -> None:
    """Detect test, lint, and check commands from project files."""
    verify.run_introspect_project(project_dir=path)


@app.command(name="transition-issue-verified", group=GROUPS["planning"])
def transition_issue_verified_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to transition to verified.",
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
    """Transition an issue from implemented to verified."""
    verify.run_transition_to_verified(
        issue=issue,
        project_dir=path,
    )


@app.command(name="transition-issue-implemented", group=GROUPS["planning"])
def transition_issue_implemented_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to transition to implemented.",
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
    """Transition an issue from implementing to implemented."""
    review.run_transition_to_implemented(
        issue=issue,
        project_dir=path,
    )


@app.command(name="transition-issue-approved", group=GROUPS["planning"])
def transition_issue_approved_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to transition to approved.",
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
    """Transition an issue from verified to approved."""
    review.run_transition_to_approved(
        issue=issue,
        project_dir=path,
    )


@app.command(name="build-start", group=GROUPS["impl"])
def build_start_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number being built.",
        ),
    ],
) -> None:
    """Record the start of a build pipeline run (writes stub telemetry)."""
    builds.run_build_start(issue)


@app.command(name="build-finish", group=GROUPS["impl"])
def build_finish_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number being finished.",
        ),
    ],
) -> None:
    """Finalize the build report by parsing Claude Code session JSONL."""
    builds.run_build_finish(issue)


@app.command(name="transition-issue-implementing", group=GROUPS["planning"])
def transition_issue_implementing_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to transition to implementing.",
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
    """Transition an issue from verified to implementing."""
    review.run_transition_to_implementing(
        issue=issue,
        project_dir=path,
    )


@app.command(name="save-review-result", group=GROUPS["review"])
def save_review_result_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number under review.",
        ),
    ],
    feedback: Annotated[
        tuple[str, ...],
        Parameter(
            name="--feedback",
            help=("Review feedback as 'criterion|status|comment'."),
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
    """Save a review result to .mantle/reviews/."""
    review.run_save_review_result(
        issue=issue,
        feedback=feedback,
        project_dir=path,
    )


@app.command(name="load-review-result", group=GROUPS["review"])
def load_review_result_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to load review for.",
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
    """Load and print a review result."""
    review.run_load_review_result(
        issue=issue,
        project_dir=path,
    )


@app.command(name="save-scout", group=GROUPS["idea"])
def save_scout_command(
    repo_url: Annotated[
        str,
        Parameter(
            name="--repo-url",
            help="Full URL of the scouted repository.",
        ),
    ],
    repo_name: Annotated[
        str,
        Parameter(
            name="--repo-name",
            help="Short name of the scouted repository.",
        ),
    ],
    dimensions: Annotated[
        list[str],
        Parameter(
            name="--dimension",
            help="Analysis dimensions covered in the report.",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full scout report content.",
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
    """Save a scout report to .mantle/scouts/."""
    scout.run_save_scout(
        repo_url=repo_url,
        repo_name=repo_name,
        dimensions=dimensions,
        content=content,
        project_dir=path,
    )


@app.command(name="compile", group=GROUPS["setup"])
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
    issue: Annotated[
        int | None,
        Parameter(
            name="--issue",
            help="Compile only skills relevant to this issue number.",
        ),
    ] = None,
) -> None:
    """Compile vault context into Claude Code commands."""
    compile_cmd.run_compile(
        if_stale=if_stale,
        project_dir=path,
        target_dir=target,
        issue=issue,
    )


@app.command(name="install", group=GROUPS["setup"])
def install_command() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    install.run_install()


@app.command(name="collect-issue-files", group=GROUPS["impl"])
def collect_issue_files_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to collect files for.",
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
    """List files changed by an issue's commits."""
    simplify.run_collect_issue_files(
        issue=issue,
        project_dir=path,
    )


@app.command(name="collect-issue-diff-stats", group=GROUPS["impl"])
def collect_issue_diff_stats_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Issue number to collect diff stats for.",
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
    """Report diff stats (file count, lines added/removed/changed) for an issue's commits."""
    simplify.run_collect_issue_diff_stats(
        issue=issue,
        project_dir=path,
    )


@app.command(name="collect-changed-files", group=GROUPS["impl"])
def collect_changed_files_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """List all changed files in the working tree."""
    simplify.run_collect_changed_files(
        project_dir=path,
    )


@app.command(name="save-distillation", group=GROUPS["knowledge"])
def save_distillation_command(
    topic: Annotated[
        str,
        Parameter(
            name="--topic",
            help="The distillation subject.",
        ),
    ],
    source_paths: Annotated[
        list[str],
        Parameter(
            name="--source-paths",
            help=("Relative path to a source note (repeatable)."),
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Distillation body content.",
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
    """Save a distillation note to .mantle/distillations/."""
    knowledge.run_save_distillation(
        topic=topic,
        source_paths=source_paths,
        content=content,
        project_dir=path,
    )


@app.command(name="list-distillations", group=GROUPS["knowledge"])
def list_distillations_command(
    topic: Annotated[
        str | None,
        Parameter(
            name="--topic",
            help=("Filter by topic substring (case-insensitive)."),
        ),
    ] = None,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """List distillation notes in .mantle/distillations/."""
    knowledge.run_list_distillations(
        topic=topic,
        project_dir=path,
    )


@app.command(name="load-distillation", group=GROUPS["knowledge"])
def load_distillation_command(
    path: Annotated[
        str,
        Parameter(
            name="--path",
            help="Absolute path to the distillation file.",
        ),
    ],
) -> None:
    """Load and print a distillation note."""
    knowledge.run_load_distillation(path=path)


@app.command(name="storage", group=GROUPS["setup"])
def storage_command(
    mode: Annotated[
        str,
        Parameter(
            name="--mode",
            help="Storage mode: 'global' or 'local'.",
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
    """Set the storage mode for the project."""
    storage.run_storage(mode=mode, project_dir=path)


@app.command(name="migrate-storage", group=GROUPS["setup"])
def migrate_storage_command(
    direction: Annotated[
        str,
        Parameter(
            name="--direction",
            help="Migration direction: 'global' or 'local'.",
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
    """Migrate .mantle/ storage between local and global."""
    storage.run_migrate_storage(direction=direction, project_dir=path)


@app.command(name="where", group=GROUPS["setup"])
def where_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Print the resolved .mantle/ directory absolute path."""
    storage.run_where(project_dir=path)


@app.command(name="show-hook-example", group=GROUPS["setup"])
def show_hook_example_command(
    name: Annotated[
        str,
        Parameter(
            help="Example name: linear, jira, or slack.",
        ),
    ],
) -> None:
    """Print a shipped lifecycle hook example to stdout.

    Usage: mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh
    """
    hooks.run_show_hook_example(name=name)


if __name__ == "__main__":
    app()
