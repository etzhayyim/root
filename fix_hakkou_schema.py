import re

with open("20-actors/magatama/py/src/pymagatama/primitives/active_inference_substrate.py", "r") as f:
    sub = f.read()

sub = sub.replace("    co2_audit_ref: str | None = None\n\n@dataclass", "    co2_audit_ref: str | None = None\n    input_hash: str | None = None\n    fermented_at: str | None = None\n\n@dataclass")

with open("20-actors/magatama/py/src/pymagatama/primitives/active_inference_substrate.py", "w") as f:
    f.write(sub)


with open("20-actors/magatama/py/src/pymagatama/primitives/at_ipfs_belief_store.py", "r") as f:
    ipfs = f.read()

ipfs = ipfs.replace("co2_audit_ref TEXT,\n  at_uri TEXT", "co2_audit_ref TEXT,\n  input_hash TEXT,\n  fermented_at TEXT,\n  at_uri TEXT")

with open("20-actors/magatama/py/src/pymagatama/primitives/at_ipfs_belief_store.py", "w") as f:
    f.write(ipfs)
