# iwakura (磐座) — baien ternary inference ASIC

Per **ADR-2605242515**.

## Spec at a glance

| Item | Value |
|---|---|
| PE grid | 256 × 256 = 65,536 ternary PE (multiplier-less) |
| Peak ternary ops | 65 Tera-ternary-ops/s @ 1 GHz |
| On-die SRAM | 16 MB (activation + KV cache scratch) |
| On-package DRAM | 2 GB LPDDR5X-7500 ×2 = 120 GB/s |
| Host I/F | USB4 (edge dongle) / PCIe Gen4 x4 (workstation) / WASM-SIMD shim (browser) |
| Modality encoder | image (SigLIP) hard-wired in iwakura-1; audio/video/3D on generic PE |
| TDP target | 3–5 W (edge dongle), 15 W (workstation tier) |
| Foundry target | TSMC N5 MPW eShuttle (Phase 3, post-Council) |
| Die size estimate | ~50 mm² |

## Phase 1 scope (this directory) — implemented + verified

| File | Role | Test | Status |
|---|---|---|---|
| `rtl/pe_array.sv` | weight-stationary ternary matrix-vector engine (generate-for over `shared-ip/ternary-pe`) | `sim/test_pe_array_4x4.py` (3 tests, 200+ cases) | ✅ green |
| `rtl/zero_skip_dispatcher.sv` | per-block clock-gate decision + activity estimate | `sim/test_zero_skip_dispatcher.py` (3 tests, 65 536 blocks) | ✅ green |
| `rtl/iwakura_top.sv` | die top: **live** compute tile + Phase-2 PHY placeholders | `sim/test_iwakura_top.py` (integration) | ✅ green |
| `rtl/pe_array.sv` (`CLOCK_GATE=1`) | zero-skip per-PE accumulator clock gating via `zero_skip_dispatcher` | `sim/test_pe_array_clockgate.py` (200 cases, bit-identical + write savings) | ✅ green |
| `rtl/memory/sram_scratch.sv` | behavioural on-die SRAM scratch (1-cycle read) | `sim/test_sram_scratch.py` (2 tests) | ✅ green |
| `rtl/memory/lpddr5x_ctrl.sv` | behavioural LPDDR5X ctrl + on-read radix-3 weight unpack | `sim/test_lpddr5x_ctrl.py` (2 tests) | ✅ green |
| `docs/microarchitecture.md` | as-built micro-arch reference | — | ✅ |

Still Phase-2+ (not yet written): the full 256×256 systolic **skew + row
pipeline registers** (current `pe_array` is time-multiplexed, 1 column/cycle),
the LPDDR5X/PCIe **PHY** RTL (foundry NDA IP — out of tree per CLAUDE.md rule 5),
and the PHY↔tile DMA path.

The canonical PE lives in `../shared-ip/ternary-pe/`. iwakura instantiates
it via SystemVerilog `generate` loop in `pe_array.sv` (one instance per lane —
shared IP, no fork). Radix-3 weight unpacking is in
`../shared-ip/radix3-packer/`.

## Build & test

```bash
cd sim
make sim DUT=pe_array              # 4×4 ternary matrix-vector engine
make sim DUT=zero_skip_dispatcher  # clock-gate mask + BitNet power-saving stat
make sim DUT=iwakura_top           # integrated compute-tile smoke
```

See `docs/microarchitecture.md` for the full datapath description, expected
outputs, and the honest scope boundary (RTL + functional sim only; no
synthesis / P&R / GDSII).

## ADR pointers

- Architecture: ADR-2605242515
- Upper charter: ADR-2605242500
- Baien edge invariant (physical target source): ADR-2605241900
