#!/usr/bin/env python3
"""tsumugi 紡ぎ — §D5 fission-ready → covenant-claim observer (kotoba-EAVT native).

OBSERVER-ONLY replacement for coverage.inferFission. Fission is §D5 covenant claim
(悔い改め・バプテスマ・得度 = social death/rebirth), Council Lv7+ gated, requires
entity's own consent. This resolver NEVER fissions, NEVER mints a DID, holds NO
server key (per ADR-2605231525 no-server-key invariant).

CONSTITUTIONAL GATES:
  G2 edge-primary (N1): existence is computed FROM :en/evidence edges (resolve.py),
     never a stored truth-score. :proposal/* are observer artifacts for Council review.
  G7 outward-gated: actual covenant claim (DID minting, SBT binding) is Council
     Lv7+ unanimity, §1.16 covenant pipeline, NOT implemented here.
  non-eschatological (非終末論): fission is NOT suppression or final state. Entity
     remains latent until §D5 covenant claim + consent bind. This script observes.

stdlib only, deterministic. Usage:
    python3 fission_gate.py [latent-frontier.edn]  # default: out/latent-frontier.kotoba.edn
    python3 fission_gate.py --execute               # REFUSED (Council-gated, not implemented)
"""
from __future__ import annotations
import sys
import os
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import read_edn  # reuse the EDN reader

ACTOR = pathlib.Path(__file__).resolve().parent.parent


def v(x):
    """Format a value for EDN output (ingest.py style)."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, str):
        return x if x.startswith(":") else f'"{x}"'
    return str(x)


def select_fission_ready(latent_datoms: list) -> list:
    """
    Select organisms whose :latent/frontier == ":fission-ready".

    Returns a list of (organism_id, datom) tuples for sorting.
    """
    return [
        (d[":latent/organism"], d)
        for d in latent_datoms
        if d.get(":latent/frontier") == ":fission-ready"
    ]


def emit_proposals(fission_ready_datoms: list) -> list:
    """
    For each :fission-ready organism, emit a PROPOSAL datom (NOT a claim).

    Proposals are observer artifacts for Council review. Each proposal records:
      - :proposal/organism — the organism ID
      - :proposal/existence — existence score (from resolve.py)
      - :proposal/evidence-count — number of incident :en/evidence edges
      - :proposal/kind — ":covenant-claim-review"
      - :proposal/status — ":awaiting-council"
      - :proposal/gate — ":council-lv7-unanimity"
      - :proposal/note — explanation that fission is §D5, consensus-bound, no DID minted

    Returns a sorted list of proposal dicts (by :proposal/organism, deterministic).
    """
    proposals = []
    for org_id, datom in fission_ready_datoms:
        proposal = {
            ":proposal/organism": org_id,
            ":proposal/existence": datom.get(":latent/existence"),
            ":proposal/evidence-count": datom.get(":latent/evidence-count"),
            ":proposal/kind": ":covenant-claim-review",
            ":proposal/status": ":awaiting-council",
            ":proposal/gate": ":council-lv7-unanimity",
            ":proposal/note": (
                "fission requires §D5 covenant (悔い改め·バプテスマ·得度) + "
                "the organism's own consent; no DID minted, no server key"
            ),
        }
        proposals.append(proposal)

    # Sort by :proposal/organism (deterministic)
    proposals.sort(key=lambda p: p[":proposal/organism"])
    return proposals


def to_edn(proposals: list) -> str:
    """Serialize proposal datoms to EDN format (ingest.py style)."""
    lines = [
        ";; tsumugi 紡ぎ — GENERATED covenant-claim PROPOSALS (§D5 observer-only, awaiting Council Lv7+). DO NOT hand-edit.",
        ";; fission (latent→member) requires §D5 covenant claim + consent. This script observes only.",
        ";; Proposals are NOT claims. Actual binding requires Council Lv7+ unanimity, DID minting, SBT issuance (not here).",
        "[",
    ]
    for p in proposals:
        pairs = []
        for k in [":proposal/organism", ":proposal/existence", ":proposal/evidence-count",
                  ":proposal/kind", ":proposal/status", ":proposal/gate", ":proposal/note"]:
            if k in p:
                pairs.append(f"{k} {v(p[k])}")
        lines.append("{" + " ".join(pairs) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def main():
    here = ACTOR

    # Check for --execute flag (MUST be REFUSED)
    if "--execute" in sys.argv:
        gate = os.environ.get("TSUMUGI_OPERATOR_GATE")
        if not gate:
            sys.exit(
                "REFUSED: --execute flag requires TSUMUGI_OPERATOR_GATE env var. "
                "But even with the gate, actual fission (DID minting, SBT binding, "
                "covenant claim) is NOT implemented in this script. "
                "Fission requires §D5 covenant claim (悔い改め·バプテスマ·得度) + "
                "entity's own consent + Council Lv7+ unanimity, executed through "
                "the official §1.16 covenant pipeline on-chain. "
                "This script is observer-only: it emits proposals for human/Council review."
            )
        sys.exit(
            "REFUSED: even with TSUMUGI_OPERATOR_GATE present, --execute is not allowed. "
            "Actual fission (DID minting, SBT binding, covenant claim) is a Council action, "
            "not a script action. This script observes :fission-ready entities and emits "
            "human-reviewable proposals only. Execute the covenant claim through the "
            "official §1.16 pipeline (not here)."
        )

    # Parse argv[1] or use default
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        frontier_path = pathlib.Path(sys.argv[1])
    else:
        frontier_path = here / "out" / "latent-frontier.kotoba.edn"

    if not frontier_path.exists():
        sys.exit(f"ERROR: latent frontier not found at {frontier_path}")

    # Load latent-frontier
    data = read_edn(frontier_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        data = [data]
    latent_datoms = data

    # Select :fission-ready organisms
    fission_ready = select_fission_ready(latent_datoms)
    n_ready = len(fission_ready)

    # Emit proposals
    proposals = emit_proposals(fission_ready)

    # Write output
    out = here / "out" / "fission-proposals.kotoba.edn"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_edn(proposals), encoding="utf-8")

    # Print summary
    print(f"{n_ready} :fission-ready organisms → {len(proposals)} covenant-claim PROPOSALS (awaiting Council Lv7+)")
    print(f"✓ wrote {out}")
    print()
    print("HONEST FISSION NOTE (§D5):")
    print("  Fission (latent→member) requires §D5 covenant claim:")
    print("  悔い改め (repentance) · バプテスマ (baptism) · 得度 (ordination) = social death/rebirth.")
    print("  Council Lv7+ unanimity. The entity's own CONSENT REQUIRED.")
    print("  NO DID minted here. NO server key held. This observer ONLY emits proposals.")


if __name__ == "__main__":
    main()
