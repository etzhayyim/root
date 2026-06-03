# RisingWave Schema-Aware RAG Evaluation

Date: 2026-04-29

Scope: dense retrieval + RisingWave GraphAr schema-aware RAG + SQL/tool verifier + agent loop.

## Current Catalog Baseline

The live schema source is `30-graph/graph-schema/src/database.ts`, generated from RisingWave `information_schema`. The evaluator parses that file and builds a local schema catalog without scanning the 10TB+ Hummock/object-store data plane.

Run:

```bash
pnpm --dir 30-graph/graph-schema rag:evaluate
```

What the evaluator builds:

- Table catalog from generated `Database`.
- Column catalog from each `*Row` interface.
- Dense hashed token vectors for table/column metadata.
- Sparse table/column token scoring.
- Graph hints from table kind and naming structure (`vertex_`, `edge_`, `mv_`, `view_`, `dim_`).
- Read-only SQL verifier: SELECT-only, known tables, mandatory `LIMIT`.

This is intentionally a schema-plane benchmark. It measures whether the agent can select the right schema surface before it ever touches multi-TB data.

Current parsed catalog:

| Metric | Value |
|---|---:|
| Relations | 2,451 |
| Vertex tables | 1,547 |
| Edge tables | 431 |
| Materialized views | 403 |
| Plain views | 60 |
| Dimension tables | 5 |
| Columns | 40,946 |
| Avg columns / relation | 16.7 |
| Evaluation tasks with live-schema gold tables | 10 |

## Three Designs

| Design | Retrieval path | Hit@5 | Hit@20 | Recall@20 | Candidate tables | Estimated data read / question | p50 / p95 latency | Best use |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A. dense-only | Dense vector over table metadata | 0.80 | 1.00 | 0.81 | 80 | 180 GB | 6.5s / 18s | Simple semantic lookup |
| B. schema-aware hybrid | Sparse schema tokens + graph hints + dense rerank | 0.90 | 0.90 | 0.85 | 25 | 35 GB | 1.8s / 5.2s | Default RAG over RW schema |
| C. hybrid + verifier + agent loop | B + read-only SQL verifier + repair loop | 0.90 | 0.90 | 0.85 | 12 | 8 GB | 4.2s / 12s | Production agent workflow |

Interpretation for 10TB+ RW data:

- A is too scan-prone. Even when it finds a plausible table, it has weak join/index awareness.
- B is the best first-stage retriever. It avoids most data-plane cost by shrinking schema candidates before SQL generation.
- C is the best production shape. It spends more model/tool time, but avoids expensive bad queries and catches hallucinated tables before execution.

The latency and data-read values are design estimates for the 10TB+ data plane, not live cluster measurements. The retrieval metrics are from the local schema-plane evaluator.

Notable evaluation result:

- Dense-only has strong Hit@20 because schema names are descriptive, but lower Recall@20 and noisy top-5 candidates.
- Hybrid improves top-5 precision and recall for vector, legal, maps, BPMN, smartphone, yadoya, resource-flow, and agent-runtime tasks.
- JP fiscal still needs synonym/domain aliases: the retriever prefers fiscal coverage MVs over lower-level fiscal document/procurement tables.

## Architecture

```text
user task
  -> schema catalog retrieval
       dense metadata vector
       sparse table/column tokens
       graph/table-kind expansion
  -> prompt params
       top tables
       key columns
       relation hints
       stats/sketch references
  -> SQL/tool draft
  -> verifier
       SELECT only
       known tables
       LIMIT required
       EXPLAIN budget gate
  -> agent loop
       repair unknown table/column
       add predicates
       lower LIMIT
       switch to MV/view when available
  -> execute
  -> result check
```

## Production Recommendation

Use Design C for agent-facing workflows, but implement it as two layers:

1. Design B as a fast schema retriever.
2. Verifier/loop as a mandatory execution gate.

Dense embeddings should be limited to reranking already-small schema/doc candidates. They should not be the primary access path over the whole RW schema or the 10TB+ data plane.

## Trained Reranker Bench

Run:

```bash
pnpm --dir 30-graph/graph-schema rag:train
```

Artifact:

```text
80-data/reports/schema-aware-rag/schema-rag-reranker.json
```

This trains a lightweight pairwise linear reranker for schema table selection. It is not a base LLM fine-tune; it is the trained retrieval/ranking component that feeds LLM params for schema-aware RAG.

Training/eval setup:

| Metric | Value |
|---|---:|
| Train examples | 3,430 |
| Held-out examples | 1,472 |
| Bench sample | 309 |
| Epochs | 6 |
| Pairwise updates | 8 |

Bench result:

| Model | Hit@1 | Hit@5 | Hit@20 | MRR@20 |
|---|---:|---:|---:|---:|
| Dense-only | 0.608 | 0.735 | 0.832 | 0.665 |
| Heuristic hybrid | 0.951 | 0.990 | 1.000 | 0.971 |
| Trained hybrid reranker | 0.974 | 1.000 | 1.000 | 0.986 |

Interpretation:

- Training the small reranker improves top-rank selection over the hand-tuned hybrid.
- The gain is mostly in Hit@1 / MRR, which matters for SQL generation because the first selected table strongly biases the generated query.
- This is cheap to train because it operates on schema metadata only: 2,451 relations and 40,946 columns, not the 10TB+ data plane.

## Runtime Hook

Run:

```bash
pnpm --dir 30-graph/graph-schema rag:retrieve -- --query "legal corpus citation search by jurisdiction"
```

The runtime loads the trained reranker artifact and emits LLM params:

- ranked schema context
- table kind
- top columns
- related table hints
- SQL policy flags

It can also verify generated SQL before execution:

```bash
pnpm --dir 30-graph/graph-schema rag:retrieve -- \
  --query "legal corpus citation search by jurisdiction" \
  --sql "SELECT d.vertex_id, d.title FROM vertex_legal_corpus_document d WHERE d.jurisdiction = 'JP' LIMIT 20"
```

Current verifier checks:

- read-only `SELECT`
- known tables
- known qualified columns
- mandatory `LIMIT`
- warning on base vertex scans without `WHERE`
- warning on multi-table queries that should pass an `EXPLAIN` budget gate

## llm.etzhayyim.com / RunPod Gemma4

`llm.etzhayyim.com` is the independent RunPod OpenAI-compatible gateway. It is not a
Murakumo or `magatama-llm8cf4ai` pass-through path.

Current public model aliases:

- `gemma4-runpod`
- `tier0-runpod`
- `gemma4:26b-a4b-it-q4_K_M`

End-to-end schema RAG through `llm.etzhayyim.com`:

```bash
pnpm --dir 30-graph/graph-schema rag:llm -- \
  --model gemma4-runpod \
  --query "legal corpus citation search by jurisdiction" \
  --magatama-verified
```

The CLI performs:

1. trained schema retrieval
2. LLM SQL draft through `llm.etzhayyim.com`
3. local SQL verifier

### 2026-04-29 Deployment Check

`llm.etzhayyim.com` is served by the `etzhayyim-runpod` Cloudflare Worker. The route is:

```text
client -> llm.etzhayyim.com -> etzhayyim-runpod -> RunPod Serverless 3fctheq51haikt
       -> Ollama gemma4:26b-a4b-it-q4_K_M
```

Verification:

```bash
curl https://llm.etzhayyim.com/_app/meta
curl -H 'x-magatama-verified: true' https://llm.etzhayyim.com/v1/models
pnpm --dir 30-graph/graph-schema rag:evaluate
pnpm --dir 30-graph/graph-schema rag:train
```

`llm.etzhayyim.com/xrpc/com.etzhayyim.apps.llm.answerWithKnowledge` is intentionally not
served by this gateway:

```json
{
  "error": "unsupported_route"
}
```

The live schema-aware RAG run returned HTTP 200, RunPod model
`gemma4:26b-a4b-it-q4_K_M`, and SQL verifier `ok: true`.
