#!/usr/bin/env bash
# aburi 炙り — run the pure-stdlib test suite (no deps). 14 tests.
set -euo pipefail
cd "$(dirname "$0")"
python3 tests/test_analyze.py
python3 tests/test_coverage.py
echo "aburi: all tests green"
