"""Arbitrage signal business logic for Zeebe workers.

This module owns the logic formerly implemented in the ``arb.etzhayyim.com``
Cloudflare Worker. The Worker is now an edge facade that forwards XRPC to the
BPMN dispatcher.
"""

from __future__ import annotations

import json
import math
import os
import random
import string
import time
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:arb.etzhayyim.com"
DISCLAIMER = "Educational signal. Not advice. No execution."
ASSET_CLASSES = {"eq", "fut", "fx", "com", "re", "cr"}
STOOQ_SYMBOLS: dict[str, list[str]] = {
    "eq": ["spy.us", "qqq.us", "dia.us", "iwm.us", "efa.us", "eem.us", "vgk.us", "ewj.us", "fxi.us", "vti.us"],
    "fut": ["gc.f", "si.f", "cl.f", "ng.f", "zw.f", "zc.f"],
    "com": ["gld.us", "slv.us", "uso.us", "ung.us", "weat.us", "corn.us", "soyb.us"],
    "re": ["vnq.us", "iyr.us", "xlre.us", "reet.us", "usrt.us"],
}
BINANCE_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT", "AVAXUSDT", "MATICUSDT"]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _float(value: Any, default: float = math.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def _gen_id(prefix: str) -> str:
    ticks = base36(int(time.time() * 1000))
    suffix = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{prefix}{ticks}{suffix}"[:14]


def base36(n: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = ""
    while n:
        n, rem = divmod(n, 36)
        out = chars[rem] + out
    return out


def quote_vid(owner_did: str, venue: str, symbol: str, ts: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in f"{venue}-{symbol}-{ts}")
    return f"at://{owner_did}/com.etzhayyim.apps.arb.quote/{safe}"


def proposal_vid(owner_did: str, proposal_id: str) -> str:
    return f"at://{owner_did}/com.etzhayyim.apps.arb.proposal/{proposal_id}"


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall() or [])


def _fetch_one(sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...] | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _http_json(url: str, timeout: int = 10) -> Any:
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "etzhayyim-arb-zeebe/1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_text(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"accept": "text/csv,*/*", "user-agent": "etzhayyim-arb-zeebe/1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def ingest_quote(args: dict[str, Any]) -> dict[str, Any]:
    asset_class = _str(args.get("assetClass"))
    venue = _str(args.get("venue"))
    symbol = _str(args.get("symbol"))
    ts = _str(args.get("ts"))
    mid = _float(args.get("mid"))
    if asset_class not in ASSET_CLASSES or not venue or not symbol or not ts or not math.isfinite(mid):
        return {"ok": False, "error": "InvalidRequest", "message": "assetClass/venue/symbol/ts/mid required"}

    owner = f"{_str(args.get('primaryDid') or OWNER_DID)}:scout"
    vid = quote_vid(owner, venue, symbol, ts)
    created_at = now_iso()
    _execute(
        """
        INSERT INTO vertex_arb_quote
          (vertex_id, created_date, sensitivity_ord, owner_did, asset_class, venue, symbol,
           ts, bid, ask, mid, currency, src_url, created_at, org_id, user_id, actor_id)
        SELECT %s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'sys.arb.scout'
        WHERE NOT EXISTS (SELECT 1 FROM vertex_arb_quote WHERE vertex_id = %s)
        """,
        (
            vid,
            created_at[:10],
            owner,
            asset_class,
            venue,
            symbol,
            ts,
            None if not math.isfinite(_float(args.get("bid"))) else _float(args.get("bid")),
            None if not math.isfinite(_float(args.get("ask"))) else _float(args.get("ask")),
            mid,
            _str(args.get("currency")),
            _str(args.get("srcUrl")),
            created_at,
            _str(args.get("orgId") or "anon"),
            _str(args.get("userId") or "anon"),
            vid,
        ),
    )
    return {"ok": True, "vertexId": vid, "ts": ts}


def detect_spread(asset_class: str, min_spread_bps: float = 20) -> dict[str, Any]:
    if asset_class not in ASSET_CLASSES:
        return {"ok": False, "error": "InvalidAssetClass"}
    rows = _fetch_all(
        """
        SELECT venue, symbol, mid, ts, currency
        FROM vertex_arb_quote
        WHERE asset_class = %s
        ORDER BY ts DESC
        LIMIT 2000
        """,
        (asset_class,),
    )
    latest: dict[str, tuple[Any, ...]] = {}
    for row in rows:
        key = f"{row[0]}:{row[1]}"
        latest.setdefault(key, row)

    by_symbol: dict[str, list[tuple[Any, ...]]] = {}
    for row in latest.values():
        by_symbol.setdefault(str(row[1]), []).append(row)

    candidates: list[dict[str, Any]] = []
    for items in by_symbol.values():
        for i, a in enumerate(items):
            for b in items[i + 1 :]:
                ma = _float(a[2])
                mb = _float(b[2])
                if not math.isfinite(ma) or not math.isfinite(mb) or ma <= 0 or mb <= 0:
                    continue
                bps = round(((mb - ma) / ma) * 10_000)
                if abs(bps) < min_spread_bps:
                    continue
                long_leg = f"{a[0]}:{a[1]}" if bps > 0 else f"{b[0]}:{b[1]}"
                short_leg = f"{b[0]}:{b[1]}" if bps > 0 else f"{a[0]}:{a[1]}"
                candidates.append(
                    {
                        "legA": long_leg,
                        "legB": short_leg,
                        "spreadBps": abs(bps),
                        "edgeBps": max(0, abs(bps) - 10),
                        "rationale": f"same-symbol cross-venue mid spread ({a[3]}/{b[3]})",
                    }
                )
    candidates.sort(key=lambda c: c["edgeBps"], reverse=True)
    return {"ok": True, "candidates": candidates[:50]}


def propose_trade(args: dict[str, Any]) -> dict[str, Any]:
    asset_class = _str(args.get("assetClass"))
    leg_a = _str(args.get("legA"))
    leg_b = _str(args.get("legB"))
    spread_bps = round(_float(args.get("spreadBps"), 0))
    edge_bps = round(_float(args.get("edgeBps"), 0))
    if asset_class not in ASSET_CLASSES or not leg_a or not leg_b or spread_bps <= 0:
        return {"ok": False, "error": "InvalidRequest", "message": "assetClass/legA/legB/spreadBps required"}
    primary = _str(args.get("primaryDid") or OWNER_DID)
    owner = f"{primary}:{asset_class}"
    proposal_id = _gen_id("p")
    vid = proposal_vid(owner, proposal_id)
    created_at = now_iso()
    expires_at = _str(args.get("expiresAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 1800)))
    org_id = _str(args.get("orgId") or "anon")
    user_id = _str(args.get("userId") or "anon")
    actor_id = f"sys.arb.{asset_class}"

    _execute(
        """
        INSERT INTO vertex_arb_proposal
          (vertex_id, created_date, sensitivity_ord, owner_did, proposal_id, asset_class,
           leg_a, leg_b, spread_bps, edge_bps, confidence, rationale, expires_at, executed,
           created_at, org_id, user_id, actor_id)
        VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false, %s, %s, %s, %s)
        """,
        (
            vid,
            created_at[:10],
            owner,
            proposal_id,
            asset_class,
            leg_a,
            leg_b,
            spread_bps,
            edge_bps,
            max(0, min(1, _float(args.get("confidence"), 0.5))),
            _str(args.get("rationale")),
            expires_at,
            created_at,
            org_id,
            user_id,
            actor_id,
        ),
    )
    for side, leg in (("long", leg_a), ("short", leg_b)):
        edge_id = f"edge:{proposal_id}:{side}"
        _execute(
            """
            INSERT INTO edge_arb_proposal_leg
              (edge_id, created_date, sensitivity_ord, owner_did, src_vid, dst_vid, side,
               created_at, org_id, user_id, actor_id)
            VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (edge_id, created_at[:10], owner, vid, leg, side, created_at, org_id, user_id, actor_id),
        )
    return {"ok": True, "proposalId": proposal_id, "uri": vid, "disclaimer": _str(args.get("disclaimer") or DISCLAIMER)}


def score_proposal(proposal_id: str, model: str = "heuristic-v1") -> dict[str, Any]:
    if not proposal_id:
        return {"ok": False, "error": "InvalidRequest", "message": "proposalId required"}
    row = _fetch_one(
        """
        SELECT edge_bps, spread_bps, confidence
        FROM vertex_arb_proposal
        WHERE proposal_id = %s
        LIMIT 1
        """,
        (proposal_id,),
    )
    if row is None:
        return {"ok": False, "error": "NotFound", "message": proposal_id}
    edge_factor = max(0, min(1, _float(row[0], 0) / 200))
    spread_factor = max(0, min(1, _float(row[1], 0) / 300))
    conf_factor = _float(row[2], 0.5)
    score = round(0.5 * edge_factor + 0.3 * spread_factor + 0.2 * conf_factor, 4)
    risk_notes = (
        "low edge or low confidence; treat as noise"
        if score < 0.4
        else "moderate edge; verify frictions before sharing"
        if score < 0.7
        else "strong cross-venue dislocation; check borrow / FX leg / venue halt"
    )
    owner = f"{OWNER_DID}:judge"
    vid = f"at://{owner}/com.etzhayyim.apps.arb.score/{proposal_id}"
    created_at = now_iso()
    _execute("DELETE FROM vertex_arb_score WHERE vertex_id = %s", (vid,))
    _execute(
        """
        INSERT INTO vertex_arb_score
          (vertex_id, created_date, sensitivity_ord, owner_did, proposal_id, score,
           risk_notes, llm_model, created_at, org_id, user_id, actor_id)
        VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, 'anon', 'anon', 'sys.arb.judge')
        """,
        (vid, created_at[:10], owner, proposal_id, score, risk_notes, model, created_at),
    )
    return {"ok": True, "score": score, "riskNotes": risk_notes, "model": model}


def publish_proposal(proposal_id: str, mention_cohort: str = "trader.etzhayyim.com", disclaimer: str = DISCLAIMER) -> dict[str, Any]:
    if not proposal_id:
        return {"ok": False, "error": "InvalidRequest", "message": "proposalId required"}
    row = _fetch_one(
        """
        SELECT p.asset_class, p.leg_a, p.leg_b, p.spread_bps, p.edge_bps, s.score
        FROM vertex_arb_proposal p
        LEFT JOIN vertex_arb_score s ON s.proposal_id = p.proposal_id
        WHERE p.proposal_id = %s
        LIMIT 1
        """,
        (proposal_id,),
    )
    if row is None:
        return {"ok": False, "error": "NotFound", "message": proposal_id}
    if row[5] is None or _float(row[5], 0) < 0.5:
        return {"ok": False, "error": "BelowThreshold", "message": "score < 0.5; skip publication"}
    text = "\n".join(
        [
            f"Arb signal [{row[0]}] long {row[1]} / short {row[2]}",
            f"spread {row[3]}bps | edge {row[4]}bps | score {row[5]}",
            f"@{mention_cohort} - {disclaimer}",
        ]
    )
    post_uri = _pds_post(text)
    owner = f"{OWNER_DID}:herald"
    vid = f"at://{owner}/com.etzhayyim.apps.arb.publication/{proposal_id}"
    created_at = now_iso()
    _execute("DELETE FROM vertex_arb_publication WHERE vertex_id = %s", (vid,))
    _execute(
        """
        INSERT INTO vertex_arb_publication
          (vertex_id, created_date, sensitivity_ord, owner_did, proposal_id, post_uri,
           mentions, disclaimer, created_at, org_id, user_id, actor_id)
        VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, 'anon', 'anon', 'sys.arb.herald')
        """,
        (vid, created_at[:10], owner, proposal_id, post_uri, mention_cohort, disclaimer, created_at),
    )
    return {"ok": True, "postUri": post_uri, "mentions": [mention_cohort]}


def _pds_post(text: str) -> str:
    from pymagatama.primitives.yoro_social import build_repo_record, insert_social_post_record

    record = {"$type": "app.bsky.feed.post", "text": text, "createdAt": now_iso()}
    row = build_repo_record(repo=f"{OWNER_DID}:herald", collection="app.bsky.feed.post", record=record)
    try:
        result = insert_social_post_record(row, flush=False)
        return _str(result.get("uri") or "")
    except Exception as e:  # noqa: BLE001
        return f"error:pds:{e}"


def scout_quotes(asset_class: str) -> dict[str, Any]:
    if asset_class not in ASSET_CLASSES:
        return {"ok": False, "error": "InvalidAssetClass"}
    owner = f"{OWNER_DID}:scout"
    ts = now_iso()
    count = 0
    if asset_class == "cr":
        pair_set = set(BINANCE_PAIRS)
        spot_params = urllib.parse.urlencode({"symbols": json.dumps(BINANCE_PAIRS)})
        spot = _http_json(f"https://api.binance.com/api/v3/ticker/price?{spot_params}", 10)
        fut = _http_json("https://fapi.binance.com/fapi/v1/ticker/price", 10)
        for venue, items in (("binance-spot", spot), ("binance-fut", [d for d in fut if d.get("symbol") in pair_set])):
            for item in items:
                mid = _float(item.get("price"))
                if not math.isfinite(mid) or mid <= 0:
                    continue
                ingest_quote({"assetClass": "cr", "venue": venue, "symbol": item["symbol"].replace("USDT", "").lower(), "ts": ts, "mid": mid, "currency": "USD", "srcUrl": "https://api.binance.com" if venue == "binance-spot" else "https://fapi.binance.com", "primaryDid": OWNER_DID})
                count += 1
        return {"ok": True, "count": count, "assetClass": asset_class, "source": "binance-spot+fut", "ts": ts}
    if asset_class == "fx":
        data = _http_json("https://api.frankfurter.app/latest?base=USD", 10)
        rate_ts = f"{data.get('date') or ts[:10]}T00:00:00Z"
        for currency, rate in (data.get("rates") or {}).items():
            rate_f = _float(rate)
            if not math.isfinite(rate_f) or rate_f <= 0:
                continue
            ingest_quote({"assetClass": "fx", "venue": "frankfurter", "symbol": f"USD{currency}", "ts": rate_ts, "mid": 1 / rate_f, "currency": currency, "srcUrl": "https://api.frankfurter.app", "primaryDid": OWNER_DID})
            count += 1
        return {"ok": True, "count": count, "assetClass": asset_class, "source": "frankfurter", "ts": ts}
    for symbol in STOOQ_SYMBOLS.get(asset_class, []):
        try:
            csv = _http_text(f"https://stooq.com/q/l/?s={urllib.parse.quote(symbol)}&f=sd2t2ohlcv&h&e=csv", 10)
            parts = (csv.strip().splitlines()[1] if len(csv.strip().splitlines()) > 1 else "").split(",")
            close = _float(parts[6] if len(parts) > 6 else None)
            if not math.isfinite(close) or close <= 0:
                continue
            date = parts[1] if len(parts) > 1 else ""
            clock = parts[2] if len(parts) > 2 else "00:00:00"
            row_ts = f"{date}T{clock}Z" if date else ts
            ingest_quote({"assetClass": asset_class, "venue": "stooq", "symbol": symbol.upper().replace(".US", "").replace(".F", "=F"), "ts": row_ts, "mid": close, "currency": "USD", "srcUrl": "https://stooq.com", "primaryDid": OWNER_DID})
            count += 1
        except Exception:
            continue
    return {"ok": True, "count": count, "assetClass": asset_class, "source": "stooq", "ts": ts}


def list_proposals(limit: int = 50, offset: int = 0, min_edge_bps: float = 20, asset_class: str = "") -> dict[str, Any]:
    params: list[Any] = [float(min_edge_bps)]
    where = "edge_bps >= %s"
    if asset_class:
        where += " AND asset_class = %s"
        params.append(asset_class)
    params.extend([int(max(1, min(500, limit))), int(max(0, offset))])
    rows = _fetch_all(
        f"""
        SELECT vertex_id, proposal_id, asset_class, leg_a, leg_b, spread_bps, edge_bps,
               confidence, expires_at, score, risk_notes
        FROM mv_arb_active_opps
        WHERE {where}
        ORDER BY edge_bps DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )
    proposals = [
        {
            "vertex_id": r[0],
            "proposal_id": r[1],
            "asset_class": r[2],
            "leg_a": r[3],
            "leg_b": r[4],
            "spread_bps": r[5],
            "edge_bps": r[6],
            "confidence": r[7],
            "expires_at": r[8],
            "score": r[9],
            "risk_notes": r[10],
        }
        for r in rows
    ]
    return {"ok": True, "proposals": proposals, "total": len(proposals), "offset": offset, "limit": limit}


def get_proposal(proposal_id: str) -> dict[str, Any]:
    if not proposal_id:
        return {"ok": False, "error": "InvalidRequest", "message": "proposalId required"}
    proposal = _fetch_one("SELECT * FROM vertex_arb_proposal WHERE proposal_id = %s LIMIT 1", (proposal_id,))
    if proposal is None:
        return {"ok": False, "error": "NotFound", "message": proposal_id}
    score = _fetch_one("SELECT * FROM vertex_arb_score WHERE proposal_id = %s LIMIT 1", (proposal_id,))
    publication = _fetch_one("SELECT * FROM vertex_arb_publication WHERE proposal_id = %s LIMIT 1", (proposal_id,))
    return {"ok": True, "proposal": tuple(proposal), "score": tuple(score) if score else None, "publication": tuple(publication) if publication else None}
