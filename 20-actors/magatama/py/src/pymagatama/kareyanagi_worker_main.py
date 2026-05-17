"""kareyanagi.etzhayyim.com — LangServer worker (BPMN service task handlers)."""

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

    @worker.task(task_type="ai.gftd.apps.kareyanagi.createListing")
    async def task_create_listing(**kwargs):
        seller_did = kwargs.get("sellerDid", "")
        product_name = kwargs.get("productName", "")
        price = float(kwargs.get("price", 0.0))
        currency = kwargs.get("currency", "JPY")
        quantity = int(kwargs.get("quantity", 0))
        owner_did = kwargs.get("ownerDid", "did:web:kareyanagi.etzhayyim.com")

        listing_id = str(uuid.uuid4())
        vertex_id = f"kareyanagi:listing:{listing_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_kareyanagi_listing
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, seller_did, product_name, price, currency, quantity, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)""",
                vertex_id, 0, date.today(), 0, owner_did,
                listing_id, seller_did, product_name, price, currency, quantity, "active",
                "did:web:kareyanagi.etzhayyim.com", "did:web:kareyanagi.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"listingId": listing_id, "status": "active"}

    @worker.task(task_type="ai.gftd.apps.kareyanagi.listListings")
    async def task_list_listings(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        seller_did = kwargs.get("sellerDid", "")

        db = await get_db()
        try:
            if seller_did:
                rows = await db.fetch(
                    "SELECT id, seller_did, product_name, price, currency, quantity, status, created_at "
                    "FROM vertex_kareyanagi_listing WHERE seller_did = $1 LIMIT $2 OFFSET $3",
                    seller_did, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_kareyanagi_listing WHERE seller_did = $1", seller_did
                )
            else:
                rows = await db.fetch(
                    "SELECT id, seller_did, product_name, price, currency, quantity, status, created_at "
                    "FROM vertex_kareyanagi_listing LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_kareyanagi_listing")
        finally:
            await db.close()

        return {
            "listings": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.kareyanagi.createOrder")
    async def task_create_order(**kwargs):
        buyer_did = kwargs.get("buyerDid", "")
        listing_id = kwargs.get("listingId", "")
        quantity = int(kwargs.get("quantity", 1))
        owner_did = kwargs.get("ownerDid", "did:web:kareyanagi.etzhayyim.com")

        order_id = str(uuid.uuid4())
        vertex_id = f"kareyanagi:order:{order_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_kareyanagi_order
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, buyer_did, listing_id, quantity, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, owner_did,
                order_id, buyer_did, listing_id, quantity, "pending",
                "did:web:kareyanagi.etzhayyim.com", "did:web:kareyanagi.etzhayyim.com", now, now,
            )
        finally:
            await db.close()

        return {"orderId": order_id, "status": "pending"}

    @worker.task(task_type="ai.gftd.apps.kareyanagi.listOrders")
    async def task_list_orders(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        buyer_did = kwargs.get("buyerDid", "")

        db = await get_db()
        try:
            if buyer_did:
                rows = await db.fetch(
                    "SELECT id, buyer_did, listing_id, quantity, status, created_at "
                    "FROM vertex_kareyanagi_order WHERE buyer_did = $1 LIMIT $2 OFFSET $3",
                    buyer_did, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_kareyanagi_order WHERE buyer_did = $1", buyer_did
                )
            else:
                rows = await db.fetch(
                    "SELECT id, buyer_did, listing_id, quantity, status, created_at "
                    "FROM vertex_kareyanagi_order LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_kareyanagi_order")
        finally:
            await db.close()

        return {
            "orders": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.kareyanagi.updateInventory")
    async def task_update_inventory(**kwargs):
        listing_id = kwargs.get("listingId", "")
        delta = int(kwargs.get("delta", 0))
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_kareyanagi_listing SET quantity = quantity + $1, updated_at = $2 WHERE id = $3",
                delta, now, listing_id,
            )
        finally:
            await db.close()

        return {"listingId": listing_id, "delta": delta, "updatedAt": now}

    @worker.task(task_type="ai.gftd.apps.kareyanagi.getInventory")
    async def task_get_inventory(**kwargs):
        listing_id = kwargs.get("listingId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, product_name, quantity, status FROM vertex_kareyanagi_listing WHERE id = $1",
                listing_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.kareyanagi.processTrade")
    async def task_process_trade(**kwargs):
        order_id = kwargs.get("orderId", "")
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                "UPDATE vertex_kareyanagi_order SET status = 'completed', updated_at = $1 WHERE id = $2",
                now, order_id,
            )
        finally:
            await db.close()

        return {"orderId": order_id, "status": "completed", "processedAt": now}

    @worker.task(task_type="ai.gftd.apps.kareyanagi.getTradeHistory")
    async def task_get_trade_history(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        seller_did = kwargs.get("sellerDid", "")

        db = await get_db()
        try:
            if seller_did:
                rows = await db.fetch(
                    "SELECT o.id, o.buyer_did, o.listing_id, o.quantity, o.status, o.created_at "
                    "FROM vertex_kareyanagi_order o "
                    "JOIN vertex_kareyanagi_listing l ON o.listing_id = l.id "
                    "WHERE l.seller_did = $1 ORDER BY o.created_at DESC LIMIT $2 OFFSET $3",
                    seller_did, limit, offset,
                )
                total_row = await db.fetchrow(
                    "SELECT COUNT(*) AS cnt FROM vertex_kareyanagi_order o "
                    "JOIN vertex_kareyanagi_listing l ON o.listing_id = l.id WHERE l.seller_did = $1",
                    seller_did,
                )
            else:
                rows = await db.fetch(
                    "SELECT id, buyer_did, listing_id, quantity, status, created_at "
                    "FROM vertex_kareyanagi_order ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total_row = await db.fetchrow("SELECT COUNT(*) AS cnt FROM vertex_kareyanagi_order")
        finally:
            await db.close()

        return {
            "trades": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
            "offset": offset,
            "limit": limit,
        }

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
