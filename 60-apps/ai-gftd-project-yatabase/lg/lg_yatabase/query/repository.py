"""Deploy-first query repository — writes to vertex_yata_deployed_query."""
from __future__ import annotations

import time
from typing import Any

from lg_yatabase.bmc.db import execute, fetch, fetchrow

_TABLE = "graphar.vertex_yata_deployed_query"


def _vertex_id(org_did: str, query_id: str) -> str:
    return f"yata:dq:{org_did}:{query_id}"


async def get_deployed_query(org_did: str, query_id: str) -> dict[str, Any] | None:
    return await fetchrow(
        f"SELECT * FROM {_TABLE} WHERE org_did = $1 AND query_id = $2 LIMIT 1",
        org_did, query_id,
    )


async def insert_deployed_query(
    *,
    org_did: str,
    actor_did: str,
    query_id: str,
    mv_name: str,
    steps_json: str,
    select_json: str | None,
    index_on_json: str | None,
    static_where_json: str | None,
    translated_ddl: str,
) -> None:
    vid = _vertex_id(org_did, query_id)
    now = int(time.time() * 1000)
    await execute(
        f"""
        INSERT INTO {_TABLE} (
            vertex_id, org_did, actor_did, query_id, mv_name,
            steps_json, select_json, index_on_json, static_where_json,
            translated_ddl, status, created_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'ready',$11)
        """,
        vid, org_did, actor_did, query_id, mv_name,
        steps_json, select_json, index_on_json, static_where_json,
        translated_ddl, now,
    )


async def delete_deployed_query(org_did: str, query_id: str) -> None:
    vid = _vertex_id(org_did, query_id)
    await execute(
        f"DELETE FROM {_TABLE} WHERE vertex_id = $1",
        vid,
    )


async def count_deployed_queries(org_did: str) -> int:
    row = await fetchrow(
        f"SELECT COUNT(*) AS n FROM {_TABLE} WHERE org_did = $1",
        org_did,
    )
    return int(row["n"]) if row else 0


async def list_deployed_queries(
    org_did: str, limit: int = 50, cursor: str | None = None
) -> list[dict[str, Any]]:
    if cursor:
        rows = await fetch(
            f"""
            SELECT query_id, mv_name, status, steps_json, created_at
            FROM {_TABLE}
            WHERE org_did = $1 AND created_at < $2
            ORDER BY created_at DESC
            LIMIT $3
            """,
            org_did, int(cursor), limit,
        )
    else:
        rows = await fetch(
            f"""
            SELECT query_id, mv_name, status, steps_json, created_at
            FROM {_TABLE}
            WHERE org_did = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            org_did, limit,
        )
    return [dict(r) for r in rows]
