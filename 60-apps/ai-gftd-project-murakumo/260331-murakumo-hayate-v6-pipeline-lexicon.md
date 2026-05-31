# Murakumo Hayate V6 Pipeline Lexicon + CLI

Namespace: `app.etzhayyim.murakumo.*`

## NSID Step Map

1. `app.etzhayyim.murakumo.planPipeline`
2. `app.etzhayyim.murakumo.graphExtract`
3. `app.etzhayyim.murakumo.graphIngest`
4. `app.etzhayyim.murakumo.coverageExport`
5. `app.etzhayyim.murakumo.fleetPlan`
6. `app.etzhayyim.murakumo.trainExperts`
7. `app.etzhayyim.murakumo.evalV6`
8. `app.etzhayyim.murakumo.runPipeline`

Lexicon JSON files live under:
`60-apps/ai-gftd-project-murakumo/lexicons/ai/gftd/murakumo/*.json`

## gftd CLI Mapping

- `gftd murakumo plan`
- `gftd murakumo graph-extract --labels <comma labels> --output /Volumes/251220/graph_results/graph_entities.jsonl`
- `gftd murakumo graph-ingest --input /Volumes/251220/graph_results --lancedb-uri /Volumes/251220/lancedb --push-yata`
- `gftd murakumo coverage-export --output /Volumes/251220/coverage_domains`
- `gftd murakumo fleet-plan --data-dir /Volumes/251220/expert_domains --target-slots 500000`
- `gftd murakumo train-experts --n-labels 8 --samples-per 5000 --epochs 2`
- `gftd murakumo eval --mode quick --cypher`

Generic XRPC invocation:

```bash
gftd murakumo xrpc --nsid app.etzhayyim.murakumo.graphExtract --payload-file payload.json
```

## Data Path Contract

- Graph extraction output: `/Volumes/251220/graph_results/*.jsonl`
- Graph ingest tables: `graph_entities`, `graph_relations` in `/Volumes/251220/lancedb`
- Coverage export: `/Volumes/251220/coverage_domains`
- Fleet inputs: `/Volumes/251220/expert_domains`
- Yata graph path: `/Volumes/251220/yata`
