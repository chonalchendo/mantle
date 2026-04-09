---
issue: 10
title: Resume template and compiler integration
status: done
failure_log: null
tags:
  - type/story
  - status/done
---

## Implementation

Create the `resume.md.j2` Jinja2 template for the project briefing and extend the compiler to include session data in the template context. The resume template renders project state, the latest session log (filtered to the current user), blockers, and next actions — all within a ~3K token budget.

### src/mantle/core/compiler.py (modify)

#### Modify `collect_context()`

Extend the existing `collect_context()` to include session-related fields after the state.md fields. Import `session` and `state` modules. Resolve the current user's git identity via `state.resolve_git_identity()`, then call `session.latest_session(project_dir, author=identity)`.

Add these fields to the context dict:

```python
# Session briefing fields
"has_session": bool           # Whether a latest session was found
"latest_session_body": str    # Session body text (or "")
"latest_session_date": str    # Formatted date string (or "")
"latest_session_commands": list[str]  # Commands used (or [])
```

If `latest_session()` returns `None`, set `has_session` to `False` and the other fields to empty values. If it returns a session, extract the fields from the `SessionNote` frontmatter and body.

Format `latest_session_date` as `YYYY-MM-DD HH:MM` (e.g., `2026-03-01 14:30`) via `note.date.strftime("%Y-%m-%d %H:%M")`.

Wrap the session retrieval in a try/except that catches `RuntimeError` (from `resolve_git_identity()` when git is not configured). If git identity is unavailable, fall back to `latest_session(project_dir)` without author filtering. This ensures compilation works even without git.

#### Modify `source_paths()`

After existing optional file checks, add the latest session file to the source paths for staleness detection:

```python
sessions_dir = project_dir / ".mantle" / "sessions"
if sessions_dir.is_dir():
    session_files = sorted(sessions_dir.glob("*.md"))
    if session_files:
        paths.append(session_files[-1])  # Latest session only
```

This ensures that when a new session is saved, the compilation manifest detects staleness and recompiles (the latest file path changes). Only the latest session is tracked — not all sessions — to keep the manifest lean.

#### Imports (modify)

Add `session` to the imports:

```python
from mantle.core import manifest, session, state, templates, vault
```

### claude/commands/mantle/resume.md.j2 (new file)

Jinja2 template that renders the project briefing for auto-display on session start and for `/mantle:resume`. Fits within ~3K tokens.

```jinja2
You are resuming work on **{{ project }}** ({{ status }}, confidence {{ confidence }}).
{% if current_issue %}
**Currently working on**: Issue {{ current_issue }}{% if current_story %}, Story {{ current_story }}{% endif %}
{% endif %}
## Current Focus

{{ current_focus }}

## Blockers

{{ blockers }}
{% if has_session %}
## Last Session ({{ latest_session_date }})

{{ latest_session_body }}
{% endif %}
## Next Steps

{{ next_steps }}
{% if skills_required %}
## Skills Required

{% for skill in skills_required %}- {{ skill }}
{% endfor %}{% endif %}
```

The template prioritises actionable context: what to work on now, what's blocked, what happened last session, and what's next. The summary and recent decisions (available in `/mantle:status`) are omitted to stay within the ~3K budget and avoid redundancy — the resume is about continuity, not overview.

#### Design decisions

- **Separate from status template.** The resume template focuses on session continuity (last session, next steps, blockers). The status template focuses on project overview (summary, recent decisions). Different purposes, different content selection.
- **Session body included verbatim.** The session log body is already structured (Summary, What Was Done, Decisions, What's Next, Open Questions) and capped at ~200 words. No need to parse or reformat it.
- **Graceful without sessions.** The `{% if has_session %}` guard means the template renders cleanly for new projects with no session history.
- **Git identity fallback.** If `git config user.email` fails (e.g., bare environments), the compiler falls back to showing the overall latest session. Better to show an unfiltered session than nothing.
- **Latest session only in source_paths.** Tracking only the latest session file keeps staleness detection efficient. Adding all session files would cause unnecessary rehashing on every compilation check.

## Tests

### tests/core/test_compiler.py (modify)

Extend existing compiler tests. Test fixtures should include a `.mantle/sessions/` directory with sample session log files.

- **collect_context**: includes `has_session` field set to False when no sessions exist
- **collect_context**: includes `has_session` field set to True when sessions exist
- **collect_context**: includes `latest_session_body` from the latest session for current user
- **collect_context**: includes `latest_session_date` formatted as "YYYY-MM-DD HH:MM"
- **collect_context**: includes `latest_session_commands` as a list
- **collect_context**: filters sessions to current user's git identity
- **collect_context**: falls back to unfiltered latest session when git identity unavailable
- **source_paths**: includes latest session file when sessions exist
- **source_paths**: excludes sessions when sessions directory is empty
- **resume template**: renders with full context (project state + session)
- **resume template**: renders without session when `has_session` is False
- **resume template**: output fits within 3K token estimate (word count check on rendered output)
