"""karakuri (絡繰) web-service-to-CLI cells — R0 scaffold.

All cells raise RuntimeError on .solve() until a Council activation ADR enables them
(ADR-2606039200 §Decision). All five cells are coded reference cells whose state_machine transitions
are unit-tested at R0:
  service_resolve  (G2/G6/G8)        — resolve service -> tier + both stance axes
  command_plan     (G4/G5/G6/N6)     — NL brief -> gated ServiceOps (Murakumo NL path operator-gated)
  session_broker   (G1/G3/G5)        — member-keyless session broker
  adapter_invoke   (G2/G5/G6/G8)     — tos-gate -> mutate-gate -> dry-run (browser-use plan) -> exec-gate
  export_roundtrip (G6/G9)           — T3 data-portability export (own-data-only, encrypted)
plus the methods layer: command.py (parser/planner), t2_browser.py (browser-use plan builder),
nl_plan.py (Murakumo NL planner), export.py (T3 export), adapter_live.py (live-exec membrane),
datom.py (kotoba Datom audit, G7).
"""
