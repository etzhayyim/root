#!/usr/bin/env bash
# tatara 鑪 — run the whole cljc test suite with one command (babashka).
# Run from anywhere; classpath root is the 20-actors dir so tatara.methods.* resolves.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cp_root="$(cd "$here/.." && pwd)"   # 20-actors/

SUITES=(
  "tatara.methods.test-analyze"
  "tatara.methods.test-kotoba"
  "tatara.methods.test-autorun"
  "tatara.methods.test-lexicons"
  "tatara.methods.test-crosscheck"
  "tatara.methods.test-maturity"
  "tatara.methods.test-seed-integrity"
  "tatara.methods.test-viz"
  "tatara.methods.test-compose"
  "tatara.methods.test-robustness"
)

fail=0
for ns in "${SUITES[@]}"; do
  if bb -cp "$cp_root" -e "(require '$ns) ($ns/-main)"; then :; else
    echo "FAILED: $ns"; fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "── tatara: ALL suites green ──"
else
  echo "── tatara: FAILURES above ──"; exit 1
fi
