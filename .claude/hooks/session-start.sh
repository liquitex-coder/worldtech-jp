#!/bin/bash
# SessionStart hook for Claude Code on the web (worldtech-jp).
# Installs the tooling needed to run tests and lint in a fresh remote container.
# The pipeline itself is stdlib-only (see pipeline/*.py); only dev tools are needed.
# Runs only in remote sessions ($CLAUDE_CODE_REMOTE); local sessions are untouched.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

echo "[session-start] installing dev tooling (pytest, ruff)..."
PIP_ROOT_USER_ACTION=ignore python3 -m pip install --quiet --disable-pip-version-check pytest ruff

# Optional: real translation client, mirrors .github/workflows/daily.yml
# (only when ANTHROPIC_API_KEY is provided in the environment).
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "[session-start] ANTHROPIC_API_KEY present -> installing anthropic"
  PIP_ROOT_USER_ACTION=ignore python3 -m pip install --quiet --disable-pip-version-check anthropic
fi

# Persist session environment: run from repo root as a package, UTF-8 for Japanese text.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export PYTHONPATH=\"${CLAUDE_PROJECT_DIR:-$(pwd)}\""
    echo 'export PYTHONUTF8=1'
    echo 'export PYTHONDONTWRITEBYTECODE=1'
  } >> "$CLAUDE_ENV_FILE"
fi

echo "[session-start] done: $(python3 -m pytest --version 2>&1 | head -1); $(python3 -m ruff --version)"
