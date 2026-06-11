#!/usr/bin/env python3
"""uchiwake 内訳 — global product bill-of-materials concentration analyzer.

ADR-2606081800. Reads a kotoba-EDN product graph (:product/* trade items keyed on
GTIN, :part/* sub-assemblies, :material/* raw inputs, :bom.edge/* parent→child
edges, :process.step/*, :logistics.leg/*, :design.ref/*, :company.ownership/*
subsidiary→parent) and emits:

  1. an AGGREGATE-FIRST product-resilience report (out/intel-report.md) — where the
     world's products concentrate onto a single raw MATERIAL, a single processing
     JURISDICTION, or a single ULTIMATE PARENT (after rolling subsidiaries up via
     GLEIF-style ownership edges), framed toward redundancy + accountability.
  2. the derived concentration datoms (out/product-criticality.kotoba.edn),
     flagged :concentration/derived true — never re-ingested as authoritative fact.

CONSTITUTIONAL framing (uchiwake G2/G4): this is a supply-chain RESILIENCE +
corporate-power TRANSPARENCY map, NEVER a target-list and NEVER a clone/counterfeit
recipe. Concentration is ranked so makers can DIVERSIFY and the public can hold
concentration accountable. uchiwake does not adjudicate.

stdlib only. Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys
import os
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uchiwake_edn import load_edn, classify, edn_str, normalize_gtin  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_SEED = ROOT / "data" / "seed-products.kotoba.edn"


def _resolve_ultimate_parent(company_id, ownership_index, _depth=0):
    """Follow :is-ultimately-consolidated-by / :is-directly-consolidated-by edges
    up to the topmost parent. Cycle/​depth guarded. Returns the input id if no edge."""
    if company_id is None or _depth > 16:
        return company_id
    parent = ownership_index.get(company_id)
    if parent is None or parent == company_id:
        return company_id
    return _resolve_ultimate_parent(parent, ownership_index, _depth + 1)


def _bom_children_index(bom):
    idx = defaultdict(list)
    for e in bom:
        idx[e.get(':bom.edge/parent')].append(e)
    return idx


def _all_materials_reachable(node_id, child_idx, _seen=None, _depth=0):
    """Recursively collect every :material/id reachable from a product/part via BOM."""
    if _seen is None:
        _seen = set()
    if node_id in _seen or _depth > 24:
        return set()
    _seen.add(node_id)
    mats = set()
    for e in child_idx.get(node_id, []):
        child = e.get(':bom.edge/child')
        if child and child.startswith('mat.'):
            mats.add(child)
        else:
            mats |= _all_materials_reachable(child, child_idx, _seen, _depth + 1)
    return mats


def analyze(seed_path: pathlib.Path):
    rows = load_edn(seed_path)
    g = classify(rows)
    products, parts, materials = g['products'], g['parts'], g['materials']
    bom, process, logistics = g['bom'], g['process'], g['logistics']
    ownership = g['ownership']

    child_idx = _bom_children_index(bom)
    ownership_index = {o[':company.ownership/child']: o[':company.ownership/parent'] for o in ownership}

    report = []
    derived = []

    # ── coverage summary ──
    report.append("# uchiwake 内訳 — product bill-of-materials resilience report\n")
    report.append("> ADR-2606081800. Aggregate-first RESILIENCE map, never a target-list (G2). "
                  "BOM decompositions are :representative public estimates, not authoritative recipes (G5).\n")
    report.append(f"- products (trade items): **{len(products)}**")
    report.append(f"- parts / sub-assemblies: **{len(parts)}**")
    report.append(f"- raw materials: **{len(materials)}**")
    report.append(f"- BOM edges: **{len(bom)}**")
    report.append(f"- process steps: **{len(process)}**")
    report.append(f"- logistics legs: **{len(logistics)}**")
    report.append(f"- ownership (子会社→parent) edges: **{len(ownership)}**\n")

    # ── GTIN coverage ──
    with_gtin = [p for p in products.values() if p.get(':product/gtin')]
    report.append(f"## GTIN coverage\n\n{len(with_gtin)}/{len(products)} products carry a GTIN. "
                  "Full coverage target = the GS1 GDSN universe (G7-gated).\n")

    # ── 1. MATERIAL concentration — how many products depend on each raw material ──
    mat_to_products = defaultdict(set)
    for pid in products:
        for mat in _all_materials_reachable(pid, child_idx):
            mat_to_products[mat].add(pid)
    report.append("## Material dependence (how many products trace down to each raw material)\n")
    report.append("| material | products depending | share |")
    report.append("|---|---:|---:|")
    n_prod = max(1, len(products))
    for mat, pids in sorted(mat_to_products.items(), key=lambda kv: -len(kv[1])):
        share = len(pids) / n_prod
        name = materials.get(mat, {}).get(':material/name', mat)
        report.append(f"| {name} | {len(pids)} | {share:.0%} |")
        derived.append({':concentration/id': f"conc.mat.{mat}",
                        ':concentration/dimension': ':material', ':concentration/key': mat,
                        ':concentration/share': round(share, 4), ':concentration/count': len(pids),
                        ':concentration/derived': True})

    # ── 2. PROCESS-COUNTRY concentration — where production steps cluster ──
    country_steps = defaultdict(int)
    for s in process:
        c = s.get(':process.step/country')
        if c:
            country_steps[c] += 1
    n_steps = max(1, sum(country_steps.values()))
    report.append("\n## Processing-jurisdiction load (where production steps cluster)\n")
    report.append("| country | process steps | share |")
    report.append("|---|---:|---:|")
    for c, n in sorted(country_steps.items(), key=lambda kv: -kv[1]):
        share = n / n_steps
        report.append(f"| {c} | {n} | {share:.0%} |")
        derived.append({':concentration/id': f"conc.procctry.{c}",
                        ':concentration/dimension': ':process-country', ':concentration/key': c,
                        ':concentration/share': round(share, 4), ':concentration/count': n,
                        ':concentration/derived': True})

    # ── 3. ULTIMATE-PARENT rollup — brand-owner subsidiaries rolled up (子会社 dimension) ──
    parent_products = defaultdict(set)
    for pid, p in products.items():
        bo = p.get(':product/brand-owner')
        if not bo:
            continue
        ultimate = _resolve_ultimate_parent(bo, ownership_index)
        parent_products[ultimate].add(pid)
    report.append("\n## Brand-owner concentration (subsidiaries rolled up to ultimate parent — 子会社)\n")
    report.append("| ultimate parent | products | rolled-up from subsidiary? |")
    report.append("|---|---:|:--:|")
    for parent, pids in sorted(parent_products.items(), key=lambda kv: -len(kv[1])):
        rolled = any(_resolve_ultimate_parent(products[pid].get(':product/brand-owner'), ownership_index)
                     != products[pid].get(':product/brand-owner') for pid in pids)
        report.append(f"| {parent} | {len(pids)} | {'yes' if rolled else 'no'} |")
        derived.append({':concentration/id': f"conc.parent.{parent}",
                        ':concentration/dimension': ':ultimate-parent', ':concentration/key': parent,
                        ':concentration/share': round(len(pids) / max(1, len(with_gtin) or len(products)), 4),
                        ':concentration/count': len(pids), ':concentration/derived': True})

    # ── 4. single-source / high-criticality BOM edges (diversification candidates) ──
    hot = [e for e in bom if (e.get(':bom.edge/criticality') or 0) >= 0.8]
    report.append("\n## High-criticality (single-source-risk) BOM edges — diversification candidates\n")
    report.append("| parent | child | criticality | disclosed supplier |")
    report.append("|---|---|---:|---|")
    for e in sorted(hot, key=lambda e: -(e.get(':bom.edge/criticality') or 0)):
        report.append(f"| {e.get(':bom.edge/parent')} | {e.get(':bom.edge/child')} | "
                      f"{e.get(':bom.edge/criticality'):.2f} | {e.get(':bom.edge/supplier') or '—'} |")

    return "\n".join(report) + "\n", derived


def main(argv):
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') else DEFAULT_SEED
    outdir = ROOT / "out"
    if '--out' in argv:
        outdir = pathlib.Path(argv[argv.index('--out') + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    md, derived = analyze(seed)
    (outdir / "intel-report.md").write_text(md, encoding='utf-8')

    lines = [";; uchiwake 内訳 — DERIVED concentration datoms. ADR-2606081800.",
             ";; :concentration/derived true — a uchiwake OBSERVATION, never re-ingested as fact.", "["]
    for d in derived:
        parts = [f"{k} {edn_str(v) if isinstance(v, str) and not v.startswith(':') else (str(v).lower() if isinstance(v, bool) else v)}"
                 for k, v in d.items()]
        lines.append(" {" + " ".join(parts) + "}")
    lines.append("]")
    (outdir / "product-criticality.kotoba.edn").write_text("\n".join(lines) + "\n", encoding='utf-8')

    print(md)
    print(f"\n→ {outdir/'intel-report.md'}\n→ {outdir/'product-criticality.kotoba.edn'} ({len(derived)} derived datoms)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
