# Japan Naphtha Stress Design

Date: 2026-05-14

This design turns Japan's naphtha pressure into a graph-backed LangServer/Pregel workflow for `did:web:naphtha-supply.etzhayyim.com`.

## Current Assessment

Japan's exposed companies are concentrated in three layers:

- Upstream petrochemical producers / cracker operators: Mitsubishi Chemical, Mitsui Chemicals, Idemitsu Kosan, ENEOS, Maruzen Petrochemical / Cosmo, Asahi Kasei Mitsubishi Chemical Ethylene, Sumitomo Chemical-linked Chiba operations.
- First-hop derivative producers: polyethylene, polypropylene, styrene monomer, acrylonitrile, polycarbonate, films, solvents, aromatics, synthetic rubber.
- Downstream buyers that feel shortages before the chemical balance looks catastrophic: food packaging, ink, films, adhesive, coating, auto resin, appliance resin, fibers.

Observed stress drivers:

- Japan relies materially on imported naphtha; recent public reporting cites roughly 60% import dependence and high Middle East exposure.
- Japanese naphtha-fed steam cracker utilization has fallen sharply in 2026 reporting, with March utilization reported at a record-low level.
- Mitsubishi Chemical has already cut ethylene output due to possible naphtha supply issues.
- Idemitsu / Mitsui, ENEOS, Maruzen, and western Japan operators are already restructuring or planning cracker consolidation, so a feedstock shock lands on an already low-utilization system.
- Asahi Kasei disclosed derivative restructuring while noting AMEC-related facilities continue to run and have naphtha procurement prospects for the time being.

Primary sources checked:

- JPCA ethylene production history: https://www.jpca.or.jp/english/04ethylen_product/index.htm
- Japan Times on Mitsubishi Chemical output cuts and Japan import dependence: https://www.japantimes.co.jp/business/2026/03/10/companies/mitsubishi-chemical-cut-ethylene-production/
- Japan Times on Japan securing several months of naphtha needs: https://www.japantimes.co.jp/news/2026/04/05/japan/japan-naphtha-needs/
- Hydrocarbon Processing / JPCA report on March 2026 run rate: https://www.hydrocarbonprocessing.com/news/2026/04/japans-ethylene-plant-run-rate-hits-record-low-of-686-in-march/
- ICIS on Asahi Kasei restructuring and AMEC status: https://www.icis.com/explore/resources/news/2026/05/12/11206506/asahi-kasei-to-discontinue-sm-pe-production-from-fy2030-amid-oversupply
- ICIS on Idemitsu / Mitsui Chiba consolidation: https://www.icis.com/explore/resources/news/2024/10/09/11039520/idemitsu-kosan-mitsui-chem-s-japan-cracker-merger-moves-to-feed-phase
- ChemOrbis on ENEOS Kawasaki closure plan: https://www.chemorbis.com/en/plastics-news/Japan-s-ENEOS-plans-permanent-closure-of-Kawasaki-cracker/2025/02/27/926654

## Company Risk Map

| Company / group | Supply-chain role | Stress signal | Graph representation |
|---|---|---|---|
| Mitsubishi Chemical | Cracker operator and derivative producer | Ethylene output cuts due to possible feedstock shortage | `vertex_naphtha_market_node` for Kashima/Osaka/Kamus; `vertex_naphtha_cracker_demand`; edge to ethylene/propylene derivatives |
| Mitsui Chemicals | Cracker operator, Chiba/Osaka, derivative producer | Alternative procurement and consolidation exposure | Chiba/Osaka nodes; term supply edges; derivative exposure edges |
| Idemitsu Kosan | Refiner, cracker operator, naphtha supplier | Potential shutdown warning under prolonged Hormuz disruption; Chiba consolidation | Refinery/export node plus Chiba cracker demand and supply edges |
| ENEOS | Refiner / petrochemical operator | Kawasaki cracker closure plan by FY2027/2028 | Kawasaki node with declining capacity and planned closure status |
| Maruzen Petrochemical / Cosmo | Chiba petrochemical producer | Chiba cracker closure/consolidation exposure | Chiba cracker node; consolidation edge to Keiyo/partner operations |
| Asahi Kasei / AMEC | Mizushima ethylene and derivatives | Procurement prospects exist, but derivative restructuring and import/feedstock sensitivity remain | Mizushima node; stable-but-monitored status; downstream SM/PE/ACN edges |
| Packaging / ink / food manufacturers | Downstream demand | Shortage appears as films, ink, bags, trays, adhesive constraints | Downstream `product:*` derivative nodes linked from olefins/aromatics |

## Supply-Chain Graph Model

Use the existing naphtha graph as the physical backbone:

- `vertex_naphtha_market_node`: JP refinery, import terminal, steam cracker, petrochemical plant.
- `vertex_naphtha_cargo`: cargoes with load/discharge country, port, laycan, tonnage.
- `vertex_naphtha_price_assessment`: CFR Japan / MOPJ and competing regional prices.
- `vertex_naphtha_cracker_demand`: daily feedstock demand by cracker.
- `edge_naphtha_supply_link`: refinery/import terminal/cracker supply lane.
- `edge_naphtha_cargo_route`: observed cargo route.
- `edge_naphtha_feedstock_to_derivative`: cracker-to-ethylene/propylene/BTX/styrene/PE/PP/film/ink exposure.

Japan-specific extensions should be additive:

- Add JP nodes: Kashima/Kamus, Chiba, Osaka, Mizushima, Kawasaki, Keiyo, Yokkaichi, Sodegaura.
- Add company operator DID in `operator_did` and link to `vertex_legal_entity` when present.
- Encode planned closures or consolidation as `status = planned_closure | consolidating | monitored`.
- Add downstream derivative product vertices using existing `vertex_product_grade` before creating new tables.
- Model packaging/ink stress as derivative exposure edges first; only add new tables if we need product-level order book or inventory.

## LangServer Design

Runtime: pod-side `k8s-langserver`; Cloudflare/SvelteKit remains a proxy.

LangServer task surface:

- `naphtha.jp.ingestNewsSignals`: parse public disclosures/news into shock candidates.
- `naphtha.jp.upsertCompanyExposure`: upsert JP company/operator nodes and derivative exposure edges.
- `naphtha.jp.computeBalance`: query `mv_naphtha_country_balance`, `mv_naphtha_cargo_flow`, `mv_naphtha_price_latest`.
- `naphtha.jp.runPregelStress`: run bounded propagation from Japan cracker/import nodes.
- `naphtha.jp.brief`: generate company-level incident brief with evidence and uncertainty.

Inputs:

- `mv_naphtha_country_balance` for JP supply/demand gap.
- `mv_naphtha_cargo_flow` for Japan-bound naphtha lane stress.
- `mv_naphtha_price_latest` for CFR Japan / Asia spread pressure.
- company disclosure/news signals with source URL and timestamp.
- manual shock event: `hormuz_disruption`, `cracker_maintenance`, `planned_closure`, `cargo_delay`, `price_spike`, `demand_cut`.

Outputs:

- `vertex_langgraph_state` rows keyed by `naphtha.jp.<run_id>.<node_id>`.
- ranked company exposure list.
- affected derivative families and downstream product families.
- recommended watchlist queries for cargoes, run rates, price spreads, and closure/consolidation dates.

## Pregel Design

Graph: `naphtha_supply_chain_japan_stress`

Source table: `mv_naphtha_supply_chain_trace`

State table: `vertex_langgraph_state`

Supersteps:

1. Seed: initialize JP import terminal and cracker nodes with shock scores.
2. Supply propagation: propagate upstream cargo/supply delay and capacity pressure through `edge_naphtha_supply_link`.
3. Demand absorption: subtract cracker demand and planned capacity from node state.
4. Derivative propagation: fan out to ethylene, propylene, BTX, SM, PE, PP, film, ink and packaging nodes.
5. Company aggregation: aggregate affected nodes by `operator_did` / legal entity.
6. Briefing: persist top exposed companies and explanation.

Node state:

```json
{
  "node_id": "naphtha-node:chiba-cracker",
  "country_code": "JP",
  "operator_did": "did:web:mitsuichemicals.com",
  "supply_pressure": 0.0,
  "demand_pressure": 0.0,
  "price_pressure": 0.0,
  "closure_pressure": 0.0,
  "downstream_pressure": 0.0,
  "confidence": 0.0,
  "evidence": []
}
```

Message:

```json
{
  "src": "naphtha-node:jurong-terminal",
  "dst": "naphtha-node:chiba-cracker",
  "grade_code": "NAPH-L",
  "capacity_tonnes_day": 2800,
  "shock_type": "cargo_delay",
  "shock_score": 0.65,
  "evidence_url": "https://..."
}
```

Risk score:

```text
risk =
  0.30 * supply_pressure
+ 0.25 * demand_pressure
+ 0.20 * price_pressure
+ 0.15 * downstream_pressure
+ 0.10 * closure_pressure
```

Confidence:

```text
confidence =
  min(1.0,
    0.35 * source_freshness
  + 0.25 * source_reliability
  + 0.20 * graph_connectivity
  + 0.20 * cargo_or_price_observation
  )
```

Halting:

- max 6 supersteps
- stop early when max delta in company risk < 0.03 for two consecutive supersteps
- do not propagate from low-confidence news-only shocks beyond two hops without cargo/price support

## Initial Ranking Logic

Highest immediate concern:

1. Mitsubishi Chemical: disclosed ethylene output cut and broad derivative exposure.
2. Idemitsu Kosan: Chiba/Yamaguchi ethylene exposure and consolidation path with Mitsui.
3. Mitsui Chemicals: major Chiba/Osaka cracker exposure, alternative procurement pressure, and consolidation dependency.
4. Maruzen Petrochemical / Cosmo: Chiba cracker closure/consolidation exposure.
5. ENEOS: Kawasaki cracker planned closure plus refining/petrochemical supply role.
6. Asahi Kasei / AMEC: Mizushima derivative exposure; current procurement appears less acute but still structurally exposed.
7. Packaging/ink/film buyers: often show operational pain before upstream balances fully fail.

This ranking should be recomputed by Pregel using fresh cargo, price, run-rate and disclosure signals, not hard-coded in the app UI.
