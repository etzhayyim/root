# 50-infra/k8s/atproto-pds

> **Status: `bridge-only` — per ADR-2606242330** (PDS consolidation).
> Bun reference `@atproto/pds` (SQL + B2) — NOT on the kotoba substrate. Kept as the
> interim production PDS *only* until `50-infra/etzhayyim-atproto-pds-clj` (canonical,
> clj-on-kotoba) reaches server/repo/identity parity, then retired. **Do not add new
> features here** — they belong in the clj-on-kotoba PDS / kotoba-server (ADR-2606015002).

K8s pod replacement for the `atproto.etzhayyim.com` PDS CF Worker (`etzhayyim-pds-2603241700`).

**ADR**: [`90-docs/adr/2605111300-pds-to-pod-bun-container.md`](../../../90-docs/adr/2605111300-pds-to-pod-bun-container.md)

**Status**: P0 (planning + scaffolding committed 2026-05-11). Not yet deployed.

## Layout

| File | Purpose |
|---|---|
| `Dockerfile` | Bun container image build (multi-stage: deps → bun build → runtime) |
| `bun-entry.ts` | Runtime entry — wraps existing CF Worker Hono `app.fetch` in `Bun.serve` + maps CF bindings to env-driven adapters |
| `deployment.yaml` | Pod with 2 containers: `pds` (Bun) + `cloudflared` (CF Tunnel sidecar) |
| `service.yaml` | ClusterIP for in-cluster callers + tunnel target |
| `secrets-template.yaml` | Template for `atproto-pds-secrets` + `atproto-pds-tunnel-token` (replace placeholders before apply) |
| `RUNBOOK.md` | Operational steps (build, deploy, cutover, rollback) |

## Why

ADR-2605111200 prohibits CF Worker → Kotoba/Datomic connections. The PDS is currently
a CF Worker with 38 source files that directly query Kotoba/Datomic via Hyperdrive.
This pod replaces that runtime location while keeping the same TS codebase
(Bun is a Node-API-compatible runtime, so no rewrite is needed).

## Not deployed yet

Until P1 (Bun image build + canary deploy) completes, the live `atproto.etzhayyim.com`
endpoint continues to be served by the CF Worker. The hyperdrive binding in
`50-infra/cloudflare/workers/atproto/wrangler.jsonc` was temporarily reverted
in `70-tools/scripts/migrations/2605111300-revert-infra-hyperdrive-binding.mjs`
to keep prod alive until pod cutover lands.

## See also

- `50-infra/vultr/geth-private/manifests/` — precedent for cloudflared sidecar pattern
- `50-infra/k8s/open-lei-mcp/README.md` — same RUNBOOK style
- ADR-2605111200 — the policy this pod satisfies
