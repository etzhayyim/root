# com.etzhayyim.murakumo.* — etzhayyim variant

Vendor-authored (etzhayyim.com) lexicons that the religious-corp (etzhayyim) substrate borrows for its murakumo distributed cluster (per the `com.etzhayyim.*` shared-namespace pattern in `etzhayyim/root`).

## Migration verdicts (2026-05-21, etzhayyim murakumo → etzhayyim)

| Lexicon | Verdict | Adaptation |
|---|---|---|
| `trainExperts` | **PORT-direct** (already migrated 2026-05-17) | none |
| `fleetPlan` | **PORT-direct** | none — LanceDB fits `50-infra/lancedb-wasm` |
| `graphExtract` | **PORT-direct** | none — MLX/Qwen runs on Mac mini fleet |
| `planPipeline` | **PORT-direct** | description updated: omits `scoreDataQuality` step |
| `optimizeCycle` | **PORT-adapted** | description updated: omits "update quality score" step |
| `coverageExport` | **PORT-adapted** | `pdsUrl` default → `https://atproto.etzhayyim.com` |
| `graphIngest` | **PORT-adapted** | description rewritten — LanceDB only; `pushYata` default `false`; `pdsUrl` default → etzhayyim |
| `runPipeline` | **PORT-adapted** | description: drops `scoreDataQuality` from canonical step list |
| `evalV6` | **PORT-adapted** | `sql` default `false` (etzhayyim has no RW SQL substrate; vendor keeps `true`) |
| `scoreDataQuality` | **REJECT** | RW `schema_registry` write-back; no etzhayyim equivalent. Would need redesign against AT MST / IPFS registry to be portable. |

## Why these are kept in the `com.etzhayyim.*` namespace (and not `com.etzhayyim.*`)

Per the operating-entity boundary (root CLAUDE.md §Identity): `etzhayyim` is the operating entity; `etzhayyim Japan株式会社` is the vendor/contractor. NSID authorship is **shared** — vendor authors religious-corp-compatible lexicons under `com.etzhayyim.*` and etzhayyim borrows them with adaptations. This keeps the lexicon registry deduplicated; if etzhayyim ever forks, the namespace can split to `com.etzhayyim.murakumo.*`.

The `com.etzhayyim.murakumo.*` namespace at `00-contracts/lexicons/com/etzhayyim/murakumo/` is reserved for **etzhayyim-only** lexicons that have no vendor equivalent (`inferenceJob`, `inferenceJobEvent`, `apiKey`).

## Substrate fit rules

A lexicon is portable to etzhayyim when **all** of the following hold:

1. No required RisingWave / Hyperdrive / Postgres-only field or referenced table (e.g. `schema_registry`).
2. No required commercial K8s control-plane primitive (Karmada CRD, VKE LoadBalancer, k3s API, etc.).
3. No required fiat payment processor (Stripe, PayPal, Square).
4. No required commercial SaaS dependency (RunPod, Linode GPU, OpenAI billed key from vendor account).
5. AT MST + IPFS + Base L2 + LanceDB-WASM + tonbo + yata CRDT cover the read/write path.

A lexicon may be PORT-adapted when the wire shape is substrate-neutral but a default value or description references vendor infrastructure. Adapt by updating defaults / descriptions only; keep the NSID and JSON Schema field shapes stable so vendor and religious-corp implementations can interop.

A lexicon is REJECT when its wire shape mandates RW / commercial K8s / fiat / SaaS in required fields (not just defaults). Document the rejection here; do not ship a half-stub.

## Related namespaces

- `00-contracts/lexicons/com/etzhayyim/apps/murakumo/` — application-level (`cronTick` etc.)
- `00-contracts/lexicons/com/etzhayyim/apps/murakumoFleet/` — fleet-level (`healthCheck` etc.)
- `00-contracts/lexicons/com/etzhayyim/murakumo/` — etzhayyim-only (`inferenceJob`, `inferenceJobEvent`, `apiKey`)
- `00-contracts/bpmn/com/etzhayyim/murakumo/` — BPMN process contracts
