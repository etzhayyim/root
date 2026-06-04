"""karakuri session_broker (絡繰) cell — R0 scaffold.

Brokers access to the member's OWN service session without the platform ever holding secret
material, allows read ops, and routes mutating ops to member-signature authorization. .solve()
raises until Council activation (ADR-2606039200). The state_machine transitions enforce G1/G3/G5
purely and are unit-tested.
"""
