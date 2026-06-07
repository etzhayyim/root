# onion crawl — py-kotodama worker (kotoba-wasm, Datom-native)

The BPMN process `onion_crawl_seeds`
(`00-contracts/bpmn/com/etzhayyim/onion/crawlSeeds.bpmn`, timer `R/PT6H` + manual) drives the
darkweb crawl. Its two `zeebe:taskDefinition` types are handled by `onion_crawl.py`, which runs
as a **py-kotodama primitive inside a kotoba-wasm component** — NOT the legacy LangServer/k8s
pod that wrote `vertex_onion_*` rows directly via Hyperdrive.

## Why this exists (ADR-2606071800)

The previous design violated the substrate boundary: a k8s pod + the `app.ts` Worker both
reached `vertex_onion_*` over **Hyperdrive/Kysely** (RisingWave-over-Postgres). Per
ADR-2605262130 / ADR-2605312345 the kotoba **Datom log is the first-class canonical state** and
the read path is **kotoba-kqe**. This worker is the kotoba-native replacement:

```
                       ┌──────────────── kotoba-wasm component ───────────────┐
 BPMN job (Zeebe)  ──▶ │  dispatch(task_type, job, ctx)                        │
   onion.crawl.*       │    ├─ handle_queue_seeds   (ctx.query / ctx.transact) │ ──▶ kotoba
                       │    └─ handle_process_queue (ctx.query / ctx.transact) │     Datom log
                       │  ctx = kotoba host binding (kqe Datalog + transact)   │
                       └──────────────────────────────────────────────────────┘
```

- **No Hyperdrive / Kysely / SQL.** State is read with `ctx.query` (kotoba-kqe Datalog) and
  written with `ctx.transact` (append Datoms → PDS/kagami land them on the log).
- **Pure handlers over an injected `KotobaCtx`.** The handlers are identical in-wasm (host
  binding) and under test (in-memory fake); the wasm wiring is the only seam.

## BPMN IO contract (matches crawlSeeds.bpmn)

| task type | inputs | outputs |
|---|---|---|
| `onion.crawl.queueSeeds` | `seeds[]`, `category`, `limit` | `queued`, `skipped`, `runs` |
| `onion.crawl.processQueue` | `runs`, `timeoutSec` | `processed`, `completed`, `failed`, `gated`, `pagesWritten` |
| `generic.audit.emit` | (platform) | — |

- **queueSeeds** — append new `vertex_onion_site` Datoms (append-only; existing hosts not
  duplicated), then claim the `limit` stalest sites (NULL `last-seen` first) as `:queued`
  `vertex_onion_crawl` runs.
- **processQueue** — for each run, call the **injected fetcher**, append `vertex_onion_page`
  Datoms, and close the run (`:completed` / `:failed`) + stamp the site's `last-seen`.

## no-server-key / G11 — the live fetch is operator-gated

The live darkweb fetch (Tor + `darkweb-proxy.etzhayyim.com` + Playwright CF Container) is an
**injected capability**, never a key this worker holds. Without an operator-provided fetcher,
`process_queue` marks each run `:gated` (neither completed nor failed) so it stays claimable for
a later authorized run. The default `_gated_fetch` refuses.

## Run the tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q test_onion_crawl.py   # 10 tests
python3 test_onion_crawl.py                                                  # standalone
```

## Production wiring (the kotoba-wasm seam)

The kotoba-wasm component supplies a `KotobaCtx` backed by the `kotoba` host import
(`datalog`/`transact`), then calls `dispatch(job.type, job.variables, ctx, fetch=<operator>)`
for each Zeebe job and returns the result as the BPMN output variables. The Datalog reads use
the canonical `[:find … :where [?e :vertex/kind "vertex_onion_site"] …]` shape over the Datom
log — no projection layer, no SQL.
