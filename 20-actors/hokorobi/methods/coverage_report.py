#!/usr/bin/env python3
"""hokorobi 綻び — systemic finance-risk COVERAGE report (ADR-2606073400).

Honest coverage of the finance-risk graph: by institution sector, by systemic-importance
tier, by risk-kind, by bearer-kind — with a gap map naming thin/missing buckets. Coverage of
all institutions is ~0 by design (a bounded :representative seed); this makes the covered
systemic backbone measurable and names the next wave.

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

# honest external denominators for the institution count
DENOMINATORS = [
    ("FSB G-SIBs (~)", 29),
    ("IAIS internationally-active insurer groups (~)", 60),
    ("Globally significant banks (~)", 1_000),
    ("All licensed banks worldwide (~)", 25_000),
]

SECTORS = [":bank", ":insurer", ":reinsurer", ":pension-fund", ":ccp", ":shadow-bank"]
SII = [":g-sib", ":d-sib", ":large", ":mid", ":small"]
RISK_KINDS = [":leverage", ":maturity-mismatch", ":interconnection",
              ":protection-gap", ":underfunding", ":concentration", ":liquidity"]
BEARERS = [":depositors", ":pensioners", ":policyholders", ":taxpayers", ":real-economy"]
THIN = 2


def report(nodes: dict, edges: list) -> str:
    insts = [n for n in nodes.values() if n.get(":organism/kind") == ":institution"]
    risks = [n for n in nodes.values() if n.get(":organism/kind") == ":risk"]
    bears = [n for n in nodes.values() if n.get(":organism/kind") == ":bearer"]

    sec_c = Counter(i.get(":inst/sector") for i in insts)
    sii_c = Counter(i.get(":inst/sii") for i in insts)
    rk_c = Counter(r.get(":risk/kind") for r in risks)
    br_c = Counter(b.get(":bearer/kind") for b in bears)

    L = []
    L.append("# hokorobi 綻び — systemic finance-risk coverage report\n")
    L.append("> Honest denominator: coverage of all institutions is ~0 by design (bounded "
             "seed). This names the systemic backbone covered and the next-wave gaps.\n")
    L.append(f"**Seed**: {len(insts)} institutions · {len(risks)} risk-sources · "
             f"{len(bears)} bearers · {len(edges)} 縁\n")

    L.append("\n## Institution coverage vs denominators\n")
    L.append("| denominator | count | seed | fraction |")
    L.append("|---|---:|---:|---:|")
    for name, denom in DENOMINATORS:
        L.append(f"| {name} | {denom:,} | {len(insts)} | {len(insts)/denom:.2e} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Sector coverage", SECTORS, sec_c)
    _bucket("Systemic-importance tier coverage (DISCLOSED)", SII, sii_c)
    _bucket("Risk-kind coverage", RISK_KINDS, rk_c)
    _bucket("Bearer-kind coverage", BEARERS, br_c)

    missing = [s.lstrip(':') for s in SECTORS if sec_c.get(s, 0) == 0] + \
              [r.lstrip(':') for r in RISK_KINDS if rk_c.get(r, 0) == 0] + \
              [b.lstrip(':') for b in BEARERS if br_c.get(b, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines (thin buckets still listed above).")
    L.append("\n---\n_hokorobi 綻び · ADR-2606073400 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-finrisk-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"hokorobi coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
