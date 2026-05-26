import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import resources_worker_main

def test_resources_crud():
    actor = "test_actor"

    # Create Resource
    res = resources_worker_main._create_resource_sync("Test Res", "cpu", "did:web:test", actor)
    res_id = res["id"]
    assert res["status"] == "active"

    # Get Resource
    r = resources_worker_main._get_resource_sync(res_id, actor)
    assert r["name"] == "Test Res"

    # List Resources
    lst = resources_worker_main._list_resources_sync("cpu", 50, 0, actor)
    assert lst["total"] == 1

    # Update Resource
    upd = resources_worker_main._update_resource_sync(res_id, "Test Res 2", "inactive", actor)
    assert upd["status"] == "inactive"

    # Allocate Resource
    alloc = resources_worker_main._allocate_resource_sync(res_id, "did:web:requester", 1, actor)
    alloc_id = alloc["allocationId"]
    assert alloc["status"] == "allocated"

    # Resource Usage
    usage = resources_worker_main._resource_usage_sync(res_id, actor)
    assert usage["totalAllocations"] == 1
    assert usage["activeAllocations"] == 1

    # Release Resource
    rel = resources_worker_main._release_resource_sync(alloc_id, actor)
    assert rel["status"] == "released"

    usage2 = resources_worker_main._resource_usage_sync(res_id, actor)
    assert usage2["activeAllocations"] == 0

    # Delete Resource
    dl = resources_worker_main._delete_resource_sync(res_id, actor)
    assert dl["deleted"] == True

    print("resources_worker_main tests passed!")

if __name__ == "__main__":
    test_resources_crud()
