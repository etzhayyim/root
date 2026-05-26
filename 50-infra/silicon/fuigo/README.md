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

- `rtl/fuigo_top.sv` — top-level port list stub
- `rtl/forward_sa.sv` — 1024×1024 ternary PE grid wrapper (instantiates `shared-ip/ternary-pe`)
- `rtl/backward_sa.sv` — 8k BF16 MAC grid stub
- `rtl/ste_glue.sv` — STE bridge stub
- `rtl/lion_optimizer.sv` — Lion optimizer hardwire stub
- `rtl/memory/hbm3e_ctrl.sv` — HBM3e PHY controller stub
- `rtl/memory/cxl_mem_3_ep.sv` — CXL.mem 3.0 endpoint stub
- `rtl/interconnect/libp2p_nic.sv` — libp2p protocol engine stub (delegates to `shared-ip/libp2p-nic`)
- `sim/test_ste_glue.py` — STE bridge unit test (cocotb)
- `sim/test_lion_step.py` — 1-step Lion optimizer update micro test
- `sim/test_forward_backward_loop.py` — 1-iteration end-to-end micro loop

## Build & test

```bash
cd sim
make sim
```

## ADR pointers

- Architecture: ADR-2605242530
- Upper charter: ADR-2605242500
- baien-distill loop (Lion recommendation source): ADR-2605231300
- Murakumo no-VKE mesh (libp2p NIC die-integration source): ADR-2605214000
