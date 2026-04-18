#!/usr/bin/env bash
# Mantle lifecycle hook — Slack incoming webhook notification.
#
# SETUP
# -----
# 1. Create a Slack incoming webhook:
#    https://api.slack.com/messaging/webhooks
# 2. Add to your .mantle/config.md frontmatter:
#
#    hooks_env:
#      SLACK_WEBHOOK_URL: https://hooks.slack.com/services/XXX/YYY/ZZZ
#
# 3. Bind to whichever events you want visibility on, e.g.:
#
#      mantle show-hook-example slack > .mantle/hooks/on-issue-review-approved.sh
#      chmod +x .mantle/hooks/on-issue-review-approved.sh
#
# Suggested binding: on-issue-review-approved.sh.
#
# CONTRACT (from mantle)
# ----------------------
#   $1 = issue number
#   $2 = new status
#   $3 = issue title
#
# Env: SLACK_WEBHOOK_URL (from hooks_env in config.md).

set -euo pipefail

ISSUE_NUMBER="$1"
NEW_STATUS="$2"
ISSUE_TITLE="$3"

: "${SLACK_WEBHOOK_URL:?SLACK_WEBHOOK_URL must be set via hooks_env in config.md}"

curl -sS -X POST "${SLACK_WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  --data "$(printf '{"text":"*Mantle issue #%s* (%s) — %s"}' \
    "${ISSUE_NUMBER}" "${NEW_STATUS}" "${ISSUE_TITLE}")"
