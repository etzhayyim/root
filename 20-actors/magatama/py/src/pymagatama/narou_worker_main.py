"""
narou_worker_main.py — Narou Web Novel Platform LangServer worker.

Handles 11 BPMN task types for narou.etzhayyim.com:
  ai.gftd.apps.narou.createNovel
  ai.gftd.apps.narou.createChapter
  ai.gftd.apps.narou.generateChapter
  ai.gftd.apps.narou.publishChapter
  ai.gftd.apps.narou.createCharacter
  ai.gftd.apps.narou.createWorldSetting
  ai.gftd.apps.narou.getNovel
  ai.gftd.apps.narou.listNovels
  ai.gftd.apps.narou.getChapter
  ai.gftd.apps.narou.listChapters
  ai.gftd.apps.narou.searchNovels

Tables (RisingWave via asyncpg):
  vertex_narou_novel:         vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                              rkey, repo, did, collection, status, id, title, description,
                              genre, tags, user_id, org_id, actor_id, created_at, updated_at
  vertex_narou_chapter:       vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                              rkey, repo, did, collection, status, id, novel_id, chapter_num,
                              title, content, word_count, user_id, published_at,
                              asset_manifest_uri, org_id, actor_id, created_at, updated_at
  vertex_narou_character:     vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                              rkey, repo, did, collection, status, id, novel_id, name,
                              role, description, user_id, org_id, actor_id, created_at, updated_at
  vertex_narou_world_setting: vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                              rkey, repo, did, collection, status, id, novel_id, name,
                              description, user_id, org_id, actor_id, created_at, updated_at

RW rule: LIMIT must be f-string interpolated (not parameterized) per
[[conventions]] rw-psycopg3-no-param-limit.
"""

import asyncio
import logging
import os
import random
import string
from datetime import date, datetime, timezone

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://root:rw_66a4db7736799bf888c50a817b4c6a65@45.32.79.245:4566/dev",
)

ACTOR_DID = "did:web:narou.etzhayyim.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


def _gid(prefix: str) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{int(datetime.now(timezone.utc).timestamp() * 1000):x}_{suffix}"


def _vid(collection: str, rkey: str) -> str:
    return f"at://{ACTOR_DID}/{collection}/{rkey}"


def _str(v) -> str:
    return v if isinstance(v, str) else ""


def _int(v, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


async def _get_conn() -> asyncpg.Connection:
    return await asyncpg.connect(DATABASE_URL)


# ---------------------------------------------------------------------------
# Task handlers
# ---------------------------------------------------------------------------

async def task_narou_create_novel(variables: dict) -> dict:
    """Create a new novel record."""
    title = _str(variables.get("title"))
    description = _str(variables.get("description"))
    genre = _str(variables.get("genre"))
    tags = _str(variables.get("tags"))
    user_id = _str(variables.get("user_id")) or "anon"
    org_id = _str(variables.get("org_id")) or "anon"

    novel_id = _gid("novel")
    rkey = novel_id
    now = _now_iso()

    conn = await _get_conn()
    try:
        await conn.execute(
            """
            INSERT INTO vertex_narou_novel
              (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
               rkey, repo, did, collection, status, id, title, description,
               genre, tags, user_id, org_id, actor_id, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20)
            """,
            _vid("ai.gftd.apps.narou.novel", rkey),
            int(datetime.now(timezone.utc).timestamp() * 1000),
            _today(),
            0,
            ACTOR_DID,
            rkey,
            ACTOR_DID,
            ACTOR_DID,
            "ai.gftd.apps.narou.novel",
            "draft",
            novel_id,
            title,
            description,
            genre,
            tags,
            user_id,
            org_id,
            ACTOR_DID,
            now,
            now,
        )
    finally:
        await conn.close()

    return {"id": novel_id, "status": "draft"}


async def task_narou_create_chapter(variables: dict) -> dict:
    """Create a chapter draft under a novel."""
    novel_id = _str(variables.get("novel_id"))
    if not novel_id:
        return {"error": "novel_id required"}

    title = _str(variables.get("title"))
    content = _str(variables.get("content"))
    chapter_num = _int(variables.get("chapter_num"), 1)
    user_id = _str(variables.get("user_id")) or "anon"
    org_id = _str(variables.get("org_id")) or "anon"

    chapter_id = _gid("chap")
    rkey = chapter_id
    now = _now_iso()

    conn = await _get_conn()
    try:
        await conn.execute(
            """
            INSERT INTO vertex_narou_chapter
              (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
               rkey, repo, did, collection, status, id, novel_id, chapter_num,
               title, content, word_count, user_id, published_at, asset_manifest_uri,
               org_id, actor_id, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23)
            """,
            _vid("ai.gftd.apps.narou.chapter", rkey),
            int(datetime.now(timezone.utc).timestamp() * 1000),
            _today(),
            0,
            ACTOR_DID,
            rkey,
            ACTOR_DID,
            ACTOR_DID,
            "ai.gftd.apps.narou.chapter",
            "draft",
            chapter_id,
            novel_id,
            chapter_num,
            title,
            content,
            len(content),
            user_id,
            "",
            "",
            org_id,
            ACTOR_DID,
            now,
            now,
        )
    finally:
        await conn.close()

    return {"id": chapter_id, "status": "draft"}


async def task_narou_generate_chapter(variables: dict) -> dict:
    """Generate placeholder chapter content (no LLM call — insert content placeholder)."""
    chapter_id = _str(variables.get("chapter_id"))
    if not chapter_id:
        return {"error": "chapter_id required"}

    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT id, title, chapter_num, novel_id FROM vertex_narou_chapter WHERE id = $1 LIMIT 1",
            chapter_id,
        )
        if not row:
            return {"error": "not found"}

        content = (
            f"Generated chapter placeholder — chapter {row['chapter_num']}: {row['title'] or 'Untitled'}. "
            "This content was automatically generated by the Narou BPMN worker. "
            "Replace with actual LLM-generated content via the generateChapter task."
        )
        now = _now_iso()

        await conn.execute(
            "UPDATE vertex_narou_chapter SET content = $1, word_count = $2, updated_at = $3 WHERE id = $4",
            content,
            len(content),
            now,
            chapter_id,
        )
    finally:
        await conn.close()

    return {"chapter_id": chapter_id, "word_count": len(content)}


async def task_narou_publish_chapter(variables: dict) -> dict:
    """Publish a chapter (set status=published, published_at=now)."""
    chapter_id = _str(variables.get("chapter_id"))
    if not chapter_id:
        return {"error": "chapter_id required"}

    asset_manifest_uri = _str(variables.get("asset_manifest_uri"))
    now = _now_iso()

    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT id, status FROM vertex_narou_chapter WHERE id = $1 LIMIT 1",
            chapter_id,
        )
        if not row:
            return {"error": "not found"}

        await conn.execute(
            """
            UPDATE vertex_narou_chapter
            SET status = $1, published_at = $2, asset_manifest_uri = $3, updated_at = $4
            WHERE id = $5
            """,
            "published",
            now,
            asset_manifest_uri,
            now,
            chapter_id,
        )
    finally:
        await conn.close()

    return {"chapter_id": chapter_id, "status": "published"}


async def task_narou_create_character(variables: dict) -> dict:
    """Create a character for a novel."""
    novel_id = _str(variables.get("novel_id"))
    if not novel_id:
        return {"error": "novel_id required"}

    name = _str(variables.get("name"))
    role = _str(variables.get("role")) or "supporting"
    description = _str(variables.get("description"))
    user_id = _str(variables.get("user_id")) or "anon"
    org_id = _str(variables.get("org_id")) or "anon"

    char_id = _gid("char")
    rkey = char_id
    now = _now_iso()

    conn = await _get_conn()
    try:
        await conn.execute(
            """
            INSERT INTO vertex_narou_character
              (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
               rkey, repo, did, collection, status, id, novel_id, name,
               role, description, user_id, org_id, actor_id, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20)
            """,
            _vid("ai.gftd.apps.narou.character", rkey),
            int(datetime.now(timezone.utc).timestamp() * 1000),
            _today(),
            0,
            ACTOR_DID,
            rkey,
            ACTOR_DID,
            ACTOR_DID,
            "ai.gftd.apps.narou.character",
            "active",
            char_id,
            novel_id,
            name,
            role,
            description,
            user_id,
            org_id,
            ACTOR_DID,
            now,
            now,
        )
    finally:
        await conn.close()

    return {"id": char_id}


async def task_narou_create_world_setting(variables: dict) -> dict:
    """Create a world setting for a novel."""
    novel_id = _str(variables.get("novel_id"))
    if not novel_id:
        return {"error": "novel_id required"}

    name = _str(variables.get("name"))
    description = _str(variables.get("description"))
    user_id = _str(variables.get("user_id")) or "anon"
    org_id = _str(variables.get("org_id")) or "anon"

    world_id = _gid("world")
    rkey = world_id
    now = _now_iso()

    conn = await _get_conn()
    try:
        await conn.execute(
            """
            INSERT INTO vertex_narou_world_setting
              (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
               rkey, repo, did, collection, status, id, novel_id, name,
               description, user_id, org_id, actor_id, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
            """,
            _vid("ai.gftd.apps.narou.worldSetting", rkey),
            int(datetime.now(timezone.utc).timestamp() * 1000),
            _today(),
            0,
            ACTOR_DID,
            rkey,
            ACTOR_DID,
            ACTOR_DID,
            "ai.gftd.apps.narou.worldSetting",
            "active",
            world_id,
            novel_id,
            name,
            description,
            user_id,
            org_id,
            ACTOR_DID,
            now,
            now,
        )
    finally:
        await conn.close()

    return {"id": world_id}


async def task_narou_get_novel(variables: dict) -> dict:
    """Get a novel by ID."""
    novel_id = _str(variables.get("id"))
    if not novel_id:
        return {"error": "id required"}

    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM vertex_narou_novel WHERE id = $1 LIMIT 1",
            novel_id,
        )
        if not row:
            return {"error": "not found"}

        chapter_count_row = await conn.fetchrow(
            "SELECT count(id) AS cnt FROM vertex_narou_chapter WHERE novel_id = $1",
            novel_id,
        )
        chapter_count = int(chapter_count_row["cnt"]) if chapter_count_row else 0
    finally:
        await conn.close()

    return {"novel": dict(row), "chapter_count": chapter_count}


async def task_narou_list_novels(variables: dict) -> dict:
    """List novel works with optional filters."""
    limit = min(_int(variables.get("limit"), 50), 100)
    offset = _int(variables.get("offset"), 0)
    genre = _str(variables.get("genre"))
    status = _str(variables.get("status"))
    user_id = _str(variables.get("user_id"))

    conditions = []
    params: list = []
    param_idx = 1

    if genre:
        conditions.append(f"genre = ${param_idx}")
        params.append(genre)
        param_idx += 1
    if status:
        conditions.append(f"status = ${param_idx}")
        params.append(status)
        param_idx += 1
    if user_id:
        conditions.append(f"user_id = ${param_idx}")
        params.append(user_id)
        param_idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    # RW rule: LIMIT/OFFSET must not be parameterized
    sql = f"SELECT * FROM vertex_narou_novel {where_clause} ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"

    conn = await _get_conn()
    try:
        rows = await conn.fetch(sql, *params)
    finally:
        await conn.close()

    novels = [dict(r) for r in rows]
    return {"novels": novels, "total": len(novels), "offset": offset, "limit": limit}


async def task_narou_get_chapter(variables: dict) -> dict:
    """Get a chapter by ID."""
    chapter_id = _str(variables.get("id"))
    if not chapter_id:
        return {"error": "id required"}

    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM vertex_narou_chapter WHERE id = $1 LIMIT 1",
            chapter_id,
        )
    finally:
        await conn.close()

    if not row:
        return {"error": "not found"}
    return {"chapter": dict(row)}


async def task_narou_list_chapters(variables: dict) -> dict:
    """List chapters for a novel."""
    novel_id = _str(variables.get("novel_id"))
    if not novel_id:
        return {"error": "novel_id required"}

    limit = min(_int(variables.get("limit"), 50), 200)
    offset = _int(variables.get("offset"), 0)
    status = _str(variables.get("status"))

    conditions = ["novel_id = $1"]
    params: list = [novel_id]
    param_idx = 2

    if status:
        conditions.append(f"status = ${param_idx}")
        params.append(status)
        param_idx += 1

    where_clause = "WHERE " + " AND ".join(conditions)
    # RW rule: LIMIT/OFFSET must not be parameterized
    sql = f"SELECT * FROM vertex_narou_chapter {where_clause} ORDER BY chapter_num ASC LIMIT {limit} OFFSET {offset}"

    conn = await _get_conn()
    try:
        rows = await conn.fetch(sql, *params)
    finally:
        await conn.close()

    chapters = [dict(r) for r in rows]
    return {"chapters": chapters, "total": len(chapters), "offset": offset, "limit": limit}


async def task_narou_search_novels(variables: dict) -> dict:
    """Search novels by keyword (app-layer post-filter; no SQL CONTAINS/LIKE per lint rule)."""
    q = _str(variables.get("q")).lower()
    if not q:
        return {"error": "q required"}

    limit = min(_int(variables.get("limit"), 20), 50)
    offset = _int(variables.get("offset"), 0)
    genre = _str(variables.get("genre"))
    tag = _str(variables.get("tag")).lower()

    conditions = []
    params: list = []
    param_idx = 1

    if genre:
        conditions.append(f"genre = ${param_idx}")
        params.append(genre)
        param_idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    # Fetch a wider set then post-filter in Python (no CONTAINS/STARTS WITH per lint rule)
    sql = f"SELECT * FROM vertex_narou_novel {where_clause} ORDER BY created_at DESC LIMIT 500"

    conn = await _get_conn()
    try:
        rows = await conn.fetch(sql, *params)
    finally:
        await conn.close()

    def _matches(row: dict) -> bool:
        title = (row.get("title") or "").lower()
        desc = (row.get("description") or "").lower()
        tags = (row.get("tags") or "").lower()
        if q in title or q in desc or q in tags:
            return True
        if tag and tag in tags:
            return True
        return False

    all_rows = [dict(r) for r in rows]
    filtered = [r for r in all_rows if _matches(r)]
    novels = filtered[offset: offset + limit]
    return {"novels": novels, "total": len(filtered), "offset": offset, "limit": limit}


# ---------------------------------------------------------------------------
# Worker registration
# ---------------------------------------------------------------------------

def register_narou_tasks(worker):
    """Register all narou task handlers with a LangServerWorker instance."""
    from pymagatama.langserver_compat import LangServerJob as Job, LangServerWorker

    _w: LangServerWorker = worker

    @_w.task(task_type="ai.gftd.apps.narou.createNovel", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _create_novel(job: Job):
        result = await task_narou_create_novel(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.createChapter", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _create_chapter(job: Job):
        result = await task_narou_create_chapter(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.generateChapter", timeout_ms=60_000, max_jobs_to_activate=3)
    async def _generate_chapter(job: Job):
        result = await task_narou_generate_chapter(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.publishChapter", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _publish_chapter(job: Job):
        result = await task_narou_publish_chapter(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.createCharacter", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _create_character(job: Job):
        result = await task_narou_create_character(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.createWorldSetting", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _create_world_setting(job: Job):
        result = await task_narou_create_world_setting(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.getNovel", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _get_novel(job: Job):
        result = await task_narou_get_novel(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.listNovels", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _list_novels(job: Job):
        result = await task_narou_list_novels(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.getChapter", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _get_chapter(job: Job):
        result = await task_narou_get_chapter(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.listChapters", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _list_chapters(job: Job):
        result = await task_narou_list_chapters(dict(job.variables))
        await job.set_success_status(variables=result)

    @_w.task(task_type="ai.gftd.apps.narou.searchNovels", timeout_ms=30_000, max_jobs_to_activate=5)
    async def _search_novels(job: Job):
        result = await task_narou_search_novels(dict(job.variables))
        await job.set_success_status(variables=result)

    logger.info("Narou tasks registered (11 handlers).")


# ---------------------------------------------------------------------------
# Standalone entry point (for local testing)
# ---------------------------------------------------------------------------

async def _smoke_test():
    """Quick local smoke test — creates a novel and lists it back."""
    novel_result = await task_narou_create_novel({
        "title": "Test Novel",
        "description": "A test novel for smoke testing",
        "genre": "fantasy",
        "tags": "test,fantasy",
        "user_id": "test_user",
        "org_id": "anon",
    })
    print("createNovel:", novel_result)

    if "id" in novel_result:
        chapter_result = await task_narou_create_chapter({
            "novel_id": novel_result["id"],
            "title": "Chapter 1",
            "content": "Once upon a time...",
            "chapter_num": 1,
        })
        print("createChapter:", chapter_result)

        if "id" in chapter_result:
            gen_result = await task_narou_generate_chapter({"chapter_id": chapter_result["id"]})
            print("generateChapter:", gen_result)

    list_result = await task_narou_list_novels({"limit": 5, "offset": 0})
    print(f"listNovels: {len(list_result.get('novels', []))} novels returned")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_smoke_test())
