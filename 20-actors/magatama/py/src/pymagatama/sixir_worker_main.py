"""6ir.etzhayyim.com — LangServer worker (BPMN service task handlers)."""

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

    @worker.task(task_type="ai.gftd.apps.sixir.listCompanies")
    async def task_list_companies(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT id, ticker, name, exchange, sector, created_at FROM vertex_sixir_company "
                "ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit, offset,
            )
            total = await db.fetchval("SELECT COUNT(*) FROM vertex_sixir_company")
        finally:
            await db.close()

        return {
            "companies": [dict(r) for r in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.sixir.getCompany")
    async def task_get_company(**kwargs):
        company_id = kwargs.get("companyId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, ticker, name, exchange, sector, created_at FROM vertex_sixir_company WHERE id = $1",
                company_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.sixir.listFilings")
    async def task_list_filings(**kwargs):
        company_id = kwargs.get("companyId", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT id, company_id, filing_type, period, filed_at, created_at FROM vertex_sixir_filing "
                "WHERE company_id = $1 ORDER BY filed_at DESC LIMIT $2 OFFSET $3",
                company_id, limit, offset,
            )
            total = await db.fetchval(
                "SELECT COUNT(*) FROM vertex_sixir_filing WHERE company_id = $1", company_id
            )
        finally:
            await db.close()

        return {
            "filings": [dict(r) for r in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.sixir.getFiling")
    async def task_get_filing(**kwargs):
        filing_id = kwargs.get("filingId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, company_id, filing_type, period, filed_at, summary, created_at "
                "FROM vertex_sixir_filing WHERE id = $1",
                filing_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.sixir.listEarnings")
    async def task_list_earnings(**kwargs):
        company_id = kwargs.get("companyId", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT id, company_id, period, eps_actual, eps_estimate, revenue_actual, revenue_estimate, created_at "
                "FROM vertex_sixir_filing WHERE company_id = $1 AND filing_type = 'earnings' "
                "ORDER BY period DESC LIMIT $2 OFFSET $3",
                company_id, limit, offset,
            )
        finally:
            await db.close()

        return {
            "earnings": [dict(r) for r in rows],
            "total": len(rows),
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.sixir.submitAnalysis")
    async def task_submit_analysis(**kwargs):
        company_id = kwargs.get("companyId", "")
        analyst_did = kwargs.get("analystDid", "did:web:6ir.etzhayyim.com")
        rating = kwargs.get("rating", "neutral")
        target_price = float(kwargs.get("targetPrice", 0))
        notes = kwargs.get("notes", "")

        analysis_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        return {
            "analysisId": analysis_id,
            "companyId": company_id,
            "analystDid": analyst_did,
            "rating": rating,
            "targetPrice": target_price,
            "submittedAt": now,
        }

    @worker.task(task_type="ai.gftd.apps.sixir.listAlerts")
    async def task_list_alerts(**kwargs):
        company_id = kwargs.get("companyId", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        return {
            "alerts": [],
            "total": 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.sixir.searchCompanies")
    async def task_search_companies(**kwargs):
        query = kwargs.get("query", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT id, ticker, name, exchange, sector, created_at FROM vertex_sixir_company "
                "WHERE name ILIKE $1 OR ticker ILIKE $1 ORDER BY name LIMIT $2 OFFSET $3",
                f"%{query}%", limit, offset,
            )
            total = await db.fetchval(
                "SELECT COUNT(*) FROM vertex_sixir_company WHERE name ILIKE $1 OR ticker ILIKE $1",
                f"%{query}%",
            )
        finally:
            await db.close()

        return {
            "companies": [dict(r) for r in rows],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
