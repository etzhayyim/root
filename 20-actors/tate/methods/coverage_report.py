#!/usr/bin/env python3
"""tate 盾 — honest jurisdiction-coverage report (G10, ADR-2606112400).

The worldwide expansion covers a REPRESENTATIVE subset of legal systems; pretending
otherwise would be the dishonest failure mode. This report makes the gap measurable
(the inochi/uchiwake coverage-honesty pattern): per-jurisdiction clause-pattern +
procedure counts, the covered/uncovered ratio against the ~193 UN member states, and
a NAMED gap list that doubles as the ingest worklist for the next wave.

Pure stdlib — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 coverage_report.py [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from terms_scan import load_patterns, HERE  # noqa: E402
from respond_plan import load_procs, load_jurisdictions  # noqa: E402

UN_MEMBER_STATES = 193  # disclosed denominator (the EU bloc entry covers instruments, not 27 states)

# named gaps = the next-wave worklist (not exhaustive — that is the point)
NAMED_GAPS = [
    ":fr / :it / :es … EU 加盟国の国内法 (現状は EU 越境 instruments のみ)",
    ":us は州レベル未分解 (small-claims 上限・answer 期限は州差が本体)",
    ":kr :cn :tw :in :br :au :ca :sg — 主要管轄ゼロ",
    "刑事手続は全管轄でスコープ外 (N6 — 即時弁護士照会のみ)",
    "労働審判・家事・倒産など民事の専門トラック未収載",
]


def coverage():
    patterns = load_patterns()
    procs = load_procs()
    juris = load_jurisdictions()
    pat_by_j = defaultdict(int)
    proc_by_j = defaultdict(int)
    for p in patterns:
        pat_by_j[p.get(":clause/jurisdiction", ":jp")] += 1
    for p in procs:
        proc_by_j[p.get(":proc/jurisdiction", ":jp")] += 1
    covered = sorted(juris.keys())
    return {
        "jurisdictions": covered,
        "patterns_by_jurisdiction": dict(sorted(pat_by_j.items())),
        "procedures_by_jurisdiction": dict(sorted(proc_by_j.items())),
        "covered_count": len(covered),
        "un_member_states": UN_MEMBER_STATES,
        "coverage_ratio": round(len(covered) / UN_MEMBER_STATES, 4),
        "named_gaps": list(NAMED_GAPS),
    }


def report(cov: dict) -> str:
    L = ["# tate 盾 — jurisdiction coverage (honest — G10)", ""]
    L.append(f"- covered: {cov['covered_count']} legal systems "
             f"({', '.join(cov['jurisdictions'])}) of ~{cov['un_member_states']} UN states "
             f"→ ratio ≈ {cov['coverage_ratio']:.2%} (低いのは仕様 — 推測より空白)")
    L.append("")
    L.append("| juris | clause patterns | procedures |")
    L.append("|---|---|---|")
    for j in cov["jurisdictions"]:
        L.append(f"| {j} | {cov['patterns_by_jurisdiction'].get(j, 0)} "
                 f"| {cov['procedures_by_jurisdiction'].get(j, 0)} |")
    L.append("")
    L.append("## Named gaps (next-wave worklist)")
    for g in cov["named_gaps"]:
        L.append(f"- {g}")
    L.append("")
    L.append("未カバー管轄の通知は :unknown-jurisdiction に honest degrade し、"
             "現地法を推測せず証拠保全 + 専門家照会のみを案内する (respond_plan G10)。")
    return "\n".join(L) + "\n"


def main(argv):
    out = HERE / "out"
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    cov = coverage()
    out.mkdir(parents=True, exist_ok=True)
    (out / "coverage-report.md").write_text(report(cov), encoding="utf-8")
    print(f"tate: {cov['covered_count']}/{cov['un_member_states']} jurisdictions "
          f"({cov['coverage_ratio']:.2%}) → {out / 'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
