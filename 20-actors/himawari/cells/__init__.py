"""himawari Pregel cell catalog (R0 scaffold; all cells gated).

Per ADR-2606021200. Activation requires Council Lv6+ ratify + ≥1 PV-process
engineer on Council technical advisory + ≥1 LANDS brownfield parcel registered
+ G2 feedstock-provenance (on-chain chain-of-custody) framework operational
+ G3 high-GWP gas abatement framework Council-ratified.

Structural anchor gates (see ADR-2606021200):
  G2:  Feedstock provenance on-chain per lot — NO XUAR/forced-labor polysilicon
       ever; full chain-of-custody CID-anchored (closes hikari §G2 structurally)
  G4:  Fab process heat + power from hikari renewable only — NO fossil/nuclear
       (inherits hikari G4/G5); net-positive lifecycle energy (EPBT < life)
  G7:  Labor-liberation transparency — every human task removed by automation
       logged to the Liberation Metric (ADR-2605261000); no opaque displacement
  G12: NO external commercial PV sale — modules for internal hikari install only
       (SBT↔SBT carve-out, ADR-2605192115 §3)

himawari COMPOSES landed, tests-green robotics (sarutahiko F10 LoaderRobot /
kami-autodrive GNC / giemon AGV / kuni-umi Otete+Mimi); it does not
re-implement them.
"""
