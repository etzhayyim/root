> **DEPRECATION NOTICE (ADR-2605215000):** The Arrow-Flight UDF server and `@udf` decorators are **superseded**. All functions have been ported to pure, in-process kotoba-native modules at `kotoba/udf_kotoba.py` and `kotoba/kiyo_kotoba.py` (which default to Murakumo loopback inference). The original files and this server deployment remain only for the vendor RisingWave cluster until it is decommissioned.

# risingwave-udf — External Python UDF server

ADR-0044 compliant External Python UDF server for RisingWave. Arrow Flight
gRPC on :8815. Deployed as LKE sidecar next to RW compute (namespace `risingwave`).

## Functions

| Name                      | Signature                                  | io_threads | Purpose                                               |
| ------------------------- | ------------------------------------------ | ---------: | ----------------------------------------------------- |
| `cosine_similarity`       | `(double[], double[]) → double`            |          1 | feature vector cosine (pure CPU)                      |
| `posterior_update`        | `(double, double) → double`                |          1 | Bayesian single-step posterior                        |
| `news_source_credibility` | `(varchar, boolean, boolean) → double`     |          1 | news.etzhayyim.com primary/official-source provenance score |
| `news_intel_priority`     | `(int, int, int, double, double) → double` |          1 | news.etzhayyim.com intel dispatch priority score            |
| `segment_hash`            | `(jsonb) → varchar`                        |          1 | sha256 k-anonymity grouping key                       |
| `gmm_fit`                 | `(double[], int) → jsonb`                  |          1 | GMM single-row assignment                             |
| `classify_t3`             | `(varchar, varchar, varchar) → varchar`    |     **50** | yabai T3 LLM gray-zone phishing classifier (ADR-0032) |

All functions declared with `@udf(..., io_threads=N)` per ADR-0044 §D3. IO-bound
functions (any HTTP fetch / LLM call) MUST set `io_threads` >= 20 (default 1
silently caps throughput at SDK gRPC pool ≈7.5 parallel).

## Files

- `udf_server.py` — arrow_udf 0.3.1 server, all 5 functions.
- `requirements.txt` — arrow-udf, pyarrow, numpy, sklearn.
- `Dockerfile` — python:3.12-slim with env knobs (`LLM_URL`, `T3_IO_THREADS`).
- `deploy.sh` — build → push ghcr.io/etzhayyim/risingwave-python-udf → kubectl apply.

## Register with RisingWave

Migration: `30-graph/graph-schema/migrations/20260421170000_udf_external_python_fix_and_classify_t3.ts`

**DDL form** (ADR-0044 §D3) — no `LANGUAGE` clause for External UDFs:

```sql
CREATE FUNCTION classify_t3(subject varchar, from_addr varchar, body_preview varchar)
  RETURNS varchar
  AS 'classify_t3'
  USING LINK 'http://risingwave-udf.risingwave.svc:8815'
```

**Anti-pattern** (silent failure on prod cluster 2026-04-16 → 2026-04-21 audit):

```sql
-- ❌ WRONG — cluster rejects with "python UDF is not enabled in configuration"
CREATE FUNCTION ... LANGUAGE python AS name USING LINK '...'
```

`LANGUAGE python` is reserved for embedded (disabled by default). External UDFs
identify themselves solely via `USING LINK` and the remote arrow-flight protocol.

## Deploy

```bash
# Build + push + apply (in-cluster sidecar, namespace=risingwave)
./deploy.sh

# Or piecewise
./deploy.sh build
./deploy.sh push
./deploy.sh apply
```

Manifest: `50-infra/linode/risingwave-iceberg/kustomize/base/python-udf.yaml`
(referenced from `kustomization.yaml` as of 2026-04-21).

## Env knobs (container)

| Var               | Default                                              | Purpose                                         |
| ----------------- | ---------------------------------------------------- | ----------------------------------------------- |
| `UDF_PORT`        | `8815`                                               | Arrow Flight port                               |
| `LLM_URL`         | `http://ollama.inference.svc:80/v1/chat/completions` | in-cluster Ollama (bypasses CF routing-gateway) |
| `LLM_MODEL`       | `gemma4:e4b`                                         | default model                                   |
| `LLM_TIMEOUT_SEC` | `8`                                                  | per-call timeout                                |
| `T3_IO_THREADS`   | `50`                                                 | classify_t3 concurrency (ADR-0044 recommended)  |

## Bench (empirical, 2026-04-21)

50 rows × 500 ms mock LLM latency (local docker RW 2.8.2, host-docker bridge):

| io_threads | total ms |      rps |    effective parallelism |
| ---------: | -------: | -------: | -----------------------: |
|          1 |     3024 |     16.5 | ~8 (SDK gRPC pool bound) |
|         20 |     1519 |     32.9 |                      ~16 |
|     **50** |  **527** | **94.9** |  **~47** (95% efficient) |

Projection for gemma4:e4b real (~2 s):

- io_threads=50 → ~33 rps = 1 instance covers **1,980 emails/min**.
- Cron (100 emails / 15 min) = 0.11 rps sustained → trivial load.

## Troubleshooting

### "Invalid Parameter Value: python UDF is not enabled in configuration"

Your DDL has `LANGUAGE python`. Remove it — External UDFs use only `AS 'name' USING LINK '...'`.

### UDF returns JSON with `"reason":"error:URLError"` or `error:HTTPError`

The UDF server can't reach `LLM_URL`. In-cluster: `ollama.inference.svc:80` must be reachable
from `risingwave` namespace (cross-namespace ClusterIP resolves by default).

### Low throughput despite `io_threads=50`

Check `LLM_TIMEOUT_SEC` isn't firing (fallback `{"reason":"error:TimeoutError"}`). Increase for
slow models or reduce `num_predict`. Also: the SDK gRPC server thread pool is ≈8 by default;
confirm `io_threads` kwarg is present on the `@udf(...)` decorator (default 1 caps parallelism).

### `DROP FUNCTION` hangs

RW doesn't drop an external UDF cleanly if inflight calls exist. Scale UDF deployment to 0
replicas first, then DROP, then scale back.

## Related

- ADR-0044 — UDF language strategy
- ADR-0032 — yabai T1/T2/T3 classifier tiers (T3 uses this server)
- ADR-0026 — cohort posterior_update / segment_hash callers
- `deps.toml [[conventions]]` "RisingWave UDF language strategy"
- `30-graph/graph-schema/migrations/20260421170000_udf_external_python_fix_and_classify_t3.ts`
