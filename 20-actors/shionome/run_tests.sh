#!/usr/bin/env bash
# 潮目 (shionome) — run the whole test suite with one command.
# The METHOD layer was MIGRATED to Clojure (ADR-2606160842): methods/*.py → *.cljc, and the
# Python source + tests were pruned once the cljc ports were verified. The method suites now
# run as Clojure via bb (registered in bb.edn test:pywasm); the cell state-machine tests remain
# Python. Exits non-zero on any failure.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
fail=0

echo "==> shionome method suites (Clojure / bb)"
( cd "$ROOT" && bb -e "(require 'clojure.test
   'shionome.methods.test-weave 'shionome.methods.test-analyze 'shionome.methods.test-edn
   'shionome.methods.test-registry 'shionome.methods.test-export 'shionome.methods.test-social
   'shionome.methods.test-kotoba 'shionome.methods.test-autorun 'shionome.methods.test-grounding
   'shionome.methods.test-ingest 'shionome.methods.test-sources 'shionome.methods.test-lexicons
   'shionome.methods.test-consistency 'shionome.methods.test-charter-invariants)
   (let [r (clojure.test/run-tests
     'shionome.methods.test-weave 'shionome.methods.test-analyze 'shionome.methods.test-edn
     'shionome.methods.test-registry 'shionome.methods.test-export 'shionome.methods.test-social
     'shionome.methods.test-kotoba 'shionome.methods.test-autorun 'shionome.methods.test-grounding
     'shionome.methods.test-ingest 'shionome.methods.test-sources 'shionome.methods.test-lexicons
     'shionome.methods.test-consistency 'shionome.methods.test-charter-invariants)]
     (System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))" ) || fail=1

echo "==> shionome cell suites (Python)"
for s in cells/test_state_machines.py cells/test_membrane_flow.py; do
  [ -f "$(dirname "$0")/$s" ] || continue
  dir="$(dirname "$0")/$(dirname "$s")"; file="$(basename "$s")"
  if ( cd "$dir" && python3 "$file" >/dev/null 2>&1 ); then echo "  ok  $s"; else echo "  FAIL $s"; fail=1; fi
done

if [ "$fail" -eq 0 ]; then
  echo "── shionome: ALL suites green ──"
else
  echo "── shionome: FAILURES above ──"; exit 1
fi
