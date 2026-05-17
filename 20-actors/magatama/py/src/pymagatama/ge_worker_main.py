"""ge.etzhayyim.com — LangServer worker (BPMN service task handlers)."""

import asyncio
import os
import uuid
from datetime import datetime, date

import asyncpg
from pymagatama.langserver_compat import LangServerWorker, create_langserver_channel

AGENTGATEWAY_MCP_URL = os.getenv("AGENTGATEWAY_MCP_URL", "localhost:8080")
DB_URL = os.getenv("DATABASE_URL", "REDACTED_USE_DATABASE_URL_ENV")


async def get_db():
    return await asyncpg.connect(DB_URL)


async def run_worker():
    channel = create_langserver_channel(grpc_address=AGENTGATEWAY_MCP_URL)
    worker = LangServerWorker(channel)

    @worker.task(task_type="ai.gftd.apps.ge.createOrg")
    async def task_create_org(**kwargs):
        name = kwargs.get("name", "")
        country = kwargs.get("country", "")
        industry = kwargs.get("industry", "")
        owner_did = kwargs.get("ownerDid", "did:web:ge.etzhayyim.com")

        org_id = str(uuid.uuid4())
        vertex_id = f"ge:org:{org_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_ge_org
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, name, country, industry, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, owner_did,
                org_id, name, country, industry, "active",
                "did:web:ge.etzhayyim.com", "did:web:ge.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"orgId": org_id, "status": "active"}

    @worker.task(task_type="ai.gftd.apps.ge.listOrgs")
    async def task_list_orgs(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        country = kwargs.get("country", "")

        db = await get_db()
        try:
            if country:
                rows = await db.fetch(
                    "SELECT id, name, country, industry, status, created_at "
                    "FROM vertex_ge_org WHERE country = $1 LIMIT $2 OFFSET $3",
                    country, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_ge_org WHERE country = $1", country
                )
            else:
                rows = await db.fetch(
                    "SELECT id, name, country, industry, status, created_at "
                    "FROM vertex_ge_org LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_ge_org")
        finally:
            await db.close()

        return {
            "orgs": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.ge.createProject")
    async def task_create_project(**kwargs):
        org_id = kwargs.get("orgId", "")
        name = kwargs.get("name", "")
        description = kwargs.get("description", "")
        owner_did = kwargs.get("ownerDid", "did:web:ge.etzhayyim.com")

        project_id = str(uuid.uuid4())
        vertex_id = f"ge:project:{project_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_ge_project
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, org_id, name, description, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, owner_did,
                project_id, org_id, name, description, "active",
                "did:web:ge.etzhayyim.com", "did:web:ge.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"projectId": project_id, "status": "active"}

    @worker.task(task_type="ai.gftd.apps.ge.listProjects")
    async def task_list_projects(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        org_id = kwargs.get("orgId", "")

        db = await get_db()
        try:
            if org_id:
                rows = await db.fetch(
                    "SELECT id, org_id, name, description, status, created_at "
                    "FROM vertex_ge_project WHERE org_id = $1 LIMIT $2 OFFSET $3",
                    org_id, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_ge_project WHERE org_id = $1", org_id
                )
            else:
                rows = await db.fetch(
                    "SELECT id, org_id, name, description, status, created_at "
                    "FROM vertex_ge_project LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_ge_project")
        finally:
            await db.close()

        return {
            "projects": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.ge.assignResource")
    async def task_assign_resource(**kwargs):
        project_id = kwargs.get("projectId", "")
        resource_did = kwargs.get("resourceDid", "")
        role = kwargs.get("role", "member")
        owner_did = kwargs.get("ownerDid", "did:web:ge.etzhayyim.com")

        assignment_id = str(uuid.uuid4())
        vertex_id = f"ge:resource_assignment:{assignment_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_ge_resource_assignment
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, project_id, resource_did, role, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, owner_did,
                assignment_id, project_id, resource_did, role, "assigned",
                "did:web:ge.etzhayyim.com", "did:web:ge.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"assignmentId": assignment_id, "status": "assigned"}

    @worker.task(task_type="ai.gftd.apps.ge.listResources")
    async def task_list_resources(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        project_id = kwargs.get("projectId", "")

        db = await get_db()
        try:
            if project_id:
                rows = await db.fetch(
                    "SELECT id, project_id, resource_did, role, status, created_at "
                    "FROM vertex_ge_resource_assignment WHERE project_id = $1 LIMIT $2 OFFSET $3",
                    project_id, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_ge_resource_assignment WHERE project_id = $1",
                    project_id,
                )
            else:
                rows = await db.fetch(
                    "SELECT id, project_id, resource_did, role, status, created_at "
                    "FROM vertex_ge_resource_assignment LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_ge_resource_assignment"
                )
        finally:
            await db.close()

        return {
            "resources": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.ge.getOrgMetrics")
    async def task_get_org_metrics(**kwargs):
        org_id = kwargs.get("orgId", "")

        db = await get_db()
        try:
            project_count = await db.fetchrow(
                "SELECT COUNT(*) AS cnt FROM vertex_ge_project WHERE org_id = $1", org_id
            )
            resource_count = await db.fetchrow(
                "SELECT COUNT(*) AS cnt FROM vertex_ge_resource_assignment ra "
                "JOIN vertex_ge_project p ON ra.project_id = p.id WHERE p.org_id = $1",
                org_id,
            )
        finally:
            await db.close()

        return {
            "orgId": org_id,
            "projectCount": project_count["cnt"] if project_count else 0,
            "resourceCount": resource_count["cnt"] if resource_count else 0,
            "computedAt": datetime.utcnow().isoformat(),
        }

    @worker.task(task_type="ai.gftd.apps.ge.planWorkforce")
    async def task_plan_workforce(**kwargs):
        org_id = kwargs.get("orgId", "")
        target_headcount = int(kwargs.get("targetHeadcount", 0))
        horizon_months = int(kwargs.get("horizonMonths", 12))

        plan_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        return {
            "planId": plan_id,
            "orgId": org_id,
            "targetHeadcount": target_headcount,
            "horizonMonths": horizon_months,
            "recommendations": [],
            "createdAt": now,
        }

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
