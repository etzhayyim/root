#!/usr/bin/env python3
"""
Kotoba IPFS Publisher Mock

Simulates pinning a static directory (like a web app) to the decentralized
Kotoba IPFS network, generating a Content Identifier (CID).
"""

import os
import hashlib
import json
import time

def generate_cid(content_string):
    """Simulate a CIDv1 hash."""
    sha = hashlib.sha256(content_string.encode('utf-8')).hexdigest()
    return f"bafybe{sha[:52]}"

def publish_to_ipfs(target_dir):
    print(f"Adding directory '{target_dir}' to Kotoba IPFS...")
    time.sleep(1) # Simulate pinning

    # Just read the index.html for the mock hash
    index_path = os.path.join(target_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            cid = generate_cid(f.read())
    else:
        cid = generate_cid(str(time.time()))

    print(f"Pinned to local node.")
    print(f"CID: {cid}")
    print(f"IPFS URI: ipfs://{cid}")
    print(f"Available on local gateway via Root Router mapping.")

    return cid

if __name__ == "__main__":
    target = "60-apps/chaos-dashboard"
    cid = publish_to_ipfs(target)

    # Write a mapping file that the Root Router can read to resolve /apps
    mapping = {
        "/apps": {
            "type": "ipfs_pin",
            "cid": cid,
            "local_path": target
        }
    }
    with open("../com-etzhayyim-root-router/ipfs_gateway_map.json", "w") as f:
        json.dump(mapping, f, indent=2)
    print("Updated Root Router IPFS gateway map.")
