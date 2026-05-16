"""resources.gftd.ai — LangServer worker (BPMN service task handlers)."""

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

    @worker.task(task_type="ai.gftd.apps.resources.createResource")
    async def task_create_resource(**kwargs):
        name = kwargs.get("name", "")
        kind = kwargs.get("kind", "")
        owner_did = kwargs.get("ownerDid", "did:web:resources.gftd.ai")

        resource_id = str(uuid.uuid4())
        vertex_id = f"resources:resource:{resource_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_resources_resource
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, name, kind, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
                vertex_id, 0, date.today(), 0, owner_did,
                resource_id, name, kind, "active",
                "did:web:resources.gftd.ai", "did:web:resources.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"id": resource_id, "status": "active", "createdAt": now}

    @worker.task(task_type="ai.gftd.apps.resources.getResource")
    async def task_get_resource(**kwargs):
        resource_id = kwargs.get("id", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, name, kind, status, created_at, updated_at "
                "FROM vertex_resources_resource WHERE id = $1",
                resource_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.resources.updateResource")
    async def task_update_resource(**kwargs):
        resource_id = kwargs.get("id", "")
        name = kwargs.get("name", "")
        status = kwargs.get("status", "active")

        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_resources_resource SET name = $1, status = $2, updated_at = $3 WHERE id = $4",
                name, status, now, resource_id,
            )
        finally:
            await db.close()

        return {"id": resource_id, "status": status, "updatedAt": now}

    @worker.task(task_type="ai.gftd.apps.resources.deleteResource")
    async def task_delete_resource(**kwargs):
        resource_id = kwargs.get("id", "")

        db = await get_db()
        try:
            await db.execute(
                "DELETE FROM vertex_resources_resource WHERE id = $1",
                resource_id,
            )
        finally:
            await db.close()

        return {"id": resource_id, "deleted": True}

    @worker.task(task_type="ai.gftd.apps.resources.listResources")
    async def task_list_resources(**kwargs):
        kind = kwargs.get("kind", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            if kind:
                rows = await db.fetch(
                    "SELECT id, name, kind, status, created_at FROM vertex_resources_resource "
                    "WHERE kind = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                    kind, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_resources_resource WHERE kind = $1", kind
                )
            else:
                rows = await db.fetch(
                    "SELECT id, name, kind, status, created_at FROM vertex_resources_resource "
                    "ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_resources_resource"
                )
        finally:
            await db.close()

        return {
            "resources": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.resources.allocateResource")
    async def task_allocate_resource(**kwargs):
        resource_id = kwargs.get("resourceId", "")
        requester_did = kwargs.get("requesterDid", "")
        quantity = kwargs.get("quantity", 1)

        allocation_id = str(uuid.uuid4())
        vertex_id = f"resources:allocation:{allocation_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_resources_allocation
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, resource_id, requester_did, quantity, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, requester_did,
                allocation_id, resource_id, requester_did, quantity, "allocated",
                "did:web:resources.gftd.ai", "did:web:resources.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"allocationId": allocation_id, "resourceId": resource_id, "status": "allocated"}

    @worker.task(task_type="ai.gftd.apps.resources.releaseResource")
    async def task_release_resource(**kwargs):
        allocation_id = kwargs.get("allocationId", "")

        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_resources_allocation SET status = 'released', updated_at = $1 WHERE id = $2",
                now, allocation_id,
            )
        finally:
            await db.close()

        return {"allocationId": allocation_id, "status": "released", "releasedAt": now}

    @worker.task(task_type="ai.gftd.apps.resources.resourceUsage")
    async def task_resource_usage(**kwargs):
        resource_id = kwargs.get("resourceId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT COUNT(*) AS total_allocations FROM vertex_resources_allocation WHERE resource_id = $1",
                resource_id,
            )
            active_row = await db.fetchrow(
                "SELECT COUNT(*) AS active_allocations FROM vertex_resources_allocation "
                "WHERE resource_id = $1 AND status = 'allocated'",
                resource_id,
            )
        finally:
            await db.close()

        return {
            "resourceId": resource_id,
            "totalAllocations": row["total_allocations"] if row else 0,
            "activeAllocations": active_row["active_allocations"] if active_row else 0,
        }

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
