# browser-agent — Clojure twin (ADR-2606280030)

Idiomatic clj/bb port of the Python `browser_agent` package (Genspark-like
Sparkpage search synthesis). Coexists with `src/browser_agent/*.py` — the Python
stays because it is wired to a live deploy (`Dockerfile` CMD, `langgraph.json`).
**No `.py` was removed.**

## Module map (python → clj)

| python | clj namespace | notes |
|---|---|---|
| `state.py` | `etzhayyim.browser-agent.state` | pydantic `BaseModel` → plain maps; `operator.add` reducers → `apply-update` |
| `tools.py` | `etzhayyim.browser-agent.tools` | `httpx` → `babashka.http-client`; `bs4` → regex `extract-text`; json → `cheshire` |
| `nodes.py` | `etzhayyim.browser-agent.nodes` | `asyncio.gather` → futures; `ChatOpenAI` → injectable `*chat-complete*` (Murakumo loopback, ADR-2605215000) |
| `graph.py` | `etzhayyim.browser-agent.graph` | langgraph StateGraph (1 conditional back-edge) → functional `run-graph` loop |
| `server.py` | `etzhayyim.browser-agent.server` | aiohttp SSE → `org.httpkit.server`; token-stream events dropped (non-streaming chat seam) |

All deps are bundled in babashka — no external deps, no langgraph-clj needed.

## Run

```bash
bb test          # clojure.test suite (offline; network stubbed)
PORT=8000 bb serve
```

`GET /health` · `POST /search {"query": "...", "page_url": "..."}` → SSE of
`phase` / `source` / `section` / `error` events, terminated by `data: [DONE]`.

## Substrate boundary

RisingWave/psycopg state is not ported here; per ADR-2605312345 any persisted
state goes through an injectable kotoba-Datom-log store seam (the python's
`langgraph-checkpoint-postgres` is deploy-only and untouched).
