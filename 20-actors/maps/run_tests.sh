#!/usr/bin/env bash
# maps — kotoba-native methods test runner (ADR-2606064500). stdlib only.
set -euo pipefail
cd "$(dirname "$0")/methods"
PY="${PYTHON:-python3}"   # set PYTHON=/path/to/venv/bin/python to exercise the real-H3 layer
"$PY" test_methods.py "$@"
"$PY" test_avet_roundtrip.py "$@"
"$PY" test_e2e_http.py "$@"
"$PY" test_transit.py "$@"
"$PY" test_search.py "$@"
"$PY" test_reverse.py "$@"
