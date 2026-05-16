"""web4.gftd.ai — LangServer worker (BPMN service task handlers)."""

import asyncio
import os
import uuid
from datetime import datetime, date

import asyncpg
from pymagatama.langserver_compat import LangServerWorker, create_langserver_channel

AGENTGATEWAY_MCP_URL = os.getenv("AGENTGATEWAY_MCP_URL", "localhost:8080")
DB_URL = os.getenv("DATABASE_URL", "postgresql://root:rw_66a4db7736799bf888c50a817b4c6a65@45.32.79.245:4566/dev")


async def get_db():
    return await asyncpg.connect(DB_URL)


async def run_worker():
    channel = create_langserver_channel(grpc_address=AGENTGATEWAY_MCP_URL)
    worker = LangServerWorker(channel)

    @worker.task(task_type="ai.gftd.apps.web4.register.expert")
    async def task_register_expert(**kwargs):
        name = kwargs.get("name", "")
        did = kwargs.get("did", "")
        specialization = kwargs.get("specialization", "")

        expert_id = str(uuid.uuid4())
        vertex_id = f"web4:expert:{expert_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_web4_expert
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, name, did, specialization, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, did,
                expert_id, name, did, specialization, "active",
                "did:web:web4.gftd.ai", "did:web:web4.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"expertId": expert_id, "status": "active"}

    @worker.task(task_type="ai.gftd.apps.web4.list.experts")
    async def task_list_experts(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                f"SELECT id, name, did, specialization, status, created_at FROM vertex_web4_expert LIMIT {limit} OFFSET {offset}"
            )
        finally:
            await db.close()

        return {"experts": [dict(r) for r in rows], "offset": offset, "limit": limit}

    @worker.task(task_type="ai.gftd.apps.web4.submit.inference")
    async def task_submit_inference(**kwargs):
        expert_id = kwargs.get("expertId", "")
        model = kwargs.get("model", "")
        input_data = kwargs.get("input", {})

        job_id = str(uuid.uuid4())
        vertex_id = f"web4:inference_job:{job_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_web4_inference_job
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, expert_id, model, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
                vertex_id, 0, date.today(), 0, "did:web:web4.gftd.ai",
                job_id, expert_id, model, "pending",
                "did:web:web4.gftd.ai", "did:web:web4.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"jobId": job_id, "status": "pending"}

    @worker.task(task_type="ai.gftd.apps.web4.get.inferenceResult")
    async def task_get_inference_result(**kwargs):
        job_id = kwargs.get("jobId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, expert_id, model, status, created_at FROM vertex_web4_inference_job WHERE id = $1",
                job_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.web4.list.jobs")
    async def task_list_jobs(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                f"SELECT id, expert_id, model, status, created_at FROM vertex_web4_inference_job LIMIT {limit} OFFSET {offset}"
            )
        finally:
            await db.close()

        return {"jobs": [dict(r) for r in rows], "offset": offset, "limit": limit}

    @worker.task(task_type="ai.gftd.apps.web4.get.jobStatus")
    async def task_get_job_status(**kwargs):
        job_id = kwargs.get("jobId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, status, updated_at FROM vertex_web4_inference_job WHERE id = $1",
                job_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.web4.get.clusterStats")
    async def task_get_cluster_stats(**kwargs):
        db = await get_db()
        try:
            expert_count = await db.fetchval("SELECT COUNT(*) FROM vertex_web4_expert WHERE status = 'active'")
            job_count = await db.fetchval("SELECT COUNT(*) FROM vertex_web4_inference_job")
        finally:
            await db.close()

        return {"activeExperts": expert_count or 0, "totalJobs": job_count or 0}

    @worker.task(task_type="ai.gftd.apps.web4.update.expert")
    async def task_update_expert(**kwargs):
        expert_id = kwargs.get("expertId", "")
        status = kwargs.get("status", "active")
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_web4_expert SET status = $1, updated_at = $2 WHERE id = $3",
                status, now, expert_id,
            )
        finally:
            await db.close()

        return {"expertId": expert_id, "status": status, "updatedAt": now}

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
