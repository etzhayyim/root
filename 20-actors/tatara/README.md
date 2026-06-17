# tatara 鑪 — world manufacturing-plant + logistics geographic KG

> Tier-B · R0 design-only · ADR-2606171800 · `did:web:etzhayyim.com:actor:tatara`

**Where on Earth the world's manufacturing physically sits** — at what scale (employment / floor
area / production capacity), feeding which logistics corridor — on the kotoba Datom log. The
geographic / facility-scale layer of the supply lineage: **kabuto 兜** (who supplies whom) +
**uchiwake 内訳** (the product BOM) + **tatara** (where the facilities are) + **watari 渡り** (live
craft) + **watatsuna 綿津綱** (cables), all composing over one shared chokepoint vocabulary.

Mirror-lineage sibling of kabuto / tsumugi / inochi: edge-primary geographic **concentration**
(per-sector country HHI + chokepoint export-dependence) routed to **redundancy / reshoring** — a
resilience map, **never a target-list** (G2).

## The worker-data boundary (read this)

`:plant/headcount-est` is the **disclosed aggregate** facility-employment figure — a SIZE, like
floor area or market-cap. There is **no `:worker/*` / `:person/*` attribute** anywhere: an
individual worker, their pace, location, or shift is **structurally unrepresentable** (G4 —
Charter Rider §2(c) reciprocity axis; Wellbecoming §1.13). Enforced by construction and by tests.

## Run

```bash
bb 20-actors/tatara/run_tests.sh
# Testing tatara.methods.test-analyze … Ran 9 tests / 403 assertions.  0 failures.
# Testing tatara.methods.test-kotoba  … Ran 5 tests / 546 assertions.  0 failures.
# Testing tatara.methods.test-autorun … Ran 5 tests / 1213 assertions. 0 failures.
# Testing tatara.methods.test-lexicons… Ran 4 tests / 44 assertions.   0 failures.
# Testing tatara.methods.test-crosscheck Ran 4 tests / 20 assertions.  0 failures.
# ── tatara: ALL suites green ──   (27 tests / 2,756 assertions)

# kabuto-linkage crosscheck → out/kabuto-crosscheck.md (21/25 = 84% linkage)
bb -cp 20-actors -e "(require 'tatara.methods.crosscheck)(tatara.methods.crosscheck/-main)"

# concentration report → out/concentration-report.md
bb -cp 20-actors -e "(require 'tatara.methods.analyze)(tatara.methods.analyze/-main)"

# autonomous heartbeat → LOCAL append-only kotoba Datom log (commit-DAG)
bb -cp 20-actors -e "(require 'tatara.methods.autorun)(tatara.methods.autorun/-main)"

# the three globes (open the .htm in a browser)
bb -cp 20-actors -e "(require 'tatara.viz.build-viz)(tatara.viz.build-viz/-main)"
#   viz/plant-globe.htm          — (C) world plants by sector + export flows
#   viz/world-supply-globe.htm   — (A) plants + live craft + chokepoint composition
#   ../watari/viz/craft-globe.htm — (B) watari's first visualization
```

## What's in the seed (R0, `:representative`)

28 real public plants across 9 sectors / 12 countries — semiconductor (TSMC ×2, Samsung, Intel, SK
hynix), automotive (Hyundai, Toyota, VW, Tesla, Ford), battery (CATL, LG, Tesla, Northvolt), steel
(POSCO, Baowu, Nippon Steel, Tata Steel), chemicals (BASF, SABIC), electronics (Foxconn), aerospace
(Boeing, Airbus, Embraer), shipbuilding (HD Hyundai), pharma (Pfizer, Serum Institute) — + 6
logistics hubs + 28 export flows keyed on shared chokepoints.

Top chokepoint export-dependence in the seed: **malacca 11 plants · luzon-strait 7 · suez-red-sea 5 ·
gibraltar 4 · panama 2 · hormuz 1 · taiwan-strait 1** — these compose with watari (live vessel
transit) and watatsuna (submarine-cable load) over the same keywords.

## Files

| path | what |
|---|---|
| `00-contracts/schemas/manufacturing-plant-ontology.kotoba.edn` | ontology (`:plant/* :hub/* :flow/* :concentration/*`) |
| `data/seed-plant-graph.kotoba.edn` | bounded `:representative` seed |
| `methods/analyze.cljc` | concentration / HHI / chokepoint / capacity engine |
| `methods/kotoba.cljc` | content-addressed EAVT commit-DAG persistence |
| `methods/autorun.cljc` | autonomous heartbeat → content-addressed commit-DAG (resume-safe) |
| `methods/crosscheck.cljc` | measures :plant/operator ⇄ kabuto :company/id linkage (84%) + ingest worklist |
| `00-contracts/lexicons/com/etzhayyim/tatara/*.json` | write surface (registerPlant/registerHub/recordFlow) |
| `methods/test_{analyze,kotoba,autorun,lexicons,crosscheck}.cljc` | 27 tests / 2,756 assertions |
| `viz/build_viz.cljc` | globe generator (derives all coords from the seeds) |
| `viz/plant-globe.htm` · `viz/world-supply-globe.htm` | the (C) and (A) globes |
| `manifest.jsonld` · `CLAUDE.md` | actor manifest + agent rules |

Live ingest (company disclosures / GLEIF / OSM facility geometry) is G7 Council+operator-gated.
