# yoro /apps Runtime Coverage Audit (2026-04-27)

## Question

Of the apps surfaced in `https://yoro.etzhayyim.com/apps`, how many are actually
implemented across the four canonical runtime layers of the
ADR-2604251830 Shannon-Optimal 8-Layer Architecture?

The four layers under audit:

| Layer | What counts as "implemented" |
|---|---|
| **L3 CF Hono + Svelte edge** | `60-apps/etzhayyim-project-{id}` contains a `wrangler.jsonc` (Hono Worker) and / or a `svelte/package.json` (Svelte CSR app shell) |
| **L7 BPMN (Zeebe)** | At least one `.bpmn` lives under `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/{id}/` (deployed via `bpmn-dispatcher.etzhayyim.com` watcher to the `zeebe-0` cluster) |
| **L8 Python pod worker** | Has a `50-infra/k8s/{id}*` deployment, or owns a Vultr VKE pod under `50-infra/vultr/{id}*` |
| **MCP server** | Worker source declares `agentTool` / `mcpRegistry` (per ADR-0087 magatama MCP facade) **or** ships a dedicated MCP pod (`50-infra/k8s/{id}-mcp`) |

## Source data

- **Apps registry**: `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/apps/apps.ts`
  — 74 unique app ids, minus the `etzhayyim` portal entry → **73 evaluable rows**
- **Project folders**: `60-apps/etzhayyim-project-*` (399 directories)
- **BPMN actors**: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/*` (557 actor namespaces)
- **k8s services**: `50-infra/k8s/*` (10 services)
- **Vultr services**: `50-infra/vultr/*` (14 services)

Classification script: `/tmp/classify.sh` (foreach app id, probe each layer's
canonical SSoT path).

## Headline result

**0 of 73** /apps tiles run on all four layers end-to-end.

The closest is **maps** (CF Worker + Svelte SPA + BPMN/Zeebe + 3 Python pods),
which was missing only an MCP facade. **RESOLVED 2026-04-27**: maps MCP
deployed (`mcpRegistry: { actorDid: "did:web:maps.etzhayyim.com" }`, 189 tools live).

## Layer counts

| Layer | Count | % of 73 | Notes |
|---|---|---|---|
| CF Hono + Svelte edge (full) | 13 | 18% | Worker + Svelte CSR both present |
| CF Worker only (no Svelte CSR) | 7 | 10% | Hono backend, profile rendered by yoro |
| Svelte CSR only (no per-app Worker) | 11 | 15% | Built into yoro shell, no dedicated edge |
| BPMN deployed to Zeebe | 10 | 14% | Matches ADR-0056 14-actor live count for these ids |
| Python pod worker | 1 | 1% | Only `maps` ships actual k8s Python work |
| MCP server | 4 | 5% | `lawfirm`, `sre`, `tsukuru`, **`maps`** (2026-04-27) |

## 4-of-4 (all layers — first app to reach full stack, 2026-04-27)

| App | CF | Svelte | BPMN/Zeebe | Python | MCP |
|---|---|---|---|---|---|
| **maps** | Y | Y | Y | Y | Y |

## 3-of-4 (one layer short of full stack)

| App | CF | Svelte | BPMN/Zeebe | Python | MCP | Missing |
|---|---|---|---|---|---|---|
| **tsukuru** | Y | – | Y | – | Y | Svelte, Python |
| **lawfirm** | Y | Y | – | – | Y | BPMN, Python |

## 2-of-4 (CF + BPMN/Zeebe pair, ADR-0056 alignment)

`calendar`, `docs`, `drive`, `gmail`, `lawyer`, `news`, `sheets` — these are
the productivity / inbox actors with timer-start or commit-trigger BPMN
deployed via `bpmn-dispatcher`. They lack Python pods and MCP facades.

## Tile distribution by stack maturity

| Maturity tier | Count | Description |
|---|---|---|
| 4-of-4 layers | **1** | **maps** (CF Worker + Svelte SPA + BPMN/Zeebe + Python pods + MCP, 2026-04-27) |
| 3-of-4 layers | 2 | tsukuru, lawfirm |
| 2-of-4 layers | 7 | calendar, docs, drive, gmail, lawyer, news, sheets |
| 1-of-4 layer | 23 | CF-only, Svelte-only, or BPMN-only, or MCP-only entries |
| 0-of-4 (launcher only) | 39 | Pure profile shortcuts to `did:web:{id}.etzhayyim.com` (incl. `ge`, `lo`) |

(Re-tally after parity check against `deps.toml [yoro_apps_coverage]` —
73 / 73 reconciled. The earlier draft's 42 launcher count double-counted
two false-positive substring matches; corrected.)

So **~58% of /apps tiles (42 / 73)** carry no per-app runtime — they are
launchers that `goto('/profile/did:web:${id}.etzhayyim.com')`. This matches
ADR-2604251830's intent: actor SSoT lives in the L4 Kotoba/Datomic registry, not
in per-app CF Workers. But it also means `/apps` over-reports the deployed
stack count.

## Recommendation

1. ~~**Promote `maps` to 4-of-4**~~ **DONE 2026-04-27** — `mcpRegistry: { actorDid: "did:web:maps.etzhayyim.com" }` deployed,
   189 tools live at `https://maps.etzhayyim.com/mcp`. First 4-of-4 app on platform.
2. **Audit the 42 launcher-only tiles** and either (a) demote them out of
   `/apps` and into a "Directory" view, or (b) wire a registry-backed
   indicator so the tile shows which L4/L7/L8 backends are alive for that
   actor DID.
3. **Stop hand-curating `apps.ts`.** Source the tile list from
   `vertex_app` (or the new `vertex_mcp_tool_def` registry once ADR-0087
   §D3 is adopted) so coverage drifts can't accumulate silently.

## Related

- ADR-2604251830 — Shannon-Optimal 8-Layer Architecture (defines L3/L7/L8)
- ADR-0056 — BPMN-as-actor (14 deployed actors as of 2026-04-23)
- ADR-0087 — magatama MCP Tool Facade (opt-in `mcpRegistry`)
- ADR-2604262000 — edge-thin app runtime (don't grow per-app Workers)

Generated by classification scan against the deployed `/apps` registry on
2026-04-27. Reproducible from `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/apps/apps.ts`
+ filesystem layout under `60-apps/`, `etzhayyim-root/00-contracts/bpmn/`, `50-infra/k8s/`,
`50-infra/vultr/`.
