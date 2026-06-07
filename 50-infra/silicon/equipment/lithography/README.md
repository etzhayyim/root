# equipment/lithography — DUV/EUV ステッパー reference design (etzhayyim 自社設計)

Per **ADR-2605242545** §"Decision 1 row 1".

## Reference vendors (for context, NOT for copy)

ASML / Nikon / Canon. EUV: ASML 100% world share (geopolitical chokepoint
this ADR-wave explicitly addresses).

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Optics | EUV reflective mirror (Bragg multilayer) reference, blank manufacturing equipment |
| Reticle handling | robotics (ROS 2 + URDF) for reticle stage + mask pellicle handling |
| Wafer stage | immersion stage RTL + 6-DoF nanopositioner (FPGA + piezo driver) |
| Light source | DUV: 193 nm ArF excimer reference; EUV: LPP-CO2 + Sn droplet generator reference |
| Control | endpoint detector + overlay metrology (ties to `equipment/metrology/`) |

Open-source toolchain: SystemVerilog/Chisel for control RTL, FreeCAD for
mechanical, KiCad for driver PCB, ROS 2 + URDF for robotics.

## Pregel cell

Paired with `40-engine/kotoba/crates/kotoba-kotodama/cells/silicon_litho/`. Each super-step =
1 wafer-lot exposure. Telemetry stream via libp2p; per-step attestation
via `com.etzhayyim.silicon.waferLotAttestation`.

## Charter Rider §2(a)(c) gate

EUV / DUV optics is dual-use (radar, laser weapons, ECM). Every commit
must include `silen-force-attest: <reason>` in commit body or pause for
Council Lv6+ ≥ 3 multisig.

## Phase 1 scope (this commit)

This README only. RTL/CAD/robotics scaffold lands in Phase 2 wave.

## Phase 3 priority (per ADR-2605242545 §Decision 7)

Lithography is the **highest difficulty** of the 8 equipment categories.
Phase 3 in the sequencing (after `silicon_test` Phase 2a, metrology
Phase 2b, packaging Phase 2c). Year-scale R&D, not weeks.
