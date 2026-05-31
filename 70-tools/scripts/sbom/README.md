# SBOM → kotoba migration tooling

Bridges CycloneDX SBOMs into the **kotoba** EAVT store (Datomic-class), per
ADR-2605262130 (kotoba supersedes RisingWave). The legacy SBOM app
(`60-apps/ai-gftd-project-sbom`, ADR-2604282300) persists to RisingWave
(`vertex_sbom_artifact` / `vertex_sbom_component`); since
`vertex_sbom_component` is **one row per CycloneDX `components[]` entry** and the
artifact row stores the original `cdxJson`, the migration is just
**CycloneDX → kotoba**.

## `cyclonedx_to_kotoba.py`

```
python3 cyclonedx_to_kotoba.py <sbom.cdx.json> [out.ingest.json]
# then POST the body to a running kotoba:
curl -s -XPOST localhost:8080/xrpc/ai.gftd.apps.kotobase.kg.ingest_batch \
  -H "Authorization: Bearer <jwt>" -H 'Content-Type: application/json' --data @out.ingest.json
```

One entity per component; claims become `kg/claim/<pred>` datoms.

## RisingWave → kotoba column mapping

| RisingWave (`vertex_sbom_*`) | CycloneDX field | kotoba datom (`kg/claim/…`) |
|---|---|---|
| `vertex_sbom_artifact.spec_version` | `specVersion` | `cdx/specVersion` |
| `vertex_sbom_artifact` (name/vehicle) | `metadata.component.name` | `cdx/sbom` |
| `vertex_sbom_component.name` | `components[].name` | entity `labelEn` |
| `vertex_sbom_component.version` | `.version` | `cdx/version` |
| `vertex_sbom_component` publisher | `.publisher` | `cdx/publisher` (manufacturer) |
| `vertex_sbom_component.supplier` | `.supplier.name` | `cdx/supplier` |
| `vertex_sbom_component.purl` *(idx)* | `.purl` | `cdx/purl` — **CVE-match join key** |
| `vertex_sbom_component.mpn` *(idx)* | `.properties[mpn]` | `cdx/prop/mpn` — supplier-recall key |
| component `bom-ref`/`purl`/`name` | — | entity id |

The two RisingWave indexes carry over as kotoba query patterns:
- `idx_sbom_component_purl` → `SELECT … WHERE { ?s <kg/claim/cdx/purl> ?p }` (CVE join)
- `idx_sbom_component_supplier_mpn` → `… <kg/claim/cdx/supplier> "X" . ?s <kg/claim/cdx/prop/mpn> ?m` (Takata-style recall)

`giemon:*` CycloneDX properties (emitted by `sbom_gen.py`) round-trip back to
`part/*` claims, so the giemon SBOMs and migrated RW data share one schema.

## Verified (2026-05-31, local `kotoba serve`, KOTOBA_IPFS=off)

- `kabitori.cdx.json` (20) round-trips: claims include `part/group`, `part/procurement`, … (giemon props preserved).
- `sample_rw_export.cdx.json` (a 2-component vehicle SBOM mimicking RW rows) → 2 entities / 22 quads; `SELECT … <cdx/supplier> "Bosch"` → 1; `<cdx/purl>` → both purls.

## purl-keyed SBOM ↔ CVE vuln-match (`purl_vuln_match.py`)

The kotoba-native equivalent of the legacy `vertex_sbom_vuln_match`
(ADR-2604282300 Phase C). Joins component `*/purl` against CVE `cve/affectsPurl`
and materializes one `VulnMatch` entity per hit (kotoba's BGP join is
subject-keyed, so the purl value-join is computed in-app then written back as
first-class entities — exactly how the RW Phase C table is populated).

```
# with a running kotoba serve holding the fleet SBOM:
curl -s -XPOST localhost:8080/xrpc/ai.gftd.apps.kotobase.kg.ingest_batch \
  -H "Authorization: Bearer <jwt>" -H 'Content-Type: application/json' --data @cve.seed.json
python3 purl_vuln_match.py <jwt>
# → VulnMatch entities; query e.g.:
kotoba --token <jwt> sparql 'SELECT * WHERE { ?m <kg/claim/match/severity> "critical" }'
```

`cve.seed.json` holds **synthetic demo CVEs** (`EXAMPLE-2026-*`, not real
advisories) whose `affectsPurl` matches fleet purls. Verified (2026-05-31):
17 components-with-purl × 4 CVEs → 3 matches (critical brake-ecu / high rp2040 /
medium ina226; the non-fleet CVE correctly excluded), 3 `VulnMatch` entities
queryable by `match/severity`. Production swaps the seed for a real OSV/NVD feed
(the kotoba sbom lexicon's `cveIngestOsv`).

## Honest scope

No live RisingWave instance was available here, so the bridge is verified by
round-tripping committed CycloneDX SBOMs + a representative RW-shaped export. The
production cutover is: export each `vertex_sbom_artifact.cdxJson` (or
reconstruct from component rows) → `cyclonedx_to_kotoba.py` → `kg.ingest_batch`.
