"""yadori (宿り) DNS-availability + domain-acquisition cells — R0 scaffold.

All cells raise RuntimeError on .solve() until a Council activation ADR enables them
(ADR-2606038400 §Decision). Only the reservation state_machine transitions (G2/G3/G5/G6)
and the availability classifier (methods/) are unit-tested at R0.
"""
