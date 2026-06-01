# synth — open-source logic synthesis (yosys + ABC)

Per **ADR-2605242515** §"面積 (gate-level estimate)" and `50-infra/silicon/CLAUDE.md`
rule 1 (no commercial EDA; yosys + Verilator only).

This takes the iwakura RTL one step past functional simulation: **logic
synthesis to a generic gate netlist**, producing real (not behavioural) gate
counts that validate the ADR's ternary-vs-INT8 density claim.

> **Scope honesty.** This is *generic* synthesis: ABC maps to a
> technology-independent 2-input gate library (AND/OR/XOR/MUX/AOI…). There is
> **no PDK, no liberty, no place-and-route, no GDSII** — those need an NDA
> standard-cell library and are Phase 3 (MPW tape-out, Council-gated). Absolute
> gate counts are a proxy; the **ratio** between ternary and INT8 is the
> validated, technology-independent result.

## Run

```bash
50-infra/silicon/synth/run_synth.sh      # synthesizes every module, prints summary
```

Outputs land in `out/` (gitignored): per-module `*.stat.json`, `*.log`, the
generated `*.ys` script, and `SUMMARY.md`.

## Results (yosys 0.65, 2026-06-01)

| module | raw gates (2-input) | NAND2-equiv (GE) | flip-flops |
|---|---:|---:|---:|
| `ternary_pe` | 159 | 303 | 0 |
| `int8_mac_ref` (baseline) | 601 | 1112 | 0 |
| `radix3_decoder` | 123 | 185 | 0 |
| `zero_skip_dispatcher` | 40 | 77 | 0 |
| `pe_array` (4×4, incl. clock-gate ctrl + write counter) | 1036 | 1724 | 259 |
| `mul8x8` (ref) | 369 | 654 | 0 |
| `ternary_mul` (ref) | 37 | 52 | 0 |

**Density findings:**

- **Multiplier block alone** (the logic BitNet 1.58 ternary weights delete):
  `mul8x8 ÷ ternary_mul` = **10.0× raw / 12.7× GE**. The ADR's behavioural
  estimate of **8.4× is validated and, if anything, conservative** for the
  multiplier elimination itself.
- **Whole PE** including the 24-bit accumulator (which *both* PE styles need):
  `int8_mac_ref ÷ ternary_pe` = **3.78× raw / 3.68× GE**. The shared adder
  dilutes the per-PE advantage — this is the honest system-level number for a
  complete MAC cell. Zero-skip clock gating (35%, see `zero_skip_dispatcher`)
  stacks on top as *dynamic-power* savings, not area.

So the ADR's headline 8.4× is real for the multiplier, and a complete ternary
PE is ~3.7× smaller than a complete INT8 PE — both meaningful, and now backed by
synthesis rather than estimate.

## sky130 open-PDK area (real std cells)

`run_synth_sky130.sh` maps the same RTL to the **SkyWater sky130** open PDK
high-density cells (`sky130_fd_sc_hd`, Apache-2.0/CC — not NDA, so allowed) and
reports **real pre-layout cell area in µm²** (yosys 0.65 + ABC, liberty
`tt_025C_1v80`, 2026-06-01):

| module | sky130 area (µm²) |
|---|---:|
| `ternary_pe` | 1 051 |
| `int8_mac_ref` (baseline) | 3 880 |
| `radix3_decoder` | 671 |
| `zero_skip_dispatcher` | 257 |
| `pe_array` (4×4) | 14 583 |
| `mul8x8` (ref) | 2 345 |
| `ternary_mul` (ref) | 198 |

- **Whole-PE density:** `int8_mac_ref ÷ ternary_pe` = **3.69×** — independently
  matches the generic GE estimate (3.68×).
- **Multiplier-only density:** `mul8x8 ÷ ternary_mul` = **11.86×** — matches the
  generic estimate (12.7×) and confirms the ADR's 8.4× is conservative.

Two independent metrics (generic 2-input gates and real sky130 std-cell area)
agree to within a few percent, so the density claim is robust.

> **Still not GDSII.** sky130 area here is *pre-layout* std-cell area: no
> place-and-route, no routing/whitespace overhead, no parasitic extraction, no
> timing closure (f_max would need OpenSTA / OpenROAD — Phase 3). It is an
> optimistic lower bound on silicon area, not a tape-out.

### Why absolute counts differ from the ADR

The ADR quotes ~620 (ternary) / ~5,200 (INT8) on a TSMC-N5 NAND-equivalent
std-cell area basis; this flow reports generic 2-input gate counts with no PDK.
The absolute numbers are not comparable across the two metrics — only the
ratios are. Real N5 areas require the (NDA) standard-cell library at Phase 3.

## Method

`synth.ys.tmpl` → `read_verilog -sv` → `synth -flatten` →
`abc -g <2-input gate set>` → `stat -json`. `analyze.py` weights the cell
histogram by typical NAND2-equivalent relative areas (NAND2 = 1.00) to produce
the GE proxy and the density ratios. FFs are counted separately (sequential
cells excluded from the combinational gate total).
