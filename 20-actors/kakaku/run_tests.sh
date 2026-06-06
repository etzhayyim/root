#!/usr/bin/env bash
# kakaku 価格 — run the agent test suite with one command.
# The repo-wide pytest plugin env is broken (langsmith/pydantic mismatch), so we
# disable plugin autoload. Exits non-zero on any failure (deploy-gate friendly).
set -uo pipefail
cd "$(dirname "$0")/py"

echo "==> kakaku agent tests"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q test_agent.py
rc=$?
if [[ $rc -eq 0 ]]; then
  echo "==> kakaku: ALL GREEN"
else
  echo "==> kakaku: FAILURES (rc=$rc)" >&2
fi
exit $rc
