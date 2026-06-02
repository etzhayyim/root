# etzhayyim-project-naphtha-supply — Naphtha Supply Chain Intelligence

> **Runtime**: K8s pod-side LangServer / LangGraph Pregel. Cloudflare edge is only a proxy.

`naphtha-supply.etzhayyim.com` tracks refinery naphtha supply, splitters, terminals, steam-cracker and petrochemical demand, cargo movement, and regional price spreads.

## App Identity

| Key | Value |
|---|---|
| **nanoid** | `n4ph7h4` |
| **DID** | `did:web:naphtha-supply.etzhayyim.com` |
| **Runtime** | `k8s-langserver` |
| **Manifest** | `20-actors/naphtha-supply/actor-manifest.jsonld` |
| **Japan stress design** | `60-apps/etzhayyim-project-naphtha-supply/JAPAN_NAPHTHA_STRESS_DESIGN.md` |

## Graph Contract

### Vertex

- `vertex_naphtha_market_node` — refinery / splitter / export terminal / import terminal / steam cracker / petrochemical plant.
- `vertex_naphtha_cargo` — cargo identity, load/discharge ports, vessel IMO, quantity, laycan.
- `vertex_naphtha_price_assessment` — regional benchmark and spread snapshots.
- `vertex_naphtha_cracker_demand` — steam-cracker feedstock demand and substitution pressure.

### Edge

- `edge_naphtha_supply_link` — stable physical or contractual flow edge between market nodes.
- `edge_naphtha_cargo_route` — cargo-to-node route observations.
- `edge_naphtha_feedstock_to_derivative` — naphtha feedstock to olefins/aromatics derivative exposure.

### MV / Visualization Surface

- `mv_naphtha_supply_chain_trace` — edge-expanded node-to-node graph for map/network views.
- `mv_naphtha_country_balance` — supply/demand capacity balance by country.
- `mv_naphtha_cargo_flow` — load/discharge country flow totals.
- `mv_naphtha_price_latest` — latest benchmark assessment by region.

## LangServer / Pregel

LangServer owns orchestration and DB access. Pregel-style propagation should run over `mv_naphtha_supply_chain_trace` with node state stored in `vertex_langgraph_state`; do not implement long-running propagation inside an edge worker.

Recommended Pregel state:

- node pressure: supply deficit/surplus from `mv_naphtha_country_balance`
- edge weight: `capacity_tonnes_day` or observed cargo tonnage
- shock input: outage, sanction, route disruption, or price-spread change
- output: affected nodes, derivative families, and country exposure

Japan-specific stress analysis is defined in `JAPAN_NAPHTHA_STRESS_DESIGN.md`. It ranks exposed Japanese cracker operators and downstream packaging/resin users by combining cargo flow, country balance, price spreads, public disclosures, and bounded Pregel propagation.

## Seed / Reference Data

Use the CLI seed to load the first reference graph:

```bash
etzhayyim seed naphtha-supply --dry-run
etzhayyim seed naphtha-supply --env prod
```

The seed writes `vertex_naphtha_*`, `edge_naphtha_*`, and naphtha-related `vertex_product_grade` rows. RisingWave maintains `mv_naphtha_supply_chain_trace`, `mv_naphtha_country_balance`, `mv_naphtha_cargo_flow`, and `mv_naphtha_price_latest` incrementally.

## Cross-Actor Joins

- `oil-refining` supplies refinery identity and yield context.
- `oil-shipping` supplies vessel/cargo routing and dark-fleet risk.
- `oil-trading` supplies counterparty, contract and benchmark context.
- `oil-distribution` supplies product terminal context.
- `legal-entity` supplies operator / buyer / seller DID identity.
