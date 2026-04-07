---
issue: 40
title: Core review persistence — save and load review results
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer whose code was flagged in review, I want review feedback saved as structured data so that automated tools can read it and fix flagged issues.

## Depends On

None — independent (first story in issue).

## Approach

Extend the existing core/review.py module (which already has ReviewChecklist and ReviewItem models) with save/load functions that persist review results to .mantle/reviews/. Follow the established vault.write_note/read_note pattern used by learning.py, shaping.py, and other core modules. Add thin CLI wrappers in cli/main.py.

## Implementation

### src/mantle/core/review.py (modify)

Add to the existing module:

1. **ReviewResultNote** pydantic model (frozen=True):
   - issue: int
   - title: str
   - status: Literal["approved", "needs-changes"]
   - author: str
   - date: date
   - tags: tuple[str, ...] = ("type/review", "phase/reviewing")

2. **save_review_result(project_root, checklist) -> tuple[ReviewResultNote, Path]**:
   - Takes a ReviewChecklist (already exists in the module)
   - Computes status from checklist.has_needs_changes
   - Resolves git identity via state.resolve_git_identity()
   - Builds ReviewResultNote frontmatter
   - Formats body from checklist items: each criterion with status, passed, detail, comment
   - Writes to .mantle/reviews/issue-{NN:02d}-review.md via vault.write_note()
   - Creates .mantle/reviews/ directory if it doesn't exist
   - Overwrites existing review file for the same issue (reviews are mutable)
   - Returns (note, path)

3. **load_review_result(project_root, issue_number) -> tuple[ReviewResultNote, str]**:
   - Reads .mantle/reviews/issue-{NN:02d}-review.md
   - Returns (frontmatter, body) via vault.read_note()
   - Raises FileNotFoundError if no review exists

4. **list_reviews(project_root) -> list[Path]**:
   - Glob .mantle/reviews/issue-*.md, sorted oldest-first
   - Returns empty list if directory doesn't exist

5. Add imports: from datetime import date, from mantle.core import state, vault

#### Design decisions

- **One review file per issue** (not per review pass): Reviews are mutable — the latest review overwrites previous ones. This matches the workflow where you fix and re-review.
- **Body is formatted markdown** (not raw JSON): Human-readable when browsing .mantle/ in git diffs. Each criterion is a list item with status markers.
- **ReviewResultNote is separate from ReviewChecklist**: The note model captures file metadata (author, date, tags). The checklist model captures review data. save_review_result bridges them.

### src/mantle/cli/main.py (modify)

Add two new commands:

1. **save-review-result** command:
   - Parameters: --issue (int), --feedback (tuple[str, ...], repeatable)
   - Each --feedback value is "criterion|status|comment" (pipe-delimited)
   - Parses feedback into ReviewItem list, builds ReviewChecklist
   - Gets issue title from issues.find_issue_path + load_issue
   - Calls review.save_review_result()
   - Prints confirmation with path

2. **load-review-result** command:
   - Parameters: --issue (int)
   - Calls review.load_review_result()
   - Prints the formatted body

Import review module: from mantle.core import review (following module import convention)

## Tests

### tests/core/test_review.py (modify)

Add to existing test file:

- **test_save_review_result_creates_file**: save_review_result with a ReviewChecklist creates .mantle/reviews/issue-NN-review.md
- **test_save_review_result_frontmatter**: saved file has correct ReviewResultNote frontmatter (issue, title, status, author, date, tags)
- **test_save_review_result_body_contains_criteria**: body contains each criterion with status and comment
- **test_save_review_result_needs_changes_status**: checklist with needs-changes items produces status "needs-changes"
- **test_save_review_result_approved_status**: checklist with all approved items produces status "approved"
- **test_save_review_result_overwrites**: saving twice for same issue overwrites the file
- **test_save_review_result_creates_directory**: saves correctly when .mantle/reviews/ doesn't exist yet
- **test_load_review_result**: load_review_result reads back saved review correctly
- **test_load_review_result_not_found**: raises FileNotFoundError when no review exists
- **test_list_reviews**: list_reviews returns paths sorted oldest-first
- **test_list_reviews_empty**: returns empty list when no reviews directory

Test fixtures: use tmp_path, mock state.resolve_git_identity to return a fixed email, use vault.write_note to set up .mantle/ structure