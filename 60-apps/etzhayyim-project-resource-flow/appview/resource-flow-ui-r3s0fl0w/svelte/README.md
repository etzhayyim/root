# resource-flow-ui-r3s0fl0w

Svelte 5 (runes mode) AppView for `resource-flow.etzhayyim.com`.

- Calls `com.etzhayyim.apps.resourceFlow.getSankey` via `atproto.etzhayyim.com` PDS pipethrough (or same-origin when served from `resource-flow.etzhayyim.com`).
- Renders `mv_resource_flow_sankey_*` edges with `d3-sankey`. Aggregation key is `COALESCE(root_did, source_did)` per ADR-0074; the AppView simply renders whatever the MV returns.
- Resolves counterparty labels via `app.bsky.actor.getProfile` (works for both `did:web:hospitality.etzhayyim.com:actor:chain:*` and ERC725 root DIDs once `did:erc725` profile resolution is wired into the PDS).

## Build

```bash
cd 60-apps/etzhayyim-project-resource-flow/appview/resource-flow-ui-r3s0fl0w/svelte
pnpm install
pnpm build      # → ./dist/
```

The Worker's `wrangler.jsonc` mounts `./dist/` at `/` via `assets.directory = "../appview/resource-flow-ui-r3s0fl0w/svelte/dist"`. `not_found_handling: "single-page-application"` so deep links fall back to `index.html`. XRPC + MCP paths still resolve through the Worker fetch handler.

## Filters

| Param | Default | Notes |
|---|---|---|
| `flowClass` | `currency` | One of `currency` / `service` / `personnel` |
| `domain` | `hospitality` | Resolves to ISIC code list inside the Worker (see `DOMAIN_INDUSTRY` map) |
| `fiscalPeriod` | (any) | ISO 8601 `YYYY-MM` / `YYYY-Qn` / `YYYY` |

`?flowClass=currency&domain=hospitality&fiscalPeriod=2026-04` is the default sankey for the yadoya pilot.
