#!/usr/bin/env bash
# meyasu 目安 — run the agent test suite with one command.
# The repo-wide pytest plugin env is broken (langsmith/pydantic mismatch), so we
# disable plugin autoload. Exits non-zero on any failure (deploy-gate friendly).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
rc=0

echo "==> meyasu agent tests"
( cd "$ROOT/py" && python3 -m pytest -q test_agent.py ) || rc=1

echo "==> meyasu viz builder tests"
( cd "$ROOT/viz" && python3 -m pytest -q test_build_viz.py ) || rc=1
if [[ $rc -eq 0 ]]; then
  echo "==> meyasu: ALL GREEN"
else
  echo "==> meyasu: FAILURES (rc=$rc)" >&2
fi
exit $rc
