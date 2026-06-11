#!/usr/bin/env python3
"""OSV → kotoba CVE entities — real OSV-schema vuln ingest.

Replaces the synthetic `cve.seed.json` with the real OSV schema
(https://ossf.github.io/osv-schema/), so the kotoba sbom lexicon's
`cveIngestOsv` path is fed real advisories. Emits a kotoba `kg.ingest_batch`
body of `CveEntry` entities using the SAME predicates the vuln-matcher expects
(`cve/id`, `cve/affectsPurl`, `cve/severity`), so `purl_vuln_match.py` works
unchanged.

One entity per (advisory, affected purl) — so a multi-package advisory yields
one matchable entity per purl (kotoba's same-subject 3-triple join needs one
affectsPurl per subject).

Input: an OSV record, a list of records, or an OSV API response `{"vulns":[…]}`
(e.g. from `POST https://api.osv.dev/v1/query` / a downloaded OSV dump).

Usage:  python3 osv_to_kotoba.py <osv.json> [out.ingest.json]
"""
import json
import re
import sys
from pathlib import Path

_ECO = {"pypi": "pypi", "npm": "npm", "go": "golang", "maven": "maven",
        "crates.io": "cargo", "rubygems": "gem", "nuget": "nuget", "packagist": "composer"}


def severity(v: dict) -> str:
    ds = (v.get("database_specific") or {}).get("severity")
    if ds:
        return str(ds).lower()
    # CVSS base-score bucket if a numeric score is present
    for s in v.get("severity", []) or []:
        m = re.search(r"(\d+(?:\.\d+)?)", str(s.get("score", "")))
        if m:
            x = float(m.group(1))
            return "critical" if x >= 9 else "high" if x >= 7 else "medium" if x >= 4 else "low"
    return "unknown"


def affected_purls(v: dict):
    for a in v.get("affected", []) or []:
        pkg = a.get("package") or {}
        if pkg.get("purl"):
            yield pkg["purl"]
        elif pkg.get("ecosystem") and pkg.get("name"):
            eco = _ECO.get(pkg["ecosystem"].lower(), pkg["ecosystem"].lower())
            yield f"pkg:{eco}/{pkg['name']}"


def records(doc):
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict) and "vulns" in doc:
        return doc["vulns"]
    return [doc]


def osv_to_ingest(doc) -> dict:
    entities = []
    for v in records(doc):
        oid = v.get("id")
        if not oid:
            continue
        sev = severity(v)
        summary = v.get("summary") or v.get("details", "")[:120]
        for purl in affected_purls(v):
            entities.append({
                "id": f"cve:{oid}::{purl}",
                "type": "CveEntry",
                "labelEn": f"{oid}",
                "claims": [
                    {"pred": "cve/id", "value": oid},
                    {"pred": "cve/affectsPurl", "value": purl},
                    {"pred": "cve/severity", "value": sev},
                    {"pred": "cve/source", "value": "osv"},
                    *([{"pred": "cve/summary", "value": summary}] if summary else []),
                    *[{"pred": "cve/alias", "value": a} for a in v.get("aliases", []) or []],
                ],
            })
    return {"entities": entities}


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: osv_to_kotoba.py <osv.json> [out.ingest.json]")
    src = Path(sys.argv[1])
    doc = json.loads(src.read_text(encoding="utf-8"))
    ing = osv_to_ingest(doc)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".ingest.json")
    out.write_text(json.dumps(ing, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{src.name}: {len(ing['entities'])} CveEntry (purl-keyed) → {out}")


if __name__ == "__main__":
    main()
