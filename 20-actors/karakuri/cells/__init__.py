"""karakuri (絡繰) web-service-to-CLI cells — R0 scaffold.

All cells raise RuntimeError on .solve() until a Council activation ADR enables them
(ADR-2606039200 §Decision). Only the session_broker state_machine transitions (G1/G3/G5) and the
ServiceOp parser/planner (methods/command.py) are unit-tested at R0.
"""
