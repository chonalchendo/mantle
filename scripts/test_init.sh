#!/usr/bin/env bash
# Test that `mantle init` and `mantle init-vault` work end-to-end.
#
# Usage:
#   ./scripts/test_init.sh
#
# This script:
#   1. Creates a temporary git repo
#   2. Runs `mantle init` and verifies the .mantle/ structure
#   3. Runs `mantle init` again to verify idempotency
#   4. Runs `mantle init-vault` and verifies vault + config update
#   5. Runs `mantle init-vault` again to verify idempotency
#   6. Cleans up

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

PROJECT="$TMPDIR/my-project"
VAULT="$TMPDIR/my-vault"

echo "==> Setting up test project..."
mkdir -p "$PROJECT"
git -C "$PROJECT" init --quiet
git -C "$PROJECT" config user.email "test@example.com"
git -C "$PROJECT" config user.name "Test User"

echo "==> Running mantle init..."
uv run --project "$ROOT" mantle init --path "$PROJECT"

echo "==> Verifying .mantle/ structure..."
for dir in decisions sessions issues stories; do
    if [ ! -d "$PROJECT/.mantle/$dir" ]; then
        echo "    FAIL: $dir/ not found"
        exit 1
    fi
done
echo "    Subdirectories: OK"

for file in state.md config.md tags.md .gitignore; do
    if [ ! -f "$PROJECT/.mantle/$file" ]; then
        echo "    FAIL: $file not found"
        exit 1
    fi
done
echo "    Files: OK"

echo "==> Verifying state.md content..."
if grep -q "project: my-project" "$PROJECT/.mantle/state.md" \
   && grep -q "status: idea" "$PROJECT/.mantle/state.md" \
   && grep -q "created_by:" "$PROJECT/.mantle/state.md"; then
    echo "    state.md: OK"
else
    echo "    FAIL: state.md content incorrect"
    cat "$PROJECT/.mantle/state.md"
    exit 1
fi

echo "==> Running mantle init again (idempotency)..."
OUTPUT=$(uv run --project "$ROOT" mantle init --path "$PROJECT" 2>&1)
if echo "$OUTPUT" | grep -q "already exists"; then
    echo "    Idempotency: OK"
else
    echo "    FAIL: Expected 'already exists' warning"
    echo "    Got: $OUTPUT"
    exit 1
fi

echo "==> Running mantle init-vault..."
cd "$PROJECT"
uv run --project "$ROOT" mantle init-vault --path "$VAULT"

echo "==> Verifying vault structure..."
for dir in skills knowledge inbox; do
    if [ ! -d "$VAULT/$dir" ]; then
        echo "    FAIL: $dir/ not found in vault"
        exit 1
    fi
done
echo "    Vault directories: OK"

echo "==> Verifying config.md updated..."
if grep -q "personal_vault:" "$PROJECT/.mantle/config.md" \
   && ! grep -q "personal_vault: null" "$PROJECT/.mantle/config.md"; then
    echo "    Config auto-set: OK"
else
    echo "    FAIL: personal_vault not set in config.md"
    cat "$PROJECT/.mantle/config.md"
    exit 1
fi

echo "==> Running mantle init-vault again (idempotency)..."
OUTPUT=$(uv run --project "$ROOT" mantle init-vault --path "$VAULT" 2>&1)
if echo "$OUTPUT" | grep -q "already exists"; then
    echo "    Idempotency: OK"
else
    echo "    FAIL: Expected 'already exists' warning"
    echo "    Got: $OUTPUT"
    exit 1
fi

echo ""
echo "All checks passed."
