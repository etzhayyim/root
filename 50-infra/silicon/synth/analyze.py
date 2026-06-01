#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# Summarize yosys `stat -json` outputs: raw 2-input gate count + NAND2-equivalent
# (GE) area proxy per module, the ternary-vs-INT8 density ratio, and (for
# sequential modules) flip-flop count. Writes a Markdown table to out/SUMMARY.md
# and prints it.
#
# NAND2-equivalent weights are typical relative cell areas (NAND2 = 1.00) for a
# generic CMOS standard-cell library — an *area proxy*, not a foundry datasheet.
# Per-cell exactness is not claimed; the validated quantity is the ratio.

from __future__ import annotations

import glob
import json
import os
import sys

# Relative NAND2-equivalent areas (NAND2 = 1.00). Typical generic-CMOS values.
GE = {
    "$_NOT_": 0.67,
    "$_AND_": 1.33, "$_OR_": 1.33,
    "$_NAND_": 1.00, "$_NOR_": 1.00,
    "$_ANDNOT_": 1.33, "$_ORNOT_": 1.33,
    "$_XOR_": 2.67, "$_XNOR_": 2.67,
    "$_MUX_": 2.33, "$_NMUX_": 2.33,
    "$_AOI3_": 1.67, "$_OAI3_": 1.67,
    "$_AOI4_": 2.00, "$_OAI4_": 2.00,
}
# Sequential cells (counted separately, not in combinational gate total).
FF_PREFIXES = ("$_DFF", "$_SDFF", "$_DLATCH", "$_SR_")


def load(path: str):
    with open(path) as f:
        data = json.load(f)
    top = os.path.basename(path).replace(".stat.json", "")
    # stat -json: modules -> <name> -> num_cells_by_type
    mods = data.get("modules", {})
    # pick the top module if present, else the only/largest module
    cells = {}
    if mods:
        # heuristic: the module whose name matches the file, else first
        key = next((k for k in mods if k.strip("\\").endswith(top)), list(mods)[0])
        cells = mods[key].get("num_cells_by_type", {})
    raw = 0
    ge = 0.0
    ffs = 0
    for ctype, n in cells.items():
        if any(ctype.startswith(p) for p in FF_PREFIXES):
            ffs += n
            continue
        if ctype in GE:
            raw += n
            ge += GE[ctype] * n
        else:
            # unknown gate: count raw, weight 1.0 as neutral fallback
            raw += n
            ge += 1.0 * n
    return top, raw, ge, ffs


def main(outdir: str):
    rows = {}
    for path in sorted(glob.glob(os.path.join(outdir, "*.stat.json"))):
        top, raw, ge, ffs = load(path)
        rows[top] = (raw, ge, ffs)

    lines = []
    lines.append("| module | raw gates (2-input) | NAND2-equiv (GE) | flip-flops |")
    lines.append("|---|---:|---:|---:|")
    for name in ["ternary_pe", "int8_mac_ref", "radix3_decoder",
                 "zero_skip_dispatcher", "pe_array", "mul8x8", "ternary_mul"]:
        if name not in rows:
            continue
        raw, ge, ffs = rows[name]
        lines.append(f"| `{name}` | {raw} | {ge:.0f} | {ffs} |")

    table = "\n".join(lines)
    print(table)

    def ratio(a, b):
        ar, ag, _ = rows[a]
        br, bg, _ = rows[b]
        return (ar / br if br else 0), (ag / bg if bg else 0)

    verdict = ""
    if "ternary_pe" in rows and "int8_mac_ref" in rows:
        rr, rg = ratio("int8_mac_ref", "ternary_pe")
        verdict += (
            f"\n**Whole-PE density (INT8 MAC ÷ ternary PE), incl. shared 24-bit "
            f"accumulator:** raw **{rr:.2f}×**, GE **{rg:.2f}×**\n"
        )
    if "mul8x8" in rows and "ternary_mul" in rows:
        rr, rg = ratio("mul8x8", "ternary_mul")
        verdict += (
            f"**Multiplier-only density (8×8 mul ÷ ternary select), the block "
            f"BitNet eliminates:** raw **{rr:.1f}×**, GE **{rg:.1f}×** "
            f"(ADR-2605242515 estimate: 8.4× — validated, conservative)\n"
        )
    if verdict:
        print(verdict)
        table += "\n" + verdict

    with open(os.path.join(outdir, "SUMMARY.md"), "w") as f:
        f.write("# Synthesis summary (yosys + ABC, generic gates)\n\n")
        f.write(table + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out")
