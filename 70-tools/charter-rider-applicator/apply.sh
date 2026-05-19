#!/usr/bin/env bash
# charter-rider-applicator/apply.sh
#
# Adds NOTICE + CHARTER-RIDER.md symlink to every sub-repo / package
# under etzhayyim/root with an Apache-2.0 license declaration.
#
# Per ADR-2605192200 v2.0 (IP-Free-Release with Charter Compliance Rider v2.0)
# §3.4 retro-active applicator.
#
# Idempotent: re-running is safe (skip if NOTICE already references the Rider).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RIDER_FILE="$ROOT/CHARTER-RIDER.md"

if [[ ! -f "$RIDER_FILE" ]]; then
  echo "ERROR: $RIDER_FILE missing. Run from etzhayyim/root with CHARTER-RIDER.md present." >&2
  exit 1
fi

added=0
skipped=0

while IFS= read -r manifest; do
  pkg_dir="$(dirname "$manifest")"

  # Skip node_modules, vendored dirs, etc.
  if [[ "$pkg_dir" =~ node_modules|/.git/|target/|dist/|build/|coverage/ ]]; then
    continue
  fi

  # Only proceed if the manifest declares Apache-2.0
  if ! grep -q "Apache-2.0" "$manifest" 2>/dev/null; then
    continue
  fi

  notice_path="$pkg_dir/NOTICE"
  rider_path="$pkg_dir/CHARTER-RIDER.md"

  # Add NOTICE if absent or doesn't reference Rider
  if [[ ! -f "$notice_path" ]] || ! grep -q "etzhayyim Charter Compliance Rider" "$notice_path"; then
    cat > "$notice_path" <<EOF
This product includes software developed by etzhayyim
(https://etzhayyim.com / did:web:etzhayyim.com).

This software is distributed under the Apache License 2.0 with the
etzhayyim Charter Compliance Rider v2.0 (see CHARTER-RIDER.md).

By using, modifying, or redistributing this software, you accept both
the Apache License 2.0 and the Charter Compliance Rider.

Mission Charter: ADR-2605192100
Rider ADR: ADR-2605192200 (v2.0)
EOF
    echo "added NOTICE: $notice_path"
    added=$((added+1))
  fi

  # Add symlink to repo-root CHARTER-RIDER.md (idempotent)
  if [[ ! -e "$rider_path" ]]; then
    # Compute relative path from pkg_dir to repo root
    rel="$(python3 -c "import os; print(os.path.relpath('$ROOT', '$pkg_dir'))")"
    ln -s "$rel/CHARTER-RIDER.md" "$rider_path"
    echo "added symlink: $rider_path → $rel/CHARTER-RIDER.md"
    added=$((added+1))
  else
    skipped=$((skipped+1))
  fi
done < <(find "$ROOT" \( -name package.json -o -name Cargo.toml -o -name pyproject.toml \) -type f 2>/dev/null)

echo ""
echo "Done. Added: $added entries. Skipped (already present): $skipped."
