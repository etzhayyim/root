#!/usr/bin/env python3
"""uchiwake 内訳 — DETERMINISTIC byte-parity oracle for the Clojure port.

analyze.py builds material→products reachability with an unordered `set`, whose iteration
order is PYTHONHASHSEED-dependent and therefore NOT reproducible run-to-run (verified). This
oracle reuses analyze.py's OWN classify/_resolve_ultimate_parent/_bom_children_index/edn_str
but pins the SAME deterministic discovery order the Clojure port uses (first BOM-edge
appearance, DFS in seed edge order). Output is byte-identical to analyze.cljc by construction;
the analyzer arithmetic, rounding, and f-string formatting are analyze.py's verbatim.

Usage:  python3 tools/parity_oracle.py <seed.edn> <outdir>
"""
import sys, os, pathlib
from collections import defaultdict, OrderedDict
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "methods"))
from uchiwake_edn import load_edn, classify, edn_str  # noqa: E402
import analyze as A  # noqa: E402


def _det_materials(node_id, child_idx, seen=None, depth=0):
    """Deterministic first-appearance DFS (replaces analyze's set-based reachability)."""
    if seen is None:
        seen = set()
    if node_id in seen or depth > 24:
        return []
    seen.add(node_id)
    out = []
    for e in child_idx.get(node_id, []):
        child = e.get(':bom.edge/child')
        if child and child.startswith('mat.'):
            if child not in out:
                out.append(child)
        else:
            for m in _det_materials(child, child_idx, seen, depth + 1):
                if m not in out:
                    out.append(m)
    return out


def analyze(seed_path):
    rows = load_edn(seed_path)
    g = classify(rows)
    products, parts, materials = g['products'], g['parts'], g['materials']
    bom, process, logistics = g['bom'], g['process'], g['logistics']
    ownership = g['ownership']
    child_idx = A._bom_children_index(bom)
    ownership_index = {o[':company.ownership/child']: o[':company.ownership/parent'] for o in ownership}
    report, derived = [], []

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

    with_gtin = [p for p in products.values() if p.get(':product/gtin')]
    report.append(f"## GTIN coverage\n\n{len(with_gtin)}/{len(products)} products carry a GTIN. "
                  "Full coverage target = the GS1 GDSN universe (G7-gated).\n")

    mat_to_products = OrderedDict()
    for pid in products:
        for mat in _det_materials(pid, child_idx):
            mat_to_products.setdefault(mat, set()).add(pid)
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

    country_steps = OrderedDict()
    for s in process:
        c = s.get(':process.step/country')
        if c:
            country_steps[c] = country_steps.get(c, 0) + 1
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

    parent_products = OrderedDict()
    for pid, p in products.items():
        bo = p.get(':product/brand-owner')
        if not bo:
            continue
        ultimate = A._resolve_ultimate_parent(bo, ownership_index)
        parent_products.setdefault(ultimate, set()).add(pid)
    report.append("\n## Brand-owner concentration (subsidiaries rolled up to ultimate parent — 子会社)\n")
    report.append("| ultimate parent | products | rolled-up from subsidiary? |")
    report.append("|---|---:|:--:|")
    for parent, pids in sorted(parent_products.items(), key=lambda kv: -len(kv[1])):
        rolled = any(A._resolve_ultimate_parent(products[pid].get(':product/brand-owner'), ownership_index)
                     != products[pid].get(':product/brand-owner') for pid in pids)
        report.append(f"| {parent} | {len(pids)} | {'yes' if rolled else 'no'} |")
        derived.append({':concentration/id': f"conc.parent.{parent}",
                        ':concentration/dimension': ':ultimate-parent', ':concentration/key': parent,
                        ':concentration/share': round(len(pids) / max(1, len(with_gtin) or len(products)), 4),
                        ':concentration/count': len(pids), ':concentration/derived': True})

    hot = [e for e in bom if (e.get(':bom.edge/criticality') or 0) >= 0.8]
    report.append("\n## High-criticality (single-source-risk) BOM edges — diversification candidates\n")
    report.append("| parent | child | criticality | disclosed supplier |")
    report.append("|---|---|---:|---|")
    for e in sorted(hot, key=lambda e: -(e.get(':bom.edge/criticality') or 0)):
        report.append(f"| {e.get(':bom.edge/parent')} | {e.get(':bom.edge/child')} | "
                      f"{e.get(':bom.edge/criticality'):.2f} | {e.get(':bom.edge/supplier') or '—'} |")
    return "\n".join(report) + "\n", derived


def main(argv):
    seed = pathlib.Path(argv[1])
    outdir = pathlib.Path(argv[2])
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
    print(f"{len(derived)} derived datoms")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
