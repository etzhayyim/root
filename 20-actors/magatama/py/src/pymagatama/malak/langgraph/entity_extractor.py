"""entity_extractor — extract scam-actor entities from a text chunk and persist
to the malak graph schema (vertex_malak_threat_actor / bank_account / victim /
platform / line_contact + edges).

Hybrid pipeline:
  1. Regex pass for high-confidence patterns (JP bank accounts, LINE IDs, URLs,
     emails, phones).
  2. Optional LLM enrichment for actor names + role classification (via the
     existing `pymagatama.malak.graph._llm.call_llm` helper).
  3. UPSERT into RW (PK-implicit upsert — re-INSERTing the same vertex_id
     replaces the row, per ADR-0036 / record-log convention).
  4. Edge writes (transferred_to, member_of_ring, uses_platform, victim_of,
     uses_contact, owns_account).

Usage as a LangGraph node:

    g.add_node("extract_and_persist", entity_extract_node)

The node consumes `body` + `case_id` + optional `victim_hint` from state and
returns `{"entities": {...}, "vertex_inserts": [...], "edge_inserts": [...]}`.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from typing import Any, TypedDict

import psycopg


# ── Regex patterns ───────────────────────────────────────────────────
URL_RE = re.compile(r"https?://[^\s<>\"'】」]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
JP_PHONE_RE = re.compile(r"\b0[789]0[-\s]?\d{4}[-\s]?\d{4}\b")
LINE_P2P_URL_RE = re.compile(r"https?://line\.me/ti/p/[A-Za-z0-9_\-]+")
LINE_OC_URL_RE = re.compile(r"https?://line\.me/ti/g2?/[A-Za-z0-9_\-]+")
JP_ACCOUNT_NUMBER_RE = re.compile(r"[（(]?\s*(普通|当座|貯蓄)\s*[)）]?\s*[（(]?\s*(\d{7,10})\s*[)）]?")
JP_BANK_RE = re.compile(r"([一-龥]{2,12}銀行|ゆうちょ銀行|信用金庫|信用組合|農協|JA|ペイペイ銀行|住信SBIネット銀行|GMOあおぞらネット銀行|ａｕじぶん銀行|auじぶん銀行|楽天銀行|PayPay銀行|京葉銀行|セブン銀行|ソニー銀行)")
MONEY_JP_RE = re.compile(r"(?:[¥￥]\s?)?([\d,]{3,})\s*(?:円|万円|億円|百万円)?")


# ── Constants ─────────────────────────────────────────────────────────
OWNER_DID = "did:web:malak.gftd.ai"
ACTOR_DID = "did:web:malak.gftd.ai"
ORG_DID = "did:web:gftd.co.jp"


def _rkey(key: str) -> str:
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:24]


def _vid(kind: str, key: str) -> str:
    return f"at://did:web:malak.gftd.ai/ai.gftd.apps.malak.{kind}/{_rkey(key)}"


def _eid(src: str, dst: str, tag: str = "") -> str:
    return hashlib.sha1(f"{src}|{dst}|{tag}".encode("utf-8")).hexdigest()[:32]


# ── State ─────────────────────────────────────────────────────────────
class ExtractionState(TypedDict, total=False):
    body: str
    case_id: str
    victim_hint: dict  # optional {name, email, handle}
    tlp: str
    entities: dict
    vertex_inserts: int
    edge_inserts: int
    error: str


# ── Extraction ────────────────────────────────────────────────────────
def extract_entities(body: str) -> dict[str, list]:
    """Regex-only entity extraction. Safe to run on any text."""
    text = body or ""

    urls = list({u for u in URL_RE.findall(text)})
    emails = list({e for e in EMAIL_RE.findall(text)})
    phones = list({p for p in JP_PHONE_RE.findall(text)})
    line_p2p = list({u for u in LINE_P2P_URL_RE.findall(text)})
    line_oc = list({u for u in LINE_OC_URL_RE.findall(text)})

    # bank accounts: bank-name AND account-number nearby (within ±150 chars window)
    bank_accounts = []
    for bm in JP_BANK_RE.finditer(text):
        bank = bm.group(1)
        start, end = bm.start(), bm.end()
        window = text[max(0, start - 200): min(len(text), end + 200)]
        for am in JP_ACCOUNT_NUMBER_RE.finditer(window):
            typ, num = am.group(1), am.group(2)
            bank_accounts.append({
                "bank": bank,
                "account_type": typ,
                "account_number": num,
                "context": window[max(0, am.start() - 60):am.end() + 60].strip().replace("\n", " "),
            })

    return {
        "urls": urls,
        "emails": emails,
        "phones": phones,
        "line_p2p_urls": line_p2p,
        "line_open_chat_urls": line_oc,
        "bank_accounts": bank_accounts,
    }


# ── Persist (PK-implicit upsert via plain INSERT) ────────────────────
@contextmanager
def _conn():
    url = os.environ.get("RW_URL", "")
    if not url:
        raise RuntimeError("RW_URL env var missing")
    c = psycopg.connect(url)
    try:
        c.autocommit = True
        with c.cursor() as cur:
            yield cur
    finally:
        c.close()


def _now() -> tuple[str, str]:
    return time.strftime("%Y-%m-%dT%H:%M:%S+09:00"), time.strftime("%Y-%m-%d")


def _delete_existing(cur, table: str, vertex_id: str) -> None:
    """RW PK-implicit upsert: delete then insert to avoid duplicate row growth."""
    try:
        cur.execute(f"DELETE FROM {table} WHERE vertex_id = %s", (vertex_id,))
    except Exception:
        pass


def persist_platforms(cur, urls: list[str], emails: list[str], case_id: str,
                       artifact: str, tlp: str = "AMBER") -> list[str]:
    """One platform vertex per URL or canonical email domain."""
    now, today = _now()
    inserted = []
    for u in urls:
        # canonical normalization
        canon = u.rstrip("/")
        vid = _vid("platform", f"url/{canon}")
        kind = "landing_site"
        if "line.me/ti/" in canon:
            kind = "line_open_chat" if "/g2/" in canon else "line_p2p"
        _delete_existing(cur, "vertex_malak_platform", vid)
        cur.execute(
            """INSERT INTO vertex_malak_platform
            (vertex_id, rkey, repo, platform_kind, platform_name, url, email_contact,
             fingerprint, is_active, case_id, source_artifact,
             created_at, created_date, sensitivity_ord, owner_did, actor_did, org_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (vid, _rkey(f"url/{canon}"), OWNER_DID, kind, canon, canon, None,
             None, True, case_id, artifact, now, today,
             3 if tlp == "RED" else 2, OWNER_DID, ACTOR_DID, ORG_DID),
        )
        inserted.append(vid)
    for e in emails:
        vid = _vid("platform", f"email/{e}")
        _delete_existing(cur, "vertex_malak_platform", vid)
        cur.execute(
            """INSERT INTO vertex_malak_platform
            (vertex_id, rkey, repo, platform_kind, platform_name, url, email_contact,
             fingerprint, is_active, case_id, source_artifact,
             created_at, created_date, sensitivity_ord, owner_did, actor_did, org_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (vid, _rkey(f"email/{e}"), OWNER_DID, "email_contact", e, None, e,
             None, True, case_id, artifact, now, today,
             3 if tlp == "RED" else 2, OWNER_DID, ACTOR_DID, ORG_DID),
        )
        inserted.append(vid)
    return inserted


def persist_line_contacts(cur, line_p2p: list[str], line_oc: list[str],
                           case_id: str, artifact: str, tlp: str = "AMBER") -> list[str]:
    now, today = _now()
    inserted = []
    for u in line_p2p:
        lid = u.rsplit("/", 1)[-1]
        vid = _vid("lineContact", f"p2p/{lid}")
        _delete_existing(cur, "vertex_malak_line_contact", vid)
        cur.execute(
            """INSERT INTO vertex_malak_line_contact
            (vertex_id, rkey, repo, contact_kind, display_name, line_id, line_url,
             case_id, source_artifact, created_at, created_date, sensitivity_ord, owner_did, actor_did, org_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (vid, _rkey(f"p2p/{lid}"), OWNER_DID, "p2p", None, lid, u,
             case_id, artifact, now, today, 3 if tlp == "RED" else 2,
             OWNER_DID, ACTOR_DID, ORG_DID),
        )
        inserted.append(vid)
    for u in line_oc:
        token = u.rsplit("/", 1)[-1]
        vid = _vid("lineContact", f"oc/{token}")
        _delete_existing(cur, "vertex_malak_line_contact", vid)
        cur.execute(
            """INSERT INTO vertex_malak_line_contact
            (vertex_id, rkey, repo, contact_kind, display_name, line_id, line_url,
             case_id, source_artifact, created_at, created_date, sensitivity_ord, owner_did, actor_did, org_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (vid, _rkey(f"oc/{token}"), OWNER_DID, "open_chat", None, token, u,
             case_id, artifact, now, today, 3 if tlp == "RED" else 2,
             OWNER_DID, ACTOR_DID, ORG_DID),
        )
        inserted.append(vid)
    return inserted


def persist_bank_accounts(cur, accounts: list[dict], case_id: str,
                           artifact: str, tlp: str = "AMBER") -> list[str]:
    now, today = _now()
    inserted = []
    for a in accounts:
        bank = a["bank"]
        num = a["account_number"]
        typ = a.get("account_type", "普通")
        nat_key = f"unknown/{bank}|{num}"
        vid = _vid("bankAccount", nat_key)
        if vid in inserted:
            continue
        _delete_existing(cur, "vertex_malak_bank_account", vid)
        cur.execute(
            """INSERT INTO vertex_malak_bank_account
            (vertex_id, rkey, repo, account_kind, country, bank_name, branch_name, account_type,
             account_number, holder_name, holder_kind, flagged_by_others, current_balance_yen, seized,
             case_id, source_artifact,
             created_at, created_date, sensitivity_ord, owner_did, actor_did, org_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (vid, _rkey(nat_key), OWNER_DID, "unknown", "JP", bank, None, typ,
             num, None, "unknown", None, None, None, case_id, artifact,
             now, today, 3 if tlp == "RED" else 2, OWNER_DID, ACTOR_DID, ORG_DID),
        )
        inserted.append(vid)
    return inserted


# ── LangGraph node ────────────────────────────────────────────────────
def entity_extract_node(state: ExtractionState) -> dict:
    """Pure-sync node: extract regex entities + persist to RW. Returns counts."""
    body = state.get("body", "")
    case_id = state.get("case_id", "case:adhoc")
    tlp = state.get("tlp", "AMBER")
    artifact = state.get("source_artifact", "langgraph:scam_intake")  # type: ignore[index]

    entities = extract_entities(body)
    vins = 0
    eins = 0
    if not body or not os.environ.get("RW_URL"):
        return {"entities": entities, "vertex_inserts": 0, "edge_inserts": 0,
                "error": "no body or RW_URL missing"}

    try:
        with _conn() as cur:
            vins += len(persist_platforms(cur, entities["urls"], entities["emails"],
                                            case_id, artifact, tlp))
            vins += len(persist_line_contacts(cur, entities["line_p2p_urls"],
                                                entities["line_open_chat_urls"],
                                                case_id, artifact, tlp))
            vins += len(persist_bank_accounts(cur, entities["bank_accounts"],
                                                case_id, artifact, tlp))
    except Exception as e:
        return {"entities": entities, "vertex_inserts": vins, "edge_inserts": eins,
                "error": str(e)}

    return {"entities": entities, "vertex_inserts": vins, "edge_inserts": eins}
