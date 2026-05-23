import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name
os.environ["BELIEF_STORE_BACKEND"] = "at-ipfs-local"

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import hakkou_worker_main

async def test_hakkou_crud():
    # Create Ferment
    create_res = await hakkou_worker_main.task_create_ferment_record(
        fermentVertexId="",
        agentDid="did:web:test_agent",
        inputKind="text",
        inputRef="Test raw input data here",
        outputKind="insight",
        callerDid="did:web:caller"
    )
    print("Create:", create_res)
    assert create_res["status"] == "pending"

    vid = create_res["fermentVertexId"]

    # Finalize Ferment
    final_res = await hakkou_worker_main.task_finalize_ferment(
        fermentVertexId=vid,
        outputVertexId="at://some-output",
        ethanolHash="abc123hash",
        co2AuditRef="co2-ref"
    )
    print("Finalize:", final_res)
    assert final_res["fermented"] is True

    print("hakkou_worker_main tests passed!")

if __name__ == "__main__":
    asyncio.run(test_hakkou_crud())
