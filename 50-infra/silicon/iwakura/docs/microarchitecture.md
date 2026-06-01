---
id: iwakura-microarchitecture-phase1
title: "iwakura-1 Phase-1 micro-architecture (RTL + cocotb)"
status: active
doc_type: reference
topic: silicon-iwakura
authoritative: false
last_verified: 2026-06-01
related:
  - 90-docs/adr/2605242515-iwakura-ternary-inference-asic.md
  - 50-infra/silicon/iwakura/rtl/
  - 50-infra/silicon/shared-ip/ternary-pe/rtl/
---

# iwakura-1 — Phase-1 micro-architecture reference

This expands ADR-2605242515 with the **as-built RTL** of the Phase-1 deliverable
(RTL + cocotb simulation; no FPGA, no MPW yet). Every block below is
Verilator-elaboratable, lint-clean (`-Wall`), and covered by a cocotb test.

## Module inventory

| Module | File | Role | Test | Status |
|---|---|---|---|---|
| `ternary_pe` | `shared-ip/ternary-pe/rtl/ternary_pe.sv` | multiplier-less ternary MAC cell (canonical, shared) | `test_ternary_pe.py` (3 tests / 75 cases) | ✅ pre-existing |
| `radix3_decoder` | `shared-ip/radix3-packer/rtl/radix3_decoder.sv` | 5-trit/byte unpacker → PE 2-bit encoding | `test_radix3_decoder.py` (2 tests / all 256 codes) | ✅ new |
| `pe_array` | `iwakura/rtl/pe_array.sv` | weight-stationary ternary matrix-vector engine | `test_pe_array_4x4.py` (3 tests / 200+ cases) | ✅ new |
| `zero_skip_dispatcher` | `iwakura/rtl/zero_skip_dispatcher.sv` | per-block clock-gate decision + activity estimate | `test_zero_skip_dispatcher.py` (3 tests / 65 536 blocks) | ✅ new |
| `iwakura_top` | `iwakura/rtl/iwakura_top.sv` | die top: live compute tile + Phase-2 PHY placeholders | `test_iwakura_top.py` (1 integration test) | ✅ live tile |

## Datapath: `pe_array`

A weight-stationary, column-streamed matrix-vector engine computing
`y[r] = Σ_c W[r][c]·a[c]`:

```
        a[k]  (shared activation bus, one column per cycle)
          │
   ┌──────┼───────────────────────────────────────┐
   │      ▼                                          │   lane 0  ─ ternary_pe ─ acc[0] ─▶ y[0]
   │   W[r][k]  (per-lane weight select on col k)    │   lane 1  ─ ternary_pe ─ acc[1] ─▶ y[1]
   │      │                                          │   ...
   │      ▼                                          │   lane R-1─ ternary_pe ─ acc[R-1]▶ y[R-1]
   └──────┴───────────────────────────────────────┘
```

- ROWS lanes run in parallel; each is one `ternary_pe` instance (shared IP, no fork).
- Column counter `col` walks `0..COLS-1`; `acc_in` is forced to 0 on `col==0`,
  so each op is independent with no clear cycle.
- Latency: **COLS cycles** from `start` to `done` (1 cycle when `COLS==1`).
- `pe_active_count` = Σ of per-cycle `pe_active` = the true (zero-skipped) MAC
  count for the op — the power-telemetry signal.

The full iwakura-1 die fans this into a 256×256 spatial grid (Phase 2); the
Phase-1 tile is parameterized `TILE_ROWS×TILE_COLS` (default 4×4) so simulation
stays fast while exercising the identical control + accumulation logic.

## Weight encoding (canonical, all modules)

| 2-bit | weight | PE behaviour |
|---|---|---|
| `2'b00` | 0 | `acc_out = acc_in`, `pe_active=0` (zero-skip) |
| `2'b01` | +1 | `acc_out = acc_in + a`, `pe_active=1` |
| `2'b10` | −1 | `acc_out = acc_in − a`, `pe_active=1` |
| `2'b11` | reserved | treated as zero-skip |

`radix3_decoder` emits only `00/01/10` (never the reserved `11`), and clamps
illegal bytes (243..255) to all-zero with `code_valid=0`.

## Zero-skip clock gating

`zero_skip_dispatcher` turns a weight block into a per-PE clock-enable mask:
`clk_en[i] = 1` iff weight `i` is ±1. On the BitNet 1.58 distribution
`{0:35%, +1:32%, −1:33%}` the cocotb statistical test measures the gated
fraction at **35.0%** over 160 000 PE-cycles — confirming the ADR's
~30% dynamic-power-reduction claim. `pe_active` from `ternary_pe` makes this a
pure power optimization: gating a zero-weight PE cannot change the result, and
the `back_to_back_independence` + `randomized_matvec` tests pin that invariant.

## How to run

```bash
cd 50-infra/silicon
python3.13 -m venv .venv-sim && .venv-sim/bin/pip install cocotb   # once
source .venv-sim/bin/activate

# shared IP
( cd shared-ip/ternary-pe/sim     && make sim )
( cd shared-ip/radix3-packer/sim  && make sim )

# iwakura
( cd iwakura/sim && make sim DUT=pe_array )
( cd iwakura/sim && make sim DUT=zero_skip_dispatcher )
( cd iwakura/sim && make sim DUT=iwakura_top )

# strict lint (synthesizability check; yosys + Verilator parsable per CLAUDE.md)
verilator --lint-only -Wall \
  shared-ip/ternary-pe/rtl/ternary_pe.sv \
  shared-ip/radix3-packer/rtl/radix3_decoder.sv \
  iwakura/rtl/pe_array.sv iwakura/rtl/zero_skip_dispatcher.sv iwakura/rtl/iwakura_top.sv \
  --top-module iwakura_top
```

## Honest scope boundary

- **RTL + functional sim only.** No synthesis netlist, no place-and-route, no
  GDSII. Gate counts in the ADR are behavioural estimates, not synthesis
  results.
- `pe_array` is the **time-multiplexed** form (one column/cycle). The physical
  256×256 systolic skew + pipeline registers between rows is Phase-2.
- `iwakura_top` PHY ports (PCIe / LPDDR5X / modality encoder) are placeholders;
  the DMA path feeding the tile is Phase-2.
- LPDDR5X / HBM PHY RTL is foundry IP under NDA — out of this tree per
  `50-infra/silicon/CLAUDE.md` rule 5.
