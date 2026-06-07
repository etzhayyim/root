# 50-infra/silicon — religious-corp first-party silicon (iwakura / fuigo + fab equipment)

Per **ADR-2605242500** (silicon + tsukuru fab charter), this directory holds
the RTL, CAD, mechanical, and robotics designs that religious-corp owns and
publishes under Apache 2.0 + Charter Compliance Rider v2.0.

## Directory layout

```
silicon/
├── iwakura/                 # Inference ASIC for baien edge (ADR-2605242515)
├── fuigo/                   # Training ASIC for baien checkpoints (ADR-2605242530)
├── shared-ip/
│   ├── ternary-pe/          # multiplier-less ternary PE — instantiated by both iwakura and fuigo
│   ├── radix3-packer/       # 5-ternary-per-byte weight packing
│   └── libp2p-nic/          # die-level libp2p protocol engine (Murakumo mesh native)
└── equipment/               # 8 fab process equipment categories (ADR-2605242545)
    ├── lithography/         # ASML/Nikon/Canon counterpart (EUV/DUV)
    ├── deposition/          # AMAT/Lam/TEL counterpart (CVD/PVD/ALD)
    ├── etch/                # Lam/TEL/AMAT counterpart (plasma RIE/ICP)
    ├── ion-implant/         # Axcelis/AMAT counterpart
    ├── cmp/                 # Ebara/AMAT counterpart
    ├── metrology/           # KLA counterpart (overlay/CD-SEM/inspection)
    ├── test/                # Advantest/Teradyne counterpart (ATE)
    └── packaging/           # ASE/Amkor/TSMC AP/Samsung AP counterpart
```

## Hard rules (per ADR-2605242500 + 2605242545)

1. **Open-source toolchain only**: SystemVerilog (yosys-compatible) or Chisel;
   Verilator + cocotb for sim; SymbiYosys for formal; KiCad / FreeCAD /
   OpenSCAD for CAD; ROS 2 + URDF for robotics. No commercial EDA
   dependency (Synopsys / Cadence / Mentor) in committed flow. PDK access
   for foundry tape-out is handled via separate NDA stack outside this tree.

2. **Charter Rider §2(a)(c) gate**: every commit under this tree is scanned
   by `charter-rider-applicator`. Design intent that even partially
   resembles `weapons` (§2(a)) or `mass surveillance` (§2(c)) requires
   Council Lv6+ ≥ 3 multisig attestation via
   `com.etzhayyim.silicon.silenForceReview` before merge.

3. **No commercial sale of completed silicon** (ADR-2605242500 Decision 6).
   Donated silicon is inalienable, land-trust analogue. Lease to SBT
   holders is permitted.

4. **Pregel cell pairing**: each equipment directory has a sibling
   `silicon_<step>` Pregel cell under `40-engine/kotoba/crates/kotoba-kotodama/cells/` that
   orchestrates the equipment via XRPC + libp2p telemetry stream.

5. **Religious-corp ownership invariant**: all RTL / CAD / mechanical /
   robotics designs in this tree are owned by religious-corp. Vendor
   (etzhayyim.com) participates only as manufacturing executor via
   `tsukuru.etzhayyim.com` production_order.

## ADR index

| ADR | Scope |
|---|---|
| ADR-2605242500 | Upper charter (silicon as core of life + 4-phase roadmap) |
| ADR-2605242515 | iwakura (inference ASIC) architecture |
| ADR-2605242530 | fuigo (training ASIC) architecture |
| ADR-2605242545 | 8 fab equipment + Pregel cell catalog |

## Phase status (2026-05-24)

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | RTL + cocotb sim scaffold (this wave) | 🟡 in progress (commit pending) |
| Phase 2 | FPGA prototype (VCK190 / V80 / VHK158) | ⏳ separate ADR + budget |
| Phase 3 | MPW tape-out (TSMC N5/N3) | ⏳ Council 5-of-7 Safe + tsukuru.production_order |
| Phase 4 | Rapidus 2nm 千歳 second source | ⏳ post-2027 separate ADR |
| Phase 5 | Self-owned fab (clean room + all 8 equipment) | ⏳ multi-decade, separate wave |
