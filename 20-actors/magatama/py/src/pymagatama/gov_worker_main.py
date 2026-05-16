"""gov.gftd.ai — LangServer worker (BPMN service task handlers)."""

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

    @worker.task(task_type="ai.gftd.apps.gov.registerAgency")
    async def task_register_agency(**kwargs):
        name = kwargs.get("name", "")
        name_local = kwargs.get("nameLocal", "")
        jurisdiction = kwargs.get("jurisdiction", "")
        branch = kwargs.get("branch", "")
        level = kwargs.get("level", "national")
        cofog = kwargs.get("cofog", "")
        parent_agency_did = kwargs.get("parentAgencyDid", "")
        established_at = kwargs.get("establishedAt", "")
        legal_basis = kwargs.get("legalBasis", "")
        website_uri = kwargs.get("websiteUri", "")

        agency_id = str(uuid.uuid4())
        actor_did = f"did:web:gov.gftd.ai:{jurisdiction.lower()}:{cofog}:{agency_id[:8]}"
        vertex_id = f"gov:agency:{agency_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_gov_official_agency
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, name, name_local, jurisdiction, branch, level, cofog,
                    parent_agency_did, established_at, legal_basis, website_uri,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20)""",
                vertex_id, 0, date.today(), 0, actor_did,
                agency_id, name, name_local, jurisdiction, branch, level, cofog,
                parent_agency_did, established_at, legal_basis, website_uri,
                actor_did, "did:web:gov.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"did": actor_did, "uri": f"at://{actor_did}/ai.gftd.apps.gov.agency/{agency_id}"}

    @worker.task(task_type="ai.gftd.apps.gov.recordOfficial")
    async def task_record_official(**kwargs):
        agency_did = kwargs.get("agencyDid", "")
        person_did = kwargs.get("personDid", "")
        role = kwargs.get("role", "")
        appointed_at = kwargs.get("appointedAt", "")
        term_ends_at = kwargs.get("termEndsAt", "")
        appointed_by_did = kwargs.get("appointedByDid", "")
        confirmation_process = kwargs.get("confirmationProcess", "appointment")

        official_id = str(uuid.uuid4())
        vertex_id = f"gov:official:{official_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_gov_official
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, agency_did, person_did, role, appointed_at,
                    term_ends_at, appointed_by_did, confirmation_process,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)""",
                vertex_id, 0, date.today(), 0, person_did,
                official_id, agency_did, person_did, role, appointed_at,
                term_ends_at, appointed_by_did, confirmation_process,
                "did:web:gov.gftd.ai", "did:web:gov.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"uri": f"at://did:web:gov.gftd.ai/ai.gftd.apps.gov.official/{official_id}"}

    @worker.task(task_type="ai.gftd.apps.gov.submitConsult")
    async def task_submit_consult(**kwargs):
        requester_did = kwargs.get("requesterDid", "")
        domain = kwargs.get("domain", "healthcare")
        category = kwargs.get("category", "")
        query = kwargs.get("query", "")
        municipality_code = kwargs.get("municipalityCode", "")
        priority = kwargs.get("priority", "normal")

        consult_id = str(uuid.uuid4())
        vertex_id = f"gov:consult:{consult_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_gov_consult
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, requester_did, domain, category, query,
                    municipality_code, priority, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)""",
                vertex_id, 0, date.today(), 2, requester_did,
                consult_id, requester_did, domain, category, query,
                municipality_code, priority, "open",
                "did:web:gov.gftd.ai", "did:web:gov.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"id": consult_id, "status": "open"}

    @worker.task(task_type="ai.gftd.apps.gov.listAgencies")
    async def task_list_agencies(**kwargs):
        jurisdiction = kwargs.get("jurisdiction", "")
        branch = kwargs.get("branch", "")
        level = kwargs.get("level", "")
        cofog = kwargs.get("cofog", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            conditions = []
            params = []
            p = 1
            if jurisdiction:
                conditions.append(f"jurisdiction = ${p}"); params.append(jurisdiction); p += 1
            if branch:
                conditions.append(f"branch = ${p}"); params.append(branch); p += 1
            if level:
                conditions.append(f"level = ${p}"); params.append(level); p += 1
            if cofog:
                conditions.append(f"cofog = ${p}"); params.append(cofog); p += 1
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            params += [limit, offset]
            rows = await db.fetch(
                f"SELECT id, name, name_local, jurisdiction, branch, cofog, actor_did, created_at "
                f"FROM vertex_gov_official_agency {where} "
                f"ORDER BY created_at DESC LIMIT ${p} OFFSET ${p+1}",
                *params,
            )
            total_row = await db.fetchrow(f"SELECT COUNT(*) as cnt FROM vertex_gov_official_agency {where}", *params[:-2])
        finally:
            await db.close()

        agencies = [dict(r) for r in rows]
        return {"agencies": agencies, "total": total_row["cnt"] if total_row else 0, "offset": offset, "limit": limit}

    @worker.task(task_type="ai.gftd.apps.gov.getAgency")
    async def task_get_agency(**kwargs):
        agency_id = kwargs.get("id", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT * FROM vertex_gov_official_agency WHERE id = $1", agency_id
            )
            officials = await db.fetch(
                "SELECT * FROM vertex_gov_official WHERE agency_did = $1 ORDER BY appointed_at DESC LIMIT 20",
                row["actor_did"] if row else "",
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return {"agency": dict(row), "officials": [dict(o) for o in officials]}

    @worker.task(task_type="ai.gftd.apps.gov.listOfficials")
    async def task_list_officials(**kwargs):
        agency_did = kwargs.get("agencyDid", "")
        role = kwargs.get("role", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            conditions = []
            params = []
            p = 1
            if agency_did:
                conditions.append(f"agency_did = ${p}"); params.append(agency_did); p += 1
            if role:
                conditions.append(f"role = ${p}"); params.append(role); p += 1
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            params += [limit, offset]
            rows = await db.fetch(
                f"SELECT id, agency_did, person_did, role, appointed_at, term_ends_at, confirmation_process "
                f"FROM vertex_gov_official {where} "
                f"ORDER BY appointed_at DESC LIMIT ${p} OFFSET ${p+1}",
                *params,
            )
        finally:
            await db.close()

        return {"officials": [dict(r) for r in rows], "offset": offset, "limit": limit}

    @worker.task(task_type="ai.gftd.apps.gov.listMunicipalities")
    async def task_list_municipalities(**kwargs):
        prefecture = kwargs.get("prefecture", "")
        limit = int(kwargs.get("limit", 100))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            conditions = []
            params = []
            p = 1
            if prefecture:
                conditions.append(f"prefecture = ${p}"); params.append(prefecture); p += 1
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            params += [limit, offset]
            rows = await db.fetch(
                f"SELECT municipality_code, prefecture, city, site_url, coverage_pct, status "
                f"FROM vertex_gov_municipality {where} "
                f"ORDER BY prefecture, city LIMIT ${p} OFFSET ${p+1}",
                *params,
            )
        finally:
            await db.close()

        return {"municipalities": [dict(r) for r in rows], "offset": offset, "limit": limit}

    @worker.task(task_type="ai.gftd.apps.gov.listConsults")
    async def task_list_consults(**kwargs):
        requester_did = kwargs.get("requesterDid", "")
        domain = kwargs.get("domain", "")
        status = kwargs.get("status", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            conditions = []
            params = []
            p = 1
            if requester_did:
                conditions.append(f"requester_did = ${p}"); params.append(requester_did); p += 1
            if domain:
                conditions.append(f"domain = ${p}"); params.append(domain); p += 1
            if status:
                conditions.append(f"status = ${p}"); params.append(status); p += 1
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            params += [limit, offset]
            rows = await db.fetch(
                f"SELECT id, requester_did, domain, category, priority, status, created_at "
                f"FROM vertex_gov_consult {where} "
                f"ORDER BY created_at DESC LIMIT ${p} OFFSET ${p+1}",
                *params,
            )
        finally:
            await db.close()

        return {"consults": [dict(r) for r in rows], "offset": offset, "limit": limit}

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
