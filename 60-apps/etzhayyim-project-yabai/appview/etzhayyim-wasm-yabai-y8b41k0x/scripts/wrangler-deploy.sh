#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$APP_DIR/../../../../" && pwd)"
WRANGLER="$REPO_ROOT/node_modules/wrangler/bin/wrangler.js"

if [[ ! -f "$WRANGLER" ]]; then
  echo "wrangler not found at $WRANGLER"
  exit 1
fi

if [[ "${FORCE_UI_BUILD:-0}" == "1" ]]; then
  cd "$APP_DIR/svelte"
  rm -rf "$APP_DIR/svelte/.svelte-kit-wrangler/output"
  npm run build
else
  echo "Skipping UI rebuild (set FORCE_UI_BUILD=1 to rebuild)."
fi

cd "$APP_DIR"
CI=1 node "$WRANGLER" deploy --config "$APP_DIR/wrangler.toml"
