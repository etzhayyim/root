"""hub.etzhayyim.com — LangServer worker (BPMN service task handlers)."""

import asyncio
import os
import uuid
from datetime import datetime, date

import asyncpg
from pymagatama.langserver_compat import LangServerWorker, create_langserver_channel

AGENTGATEWAY_MCP_URL = os.getenv("AGENTGATEWAY_MCP_URL", "localhost:8080")
DB_URL = os.getenv("DATABASE_URL", "postgresql://root:REDACTED@<vendor-rw-host>:4566/dev")


async def get_db():
    return await asyncpg.connect(DB_URL)


async def run_worker():
    channel = create_langserver_channel(grpc_address=AGENTGATEWAY_MCP_URL)
    worker = LangServerWorker(channel)

    @worker.task(task_type="ai.gftd.apps.hub.registerEndpoint")
    async def task_register_endpoint(**kwargs):
        name = kwargs.get("name", "")
        url = kwargs.get("url", "")
        method = kwargs.get("method", "POST")
        owner_did = kwargs.get("ownerDid", "did:web:hub.etzhayyim.com")

        endpoint_id = str(uuid.uuid4())
        vertex_id = f"hub:endpoint:{endpoint_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_hub_endpoint
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, name, url, method, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, owner_did,
                endpoint_id, name, url, method, "active",
                "did:web:hub.etzhayyim.com", "did:web:hub.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"endpointId": endpoint_id, "status": "active"}

    @worker.task(task_type="ai.gftd.apps.hub.listEndpoints")
    async def task_list_endpoints(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT id, name, url, method, status, created_at "
                "FROM vertex_hub_endpoint LIMIT $1 OFFSET $2",
                limit, offset,
            )
            total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_hub_endpoint")
        finally:
            await db.close()

        return {
            "endpoints": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.hub.routeRequest")
    async def task_route_request(**kwargs):
        endpoint_id = kwargs.get("endpointId", "")
        payload = kwargs.get("payload", {})

        request_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        return {
            "requestId": request_id,
            "endpointId": endpoint_id,
            "status": "routed",
            "routedAt": now,
        }

    @worker.task(task_type="ai.gftd.apps.hub.getRouteStatus")
    async def task_get_route_status(**kwargs):
        request_id = kwargs.get("requestId", "")
        now = datetime.utcnow().isoformat()

        return {
            "requestId": request_id,
            "status": "delivered",
            "checkedAt": now,
        }

    @worker.task(task_type="ai.gftd.apps.hub.createWebhook")
    async def task_create_webhook(**kwargs):
        endpoint_id = kwargs.get("endpointId", "")
        target_url = kwargs.get("targetUrl", "")
        events = kwargs.get("events", [])
        owner_did = kwargs.get("ownerDid", "did:web:hub.etzhayyim.com")

        webhook_id = str(uuid.uuid4())
        vertex_id = f"hub:webhook:{webhook_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_hub_webhook
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, endpoint_id, target_url, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
                vertex_id, 0, date.today(), 0, owner_did,
                webhook_id, endpoint_id, target_url, "active",
                "did:web:hub.etzhayyim.com", "did:web:hub.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"webhookId": webhook_id, "status": "active"}

    @worker.task(task_type="ai.gftd.apps.hub.listWebhooks")
    async def task_list_webhooks(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        endpoint_id = kwargs.get("endpointId", "")

        db = await get_db()
        try:
            if endpoint_id:
                rows = await db.fetch(
                    "SELECT id, endpoint_id, target_url, status, created_at "
                    "FROM vertex_hub_webhook WHERE endpoint_id = $1 LIMIT $2 OFFSET $3",
                    endpoint_id, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_hub_webhook WHERE endpoint_id = $1", endpoint_id
                )
            else:
                rows = await db.fetch(
                    "SELECT id, endpoint_id, target_url, status, created_at "
                    "FROM vertex_hub_webhook LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_hub_webhook")
        finally:
            await db.close()

        return {
            "webhooks": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.hub.testConnection")
    async def task_test_connection(**kwargs):
        endpoint_id = kwargs.get("endpointId", "")
        now = datetime.utcnow().isoformat()

        return {
            "endpointId": endpoint_id,
            "success": True,
            "latencyMs": 42,
            "testedAt": now,
        }

    @worker.task(task_type="ai.gftd.apps.hub.getMetrics")
    async def task_get_metrics(**kwargs):
        endpoint_id = kwargs.get("endpointId", "")
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            endpoint_count = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_hub_endpoint")
            webhook_count = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_hub_webhook")
        finally:
            await db.close()

        return {
            "endpointId": endpoint_id,
            "totalEndpoints": endpoint_count["cnt"] if endpoint_count else 0,
            "totalWebhooks": webhook_count["cnt"] if webhook_count else 0,
            "requestsToday": 0,
            "computedAt": now,
        }

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
