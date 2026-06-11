#!/usr/bin/env bash
# Copy BPMN files from 60-apps/etzhayyim-project-states/data/gov/{iso}/bpmn/*.bpmn
# into svelte/static/bpmn-files/{iso}/bpmn/*.bpmn so they are served as static
# assets by the yoro Workers Assets binding.
#
# Run during pre-build. The target dir is gitignored.

set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
REPO_ROOT=$(cd "$ROOT/../../../../.." && pwd)
SRC_DIR="$REPO_ROOT/60-apps/etzhayyim-project-states/data/gov"
# Target is the Workers Assets binding dir (yoro-ui-g00h5zto/static/),
# NOT svelte/static/ (this project is a plain Vite SPA, not SvelteKit —
# `static/` is not a magic folder). Also mirror into svelte/static/ for
# dev-server convenience.
WORKER_ASSETS_DIR="$(cd "$ROOT/.." && pwd)/static"
DEST_DIR="$WORKER_ASSETS_DIR/bpmn-files"
MIRROR_DIR="$ROOT/static/bpmn-files"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "[copy-bpmn-files] source dir not found: $SRC_DIR" >&2
  exit 0  # non-fatal
fi

mkdir -p "$DEST_DIR" "$MIRROR_DIR"

copied=0
for iso_dir in "$SRC_DIR"/*/; do
  iso=$(basename "$iso_dir")
  bpmn_src="$iso_dir/bpmn"
  [[ -d "$bpmn_src" ]] || continue
  for dest_parent in "$DEST_DIR" "$MIRROR_DIR"; do
    target="$dest_parent/$iso/bpmn"
    mkdir -p "$target"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete "$bpmn_src/" "$target/"
    else
      rm -rf "$target"
      cp -a "$bpmn_src" "$target"
    fi
  done
  n=$(find "$DEST_DIR/$iso/bpmn" -name '*.bpmn' | wc -l | tr -d ' ')
  if [[ "$n" -gt 0 ]]; then
    copied=$((copied + n))
  fi
done

echo "[copy-bpmn-files] copied $copied BPMN files to $DEST_DIR (+ mirror)"
