"""yatabase Activation actor — day-3 / day-7 onboarding sequence.

Runs daily at 08:30 JST via APScheduler (registered in server.py).
Finds tenants who signed up but haven't queried yet and sends
targeted onboarding emails via vertex_email_outbox.

Pipeline: find_inactive → enqueue_d3 → enqueue_d7 → report

Env vars: none additional (uses shared DB pool)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch

_log = logging.getLogger(__name__)

_D3_SUBJECT = "yatabase — ここから始めてみてください (Cypher入門)"
_D7_SUBJECT = "yatabase — セットアップでお困りですか？"

_D3_BODY = """\
こんにちは！

yatabase にサインアップいただいてから3日が経ちました。
まだクエリを試していない場合、これが最初の一歩です。

◆ 最初の Cypher クエリ (30秒)

  curl -X POST https://yatabase.etzhayyim.com/cypher \\
    -H "Authorization: Bearer $YOUR_API_KEY" \\
    -H "Content-Type: application/json" \\
    -d '{"query": "CREATE (n:Person {name: \\"Alice\\"}) RETURN n"}'

詳細: https://yatabase.etzhayyim.com/docs/quickstart

ご不明な点があれば、このメールに返信してください。

yatabase team
"""

_D7_BODY = """\
こんにちは！

yatabase をご利用いただきありがとうございます。
サインアップから7日が経ちましたが、まだクエリが少ない状態のようです。

もし何かお困りのことがあれば、15分のセットアップサポートをご利用ください:
  → https://yatabase.etzhayyim.com/support

◆ MCP endpoint (AI エージェント連携):
  curl -X POST https://yatabase.etzhayyim.com/mcp \\
    -H "Authorization: Bearer $YOUR_API_KEY" \\
    -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

引き続きよろしくお願いします。

yatabase team
"""


# ── State ─────────────────────────────────────────────────────────────────────

class ActivationState(TypedDict, total=False):
    run_date: str
    d3_candidates: list[dict]
    d7_candidates: list[dict]
    sent_d3: int
    sent_d7: int
    summary: str


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def find_inactive(state: ActivationState) -> ActivationState:
    today = datetime.now(timezone.utc).date().isoformat()
    d3: list[dict] = []
    d7: list[dict] = []
    try:
        # Day-3: signed up 3-4 days ago, 0 queries (plan=free, query_count=0)
        # Note: owner_did serves as org_did; contact_email added by migration 20260521110000
        d3_rows = await fetch(
            """
            SELECT vertex_id, owner_did AS org_did,
                   COALESCE(contact_email, '') AS contact_email
            FROM vertex_api_key
            WHERE created_at::timestamptz BETWEEN NOW() - INTERVAL '4 days' AND NOW() - INTERVAL '3 days'
              AND COALESCE(plan, 'free') = 'free'
              AND COALESCE(query_count, 0) = 0
            LIMIT 50
            """
        )
        d3 = [dict(r) for r in d3_rows]

        # Day-7: signed up 7-8 days ago, fewer than 10 queries
        d7_rows = await fetch(
            """
            SELECT vertex_id, owner_did AS org_did,
                   COALESCE(contact_email, '') AS contact_email
            FROM vertex_api_key
            WHERE created_at::timestamptz BETWEEN NOW() - INTERVAL '8 days' AND NOW() - INTERVAL '7 days'
              AND COALESCE(plan, 'free') = 'free'
              AND COALESCE(query_count, 0) < 10
            LIMIT 50
            """
        )
        d7 = [dict(r) for r in d7_rows]
    except Exception as e:
        _log.warning("[activation] find_inactive query failed: %s", e)

    _log.info("[activation] d3=%d d7=%d candidates", len(d3), len(d7))
    return {**state, "run_date": today, "d3_candidates": d3, "d7_candidates": d7}


async def enqueue_d3(state: ActivationState) -> ActivationState:
    sent = 0
    for tenant in (state.get("d3_candidates") or []):
        email = (tenant.get("contact_email") or "").strip()
        org_did = tenant.get("org_did", "unknown")
        # Skip if already sent activation-d3 for this org
        try:
            existing = await fetch(
                """
                SELECT 1 FROM vertex_email_outbox
                WHERE org_did = $1 AND kind = 'activation-d3'
                LIMIT 1
                """,
                org_did,
            )
            if existing:
                continue
        except Exception:
            pass
        try:
            await execute(
                """
                INSERT INTO vertex_email_outbox
                  (vertex_id, org_did, kind, subject, body_text,
                   recipient_email, status, created_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                str(uuid.uuid4()),
                org_did,
                "activation-d3",
                _D3_SUBJECT,
                _D3_BODY,
                email,
                "queued-no-recipient" if not email else "queued",
                datetime.now(timezone.utc),
            )
            sent += 1
        except Exception as e:
            _log.warning("[activation] d3 insert failed for %s: %s", org_did, e)
    return {**state, "sent_d3": sent}


async def enqueue_d7(state: ActivationState) -> ActivationState:
    sent = 0
    for tenant in (state.get("d7_candidates") or []):
        email = (tenant.get("contact_email") or "").strip()
        org_did = tenant.get("org_did", "unknown")
        try:
            existing = await fetch(
                """
                SELECT 1 FROM vertex_email_outbox
                WHERE org_did = $1 AND kind = 'activation-d7'
                LIMIT 1
                """,
                org_did,
            )
            if existing:
                continue
        except Exception:
            pass
        try:
            await execute(
                """
                INSERT INTO vertex_email_outbox
                  (vertex_id, org_did, kind, subject, body_text,
                   recipient_email, status, created_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                str(uuid.uuid4()),
                org_did,
                "activation-d7",
                _D7_SUBJECT,
                _D7_BODY,
                email,
                "queued-no-recipient" if not email else "queued",
                datetime.now(timezone.utc),
            )
            sent += 1
        except Exception as e:
            _log.warning("[activation] d7 insert failed for %s: %s", org_did, e)
    return {**state, "sent_d7": sent}


async def report(state: ActivationState) -> ActivationState:
    run_date = state.get("run_date", "")
    d3 = state.get("sent_d3", 0)
    d7 = state.get("sent_d7", 0)
    summary = f"[{run_date}] activation: d3={d3}件送信 d7={d7}件送信"
    _log.info("[activation] %s", summary)
    return {**state, "summary": summary}


# ── Graph ──────────────────────────────────────────────────────────────────────

def _build() -> Any:
    sg = StateGraph(ActivationState)
    sg.add_node("find_inactive", find_inactive)
    sg.add_node("enqueue_d3", enqueue_d3)
    sg.add_node("enqueue_d7", enqueue_d7)
    sg.add_node("report", report)
    sg.add_edge(START, "find_inactive")
    sg.add_edge("find_inactive", "enqueue_d3")
    sg.add_edge("enqueue_d3", "enqueue_d7")
    sg.add_edge("enqueue_d7", "report")
    sg.add_edge("report", END)
    return sg.compile()


GRAPH = _build()
