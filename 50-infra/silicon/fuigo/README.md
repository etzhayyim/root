# fuigo (鞴) — baien hybrid ternary/BF16 training ASIC

Per **ADR-2605242530**.

## Spec at a glance

| Item | Value |
|---|---|
| Forward SA | 1024 × 1024 ternary PE (IP reused from `shared-ip/ternary-pe`) |
| Forward peak | 1 PetaTernary-ops/s @ 1 GHz |
| Backward SA | 8,192 BF16 MAC = 16 TFLOPS BF16 |
| Optimizer engine | Lion hard-wired (Adam = software emulation) |
| STE Glue | forward-ternary ↔ backward-BF16 master-weight bridge |
| HBM | 4 × HBM3e × 24 GB = 96 GB @ 4.8 TB/s |
| Interconnect | libp2p NIC (Murakumo no-VKE mesh native) + CXL.mem 3.0 endpoint |
| TDP target | 350 W (board), liquid-cooled 1U |
| Foundry target | TSMC N3 chiplet (Phase 3); Rapidus 2nm 千歳 second source (Phase 4) |
| Die size estimate | ~600 mm² (4× iwakura) |

## Phase 1 scope (this directory)

| File | Role | Test | Status |
|---|---|---|---|
| `rtl/fuigo_top.sv` | die top: **live forward path** (shared `pe_array` / ternary-pe IP) + Phase-2 placeholders | `sim/test_fuigo_top.py` (101 cases, ACC_WIDTH=32) | ✅ green |

The forward systolic array reuses the canonical `../shared-ip/ternary-pe/`
through `../iwakura/rtl/pe_array.sv` — **the exact IP-reuse deliverable** of
ADR-2605242530 §Phase-1. No fork: iwakura inference and fuigo training share one
verified ternary MAC engine, differing only in accumulator width (24 vs 32).

Still Phase-2 (not yet written): `backward_sa.sv` (BF16), `ste_glue.sv`,
`lion_optimizer.sv`, `memory/hbm3e_ctrl.sv`, `memory/cxl_mem_3_ep.sv`,
`interconnect/libp2p_nic.sv`. Backward BF16 is the part fuigo does **not** share
with iwakura and is deliberately out of Phase-1.

## Build & test

```bash
cd sim
make sim     # forward-path integration (shared ternary-pe IP, ACC_WIDTH=32)
```

## ADR pointers

- Architecture: ADR-2605242530
- Upper charter: ADR-2605242500
- baien-distill loop (Lion recommendation source): ADR-2605231300
- Murakumo no-VKE mesh (libp2p NIC die-integration source): ADR-2605214000
