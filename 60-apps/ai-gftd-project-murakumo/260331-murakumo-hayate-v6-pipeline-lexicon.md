# Murakumo Hayate V6 Pipeline Lexicon + CLI

Namespace: `ai.gftd.murakumo.*`

## NSID Step Map

1. `ai.gftd.murakumo.planPipeline`
2. `ai.gftd.murakumo.graphExtract`
3. `ai.gftd.murakumo.graphIngest`
4. `ai.gftd.murakumo.coverageExport`
5. `ai.gftd.murakumo.fleetPlan`
6. `ai.gftd.murakumo.trainExperts`
7. `ai.gftd.murakumo.evalV6`
8. `ai.gftd.murakumo.runPipeline`

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
gftd murakumo xrpc --nsid ai.gftd.murakumo.graphExtract --payload-file payload.json
```

## Data Path Contract

- Graph extraction output: `/Volumes/251220/graph_results/*.jsonl`
- Graph ingest tables: `graph_entities`, `graph_relations` in `/Volumes/251220/lancedb`
- Coverage export: `/Volumes/251220/coverage_domains`
- Fleet inputs: `/Volumes/251220/expert_domains`
- Yata graph path: `/Volumes/251220/yata`
