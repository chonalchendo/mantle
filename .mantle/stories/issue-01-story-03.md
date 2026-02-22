---
issue: 1
title: GitHub workflows (CI + publish)
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Create two GitHub Actions workflows: CI (on every push/PR) and publish (on version tags).

### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.14"]

    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install Python
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --group check

      - name: Run CI checks
        run: just ci
```

### .github/workflows/publish.yml

```yaml
name: Publish

on:
  push:
    tags:
      - "v*"

permissions:
  id-token: write
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5

      - name: Install Python
        run: uv python install 3.14

      - name: Build distributions
        run: uv build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/mantle-ai/

    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### Setup instructions

Add a section to CLAUDE.md or a note in the publish workflow comments explaining:
- Trusted publisher must be configured on PyPI (project settings → Publishing → Add GitHub as trusted publisher)
- Repository owner, repo name, and workflow filename must match exactly
- The `pypi` environment should be created in GitHub repo settings with protection rules

## Tests

- `.github/workflows/ci.yml` exists and is valid YAML
- `.github/workflows/publish.yml` exists and is valid YAML
- CI workflow references `just ci` command
- CI workflow uses `astral-sh/setup-uv@v5` with caching enabled
- CI workflow matrix includes Python 3.14
- Publish workflow triggers on `v*` tags
- Publish workflow has `id-token: write` permission
- Publish workflow uses `pypa/gh-action-pypi-publish@release/v1`
