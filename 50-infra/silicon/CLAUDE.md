# 50-infra/silicon — CLAUDE rules

Per ADR-2605242500 (silicon charter) and ADR-2605242545 (fab equipment charter).

## Hard rules

1. **No commercial EDA** in the committed flow. SystemVerilog must remain
   `yosys + Verilator` parsable. Chisel emits SystemVerilog through
   FIRRTL → CIRCT (open). PDK files under NDA must not be committed;
   reference them via `pdk-N5/` etc. that is `.gitignore`d.

2. **Every `.sv` / `.scala` / `.cad` commit must pass
   `charter-rider-applicator`** with the §2(a)(c) silicon profile (when
   the profile lands — until then, manually attest design intent in the
   commit message: `silen-force-attest: ok` or pause for Council review).

3. **Ternary PE is shared IP**. `shared-ip/ternary-pe/rtl/ternary_pe.sv`
   is the canonical multiplier-less PE. Both iwakura and fuigo
   instantiate it. Do not fork.

4. **cocotb tests are the executable contract**. Each RTL module has a
   `sim/test_<module>.py` that defines its functional behaviour. Verilator
   build + cocotb run pass = module accepted.

5. **No HBM / LPDDR PHY RTL in this tree** (those are foundry IP under
   NDA). Only behavioural sim wrappers under `*_ctrl.sv` files.

6. **`ipfs://` reference for any large reference data** (e.g., weight
   binary used in test). Inline binary blobs are forbidden in commits.

## Naming

- modules: `snake_case` matching file name (`ternary_pe` in
  `ternary_pe.sv`)
- signals: `lowerCamelCase` (Chisel convention) or `snake_case`
  (SystemVerilog convention); pick one per module and stick with it
- top-level dies: `iwakura_top`, `fuigo_top`
- packages: `iwakura_pkg`, `fuigo_pkg`

## Testing

```bash
cd 50-infra/silicon/shared-ip/ternary-pe/sim
make sim                  # invokes Verilator + cocotb (Makefile per-module)
```

Each `sim/` directory has a `Makefile` that:
- builds the module under test with Verilator
- runs the cocotb Python tests
- emits a JUnit XML for CI ingestion

## Charter Rider scanner

```bash
charter-rider-applicator scan 50-infra/silicon/ --profile silicon-2a-2c
```

(scanner extension TBD — Phase 2 wave will add `--profile silicon-2a-2c`
keyword set + design intent attestation parser).
