"""karakuri (絡繰) web-service-to-CLI cells — R0 scaffold.

All cells raise RuntimeError on .solve() until a Council activation ADR enables them
(ADR-2606039200 §Decision). The session_broker (G1/G3/G5) and adapter_invoke (G2/G5/G6/G8 — wiring
the planner + browser-use T2 plan builder) state_machine transitions, plus the ServiceOp parser/
planner (methods/command.py) and the browser-use plan builder (methods/t2_browser.py), are
unit-tested at R0.
"""
