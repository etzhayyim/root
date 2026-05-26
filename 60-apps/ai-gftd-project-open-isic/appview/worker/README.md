# open-isic-appview Worker

XRPC AppView for the ISIC Rev. 4 LangGraph Pregel fleet. ADR-2605180900 Phase 7.

Public surface at `https://isic.etzhayyim.com`. Proxies XRPC under
`/xrpc/app.etzhayyim.apps.isic.*` to the in-cluster `lg-open-isic` langserver.
Same shape as `open-unispsc-appview`; the only difference is the taxonomy
binding and the inclusion of the `hierarchicalClassify` lexicon.

## Endpoints

```
POST /xrpc/app.etzhayyim.apps.isic.classify                # description -> top-K
POST /xrpc/app.etzhayyim.apps.isic.hierarchicalClassify    # section -> ... -> class
POST /xrpc/app.etzhayyim.apps.isic.invokeAgent             # classCode -> agent
GET  /xrpc/app.etzhayyim.apps.isic.listAgents              # paged registry
GET  /xrpc/app.etzhayyim.apps.isic.health                  # lexicon health
GET  /health                                         # plain k8s probe
GET  /                                               # service banner
```

## Build / deploy

```bash
cd 60-apps/ai-gftd-project-open-isic/appview/worker
pnpm install
pnpm run deploy
```

`wrangler.jsonc` binds the Worker to `isic.etzhayyim.com` and sets
`LG_ISIC_ENDPOINT` to `https://lg-open-isic.etzhayyim.com`. The
underlying langserver pod can be empty (Phase 3 fills it) — the
hierarchicalClassify endpoint correctly returns an escalated empty path.

## Tests

Handler library covered by 13 vitest cases at
`20-actors/magatama/sdk/magatama-host-sdk/test/langserver-xrpc-handler.test.ts`.
