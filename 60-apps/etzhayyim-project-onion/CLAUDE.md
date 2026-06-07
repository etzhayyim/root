# etzhayyim-project-onion — Dark Web Page Intelligence Platform

Multi-DID Site-per-DID Architecture で dark web (.onion) page をモデル化。malak (cybercrime intelligence) との cross-actor 統合。

## Architecture: 1 APP + Multi-DID (Site-per-DID)

```
onion.etzhayyim.com (single APP, 1 Worker)
  → 1 primary DID (coordinator)
    → N .onion site path-based DIDs (per hidden service)
      → Page records (per-URL AT records under site DID)
```

### DID Path Hierarchy

| Level | DID Representation | 例 |
|---|---|---|
| **APP** | primary DID | `did:web:onion.etzhayyim.com` |
| **Site** | path-based DID (depth 1) | `did:web:onion.etzhayyim.com:abc123def456` |
| **Page** | AT Record under site DID | `ai.etzhayyim.apps.onion.page` record |

### CONTROLS Chain

```sql
(:DID {id:"did:web:onion.etzhayyim.com"})
  -[:CONTROLS]->(:DID {id:"did:web:onion.etzhayyim.com:abc123def456"})
```

## W Protocol Event Stream Records (DID-scoped)

| Record Kind | Lexicon NSID | Writer DID | Key Fields |
|---|---|---|---|
| `onion.page` | `ai.etzhayyim.apps.onion.page` | Site DID | onion_url, title, content_hash, crawled_at, status_code, language, threat_indicators |
| `onion.crawl` | `ai.etzhayyim.apps.onion.crawl` | Site DID | onion_host, started_at, page_count, error_count, reachable |
| `onion.site` | `ai.etzhayyim.apps.onion.site` | Primary DID | onion_host, first_seen, last_seen, category, risk_score, reachable |

## Storage (kotoba Datom-native — ADR-2606071800)

Canonical state is the **kotoba Datom log**, read via **kotoba-kqe** and written via `transact`
(PDS → kagami). **No Hyperdrive / Kysely / RisingWave / SQL** anywhere in this app:

- the CF Worker (`wasm/.../src/app.ts`) reads with `sdk.graph.query` (kotoba-kqe) and writes
  with `sdk.pds.dispatch(createRecord)`;
- the BPMN crawl worker runs as a **py-kotodama primitive inside a kotoba-wasm component**
  ([`kotodama/`](kotodama/README.md)) over the same Datom log; the live Tor/darkweb fetch is
  operator-injected (no-server-key / G11).

The tables below are the **logical entity model** of those Datoms (`:vertex/kind
"vertex_onion_{site,page,crawl}"` + `:onion.{site,page,crawl}/*` attributes), not a SQL schema.

## Graph Schema (logical — kotoba Datoms)

| Node | Properties |
|---|---|
| `:OnionPage` | onion_url, onion_host, title, content_hash, crawled_at, status_code, language, threat_indicators |
| `:OnionSite` | onion_host, first_seen, last_seen, category, risk_score, reachable, mirror_clearnet |
| `:OnionCrawlSession` | session_id, onion_host, started_at, page_count, reachable |

| Edge | From → To |
|---|---|
| `:HOSTED_ON` | `:OnionPage` → `:OnionSite` |
| `:LINKS_TO` | `:OnionPage` → `:OnionPage` |
| `:MIRRORS` | `:OnionSite` → `:WebDomain` (clearnet mirror) |
| `:THREAT_LINKED` | `:OnionSite` → `:ThreatActor` (malak cross-ref) |

## Cross-Project Links

| Link | 用途 |
|---|---|
| `etzhayyim-project-malak` | Threat actor tracking, OSINT enrichment |
| `etzhayyim-project-yabai` | Risk scoring, AML/sanctions flagging |
| `etzhayyim-project-webpage` | Clearnet mirror detection, cross-reference |

## Sensitivity & Governance

- **performerType**: `service`
- **profile.sensitivity**: `confidential` (dark web intelligence)
- **defaultFollowApproval**: `required` (access control)

## Crawl ownership (kotoba-wasm + py-kotodama — ADR-2606071800)

The active darkweb crawl is driven by the BPMN contract and executed by a **py-kotodama worker
running in a kotoba-wasm component** (the legacy LangServer/k8s pod + Hyperdrive path is retired):

| Layer | Component | Role |
|---|---|---|
| L7 BPMN | `00-contracts/bpmn/com/etzhayyim/onion/crawlSeeds.bpmn` (timer-start `R/PT6H` + manual) | Cadence + audit; `onion.crawl.{queueSeeds,processQueue}` + `generic.audit.emit` service tasks |
| L8 Worker | `60-apps/etzhayyim-project-onion/kotodama/onion_crawl.py` (py-kotodama primitive, **kotoba-wasm**) | `queueSeeds`: append-only seed `vertex_onion_site` Datoms + claim stalest (NULL-first) as `:queued` runs. `processQueue`: operator-injected Tor/darkweb fetch → append `vertex_onion_page` Datoms + close runs. **kotoba-kqe reads + `transact` writes — no Hyperdrive/SQL.** Live fetch is no-server-key/G11 (default `:gated`). |
| L3 Dispatcher | `wasm/etzhayyim-wasm-onion-0n10n001/src/app.ts` (CF Worker) | Read XRPCs (`listSites`/`listPages`/`getStats`) via `sdk.graph.query`; `seedCrawl` enqueue via `sdk.pds.dispatch(createRecord)` (`last_seen=NULL`; next BPMN tick claims). No outbound HTTP to darkweb-proxy from this Worker. |

`seedCrawl` returns `{seeded, hosts, note}` — `note` informs the caller that crawling happens on
the next BPMN tick (≤6h). Handlers are pure over an injected `KotobaCtx`; the kotoba-wasm host
binding supplies `query`/`transact` in production, an in-memory fake under test.

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-onion/wasm/etzhayyim-wasm-onion-0n10n001
ETZHAYYIM_ALLOW_NON_ALPHA_SEGMENTS=1 etzhayyim deploy
```

Pod bump (only when `kotodama/primitives/onion_crawl.py` changes):

```bash
cd 40-engine/kotoba/crates/kotoba-kotodama/py && docker buildx build --platform linux/amd64 \
  --tag ghcr.io/etzhayyim/kotodama:onion-crawl-$(date -u +%Y%m%d-%H%M%S)-$(git rev-parse --short=11 HEAD) --push .
helm -n mitama-udf upgrade mitama-udf-pool ./50-infra/vultr/mitama-udf-pool \
  --reuse-values --set image.tag=<new-tag>
```
