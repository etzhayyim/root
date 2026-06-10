#!/usr/bin/env python3
"""tsumugi 紡ぎ — scale+banner COVERAGE report.

HONEST FRAMING: real-world coverage is ~0 BY DESIGN (bounded :representative
sample); this measures the *exercised structure* and *names gaps*, it is NOT
real-world coverage. Aggregate-only, no per-person data. Mirror, non-adjudicating.

stdlib only (reuses analyze_scale's EDN loader). Usage:
    python3 coverage_scale.py [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
from analyze_scale import read_edn, SCALES, COLLECTIVE_KINDS, SECTORS  # noqa: E402

DEFAULT_SCALE_SEED = ACTOR_DIR / "data" / "seed-scale-power.kotoba.edn"
DEFAULT_BANNER_SEED = ACTOR_DIR / "data" / "seed-banner.kotoba.edn"

# A DENOMINATORS table as clearly-labelled APPROXIMATE constants.
DENOMINATORS = {
    "Countries (~sovereign states)": 195,
    "JP basic municipalities": 1741,
    "World municipalities (order of magnitude)": 100_000,
    "JP corporations (approx)": 3_800_000,
    "World listed companies (approx)": 50_000,
    "Universities (approx)": 25_000,
}

def load_data(scale_seed: str | pathlib.Path = DEFAULT_SCALE_SEED,
              banner_seed: str | pathlib.Path = DEFAULT_BANNER_SEED):
    scale_text = pathlib.Path(scale_seed).read_text(encoding="utf-8")
    banner_text = pathlib.Path(banner_seed).read_text(encoding="utf-8")
    scale_records = read_edn(scale_text)
    banner_records = read_edn(banner_text)

    nodes, ties = {}, []
    if scale_records:
        for r in scale_records:
            if not isinstance(r, dict): continue
            if ":pwr/id" in r:
                nodes[r[":pwr/id"]] = r
            elif ":tie/id" in r:
                ties.append(r)

    banners, ents, flies = {}, {}, []
    if banner_records:
        for r in banner_records:
            if not isinstance(r, dict): continue
            if ":banner/id" in r:
                banners[r[":banner/id"]] = r
            elif ":ent/id" in r:
                ents[r[":ent/id"]] = r
            elif ":flies/id" in r:
                flies.append(r)

    return nodes, ties, banners, ents, flies

def compute(nodes, ties, banners, ents, flies) -> dict:
    localities = set()
    scale_counts = Counter()
    kind_counts = Counter()
    sector_counts = Counter()
    countries = set()

    num_jp_muni = 0
    num_jp_corp = 0
    num_world_listed = 0
    num_univ = 0

    for n in nodes.values():
        sec = n.get(":pwr/sector")
        loc = n.get(":pwr/locality", "")

        if loc:
            localities.add(loc)
            countries.add(loc.split(".")[0])
            if loc.startswith("jp.") and len(loc.split(".")) >= 3:
                num_jp_muni += 1

        if sc := n.get(":pwr/scale"):
            scale_counts[sc] += 1
        if ck := n.get(":pwr/collective-kind"):
            kind_counts[ck] += 1
        if sec:
            sector_counts[sec] += 1
            if sec == ":san":
                num_world_listed += 1
                if loc.startswith("jp"):
                    num_jp_corp += 1
            elif sec == ":gaku":
                num_univ += 1

    c_countries = len(countries)
    num_world_muni = len(localities)

    coverage_stats = {
        "Countries (~sovereign states)": c_countries,
        "JP basic municipalities": len(set(loc for loc in localities if loc.startswith("jp.") and len(loc.split(".")) >= 3)),
        "World municipalities (order of magnitude)": num_world_muni,
        "JP corporations (approx)": num_jp_corp,
        "World listed companies (approx)": num_world_listed,
        "Universities (approx)": num_univ,
    }

    coverages = {}
    for k, denom in DENOMINATORS.items():
        num = coverage_stats.get(k, 0)
        coverages[k] = {"numerator": num, "denominator": denom, "percent": (num / denom) * 100 if denom else 0}

    return {
        "raw": {
            "nodes": len(nodes),
            "ties": len(ties),
            "distinct_localities": len(localities),
            "banners": len(banners),
            "ents": len(ents),
            "flies": len(flies),
        },
        "per_scale": {
            "exercised": [s for s in SCALES if scale_counts[s] > 0],
            "missing": [s for s in SCALES if scale_counts[s] == 0]
        },
        "per_kind": {
            "exercised": [k for k in COLLECTIVE_KINDS if kind_counts[k] > 0],
            "missing": [k for k in COLLECTIVE_KINDS if kind_counts[k] == 0]
        },
        "per_sector": {
            "exercised": [s for s in SECTORS if sector_counts[s] > 0],
            "missing": [s for s in SECTORS if sector_counts[s] == 0]
        },
        "per_country": {
            "countries": sorted(list(countries)),
        },
        "coverages": coverages
    }

def render(c: dict) -> str:
    lines = [
        "# tsumugi 紡ぎ — Scale & Banner Coverage Report",
        "",
        "> HONEST FRAMING: real-world coverage is ~0 BY DESIGN (bounded `:representative`",
        "> sample); this measures the *exercised structure* and *names gaps*, it is NOT",
        "> real-world coverage. Aggregate-only, no per-person data. Mirror, non-adjudicating.",
        "",
        "## Raw Counts",
        f"- Power nodes: {c['raw']['nodes']}",
        f"- Power ties: {c['raw']['ties']}",
        f"- Distinct localities: {c['raw']['distinct_localities']}",
        f"- Banners: {c['raw']['banners']}",
        f"- Entities: {c['raw']['ents']}",
        f"- Flies (alignments): {c['raw']['flies']}",
        "",
        "## Structural Dimensions (Gap Map)",
        f"- **Scales Exercised**: {', '.join(c['per_scale']['exercised'])}",
        f"- **Scales MISSING**: {', '.join(c['per_scale']['missing']) if c['per_scale']['missing'] else 'None (All exercised)'}",
        f"- **Collective Kinds Exercised**: {', '.join(c['per_kind']['exercised'])}",
        f"- **Collective Kinds MISSING**: {', '.join(c['per_kind']['missing']) if c['per_kind']['missing'] else 'None'}",
        f"- **Sectors Exercised**: {', '.join(c['per_sector']['exercised'])}",
        f"- **Sectors MISSING**: {', '.join(c['per_sector']['missing']) if c['per_sector']['missing'] else 'None'}",
        "",
        "## Geographic Coverage",
        f"- **Countries Exercised**: {', '.join(c['per_country']['countries'])}",
        "",
        "## Denominators & Contextual Coverage",
    ]
    for k, v in c["coverages"].items():
        lines.append(f"- {k}: {v['numerator']} / ~{v['denominator']:,} ({v['percent']:.4f}%)")
    return "\n".join(lines) + "\n"

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default="out")
    args = parser.parse_args()

    nodes, ties, banners, ents, flies = load_data()
    c = compute(nodes, ties, banners, ents, flies)

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    report_path = outdir / "coverage-report.md"
    report_path.write_text(render(c), encoding="utf-8")

    country_cov = c['coverages']['Countries (~sovereign states)']['percent']
    print(f"Coverage scale report written to {report_path}: {c['raw']['nodes']} nodes, {c['raw']['banners']} banners, {country_cov:.4f}% country cov")

if __name__ == "__main__":
    main()
