#!/usr/bin/env python3
"""purl-keyed SBOM ↔ CVE vuln-match, materialized into kotoba.

The kotoba-native equivalent of the legacy `vertex_sbom_vuln_match`
(ADR-2604282300 Phase C): join SBOM component `cdx/purl` against CVE
`cve/affectsPurl`, and materialize one `VulnMatch` entity per hit so the result
is itself queryable in the EAVT store.

Because kotoba's BGP join is subject-keyed (not a literal value-join across
different subjects), the join is computed in-app from two AVET scans, then the
matches are written back as first-class entities (exactly how the RW Phase C
table is populated). Requires a running `kotoba serve` with the fleet SBOM
already ingested.

Usage:  python3 purl_vuln_match.py <jwt> [kotoba_url]
"""
import json
import subprocess
import sys

TOK = sys.argv[1]
URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8080"


def sparql(query):
    out = subprocess.run(
        ["kotoba", "--token", TOK, "--url", URL, "sparql", query],
        capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def by_subject(quads):
    d = {}
    for q in quads:
        d.setdefault(q["subject"], {})[q["predicate"].rsplit("/", 1)[-1]] = q.get("object", {}).get("text")
    return d


def main():
    # 1. component purls: subject → purl. Fleet parts carry `part/purl`
    #    (sbom_gen); CycloneDX-adapter rows carry `cdx/purl`. Union both.
    comp_purl = {}
    for pred in ("part/purl", "cdx/purl"):
        r = sparql(f'SELECT * WHERE {{ ?s <kg/claim/{pred}> ?p }}')
        for q in r["quads"]:
            if q["predicate"].endswith("purl"):
                comp_purl[q["subject"]] = q["object"]["text"]
    purl_to_comps = {}
    for s, p in comp_purl.items():
        purl_to_comps.setdefault(p, []).append(s)

    # 2. CVEs: subject → {affectsPurl, id, severity}
    cve = sparql('SELECT * WHERE { ?c <kg/claim/cve/affectsPurl> ?p . ?c <kg/claim/cve/id> ?i . ?c <kg/claim/cve/severity> ?s }')
    cves = by_subject(cve["quads"])  # keys: affectsPurl, id, severity

    # 3. join on purl, materialize VulnMatch entities
    entities, matches = [], []
    for cve_subj, c in cves.items():
        purl = c.get("affectsPurl")
        for comp_subj in purl_to_comps.get(purl, []):
            mid = f"vulnmatch:{c['id']}@{purl}"
            entities.append({
                "id": mid, "type": "VulnMatch", "labelEn": f"{c['id']} ⟶ {purl}",
                "claims": [
                    {"pred": "match/cve", "value": c["id"]},
                    {"pred": "match/purl", "value": purl},
                    {"pred": "match/severity", "value": c.get("severity", "")},
                    {"pred": "match/componentCid", "value": comp_subj},
                ],
            })
            matches.append((c.get("severity"), c["id"], purl))

    if entities:
        subprocess.run(
            ["curl", "-s", "-XPOST", f"{URL}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch",
             "-H", f"Authorization: Bearer {TOK}", "-H", "Content-Type: application/json",
             "--data", json.dumps({"entities": entities})],
            capture_output=True, text=True,
        )

    print(f"components-with-purl={len(comp_purl)}  cves={len(cves)}  matches={len(matches)}")
    for sev, cid, purl in sorted(matches, key=lambda m: m[0] or ""):
        print(f"  [{sev:>8}] {cid}  {purl}")

    # 4. verify the materialized join is queryable
    back = sparql('SELECT * WHERE { ?m <kg/claim/match/cve> ?c }')
    n = len({q["subject"] for q in back["quads"]})
    print(f"materialized VulnMatch entities in kotoba: {n}")


if __name__ == "__main__":
    main()
