"""todoke (届け) last-mile autonomous-delivery cells — R0 scaffold.

All cells raise RuntimeError on .solve() until a Council activation ADR enables them
(ADR-2606042300 §Design). Only the state_machine transitions are unit-tested at R0. The
defining cells route_sequencing and handoff_proof are fully coded; the remaining three
(parcel_intake, autonomous_run, telemetry_log) ship as cell .edn definitions at R0.
"""
