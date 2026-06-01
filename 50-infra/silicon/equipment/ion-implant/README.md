# equipment/ion-implant — イオン注入 (ion implanter) reference design

Per **ADR-2605242545** §"Decision 1 row 4".

## Reference vendors

Axcelis Technologies / Applied Materials. 2-company duopoly (~80% share).

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Ion source | Bernas / Freeman / RF / Microwave plasma source reference RTL |
| Mass analyzer | dipole magnet (electromagnet + Hall sensor feedback FPGA RTL) |
| Acceleration | DC HV stack (10 kV–500 kV) — PCB-level safety interlock RTL |
| Beam scanner | electrostatic + magnetic 2D scan, deterministic-latency control FPGA |
| Dose measurement | Faraday cup + 4-quadrant beam profiler RTL |
| Wafer handler | end-station 6-DoF tilt/rotate (ROS 2 + custom kinematic plugin) |

## Pregel cell

`silicon_implant`. Super-step = 1 wafer implant.

## Charter Rider §2(a)(c) gate

**HIGH §2(a) risk**: ion implanter technology overlaps with:
- particle accelerator weapons (cyclotron / synchrotron)
- nuclear weapon trigger components

Every commit MUST include silen-force-attest with explicit dual-use
analysis + Council Lv6+ ≥ 3 multisig pre-approval (no exceptions for
ion-implant tree).

## Phase 1 scope

README only. Real RTL = Phase 4, only after Charter Rider scanner
extension lands silen-force profile.
