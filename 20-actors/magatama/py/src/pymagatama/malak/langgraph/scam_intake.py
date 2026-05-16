"""scam_intake — mail / line / intel-feed 3-source ingestion chain.

Normalizes inbound scam-actor signal into Malak `ingestTrapMessage` shape,
then delegates to the existing PEGEL workflow (`run_langgraph_pipeline`).

Sources
-------
- `email`  : trap-inbox forwards (microsoft.gftd.ai sendDraft pipeline NOT usable
             for inbound — caller hands raw email envelope here)
- `sms`    : SMS trap forwarder
- `line`   : LINE Bot webhook events. `LINE_CHANNEL_ACCESS_TOKEN` required.
             API binding NOT wired in this skeleton (lexicon does not yet exist
             for LINE — extend `ingestTrapMessage` knownValues or add a sibling
             `ingestLineTrapMessage` before production).
- `intel`  : passive feed (AbuseIPDB / OpenCTI / VirusTotal). Caller pre-fetches
             and forwards normalized indicator dict.

Output state per invocation joins the original PEGEL result so callers can
chain into `record_tick` / Yoro social-post.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from pymagatama.malak.langgraph.workflow import run_langgraph_pipeline
from pymagatama.malak.langgraph.entity_extractor import (
    extract_entities,
    persist_platforms,
    persist_line_contacts,
    persist_bank_accounts,
    _conn as _entity_conn,
)


SUPPORTED_SOURCES = {"email", "sms", "line", "intel"}

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
WALLET_RE = re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b")


class IntakeState(TypedDict, total=False):
    source: str            # email | sms | line | intel
    raw: dict[str, Any]    # source-specific raw envelope
    normalized: dict[str, Any]
    indicators: dict[str, list[str]]
    pegel_result: dict[str, Any]
    extracted_entities: dict[str, Any]
    vertex_inserts: int
    persist_error: str
    error: str


def _hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()


def normalize_node(state: IntakeState) -> dict:
    """Map source-specific envelope → Malak trap-message shape."""
    source = state.get("source", "")
    raw = state.get("raw", {}) or {}

    if source not in SUPPORTED_SOURCES:
        return {"error": f"unsupported source: {source!r}"}

    if source == "email":
        body = str(raw.get("body") or raw.get("bodyPreview") or "")
        normalized = {
            "trapKind": "email",
            "recipient": str(raw.get("to") or raw.get("recipient") or ""),
            "provider": str(raw.get("provider") or "microsoft.gftd.ai"),
            "providerMessageId": str(raw.get("messageId") or raw.get("providerMessageId") or ""),
            "sender": str(raw.get("from") or raw.get("sender") or ""),
            "subject": str(raw.get("subject") or ""),
            "bodyPreview": body[:2000],
            "rawPayloadHash": _hash(body),
            "receivedAt": str(raw.get("receivedAt") or raw.get("date") or ""),
            "headersJson": str(raw.get("headersJson") or ""),
            "urls": list(URL_RE.findall(body))[:50],
            "tlp": str(raw.get("tlp") or "AMBER"),
        }
    elif source == "sms":
        body = str(raw.get("body") or raw.get("text") or "")
        normalized = {
            "trapKind": "sms",
            "recipient": str(raw.get("to") or ""),
            "provider": str(raw.get("provider") or "carrier"),
            "providerMessageId": str(raw.get("messageId") or ""),
            "sender": str(raw.get("from") or ""),
            "subject": "",
            "bodyPreview": body[:2000],
            "rawPayloadHash": _hash(body),
            "receivedAt": str(raw.get("receivedAt") or ""),
            "headersJson": "",
            "urls": list(URL_RE.findall(body))[:50],
            "tlp": str(raw.get("tlp") or "AMBER"),
        }
    elif source == "line":
        # LINE webhook event: { type:"message", source:{userId,...}, message:{type,text} }
        msg = raw.get("message") or {}
        body = str(msg.get("text") or "")
        line_source = raw.get("source") or {}
        normalized = {
            # Reuse `trapKind=email` until lexicon adds `line`. Caller can downstream-filter on provider="line".
            "trapKind": "email",
            "recipient": str(raw.get("destination") or "line:bot"),
            "provider": "line",
            "providerMessageId": str(msg.get("id") or raw.get("webhookEventId") or ""),
            "sender": str(line_source.get("userId") or line_source.get("groupId") or ""),
            "subject": "",
            "bodyPreview": body[:2000],
            "rawPayloadHash": _hash(body),
            "receivedAt": str(raw.get("timestamp") or ""),
            "headersJson": "",
            "urls": list(URL_RE.findall(body))[:50],
            "tlp": str(raw.get("tlp") or "AMBER"),
        }
    else:  # intel
        # External feed indicator: { actor, ttp, ip, domain, wallet, narrative, source_url }
        narrative = str(raw.get("narrative") or raw.get("description") or "")
        normalized = {
            "trapKind": "email",
            "recipient": "intel:feed",
            "provider": str(raw.get("feedProvider") or "intel"),
            "providerMessageId": str(raw.get("indicatorId") or ""),
            "sender": str(raw.get("actor") or ""),
            "subject": str(raw.get("ttp") or ""),
            "bodyPreview": narrative[:2000],
            "rawPayloadHash": _hash(narrative),
            "receivedAt": str(raw.get("observedAt") or ""),
            "headersJson": "",
            "urls": [str(raw.get("source_url"))] if raw.get("source_url") else [],
            "tlp": str(raw.get("tlp") or "AMBER"),
        }

    return {"normalized": normalized}


def extract_indicators_node(state: IntakeState) -> dict:
    """Pull IP / URL / wallet / domain out of body for downstream graph linkage."""
    n = state.get("normalized") or {}
    body = " ".join(str(n.get(k, "")) for k in ("subject", "bodyPreview", "sender"))
    return {
        "indicators": {
            "ips": list({ip for ip in IP_RE.findall(body)})[:20],
            "urls": list({u for u in URL_RE.findall(body)})[:20],
            "wallets": list({w for w in WALLET_RE.findall(body)})[:20],
        }
    }


async def entity_persist_node(state: IntakeState) -> dict:
    """Persist extracted entities into the malak graph schema (vertex_*).

    Only runs if RW_URL is set. Failure is non-fatal — chain still produces a
    PEGEL tick even if RW is unreachable.
    """
    import os
    if not os.environ.get("RW_URL"):
        return {"vertex_inserts": 0, "persist_error": "RW_URL not set"}
    n = state.get("normalized") or {}
    body = " ".join(filter(None, [
        n.get("subject", ""), n.get("bodyPreview", ""), n.get("sender", ""),
    ]))
    if not body.strip():
        return {"vertex_inserts": 0}
    case_id = f"case:scam_intake:{n.get('provider', 'unknown')}:{n.get('providerMessageId', '') or n.get('rawPayloadHash', '')}"
    tlp = n.get("tlp", "AMBER")
    artifact = f"scam_intake:{n.get('provider', 'unknown')}"
    ents = extract_entities(body)
    inserted = 0
    try:
        with _entity_conn() as cur:
            inserted += len(persist_platforms(cur, ents["urls"], ents["emails"], case_id, artifact, tlp))
            inserted += len(persist_line_contacts(cur, ents["line_p2p_urls"], ents["line_open_chat_urls"], case_id, artifact, tlp))
            inserted += len(persist_bank_accounts(cur, ents["bank_accounts"], case_id, artifact, tlp))
    except Exception as e:  # noqa: BLE001
        return {"vertex_inserts": inserted, "persist_error": str(e)}
    return {"vertex_inserts": inserted, "extracted_entities": ents}


async def pegel_relay_node(state: IntakeState) -> dict:
    """Hand the normalized envelope to the existing Malak PEGEL workflow."""
    n = state.get("normalized") or {}
    indicators = state.get("indicators") or {}

    detail_lines = [
        f"Sender: {n.get('sender','')}",
        f"Recipient: {n.get('recipient','')}",
        f"Subject: {n.get('subject','')}",
        f"Provider: {n.get('provider','')}",
        f"IPs: {','.join(indicators.get('ips', []))}",
        f"URLs: {','.join(indicators.get('urls', []))}",
        f"Wallets: {','.join(indicators.get('wallets', []))}",
        "---",
        n.get("bodyPreview", ""),
    ]
    details = "\n".join(detail_lines)

    pegel = await run_langgraph_pipeline(
        role_id="malak",
        params={
            "tlp": n.get("tlp", "AMBER"),
            "action": "ingest_scam_message",
            "details": details,
        },
    )
    return {"pegel_result": pegel}


def build_scam_intake_graph() -> StateGraph:
    g = StateGraph(IntakeState)
    g.add_node("normalize", normalize_node)
    g.add_node("extract_indicators", extract_indicators_node)
    g.add_node("pegel_relay", pegel_relay_node)
    g.add_node("entity_persist", entity_persist_node)
    g.set_entry_point("normalize")
    g.add_edge("normalize", "extract_indicators")
    g.add_edge("extract_indicators", "pegel_relay")
    g.add_edge("pegel_relay", "entity_persist")
    g.add_edge("entity_persist", END)
    return g.compile()


async def run_scam_intake(source: str, raw: dict[str, Any]) -> dict:
    """Public entrypoint. `source` ∈ {email, sms, line, intel}."""
    graph = build_scam_intake_graph()
    initial: IntakeState = {"source": source, "raw": raw}
    return await graph.ainvoke(initial)
