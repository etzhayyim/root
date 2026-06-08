#!/usr/bin/env python3
"""uchiwake 内訳 — kabuto coverage-linkage crosscheck (stdlib only). ADR-2606081800.

uchiwake's product graph references companies (brand-owner, BOM supplier, process
operator, logistics carrier, ownership parent/child) by kabuto :company/id in the
shared org.corp.* space. This tool computes — does not claim — how much of that
product graph actually WIRES INTO kabuto's ingested company universe, and surfaces
the gap honestly (a reference that does not resolve = "not yet ingested in kabuto",
NOT "does not exist"; G5).

It also reports the OWNERSHIP-ROLLUP effect: a brand-owner subsidiary that is NOT
itself in kabuto but whose ULTIMATE parent IS — i.e. the 子会社 edge recovers a link
that the flat reference would have missed.

This directly answers the standing coverage question ("how integrated is the
supply chain across actors?") with a measured percentage, not an assertion.

stdlib only. Usage:
    python3 crosscheck.py            # human report
    python3 crosscheck.py --json     # machine summary
"""
from __future__ import annotations
import sys
import os
import json
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uchiwake_edn import load_edn, classify  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SEED = ROOT / "data" / "seed-products.kotoba.edn"
# kabuto seed lives at 20-actors/kabuto/data/seed-public-companies.kotoba.edn
KABUTO_SEED = ROOT.parent / "kabuto" / "data" / "seed-public-companies.kotoba.edn"


def load_kabuto_company_ids():
    if not KABUTO_SEED.is_file():
        return None
    ids = set()
    for r in load_edn(KABUTO_SEED):
        if isinstance(r, dict) and ':company/id' in r:
            ids.add(r[':company/id'])
    return ids


def collect_company_refs(g):
    """Return {kind: [(ref_id, holder_id), ...]} for every company reference in the graph."""
    refs = defaultdict(list)
    for pid, p in g['products'].items():
        bo = p.get(':product/brand-owner')
        if bo:
            refs['brand-owner'].append((bo, pid))
    for e in g['bom']:
        s = e.get(':bom.edge/supplier')
        if s:
            refs['bom-supplier'].append((s, e[':bom.edge/id']))
    for s in g['process']:
        op = s.get(':process.step/operator')
        if op:
            refs['process-operator'].append((op, s[':process.step/id']))
    for lg in g['logistics']:
        c = lg.get(':logistics.leg/carrier')
        if c:
            refs['logistics-carrier'].append((c, lg[':logistics.leg/id']))
    for o in g['ownership']:
        refs['ownership-child'].append((o[':company.ownership/child'], o[':company.ownership/id']))
        refs['ownership-parent'].append((o[':company.ownership/parent'], o[':company.ownership/id']))
    return refs


def crosscheck():
    g = classify(load_edn(SEED))
    kabuto_ids = load_kabuto_company_ids()
    refs = collect_company_refs(g)
    ownership_index = {o[':company.ownership/child']: o[':company.ownership/parent']
                       for o in g['ownership']}

    def ultimate(cid, _d=0):
        if cid is None or _d > 16:
            return cid
        nxt = ownership_index.get(cid)
        return cid if (nxt is None or nxt == cid) else ultimate(nxt, _d + 1)

    summary = {'kabuto_available': kabuto_ids is not None,
               'kabuto_company_count': len(kabuto_ids) if kabuto_ids else 0,
               'by_kind': {}, 'rollup_recovered': []}

    all_refs = set()
    resolved = set()
    for kind, items in refs.items():
        k_total, k_res = 0, 0
        for ref_id, holder in items:
            all_refs.add(ref_id)
            k_total += 1
            if kabuto_ids and ref_id in kabuto_ids:
                k_res += 1
                resolved.add(ref_id)
            elif kabuto_ids:
                # rollup: subsidiary not in kabuto but ultimate parent is
                up = ultimate(ref_id)
                if up != ref_id and up in kabuto_ids:
                    summary['rollup_recovered'].append({'ref': ref_id, 'ultimate': up, 'kind': kind})
        summary['by_kind'][kind] = {'total': k_total, 'resolved': k_res}

    distinct = sorted(all_refs)
    summary['distinct_company_refs'] = len(distinct)
    summary['distinct_resolved'] = len(resolved)
    summary['linkage_pct'] = round(100.0 * len(resolved) / max(1, len(distinct)), 1)
    summary['unresolved'] = sorted(all_refs - resolved)
    return summary


def render(s):
    out = ["# uchiwake ⇄ kabuto coverage-linkage crosscheck\n",
           "> Measured (not claimed) integration of the uchiwake product graph into kabuto's",
           "> ingested company universe. Unresolved = \"not yet ingested in kabuto\", not \"nonexistent\" (G5).\n"]
    if not s['kabuto_available']:
        out.append("kabuto seed not found — cannot crosscheck. (expected at 20-actors/kabuto/data/)")
        return "\n".join(out) + "\n"
    out.append(f"- kabuto ingested companies: **{s['kabuto_company_count']}**")
    out.append(f"- distinct company refs in uchiwake: **{s['distinct_company_refs']}**")
    out.append(f"- resolved into kabuto: **{s['distinct_resolved']}** "
               f"(**{s['linkage_pct']}%** linkage)\n")
    out.append("| reference kind | total | resolved |")
    out.append("|---|---:|---:|")
    for kind, v in sorted(s['by_kind'].items()):
        out.append(f"| {kind} | {v['total']} | {v['resolved']} |")
    if s['rollup_recovered']:
        out.append("\n## 子会社 rollup recovered (subsidiary not in kabuto, but ultimate parent is)\n")
        for r in s['rollup_recovered']:
            out.append(f"- `{r['ref']}` → ultimate `{r['ultimate']}` ({r['kind']})")
    if s['unresolved']:
        out.append("\n## Not yet ingested in kabuto (honest gap)\n")
        for u in s['unresolved']:
            out.append(f"- `{u}`")
    return "\n".join(out) + "\n"


def main(argv):
    s = crosscheck()
    if '--json' in argv:
        print(json.dumps(s, indent=2, ensure_ascii=False))
    else:
        print(render(s))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
