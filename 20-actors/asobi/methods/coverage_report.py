#!/usr/bin/env python3
"""asobi 遊び — freed-time COVERAGE report (ADR-2606073200).

Honest coverage of the play/expression graph: by access category, by work medium, by
practice domain, by venue kind, by enclosure kind — with a gap map naming thin/missing
buckets. Coverage of all culture is ~0 by design (a bounded :representative seed); this
makes the real covered backbone measurable and names the next wave.

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

MEDIA = [":music", ":film", ":text", ":game", ":stage", ":visual", ":sport-form"]
DOMAINS = [":sport", ":music", ":dance", ":stage", ":craft", ":game", ":letters"]
VENUES = [":public-library", ":public-park", ":museum", ":hall", ":field",
          ":makerspace", ":online-commons", ":enclosed-venue"]
ENCLOSURES = [":paywall", ":attention-platform", ":ticketing-lock",
              ":copyright-lock", ":geo-block"]
ACCESS = [":public-domain", ":open-license", ":free-gratis", ":ticketed",
          ":paywalled", ":proprietary"]
THIN = 2


def report(nodes: dict, edges: list) -> str:
    works = [n for n in nodes.values() if n.get(":organism/kind") == ":work"]
    pracs = [n for n in nodes.values() if n.get(":organism/kind") == ":practice"]
    venues = [n for n in nodes.values() if n.get(":organism/kind") == ":venue"]
    encs = [n for n in nodes.values() if n.get(":organism/kind") == ":enclosure"]

    med_c = Counter(w.get(":work/medium") for w in works)
    dom_c = Counter(p.get(":practice/domain") for p in pracs)
    ven_c = Counter(v.get(":venue/kind") for v in venues)
    enc_c = Counter(e.get(":enclosure/kind") for e in encs)
    acc_c = Counter(w.get(":work/access") for w in works)

    L = []
    L.append("# asobi 遊び — freed-time coverage report\n")
    L.append("> Honest denominator: coverage of all culture is ~0 by design (bounded seed). "
             "This names the participation backbone covered and the next-wave gaps.\n")
    L.append(f"**Seed**: {len(works)} works · {len(pracs)} practices · {len(venues)} venues · "
             f"{len(encs)} enclosures · {len(edges)} 縁\n")

    L.append("\n## Access spread (DISCLOSED facts, not verdicts)\n")
    L.append("| access | count |")
    L.append("|:--:|---:|")
    for a in ACCESS:
        L.append(f"| {a.lstrip(':')} | {acc_c.get(a, 0)} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Work-medium coverage", MEDIA, med_c)
    _bucket("Practice-domain coverage", DOMAINS, dom_c)
    _bucket("Venue-kind coverage", VENUES, ven_c)
    _bucket("Enclosure-kind coverage", ENCLOSURES, enc_c)

    missing = [b.lstrip(':') for b in MEDIA if med_c.get(b, 0) == 0] + \
              [d.lstrip(':') for d in DOMAINS if dom_c.get(d, 0) == 0] + \
              [v.lstrip(':') for v in VENUES if ven_c.get(v, 0) == 0] + \
              [e.lstrip(':') for e in ENCLOSURES if enc_c.get(e, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines (thin buckets still listed above).")
    L.append("\n---\n_asobi 遊び · ADR-2606073200 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-asobi-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"asobi coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
