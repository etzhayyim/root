# lg-media-gamers — Clojure port (langgraph-clj)

clj twin of the Python LangGraph app (`../lg_media_gamers/`), per **ADR-2606280030**
(langgraph-python → langgraph-clj). **Coexists** with the Python package: the live
deploy (`../Dockerfile` + `../langgraph.json`) still runs the Python LangGraph
server, so **no `.py` was removed** — this directory is the verified clj twin
pending a runtime cutover.

## Layout

```
media_gamers/
  llm.cljc                  _chat helper → babashka.http-client + cheshire, Murakumo loopback default
  audit.cljc                emit_audit / emit_audit_bg → http-client fire-and-forget (future)
  games.cljc                SEED_GAMES / moods / compute_quality / build_prompt (pure)
  graphs/health.cljc        START→check→audit→END
  graphs/ingest_charts.cljc START→fetch→persist→analyze→audit→END
  graphs/guide_generator.cljc resolve→generate→evaluate─cond→[translate]→commit→audit
  graphs/autopilot.cljc     resolve_mood→select_game→generate→evaluate─cond→[translate]→commit→post→audit
  server.cljc               GRAPHS registry + NSID map + camel→snake + xrpc dispatch
tests/test_smoke.cljc       clojure.test (20 tests / 56 assertions)
run_tests.clj               repo-rule runner (NOT .sh)
bb.edn                      app-scoped (langgraph-clj/langchain-clj pinned; cheshire/http-client = bb built-in)
```

## Verify

```bash
cd 60-apps/etzhayyim-project-media-gamers/lg/clj
bb run_tests.clj      # or: bb test
```

## Port deviations (faithful where noted)

- **RisingWave removed** (substrate boundary, ADR-2605262130): `ingest_charts`
  `persist` built RW `vertex_game_chart_*` INSERTs via psycopg; the clj twin
  builds content-addressable kotoba **EAVT datoms** (`entries->datoms` /
  `analysis->datoms`) and returns the same snapshot count. Live kotoba-log append
  is a gated operator leg (deferred); the loop does no DB write. `health`'s RW
  connectivity probe → `:store-ok false` placeholder (kotoba probe deferred).
- **RunPod fallback dropped** (ADR-2605215000): the LLM helper defaults to the
  **Murakumo loopback** (LiteLLM 127.0.0.1:4000, no-server-key); RunPod is only
  used if its env is explicitly set, preserving the try-each-endpoint topology.
- **HTTP transport not ported**: `server.cljc` ports the dispatch LOGIC (registry,
  NSID map, XRPC body transform, invoke) the python smoke tests assert on, not the
  FastAPI/uvicorn transport. A bb HTTP server on top is a follow-up.
- **pokopia_research coexists unported**: it is a thin re-export of a kotodama
  python graph (`kotodama.langgraph_graphs.pokopia_research_agent_loop`); kotodama
  itself is unported, so the name stays in the registry (NSID/langgraph.json
  parity) but is not in the compiled clj `graphs` map.
- `checkpointer.py` / `cron.py` (postgres saver + APScheduler) are server-runtime
  glue, not graph logic — not ported in this pass (coexist).
