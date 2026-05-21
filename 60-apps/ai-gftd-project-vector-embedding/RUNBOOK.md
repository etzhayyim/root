# Vector Embedding Backfill Runbook

This runbook starts the Phase 1 actor/post embedding backfill.

## 1. Build Runtime Image

The current runtime image in Kubernetes must include:

- `pymagatama.primitives.vector_embedding`
- `pymagatama.vector_embedding_worker_main`
- `pymagatama.vector_embedding_ops`

Build and push a new image from `20-actors/magatama/py` before scaling the
worker:

```sh
cd 20-actors/magatama/py
docker buildx build --platform linux/arm64 \
  -t ghcr.io/gftdcojp/pymagatama:yoro-vector-embedding-20260427-arm64 \
  --push .
```

Then update
`50-infra/multicluster/murakumo-vke/yoro-actors/vector-embedding-worker.yaml`
to use that image tag.

## 2. Deploy BPMN

```sh
cd 20-actors/magatama/py
AGENTGATEWAY_MCP_URL="$AGENTGATEWAY_MCP_URL" \
  uv run python -m pymagatama.vector_embedding_ops deploy \
  --bpmn ../../../etzhayyim-root/00-contracts/bpmn/ai/gftd/vector-embedding/backfillBatch.bpmn
```

## 3. Apply Worker Manifest

```sh
kubectl apply -f 50-infra/multicluster/murakumo-vke/yoro-actors/vector-embedding-worker.yaml
kubectl -n yoro-actors scale deploy/yoro-vector-embedding-worker --replicas=1
```

The CronJobs are suspended by default.

Optional Hume AI emotion enrichment:

- Set `HUME_API_KEY` in `yoro-actor-runtime-secrets`.
- Keep `VECTOR_EMBEDDING_HUME=1` on the worker.
- If the key is absent, the worker writes BGE-M3 vectors and reports Hume as
  skipped instead of failing the batch.

## 4. Start Dry Run

```sh
cd 20-actors/magatama/py
AGENTGATEWAY_MCP_URL="$AGENTGATEWAY_MCP_URL" \
  uv run python -m pymagatama.vector_embedding_ops start \
  --surface posts \
  --limit 10 \
  --dry-run
```

## 5. Start Small Write Batch

```sh
cd 20-actors/magatama/py
AGENTGATEWAY_MCP_URL="$AGENTGATEWAY_MCP_URL" \
  uv run python -m pymagatama.vector_embedding_ops start \
  --surface posts \
  --limit 25
```

Verify in RisingWave:

```sql
SELECT model_id, space_id, modality, count(*)
FROM vertex_vector_embedding_768
GROUP BY model_id, space_id, modality;

SELECT model_id, top_emotion, count(*)
FROM vertex_vector_emotion_signal
GROUP BY model_id, top_emotion;
```

Enable scheduled backfill only after small batches are healthy:

```sh
kubectl -n yoro-actors patch cronjob yoro-vector-embedding-posts \
  -p '{"spec":{"suspend":false}}'
```

Keep `yoro-vector-embedding-actors` suspended until post throughput and
RisingWave write pressure are measured.

To backfill Hume emotion signals for already embedded rows without creating new
vectors:

```sh
cd 20-actors/magatama/py
AGENTGATEWAY_MCP_URL="$AGENTGATEWAY_MCP_URL" \
  uv run python -m pymagatama.vector_embedding_ops start \
  --surface posts \
  --limit 25 \
  --emotion-only
```

The Kubernetes manifest also includes suspended emotion-only CronJobs:

```sh
kubectl -n yoro-actors create job \
  --from=cronjob/yoro-vector-emotion-posts \
  yoro-vector-emotion-posts-manual-$(date +%Y%m%d%H%M%S)
```

Keep `yoro-vector-emotion-actors` suspended until actor profile embedding volume
and Hume latency are measured. Enable schedules only after one manual job writes
rows into `vertex_vector_emotion_signal`.
