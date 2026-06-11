#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# Map the silicon RTL to the **SkyWater sky130 open PDK** high-density standard
# cells (sky130_fd_sc_hd) with yosys + ABC, reporting REAL cell area (µm²) and
# std-cell counts. This is one rung past generic synthesis: an actual,
# open-source, manufacturable cell library.
#
# Open PDK only — sky130 is Apache-2.0 / CC, NOT under NDA, so it is allowed in
# the committed flow (50-infra/silicon/CLAUDE.md rule 1 forbids *commercial* EDA
# and *NDA* PDKs; sky130 is neither). The liberty file is fetched on demand and
# gitignored.
#
# STILL NOT done here: place-and-route, parasitic extraction, timing closure,
# GDSII. Those need OpenROAD/OpenLane (Phase 3). Area here is pre-layout
# std-cell area (no routing/whitespace), an optimistic lower bound.
#
#   50-infra/silicon/synth/run_synth_sky130.sh

set -euo pipefail
SYNTH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIL="$(cd "$SYNTH_DIR/.." && pwd)"
OUT="$SYNTH_DIR/out-sky130"
LIB="$SYNTH_DIR/pdk/sky130_fd_sc_hd__tt_025C_1v80.lib"
mkdir -p "$OUT"

if [[ ! -f "$LIB" ]]; then
  echo "sky130 liberty missing — fetching (~12 MB, open PDK)…"
  mkdir -p "$SYNTH_DIR/pdk"
  curl -fsSL \
    "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib" \
    -o "$LIB"
fi

PE="$SIL/shared-ip/ternary-pe/rtl"; RX="$SIL/shared-ip/radix3-packer/rtl"; IW="$SIL/iwakura/rtl"

declare -a NAMES=(ternary_pe int8_mac_ref radix3_decoder zero_skip_dispatcher pe_array mul8x8 ternary_mul)
declare -a TOPS=(ternary_pe int8_mac_ref radix3_decoder zero_skip_dispatcher pe_array mul8x8 ternary_mul)
declare -a SRCS=(
  "$PE/ternary_pe.sv"
  "$PE/int8_mac_ref.sv"
  "$RX/radix3_decoder.sv"
  "$IW/zero_skip_dispatcher.sv"
  "$PE/ternary_pe.sv $IW/pe_array.sv"
  "$SYNTH_DIR/ref/mul_compare.sv"
  "$SYNTH_DIR/ref/mul_compare.sv"
)

declare -A AREA
for i in "${!NAMES[@]}"; do
  name="${NAMES[$i]}"; top="${TOPS[$i]}"; src="${SRCS[$i]}"
  yosys -p "read_liberty -lib $LIB; read_verilog -sv $src; synth -top $top -flatten; dfflibmap -liberty $LIB; abc -liberty $LIB; stat -liberty $LIB" \
    > "$OUT/$name.log" 2>&1
  a=$(grep "Chip area" "$OUT/$name.log" | grep -oE "[0-9]+\.[0-9]+" | tail -1)
  AREA[$name]="$a"
  echo "── $name : ${a} µm²"
done

echo
echo "| module | sky130 area (µm²) |"
echo "|---|---:|"
for name in "${NAMES[@]}"; do printf "| \`%s\` | %s |\n" "$name" "${AREA[$name]}"; done

# Density ratios.
awk -v p="${AREA[ternary_pe]}" -v i="${AREA[int8_mac_ref]}" \
    -v m="${AREA[mul8x8]}" -v t="${AREA[ternary_mul]}" 'BEGIN{
  printf "\n**Whole-PE density (INT8 ÷ ternary), sky130 area:** %.2f×\n", i/p;
  printf "**Multiplier-only density (mul8x8 ÷ ternary_mul):** %.2f×\n", m/t;
}'
