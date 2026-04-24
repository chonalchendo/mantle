# Build-90 Session Fixture

## Provenance

Captured from `~/.claude/projects/-Users-conal-Development-mantle/514d3e78-4614-4206-a4c1-4f26dafe9e10`
on 2026-04-24 for issue 92 regression test.

This is real Claude Code session data from the issue-90 build (parity harness
implementation). It is used by `tests/core/test_build90_fixture.py` to verify
that `find_subagent_files` and `group_stories` correctly attribute sub-agent
runs to their stages.

## Layout

```
build-90-session/
├── README.md                            # this file
└── mantle-session/                      # synthetic slug directory
    ├── 514d3e78-4614-4206-a4c1-4f26dafe9e10.jsonl   # truncated parent
    └── 514d3e78-4614-4206-a4c1-4f26dafe9e10/
        └── subagents/
            ├── agent-*.jsonl   (5 files, untouched)
            └── agent-*.meta.json (5 files, untouched)
```

## Parent JSONL truncation

The original parent JSONL (`514d3e78-4614-4206-a4c1-4f26dafe9e10.jsonl`) had
447 lines (~450 KB). It has been truncated to the first 50 lines (9 assistant
turns) to keep the fixture small while still proving that the parent-session
parser works correctly.

## Sub-agent types

The 5 sub-agent sidecars carry these `agentType` values:

- `agent-a0f548c9d2ceaa677` — `general-purpose` (verify step)
- `agent-a657b254269f29b28` — `refactorer` (simplify step)
- `agent-a960574993a66c6b2` — `story-implementer` (story 2)
- `agent-ac579fb0f016e7a99` — `story-implementer` (story 3)
- `agent-ad1760f99dd1021bc` — `story-implementer` (story 1)

Expected `group_stories` output: 3x `implement`, 1x `simplify`, 1x `verify`.
