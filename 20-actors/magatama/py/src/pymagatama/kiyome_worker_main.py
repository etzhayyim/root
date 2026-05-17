"""kiyome.etzhayyim.com — LangServer worker (BPMN service task handlers)."""

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

    @worker.task(task_type="ai.gftd.apps.kiyome.submitClearance")
    async def task_submit_clearance(**kwargs):
        subject_did = kwargs.get("subjectDid", "")
        clearance_type = kwargs.get("clearanceType", "")
        description = kwargs.get("description", "")
        owner_did = kwargs.get("ownerDid", "did:web:kiyome.etzhayyim.com")

        clearance_id = str(uuid.uuid4())
        vertex_id = f"kiyome:clearance:{clearance_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_kiyome_clearance
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, subject_did, clearance_type, description, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, owner_did,
                clearance_id, subject_did, clearance_type, description, "pending",
                "did:web:kiyome.etzhayyim.com", "did:web:kiyome.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"clearanceId": clearance_id, "status": "pending"}

    @worker.task(task_type="ai.gftd.apps.kiyome.listClearances")
    async def task_list_clearances(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        status = kwargs.get("status", "")

        db = await get_db()
        try:
            if status:
                rows = await db.fetch(
                    "SELECT id, subject_did, clearance_type, description, status, created_at "
                    "FROM vertex_kiyome_clearance WHERE status = $1 LIMIT $2 OFFSET $3",
                    status, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_kiyome_clearance WHERE status = $1", status
                )
            else:
                rows = await db.fetch(
                    "SELECT id, subject_did, clearance_type, description, status, created_at "
                    "FROM vertex_kiyome_clearance LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_kiyome_clearance")
        finally:
            await db.close()

        return {
            "clearances": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.kiyome.approveClearance")
    async def task_approve_clearance(**kwargs):
        clearance_id = kwargs.get("clearanceId", "")
        approver_did = kwargs.get("approverDid", "")
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_kiyome_clearance SET status = 'approved', updated_at = $1 WHERE id = $2",
                now, clearance_id,
            )
        finally:
            await db.close()

        return {"clearanceId": clearance_id, "status": "approved", "approvedAt": now, "approverDid": approver_did}

    @worker.task(task_type="ai.gftd.apps.kiyome.rejectClearance")
    async def task_reject_clearance(**kwargs):
        clearance_id = kwargs.get("clearanceId", "")
        reason = kwargs.get("reason", "")
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_kiyome_clearance SET status = 'rejected', updated_at = $1 WHERE id = $2",
                now, clearance_id,
            )
        finally:
            await db.close()

        return {"clearanceId": clearance_id, "status": "rejected", "rejectedAt": now, "reason": reason}

    @worker.task(task_type="ai.gftd.apps.kiyome.createAuditLog")
    async def task_create_audit_log(**kwargs):
        actor_did = kwargs.get("actorDid", "")
        action = kwargs.get("action", "")
        resource = kwargs.get("resource", "")
        owner_did = kwargs.get("ownerDid", "did:web:kiyome.etzhayyim.com")

        log_id = str(uuid.uuid4())
        vertex_id = f"kiyome:audit_log:{log_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_kiyome_audit_log
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, actor_did_ref, action, resource,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
                vertex_id, 0, date.today(), 0, owner_did,
                log_id, actor_did, action, resource,
                "did:web:kiyome.etzhayyim.com", "did:web:kiyome.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"logId": log_id, "createdAt": now}

    @worker.task(task_type="ai.gftd.apps.kiyome.listAuditLogs")
    async def task_list_audit_logs(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        actor_did = kwargs.get("actorDid", "")

        db = await get_db()
        try:
            if actor_did:
                rows = await db.fetch(
                    "SELECT id, actor_did_ref, action, resource, created_at "
                    "FROM vertex_kiyome_audit_log WHERE actor_did_ref = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                    actor_did, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_kiyome_audit_log WHERE actor_did_ref = $1", actor_did
                )
            else:
                rows = await db.fetch(
                    "SELECT id, actor_did_ref, action, resource, created_at "
                    "FROM vertex_kiyome_audit_log ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_kiyome_audit_log")
        finally:
            await db.close()

        return {
            "logs": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.kiyome.getComplianceStatus")
    async def task_get_compliance_status(**kwargs):
        subject_did = kwargs.get("subjectDid", "")
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            pending = await db.fetchrow(
                "SELECT COUNT(*) AS cnt FROM vertex_kiyome_clearance WHERE subject_did = $1 AND status = 'pending'",
                subject_did,
            )
            approved = await db.fetchrow(
                "SELECT COUNT(*) AS cnt FROM vertex_kiyome_clearance WHERE subject_did = $1 AND status = 'approved'",
                subject_did,
            )
            rejected = await db.fetchrow(
                "SELECT COUNT(*) AS cnt FROM vertex_kiyome_clearance WHERE subject_did = $1 AND status = 'rejected'",
                subject_did,
            )
        finally:
            await db.close()

        return {
            "subjectDid": subject_did,
            "pendingClearances": pending["cnt"] if pending else 0,
            "approvedClearances": approved["cnt"] if approved else 0,
            "rejectedClearances": rejected["cnt"] if rejected else 0,
            "compliant": (pending["cnt"] if pending else 0) == 0,
            "checkedAt": now,
        }

    @worker.task(task_type="ai.gftd.apps.kiyome.runPurification")
    async def task_run_purification(**kwargs):
        scope = kwargs.get("scope", "all")
        dry_run = kwargs.get("dryRun", False)
        now = datetime.utcnow().isoformat()

        run_id = str(uuid.uuid4())

        return {
            "runId": run_id,
            "scope": scope,
            "dryRun": dry_run,
            "status": "completed",
            "itemsPurified": 0,
            "completedAt": now,
        }

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
