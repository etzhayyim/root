#!/usr/bin/env python3
"""inochi 命 — biosphere COVERAGE report (ADR-2606073000).

Honest coverage measurement of the living-world graph: how much of the target space the
seed covers — by IUCN denominator, by realm (terrestrial/marine/freshwater), by biome,
by kingdom, and by graph connectedness — and a gap map naming what is thin/missing.

NOT a completeness claim: coverage of *all* species is ~0 by design (a bounded
:representative seed). This makes the real, useful coverage (the at-risk backbone)
measurable, and names the next wave's targets.

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

# honest external denominators for the SPECIES count
DENOMINATORS = [
    ("IUCN Red List assessed species (~)", 169_000),
    ("IUCN threatened species (~)", 47_000),
    ("Described species (~)", 2_160_000),
    ("Estimated species on Earth (~)", 8_700_000),
]

REALMS = [":terrestrial", ":marine", ":freshwater"]
BIOMES = [":tropical-forest", ":boreal-forest", ":coral-reef", ":mangrove",
          ":tundra", ":grassland", ":wetland", ":pelagic"]
KINGDOMS = [":animalia", ":plantae", ":fungi", ":chromista", ":bacteria"]
PRESSURE_KINDS = [":habitat-loss", ":overharvest", ":climate-forcing",
                  ":pollution", ":invasive", ":wildlife-trade"]
THIN = 2  # a bucket with < THIN members is flagged thin


def report(nodes: dict, edges: list) -> str:
    species = [n for n in nodes.values() if n.get(":organism/kind") == ":species"]
    ecos = [n for n in nodes.values() if n.get(":organism/kind") in (":ecosystem", ":biome")]
    press = [n for n in nodes.values() if n.get(":organism/kind") == ":pressure"]

    realm_c = Counter(e.get(":eco/realm") for e in ecos)
    biome_c = Counter(e.get(":eco/biome") for e in ecos)
    king_c = Counter(s.get(":taxon/kingdom") for s in species)
    iucn_c = Counter(s.get(":taxon/iucn") for s in species)
    pk_c = Counter(p.get(":pressure/kind") for p in press)

    L = []
    L.append("# inochi 命 — biosphere coverage report\n")
    L.append("> Honest denominator: coverage of all life is ~0 by design (bounded seed). "
             "This names the at-risk backbone covered and the next-wave gaps.\n")
    L.append(f"**Seed**: {len(species)} species · {len(ecos)} ecosystems/biomes · "
             f"{len(press)} pressures · {len(edges)} 縁\n")

    L.append("\n## Species coverage vs denominators\n")
    L.append("| denominator | count | seed | fraction |")
    L.append("|---|---:|---:|---:|")
    for name, denom in DENOMINATORS:
        L.append(f"| {name} | {denom:,} | {len(species)} | {len(species)/denom:.2e} |")

    L.append("\n## IUCN category spread (DISCLOSED facts, not verdicts)\n")
    L.append("| category | count |")
    L.append("|:--:|---:|")
    for cat in [":EX", ":EW", ":CR", ":EN", ":VU", ":NT", ":LC", ":DD"]:
        L.append(f"| {cat.lstrip(':')} | {iucn_c.get(cat, 0)} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Realm coverage", REALMS, realm_c)
    _bucket("Biome coverage", BIOMES, biome_c)
    _bucket("Kingdom coverage", KINGDOMS, king_c)
    _bucket("Pressure-kind coverage", PRESSURE_KINDS, pk_c)

    missing = [b.lstrip(':') for b in BIOMES if biome_c.get(b, 0) == 0] + \
              [k.lstrip(':') for k in KINGDOMS if king_c.get(k, 0) == 0] + \
              [p.lstrip(':') for p in PRESSURE_KINDS if pk_c.get(p, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines (thin buckets still listed above).")
    L.append("\n---\n_inochi 命 · ADR-2606073000 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-biosphere-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"inochi coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
