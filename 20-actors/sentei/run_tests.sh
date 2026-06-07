#!/usr/bin/env bash
# sentei 剪定 — run the pruning-engine test suite (ADR-2606072000).
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m unittest 20-actors/sentei/methods/test_prune.py -v
