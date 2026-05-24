# equipment/deposition — CVD/PVD/ALD 成膜装置 reference design

Per **ADR-2605242545** §"Decision 1 row 2".

## Reference vendors

Applied Materials / Lam Research / Tokyo Electron. 3-company oligopoly
(~70% share).

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Precursor delivery | mass-flow controller + bubbler temperature control RTL + valve sequencing |
| Plasma source | RF generator (13.56 MHz + 60 MHz) + matching network reference |
| Chamber | OpenSCAD vacuum chamber + heater control RTL + endpoint optical emission spectroscopy |
| Wafer handler | ROS 2 + URDF robotics for cassette → load lock → process → unload |
| ALD pulse logic | TimingFSM RTL for atomic-layer-deposition pulse sequencing |

## Pregel cell

`silicon_deposition`. Super-step = 1 wafer deposition cycle.

## Charter Rider §2(a)(c) gate

Lower §2(a) risk than litho. §2(c) risk minimal. Commit attestation only
where pre-cursor chemistry overlaps with chemical weapon precursors
(e.g., certain organotellurium / organoarsenic compounds → mandatory
Council review).

## Phase 1 scope

README only. RTL/CAD scaffold = Phase 4 per ADR-2605242545 §Decision 7.
