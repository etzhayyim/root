#!/usr/bin/env bash
# ossekai 御節介 — run the agent test suite with one command.
# The repo-wide pytest plugin env is broken (langsmith/pydantic mismatch), so we
# disable plugin autoload. Exits non-zero on any failure (deploy-gate friendly).
set -uo pipefail
cd "$(dirname "$0")/py"

echo "==> ossekai agent tests"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q test_agent.py
rc=$?
if [[ $rc -eq 0 ]]; then
  echo "==> ossekai: ALL GREEN"
else
  echo "==> ossekai: FAILURES (rc=$rc)" >&2
fi
exit $rc
