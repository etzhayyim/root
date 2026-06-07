"""social.py — 高札 (kosatsu) DRY-RUN social posts. ADR-2606072000.

Projects the aggregate divergence/agreement findings into member-signable, NON-adjudicating
dry-run posts. G8: status is always 'dry-run' (never published; outward-gated). G9: every post
opens with the mirror/competing-claim disclaimer and never speaks AS an authority. G7: the
server never signs — a real post requires a member signature (serverHeldKey false). G2: a post
reports who-designated-whom + disagreement, never a verdict.

Stdlib only. Deterministic.
"""

from __future__ import annotations

from weave import agreement_index, divergence_all, report

MIRROR_PREFIX = (
    "[mirror · not a verdict] kosatsu reports, attributed, what public authorities themselves "
    "posted; a designation is asserter-relative. "
)


def _post(post_id: str, subject: str, body: str, sources: list[str]) -> dict:
    """Build a dry-run networkPost record. The structural fields are const-locked (G2/G7/G8/G9)."""
    if len(sources) < 2:
        raise ValueError("G3: a post needs ≥2 primary-source citations")
    return {
        ":post/id": post_id,
        ":post/subject": subject,
        ":post/body": MIRROR_PREFIX + body,
        ":post/status": ":dry-run",          # G8 — never :published at R0
        ":post/is-mirror": True,             # G9
        ":post/non-adjudicating-notice": True,  # G2
        ":post/server-held-key": False,      # G7 — member signs, not the server
        ":post/sources": sources,
    }


def posts(g: dict, ts: int | None = None) -> list[dict]:
    r = report(g, ts)
    ai = r["agreement_index"]
    out = []

    out.append(_post(
        "post-summary",
        "designation divergence summary",
        f"Across {ai['designated_subjects']} designated subjects: {ai['contested']} contested "
        f"(jurisdictions disagree), {ai['unanimous']} unanimous, {ai['single_asserter']} "
        f"single-asserter. Contested-ratio {ai['contested_ratio']}.",
        ["https://ofac.treasury.gov/", "https://www.sanctionsmap.eu/"],
    ))

    for d in divergence_all(g, ts):
        if d["class"] != "contested":
            continue
        out.append(_post(
            f"post-{d['subject']}",
            f"{d['subject']} — contested designation",
            f"{d['subject']}: listed by {d['listing']}; delisted by {d['delisted'] or '—'}; "
            f"no designation from {d['silent'] or '—'}. The same subject is treated differently "
            f"across jurisdictions — that divergence is the fact, not a verdict.",
            ["https://ofac.treasury.gov/", "https://www.sanctionsmap.eu/"],
        ))
    return out


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn
    from weave import weave

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn")
    g = weave(seed)
    for p in posts(g):
        print(f"[{p[':post/status'].lstrip(':')}] {p[':post/subject']}\n  {p[':post/body']}\n")
