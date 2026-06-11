"""social.py — 潮目 (shionome) DRY-RUN social-post projection. ADR-2606072200.

Projects an AGGREGATE capital-flow finding into a social post (app.bsky.feed.post-shaped),
enforcing the post invariants in their third home (mirror of the ontology :db/allowed +
networkPost.edn :const):

  G2 — THE DEFINING INVARIANT (トレードはしない): noTradeNotice=true; the body is SCANNED for
       trade/advisory tokens (buy / sell / target / 推奨 / 買い / 売り …) and REFUSED if any
       appear. A post narrates where money MOVED, never what anyone should do.
  G5 — every post opens with the observational-mirror disclaimer (isMirror=true), never a
       trade signal, never financial advice.
  G7 — serverHeldKey=false; the member signs, the server never does (ADR-2605231525).
  G8 — status is 'dry-run' only at R0; 'published' is unrepresentable. A live post needs
       Council Lv6+ + operator + a member signature (build_live raises here).
  G3 — the post carries the same ≥2 public-source citations as the finding.

Stdlib only. Deterministic.
"""

from __future__ import annotations

from weave import source_denied, trade_token_in

DISCLAIMER = (
    "【観測ミラー / capital-flow observation — NOT financial advice, トレードはしない】 "
    "公開市場データから観測した資金フローの集計です。売買の推奨・目標価格・ポジション提案は一切しません。"
)


def _guard_sources(sources) -> list[str]:
    s = [x for x in (sources or []) if str(x).strip()]
    if len(s) < 2:
        raise ValueError("G3: a post needs ≥2 public-source citations")
    if (d := source_denied(s)):
        raise ValueError(f"Rider §2(e)/N5: source {d!r} is a commercial market-data terminal — a post may not cite it")
    return s


def _guard_no_trade(body: str) -> None:
    """G2 core (トレードはしない) — refuse to emit a post whose body contains a trade/advisory
    token. The disclaimer text is exempt (it NAMES the prohibited acts to disclaim them)."""
    scanned = body.replace(DISCLAIMER, "")
    if (t := trade_token_in(scanned)):
        raise ValueError(
            f"G2: post body contains the trade/advisory token {t!r} — refused (shionome never "
            f"recommends a trade; it only observes flows). トレードはしない."
        )


def draft_netflow_post(net_rows: list[dict], sources, author: str = "") -> dict:
    """A dry-run post about where money is going / leaving (top inflow + top outflow bucket).
    Aggregate, factual, non-advisory."""
    srcs = _guard_sources(sources)
    inflows = [r for r in net_rows if r["net"] > 0]
    outflows = [r for r in net_rows if r["net"] < 0]
    top_in = inflows[0] if inflows else None
    top_out = min(outflows, key=lambda r: r["net"]) if outflows else None
    parts = [DISCLAIMER, ""]
    if top_in:
        parts.append(f"資金流入トップ: {top_in['label']} (net +{top_in['net']:.1f}bn)。")
    if top_out:
        parts.append(f"資金流出トップ: {top_out['label']} (net {top_out['net']:.1f}bn)。")
    parts.append(f"出典 {len(srcs)} 件。")
    body = "\n\n".join([parts[0], " ".join(parts[2:])]) if len(parts) > 2 else DISCLAIMER
    _guard_no_trade(body)
    return _post("netflow", body, srcs, author)


def draft_rotation_post(rotation_rows: list[dict], sources, author: str = "") -> dict:
    """A dry-run post about the largest observed rotation pair (どこからどこへ)."""
    srcs = _guard_sources(sources)
    top = rotation_rows[0] if rotation_rows else None
    if top:
        body = (f"{DISCLAIMER}\n\n"
                f"最大の資金回転: {top['from_label']} → {top['to_label']} ({top['magnitude']:.1f}bn 相当)。"
                f"出典 {len(srcs)} 件。")
    else:
        body = f"{DISCLAIMER}\n\n観測された資金回転はありません。出典 {len(srcs)} 件。"
    _guard_no_trade(body)
    return _post("rotation", body, srcs, author)


def draft_regime_post(regime: dict, sources, author: str = "") -> dict:
    """A dry-run post stating the FACTUAL cross-asset regime descriptor (risk-on/off/mixed).
    Descriptive only — explicitly carries the no-trade notice (G2)."""
    srcs = _guard_sources(sources)
    jp = {"risk-on": "リスクオン", "risk-off": "リスクオフ", "mixed": "まちまち",
          "indeterminate": "判定不能"}.get(regime["regime"], regime["regime"])
    body = (f"{DISCLAIMER}\n\n"
            f"クロスアセット観測: {jp} ({regime['regime']}) — リスク資産 net {regime['risk_net']:+.1f}bn / "
            f"安全資産 net {regime['safe_net']:+.1f}bn。記述であり助言ではありません。出典 {len(srcs)} 件。")
    _guard_no_trade(body)
    return _post("regime", body, srcs, author)


def _post(subject: str, body: str, sources: list[str], author: str) -> dict:
    """Assemble a networkPost record with every invariant pinned. status is ALWAYS dry-run."""
    return {
        ":post/subject": subject,
        ":post/body": body,
        ":post/status": ":dry-run",          # G8 — published is unrepresentable
        ":post/is-mirror": True,             # G5
        ":post/no-trade-notice": True,       # G2 — トレードはしない
        ":post/server-held-key": False,      # G7 / no-server-key
        ":post/author": author,              # member DID (required only for a gated live post)
        ":post/sources": sources,            # G3
    }


def build_live(*_args, **_kwargs):
    """G8 — live posting is outward-gated. Refuses by construction at R0."""
    raise RuntimeError(
        "shionome R0: live social posting is Council Lv6+ + operator + member-signature gated (G8). "
        "Only dry-run posts are producible offline."
    )


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn
    from weave import concentration, weave

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-capital-flow-graph.kotoba.edn")
    g = weave(seed)
    c = concentration(g)
    allsrcs = sorted({s for f in g["flows"] for s in f.get(":flow/sources", [])})
    print("# 潮目 (shionome) — DRY-RUN social posts\n")
    for p in (draft_netflow_post(c["net_flow_by_bucket"], allsrcs),
              draft_rotation_post(c["rotation_pairs"], allsrcs),
              draft_regime_post(c["regime"], allsrcs)):
        print(p[":post/body"])
        print(f"  status={p[':post/status']} noTrade={p[':post/no-trade-notice']} "
              f"serverHeldKey={p[':post/server-held-key']}\n")
