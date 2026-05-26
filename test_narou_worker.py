import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import narou_worker_main

def test_narou_crud():
    actor = "test_actor"

    # Create Novel
    n = narou_worker_main._task_narou_create_novel_sync({
        "title": "Title",
        "description": "Desc",
        "genre": "fantasy",
        "tags": "test"
    }, actor)
    n_id = n["id"]
    assert n["status"] == "draft"

    # Create Chapter
    c = narou_worker_main._task_narou_create_chapter_sync({
        "novel_id": n_id,
        "title": "Chap 1",
        "content": "Content"
    }, actor)
    c_id = c["id"]

    # Generate Chapter
    g = narou_worker_main._task_narou_generate_chapter_sync({"chapter_id": c_id}, actor)
    assert g["chapter_id"] == c_id

    # Publish Chapter
    p = narou_worker_main._task_narou_publish_chapter_sync({"chapter_id": c_id, "asset_manifest_uri": "uri"}, actor)
    assert p["status"] == "published"

    # Create Character
    char = narou_worker_main._task_narou_create_character_sync({
        "novel_id": n_id,
        "name": "Bob",
        "role": "main"
    }, actor)
    assert "id" in char

    # Create World Setting
    ws = narou_worker_main._task_narou_create_world_setting_sync({
        "novel_id": n_id,
        "name": "Earth"
    }, actor)
    assert "id" in ws

    # Get Novel
    n_get = narou_worker_main._task_narou_get_novel_sync({"id": n_id}, actor)
    assert n_get["novel"]["title"] == "Title"
    assert n_get["chapter_count"] == 1

    # List Novels
    ns = narou_worker_main._task_narou_list_novels_sync({"limit": 50, "genre": "fantasy"}, actor)
    assert ns["total"] == 1

    # Get Chapter
    c_get = narou_worker_main._task_narou_get_chapter_sync({"id": c_id}, actor)
    assert c_get["chapter"]["status"] == "published"

    # List Chapters
    cs = narou_worker_main._task_narou_list_chapters_sync({"novel_id": n_id}, actor)
    assert cs["total"] == 1

    # Search Novels
    search = narou_worker_main._task_narou_search_novels_sync({"q": "title"}, actor)
    assert search["total"] == 1

    print("narou_worker_main 11 handlers passed!")

if __name__ == "__main__":
    test_narou_crud()
