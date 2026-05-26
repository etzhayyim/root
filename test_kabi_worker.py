import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name
os.environ["BELIEF_STORE_BACKEND"] = "at-ipfs-local"

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import kabi_worker_main

async def test_kabi_crud():
    # Test Anastomosis Probe
    res = await kabi_worker_main.task_anastomosis_probe(
        networkADid="did:web:net_a",
        networkBDid="did:web:net_b",
        edgeId="edge-123",
        callerDid="did:web:caller"
    )
    print("Probe:", res)
    assert res["probeResult"]["compatible"] is True

    print("kabi_worker_main tests passed!")

if __name__ == "__main__":
    asyncio.run(test_kabi_crud())
