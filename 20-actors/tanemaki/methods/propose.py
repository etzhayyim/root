#!/usr/bin/env python3
"""tanemaki 種蒔き — public DD scorecard renderer + ADVISORY grant-proposal builder.

ADR-2606122001. Two artefacts, both PUBLIC and both structurally decision-free:

  render_scorecard(org)  — the 参考意見 card shown in the voting UI: screens, rubric,
    evidence sources, fit, route. Content-addressed (CIDv1+SHA-256) so anyone can verify the
    bytes the voters saw are the bytes tanemaki published (G4).

  build_proposal(org, …) — an UNSENT `com.etzhayyim.tanemaki.grantProposal` record feeding the
    GrantGovernor propose() lane (ADR-2605192145). The record is structurally advisory:
    `advisory: true`, `bindsFund: false`, `decidedBy: "1-sbt-1-vote"`. It REFUSES (raises) for
    any org whose route is not :propose — a screen-conflicting or under-evidenced org cannot
    be drafted into a proposal (G1/G5, the action-layer tripwire). Instruments outside the G2
    allowlist (equity/debt/convertible/revenue-share/carry/exit/…) raise. Free-text
    justifications are scanned for investment-return language and rejected (G2).

Actually SUBMITTING a proposal on-chain is a G7-gated member/operator step — tanemaki holds no
key and no vote weight (no-server-key, ADR-2605231525).

Pure stdlib. Usage:
    python3 propose.py --org org.osslib [--amount-usdc 25000] [--instrument grant]
"""
from __future__ import annotations
import sys, re, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, recommend_route, criteria  # noqa: E402
from cid import cidv1_raw, sha256_hex  # noqa: E402

# G2 — the disbursement allowlist (mirrors :instrument/allowlist in the schema + fuchi G1).
# The investment-instrument vocabulary is NOT a low-scoring option; it is unrepresentable.
ALLOWED_INSTRUMENTS = (":grant", ":milestone-escrow", ":in-kind")
FORBIDDEN_INSTRUMENTS = (":equity", ":debt", ":convertible", ":revenue-share",
                         ":profit-claim", ":carry", ":dividend", ":exit")

# G2 — investment-return language never enters a proposal justification
_INVESTMENT_RE = re.compile(
    r"equity|出資|持分|配当|株式|新株|転換社債|リターン|投資回収|ROI|内部収益|IRR|"
    r"revenue\s*share|profit\s*shar|carried\s*interest|carry|exit|キャピタルゲイン|利回り",
    re.IGNORECASE)


def assert_instrument(instrument: str) -> str:
    """G2 — raises on any investment-shaped instrument (the fund GIVES, never INVESTS)."""
    k = instrument if instrument.startswith(":") else ":" + instrument
    if k in FORBIDDEN_INSTRUMENTS:
        raise AssertionError(
            f"G2 VIOLATION: {k} is an investment instrument — unrepresentable in the Public "
            f"Fund (grant / milestone-escrow / in-kind only; ADR-2606052300 G1 pattern)")
    if k not in ALLOWED_INSTRUMENTS:
        raise AssertionError(f"unknown instrument {k}; allowed: {ALLOWED_INSTRUMENTS}")
    return k


def assert_no_investment_language(text: str) -> str:
    """G2 — rejects investment-return language injected into a free-text justification."""
    m = _INVESTMENT_RE.search(text or "")
    if m:
        raise AssertionError(
            f"G2 VIOLATION: investment-return language ({m.group(0)!r}) in a grant "
            f"justification — the Public Fund gives, it never invests")
    return text


def render_scorecard(org_id: str, nodes: dict, edges: list) -> str:
    """The PUBLIC 参考意見 card (markdown) for one org — advisory, vote-decided."""
    rec = recommend_route(org_id, nodes, edges)
    crit = criteria(nodes)
    org = nodes[org_id]
    L = []
    L.append(f"# DD scorecard — {org.get(':fs/label', org_id)}\n")
    L.append("> **参考意見 (advisory)** — this card informs the 1 SBT = 1 vote decision "
             "(GrantGovernor, ADR-2605192145); it decides nothing. Findings are DISCLOSED "
             "public facts with named sources, never verdicts (N3)."
             + (" **This org is FICTIONAL (G6 seed).**" if rec["synthetic"] else "") + "\n")
    L.append("## Hard screens (適格性 — charter anchors disclosed)\n")
    L.append("| screen | basis | finding |")
    L.append("|---|---|---|")
    for s, f in rec["screen_findings"].items():
        sn = nodes.get(s, {})
        L.append(f"| {sn.get(':screen/code', s)} {sn.get(':fs/label', '')} | "
                 f"{sn.get(':screen/basis', '—')} | {(f or ':unevaluated').lstrip(':')} |")
    L.append("\n## Weighted rubric (公開 weight × evidence)\n")
    L.append("| criterion | weight | evidence | sources |")
    L.append("|---|---:|---:|---|")
    for c in sorted(crit, key=lambda c: -float(crit[c].get(":criterion/weight", 0))):
        w = float(crit[c].get(":criterion/weight", 0))
        ev = min(1.0, rec["per_criterion"].get(c, 0.0))
        srcs = ", ".join(sorted({str(s) for s in rec["evidence"].get(c, [])})) or "—"
        L.append(f"| {nodes.get(c, {}).get(':fs/label', c)} | {w:.2f} | {ev:.2f} | {srcs} |")
    L.append(f"\n**DD fit**: {rec['dd_fit']:.3f} · **evidence coverage**: "
             f"{rec['evidence_coverage']:.0%} · **route**: `{rec['route']}`\n")
    L.append("---\n_tanemaki 種蒔き · ADR-2606122001 · advisory-only · decided by "
             "1 SBT = 1 vote._\n")
    return "\n".join(L)


def build_proposal(org_id: str, nodes: dict, edges: list, *,
                   amount_usdc_micros: int = 0, instrument: str = ":grant",
                   justification: str = "", proposer_did: str = "") -> dict:
    """An UNSENT advisory grant-proposal record for the SBT vote (G1/G2/G5/G7 enforced)."""
    rec = recommend_route(org_id, nodes, edges)
    if rec["route"] != ":propose":
        raise AssertionError(
            f"G1/G5 REFUSAL: org {org_id} routes to {rec['route']} — tanemaki cannot draft a "
            f"proposal for a screen-conflicting or under-evidenced org"
            + (f" (conflicts: {', '.join(rec['conflicts'])})" if rec["conflicts"] else "")
            + (f" (undetermined: {', '.join(rec['undetermined'])})" if rec["undetermined"] else ""))
    inst = assert_instrument(instrument)
    assert_no_investment_language(justification)
    if inst == ":milestone-escrow":
        milestones = [e[":en/to"] for e in edges
                      if e.get(":en/kind") == ":watched-by" and e.get(":en/from") == org_id]
        if not milestones:
            raise AssertionError(
                f"milestone-escrow needs :watched-by milestones for {org_id} "
                f"(attestation-gated tranches, ADR-2605192145 §4)")
    else:
        milestones = []
    card = render_scorecard(org_id, nodes, edges).encode("utf-8")
    return {
        "$type": "com.etzhayyim.tanemaki.grantProposal",
        "orgId": org_id,
        "orgSynthetic": rec["synthetic"],
        "instrument": inst,
        "amountUsdcMicros": int(amount_usdc_micros),
        "milestones": milestones,
        "justification": justification,
        "scorecardCid": cidv1_raw(card),
        "scorecardSha256": sha256_hex(card),
        "ddFit": rec["dd_fit"],
        "evidenceCoverage": rec["evidence_coverage"],
        "advisory": True,            # structurally advisory — tanemaki decides nothing (G1)
        "bindsFund": False,          # only the vote + timelock moves funds
        "decidedBy": "1-sbt-1-vote", # GrantGovernor, ADR-2605192145
        "status": "drafted-unsent",  # on-chain submission is a G7-gated member/operator step
        "proposerDid": proposer_did,
    }


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = here / "data" / "seed-stewardship-graph.kotoba.edn"
    org = argv[argv.index("--org") + 1] if "--org" in argv else "org.osslib"
    amount = int(argv[argv.index("--amount-usdc") + 1]) * 1_000_000 if "--amount-usdc" in argv else 0
    inst = argv[argv.index("--instrument") + 1] if "--instrument" in argv else "grant"
    outdir = here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    card = render_scorecard(org, nodes, edges)
    (outdir / f"scorecard-{org}.md").write_text(card, encoding="utf-8")
    prop = build_proposal(org, nodes, edges, amount_usdc_micros=amount, instrument=inst)
    (outdir / f"proposal-{org}.json").write_text(
        json.dumps(prop, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"tanemaki: scorecard + UNSENT advisory proposal for {org} → {outdir} "
          f"(decidedBy={prop['decidedBy']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
