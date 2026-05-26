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
#   - manifest-lexicon-drift.py    (iter-47 of /loop)
#
# History:
#   - iter-30 of /loop: codified the first 3 audit scripts
#   - iter-31 of /loop: added subrepo-symlink-health.sh
#   - iter-32 of /loop: this aggregator
#
# Usage:
#   bash 70-tools/scripts/audit/all.sh             # report (~1.1 s wall)
#   bash 70-tools/scripts/audit/all.sh --strict    # exit 1 if any finding
#   bash 70-tools/scripts/audit/all.sh --test      # run pytest suite instead
#   bash 70-tools/scripts/audit/all.sh --all       # pytest + aggregator
#
# Requires: python3 + bash + `gh` CLI (for subrepo-upstream-health.sh).
# Returns: rollup count via stdout. Exit code 0 unless --strict and any
# script returned non-zero finding count.

set -euo pipefail

STRICT=0
TEST=0
RUN_AGGREGATOR=1
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    --test)   TEST=1; RUN_AGGREGATOR=0 ;;
    --all)    TEST=1; RUN_AGGREGATOR=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

# --test or --all: run the pytest suite first. STRICT-mode behaviour
# matters here — pytest failures always exit non-zero (regressions
# should never silently pass).
if [ "$TEST" -eq 1 ]; then
  echo
  echo "── pytest suite (5 files / 74 tests) ──"
  if ! PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
       70-tools/scripts/audit/test_adr_cross_ref_health.py \
       70-tools/scripts/audit/test_manifest_lexicon_drift.py \
       70-tools/scripts/audit/test_subrepo_scripts.py \
       70-tools/scripts/audit/test_simple_audits.py \
       70-tools/scripts/audit/test_e7m_verify_perf.py \
       2>&1; then
    echo "pytest suite FAILED — see output above" >&2
    exit 1
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
run "manifest-lexicon-drift" python3 70-tools/scripts/audit/manifest-lexicon-drift.py

echo
echo "═══════════════════════════════════════"
echo " total findings across all audits: $total"
echo "═══════════════════════════════════════"

if [ "$STRICT" -eq 1 ] && [ "$total" -gt 0 ]; then
  exit 1
fi
exit 0
