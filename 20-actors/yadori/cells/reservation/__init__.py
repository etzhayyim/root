"""yadori reservation (宿り) cell — R0 scaffold.

Builds an unsigned, member-principal reservation intent and authorizes it with a member
signature only. .solve() raises until Council activation (ADR-2606038400). The state_machine
transitions enforce G2/G3/G5/G6 purely and are unit-tested.
"""
