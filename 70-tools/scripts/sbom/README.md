# SBOM → kotoba migration tooling

Bridges CycloneDX SBOMs into the **kotoba** EAVT store (Datomic-class), per
ADR-2605262130 (kotoba supersedes RisingWave). The legacy SBOM app
(`60-apps/etzhayyim-project-sbom`, ADR-2604282300) persists to RisingWave
(`vertex_sbom_artifact` / `vertex_sbom_component`); since
`vertex_sbom_component` is **one row per CycloneDX `components[]` entry** and the
artifact row stores the original `cdxJson`, the migration is just
**CycloneDX → kotoba**.

## `cyclonedx_to_kotoba.py`

```
python3 cyclonedx_to_kotoba.py <sbom.cdx.json> [out.ingest.json]
# then POST the body to a running kotoba:
curl -s -XPOST localhost:8080/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch \
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
curl -s -XPOST localhost:8080/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch \
  -H "Authorization: Bearer <jwt>" -H 'Content-Type: application/json' --data @cve.seed.json
python3 purl_vuln_match.py <jwt>
# → VulnMatch entities; query e.g.:
kotoba --token <jwt> sparql 'SELECT * WHERE { ?m <kg/claim/match/severity> "critical" }'
```

### CVE sources

- `cve.seed.json` — **synthetic demo CVEs** (`EXAMPLE-2026-*`, not real advisories).
- `osv_to_kotoba.py` + `osv_sample.json` — **real OSV schema** ingest
  (https://ossf.github.io/osv-schema/): converts OSV records (a record, a list,
  or an `{"vulns":[…]}` API response) → the same `cve/{id,affectsPurl,severity}`
  entities, so `purl_vuln_match.py` is unchanged. Production replaces the sample
  with a download from `api.osv.dev` (`POST /v1/query` per purl) or an OSV bucket
  dump — this is the kotoba-native form of the sbom lexicon's `cveIngestOsv`.
  Verified: OSV `OSV-DEMO-RP2040` (critical) joins the fleet alongside the
  synthetic `EXAMPLE-2026-0001` (high) → the RP2040 shows **two advisories from
  two sources**.
- `osv_fetch.py` — **live fetch from api.osv.dev** (read-only public query):
  ```
  python3 osv_fetch.py --ecosystem Maven --name org.apache.logging.log4j:log4j-core \
      --version 2.14.0 --out log4j.osv.json
  python3 osv_to_kotoba.py log4j.osv.json log4j.ingest.json   # → kg.ingest body
  ```
  **Verified live (2026-05-31)**: osv.dev returned 7 real advisories →
  35 CveEntry; querying kotoba shows real GHSAs (incl. Log4Shell
  `GHSA-jfh8-c2jp-5v3q`) across real Maven purls
  (`pkg:maven/org.apache.logging.log4j/log4j-core`, …). OSV indexes **software**
  packages, so the giemon **hardware** purls (`pkg:generic/*`) won't match — a
  robot's software stack (RPi OS / ROS2 / Python deps) is the OSV-matchable
  surface; hardware needs an ICS-CERT-style feed.

### Software-stack SBOM (the OSV-matchable surface)

`60-apps/etzhayyim-project-open-robo/firmware/software-sbom.edn` is the Otete
firmware's software SBOM (`:bom/of giemon-otete-sw`) — PyPI deps
(`pkg:pypi/*`, from pyproject.toml) + ROS2 Humble debs (`pkg:deb/ros-humble-*`).
Run it through the same pipeline and match against **real** OSV:
```
python3 70-tools/e7m-sim/scenes/giemon_kabitori/sbom_gen.py software-sbom.edn .   # → otete-sw.cdx.json + ingest
# ingest otete-sw.ingest.json, then for each PyPI dep:
python3 osv_fetch.py --ecosystem PyPI --name setuptools --out o.json && python3 osv_to_kotoba.py o.json o.ingest.json   # ingest
python3 purl_vuln_match.py <jwt>
```
Verified live (2026-05-31): real osv.dev advisories (setuptools 7 · numpy 16 ·
scipy 4 · pytest 1 · pyserial 0) → **28 pkg:pypi VulnMatch** across the robot's
actual declared deps. This is the real-data counterpart to the hardware fleet's
synthetic CVEs.

`cve.seed.json` holds **synthetic demo CVEs** (`EXAMPLE-2026-*`, not real
advisories) whose `affectsPurl` matches fleet purls. Verified (2026-05-31):
17 components-with-purl × 4 CVEs → 3 matches (critical brake-ecu / high rp2040 /
medium ina226; the non-fleet CVE correctly excluded), 3 `VulnMatch` entities
queryable by `match/severity`. Production swaps the seed for a real OSV/NVD feed
(the kotoba sbom lexicon's `cveIngestOsv`).

## CAD-feature ↔ BOM binding (`sim_part_binding.py`)

Tightens the loose `:part/sim-feature` link: validates that every part's
`:part/sim-feature` resolves to a real `<link>`/`<joint>` in the robot's URDF,
and reports bound / unbound parts + uncovered sim features (exits non-zero on an
invalid binding, so it is gate-worthy).

```
python3 sim_part_binding.py \
  70-tools/e7m-sim/scenes/giemon_kabitori/giemon_kabitori.urdf \
  70-tools/e7m-sim/scenes/giemon_kabitori/parts.edn
```

Verified (kabitori): 13 URDF features, **0 invalid** bindings, 10 bound / 10
unbound (electronics + cleaning parts have no mechanical feature — expected),
5 uncovered features. (otete has no committed sim/URDF, so its parts are all
unbound — also expected.)

## Honest scope

No live RisingWave instance was available here, so the bridge is verified by
round-tripping committed CycloneDX SBOMs + a representative RW-shaped export. The
production cutover is: export each `vertex_sbom_artifact.cdxJson` (or
reconstruct from component rows) → `cyclonedx_to_kotoba.py` → `kg.ingest_batch`.
