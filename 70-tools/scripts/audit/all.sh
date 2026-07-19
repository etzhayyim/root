#!/usr/bin/env bash
#
# all.sh — run every audit script under `70-tools/scripts/audit/` and
# report a single rollup total. Convenient single-command entry point
# for operators who want a "is the monorepo's distribution surface
# healthy?" check before publishing / pushing / opening a PR.
#
# Scripts invoked (in order of historical addition):
#   - dependabot-defunct.py        (iter-18 + iter-23 of /loop)
#   - sdk-exports-dist.py          (iter-26 of /loop)
#   - subrepo-upstream-health.sh   (iter-28 + iter-29 of /loop)
#   - subrepo-symlink-health.sh    (iter-24 + iter-31 of /loop)
#   - sibling-convention-drift.py  (iter-37 of /loop)
#
# History:
#   - iter-30 of /loop: codified the first 3 audit scripts
#   - iter-31 of /loop: added subrepo-symlink-health.sh
#   - iter-32 of /loop: this aggregator
#
# Usage:
#   bash 70-tools/scripts/audit/all.sh             # report (~1.1 s wall)
#   bash 70-tools/scripts/audit/all.sh --strict    # exit 1 if any finding
#   bash 70-tools/scripts/audit/all.sh --test      # run full pytest suite
#   bash 70-tools/scripts/audit/all.sh --test <file>  # run one test file
#   bash 70-tools/scripts/audit/all.sh --all       # pytest + aggregator
#
# Why --test is a wrapper: pytest crashes on this dev box's langsmith
# plugin (pydantic version mismatch); the wrapper sets
# PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 so operators don't have to remember
# the env var. A specific test file can be passed after --test for
# targeted reruns (e.g. `bash all.sh --test test_e7m_verify_perf.py`).
#
# Requires: python3 + bash + `gh` CLI (for subrepo-upstream-health.sh).
# Returns: rollup count via stdout. Exit code 0 unless --strict and any
# script returned non-zero finding count.

set -euo pipefail

STRICT=0
TEST=0
RUN_AGGREGATOR=1
TEST_FILE=""

# Two-pass arg parsing: --test may take an optional positional file.
i=0
ARGS=("$@")
while [ "$i" -lt "${#ARGS[@]}" ]; do
  arg="${ARGS[$i]}"
  case "$arg" in
    --strict) STRICT=1 ;;
    --test)
      TEST=1
      RUN_AGGREGATOR=0
      # Peek at next arg; if it's a test_*.py filename (not a flag),
      # consume it as the targeted file.
      next_i=$((i + 1))
      if [ "$next_i" -lt "${#ARGS[@]}" ]; then
        next_arg="${ARGS[$next_i]}"
        case "$next_arg" in
          test_*.py)
            TEST_FILE="$next_arg"
            i=$next_i
            ;;
        esac
      fi
      ;;
    --all)    TEST=1; RUN_AGGREGATOR=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
  i=$((i + 1))
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

# --test or --all: run the pytest suite first. STRICT-mode behaviour
# matters here — pytest failures always exit non-zero (regressions
# should never silently pass).
if [ "$TEST" -eq 1 ]; then
  echo
  if [ -n "$TEST_FILE" ]; then
    target="70-tools/scripts/audit/$TEST_FILE"
    if [ ! -f "$target" ]; then
      echo "target test file not found: $target" >&2
      exit 2
    fi
    echo "── pytest (single file: $TEST_FILE) ──"
    if ! PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest "$target" 2>&1; then
      echo "pytest FAILED — see output above" >&2
      exit 1
    fi
  else
    echo "── root-owned pytest suite (5 files) ──"
    if ! PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
         70-tools/scripts/audit/test_adr_cross_ref_health.py \
         70-tools/scripts/audit/test_subrepo_scripts.py \
         70-tools/scripts/audit/test_simple_audits.py \
         70-tools/scripts/audit/test_e7m_verify_perf.py \
         70-tools/scripts/audit/test_gitmodules.py \
         2>&1; then
      echo "pytest suite FAILED — see output above" >&2
      exit 1
    fi

  fi
fi

# --test alone returns now (no aggregator run).
if [ "$RUN_AGGREGATOR" -eq 0 ]; then
  exit 0
fi

total=0
exit_code=0

run() {
  local name="$1"; shift
  echo
  echo "── $name ──"
  # Capture both stdout + exit, but never propagate non-zero (we summarize).
  output=$("$@" 2>&1) || true
  echo "$output"
  # Extract a "<label>: <count>" tail line; pick the highest single integer
  # at end-of-line (each script's final summary line follows that pattern).
  count=$(echo "$output" | grep -oE ":[[:space:]]+[0-9]+$" | grep -oE "[0-9]+$" | tail -1)
  [ -z "$count" ] && count=0
  total=$((total + count))
}

run "dependabot-defunct" python3 70-tools/scripts/audit/dependabot-defunct.py
run "sdk-exports-dist" python3 70-tools/scripts/audit/sdk-exports-dist.py
run "subrepo-upstream-health" bash 70-tools/scripts/audit/subrepo-upstream-health.sh
run "subrepo-symlink-health" bash 70-tools/scripts/audit/subrepo-symlink-health.sh
run "sibling-convention-drift" python3 70-tools/scripts/audit/sibling-convention-drift.py

echo
echo "═══════════════════════════════════════"
echo " total findings across all audits: $total"
echo "═══════════════════════════════════════"

if [ "$STRICT" -eq 1 ] && [ "$total" -gt 0 ]; then
  exit 1
fi
exit 0
