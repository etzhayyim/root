# com.etzhayyim.apps.maps3d.* — etzhayyim variant

Vendor-authored maps3d lexicons borrowed by religious-corp (etzhayyim) under the shared `com.etzhayyim.*` namespace pattern. Verdicts assigned per **ADR-2605214000 §2** substrate-fit rules.

## Verdicts (2026-05-21)

| Lexicon | Verdict | Adaptation |
|---|---|---|
| `linkActor` | **PORT-adapted** | description: dropped "Per ADR-0036 the worker writes vertex / edge rows directly via Hyperdrive, no PDS round-trip" → replaced with "Graph entity + edge writes go via the etzhayyim substrate (AT MST + LanceDB per ADR-2605172000), not via PDS round-trip" |
| `processTile` | **PORT-adapted** | description: dropped "vertex_spatial ingest" → "LanceDB spatial ingest"; dropped "Real work runs in LangServer handlers under namespace `maps3d` in Vultr LKE" → "Real work runs in Murakumo cell handlers on the etzhayyim fleet per ADR-2605214000"; rephrased "`vertex_maps3d_tile WHERE status IN (...)`" → "the maps3d tile queue (MST-backed)" |
| `colmapTile` | **PORT-direct** | no edits; description substrate-neutral (B2 storage is allowed; no required fields reference prohibited infrastructure) |
| `curateImages` | **PORT-direct** | no edits; description substrate-neutral (references Murakumo Vision and LangGraph nodes only) |
| `fetchMapillary` | **PORT-direct** | no edits; description substrate-neutral (Mapillary is external data source, not prohibited infrastructure) |
| `replanReconstruction` | **PORT-direct** | no edits; description substrate-neutral (LangGraph planning, no vendor infra) |
| `simplifyAndExport` | **PORT-adapted** | description: replaced "vertex_spatial Building row" → "LanceDB spatial Building row (etzhayyim substrate per ADR-2605172000)" |
| `visionAnnotate` | **PORT-direct** | no edits; description substrate-neutral (Murakumo Vision qwen3-vl-8b, internal pipeline reference) |

## What changed

Only top-level `description` text in 3 lexicons (`linkActor`, `processTile`, `simplifyAndExport`) was edited to remove vendor-specific vocabulary and replace with etzhayyim substrate references. For all 8 lexicons, NSID, `defs.main.type`, `parameters`, `input/output` schemas, and required fields are **byte-identical** to the vendor version. Vendor and religious-corp implementations interop on all these lexicons.

The five PORT-direct lexicons (`colmapTile`, `curateImages`, `fetchMapillary`, `replanReconstruction`, `visionAnnotate`) required no edits; their descriptions already reference substrate-compatible infrastructure (open standards like Mapillary, LangGraph, and OSM; or internal systems like Murakumo Vision).

## Why the namespace stays `com.etzhayyim.apps.maps3d.*`

Per ADR-2605214000 §2 namespace placement rule: vendor-authored lexicons borrowed by religious-corp keep the `com.etzhayyim.*` NSID. The `com.etzhayyim.*` namespace is reserved for religious-corp-only lexicons with no vendor equivalent.

## Substrate-fit conditions (recap)

1. No required RisingWave / Hyperdrive / Postgres-only field or referenced table.
2. No required commercial K8s control-plane primitive (Karmada, VKE LoadBalancer, k3s API).
3. No required fiat payment processor.
4. No required commercial SaaS dependency (RunPod, Linode GPU, vendor-billed OpenAI/Anthropic key).
5. AT MST + IPFS + Base L2 + LanceDB-WASM + tonbo + yata CRDT + Pregel cells cover the read/write path.

The two PORT-adapted lexicons here pass all five conditions on **required fields**; their descriptions previously narrated vendor infrastructure, which the edits removed.

## See also

- ADR-2605214000 — Murakumo distributed cluster (no-VKE mesh) + vendor→religious-corp lexicon port rules
- ADR-2605172000 — etzhayyim kotoba substrate
- ADR-2605191346 — etzhayyim is Vultr-free / no commercial K8s
- `00-contracts/lexicons/com/etzhayyim/murakumo/README.md` — sister registry for murakumo lexicons
- `00-contracts/bpmn/com/etzhayyim/murakumo/README.md` — sister registry for murakumo BPMN
