"""analyze.py — 高札 (kosatsu) end-to-end dry-run → methods/out/intel-report.md. ADR-2606072000.

Loads the :representative seed, weaves the competing-claim graph, and renders an aggregate-first,
NON-adjudicating Markdown report whose headline is the DIVERGENCE view: where jurisdictions
disagree about a designation. Every line is an ATTRIBUTED mirror ('asserter A listed S'), never
a verdict of ours. Writes nothing live (G8) — output is a local file only.

Stdlib only. Deterministic.
"""

from __future__ import annotations

import pathlib

from _edn import load_edn
from weave import report, weave

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed-designation-graph.kotoba.edn"
OUT = pathlib.Path(__file__).resolve().parent / "out" / "intel-report.md"

DISCLAIMER = (
    "> **Mirror, not a verdict.** 高札 (kosatsu) records, ATTRIBUTED, what each PUBLIC authority "
    "itself posted (\"asserter A listed subject S under program P as-of T\"). etzhayyim asserts "
    "nothing about any subject and authors no designation of its own. A designation is "
    "**asserter-relative** — the *divergence* view below is the neutral, computed fact that what "
    "counts as a sanctionable act varies by political position. This is an accountability / "
    "due-process-visibility MAP, **never a target-list** and never legal advice."
)


def render(g: dict) -> str:
    r = report(g)
    ai = r["agreement_index"]
    L = []
    L.append("# 高札 (kosatsu) — crime/sanctions competing-claim report\n")
    L.append(DISCLAIMER + "\n")
    L.append(f"authorities **{r['authority_count']}** · subjects **{r['subject_count']}** · "
             f"designation events **{r['designation_count']}**\n")
    L.append(f"**contested {ai['contested']}** · single-asserter {ai['single_asserter']} · "
             f"unanimous {ai['unanimous']} · contested-ratio **{ai['contested_ratio']}**\n")

    L.append("## Divergence — where jurisdictions disagree (the political-stance signal)\n")
    L.append("- **contested** = a jurisdiction actively *delisted* what another still lists "
             "(real disagreement on current status).")
    L.append("- **coverage-split** = listed by some jurisdictions while others never designated it "
             "(silence is reported, never inferred as dissent).\n")
    L.append("| subject | class | coverage-split | listing | delisted | silent |")
    L.append("|---|---|---|---|---|---|")
    for d in r["divergence"]:
        L.append(f"| {d['subject']} | **{d['class']}** | {'yes' if d.get('coverage_split') else '—'} | "
                 f"{', '.join(d['listing']) or '—'} | {', '.join(d['delisted']) or '—'} | "
                 f"{', '.join(d['silent']) or '—'} |")
    L.append("")

    L.append("## Delisting timeline — as-of history (append-only, non-eschatological)\n")
    if r["delisting_timeline"]:
        for d in r["delisting_timeline"]:
            L.append(f"- **{d['asserter']}** delisted `{d['subject']}` on {d['lifted_at']} "
                     f"(originally listed {d['posted_at']}, program {d['program']}). "
                     f"The original `:listed` event is retained, never deleted.")
    else:
        L.append("- (none in seed)")
    L.append("")

    L.append("## By authority — currently-listed subjects (as-of)\n")
    for a in r["by_authority"]:
        L.append(f"- **{a['label']}** ({a['jurisdiction']}): {a['listed_subjects']} listed")
    L.append("")

    L.append("## Co-designation — subjects sharing an asserter+program (network)\n")
    if r["co_designation"]:
        for c in r["co_designation"]:
            L.append(f"- {c['asserter']} / {c['program']}: {c['count']} subjects {c['subjects']}")
    else:
        L.append("- (no shared program with >1 subject in seed)")
    L.append("")

    integ = r["integrity"]
    L.append(f"## Integrity\n\n- dangling refs: **{integ['dangling_count']}**\n")
    L.append("---\n")
    L.append("Honest R0: `:representative` seed (synthetic ids/labels), offline analyzer only. "
             "Live full-universe ingest (OFAC SDN / EU / UN / UK OFSI / JP-MOF / Interpol public "
             "notices) + any outward publication are Council Lv6+ + operator + member-signature "
             "gated (G8). Murakumo-only narration (G7). No-server-key (ADR-2605231525).")
    return "\n".join(L) + "\n"


def main() -> str:
    seed = load_edn(SEED)
    g = weave(seed)
    md = render(g)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    return str(OUT)


if __name__ == "__main__":
    path = main()
    print(f"wrote {path}")
