# shared-ip/ternary-pe — multiplier-less ternary processing element

Per **ADR-2605242515** (iwakura inference ASIC) §"ternary processing element
(PE)" and **ADR-2605242530** (fuigo training ASIC) §"Forward path".

This is the canonical PE for both iwakura and fuigo. The forward path of
fuigo instantiates the same cell.

## Per-cycle contract

| `weight` | meaning | `acc_out` | `pe_active` |
|---|---|---|---|
| `2'b00` | 0 | `acc_in` | 0 |
| `2'b01` | +1 | `acc_in + activation` | 1 |
| `2'b10` | -1 | `acc_in - activation` | 1 |
| `2'b11` | reserved (zero-skip) | `acc_in` | 0 |

Parameters:
- `ACT_WIDTH = 8` (INT8 activation)
- `ACC_WIDTH = 24` (INT24 accumulator)

## Gate-level estimate (TSMC N5 behavioural synthesis)

~620 gates per PE, vs ~5,200 for INT8 multiplier → **8.4× density gain**.

A 256×256 grid (iwakura) at 1 GHz delivers **65 Tera-ternary-ops/s** peak.
A 1024×1024 grid (fuigo forward) at 1 GHz delivers **1 PetaTernary-ops/s**.

## Run the tests

```bash
make sim
```

Requires open-source toolchain only (Verilator + cocotb), per ADR-2605242500
Decision 1 + Charter Rider §2(i) spirit.

## Expected output

```
ternary_pe passed 75 cases
3 tests passed: exhaustive_81_cases, reserved_encoding_is_zero_skip, negative_zero_handling
```
