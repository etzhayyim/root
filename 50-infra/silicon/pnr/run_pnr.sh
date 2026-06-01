#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# Full RTL→GDSII place-and-route + static timing for a silicon block, via
# OpenLane2 (OpenROAD + yosys + magic + klayout + netgen) on the sky130hd OPEN
# PDK. Open-source EDA + open PDK only — sky130 is Apache/CC, not NDA
# (50-infra/silicon/CLAUDE.md rule 1).
#
# This is the deepest open rung: real placement, clock-tree synthesis, global +
# detailed routing, parasitic-aware STA (→ f_max), DRC and LVS. It produces a
# GDSII — on sky130, NOT the TSMC N5 tape-out (Phase 3, Council-gated).
#
# Prereqs: Docker (OrbStack ok) + `pip install openlane` (.venv-ol).
# Usage:   pnr/run_pnr.sh [design]      # default design: pe_array
set -euo pipefail
PNR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIL="$(cd "$PNR_DIR/.." && pwd)"
DESIGN="${1:-pe_array}"
D="$PNR_DIR/$DESIGN"

# Refresh src/ from the canonical RTL (src/ is gitignored — no duplicate commit).
mkdir -p "$D/src"
cp "$SIL/shared-ip/ternary-pe/rtl/ternary_pe.sv" "$D/src/"
cp "$SIL/iwakura/rtl/zero_skip_dispatcher.sv"    "$D/src/"
cp "$SIL/iwakura/rtl/pe_array.sv"                "$D/src/"

cd "$D"
echo "── OpenLane2 RTL→GDSII: $DESIGN (sky130hd) ──"
# --docker-no-tty MUST precede --dockerized (no TTY in non-interactive shells).
"$SIL/.venv-ol/bin/openlane" --docker-no-tty --dockerized "$D/config.json"

# Surface the headline metrics.
python3 "$PNR_DIR/report_pnr.py" "$D"
