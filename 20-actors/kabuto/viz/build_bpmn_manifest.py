#!/usr/bin/env python3
"""kabuto 兜 — BPMN manifest builder for the profile-page Process tab.

ADR-2606022000. Reads the generated BPMN files (out/bpmn/*.bpmn) + the process
datoms (out/processes.kotoba.edn) and emits a SINGLE manifest JSON that an actor
serves at `<embed-base>/_app/bpmn.json`. The yoro AgentProfile "Process" tab
discovers this file generically (any actor that publishes it gets a BPMN tab) and
renders each process read-only with bpmn-js.

The seed has ~1.7k generic templates; inlining every XML would be multi-MB, so the
manifest inlines a bounded FEATURED set (notable companies) and reports the total.
Non-featured processes carry an `xmlUrl` (relative) for lazy fetch by a deployed
actor. Honest (G5): these are :synthesized generic templates, not real processes.

stdlib only. Usage:
    python3 viz/build_bpmn_manifest.py        # → viz/bpmn-manifest.json
"""
from __future__ import annotations
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent      # 20-actors/kabuto
OUT = HERE / "out"
BPMN = OUT / "bpmn"

# Notable companies to feature inline (browsable set for the profile tab). Only
# those actually present in the seed are emitted; missing ones are skipped.
FEATURED = [
    "org.corp.tw.tsmc", "org.corp.us.apple", "org.corp.jp.toyota",
    "org.corp.kr.samsung-electronics", "org.corp.nl.asml", "org.corp.us.nvidia",
    "org.corp.tw.foxconn", "org.corp.jp.sony", "org.corp.us.intel",
    "org.corp.sa.aramco", "org.corp.ch.nestle", "org.corp.de.volkswagen",
    "org.corp.us.microsoft", "org.corp.cn.byd", "org.corp.us.boeing",
    "org.corp.fr.airbus", "org.corp.gb.astrazeneca", "org.corp.in.reliance",
]


def _proc_meta():
    """Parse out/processes.kotoba.edn → list of {id, company, name, kind, cid}."""
    txt = (OUT / "processes.kotoba.edn").read_text(encoding="utf-8")
    procs = []
    for m in re.finditer(r"\{:company\.process/id\s+\"([^\"]+)\""
                         r"[^}]*?:company\.process/company\s+\"([^\"]+)\""
                         r"[^}]*?:company\.process/name\s+\"([^\"]+)\""
                         r"[^}]*?:company\.process/kind\s+(:[a-z-]+)"
                         r"[^}]*?:company\.process/bpmn-cid\s+\"([^\"]+)\"", txt):
        pid, company, name, kind, cid = m.groups()
        procs.append({"id": pid, "company": company, "name": name,
                      "kind": kind.lstrip(":"), "cid": cid})
    return procs


def _bpmn_path(company: str, kind: str) -> pathlib.Path:
    slug = company.replace("org.corp.", "").replace(".", "_")
    return BPMN / f"{slug}.{kind}.bpmn"


def main():
    if not (OUT / "processes.kotoba.edn").exists():
        sys.exit("run methods/bpmn.py first (out/processes.kotoba.edn missing)")
    procs = _proc_meta()
    by_company = {}
    for p in procs:
        by_company.setdefault(p["company"], []).append(p)

    featured = []
    for company in FEATURED:
        for p in by_company.get(company, []):
            path = _bpmn_path(company, p["kind"])
            if not path.exists():
                continue
            featured.append({
                "id": p["id"], "company": company, "name": p["name"],
                "kind": p["kind"], "cid": p["cid"],
                "xml": path.read_text(encoding="utf-8"),
            })

    manifest = {
        "schema": "com.etzhayyim.kabuto.bpmnManifest/1",
        "actor": "kabuto",
        "did": "did:web:etzhayyim.com:actor:kabuto",
        "note": ("Generic :synthesized BPMN procurement/disclosure templates per "
                 "ADR-2606022000 — NOT a company's actual internal process. "
                 "Aggregate-first resilience/transparency, never a target-list (G2)."),
        "total": len(procs),
        "featuredCount": len(featured),
        "processes": featured,
    }
    dest = HERE / "viz" / "bpmn-manifest.json"
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"kabuto.bpmn-manifest: {len(featured)} featured / {len(procs)} total "
          f"→ {dest} ({dest.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
