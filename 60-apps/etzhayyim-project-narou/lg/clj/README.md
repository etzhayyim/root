# lg-narou — langgraph-clj port (ADR-2606280030)

clj/bb twin of `lg_narou/**.py`: the narou LangGraph graphs + OSS server,
ported langgraph-python → **langgraph-clj** per ADR-2606280030 (and the
repo-wide clj/bb rule). **Coexistence: the `.py` modules are unchanged and
still drive the live deploy** (`langgraph.json` graphs → `*.py:GRAPH`,
`Dockerfile` → `uvicorn lg_narou.server:app`). Nothing is retired; the clj
port runs alongside until a human flips the runtime.

## Layout (`clj/` source root, scoped `bb.edn`)

| clj ns | file | py twin | what it is |
|---|---|---|---|
| `lg-narou.audit` | `lg_narou/audit.cljc` | `audit.py` | fire-and-forget OCEL `generic.audit.emit` → bpmn-dispatcher (`babashka.http-client` + `cheshire`) |
| `lg-narou.graphs.health` | `lg_narou/graphs/health.cljc` | `graphs/health.py` | StateGraph `check-rw → summarize → emit-audit` |
| `lg-narou.graphs.agent-chat` | `lg_narou/graphs/agent_chat.cljc` | `graphs/agent_chat.py` | StateGraph `resolve-actor → llm-call → emit-audit` (5 writer personas) |
| `lg-narou.cron` | `lg_narou/cron.cljc` | `cron.py` | cron spec loader + `_rotateSceneByEpoch` fire-input shaping |
| `lg-narou.server` | `lg_narou/server.cljc` | `server.py` | httpkit server: `/ok /health /runs /runs/stream /xrpc/{nsid} /threads/{tid}/state` |

`checkpointer.py` is **intentionally not ported** — it is a RisingWave/Postgres
`AsyncPostgresSaver` subclass, and the charter deprecates RisingWave in favour
of the kotoba Datom log (ADR-2605262130/2605312345). langgraph-clj checkpoints
are datomic-isomorphic; the clj server compiles graphs without it.

## Run (bb)

```
bb run_tests.clj        # 29 tests / 52 assertions (clojure.test)
bb test                 # same, via the scoped bb.edn task
bb server 8080          # boot the httpkit server (= server.py FastAPI)
```

## Faithful-port deviations (same topology, same endpoints)

- `httpx → babashka.http-client`, `json → cheshire`, `FastAPI/uvicorn → org.httpkit.server`.
- **agent_chat** inference default endpoint changed RunPod-proxy → **Murakumo
  loopback** (`127.0.0.1:4000`, ADR-2605215000); `VLLM_URL` still overrides.
- **health** RW check: psycopg `SELECT 1` → TCP-reachability probe (no PG driver
  under bb; `:rw-probe` injectable). Proves reachability, not SQL.
- Per-node `RetryPolicy` (langgraph-python) has no langgraph-clj add-node
  equivalent → dropped (nodes are already fail-soft; errors returned in state).
- **cron**: APScheduler crontab scheduling not reimplemented (narou ships
  `crons: []`); spec-loading + fire-input shaping ported faithfully.
- `/runs/stream` computes events then flushes as SSE (not incrementally streamed);
  JSON output keys are kebab (clj state) rather than snake.
- HTTP/LLM are injectable (`:llm-post`, `:rw-probe`) so every node is testable
  with no network.
