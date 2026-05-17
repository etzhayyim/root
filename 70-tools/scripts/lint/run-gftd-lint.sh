#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: run-gftd-lint.sh <target>" >&2
  exit 2
fi

TARGET="$1"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

if command -v gftd >/dev/null 2>&1; then
  if gftd help 2>/dev/null | grep -qE '^[[:space:]]+lint[[:space:]]'; then
    exec gftd lint "$TARGET" --root "$ROOT"
  fi
fi

exec bash -lc "cd \"$ROOT/packages/cmd/gftd\" && go run . lint \"$TARGET\" --root \"$ROOT\""
