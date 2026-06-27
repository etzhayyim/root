# lg-open-patent (clj twin)

Clojure-native port of the Python LangGraph server in `../lg/`, per
**ADR-2606280030** (langgraph-python → langgraph-clj). **WAVE 2.**

This twin is **additive**. The Python FastAPI server (`../lg/`, `langgraph.json`,
`Dockerfile`, Helm) remains the **deployed runtime** for
`open-patent.etzhayyim.com`. The clj twin runs alongside until a human cuts over;
nothing here changes the Python deployment.

## Run

```bash
bb test          # clojure.test suite (run_tests.clj)
bb run_tests.clj # same, explicit
```

## Layout

| clj ns | ports | notes |
|---|---|---|
| `graphs.health` | `graphs/health.py` | START→check→END, `{:ok true}` (exact) |
| `graphs.ingest-multi` | `graphs/ingest_multi.py` → kotodama | Follow-based ingest: subscribe→enrich→persist→emit_audit |
| `graphs.synthesize-invention` | `graphs/synthesize_invention.py` → kotodama | gather_tech_trends→synthesize_seeds→search_prior_art→assess_novelty→flag_for_review→emit_audit |
| `server` | `server.py` | GRAPHS / NSID-MAP registry + `/ok` `/health` `/runs` `/xrpc` dispatch |
| `cron` | `cron.py` | reads the SAME `../lg/langgraph.json` crons (drift guard) |
| `store` | RisingWave layer | injectable `PatentStore` seam — Fake (default/tests) + kotoba Datom log |
| `kotoba-datomic` | psycopg/RW | substrate-clean persistence target (XRPC, no RisingWave) |
| `llm` | RunPod/vLLM call | Murakumo loopback only (ADR-2605215000), injectable `*chat*` |

## Faithfulness & deviations

- **Topology** matches the Python graphs node-for-node where the source is
  available (`health`) and matches the **documented** pipeline (app `CLAUDE.md`)
  for `ingest_multi` / `synthesize_invention` — whose Python bodies are thin
  re-exports of `kotodama.langgraph_graphs.*`, a package **not vendored** in this
  checkout. The HITL novelty threshold (≥ 60 → `status='review'`) and seed
  temperature (0.6) follow `CLAUDE.md`.
- **No RisingWave** (substrate boundary): `psycopg`/`vertex_open_patent_*` →
  injectable `PatentStore` seam, kotoba-Datom-log target. **No checkpointer** port
  (RW-compat `_RwAsyncPostgresSaver` is RW-specific); the clj graphs are pure.
- `httpx`→`babashka.http-client`, JSON→`cheshire`, FastAPI/uvicorn→dispatch fns
  (HTTP wiring is the deploy layer's job, like the wave-1 twins), LLM→Murakumo
  loopback. No `RetryPolicy` (not in langgraph-clj) — graphs are linear.
- **The Python is the runtime; `py_removed = 0` is correct.**
