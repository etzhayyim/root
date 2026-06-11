#!/usr/bin/env bash
set -euo pipefail

base_dir="projects/etzhayyim-project-open-unispsc/wasm"
donor="$base_dir/etzhayyim-wasm-unispsc-seg-43-it-s43t7k2m/main.go"
marker_primary='var schemaReady bool'
marker_fallback='func init()'

if [[ ! -f "$donor" ]]; then
  echo "donor main.go not found: $donor" >&2
  exit 1
fi

donor_line=$(grep -n "^${marker_primary}" "$donor" | head -n1 | cut -d: -f1 || true)
if [[ -z "${donor_line}" ]]; then
  echo "marker not found in donor: ${marker_primary}" >&2
  exit 1
fi

donor_tail=$(mktemp)
tail -n +"$donor_line" "$donor" > "$donor_tail"

updated=0
skipped=0
for target in "$base_dir"/etzhayyim-wasm-unispsc-seg-*/main.go; do
  [[ "$target" == "$donor" ]] && continue

  target_line=$(grep -n "^${marker_primary}" "$target" | head -n1 | cut -d: -f1 || true)
  if [[ -z "${target_line}" ]]; then
    target_line=$(grep -n "^${marker_fallback}" "$target" | head -n1 | cut -d: -f1 || true)
  fi
  if [[ -z "${target_line}" ]]; then
    echo "skip (marker missing): $target"
    skipped=$((skipped + 1))
    continue
  fi

  tmp="${target}.tmp"
  head -n $((target_line - 1)) "$target" > "$tmp"
  cat "$donor_tail" >> "$tmp"

  # Ensure strings import exists for copied function bodies.
  if ! grep -q '"strings"' "$tmp"; then
    awk '
      BEGIN{added=0}
      /^import \(/ && !added { print; print "\t\"strings\""; added=1; next }
      { print }
    ' "$tmp" > "${tmp}.imports" && mv "${tmp}.imports" "$tmp"
  fi

  mv "$tmp" "$target"
  updated=$((updated + 1))
done

rm -f "$donor_tail"

echo "updated=$updated skipped=$skipped"
