#!/usr/bin/env bash
# warifu 割符 — unified test runner across all layers (ADR-2605302000).
# Apache-2.0 + Charter Rider v2.0. Runs forge (contracts) + python (cells / eavt-schema /
# guarded-substrate / lexicons) + node (gateway). Exits non-zero if any suite fails.
#
#   bash 70-tools/scripts/warifu-test.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
fail=0
ROWS=()

run() { # name  cmd...
  local name="$1"; shift
  local log="$TMP/$(echo "$name" | tr ' /' '__').log"
  if "$@" >"$log" 2>&1; then
    local line
    line="$(grep -hiE 'tests? passed|checks passed' "$log" | tail -1)"
    ROWS+=("PASS|$name|${line:-ok}")
  else
    ROWS+=("FAIL|$name|$(tail -1 "$log" 2>/dev/null)")
    fail=1
  fi
}

echo "warifu test runner — root: $ROOT"

run "forge contracts"   bash -c "cd '$ROOT/50-infra/warifu-contracts' && forge test"
run "cells"             python3 "$ROOT/orgs/etzhayyim/com-etzhayyim-warifu/cells/test_cells.py"
run "eavt-schema"       python3 "$ROOT/orgs/etzhayyim/com-etzhayyim-warifu/cells/test_eavt_schema.py"
run "guarded-substrate" python3 "$ROOT/orgs/etzhayyim/com-etzhayyim-warifu/cells/test_guarded_substrate.py"
run "lexicons"          python3 "$ROOT/orgs/etzhayyim/com-etzhayyim-warifu/test_lexicons.py"
run "gateway (node)"    bash -c "cd '$ROOT/50-infra/warifu-gateway' && npm test --silent"

echo ""
printf '%-22s %-6s %s\n' "SUITE" "STATUS" "SUMMARY"
printf '%-22s %-6s %s\n' "----------------------" "------" "-------------------------------"
for r in "${ROWS[@]}"; do
  IFS='|' read -r st nm sm <<<"$r"
  printf '%-22s %-6s %s\n' "$nm" "$st" "$sm"
done
echo ""
if [ "$fail" -eq 0 ]; then echo "ALL WARIFU SUITES GREEN"; else echo "SOME SUITES FAILED (see above)"; fi
rm -rf "$TMP"
exit "$fail"
