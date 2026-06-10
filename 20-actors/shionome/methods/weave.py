"""weave.py — 潮目 (shionome) capital-flow graph build + aggregate concentration. ADR-2606072200.

THE HEART of the actor and the G1/G2/G3/G4 anchor. Given the seed flow-graph it:

  1. VALIDATES every bucket / flow / snapshot against the closed structural vocab
     (mirror of the ontology :db/allowed + lexicon :enum/:const). A person/account node,
     a TRADE/advisory flow kind (buy / sell / recommend / target-price), an under-sourced
     flow, or a NaN/negative magnitude is a ValueError — not a silent drop. This is the
     third home of the invariants.
  2. WEAVES the validated records into an in-memory capital-flow graph.
  3. Computes AGGREGATE, EDGE-PRIMARY flow metrics (G4) — there is NO per-bucket
     rating/signal/target/score anywhere:
       - net flow per bucket (inflow − outflow)  — WHERE money is going / leaving
       - rotation pairs (source → target)         — どこからどこへ資金が流れているか
       - per-bucket inflow concentration (HHI)     — is money crowding into few buckets?
       - cross-asset regime descriptor             — FACTUAL risk-on/risk-off (NOT advice)

THE DEFINING INVARIANT — トレードはしない: nothing here is a buy/sell signal, a price
target, an over/under-weight call, or a portfolio instruction. Every output is an
observational MAP (G5) of realized flows, NON-advisory (G2): the metrics describe where
capital moved, never what anyone should do.

Stdlib only. Deterministic.
"""

from __future__ import annotations

import math
from typing import Any

# ── closed vocab (mirror of the ontology :db/allowed) ───────────────────────────
BUCKET_SCOPES = ("asset-class", "sector", "region", "theme")
FLOW_KINDS = (
    "rotation", "fund-inflow", "fund-outflow", "price-move",
    "cross-correlation", "volume-shift", "yield-shift", "fx-flow",
)
# the subset of flow kinds that move actual CAPITAL (a measurable amount of money). The
# net-flow / HHI / rotation money math sums ONLY these — co-movement / price / volume / yield
# observations are signals in other units (zscore / pct / bps), not capital amounts, so mixing
# them into the money totals would be a unit error.
CAPITAL_MOVEMENT_KINDS = ("rotation", "fund-inflow", "fund-outflow", "fx-flow")
SNAPSHOT_METRICS = ("return-pct", "net-fund-flow", "volume-z", "yield-pct", "spread-bps", "drawdown-pct", "outstanding-usd")
# the snapshot metric carrying a STOCK (the total SIZE of an asset class in USD trillions), as
# opposed to a flow/rate metric. `stock_pyramid` aggregates this into the money-and-markets
# sizing view. A size is a factual observed quantity (like return/yield), NEVER summed with flow
# magnitudes (usd-bn) — different unit — and NEVER a rating/signal/target (G2/G4 untouched).
STOCK_METRIC = "outstanding-usd"
REGIMES = ("risk-on", "risk-off", "mixed", "indeterminate")
SOURCING = ("representative", "authoritative")

# THE NO-TRADE TOKENS (トレードはしない) — any of these as a flow/bucket kind, or appearing
# in a social post body, turns an observation into a trade instruction / advice. They must
# NEVER be a flow/bucket attribute value and must never appear in published text. This is the
# Python mirror of the ontology's "advisory ABSENT" rule (G2 core).
TRADE_TOKENS = (
    "buy", "sell", "long", "short", "overweight", "underweight", "accumulate",
    "recommend", "recommendation", "rating", "target price", "target-price", "price target",
    "stop loss", "stop-loss", "take profit", "take-profit", "entry point", "exit point",
    "allocate", "strong buy", "strong sell", "outperform-rated", "should buy", "should sell",
    "推奨", "買い推奨", "売り推奨", "買い", "売り", "目標株価", "空売り", "ロング", "ショート",
    "利確", "損切り", "エントリー", "建玉", "ポジション取",
)

# Charter Rider §2(e) / N5 — commercial market-data / sell-side terminals are PROHIBITED as a
# citation source (anti-gatekeeping: cite the public record, never the paywalled compilation).
# A derived datom citing one of these is refused on EVERY path (seed / ingest / bridge).
SOURCE_DENY = ("bloomberg terminal", "bloomberg.com/professional", "refinitiv", "eikon",
               "factset", "capital iq", "capiq", "morningstar direct", "pitchbook",
               "tradingview premium", "koyfin pro", "四季報", "q(uick)", "sell-side desk")

# G9 / G1 no-doxxing — a node is a public BUCKET, so an individual-investor / account /
# personal field is unrepresentable (no tracking of who holds what).
PII_FORBIDDEN_BUCKET_ATTRS = frozenset({
    "account", "account-id", "broker", "holder", "owner", "investor", "trader",
    "wallet", "address", "email", "phone", "name", "person", "portfolio", "position-size",
})


def source_denied(sources) -> str:
    """Return the first prohibited commercial market-data term found in any source, or '' if clean."""
    blob = " ".join(str(s) for s in (sources or [])).lower()
    for d in SOURCE_DENY:
        if d in blob:
            return d
    return ""


def trade_token_in(text) -> str:
    """Return the first no-trade/advisory token found in `text`, or '' if clean. The core
    トレードはしない guard — used on every flow/bucket kind AND on every social-post body."""
    blob = str(text or "").lower()
    for t in TRADE_TOKENS:
        if t in blob:
            return t
    return ""


def _kw(v: Any) -> str:
    """Normalize an edn keyword/string to a bare lowercase token (':flow/kind' → 'kind')."""
    s = str(v or "").lstrip(":")
    return s.split("/")[-1].lower()


# ── validation (G1/G2/G3) ───────────────────────────────────────────────────────
def validate_bucket(b: dict) -> None:
    scope = _kw(b.get(":bucket/scope", ""))
    if scope not in BUCKET_SCOPES:
        raise ValueError(
            f"G1: bucket scope {scope!r} not in {BUCKET_SCOPES} — a person/account/portfolio is "
            f"unrepresentable (shionome maps public capital buckets, never individual investors)"
        )
    for forbidden in ("rating", "signal", "target", "score", "recommendation"):
        if f":bucket/{forbidden}" in b or forbidden in b:
            raise ValueError(
                f"G2/G4: a per-bucket {forbidden!r} is a trade instruction — unrepresentable "
                f"(トレードはしない; concentration is edge-primary, computed on read)"
            )
    for key in b:
        if _kw(key) in PII_FORBIDDEN_BUCKET_ATTRS:
            raise ValueError(
                f"G9/G1 no-doxxing: bucket field {key!r} is an individual-investor/account field — "
                f"unrepresentable on a public capital bucket (shionome never tracks who holds what)"
            )
    if _kw(b.get(":bucket/sourcing", "")) not in SOURCING:
        raise ValueError("G11: every bucket must declare :bucket/sourcing")


def validate_flow(f: dict) -> None:
    kind = _kw(f.get(":flow/kind", ""))
    if (t := trade_token_in(kind)):
        raise ValueError(f"G2: flow kind {kind!r} contains the trade token {t!r} — unrepresentable (トレードはしない)")
    if kind not in FLOW_KINDS:
        raise ValueError(f"G2: flow kind {kind!r} not in the factual observation vocab {FLOW_KINDS}")
    if f.get(":flow/no-trade-notice") is not True:
        raise ValueError("G2: :flow/no-trade-notice must be true (an observation, never a trade instruction)")
    srcs = f.get(":flow/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 2:
        raise ValueError(f"G3: flow {f.get(':flow/id')!r} needs ≥2 public-source citations")
    if (d := source_denied(srcs)):
        raise ValueError(f"Rider §2(e)/N5: source {d!r} is a commercial market-data terminal — prohibited citation")
    try:
        mag = float(f.get(":flow/magnitude", 0.0))
    except (TypeError, ValueError):
        raise ValueError(f"flow {f.get(':flow/id')!r} magnitude must be a number")
    if not math.isfinite(mag) or mag < 0:
        raise ValueError(
            f"flow {f.get(':flow/id')!r} magnitude must be finite and ≥ 0 "
            f"(a negative/NaN magnitude corrupts the net-flow/HHI math)"
        )
    if _kw(f.get(":flow/sourcing", "")) not in SOURCING:
        raise ValueError("G11: every flow must declare :flow/sourcing")


def validate_snapshot(s: dict) -> None:
    """An observed as-of bucket metric (return / net-flow / volume / yield). Must name a known
    metric (G2), carry ≥1 public source (G3, no prohibited terminal), declare sourcing (G11),
    and have a finite value."""
    metric = _kw(s.get(":snap/metric", ""))
    if metric not in SNAPSHOT_METRICS:
        raise ValueError(f"G2: snapshot metric {metric!r} not in {SNAPSHOT_METRICS}")
    srcs = s.get(":snap/sources") or []
    if not isinstance(srcs, list) or len(srcs) < 1:
        raise ValueError(f"G3: snapshot {s.get(':snap/id')!r} needs ≥1 public source")
    if (d := source_denied(srcs)):
        raise ValueError(f"Rider §2(e)/N5: source {d!r} is a commercial market-data terminal — prohibited citation")
    try:
        val = float(s.get(":snap/value", 0.0))
    except (TypeError, ValueError):
        raise ValueError(f"snapshot {s.get(':snap/id')!r} value must be a number")
    if not math.isfinite(val):
        raise ValueError(f"snapshot {s.get(':snap/id')!r} value must be finite")
    if _kw(s.get(":snap/sourcing", "")) not in SOURCING:
        raise ValueError("G11: every snapshot must declare :snap/sourcing")


# ── weave ───────────────────────────────────────────────────────────────────────
def weave(graph: dict) -> dict:
    """Validate + index the seed graph into an in-memory capital-flow graph. Raises on a gate."""
    buckets = {b[":bucket/id"]: b for b in graph.get(":buckets", [])}
    for b in buckets.values():
        validate_bucket(b)
    flows = list(graph.get(":flows", []))
    for f in flows:
        validate_flow(f)
    snapshots = list(graph.get(":snapshots", []))
    for s in snapshots:
        validate_snapshot(s)
    return {"buckets": buckets, "flows": flows, "snapshots": snapshots}


# ── aggregate, edge-primary flow metrics (G4) ────────────────────────────────────
def net_flow_by_bucket(g: dict) -> list[dict]:
    """Per bucket: net capital flow = (Σ magnitude of flows INTO it) − (Σ OUT of it).
    Positive = money flowing IN; negative = money flowing OUT. This is the core
    'どこに資金が流れているか'. Aggregate, edge-primary — NOT a rating to act on (G2/G4).
    The synthetic 'external' node is excluded (it represents the outside, not a bucket)."""
    into: dict[str, float] = {}
    outof: dict[str, float] = {}
    for f in g["flows"]:
        if _kw(f.get(":flow/kind")) not in CAPITAL_MOVEMENT_KINDS:
            continue   # only actual capital amounts contribute to net flow
        mag = float(f.get(":flow/magnitude", 0.0))
        tgt, src = f.get(":flow/target"), f.get(":flow/source")
        if tgt and tgt != "external":
            into[tgt] = into.get(tgt, 0.0) + mag
        if src and src != "external":
            outof[src] = outof.get(src, 0.0) + mag
    keys = set(into) | set(outof)
    out = []
    for b in keys:
        i, o = into.get(b, 0.0), outof.get(b, 0.0)
        out.append({
            "bucket": b,
            "label": g["buckets"].get(b, {}).get(":bucket/label", b),
            "inflow": round(i, 4),
            "outflow": round(o, 4),
            "net": round(i - o, 4),
        })
    return sorted(out, key=lambda x: (-x["net"], x["bucket"]))


def rotation_pairs(g: dict) -> list[dict]:
    """Ranked source→target rotation flows: どこからどこへ資金が回っているか. Only
    bucket→bucket flows where BOTH ends are real buckets (a rotation, not a pure in/outflow).
    Aggregate (summed over duplicate pairs), factual (G2)."""
    pairs: dict[tuple, float] = {}
    for f in g["flows"]:
        if _kw(f.get(":flow/kind")) not in CAPITAL_MOVEMENT_KINDS:
            continue   # a co-movement / price observation is not a rotation of capital
        src, tgt = f.get(":flow/source"), f.get(":flow/target")
        if src and tgt and src != "external" and tgt != "external" and src != tgt:
            pairs[(src, tgt)] = pairs.get((src, tgt), 0.0) + float(f.get(":flow/magnitude", 0.0))
    out = []
    for (src, tgt), mag in pairs.items():
        out.append({
            "from": src,
            "from_label": g["buckets"].get(src, {}).get(":bucket/label", src),
            "to": tgt,
            "to_label": g["buckets"].get(tgt, {}).get(":bucket/label", tgt),
            "magnitude": round(mag, 4),
        })
    return sorted(out, key=lambda x: (-x["magnitude"], x["from"], x["to"]))


def inflow_concentration(g: dict) -> dict:
    """Per-bucket INFLOW share + Herfindahl-Hirschman Index (HHI) over gross inflows.
    HHI ∈ (0,1]; higher = capital crowding into fewer buckets. Aggregate, factual (G4) —
    a description of crowding, NOT a signal to chase it (G2)."""
    by_bucket: dict[str, float] = {}
    total = 0.0
    for f in g["flows"]:
        if _kw(f.get(":flow/kind")) not in CAPITAL_MOVEMENT_KINDS:
            continue
        tgt = f.get(":flow/target")
        if tgt and tgt != "external":
            mag = float(f.get(":flow/magnitude", 0.0))
            by_bucket[tgt] = by_bucket.get(tgt, 0.0) + mag
            total += mag
    shares = {b: (v / total if total else 0.0) for b, v in by_bucket.items()}
    hhi = sum(s * s for s in shares.values())
    ranked = sorted(shares.items(), key=lambda kv: -kv[1])
    return {"total": round(total, 4), "hhi": round(hhi, 4), "shares": ranked, "by_bucket": by_bucket}


def by_asset_class(g: dict) -> list[dict]:
    """Net flow aggregated to the ASSET-CLASS level (equities / bonds / commodities / fx /
    crypto / real-estate / cash) — the top-level 'どの資産クラスに資金が向かっているか' view.
    Money is attributed to a flow end's bucket's asset-class. Aggregate, factual."""
    net = {r["bucket"]: r["net"] for r in net_flow_by_bucket(g)}
    klass: dict[str, dict] = {}
    for bid, n in net.items():
        ac = g["buckets"].get(bid, {}).get(":bucket/asset-class", "(unknown)")
        slot = klass.setdefault(ac, {"asset_class": ac, "net": 0.0, "buckets": 0})
        slot["net"] += n
        slot["buckets"] += 1
    for v in klass.values():
        v["net"] = round(v["net"], 4)
    return sorted(klass.values(), key=lambda x: (-x["net"], x["asset_class"]))


def by_region(g: dict) -> list[dict]:
    """Net flow aggregated to the REGION level (us / jp / eu / cn / em / global). The
    geographic 'どの地域に資金が向かっているか' view. Aggregate, factual."""
    net = {r["bucket"]: r["net"] for r in net_flow_by_bucket(g)}
    reg: dict[str, dict] = {}
    for bid, n in net.items():
        rg = g["buckets"].get(bid, {}).get(":bucket/region", "(unknown)")
        slot = reg.setdefault(rg, {"region": rg, "net": 0.0, "buckets": 0})
        slot["net"] += n
        slot["buckets"] += 1
    for v in reg.values():
        v["net"] = round(v["net"], 4)
    return sorted(reg.values(), key=lambda x: (-x["net"], x["region"]))


def regime(g: dict) -> dict:
    """A FACTUAL cross-asset regime descriptor (risk-on / risk-off / mixed / indeterminate),
    derived from the SIGN of net flow into :risk buckets vs :safe buckets. DESCRIPTIVE, NOT
    advice (G2): it summarizes which way capital leaned, it does not say what to do. Carries
    the no-trade notice. A bucket with no :bucket/risk tag is :neutral and ignored."""
    net = {r["bucket"]: r["net"] for r in net_flow_by_bucket(g)}
    risk_net = safe_net = 0.0
    for bid, n in net.items():
        tag = _kw(g["buckets"].get(bid, {}).get(":bucket/risk", ""))
        if tag == "risk":
            risk_net += n
        elif tag == "safe":
            safe_net += n
    if risk_net == 0.0 and safe_net == 0.0:
        label = "indeterminate"
    elif risk_net > 0 and safe_net <= 0:
        label = "risk-on"
    elif risk_net < 0 and safe_net >= 0:
        label = "risk-off"
    else:
        label = "mixed"
    return {
        "regime": label,
        "risk_net": round(risk_net, 4),
        "safe_net": round(safe_net, 4),
        "no_trade_notice": True,   # G2 — a description of capital flow, never advice
    }


def correlation_clusters(g: dict) -> list[dict]:
    """Buckets observed moving together (:cross-correlation edges) — undirected co-movement
    components. Aggregate; the substance lives on the edges (G4), never a per-bucket score."""
    adj: dict[str, set] = {}
    for f in g["flows"]:
        if _kw(f.get(":flow/kind")) == "cross-correlation":
            a, b = f.get(":flow/source"), f.get(":flow/target")
            if a and b and a != "external" and b != "external":
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
    seen: set = set()
    clusters = []
    for node in sorted(adj):
        if node in seen:
            continue
        stack, comp = [node], []
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            comp.append(n)
            stack.extend(adj.get(n, ()) - seen)
        if len(comp) > 1:
            clusters.append({"members": sorted(comp), "size": len(comp)})
    return sorted(clusters, key=lambda x: (-x["size"], x["members"]))


def active_as_of(g: dict, ts: int) -> dict:
    """G10 / 非終末論 — time-travel: how many flows/snapshots are observed as of `ts`
    (as-of ≤ ts). The graph is append-only, so a query at an earlier ts simply sees fewer
    datoms; nothing is ever overwritten or deleted."""
    active_flows = [f for f in g["flows"] if int(f.get(":flow/as-of", 0)) <= ts]
    active_snaps = [s for s in g["snapshots"] if int(s.get(":snap/as-of", 0)) <= ts]
    return {
        "ts": ts,
        "active_flows": len(active_flows),
        "total_flows": len(g["flows"]),
        "active_snapshots": len(active_snaps),
        "total_snapshots": len(g["snapshots"]),
    }


def check_integrity(g: dict) -> dict:
    """Referential integrity: every flow/snapshot end must resolve to an existing bucket (or
    the synthetic 'external' node for a flow end). A data-quality diagnostic, not a charter gate."""
    buckets = set(g["buckets"])
    flow_space = buckets | {"external"}
    dangling = []

    def chk(ref, space, kind, owner, field):
        if ref and ref not in space:
            dangling.append({"kind": kind, "owner": owner, "field": field, "ref": ref})

    for f in g["flows"]:
        chk(f.get(":flow/source"), flow_space, "flow", f.get(":flow/id"), "source")
        chk(f.get(":flow/target"), flow_space, "flow", f.get(":flow/id"), "target")
    for s in g["snapshots"]:
        chk(s.get(":snap/bucket"), buckets, "snapshot", s.get(":snap/id"), "bucket")
    return {"dangling_count": len(dangling), "dangling": dangling}


def assert_integrity(g: dict) -> None:
    """Strict mode — raise if any reference dangles (used by the ingest data-quality gate)."""
    rep = check_integrity(g)
    if rep["dangling_count"]:
        first = rep["dangling"][0]
        raise ValueError(
            f"integrity: {rep['dangling_count']} dangling ref(s); e.g. {first['kind']} "
            f"{first['owner']!r} {first['field']}→{first['ref']!r} (no such bucket)"
        )


# ── stock layer (the money-and-markets pyramid) ───────────────────────────────────
def latest_stock_by_bucket(g: dict) -> dict:
    """For each bucket carrying an :outstanding-usd snapshot, the LATEST observed stock size
    (USD trillions), taken by max :snap/as-of (G10 append-only — the newest observation wins on
    read, the older ones are never deleted). Returns {bucket_id: (value, as_of)}. Factual sizes,
    never a rating/signal (G2/G4)."""
    latest: dict[str, tuple[float, int]] = {}
    for s in g["snapshots"]:
        if _kw(s.get(":snap/metric")) != STOCK_METRIC:
            continue
        bid = s.get(":snap/bucket")
        if not bid:
            continue
        as_of = int(s.get(":snap/as-of", 0))
        val = float(s.get(":snap/value", 0.0))
        if bid not in latest or as_of >= latest[bid][1]:
            latest[bid] = (val, as_of)
    return latest


def stock_pyramid(g: dict) -> dict:
    """THE 'how big is everything' SIZING VIEW — the Visual-Capitalist money-and-markets pyramid.
    Aggregates the latest :outstanding-usd stock per bucket up to the ASSET-CLASS level and sizes
    each layer against the grand total (share of all observed capital). This is a FACTUAL stock
    sizing — descriptive, NOT a per-asset rating/signal/target and NOT advice (G2/G4): it says how
    large each pool of capital is, never what to do with it (トレードはしない). Stock values are
    USD trillions; they are NEVER mixed with flow magnitudes (usd-bn) — a separate, on-read view."""
    latest = latest_stock_by_bucket(g)
    layers: dict[str, dict] = {}
    for bid, (val, _as_of) in latest.items():
        ac = g["buckets"].get(bid, {}).get(":bucket/asset-class", "(unknown)")
        slot = layers.setdefault(ac, {"asset_class": ac, "usd_tn": 0.0, "buckets": 0})
        slot["usd_tn"] += val
        slot["buckets"] += 1
    grand = sum(l["usd_tn"] for l in layers.values())
    rows = []
    for l in sorted(layers.values(), key=lambda x: (-x["usd_tn"], x["asset_class"])):
        rows.append({
            "asset_class": l["asset_class"],
            "usd_tn": round(l["usd_tn"], 4),
            "share": round(l["usd_tn"] / grand, 4) if grand else 0.0,
            "buckets": l["buckets"],
        })
    return {
        "layers": rows,
        "grand_total_usd_tn": round(grand, 4),
        "bucket_count": len(latest),
        "unit": "usd-tn",
        "no_trade_notice": True,   # G2 — a size, never advice (トレードはしない)
    }


def concentration(g: dict) -> dict:
    """The full aggregate-first flow report (G3/G4). All metrics are derived on read from
    flows/snapshots; nothing is a per-bucket rating/signal/target/score (トレードはしない)."""
    return {
        "bucket_count": len(g["buckets"]),
        "flow_count": len(g["flows"]),
        "snapshot_count": len(g["snapshots"]),
        "net_flow_by_bucket": net_flow_by_bucket(g),
        "rotation_pairs": rotation_pairs(g),
        "inflow_concentration": inflow_concentration(g),
        "by_asset_class": by_asset_class(g),
        "by_region": by_region(g),
        "stock_pyramid": stock_pyramid(g),
        "regime": regime(g),
        "correlation_clusters": correlation_clusters(g),
        "integrity": check_integrity(g),
    }


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-capital-flow-graph.kotoba.edn")
    g = weave(seed)
    c = concentration(g)
    print("# 潮目 (shionome) — aggregate capital-flow concentration over the :representative seed\n")
    print(f"buckets={c['bucket_count']} flows={c['flow_count']} snapshots={c['snapshot_count']}\n")
    print("## net flow by bucket (where money is going / leaving)")
    for r in c["net_flow_by_bucket"]:
        arrow = "▲ in " if r["net"] > 0 else ("▼ out" if r["net"] < 0 else "= flat")
        print(f"- {r['label']}: net {r['net']:+.2f} {arrow}  (in {r['inflow']:.2f} / out {r['outflow']:.2f})")
    print("\n## rotation pairs (どこからどこへ)")
    for r in c["rotation_pairs"]:
        print(f"- {r['from_label']} → {r['to_label']}: {r['magnitude']:.2f}")
    ic = c["inflow_concentration"]
    print(f"\n## inflow concentration — HHI={ic['hhi']} over total {ic['total']:.2f}")
    sp = c["stock_pyramid"]
    print(f"\n## stock pyramid — how big is everything (USD tn; grand total {sp['grand_total_usd_tn']:.1f})")
    for r in sp["layers"]:
        bar = "█" * max(1, round(r["share"] * 40))
        print(f"- {r['asset_class']:<14} {r['usd_tn']:>8.1f} tn  {r['share']*100:5.1f}%  {bar}")
    print(f"\n## cross-asset regime: {c['regime']['regime']} "
          f"(risk_net={c['regime']['risk_net']:+.2f} safe_net={c['regime']['safe_net']:+.2f}) "
          f"— descriptive, NOT advice (トレードはしない)")
