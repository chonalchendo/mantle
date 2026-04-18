#!/usr/bin/env bash
# Mantle lifecycle hook — Jira integration via Atlassian CLI (acli).
#
# SETUP
# -----
# 1. Install acli: https://developer.atlassian.com/cloud/acli/
# 2. Authenticate once: `acli jira auth login`
#    (acli stores tokens in your OS keychain — mantle never sees them.)
# 3. Add to your .mantle/config.md frontmatter:
#
#    hooks_env:
#      JIRA_PROJECT_KEY: PLAT
#
# 4. Bind to an event:
#
#      mantle show-hook-example jira > .mantle/hooks/on-issue-shaped.sh
#      chmod +x .mantle/hooks/on-issue-shaped.sh
#
# Suggested binding: on-issue-shaped.sh.
#
# CONTRACT (from mantle)
# ----------------------
#   $1 = issue number
#   $2 = new status
#   $3 = issue title
#
# Env: JIRA_PROJECT_KEY (from hooks_env in config.md).

set -euo pipefail

ISSUE_NUMBER="$1"
NEW_STATUS="$2"
ISSUE_TITLE="$3"

: "${JIRA_PROJECT_KEY:?JIRA_PROJECT_KEY must be set via hooks_env in config.md}"

# Create or update a Jira work item for this mantle issue.
acli jira work-item create \
  --project "${JIRA_PROJECT_KEY}" \
  --type Task \
  --summary "[mantle #${ISSUE_NUMBER}] ${ISSUE_TITLE}" \
  --description "Mantle status: ${NEW_STATUS}"
