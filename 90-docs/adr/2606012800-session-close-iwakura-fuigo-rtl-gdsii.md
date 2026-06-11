---
id: adr-2606012800-session-close-iwakura-fuigo-rtl-gdsii
title: "ADR-2606012800: Session close — iwakura/fuigo ternary RTL → functional sim → synthesis → sky130 GDSII"
status: active
doc_type: adr
topic: silicon-iwakura
authoritative: false
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Documentation-only session-close record for the 2026-06-01 session that took the ternary-silicon design from RTL stubs to a verified, synthesized, placed-and-routed GDSII on the sky130 open PDK. Authoritative design lives in ADR-2605242515 (iwakura) + ADR-2605242530 (fuigo)."
authoritative_for:
  - session-close record for the 2026-06-01 iwakura/fuigo RTL→GDSII session
depends_on:
  - adr-2605242515-iwakura-ternary-inference-asic
  - adr-2605242530-fuigo-hybrid-ternary-bf16-training-asic
related:
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605241900-baien-edge-target-invariant
supersedes: []
superseded_by: []
---

# ADR-2606012800: Session close — iwakura/fuigo ternary RTL → sim → synthesis → sky130 GDSII

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Originating question: *「今の chip 製造は rtl まで? gdsii まで? 設計されている?」* — how far is the
chip design taken: RTL? GDSII? The audit verdict was **RTL-stub only** — `pe_array.sv` /
`zero_skip_dispatcher.sv` were Phase-2 stubs, `radix3_decoder` was README-only, and the gate
counts in ADR-2605242515 were behavioural estimates, not synthesis results. The user then asked
to advance the design and simulation, then (in sequence) to: (1) sky130 open-PDK synthesis,
(2) Phase-2 RTL, (3) fuigo forward path, (4) commit, and finally (5) real OpenLane P&R + timing.

# Decision (what shipped this session)

Authoritative design unchanged (ADR-2605242515 / 2605242530). This session made the design
**empirical**, advancing it through every open rung below an NDA tape-out:

## RTL implemented (was stub / README-only)
- `shared-ip/radix3-packer/rtl/radix3_decoder.sv` — 5-trit/byte radix-3 unpacker → PE encoding.
- `iwakura/rtl/pe_array.sv` — weight-stationary ternary matrix-vector engine, `generate-for`
  over the canonical `ternary_pe` (shared IP, no fork). `CLOCK_GATE=1` wires
  `zero_skip_dispatcher` into per-PE accumulator clock gating.
- `iwakura/rtl/zero_skip_dispatcher.sv` — per-block clock-gate mask + activity estimate.
- `iwakura/rtl/memory/{sram_scratch,lpddr5x_ctrl}.sv` — behavioural memory wrappers
  (`lpddr5x_ctrl` reuses `radix3_decoder` for on-read weight unpack; no PHY RTL, per CLAUDE rule 5).
- `iwakura/rtl/iwakura_top.sv` — stub → live compute tile + dispatcher telemetry.
- `fuigo/rtl/fuigo_top.sv` — forward path now reuses the shared `pe_array` / ternary-pe IP
  (ADR-2605242530 §Phase-1 deliverable), `ACC_WIDTH=32` training accumulator.
- `shared-ip/ternary-pe/rtl/int8_mac_ref.sv` + `synth/ref/mul_compare.sv` — synthesis baselines.

## Verification (Verilator 5.048 + cocotb 2.0.1) — 9 suites / 18 tests green, all -Wall lint clean
- ternary_pe 3 / radix3_decoder 2 (all 256 codes) / pe_array 3 (200+ matvec vs ref) /
  pe_array_cg 1 (200 cases bit-identical, 24.2% acc-writes gated) /
  zero_skip_dispatcher 3 (65,536-block exhaustive; BitNet dist → **35.0% gated**) /
  sram_scratch 2 / lpddr5x_ctrl 2 / iwakura_top 1 / fuigo_top 1 (101 cases).

## Synthesis — generic gates + sky130 std-cell area AGREE
- yosys 0.65: whole-PE density **3.69× (sky130) / 3.68× (GE)**; multiplier-only **11.9× / 12.7×**
  → ADR-2605242515's **8.4× behavioural estimate is validated and conservative**.

## P&R → GDSII (OpenLane2 2.3.10, sky130hd, `pe_array`)
- Sign-off **CLEAN: DRC 0 / LVS 0 / antenna 0**; **GDSII produced** (5.8 MB).
- Post-route multi-corner STA, f_max = 1/(T−WNS): **~93 MHz** (slow `ss_100C_1v60` sign-off) /
  **160 MHz** (typical `tt`) / 211 MHz (fast `ff`); hold positive at all corners.
- Die 53,120 µm² / std-cell 24,286 µm² / 3,588 cells / ~53.5% util / 56,028 µm wirelength.

## Design level reached

```
spec ─ RTL ─ func sim ─ generic synth ─ sky130 area ─ P&R + STA + GDSII ─│─ N5 tape-out
 ✅    ✅      ✅           ✅              ✅            ✅ (sky130)         gate   ⏳ Phase 3
```

# Consequences

- The ternary-vs-INT8 density advantage is no longer an estimate: two independent metrics
  (generic 2-input gates, real sky130 std-cell area) agree, and the multiplier-elimination
  ratio (~12×) exceeds the ADR's headline 8.4×.
- The RTL is proven physically implementable: routable, DRC/LVS-clean, timing-analyzable.
- iwakura and fuigo share one verified ternary MAC engine (no fork), as the charter intended.

## Honest scope / what is NOT done

- **Open PDK, not the tape-out.** sky130 is 130 nm (Apache/CC); the iwakura-1 production target
  is TSMC **N5** (5 nm) — Phase 3, MPW shuttle, Council 5-of-7 + tsukuru production_order. The
  93–160 MHz sky130 result vs the 1 GHz N5 target is the expected ~26×-older-node process gap,
  not a regression. N5 P&R/timing/GDSII need the NDA PDK and are out of scope here.
- `pe_array` is the **time-multiplexed** form (1 column/cycle); the full 256×256 systolic skew +
  inter-row pipeline registers remain Phase 2.
- `iwakura_top` PHY ports (PCIe / LPDDR5X / modality encoder) are placeholders; LPDDR5X/PCIe PHY
  RTL is foundry NDA IP, out of this tree.
- Backward BF16 SA + STE glue + Lion + HBM3e/CXL/libp2p (fuigo) remain Phase 2.

# Artifacts

- RTL + cocotb: `50-infra/silicon/{shared-ip,iwakura,fuigo}/`
- Synthesis: `50-infra/silicon/synth/` (`run_synth.sh`, `run_synth_sky130.sh`, `README.md`)
- P&R: `50-infra/silicon/pnr/` (`run_pnr.sh`, `report_pnr.py`, `config.json`, `README.md`)
- Commits: `feat/iwakura-fuigo-ternary-rtl-synth` — RTL/sim/synth (`407f57a65`), P&R/GDSII (`b7b4a4c0d`).

# References

- ADR-2605242515 (iwakura architecture; honest-scope note updated this session)
- ADR-2605242530 (fuigo architecture; forward-path IP-reuse status updated)
- ADR-2605242500 (silicon charter — open-source EDA only, Council-gated tape-out)
