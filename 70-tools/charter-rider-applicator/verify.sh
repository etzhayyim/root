#!/usr/bin/env bash
# charter-rider-applicator/verify.sh
#
# Verifies that every Apache-2.0 sub-repo / package has the NOTICE +
# CHARTER-RIDER.md symlink present, content-consistent with the repo-root
# CHARTER-RIDER.md, AND stamped with the CURRENT Rider version string.
#
# Per ADR-2605192200 → v3.0 (ADR-2606062100) → v3.1 (ADR-2606082400). The
# current version is derived from the repo-root CHARTER-RIDER.md header, so this
# check auto-tracks future bumps and flags any NOTICE left on a stale version
# (run ./apply.sh to re-stamp).
#
# Exit code 0 if all green, 1 if any missing / drifted / stale.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RIDER_FILE="$ROOT/CHARTER-RIDER.md"
EXPECTED_HASH="$(shasum -a 256 "$RIDER_FILE" | awk '{print $1}')"

# Derive the current version from the canonical Rider header (single source of truth).
CURRENT_VER="$(grep -m1 -oE 'Charter Compliance Rider v[0-9]+\.[0-9]+' "$RIDER_FILE" | grep -oE 'v[0-9]+\.[0-9]+')"
if [[ -z "$CURRENT_VER" ]]; then
  echo "ERROR: could not derive current Rider version from $RIDER_FILE" >&2
  exit 1
fi

missing_notice=()
missing_rider=()
mismatch_rider=()
stale_version=()
checked=0

while IFS= read -r manifest; do
  pkg_dir="$(dirname "$manifest")"

  if [[ "$pkg_dir" =~ node_modules|/.git/|target/|dist/|build/|coverage/ ]]; then
    continue
  fi

  # Skip 3rd-party vendored packages (must match apply.sh exclusion list)
  if [[ "$pkg_dir" =~ /lib/|/vendor/|-fork/|-fork$ ]]; then
    continue
  fi

  if ! grep -q "Apache-2.0" "$manifest" 2>/dev/null; then
    continue
  fi

  checked=$((checked+1))

  if [[ ! -f "$pkg_dir/NOTICE" ]] || ! grep -q "etzhayyim Charter Compliance Rider" "$pkg_dir/NOTICE"; then
    missing_notice+=("$pkg_dir")
  elif ! grep -q "Charter Compliance Rider ${CURRENT_VER}" "$pkg_dir/NOTICE"; then
    stale_version+=("$pkg_dir")
  fi

  if [[ ! -e "$pkg_dir/CHARTER-RIDER.md" ]]; then
    missing_rider+=("$pkg_dir")
  else
    actual_hash="$(shasum -a 256 "$pkg_dir/CHARTER-RIDER.md" | awk '{print $1}')"
    if [[ "$actual_hash" != "$EXPECTED_HASH" ]]; then
      mismatch_rider+=("$pkg_dir")
    fi
  fi
done < <(find "$ROOT" \( -name package.json -o -name Cargo.toml -o -name pyproject.toml \) -type f 2>/dev/null)

echo "Checked: $checked Apache-2.0 manifests (current Rider version: ${CURRENT_VER})"

ok=true
if [[ ${#missing_notice[@]} -gt 0 ]]; then
  echo ""
  echo "MISSING NOTICE in:"
  printf '  %s\n' "${missing_notice[@]}"
  ok=false
fi

if [[ ${#missing_rider[@]} -gt 0 ]]; then
  echo ""
  echo "MISSING CHARTER-RIDER.md in:"
  printf '  %s\n' "${missing_rider[@]}"
  ok=false
fi

if [[ ${#mismatch_rider[@]} -gt 0 ]]; then
  echo ""
  echo "CHARTER-RIDER.md content mismatch (drift detected) in:"
  printf '  %s\n' "${mismatch_rider[@]}"
  ok=false
fi

if [[ ${#stale_version[@]} -gt 0 ]]; then
  echo ""
  echo "NOTICE Rider version string STALE (not ${CURRENT_VER}) in:"
  printf '  %s\n' "${stale_version[@]}"
  ok=false
fi

if $ok; then
  echo ""
  echo "✓ All Apache-2.0 manifests have NOTICE + CHARTER-RIDER.md correctly applied at ${CURRENT_VER}."
  exit 0
else
  echo ""
  echo "✗ Run ./apply.sh to fix the above."
  exit 1
fi
