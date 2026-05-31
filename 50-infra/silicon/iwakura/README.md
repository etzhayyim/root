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

## Phase 1 scope (this directory)

- `rtl/iwakura_top.sv` — top-level port list stub
- `rtl/pe_array.sv` — 256×256 PE grid wrapper (generate-for instantiation of `shared-ip/ternary-pe`)
- `rtl/zero_skip_dispatcher.sv` — Zero-skip dispatcher logic stub
- `rtl/memory/sram_scratch.sv` — 16 MB on-die SRAM wrapper stub
- `rtl/memory/lpddr5x_ctrl.sv` — LPDDR5X PHY controller stub
- `sim/test_pe_array_4x4.py` — 4×4 micro array sim (cocotb)

The canonical PE lives in `../shared-ip/ternary-pe/`. iwakura instantiates
it via SystemVerilog `generate` loop in `pe_array.sv`.

## Build & test

```bash
cd sim
make sim   # Verilator + cocotb
```

## ADR pointers

- Architecture: ADR-2605242515
- Upper charter: ADR-2605242500
- Baien edge invariant (physical target source): ADR-2605241900
