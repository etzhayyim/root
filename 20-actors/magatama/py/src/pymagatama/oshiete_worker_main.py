"""oshiete.gftd.ai — LangServer worker (BPMN service task handlers)."""

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

    @worker.task(task_type="ai.gftd.apps.oshiete.submit.question")
    async def task_submit_question(**kwargs):
        actor_did = kwargs.get("actorDid", "did:web:oshiete.gftd.ai")
        title = kwargs.get("title", "")
        body = kwargs.get("body", "")
        topic = kwargs.get("topic", "")

        question_id = str(uuid.uuid4())
        vertex_id = f"oshiete:question:{question_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_oshiete_question
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, title, body, topic, status,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
                vertex_id, 0, date.today(), 0, actor_did,
                question_id, title, body, topic, "open",
                "did:web:oshiete.gftd.ai", "did:web:oshiete.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"questionId": question_id, "status": "open"}

    @worker.task(task_type="ai.gftd.apps.oshiete.list.questions")
    async def task_list_questions(**kwargs):
        topic = kwargs.get("topic", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            if topic:
                rows = await db.fetch(
                    "SELECT id, title, topic, status, created_at FROM vertex_oshiete_question "
                    "WHERE topic = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                    topic, limit, offset,
                )
                total = await db.fetchval(
                    "SELECT COUNT(*) FROM vertex_oshiete_question WHERE topic = $1", topic
                )
            else:
                rows = await db.fetch(
                    "SELECT id, title, topic, status, created_at FROM vertex_oshiete_question "
                    "ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total = await db.fetchval("SELECT COUNT(*) FROM vertex_oshiete_question")
        finally:
            await db.close()

        return {
            "questions": [dict(r) for r in rows],
            "total": total or 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.oshiete.get.question")
    async def task_get_question(**kwargs):
        question_id = kwargs.get("questionId", "")

        db = await get_db()
        try:
            row = await db.fetchrow(
                "SELECT id, title, body, topic, status, created_at, updated_at "
                "FROM vertex_oshiete_question WHERE id = $1",
                question_id,
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return dict(row)

    @worker.task(task_type="ai.gftd.apps.oshiete.submit.answer")
    async def task_submit_answer(**kwargs):
        actor_did = kwargs.get("actorDid", "did:web:oshiete.gftd.ai")
        question_id = kwargs.get("questionId", "")
        body = kwargs.get("body", "")

        answer_id = str(uuid.uuid4())
        vertex_id = f"oshiete:answer:{answer_id}"
        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO vertex_oshiete_answer
                   (vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                    id, question_id, body, vote_count,
                    actor_did, org_did, created_at, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
                vertex_id, 0, date.today(), 0, actor_did,
                answer_id, question_id, body, 0,
                "did:web:oshiete.gftd.ai", "did:web:oshiete.gftd.ai", now, now,
            )
        finally:
            await db.close()

        return {"answerId": answer_id, "questionId": question_id}

    @worker.task(task_type="ai.gftd.apps.oshiete.list.answers")
    async def task_list_answers(**kwargs):
        question_id = kwargs.get("questionId", "")
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT id, question_id, body, vote_count, created_at FROM vertex_oshiete_answer "
                "WHERE question_id = $1 ORDER BY vote_count DESC, created_at ASC LIMIT $2 OFFSET $3",
                question_id, limit, offset,
            )
            total = await db.fetchval(
                "SELECT COUNT(*) FROM vertex_oshiete_answer WHERE question_id = $1", question_id
            )
        finally:
            await db.close()

        return {
            "answers": [dict(r) for r in rows],
            "total": total or 0,
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.oshiete.vote.answer")
    async def task_vote_answer(**kwargs):
        answer_id = kwargs.get("answerId", "")
        direction = kwargs.get("direction", "up")

        now = datetime.utcnow().isoformat()

        db = await get_db()
        try:
            if direction == "up":
                await db.execute(
                    "UPDATE vertex_oshiete_answer SET vote_count = vote_count + 1, updated_at = $1 WHERE id = $2",
                    now, answer_id,
                )
            else:
                await db.execute(
                    "UPDATE vertex_oshiete_answer SET vote_count = vote_count - 1, updated_at = $1 WHERE id = $2",
                    now, answer_id,
                )
            row = await db.fetchrow(
                "SELECT id, vote_count FROM vertex_oshiete_answer WHERE id = $1", answer_id
            )
        finally:
            await db.close()

        if not row:
            return {"error": "not found"}
        return {"answerId": answer_id, "voteCount": row["vote_count"], "direction": direction}

    @worker.task(task_type="ai.gftd.apps.oshiete.list.topics")
    async def task_list_topics(**kwargs):
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT topic, COUNT(*) AS question_count FROM vertex_oshiete_question "
                "WHERE topic IS NOT NULL AND topic != '' "
                "GROUP BY topic ORDER BY question_count DESC LIMIT $1 OFFSET $2",
                limit, offset,
            )
        finally:
            await db.close()

        return {
            "topics": [dict(r) for r in rows],
            "offset": offset,
            "limit": limit,
        }

    @worker.task(task_type="ai.gftd.apps.oshiete.get.expert")
    async def task_get_expert(**kwargs):
        topic = kwargs.get("topic", "")

        db = await get_db()
        try:
            rows = await db.fetch(
                "SELECT actor_did, COUNT(*) AS answer_count, SUM(vote_count) AS total_votes "
                "FROM vertex_oshiete_answer a "
                "JOIN vertex_oshiete_question q ON q.id = a.question_id "
                "WHERE q.topic = $1 "
                "GROUP BY actor_did ORDER BY total_votes DESC LIMIT 10",
                topic,
            )
        finally:
            await db.close()

        return {
            "topic": topic,
            "experts": [dict(r) for r in rows],
        }

    await worker.work()


if __name__ == "__main__":
    asyncio.run(run_worker())
