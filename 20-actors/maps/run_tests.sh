#!/usr/bin/env bash
# maps — kotoba-native methods test runner (ADR-2606064500). stdlib only.
set -euo pipefail
cd "$(dirname "$0")/methods"
python3 test_methods.py "$@"
