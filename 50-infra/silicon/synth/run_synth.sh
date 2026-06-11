#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# Synthesize every silicon RTL module to a generic 2-input gate library with
# yosys + ABC, emit per-module JSON cell counts, then summarize raw and
# NAND2-equivalent (GE) gate counts + the ternary-vs-INT8 density ratio.
#
# Open-source only (yosys + abc); no PDK / liberty. Run from anywhere:
#   50-infra/silicon/synth/run_synth.sh

set -euo pipefail

SYNTH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIL="$(cd "$SYNTH_DIR/.." && pwd)"
OUT="$SYNTH_DIR/out"
TMPL="$SYNTH_DIR/synth.ys.tmpl"
mkdir -p "$OUT"

PE="$SIL/shared-ip/ternary-pe/rtl"
RX="$SIL/shared-ip/radix3-packer/rtl"
IW="$SIL/iwakura/rtl"

# module | top | space-separated sources
run() {
  local name="$1" top="$2" srcs="$3"
  local ys="$OUT/$name.ys" json="$OUT/$name.stat.json"
  sed -e "s|@SOURCES@|$srcs|" -e "s|@TOP@|$top|" -e "s|@JSON@|$json|" "$TMPL" > "$ys"
  echo "── synth: $name (top=$top)"
  yosys -q "$ys" > "$OUT/$name.log" 2>&1 || { echo "  FAILED — see $OUT/$name.log"; tail -5 "$OUT/$name.log"; return 1; }
}

run ternary_pe           ternary_pe           "$PE/ternary_pe.sv"
run int8_mac_ref         int8_mac_ref         "$PE/int8_mac_ref.sv"
run radix3_decoder       radix3_decoder       "$RX/radix3_decoder.sv"
run zero_skip_dispatcher zero_skip_dispatcher "$IW/zero_skip_dispatcher.sv"
run pe_array             pe_array             "$PE/ternary_pe.sv $IW/pe_array.sv"

# Multiplier-only micro-comparison (isolates the block ternary eliminates).
run mul8x8               mul8x8               "$SYNTH_DIR/ref/mul_compare.sv"
run ternary_mul          ternary_mul          "$SYNTH_DIR/ref/mul_compare.sv"

python3 "$SYNTH_DIR/analyze.py" "$OUT"
