#!/usr/bin/env bash
# Test that the built wheel installs correctly and `mantle install`
# copies bundled files into a target directory.
#
# Usage:
#   ./scripts/test_wheel_install.sh
#
# This script:
#   1. Builds the wheel
#   2. Creates a temporary virtualenv
#   3. Installs the wheel into it
#   4. Verifies `mantle install` copies help.md into a temp target dir
#   5. Cleans up

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "==> Building wheel..."
uv build --directory "$ROOT" --out-dir "$TMPDIR/dist" --quiet

WHEEL="$(ls "$TMPDIR/dist"/*.whl)"
echo "    Built: $(basename "$WHEEL")"

echo "==> Creating temp virtualenv..."
uv venv "$TMPDIR/venv" --python 3.14 --quiet
PYTHON="$TMPDIR/venv/bin/python"

echo "==> Installing wheel..."
uv pip install "$WHEEL" --python "$PYTHON" --quiet

echo "==> Verifying package import..."
"$PYTHON" -c "import mantle; print(f'    mantle {mantle.__version__}')"

echo "==> Verifying bundled claude/ directory..."
"$PYTHON" -c "
from importlib import resources
from pathlib import Path

ref = resources.files('mantle').joinpath('claude')
source = Path(str(ref))
assert source.is_dir(), f'claude/ not found at {source}'
help_md = source / 'commands' / 'mantle' / 'help.md'
assert help_md.is_file(), f'help.md not found at {help_md}'
print(f'    help.md found at {help_md}')
"

echo "==> Running mantle install (with temp HOME)..."
export HOME="$TMPDIR/fakehome"
mkdir -p "$HOME"
"$TMPDIR/venv/bin/mantle" install

echo "==> Verifying installed files..."
HELP_TARGET="$HOME/.claude/commands/mantle/help.md"
if [ -f "$HELP_TARGET" ]; then
    echo "    help.md installed at $HELP_TARGET"
else
    echo "    FAIL: help.md not found at $HELP_TARGET"
    exit 1
fi

MANIFEST="$HOME/.claude/mantle-file-manifest.json"
if [ -f "$MANIFEST" ]; then
    echo "    manifest created at $MANIFEST"
else
    echo "    FAIL: manifest not found at $MANIFEST"
    exit 1
fi

echo ""
echo "All checks passed."
