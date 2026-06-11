#!/usr/bin/env python3
"""CycloneDX → kotoba kg.ingest_batch — generic SBOM → EAVT bridge.

Reads a CycloneDX 1.x JSON SBOM and emits a kotoba `kg.ingest_batch` body (one
entity per `components[]` entry). This is the migration path for the legacy
RisingWave SBOM registry (`vertex_sbom_artifact` / `vertex_sbom_component`,
ADR-2604282300): that store holds CycloneDX (one component row per
`components[]`), so exporting its `cdxJson` and piping it here moves the data
onto kotoba (Datomic-class EAVT) per ADR-2605262130 (no-RisingWave). It also
round-trips the giemon SBOMs (kabitori.cdx.json / otete.cdx.json).

Datom mapping (claims → kg/claim/<pred>):
  component.type            → cdx/type
  component.name            → (entity labelEn)
  component.version         → cdx/version
  component.publisher       → cdx/publisher        (manufacturer)
  component.supplier.name   → cdx/supplier
  component.group           → cdx/group
  component.purl            → cdx/purl             (CVE-match join key)
  component.properties[]    → giemon:X → part/X (camel) ; else cdx/prop/<name>
  + provenance: cdx/sbom (metadata.component.name), cdx/specVersion
Entity id = bom-ref → purl → name (first present).

Usage:  python3 cyclonedx_to_kotoba.py <sbom.cdx.json> [out.ingest.json]
        (writes the kg.ingest_batch body; defaults to <stem>.ingest.json)
"""
import json
import sys
from pathlib import Path


def _camel(name: str) -> str:
    parts = name.replace("-", " ").replace("_", " ").split()
    return parts[0] + "".join(w.capitalize() for w in parts[1:]) if parts else name


def component_to_entity(comp: dict, sbom_name: str, spec_version: str) -> dict:
    cid = comp.get("bom-ref") or comp.get("purl") or comp.get("name") or "unknown"
    claims = [
        {"pred": "cdx/sbom", "value": sbom_name},
        {"pred": "cdx/specVersion", "value": spec_version},
    ]
    def add(pred, val):
        if val is not None and val != "":
            claims.append({"pred": pred, "value": str(val)})
    add("cdx/type", comp.get("type"))
    add("cdx/version", comp.get("version"))
    add("cdx/publisher", comp.get("publisher"))
    add("cdx/supplier", (comp.get("supplier") or {}).get("name"))
    add("cdx/group", comp.get("group"))
    add("cdx/purl", comp.get("purl"))
    for p in comp.get("properties", []) or []:
        n = p.get("name", "")
        v = p.get("value")
        if n.startswith("giemon:"):
            add(f"part/{_camel(n[len('giemon:'):])}", v)
        else:
            add(f"cdx/prop/{n}", v)
    return {
        "id": cid,
        "type": "SbomComponent",
        "labelEn": comp.get("name", cid),
        "claims": claims,
    }


def cyclonedx_to_ingest(doc: dict) -> dict:
    spec = doc.get("specVersion", "1.5")
    sbom_name = ((doc.get("metadata") or {}).get("component") or {}).get("name", "sbom")
    comps = doc.get("components", []) or []
    return {"entities": [component_to_entity(c, sbom_name, spec) for c in comps]}


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: cyclonedx_to_kotoba.py <sbom.cdx.json> [out.ingest.json]")
    src = Path(sys.argv[1])
    doc = json.loads(src.read_text(encoding="utf-8"))
    assert doc.get("bomFormat") == "CycloneDX", "not a CycloneDX document"
    ing = cyclonedx_to_ingest(doc)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix("").with_suffix(".ingest.json")
    out.write_text(json.dumps(ing, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{src.name}: {len(ing['entities'])} components → {out}")


if __name__ == "__main__":
    main()
