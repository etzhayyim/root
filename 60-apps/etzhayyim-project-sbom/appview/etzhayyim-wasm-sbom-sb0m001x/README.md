# sbom.etzhayyim.com — `etzhayyim-wasm-sbom-sb0m001x`

CF Worker facade for the SBOM artifact registry. **Edge layer only** —
all RisingWave writes happen in the K8s LangServer pod (ADR-2604282300).

## Topology

```
caller (kami-cad-import / cargo-cyclonedx)
    │
    ▼  POST /xrpc/com.etzhayyim.sbom.registerArtifact
sbom.etzhayyim.com  (this CF Worker)
    │   validate input shape
    │   parse cdxJson, count components
    │   compute deterministic artifactUri
    │
    ▼  proxyToDispatcher(x-internal-trust)
dispatcher.etzhayyim.com  (K8s ClusterIP)
    │
    ▼  LangServer broker (BPMN: sbom_register_artifact)
LangServer pod
    │
    ▼  task_sbom_register_artifact
    │   psycopg2 INSERT vertex_sbom_artifact
    │   psycopg2 executemany INSERT vertex_sbom_component
    │
    ▼
RisingWave  (vertex_sbom_artifact + vertex_sbom_component)
```

Both software SBOMs (`cargo-cyclonedx` output) and vehicle BOMs
(`kami-cad-import`, CycloneDX `type: "device"` per part) flow through
the same handler.

## Phases

| Phase | Status | What |
|---|---|---|
| **0 stub** | ✅ prior rev | Facade-only: validate + log + return artifactUri. |
| **B persist** | ✅ prior rev | CF Worker → dispatcher → LangServer → LangServer → RisingWave (vertex_sbom_artifact + vertex_sbom_component). |
| **C vuln-match** | ✅ this rev | BPMN adds Task_VulnMatch (purl/cpe LIKE × `vertex_cve_entry`) → `vertex_sbom_vuln_match`. Returns `vulnMatchCount` + `severityCounts`. CVE catalog populated by upstream feeder (yabai). |
| **D recall** | 🚧 forward | Hardware-only blast-radius queries (`supplier=Toray AND mpn=...`). |

## Files

| Path | Purpose |
|---|---|
| `kotodama.jsonld` | Worker manifest + profile + triggers |
| `wrangler.jsonc` | CF Worker config + DISPATCHER_INTERNAL_SECRET binding |
| `src/app.ts` | Hono facade — validate + `proxyToDispatcher` only |
| `00-contracts/lexicons/com/etzhayyim/apps/sbom/registerArtifact.json` | XRPC contract (already existed) |
| `00-contracts/lexicons/com/etzhayyim/apps/sbom/health.json` | Liveness contract |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/sbom/registerArtifact.bpmn` | BPMN process definition |
| `30-graph/graph-schema/migrations/20260506100000_vertex_sbom_artifact.ts` | RisingWave schema |
| `30-graph/graph-schema/migrations/20260506100100_seed_sbom_bpmn_actor.ts` | BPMN process_def + binding seed |
| `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/sbom.py` | LangServer handler (psycopg2 INSERT) |
| `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py` | Worker registration |

## Tables

| Table | Indexes |
|---|---|
| `vertex_sbom_artifact` | `source_sha256` (dedup), `vehicle_id` (recall), `kind` (software/vehicle), `registered_at` |
| `vertex_sbom_component` | `artifact_uri`, `purl` + `cpe` (CVE join), `supplier_mpn` (Takata-style supplier recall), `component_type` |
| `vertex_cve_entry` | `affected_purl_pattern`, `affected_cpe_pattern`, `severity`, `source` |
| `vertex_sbom_vuln_match` | `artifact_uri`, `cve_id` (blast-radius), `severity`, `component_purl` |

## Deploy

```bash
# 1. apply RW migrations (out-of-band per ADR-2604241342)
cd 30-graph/graph-schema
./scripts/apply-pending.sh 20260506100000_vertex_sbom_artifact
./scripts/apply-pending.sh 20260506100100_seed_sbom_bpmn_actor
./scripts/apply-pending.sh 20260506110000_vertex_sbom_vuln_match
./scripts/apply-pending.sh 20260506110100_bump_sbom_bpmn_v2

# 2. F5 watcher deploys the BPMN to LangServer within 30s

# 3. rebuild + roll kotodama image (registers task_sbom_register_artifact)
cd 40-engine/kotoba/crates/kotoba-kotodama/py
docker buildx build --platform linux/amd64 --no-cache --push \
  -t ghcr.io/etzhayyim/kotodama:0.4.0-amd64 .
helm upgrade mitama-udf/langserver-worker --reuse-values \
  --set "image.tag=0.4.0-amd64"

# 4. deploy CF Worker
cd 60-apps/etzhayyim-project-sbom/appview/etzhayyim-wasm-sbom-sb0m001x
etzhayyim deploy
```

## Smoke

```bash
# Vehicle BOM (kami-cad-import)
cargo run -p kami-cad-import --example register_roadster | bash

# Software SBOM (cargo-cyclonedx)
cargo cyclonedx -f json
etzhayyim agent-token --lxm com.etzhayyim.sbom.registerArtifact > /tmp/tok
curl -fsSL -X POST https://sbom.etzhayyim.com/xrpc/com.etzhayyim.sbom.registerArtifact \
  -H "Authorization: Bearer $(cat /tmp/tok)" \
  -H "Content-Type: application/json" \
  --data '{"format":"CycloneDX","specVersion":"1.5","sourceUri":"file://Cargo.lock","sourceSha256":"...","license":"MIT","cdxJson":"<<full doc>>"}'
```

## Health

`POST /xrpc/com.etzhayyim.sbom.health` → `{ ok, did, ts, phase, note }`
— public, no auth.
