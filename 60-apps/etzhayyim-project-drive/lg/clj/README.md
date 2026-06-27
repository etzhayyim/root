# lg-drive — Clojure port (langgraph-python → langgraph-clj, ADR-2606280030)

This is the **clj twin** of the FastAPI/LangGraph `lg_drive/*.py` backend. Same
canonical XRPC surface (`ai.etzhayyim.apps.drive.*`), same graph topology, same
handler behavior (concurrency / not-found / pagination / change-feed), persisted
on the same kotoba datomic graph (`drive-v1`).

## Coexistence (the `.py` is NOT removed)

The Python pod is **actively deployed** — `lg/Dockerfile` runs
`uvicorn lg_drive.server:app`, `lg/langgraph.json` points at
`lg_drive/graphs/health.py:GRAPH`, and `lg/pyproject.toml` declares the runtime.
Per the coexist discipline (the app is in active use), **every `.py` is kept**.
This clj port is verified standalone and runs in parallel; cutting the deploy
over to clj (Dockerfile/langgraph.json/Helm) is a follow-up, not part of this PR.

## Namespace map (1:1 with the Python modules)

| Clojure ns (`clj/lg_drive/…`) | Python twin | role |
|---|---|---|
| `lg-drive.edn` | `edn.py` | EDN tx-ops + scalar decode (`pr-str`/native keywords) |
| `lg-drive.ids` | `ids.py` | slug / eid / DID / AT-URI / resolve |
| `lg-drive.mapping` | `mapping.py` | canonical file ↔ `:drive/*` datoms |
| `lg-drive.kotoba-datomic` | `kotoba_datomic.py` | `transact`/`q`/`pull` (httpx→babashka.http-client, JSON→cheshire); CID byte-identical to Python |
| `lg-drive.store` | `store.py` | `DriveStore` protocol + `KotobaDriveStore` + `FakeDriveStore` |
| `lg-drive.handlers` | `handlers.py` | the 7 canonical method handlers (SSoT behavior) |
| `lg-drive.graphs.health` | `graphs/health.py` | langgraph-clj `StateGraph` health probe |
| `lg-drive.server` | `server.py` | FastAPI→httpkit; pure `route` dispatch + auth |

## Deviations from the Python (faithful, noted)

- **Sync, not async.** httpx's `AsyncClient` was only needed for async I/O;
  `babashka.http-client` is synchronous, so the store/handlers are synchronous.
  The graph topology and external behavior are unchanged.
- **Server.** FastAPI decorators → a single pure `route` fn + a babashka-httpkit
  ring adapter (`-main` / `bb serve`). Same 8 routes, same `x-api-key` enforcement.
- **Wire vs attr keys.** Wire/JSON `file` maps keep STRING keys (faithful to the
  JSON surface + the Python tests); `:drive/*` attr maps use keyword keys.

## Run

```bash
cd 60-apps/etzhayyim-project-drive/lg
bb run_tests.clj      # 13 tests / 38 assertions (8 ported handler + 5 graph/server)
bb serve              # httpkit XRPC server on :8000 (PORT overrides), kotoba-backed
```
