#!/usr/bin/env bash
# charter-rider-applicator/apply.sh
#
# Adds NOTICE + CHARTER-RIDER.md symlink to every sub-repo / package
# under etzhayyim/root with an Apache-2.0 license declaration, AND re-stamps
# any existing NOTICE whose Rider version string is stale.
#
# Per ADR-2605192200 (Rider spec) → reframed v3.0 (ADR-2606062100, 3-Tier) →
# v3.1 (ADR-2606082400, §2(c) reciprocity axis). The Rider TEXT per package is a
# symlink to the repo-root CHARTER-RIDER.md, so the substance is always current;
# this script keeps the NOTICE *version string* in sync with it.
#
# Idempotent: re-running is safe. A NOTICE that already references the CURRENT
# version is skipped; one that references an OLDER version is re-stamped in place
# (only the two version-bearing lines change — any custom trailer such as an
# "Actor ADR:" line is preserved). Historical version references in ADRs / READMEs
# are NOT touched — this script only edits NOTICE files.

set -euo pipefail

# ── current Rider version + ADR chain (single source of truth) ──────────────
CURRENT_VER="v3.1"
RIDER_DECL="etzhayyim Charter Compliance Rider ${CURRENT_VER} (see CHARTER-RIDER.md)."
RIDER_ADR_LINE="Rider ADR: ADR-2605192200 + ADR-2606062100 + ADR-2606082400 (${CURRENT_VER})"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RIDER_FILE="$ROOT/CHARTER-RIDER.md"

if [[ ! -f "$RIDER_FILE" ]]; then
  echo "ERROR: $RIDER_FILE missing. Run from etzhayyim/root with CHARTER-RIDER.md present." >&2
  exit 1
fi

added=0
restamped=0
skipped=0

# Re-stamp the two version-bearing NOTICE lines in place, preserving everything
# else (custom "Actor ADR:" trailers, the Mission Charter line, etc.).
restamp_notice() {
  local f="$1"
  perl -i -pe "s|Charter Compliance Rider v\d+\.\d+ \(see [^)]+\)|Charter Compliance Rider ${CURRENT_VER} (see CHARTER-RIDER.md)|g" "$f"
  perl -i -pe "s|^Rider ADR:.*\(v\d+\.\d+\).*\$|${RIDER_ADR_LINE}|" "$f"
}

while IFS= read -r manifest; do
  pkg_dir="$(dirname "$manifest")"

  # Skip node_modules, vendored dirs, etc.
  if [[ "$pkg_dir" =~ node_modules|/.git/|target/|dist/|build/|coverage/ ]]; then
    continue
  fi

  # Skip 3rd-party vendored packages (Foundry lib/, Rust vendor/, our forks)
  # Apache 2.0 §4 requires preserving original NOTICE files of 3rd-party works;
  # we must NOT add our Charter Rider to forge-std / openzeppelin / etc.
  if [[ "$pkg_dir" =~ /lib/|/vendor/|-fork/|-fork$ ]]; then
    continue
  fi

  # Only proceed if the manifest declares Apache-2.0
  if ! grep -q "Apache-2.0" "$manifest" 2>/dev/null; then
    continue
  fi

  notice_path="$pkg_dir/NOTICE"
  rider_path="$pkg_dir/CHARTER-RIDER.md"

  if [[ ! -f "$notice_path" ]] || ! grep -q "etzhayyim Charter Compliance Rider" "$notice_path"; then
    # First-time stamp.
    cat > "$notice_path" <<EOF
This product includes software developed by etzhayyim
(https://etzhayyim.com / did:web:etzhayyim.com).

This software is distributed under the Apache License 2.0 with the
${RIDER_DECL}

By using, modifying, or redistributing this software, you accept both
the Apache License 2.0 and the Charter Compliance Rider.

Mission Charter: ADR-2605192100
${RIDER_ADR_LINE}
EOF
    echo "added NOTICE: $notice_path"
    added=$((added+1))
  elif ! grep -q "Charter Compliance Rider ${CURRENT_VER}" "$notice_path"; then
    # Exists but stale version → re-stamp in place (preserve custom trailer).
    restamp_notice "$notice_path"
    echo "re-stamped NOTICE → ${CURRENT_VER}: $notice_path"
    restamped=$((restamped+1))
  else
    skipped=$((skipped+1))
  fi

  # Add symlink to repo-root CHARTER-RIDER.md (idempotent)
  if [[ ! -e "$rider_path" ]]; then
    rel="$(python3 -c "import os; print(os.path.relpath('$ROOT', '$pkg_dir'))")"
    ln -s "$rel/CHARTER-RIDER.md" "$rider_path"
    echo "added symlink: $rider_path → $rel/CHARTER-RIDER.md"
    added=$((added+1))
  fi
done < <(find "$ROOT" \( -name package.json -o -name Cargo.toml -o -name pyproject.toml \) -type f 2>/dev/null)

# ── Sweep ALL Rider NOTICE files (catch any outside manifest-Apache-2.0 dirs) ──
# Comprehensive re-stamp so no stale version string survives anywhere a NOTICE
# already declares the Rider (still NOTICE-only; never ADRs / READMEs).
while IFS= read -r notice_path; do
  [[ "$notice_path" =~ /lib/|/vendor/|-fork/|node_modules ]] && continue
  if grep -q "etzhayyim Charter Compliance Rider" "$notice_path" \
     && ! grep -q "Charter Compliance Rider ${CURRENT_VER}" "$notice_path"; then
    restamp_notice "$notice_path"
    echo "re-stamped NOTICE → ${CURRENT_VER}: $notice_path"
    restamped=$((restamped+1))
  fi
done < <(find "$ROOT" -name NOTICE -type f 2>/dev/null)

echo ""
echo "Done. Added: $added · Re-stamped: $restamped · Skipped (already ${CURRENT_VER}): $skipped."
