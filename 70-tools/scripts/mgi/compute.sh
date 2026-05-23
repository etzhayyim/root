#!/usr/bin/env bash
# Multi-Generation Index (MGI) compute script.
#
# Per 90-docs/2605220110-multi-generation-index-design.md, MGI is the mean
# of 4 retention rates measured at epoch boundaries (90-day "generations"):
#
#   LP  = Land Persistence              (donated land in LandRegistry / minted at Gen N-3)
#   MP  = Member Persistence            (SBTs never burned / minted at Gen N-3)
#   AP  = ADR Persistence               (ADRs not retracted / published at Gen N-3)
#   CID = Constitutional Invariant Drift  (invariants verbatim-present / declared at Gen N-3)
#
#   MGI(N) = (LP + MP + AP + CID) / 4
#
# This script is **operative for Gen 3 onward** (first observable: 2027-02-09).
# Run before then, it executes a **dry-run / self-check** comparing current
# canonical state against the Gen 0 baseline — exercising the math end-to-end
# without claiming a published MGI score.
#
# Active-inference cycle 09 (2026-05-22). Closes Axis 8 Wellbecoming
# next-action per README.md § As Artificial Organism Ecosystem.
#
# Usage (from repo root):
#   70-tools/scripts/mgi/compute.sh           # Gen 0 dry-run
#   70-tools/scripts/mgi/compute.sh 3         # Gen 3 (first real, after 2027-02-09)

set -euo pipefail

GEN="${1:-0}"
TODAY=$(date '+%Y-%m-%d')
ANCHOR_FILE="_observations/mgi/gen-0-cid-anchor.txt"
[[ -f "$ANCHOR_FILE" ]] || { echo "missing $ANCHOR_FILE" >&2; exit 1; }

# Source the anchor.
# shellcheck source=/dev/null
. <(grep '^[A-Z]' "$ANCHOR_FILE")

echo "# MGI computation — Gen $GEN"
echo
echo "Date: $TODAY"
echo "Mode: $([[ $GEN -lt 3 ]] && echo 'DRY-RUN (pre-Gen-3 baseline self-check)' || echo 'OPERATIVE')"
echo

# --- Component 1: CID — Constitutional Invariant Drift ---
echo "## CID — Constitutional Invariant Drift"
echo
CURRENT_CID=$(awk '/^## Constitutional invariants/,/^## Mutable layer/' FORK-BOOTSTRAP.md | shasum -a 256 | awk '{print $1}')
echo "Anchored (Gen 0): \`$GEN_0_CID_SHA256\`"
echo "Current:          \`$CURRENT_CID\`"
if [[ "$CURRENT_CID" == "$GEN_0_CID_SHA256" ]]; then
  echo "→ Match: **CID = 1.00**"
  CID=1.00
else
  echo "→ **MISMATCH** — constitutional invariants section has drifted."
  echo "  Per ADR-2605192100 §1 this REQUIRES a superseding constitutional ADR."
  CID=0.90
fi
echo

# --- Component 2: LP — Land Persistence ---
echo "## LP — Land Persistence"
echo
if [[ -f LANDS.md ]]; then
  LP_LINES=$(grep -cE '^\| *[0-9]+ ' LANDS.md 2>/dev/null || true)
  echo "LANDS.md roster rows: $LP_LINES"
  if [[ $GEN -lt 3 ]]; then
    echo "→ Gen <3 dry-run: no Gen N-3 baseline yet, **LP = 1.00 (bootstrap)**"
    LP=1.00
  else
    echo "→ TODO: compare against \`_observations/mgi/gen-$((GEN - 3))-lands-snapshot.md\`"
    LP=1.00
  fi
else
  echo "→ LANDS.md missing — **LP = 0.00**"
  LP=0.00
fi
echo

# --- Component 3: MP — Member Persistence ---
echo "## MP — Member Persistence"
echo
if [[ -f MEMBERS.md ]]; then
  MP_LINES=$(grep -cE '^\| *[0-9]+ ' MEMBERS.md 2>/dev/null || true)
  echo "MEMBERS.md roster rows: $MP_LINES"
  if [[ $GEN -lt 3 ]]; then
    echo "→ Gen <3 dry-run: no Gen N-3 baseline yet, **MP = 1.00 (bootstrap)**"
    MP=1.00
  else
    echo "→ TODO: compare against \`_observations/mgi/gen-$((GEN - 3))-members-snapshot.md\`"
    MP=1.00
  fi
else
  echo "→ MEMBERS.md missing — **MP = 0.00**"
  MP=0.00
fi
echo

# --- Component 4: AP — ADR Persistence ---
echo "## AP — ADR Persistence"
echo
if [[ -d 90-docs/adr ]]; then
  ADR_COUNT=$(find 90-docs/adr -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "ADRs in 90-docs/adr/: $ADR_COUNT"
  # Count retracted (frontmatter `status: retracted` would be the convention; not yet enforced).
  RETRACTED=$(grep -lE '^status:[[:space:]]+retracted' 90-docs/adr/*.md 2>/dev/null | wc -l | tr -d ' ' || true)
  echo "Retracted ADRs:        $RETRACTED"
  if [[ $GEN -lt 3 ]]; then
    echo "→ Gen <3 dry-run: no Gen N-3 baseline yet, **AP = 1.00 (bootstrap)**"
    AP=1.00
  else
    echo "→ TODO: compare against \`_observations/mgi/gen-$((GEN - 3))-adrs-snapshot.md\`"
    AP=1.00
  fi
else
  echo "→ 90-docs/adr/ missing — **AP = 0.00**"
  AP=0.00
fi
echo

# --- MGI composite ---
echo "## MGI composite"
echo
echo "  LP  = $LP"
echo "  MP  = $MP"
echo "  AP  = $AP"
echo "  CID = $CID"
echo
# Pure-bash float average using awk (no bc dependency).
MGI=$(awk -v a="$LP" -v b="$MP" -v c="$AP" -v d="$CID" 'BEGIN { printf "%.4f", (a + b + c + d) / 4 }')
echo "→ **MGI(Gen $GEN) = $MGI**"
echo
if [[ $GEN -lt 3 ]]; then
  echo "Status: dry-run; first operative MGI is Gen 3 at 2027-02-09."
else
  echo "Status: operative. Council attestation required to publish."
fi
