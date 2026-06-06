"""social.py — 系図 (keizu) DRY-RUN social-post projection. ADR-2606066000.

Projects an AGGREGATE concentration finding into a social post (app.bsky.feed.post-shaped),
enforcing the post invariants in their third home (mirror of the ontology :db/allowed +
networkPost.edn :const):

  G5 — every post opens with the mirror / accountability-map disclaimer (isMirror=true),
       never speaks AS a government, never names a private individual.
  G2 — nonAdjudicatingNotice=true; the post narrates ties/shares, never a verdict.
  G7 — serverHeldKey=false; the member signs, the server never does (ADR-2605231525).
  G8 — status is 'dry-run' only at R0; `published` is unrepresentable. A live post needs
       Council Lv6+ + operator + a member signature (build_live raises here).
  G3 — the post carries the same ≥2 public-source citations as the finding.

Stdlib only. Deterministic.
"""

from __future__ import annotations

DISCLAIMER = (
    "【観測ミラー / accountability map — NOT the government, non-adjudicating】 "
    "公開情報から編んだ関係グラフの集計です。特定個人を名指しせず、不正の断定もしません。"
)


def _enough_sources(sources) -> list[str]:
    s = [x for x in (sources or []) if str(x).strip()]
    if len(s) < 2:
        raise ValueError("G3: a post needs ≥2 public-source citations")
    return s


def draft_committee_post(finding: dict, sources, author: str = "") -> dict:
    """A dry-run post about a committee's cross-organ concentration (aggregate, no person)."""
    srcs = _enough_sources(sources)
    body = (
        f"{DISCLAIMER}\n\n"
        f"{finding['label']}: {finding['member_count']} seats drawn from "
        f"{finding['distinct_organs']} organ(s) {finding['organs']}. "
        f"出典 {len(srcs)} 件。"
    )
    return _post(f"committee:{finding['committee']}", body, srcs, author)


def draft_money_post(money_concentration: dict, sources, author: str = "") -> dict:
    """A dry-run post about per-payee money concentration (HHI), aggregate + factual."""
    srcs = _enough_sources(sources)
    top = money_concentration["shares"][0] if money_concentration["shares"] else ("(none)", 0.0)
    body = (
        f"{DISCLAIMER}\n\n"
        f"公開された資金フローの集中度 HHI={money_concentration['hhi']}。"
        f"最大受領 {top[0]} = {top[1]*100:.1f}%。出典 {len(srcs)} 件。"
    )
    return _post("money:concentration", body, srcs, author)


def _post(subject: str, body: str, sources: list[str], author: str) -> dict:
    """Assemble a networkPost record with every invariant pinned. status is ALWAYS dry-run."""
    return {
        ":post/subject": subject,
        ":post/body": body,
        ":post/status": ":dry-run",          # G8 — published is unrepresentable
        ":post/is-mirror": True,             # G5
        ":post/non-adjudicating-notice": True,  # G2
        ":post/server-held-key": False,      # G7 / no-server-key
        ":post/author": author,              # member DID (required only for a gated live post)
        ":post/sources": sources,            # G3
    }


def build_live(*_args, **_kwargs):
    """G8 — live posting is outward-gated. Refuses by construction at R0."""
    raise RuntimeError(
        "keizu R0: live social posting is Council Lv6+ + operator + member-signature gated (G8). "
        "Only dry-run posts are producible offline."
    )


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn
    from weave import weave, concentration

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-relation-graph.kotoba.edn")
    g = weave(seed)
    c = concentration(g)
    print("# 系図 (keizu) — DRY-RUN social posts\n")
    if c["committee_cross_organ"]:
        f = c["committee_cross_organ"][0]
        comm = g["committees"].get(f["committee"], {})
        p = draft_committee_post(f, comm.get(":committee/sources", ["", ""]) + ["https://www.mof.go.jp/"])
        print(p[":post/body"], "\n  status:", p[":post/status"], "serverHeldKey:", p[":post/server-held-key"], "\n")
    mc = c["money_concentration"]
    allsrcs = sorted({s for m in g["money"] for s in m.get(":money/sources", [])})
    p2 = draft_money_post(mc, allsrcs)
    print(p2[":post/body"], "\n  status:", p2[":post/status"], "isMirror:", p2[":post/is-mirror"])
