"""karakuri adapter_invoke (絡繰) cell — R0 coded reference cell.

Executes a single ServiceOp via the selected adapter (T1 official-API > T2 browser-use ToS-permitted
headless > T3 export). At R0 it is the dry-run PLANNING path only: it wires the ServiceOp parser/
planner (methods/command.py) and the browser-use T2 plan builder (methods/t2_browser.py) into the
manifest state graph (tos-gate -> mutate-gate -> dry-run -> execute-gated). .solve() raises until
Council activation (ADR-2606039200); the state_machine transitions enforce G2/G5/G6 purely and are
unit-tested. EVERY live execution remains Council Lv6+ + operator gated (G6).
"""
