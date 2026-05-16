"""SES persistence layer — Phase 2 (ADR-2605120000).

All INSERTs use content-addressed PKs (sha256).  No ON CONFLICT — record-log
semantics (ADR-0041).  Duplicate run_id / vertex_id rows are idempotent
because the sha256 key will collide and psycopg3 will raise IntegrityError,
which the caller can catch and treat as a no-op.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date
from typing import Optional

from pymagatama.db_sync import sync_cursor
from pymagatama.ses.state import AnkenExtraction


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _today() -> date:
    return date.today()


def _anken_vid(actor_did: str, client_name: str, start_month: Optional[str]) -> str:
    key = f"{actor_did}|{client_name}|{start_month or ''}"
    return f"at://{actor_did}/ai.gftd.apps.ses.anken/{_sha(key)}"


def _jokyo_vid(anken_vid: str, jokyo: str, ts_ms: int) -> str:
    key = f"{anken_vid}|{jokyo}|{ts_ms}"
    return f"at://{anken_vid.split('/')[2]}/ai.gftd.apps.ses.jokyo/{_sha(key)}"


def _client_vid(actor_did: str, company_normalized: str) -> str:
    key = f"{actor_did}|{company_normalized}"
    return f"at://{actor_did}/ai.gftd.apps.ses.client/{_sha(key)}"


def _engineer_vid(actor_did: str, name_normalized: str) -> str:
    key = f"{actor_did}|{name_normalized}"
    return f"at://{actor_did}/ai.gftd.apps.ses.engineer/{_sha(key)}"


def insert_anken(
    actor_did: str,
    org_did: str,
    extraction: AnkenExtraction,
    *,
    source_kind: str = "email",
) -> str:
    """INSERT vertex_ses_anken. Returns vertex_id."""
    vid = _anken_vid(actor_did, extraction.client_name, extraction.start_month)
    now = _now_iso()
    today = _today()

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_ses_anken (
                vertex_id, _seq, created_date, sensitivity_ord,
                owner_did, actor_did, org_did, at_did,
                client_name, client_company, skill_reqs_json,
                start_month, end_month,
                rate_lower_yen, rate_upper_yen,
                work_location, remote_ok, engineer_name, notes,
                source_kind, created_at
            ) VALUES (
                %s, 0, %s, 2,
                %s, %s, %s, NULL,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            """,
            (
                vid, today,
                actor_did, actor_did, org_did,
                extraction.client_name,
                extraction.client_company,
                json.dumps(extraction.skill_requirements, ensure_ascii=False),
                extraction.start_month,
                extraction.end_month,
                extraction.rate_lower_yen,
                extraction.rate_upper_yen,
                extraction.work_location,
                extraction.remote_ok,
                extraction.engineer_name,
                extraction.notes,
                source_kind,
                now,
            ),
        )
    return vid


def insert_jokyo(
    actor_did: str,
    org_did: str,
    anken_vertex_id: str,
    jokyo: str,
    run_id: str,
    rationale: str,
) -> str:
    """INSERT vertex_ses_jokyo (append-only). Returns vertex_id."""
    ts_ms = int(time.time() * 1000)
    vid = _jokyo_vid(anken_vertex_id, jokyo, ts_ms)
    now = _now_iso()
    today = _today()

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_ses_jokyo (
                vertex_id, _seq, created_date, sensitivity_ord,
                owner_did, actor_did, org_did, at_did,
                anken_vertex_id, jokyo, rationale, run_id, created_at
            ) VALUES (
                %s, 0, %s, 2,
                %s, %s, %s, NULL,
                %s, %s, %s, %s, %s
            )
            """,
            (
                vid, today,
                actor_did, actor_did, org_did,
                anken_vertex_id, jokyo, rationale, run_id, now,
            ),
        )
    return vid


def upsert_client(
    actor_did: str,
    org_did: str,
    client_company: str,
) -> str:
    """INSERT vertex_ses_client if not present. Returns vertex_id."""
    normalized = client_company.lower().strip()
    vid = _client_vid(actor_did, normalized)
    now = _now_iso()
    today = _today()

    with sync_cursor() as cur:
        # Check existence first (no ON CONFLICT in RW)
        cur.execute(
            "SELECT 1 FROM vertex_ses_client WHERE vertex_id = %s LIMIT 1",
            (vid,),
        )
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO vertex_ses_client (
                    vertex_id, _seq, created_date, sensitivity_ord,
                    owner_did, actor_did, org_did, at_did,
                    client_company, company_normalized, first_seen_at, created_at
                ) VALUES (
                    %s, 0, %s, 2,
                    %s, %s, %s, NULL,
                    %s, %s, %s, %s
                )
                """,
                (vid, today, actor_did, actor_did, org_did,
                 client_company, normalized, now, now),
            )
    return vid


def upsert_engineer(
    actor_did: str,
    org_did: str,
    engineer_name: str,
) -> str:
    """INSERT vertex_ses_engineer if not present. Returns vertex_id."""
    normalized = engineer_name.lower().strip()
    vid = _engineer_vid(actor_did, normalized)
    now = _now_iso()
    today = _today()

    with sync_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM vertex_ses_engineer WHERE vertex_id = %s LIMIT 1",
            (vid,),
        )
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO vertex_ses_engineer (
                    vertex_id, _seq, created_date, sensitivity_ord,
                    owner_did, actor_did, org_did, at_did,
                    engineer_name, name_normalized, first_seen_at, created_at
                ) VALUES (
                    %s, 0, %s, 2,
                    %s, %s, %s, NULL,
                    %s, %s, %s, %s
                )
                """,
                (vid, today, actor_did, actor_did, org_did,
                 engineer_name, normalized, now, now),
            )
    return vid


def insert_run(
    actor_did: str,
    org_did: str,
    run_id: str,
    *,
    source_kind: str,
    anken_decision: Optional[str],
    anken_vertex_id: Optional[str],
    jokyo_vertex_id: Optional[str],
    jokyo_appended: bool,
    jokyo_skipped: bool,
    status: str,
    error_text: Optional[str],
    model_ids: list[str],
    tokens_total: int,
    started_at: str,
) -> str:
    """INSERT vertex_ses_run. Returns vertex_id (= run_id)."""
    vid = f"at://{actor_did}/ai.gftd.apps.ses.run/{run_id}"
    now = _now_iso()
    today = _today()

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_ses_run (
                vertex_id, _seq, created_date, sensitivity_ord,
                owner_did, actor_did, org_did, at_did,
                run_id, source_kind, anken_decision,
                anken_vertex_id, jokyo_vertex_id,
                jokyo_appended, jokyo_skipped,
                status, error_text, model_ids_json, tokens_total,
                started_at, finished_at, created_at
            ) VALUES (
                %s, 0, %s, 2,
                %s, %s, %s, NULL,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
            """,
            (
                vid, today,
                actor_did, actor_did, org_did,
                run_id, source_kind, anken_decision,
                anken_vertex_id, jokyo_vertex_id,
                jokyo_appended, jokyo_skipped,
                status, error_text,
                json.dumps(model_ids, ensure_ascii=False),
                tokens_total,
                started_at, now, now,
            ),
        )
    return vid


def insert_edge_anken_client(
    actor_did: str,
    org_did: str,
    anken_vid: str,
    client_vid: str,
) -> None:
    """INSERT edge_ses_anken_client."""
    edge_id = f"at://{actor_did}/ai.gftd.apps.ses.ankenClient/{_sha(anken_vid + '|' + client_vid)}"
    now = _now_iso()
    today = _today()
    with sync_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM edge_ses_anken_client WHERE edge_id = %s LIMIT 1",
            (edge_id,),
        )
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO edge_ses_anken_client (
                    edge_id, src_vid, dst_vid, _seq, created_date,
                    sensitivity_ord, owner_did, actor_did, org_did, created_at
                ) VALUES (%s, %s, %s, 0, %s, 2, %s, %s, %s, %s)
                """,
                (edge_id, anken_vid, client_vid, today,
                 actor_did, actor_did, org_did, now),
            )


def insert_edge_anken_engineer(
    actor_did: str,
    org_did: str,
    anken_vid: str,
    engineer_vid: str,
    confidence: float | None = None,
) -> None:
    """INSERT edge_ses_anken_engineer (Phase B: confidence = extraction confidence)."""
    edge_id = f"at://{actor_did}/ai.gftd.apps.ses.ankenEngineer/{_sha(anken_vid + '|' + engineer_vid)}"
    now = _now_iso()
    today = _today()
    with sync_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM edge_ses_anken_engineer WHERE edge_id = %s LIMIT 1",
            (edge_id,),
        )
        if not cur.fetchone():
            cur.execute(
                """
                INSERT INTO edge_ses_anken_engineer (
                    edge_id, src_vid, dst_vid, _seq, created_date,
                    sensitivity_ord, owner_did, actor_did, org_did, created_at,
                    confidence
                ) VALUES (%s, %s, %s, 0, %s, 2, %s, %s, %s, %s, %s)
                """,
                (edge_id, anken_vid, engineer_vid, today,
                 actor_did, actor_did, org_did, now, confidence),
            )
