#!/usr/bin/env bash
# uchiwake 内訳 — test + smoke runner. ADR-2606081800.
set -euo pipefail
cd "$(dirname "$0")"
echo "== uchiwake tests =="
python3 -m unittest tests.test_uchiwake -v
echo "== ingest (offline) =="
python3 methods/ingest.py
echo "== analyze (seed) =="
python3 methods/analyze.py >/dev/null && echo "analyze OK → out/intel-report.md"
