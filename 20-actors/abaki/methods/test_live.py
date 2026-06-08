import os
from live_gate import LiveGate, require
from analyze import publish_live

gate = LiveGate(
    operator_did="did:web:etzhayyim.com:operator:1",
    council_level=6,
    member_signature="sig_12345"
)
os.environ["ABAKI_ALLOW_LIVE_PUBLISH"] = "1"
routing_policy = {"blocked_entities": [{"id": "entity:compute:megacorp_a", "reason_ci": 100}]}
datoms = publish_live(routing_policy, gate, env=os.environ.copy())
print("Datoms generated:", datoms)
