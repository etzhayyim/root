#!/usr/bin/env python3
"""aburi 炙り — tracker-exposure COVERAGE report (ADR-2606161630).

Honest coverage of the exposure graph: by surface kind, by permission kind, by collector kind, by
collector catalogue (provenance), by data-type kind — with a gap map naming thin/missing buckets.
Coverage of all surfaces/collectors is ~0 by design (a bounded :representative public seed); this
makes the covered backbone measurable and names the next wave (more surfaces, more SDKs).

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

# honest external denominators (public scale context — NOT measurements of a person)
DENOMINATORS = [
    ("Trackers catalogued by Exodus Privacy (public, ~)", "hundreds"),
    ("Apps Exodus has analysed (public, ~)", "100,000+"),
    ("Median trackers in a free Android app (research, ~)", "several"),
    ("Collectors modelled (this seed)", 14),
]

SURFACE_KINDS = [":search", ":social", ":app-store", ":mobile-app", ":website", ":os"]
PERMISSION_KINDS = [":ad-id", ":precise-location", ":location", ":contacts", ":camera",
                    ":microphone", ":photos", ":browsing-history", ":purchase-history",
                    ":app-usage", ":health", ":tos-data-sharing", ":ad-personalization"]
COLLECTOR_KINDS = [":ad-network", ":dsp", ":ssp", ":exchange", ":data-broker",
                   ":analytics", ":tracker-sdk"]
CATALOGS = [":exodus", ":apple-privacy", ":play-data-safety", ":sellers-json", ":iab"]
DATATYPE_KINDS = [":precise-location", ":coarse-location", ":device-id", ":contacts",
                  ":browsing", ":purchases", ":app-usage", ":identifiers", ":photos",
                  ":health-fitness"]
THIN = 2


def report(nodes: dict, edges: list) -> str:
    surfs = [n for n in nodes.values() if n.get(":organism/kind") == ":surface"]
    perms = [n for n in nodes.values() if n.get(":organism/kind") == ":permission"]
    cols = [n for n in nodes.values() if n.get(":organism/kind") == ":collector"]
    dts = [n for n in nodes.values() if n.get(":organism/kind") == ":datatype"]

    surf_c = Counter(s.get(":surface/kind") for s in surfs)
    perm_c = Counter(p.get(":permission/kind") for p in perms)
    col_c = Counter(c.get(":collector/kind") for c in cols)
    cat_c = Counter(c.get(":collector/catalog") for c in cols)
    dt_c = Counter(d.get(":datatype/kind") for d in dts)

    L = []
    L.append("# aburi 炙り — tracker-exposure coverage report\n")
    L.append("> Honest denominator: coverage of all real surfaces/collectors is ~0 by design "
             "(bounded REPRESENTATIVE public seed; G1 = own-data, no real person). This names the "
             "covered backbone and the next-wave gaps (more surfaces, more catalogued SDKs).\n")
    L.append(f"**Seed**: {len(surfs)} surfaces · {len(perms)} permissions · {len(cols)} collectors "
             f"· {len(dts)} data-types · {len(edges)} 縁\n")

    L.append("\n## Scale context (public catalogues — NOT measurements of a person, G1/N3)\n")
    L.append("| denominator | value |")
    L.append("|---|---:|")
    for name, val in DENOMINATORS:
        L.append(f"| {name} | {val} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Surface-kind coverage", SURFACE_KINDS, surf_c)
    _bucket("Permission-kind coverage", PERMISSION_KINDS, perm_c)
    _bucket("Collector-kind coverage", COLLECTOR_KINDS, col_c)
    _bucket("Collector-catalogue coverage (provenance, G5)", CATALOGS, cat_c)
    _bucket("Data-type-kind coverage", DATATYPE_KINDS, dt_c)

    missing = [k.lstrip(':') for k in SURFACE_KINDS if surf_c.get(k, 0) == 0] + \
              [k.lstrip(':') for k in PERMISSION_KINDS if perm_c.get(k, 0) == 0] + \
              [k.lstrip(':') for k in COLLECTOR_KINDS if col_c.get(k, 0) == 0] + \
              [k.lstrip(':') for k in DATATYPE_KINDS if dt_c.get(k, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines (thin buckets still listed above).")
    L.append("\n---\n_aburi 炙り · ADR-2606161630 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-tracker-exposure.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"aburi coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
