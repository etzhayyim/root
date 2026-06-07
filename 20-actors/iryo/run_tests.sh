#!/usr/bin/env bash
# iryo 医療 — run the レセプト engine test suite with one command.
# The repo-wide pytest plugin env can be broken (langsmith/pydantic mismatch), so we
# disable plugin autoload. Exits non-zero on any failure (deploy-gate friendly).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
rc=0

echo "==> iryo レセプト点数計算 engine tests"
( cd "$ROOT/py" && python3 -m pytest -q test_rezept.py ) || rc=1

echo "==> iryo 電子カルテ PHI gate tests"
( cd "$ROOT/py" && python3 -m pytest -q test_karte.py ) || rc=1

echo "==> iryo レセ電 (レセプト電算) record tests"
( cd "$ROOT/py" && python3 -m pytest -q test_receden.py ) || rc=1

echo "==> iryo e2e (診療録 → レセプト → レセ電 → FHIR)"
( cd "$ROOT/py" && python3 -m pytest -q test_e2e.py ) || rc=1

if [[ $rc -eq 0 ]]; then
  echo "==> iryo: ALL GREEN"
else
  echo "==> iryo: FAILURES (rc=$rc)" >&2
fi
exit $rc
