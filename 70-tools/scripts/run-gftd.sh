#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

if [[ -f "$ROOT/packages/cmd/gftd/main.go" ]] && [[ "${GFTD_USE_GLOBAL:-0}" != "1" ]]; then
  cd "$ROOT/packages/cmd/gftd"
  exec go run . "$@"
fi

if command -v gftd >/dev/null 2>&1; then
  exec gftd "$@"
fi

echo "gftd binary not found and local source unavailable at $ROOT/packages/cmd/gftd" >&2
exit 1
