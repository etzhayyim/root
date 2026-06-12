#!/usr/bin/env python3
"""kaiyaku 解約 — edge-primary tie-burden analyzer over the member's 縁-ledger.

ADR-2606112201. Reads a kotoba-EDN 縁-ledger (:svc/* + :member/* nodes, :en/* 縁) and
surfaces — per TIE, never per member — where unused paid ties (sub-scriptions, dormant
accounts, recurring card charges) accumulate burden, routed to RELEASE (縁切り = the
member severing their OWN unused service ties), with a dependency cascade-guard.

CONSTITUTIONAL (read before any change):
  G2 — edge-primary. The severance decision lives ONLY on the :en/* tie (burden =
    monthly cost × unused fraction + dormancy, computed on READ). There is no
    per-member score, no score-of-soul, no "toxic person" rating (反個人主義).
  G1 — member-principal, own ties only. The ledger is the MEMBER's own service ties
    (synthetic demo seed at R0); never a third party's, never another person.
  N1 — human relationships are NOT in this ledger. :en/to is always a SERVICE.
  G8 — honesty: recommendations mirror the disclosed organizer thresholds
    (ADR usageScore<20 ∧ cost>500 → :sever; <50 → :review); notice/penalty are
    surfaced as cost-of-severance, never advised around.

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t  # keep keywords as ":ns/name" strings
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text: str):
    return _parse(_tokens(text))


MEMBER_TIE_KINDS = {":subscribes", ":holds-account", ":recurring-charge"}
DEPENDENCY_KINDS = {":depends-on"}

# disclosed organizer thresholds (organizer CLAUDE.md monthly analysis — mirrored, not invented)
SEVER_USAGE = 20
SEVER_COST_JPY = 500
REVIEW_USAGE = 50
# dormant-account thresholds (cost-free :holds-account ties)
DORMANT_SEVER_DAYS = 365
DORMANT_REVIEW_DAYS = 180


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a 縁-ledger EDN graph."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":svc/id" in f:
            nodes[f[":svc/id"]] = f
        elif ":member/id" in f:
            nodes[f[":member/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def _dependents(edges: list) -> dict:
    """svc-id → [svc-ids that depend on it] (SSO / payment-method cascade inputs)."""
    deps = defaultdict(list)
    for e in edges:
        if e.get(":en/kind") in DEPENDENCY_KINDS:
            deps[e[":en/to"]].append(e[":en/from"])
    return deps


def _burden(tie: dict) -> float:
    """Tie burden, computed on read (G2): paid waste + dormancy pressure."""
    cost = float(tie.get(":en/monthly-cost-jpy", 0) or 0)
    usage = float(tie.get(":en/usage-score", 0) or 0)
    waste = cost * (1.0 - min(usage, 100.0) / 100.0)
    dormancy = min(float(tie.get(":en/last-used-days", 0) or 0), 1000.0) / 1000.0
    return round(waste + dormancy, 4)


def _recommend(tie: dict) -> str:
    cost = float(tie.get(":en/monthly-cost-jpy", 0) or 0)
    usage = float(tie.get(":en/usage-score", 0) or 0)
    last = float(tie.get(":en/last-used-days", 0) or 0)
    kind = tie.get(":en/kind")
    if kind == ":recurring-charge" and usage == 0:
        return ":review" if cost == 0 else ":sever"  # unrecognized live charge
    if cost > 0:  # paid tie → disclosed organizer thresholds
        if usage < SEVER_USAGE and cost > SEVER_COST_JPY:
            return ":sever"
        if usage < REVIEW_USAGE:
            return ":review"
        return ":keep"
    # cost-free account → dormancy rule (退会候補)
    if last >= DORMANT_SEVER_DAYS:
        return ":sever"
    if last >= DORMANT_REVIEW_DAYS:
        return ":review"
    return ":keep"


def analyze(nodes: dict, edges: list):
    """Per-tie readout (transient — G2): burden, recommendation, cascade-guard.

    A :sever on a service with dependents is DOWNGRADED to :review-cascade — the
    dependency must be re-homed first (依存 detection); kaiyaku never auto-severs
    a tie other ties stand on.
    """
    deps = _dependents(edges)
    ties = []
    for e in edges:
        if e.get(":en/kind") not in MEMBER_TIE_KINDS:
            continue
        svc = nodes.get(e[":en/to"], {})
        rec = _recommend(e)
        dependents = sorted(deps.get(e[":en/to"], []))
        if rec == ":sever" and dependents:
            rec = ":review-cascade"
        ties.append({
            "member": e[":en/from"],
            "svc": e[":en/to"],
            "svc_label": svc.get(":svc/label", e[":en/to"]),
            "kind": e.get(":en/kind"),
            "monthly_cost_jpy": float(e.get(":en/monthly-cost-jpy", 0) or 0),
            "usage_score": float(e.get(":en/usage-score", 0) or 0),
            "last_used_days": float(e.get(":en/last-used-days", 0) or 0),
            "burden": _burden(e),
            "recommendation": rec,
            "dependents": dependents,
            "notice_days": svc.get(":svc/notice-days", 0),
            "penalty_jpy": svc.get(":svc/penalty-jpy", 0),
        })
    ties.sort(key=lambda t: (-t["burden"], t["svc"]))

    total = sum(t["monthly_cost_jpy"] for t in ties)
    recoverable = sum(t["monthly_cost_jpy"] for t in ties if t["recommendation"] == ":sever")
    by_rec = defaultdict(int)
    for t in ties:
        by_rec[t["recommendation"]] += 1
    return {
        "ties": ties,
        "total_monthly_jpy": round(total, 2),
        "recoverable_monthly_jpy": round(recoverable, 2),
        "counts": dict(sorted(by_rec.items())),
    }


def report(res: dict) -> str:
    L = ["# kaiyaku 縁切り readout (transient — computed on read, G2)", ""]
    L.append(f"- ties: {len(res['ties'])} · total ¥{res['total_monthly_jpy']:,.0f}/mo · "
             f"recoverable ¥{res['recoverable_monthly_jpy']:,.0f}/mo")
    L.append(f"- counts: {res['counts']}")
    L.append("")
    L.append("| svc | kind | ¥/mo | usage | burden | recommendation | cost-of-severance |")
    L.append("|---|---|---|---|---|---|---|")
    for t in res["ties"]:
        sev = (f"notice {t['notice_days']}d / penalty ¥{t['penalty_jpy']:,}"
               if (t["notice_days"] or t["penalty_jpy"]) else "—")
        L.append(f"| {t['svc_label']} | {t['kind']} | {t['monthly_cost_jpy']:,.0f} "
                 f"| {t['usage_score']:.0f} | {t['burden']:.1f} | {t['recommendation']}"
                 f"{' (deps: ' + ', '.join(t['dependents']) + ')' if t['dependents'] else ''} | {sev} |")
    L.append("")
    L.append("severance is PLANNED only (plan.py); execution is member-sig + dry-run + "
             "Council-gated (G5/G6).")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-en-ledger.kotoba.edn"
    out = here / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    out.mkdir(parents=True, exist_ok=True)
    (out / "enkiri-readout.md").write_text(report(res), encoding="utf-8")
    print(f"kaiyaku: {len(res['ties'])} ties · recoverable ¥{res['recoverable_monthly_jpy']:,.0f}/mo "
          f"→ {out / 'enkiri-readout.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
