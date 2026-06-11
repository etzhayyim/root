# equipment/etch — plasma etcher (RIE/ICP) reference design

Per **ADR-2605242545** §"Decision 1 row 3".

## Reference vendors

Lam Research / Tokyo Electron / Applied Materials.

## Religious-corp design scope

| Layer | Self-design target |
|---|---|
| Plasma source | RIE (reactive ion etch) + ICP (inductively coupled plasma) RTL + matching network |
| Endpoint detection | optical emission spectroscopy + interferometric endpoint RTL |
| Chamber | vacuum chamber CAD + electrostatic chuck driver |
| Gas delivery | SF6 / Cl2 / HBr / CF4 / O2 etc. MFC + valve sequencer (overlap with deposition) |
| Wafer handler | shared with deposition + CMP — common ROS 2 robotics library |

## Pregel cell

`silicon_etch`. Super-step = 1 wafer etch step.

## Charter Rider §2(a)(c) gate

Halogen-based etch chemistry (Cl2, HBr) has tactical-weapon dual-use
overlap. Council review trigger keywords listed in
`docs/design-intent.md` (Phase 2 wave).

## Phase 1 scope

README only.
