#!/usr/bin/env bash
# iryo 医療 — run the レセプト engine test suite with one command.
# The repo-wide pytest plugin env can be broken (langsmith/pydantic mismatch), so we
# disable plugin autoload. Exits non-zero on any failure (deploy-gate friendly).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
rc=0

echo "==> iryo レセプト点数計算 engine tests"
( cd "$ROOT/py" && python3 -m pytest -q test_rezept.py ) || rc=1

echo "==> iryo 高額療養費 全区分 tests"
( cd "$ROOT/py" && python3 -m pytest -q test_kogaku.py ) || rc=1

echo "==> iryo 保険・年齢区分・負担区分 tests"
( cd "$ROOT/py" && python3 -m pytest -q test_insurance.py ) || rc=1

echo "==> iryo マスタ取り込み (全件対応) tests"
( cd "$ROOT/py" && python3 -m pytest -q test_master_loader.py ) || rc=1

echo "==> iryo 全診療区分カバレッジ (入院/公費/食事) tests"
( cd "$ROOT/py" && python3 -m pytest -q test_coverage.py ) || rc=1

echo "==> iryo 電子カルテ PHI gate tests"
( cd "$ROOT/py" && python3 -m pytest -q test_karte.py ) || rc=1

echo "==> iryo レセ電 (レセプト電算) record tests"
( cd "$ROOT/py" && python3 -m pytest -q test_receden.py ) || rc=1

echo "==> iryo e2e (診療録 → レセプト → レセ電 → FHIR)"
( cd "$ROOT/py" && python3 -m pytest -q test_e2e.py ) || rc=1

# cljc (babashka) tests — py→cljc port
BB_CP="20-actors:20-actors/kotodama/src:50-infra/etzhayyim-moyai-credit/src:70-tools/src:70-tools"
run_cljc() {
  local ns="$1"
  echo "==> iryo [cljc] $ns"
  ( cd "$REPO_ROOT" && bb -cp "$BB_CP" -e "(require (quote clojure.test) (quote $ns))(let [r (clojure.test/run-tests (quote $ns))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))" ) || rc=1
}

run_cljc "iryo.methods.test-masters"
run_cljc "iryo.methods.test-master-loader"
run_cljc "iryo.methods.test-insurance"
run_cljc "iryo.methods.test-kogaku"
run_cljc "iryo.methods.test-rezept"
run_cljc "iryo.methods.test-karte"
run_cljc "iryo.methods.test-receden"
run_cljc "iryo.methods.test-coverage"
run_cljc "iryo.methods.test-e2e"
run_cljc "iryo.methods.test-datoms"
run_cljc "iryo.methods.test-kotoba"

if [[ $rc -eq 0 ]]; then
  echo "==> iryo: ALL GREEN"
else
  echo "==> iryo: FAILURES (rc=$rc)" >&2
fi
exit $rc
