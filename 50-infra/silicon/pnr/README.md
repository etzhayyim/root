# pnr — RTL→GDSII place-and-route + sign-off timing (OpenLane2 / sky130)

Per **ADR-2605242515**. This is the deepest open-source rung below a real
tape-out: full physical implementation of a silicon block through
**OpenLane2** (OpenROAD + yosys + magic + klayout + netgen) on the **sky130hd
open PDK** — placement, clock-tree synthesis, global+detailed routing,
parasitic extraction, multi-corner static timing, DRC and LVS, ending in a
**GDSII layout**.

> **Open PDK, not the tape-out.** sky130 is SkyWater's 130 nm Apache/CC open
> PDK — allowed in the committed flow (not commercial EDA, not an NDA PDK; see
> `50-infra/silicon/CLAUDE.md` rule 1). The iwakura-1 production target is TSMC
> **N5** (5 nm), which is Phase 3 (MPW shuttle, Council 5-of-7 + tsukuru
> production_order). sky130 numbers below are a *real* physical sign-off on a
> ~26× older node — they validate that the RTL is physically implementable,
> routable, and DRC/LVS-clean, NOT the N5 frequency/area.

## Run

```bash
# prereqs: Docker (OrbStack ok) + `pip install openlane` into .venv-ol
50-infra/silicon/pnr/run_pnr.sh pe_array
```

First run downloads the sky130 PDK (~2–3 GB) via volare and the OpenLane2
image (~4.5 GB). Run artifacts (GDS/DEF/LEF/SPEF/logs) land under
`pe_array/runs/<tag>/` and are gitignored; the committed design is
`pe_array/config.json` + the scripts + this report.

## Result — `pe_array` (4×4 ternary matrix-vector engine), 2026-06-01

OpenLane 2.3.10, sky130hd, 100 MHz target (10 ns clock).

### Sign-off — **GDSII produced, clean**
| check | result |
|---|---:|
| DRC violations | **0** |
| LVS errors | **0** |
| antenna violations | **0** |
| GDSII | `…/final/gds/pe_array.gds` (5.8 MB) |

### Timing (post-route, parasitic-aware multi-corner STA)
f_max = 1 / (T − WNS), T = 10 ns:

| corner | setup WNS | f_max |
|---|---:|---:|
| fast `ff_n40C_1v95` | +5.27 ns | ~211 MHz |
| typical `tt_025C_1v80` | +3.74 ns | **~160 MHz** |
| slow `ss_100C_1v60` (sign-off) | −0.85 ns | **~93 MHz** |

- Hold: positive at **all** corners (no hold violations).
- The slow sign-off corner misses the 100 MHz target by 0.85 ns → the block
  closes timing at **~92 MHz worst-case on sky130**. The ADR's 1 GHz target is
  on TSMC N5; a ~26× newer node closing ~10× higher is the expected process
  scaling, so this is consistent, not a regression.

### Area / utilization
| metric | value |
|---|---:|
| die area | 53 120 µm² |
| core area | 45 381 µm² |
| std-cell area | 24 286 µm² |
| std cells | 3 588 |
| core utilization | ~53.5 % |
| total wirelength | 56 028 µm |

Note the placed-and-routed std-cell area (24 286 µm²) is ~1.7× the pre-layout
sky130 synthesis estimate (14 583 µm²) — the gap is real routing, CTS buffers,
tap/endcap/diode insertion and timing-repair sizing that synthesis area omits.

## Design level reached

```
spec ─ RTL ─ func sim ─ generic synth ─ sky130 area ─ P&R + STA + GDSII ─│─ N5 tape-out
 ✅    ✅      ✅           ✅              ✅            ✅ (sky130, here)  gate   ⏳ Phase 3
```

This is the furthest an open, license-clean flow can go. The remaining step to
silicon is an N5 MPW shuttle with the NDA PDK — Phase 3, Council-gated.
