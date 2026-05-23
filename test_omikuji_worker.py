import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import omikuji_worker_main

def test_omikuji_crud():
    actor = "test_actor"

    # Create Shrine
    shrine = omikuji_worker_main._create_shrine_sync("Test Shrine", "Tokyo", "A test shrine", actor)
    shrine_id = shrine["shrineId"]
    assert shrine["status"] == "active"

    # Get Shrine
    s = omikuji_worker_main._get_shrine_sync(shrine_id, actor)
    assert s["name"] == "Test Shrine"

    # List Shrines
    lst = omikuji_worker_main._list_shrines_sync(50, 0, actor)
    assert lst["total"] == 1

    # Update Shrine
    upd = omikuji_worker_main._update_shrine_sync(shrine_id, "Test Shrine 2", "Updated desc", actor)
    assert upd["shrineId"] == shrine_id

    # Draw Fortune
    fortune = omikuji_worker_main._draw_fortune_sync(shrine_id, "did:web:user", actor)
    draw_id = fortune["drawId"]
    assert fortune["result"] in omikuji_worker_main.FORTUNE_RESULTS

    # Get Fortune
    f = omikuji_worker_main._get_fortune_sync(draw_id, actor)
    assert f["result"] == fortune["result"]

    # List Fortunes
    lst_f = omikuji_worker_main._list_fortunes_sync(50, 0, shrine_id, actor)
    assert lst_f["total"] == 1

    # Reset Fortune
    res = omikuji_worker_main._reset_fortune_sync("did:web:user", actor)
    assert res["ok"] == True

    print("omikuji_worker_main tests passed!")

if __name__ == "__main__":
    test_omikuji_crud()
