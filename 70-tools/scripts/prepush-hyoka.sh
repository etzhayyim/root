#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

exec gftd monitor shinka \
  --dir "$ROOT/60-apps" \
  --hyoka \
  --store \
  "$@"
