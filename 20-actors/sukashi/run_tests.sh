#!/usr/bin/env bash
# sukashi 透かし — run the actor's test suite (stdlib unittest; no install step). ADR-2606071600.
set -euo pipefail
cd "$(dirname "$0")"
echo "== sukashi: analyze (seed) =="
python3 methods/analyze.py >/dev/null
echo "== sukashi: tests =="
python3 tests/test_sukashi.py
echo "== sukashi: autonomous heartbeat + kotoba Datom-log tests =="
python3 methods/test_autorun.py
