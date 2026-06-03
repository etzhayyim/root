#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find repo root
REPO_ROOT="$SCRIPT_DIR"
while [[ "$REPO_ROOT" != "/" ]]; do
  if [[ -f "$REPO_ROOT/MODULE.bazel" ]] && [[ -d "$REPO_ROOT/packages/ts/appshellv2" ]]; then
    break
  fi
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done

if [[ "$REPO_ROOT" == "/" ]]; then
  echo "ERROR: Could not find repo root (MODULE.bazel + packages/ts/appshellv2)" >&2
  exit 1
fi

APPSHELL_DIST="$REPO_ROOT/packages/ts/appshellv2/dist"

# Build appshell if not already done
if [[ ! -d "$APPSHELL_DIST" ]]; then
  echo "Building appshellv2..."
  (cd "$REPO_ROOT/packages/ts/appshellv2" && pnpm install && pnpm run build)
fi

# Create temp sandbox
SANDBOX=$(mktemp -d)
trap "rm -rf $SANDBOX" EXIT

rsync -a --exclude=node_modules --exclude=build --exclude=.svelte-kit "$SCRIPT_DIR/" "$SANDBOX/"

# Install dependencies and build
cd "$SANDBOX"
pnpm install
pnpm run build

# Copy output back
rsync -a "$SANDBOX/build/" "$SCRIPT_DIR/build/"
rsync -a "$SANDBOX/.svelte-kit/" "$SCRIPT_DIR/.svelte-kit/"

echo "Build complete: $SCRIPT_DIR/build/"
