"""shionome_core — pure capital-flow logic shared by the shionome_* fleet cells.

Per ADR-2606072200. The 5 shionome Pregel cells (ingest / flow_graph / rotation_weave /
regime_observer / social_post) run as kotoba-WASM cells under cron on the Murakumo fleet. Their
cell.py wrappers import kotoba_langgraph (present only in the kotoba runtime); this module holds
the PURE logic with NO runtime dependency, so it is unit-testable off-fleet (the watatsuna/
shionome WASM split) and is the single home of the no-trade discipline for the cells.

THE DEFINING INVARIANT — トレードはしない (G2): trade/advisory tokens are refused on every flow
kind AND on every dry-run post body; only capital-movement kinds feed the money math. Nothing
here is a buy/sell signal, price target, or portfolio instruction.

Stdlib only. Deterministic.
"""

from __future__ import annotations

CAPITAL_MOVEMENT = ("rotation", "fund-inflow", "fund-outflow", "fx-flow")
FLOW_KINDS = CAPITAL_MOVEMENT + ("price-move", "cross-correlation", "volume-shift", "yield-shift")
TRADE_TOKENS = ("buy", "sell", "long", "short", "overweight", "underweight", "recommend",
                "target price", "target-price", "推奨", "買い", "売り", "目標株価", "空売り")

DISCLAIMER = ("【観測ミラー / capital-flow observation — NOT financial advice, トレードはしない】 "
              "公開市場データから観測した資金フローの集計です。売買の推奨・目標価格・ポジション提案はしません。")


def _kw(v) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def trade_token_in(text) -> str:
    blob = str(text or "").lower()
    for t in TRADE_TOKENS:
        if t in blob:
            return t
    return ""


def screen_flows(flows: list[dict]) -> list[dict]:
    """G1/G2/G3 intake screen. Each flow needs a factual (non-trade) kind + ≥2 sources. Raises on
    a violation (refuse the batch, never silently drop). Returns the screened flows."""
    for f in flows:
        kind = _kw(f.get("kind"))
        if (t := trade_token_in(kind)):
            raise ValueError(f"G2: flow kind contains trade token {t!r} — unrepresentable (トレードはしない)")
        if kind not in FLOW_KINDS:
            raise ValueError(f"G2: flow kind {kind!r} not a factual observation")
        if len([s for s in f.get("sources", []) if str(s).strip()]) < 2:
            raise ValueError("G3: a flow needs ≥2 public-source citations")
    return flows


def net_flow(flows: list[dict]) -> list[dict]:
    """Per-bucket net capital flow (in − out), capital-movement kinds only. Descending by net."""
    into, outof = {}, {}
    for f in flows:
        if _kw(f.get("kind")) not in CAPITAL_MOVEMENT:
            continue
        mag = float(f.get("magnitude", 0.0))
        src, tgt = f.get("source"), f.get("target")
        if tgt and tgt != "external":
            into[tgt] = into.get(tgt, 0.0) + mag
        if src and src != "external":
            outof[src] = outof.get(src, 0.0) + mag
    rows = [{"bucket": b, "net": round(into.get(b, 0.0) - outof.get(b, 0.0), 4)}
            for b in set(into) | set(outof)]
    rows.sort(key=lambda r: (-r["net"], r["bucket"]))
    return rows


def top_rotation(flows: list[dict]) -> dict | None:
    """The largest bucket→bucket rotation (capital-movement kinds only), or None."""
    pairs: dict[tuple, float] = {}
    for f in flows:
        if _kw(f.get("kind")) not in CAPITAL_MOVEMENT:
            continue
        s, t = f.get("source"), f.get("target")
        if s and t and s != "external" and t != "external" and s != t:
            pairs[(s, t)] = pairs.get((s, t), 0.0) + float(f.get("magnitude", 0.0))
    if not pairs:
        return None
    (s, t), m = max(pairs.items(), key=lambda kv: kv[1])
    return {"from": s, "to": t, "magnitude": round(m, 4)}


def regime(net_rows: list[dict], risk_tags: dict) -> dict:
    """FACTUAL cross-asset regime from net flow into risk vs safe buckets. Descriptive, NOT advice."""
    risk_net = sum(r["net"] for r in net_rows if risk_tags.get(r["bucket"]) == "risk")
    safe_net = sum(r["net"] for r in net_rows if risk_tags.get(r["bucket"]) == "safe")
    if risk_net == 0 and safe_net == 0:
        label = "indeterminate"
    elif risk_net > 0 and safe_net <= 0:
        label = "risk-on"
    elif risk_net < 0 and safe_net >= 0:
        label = "risk-off"
    else:
        label = "mixed"
    return {"regime": label, "risk_net": round(risk_net, 4), "safe_net": round(safe_net, 4),
            "no_trade_notice": True}


def draft_dry_run_post(body_core: str, sources: list[str]) -> dict:
    """A dry-run post (status dry-run only, G8). Refuses a trade-token body (G2) / <2 sources (G3)."""
    if (t := trade_token_in(body_core)):
        raise ValueError(f"G2: post body contains trade token {t!r} — refused (トレードはしない)")
    if len([s for s in (sources or []) if str(s).strip()]) < 2:
        raise ValueError("G3: a post needs ≥2 public-source citations")
    return {
        "status": "dry-run",          # G8 — :published unrepresentable
        "is_mirror": True,            # G5
        "no_trade_notice": True,      # G2
        "server_held_key": False,     # G7
        "body": f"{DISCLAIMER}\n\n{body_core}",
        "sources": list(sources),
    }
