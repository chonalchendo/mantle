"""Central registry of cyclopts Group objects for 'mantle --help' panels.

Every command registered on the top-level app must reference one of these
groups via 'group=GROUPS[key]'. The key set is closed; adding a group means
adding an entry here and updating the taxonomy test.
"""

from cyclopts import Group

GROUPS: dict[str, Group] = {
    "setup": Group("Setup & plumbing", sort_key=1),
    "idea": Group("Idea & Validation", sort_key=2),
    "design": Group("Design", sort_key=3),
    "planning": Group("Planning", sort_key=4),
    "impl": Group("Implementation", sort_key=5),
    "review": Group("Review & Verification", sort_key=6),
    "capture": Group("Capture", sort_key=7),
    "knowledge": Group("Knowledge", sort_key=8),
}
