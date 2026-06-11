#!/usr/bin/env bash
# actor-dna — hermetic stdlib-only test suite.
set -euo pipefail
cd "$(dirname "$0")"
fail=0
for t in test_cid.py test_dna.py test_integrity.py test_deploy.py test_real_actors.py; do
  python3 "$t" || fail=1
done
if [ "$fail" -eq 0 ]; then echo "── actor-dna: ALL suites green ──"; else echo "── actor-dna: FAILURES ──"; exit 1; fi
