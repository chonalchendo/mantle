#!/usr/bin/env bash
# Mantle lifecycle hook — Linear integration.
#
# SETUP
# -----
# 1. Create a Linear API key: https://linear.app/settings/api
# 2. Add to your .mantle/config.md frontmatter:
#
#    hooks_env:
#      LINEAR_API_KEY: lin_api_xxx
#      LINEAR_TEAM_ID: team-uuid
#
# 3. Copy this script and bind it to the event you care about, e.g.:
#
#      mantle show-hook-example linear > .mantle/hooks/on-issue-shaped.sh
#      chmod +x .mantle/hooks/on-issue-shaped.sh
#
# Suggested binding: on-issue-shaped.sh (creates/updates a Linear ticket
# when you finish shaping).
#
# CONTRACT (from mantle)
# ----------------------
#   $1 = issue number
#   $2 = new status (e.g. "shaped", "implementing", "verified", "approved")
#   $3 = issue title
#
# Env: LINEAR_API_KEY, LINEAR_TEAM_ID (from hooks_env in config.md).

set -euo pipefail

ISSUE_NUMBER="$1"
NEW_STATUS="$2"
ISSUE_TITLE="$3"

: "${LINEAR_API_KEY:?LINEAR_API_KEY must be set via hooks_env in config.md}"
: "${LINEAR_TEAM_ID:?LINEAR_TEAM_ID must be set via hooks_env in config.md}"

# GraphQL mutation: create an issue in the configured team.
curl -sS -X POST https://api.linear.app/graphql \
  -H "Authorization: ${LINEAR_API_KEY}" \
  -H "Content-Type: application/json" \
  --data @- <<EOF
{
  "query": "mutation IssueCreate(\$input: IssueCreateInput!) { issueCreate(input: \$input) { success issue { id identifier } } }",
  "variables": {
    "input": {
      "teamId": "${LINEAR_TEAM_ID}",
      "title": "[mantle #${ISSUE_NUMBER}] ${ISSUE_TITLE}",
      "description": "Mantle status: ${NEW_STATUS}"
    }
  }
}
EOF
