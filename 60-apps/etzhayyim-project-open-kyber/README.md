# open-kyber — Open Source ERP (APQC-aligned)

Apache-2.0 ERP built on AT Protocol + APQC PCF + BPMN 2.0 + OCEL 2.0.

Source-of-truth for the Kyber ERP product. The etzhayyim tenancy runs at `kyber.etzhayyim.com` (this monorepo); the original etzhayyim tenancy at `kyber.etzhayyim.com` remains a separate managed deployment of the same codebase. Fork this repo to run your own instance.

## What's inside

- **ERP Worker** (`etzhayyim-wasm-kyber-erp-kyb3rerp/`) — 24 XRPC commands across accounting (double-entry GL, IFRS/JP-GAAP CoA), AP/AR, HR, procurement, inventory, sales, fixed asset depreciation, and governance/risk controls. Hono + Svelte SPA included.
- **APQC/BPMN Projector** (`etzhayyim-wasm-kyber-projector-kyb3proj/`) — reactive onCommit consumer that maps ERP records to APQC PCF 13 L1 + BPMN 2.0 task catalog (28 tasks) and emits OCEL 2.0 events to RisingWave.
  Includes compatibility XRPCs for `process group` / `process` / `activity` callers.
- **Multi-DID** — 7 department writers (`did:web:kyber.etzhayyim.com:dept:*` — accounting, hr, procurement, inventory, sales, asset, governance) + 13 APQC L1 path DIDs on the projector.

## Architecture

```
Client → XRPC /xrpc/com.etzhayyim.apps.kyber.*
      → ERP Worker (kyb3rerp)
      → com.atproto.repo.createRecord → PDS
      → onCommit → Projector (kyb3proj)
      → emit com.etzhayyim.apps.apqc.apqcEvent
      → RisingWave streaming MV → getApqcCoverage
```

See `CLAUDE.md` for the full design and ADR-0025 for the consolidation rationale (13-WASM → 1 Worker, Shannon η 0.08 → 0.95).

## Not included

Payroll, FX revaluation, consolidation, tax filing, bank feed, Signal E2E encryption. Bring your own PDS, graph store, auth, and Tier 3 PII store.

## Quickstart

```bash
# ERP
cd etzhayyim-wasm-kyber-erp-kyb3rerp && pnpm install && etzhayyim deploy

# Projector
cd etzhayyim-wasm-kyber-projector-kyb3proj && pnpm install && etzhayyim deploy

# Bootstrap projector from ERP side
curl -X POST https://<your-erp>/xrpc/com.etzhayyim.apps.kyber.initApqcProjector \
  -H 'content-type: application/json' -d '{}'
```

## License

Apache-2.0. Instances publish records as `isBot: true` per AT Protocol AI-Agent profile convention.
