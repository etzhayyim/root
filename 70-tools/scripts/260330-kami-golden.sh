#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/40-engine/kotoba/crates/kotoba-kotodama/hosts/kotodama-kami-host/Cargo.toml"
GOLDEN_DIR="$ROOT/40-engine/kotoba/crates/kotoba-kotodama/hosts/kotodama-kami-host/golden"

usage() {
  cat <<'EOF'
usage:
  scripts/260330-kami-golden.sh update
  scripts/260330-kami-golden.sh verify
EOF
}

cmd="${1:-}"
case "$cmd" in
  update)
    cargo run --manifest-path "$MANIFEST" -- \
      --update-golden "$GOLDEN_DIR" \
      --artifact-dir /tmp/kotodama-kami-golden-update
    ;;
  verify)
    cargo run --manifest-path "$MANIFEST" -- \
      --verify-golden "$GOLDEN_DIR" \
      --min-uiux-score 85 \
      --artifact-dir /tmp/kotodama-kami-golden-verify
    ;;
  *)
    usage
    exit 2
    ;;
esac
