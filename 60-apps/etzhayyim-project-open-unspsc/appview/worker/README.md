# open-unispsc-appview Worker

XRPC AppView for the UNSPSC LangGraph Pregel fleet. ADR-2605180900 Phase 7.

Public surface at `https://unispsc.etzhayyim.com`. Proxies XRPC under
`/xrpc/com.etzhayyim.apps.unispsc.*` to the in-cluster `lg-open-unispsc`
langserver. The handler itself lives in
`@etzhayyim/kotodama-host-sdk/langserver-xrpc-handler` — this Worker is
just a thin CF Worker entry that supplies environment.

## Endpoints

```
POST /xrpc/com.etzhayyim.apps.unispsc.classify       # description -> top-K codes
POST /xrpc/com.etzhayyim.apps.unispsc.invokeAgent    # code -> agent.ainvoke(state)
GET  /xrpc/com.etzhayyim.apps.unispsc.listAgents     # paged registry
GET  /xrpc/com.etzhayyim.apps.unispsc.health         # lexicon health
GET  /health                                   # plain health probe
GET  /                                         # service banner
```

## Build / deploy

```bash
cd 60-apps/etzhayyim-project-open-unispsc/appview/worker
pnpm install
pnpm run deploy
```

`wrangler.jsonc` binds the Worker to the `unispsc.etzhayyim.com` custom
domain and sets `LG_UNISPSC_ENDPOINT` to
`https://lg-open-unispsc.etzhayyim.com`. To swap to a CF Service binding
(skips DNS, stays in-mesh), add `LG_UNISPSC` to `wrangler.jsonc` under
`services` — the handler picks it up automatically.

## Tests

The handler library is exercised by 13 vitest cases at
`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/test/langserver-xrpc-handler.test.ts`
(see PR for status). The Worker entry has no additional logic to test.
