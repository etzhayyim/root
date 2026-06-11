# etzhayyim-project-kuruma

Car information site for kuruma.etzhayyim.com — vehicle specs, reviews, comparisons, maker catalogs. Multi-DID actor graph (7 actor types). Multi-language (i18n.etzhayyim.com integration). Ad revenue target: 10M JPY/month.

## Architecture

```
Browser → kuruma.etzhayyim.com → XRPC /xrpc/{NSID}
                              ↓
           App: etzhayyim-wasm-kuruma-qewr7sl0 (performerType: service)
             ├─ Vehicle CRUD + Collection (NHTSA, Wikidata, Web Crawl)
             ├─ Multi-DID Actor Sync (44 entity DIDs: 30 makers + 4 dealers + 8 categories + 2 sources)
             ├─ Graph: Vehicle→Maker/Parts/Seller/Maintainer/Insurance/Registration
             ├─ Shinka: LLM social evolution (llm.etzhayyim.com, llama-3.1-8b)
             ├─ Kyumei-Koji: LLM fact gathering/validation (llm.etzhayyim.com, qwen2.5-coder-32b / deepseek-r1-distill)
             ├─ Web Crawl: CF Browser Rendering via Collection Job pipeline
             └─ Reactive pipeline: vehicle auto-validation on ingest
```

## LLM Integration (llm.etzhayyim.com)

| Feature | use_case | CF Workers AI Model | Interval |
|---|---|---|---|
| Shinka social post | `shinka` | llama-3.1-8b | 30min |
| Shinka engagement analysis | `shinka` | llama-3.1-8b | 3h |
| Kyumei-koji discover | `kyumei-koji` | qwen2.5-coder-32b | on-demand |
| Kyumei-koji gather | `kyumei-koji` | qwen2.5-coder-32b | on-demand |
| Kyumei-koji validate | `kyumei-koji-validate` | deepseek-r1-distill | 1.5h (auto) + on-demand |
| Kyumei-koji enrich | `kyumei-koji` | qwen2.5-coder-32b | on-demand |
| Reactive vehicle validation | `heartbeat` | llama-3.2-3b | on ingest |
| Crawl extraction plan | `kyumei-koji` | qwen2.5-coder-32b | on-demand |

## Commands (22)

| Command | Category | Description |
|---|---|---|
| `collect_nhtsa` | collect | NHTSA Vehicle API (US government) |
| `collect_wikidata_cars` | collect | Wikidata SPARQL (CC0) |
| `crawl_maker_page` | crawl | Web crawl job via CF Browser Rendering pipeline |
| `crawl_and_extract` | crawl | LLM extraction plan for automotive URL |
| `search_vehicles` | query | Search vehicles with filters |
| `list_makes` | query | Distinct makes with model counts |
| `list_models` | query | Models for a make |
| `get_vehicle` | query | Vehicle by model_id |
| `create_vehicle` | write | Manual vehicle record |
| `stats` | analytics | Vehicle statistics |
| `source_list` | query | Data sources with DIDs |
| `describe` | meta | Agent capabilities |
| `wave` | social | Greeting |
| `kyumei_discover` | kyumei-koji | Discover data sources for vehicle info |
| `kyumei_gather` | kyumei-koji | Analyze missing data, plan gathering |
| `kyumei_validate` | kyumei-koji | Validate vehicle record consistency |
| `kyumei_enrich` | kyumei-koji | Enrich partial data via LLM inference |

## Multi-DID Actor Types (7)

| Actor | DID Path Prefix | NSID Collection | ID Source |
|---|---|---|---|
| vehicle | `vehicle_{id}` | `com.etzhayyim.apps.kuruma.vehicle` | vehicle_id (VIN or slug) |
| maker | `maker_{slug}` | `com.etzhayyim.apps.kuruma.maker` | make_slug |
| parts | `parts_{part_number}` | `com.etzhayyim.apps.kuruma.parts` | OEM part number |
| seller | `seller_{dealer_id}` | `com.etzhayyim.apps.kuruma.seller` | dealer ID |
| maintainer | `maintainer_{shop_id}` | `com.etzhayyim.apps.kuruma.maintainer` | shop ID |
| insurance | `insurance_{provider_slug}` | `com.etzhayyim.apps.kuruma.insurance` | provider slug |
| registration | `registration_{plate_slug}` | `com.etzhayyim.apps.kuruma.registration` | plate slug |

## Graph Model

```
(:KurumaVehicle)-[:MANUFACTURED_BY]->(:Maker)
(:KurumaVehicle)-[:USES_PART]->(:Parts)
(:KurumaVehicle)-[:SOLD_BY]->(:Seller)
(:KurumaVehicle)-[:MAINTAINED_BY]->(:Maintainer)
(:KurumaVehicle)-[:INSURED_BY]->(:Insurance)
(:KurumaVehicle)-[:REGISTERED_AS]->(:Registration)
```

## Cross-App Follow

- `legal-entity` (le01corp0) → maker 法人情報
- `maps` (uqpel6i6) → seller/maintainer 所在地
- `llm` (llm8cf4ai) → LLM inference gateway

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-kuruma/wasm/etzhayyim-wasm-kuruma-qewr7sl0
etzhayyim deploy --smoke-url https://qewr7sl0.etzhayyim.com/health
```
