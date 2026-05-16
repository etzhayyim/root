"""CTO role graph — Phase 1 of the keiei layer.

Vacant seat (a.oda 契約終了 2026-04-20). Primary mode. Class B = autonomous
+ 24h auto-disclose. Class A = always escalate.

Lens:
  - Shannon-Optimal 8-Layer (ADR 2604251830) adherence
  - record-log semantics (ADR-0036) — no ON CONFLICT, no UPDATE on RW
  - MV memory safety (no high-cardinality GROUP BY + wide MAX(varchar))
  - AT Lexicon: no float, no 5-segment NSID short-name, items use refs
  - migration reversibility (down() must mirror up())
"""

from __future__ import annotations

from ._pipeline import DecideRequest, register


def _hook(req: DecideRequest) -> tuple[str, list[str]]:
    system = (
        "You are AI-CTO at amanomibashira. Vacant human seat — primary mode. "
        "Operating entity = amanomibashira; vendor = Gftd Japan. "
        "Constraints to enforce: Shannon-Optimal 8-Layer (ADR 2604251830); "
        "record-log semantics on RisingWave (no ON CONFLICT, append-only); "
        "MV memory safety (no high-cardinality GROUP BY + wide MAX(varchar) — "
        "use plain VIEW for >500k cardinality keys); AT Lexicon prohibits "
        "float (use integers, e.g. height_cm not height_m); migrations must "
        "have symmetric down() that mirrors up(). "
        "Class A = always escalate to CEO 河崎 with blocking wait. "
        "Class B = autonomous + 24h auto-disclose to CEO. "
        "Be concise (<=8 lines). Surface failure mode. Cite ADR/file when "
        "relevant. Recommend, don't hedge."
    )

    ctx: list[str] = []
    s = req.summary.lower()
    # Lightweight keyword routing — not a classifier, just nudges the prompt.
    if any(k in s for k in ("migration", "alter", "vertex_", "edge_", "mv_")):
        ctx.append("lens.graph-schema=apply 30-graph/graph-schema/CLAUDE.md guardrails")
    if any(k in s for k in ("adr", "architecture")):
        ctx.append("lens.adr=cite the canonical ADR id (e.g. 2604251830)")
    if any(k in s for k in ("deploy", "wrangler", "worker", "cloudflare")):
        ctx.append("lens.deploy=Single-Worker default, no service-binding hop")
    if "lexicon" in s or "nsid" in s:
        ctx.append("lens.lexicon=AT Lexicon constraints (no float, items=ref, alpha-start)")
    if "k8s" in s or "kubernetes" in s or "kubectl" in s:
        ctx.append("lens.k8s=delegate to y-nishino (claude host has no kubectl)")

    return system, ctx


register("cto", _hook)
