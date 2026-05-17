"""omikuji.etzhayyim.com — LangServer worker (BPMN service task handlers)."""

import asyncio
import os
import random
import uuid
from datetime import datetime, date

import asyncpg
from pymagatama.langserver_compat import LangServerWorker, create_langserver_channel

AGENTGATEWAY_MCP_URL = os.getenv("AGENTGATEWAY_MCP_URL", "localhost:8080")
DB_URL = os.getenv("DATABASE_URL", "postgresql://root:rw_66a4db7736799bf888c50a817b4c6a65@45.32.79.245:4566/dev")

ACTOR_DID = "did:web:omikuji.etzhayyim.com"

FORTUNE_RESULTS = ["大吉", "吉", "中吉", "小吉", "末吉", "凶", "大凶"]


async def get_db():
    return await asyncpg.connect(DB_URL)


async def run_worker():
    channel = create_langserver_channel(grpc_address=AGENTGATEWAY_MCP_URL)
    worker = LangServerWorker(channel)

    @worker.task(task_type="ai.gftd.apps.omikuji.drawFortune")
    async def task_draw_fortune(**kwargs):
        shrine_id = kwargs.get("shrineId", "")
        user_did = kwargs.get("userDid", ACTOR_DID)

        fortune_result = random.choice(FORTUNE_RESULTS)
        draw_id = str(uuid.uuid4())
        vertex_id = f"omikuji:fortune_draw:{draw_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_omikuji_fortune_draw
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, shrine_id, user_did, result, drawn_at,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, ACTOR_DID,
                draw_id, shrine_id, user_did, fortune_result, now,
                ACTOR_DID, ACTOR_DID, now, now,
            )
        finally:
            await db.close()

        return {"drawId": draw_id, "result": fortune_result, "drawnAt": now}

    @worker.task(task_type="ai.gftd.apps.omikuji.listFortunes")
    async def task_list_fortunes(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        shrine_id = kwargs.get("shrineId", "")

        db = await get_db()
        try:
            if shrine_id:
                rows = await db.fetch(
                    "SELECT id, shrine_id, user_did, result, drawn_at FROM vertex_omikuji_fortune_draw WHERE shrine_id = $1 LIMIT $2 OFFSET $3",
                    shrine_id, limit, offset,
                )
                total = await db.fetchval("SELECT COUNT(*) FROM vertex_omikuji_fortune_draw WHERE shrine_id = $1", shrine_id)
            else:
                rows = await db.fetch(
                    "SELECT id, shrine_id, user_did, result, drawn_at FROM vertex_omikuji_fortune_draw LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total = await db.fetchval("SELECT COUNT(*) FROM vertex_omikuji_fortune_draw")
        finally:
            await db.close()

        return {"fortunes": [dict(r) for r in rows], "total": total or 0, "offset": offset, "limit": limit}

    @worker.task(task_type="ai.gftd.apps.omikuji.getFortune")
    async def task_get_fortune(**kwargs):
        draw_id = kwargs.get("drawId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, shrine_id, user_did, result, drawn_at, created_at FROM vertex_omikuji_fortune_draw WHERE id = $1",
                draw_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.omikuji.resetFortune")
    async def task_reset_fortune(**kwargs):
        user_did = kwargs.get("userDid", ACTOR_DID)
        now = datetime.utcnow().isoformat()

        return {"userDid": user_did, "resetAt": now, "ok": True}

    @worker.task(task_type="ai.gftd.apps.omikuji.createShrine")
    async def task_create_shrine(**kwargs):
        name = kwargs.get("name", "")
        location = kwargs.get("location", "")
        description = kwargs.get("description", "")

        shrine_id = str(uuid.uuid4())
        vertex_id = f"omikuji:shrine:{shrine_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_omikuji_shrine
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, name, location, description, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, ACTOR_DID,
                shrine_id, name, location, description, "active",
                ACTOR_DID, ACTOR_DID, now, now,
            )
        finally:
            await db.close()

        return {"shrineId": shrine_id, "status": "active", "createdAt": now}

    @worker.task(task_type="ai.gftd.apps.omikuji.updateShrine")
    async def task_update_shrine(**kwargs):
        shrine_id = kwargs.get("shrineId", "")
        name = kwargs.get("name", "")
        description = kwargs.get("description", "")

        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_omikuji_shrine SET name = $1, description = $2, updated_at = $3 WHERE id = $4",
                name, description, now, shrine_id,
            )
        finally:
            await db.close()

        return {"shrineId": shrine_id, "updatedAt": now}

    @worker.task(task_type="ai.gftd.apps.omikuji.listShrines")
    async def task_list_shrines(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT id, name, location, status, created_at FROM vertex_omikuji_shrine LIMIT $1 OFFSET $2",
                limit, offset,
            )
            total = await db.fetchval("SELECT COUNT(*) FROM vertex_omikuji_shrine")
        finally:
            await db.close()

        return {"shrines": [dict(r) for r in rows], "total": total or 0, "offset": offset, "limit": limit}

    @worker.task(task_type="ai.gftd.apps.omikuji.getShrine")
    async def task_get_shrine(**kwargs):
        shrine_id = kwargs.get("shrineId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, name, location, description, status, created_at, updated_at FROM vertex_omikuji_shrine WHERE id = $1",
                shrine_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
