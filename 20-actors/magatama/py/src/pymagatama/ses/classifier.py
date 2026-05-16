"""SES案件 classifier — Phase 2 (ADR-2605120000).

Determines whether parsed text represents a new 案件, an update to an
existing one, or should be discarded.  Uses a two-step approach:

1. SQL lookup — fetch active anken for this actor_did by client_name
   similarity (prefix match; ILIKE is unsupported in RisingWave so we
   normalise both sides and compare with ``=`` or ``LIKE 'prefix%'``).
2. LLM tiebreak — when a candidate anken is found, ask the LLM to
   decide "new" vs "existing" based on context.
"""

from __future__ import annotations

from typing import Any, Optional

from pymagatama.db_sync import sync_cursor
from pymagatama.llm import call_tier_json

_CLASSIFY_SYSTEM = """\
あなたはSES案件管理AIです。
以下のメール本文と既存案件情報を比較し、JSON形式のみで返してください。

{
  "decision": "new|existing|discard",
  "existing_anken_id": "既存案件のvertex_idまたはnull",
  "rationale": "理由100文字以内"
}

decision:
  "new"      → 新規案件
  "existing" → 既存案件の続報（existing_anken_idを必ず指定）
  "discard"  → SES案件ではない/無関係
"""


def _normalize(s: str) -> str:
    """Minimal normalization: lower + strip spaces."""
    return s.lower().replace("　", " ").replace("（株）", "").replace("(株)", "").strip()


def _fetch_active_anken(actor_did: str, client_name: str) -> list[dict[str, Any]]:
    """Fetch active anken rows for this actor_did with matching client_name prefix."""
    norm = _normalize(client_name)
    if not norm:
        return []

    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT a.vertex_id, a.client_name, a.client_company,
                   a.start_month, lj.jokyo AS current_jokyo
            FROM vertex_ses_anken a
            LEFT JOIN mv_ses_anken_latest_jokyo lj
                ON lj.anken_vertex_id = a.vertex_id
            WHERE a.actor_did = %s
              AND a.client_name LIKE %s
            LIMIT 10
            """,
            (actor_did, norm[:20] + "%"),
        )
        rows = cur.fetchall() or []

    return [
        {
            "vertex_id": r[0],
            "client_name": r[1],
            "client_company": r[2],
            "start_month": r[3],
            "current_jokyo": r[4],
        }
        for r in rows
    ]


def _llm_classify(
    parsed_text: str,
    candidates: list[dict[str, Any]],
) -> tuple[str, Optional[str], Optional[str]]:
    """Returns (decision, existing_anken_id, existing_jokyo_current)."""
    cand_text = "\n".join(
        f"- vertex_id={c['vertex_id']}, client={c['client_name']}, "
        f"company={c['client_company']}, start={c['start_month']}, "
        f"jokyo={c['current_jokyo']}"
        for c in candidates
    )
    user = f"## 既存案件候補\n{cand_text}\n\n## メール本文\n{parsed_text[:2000]}"

    resp = call_tier_json(
        "ses-extraction",
        system=_CLASSIFY_SYSTEM,
        user=user,
        max_tokens=256,
        temperature=0.1,
    )
    if not resp.get("ok"):
        return "new", None, None

    data = resp.get("data") or {}
    decision = data.get("decision", "new")
    if decision not in ("new", "existing", "discard"):
        decision = "new"

    existing_id: Optional[str] = data.get("existing_anken_id")
    existing_jokyo: Optional[str] = None
    if existing_id:
        for c in candidates:
            if c["vertex_id"] == existing_id:
                existing_jokyo = c.get("current_jokyo")
                break

    return decision, existing_id, existing_jokyo


def classify_anken(
    actor_did: str,
    client_name: str,
    parsed_text: str,
) -> tuple[str, Optional[str], Optional[str]]:
    """Classify this inbound text.

    Returns:
        (decision, existing_anken_id, existing_jokyo_current)
        decision ∈ {"new", "existing", "discard"}
    """
    candidates = _fetch_active_anken(actor_did, client_name)

    if not candidates:
        return "new", None, None

    return _llm_classify(parsed_text, candidates)
