# houki XRPC Adapter

CF Worker that exposes the 9 rw-free commands as XRPC endpoints.

## Endpoints

### Document Registry (Slice 1)
- `POST /xrpc/ai.gftd.houki.ingestDocument` — ingest document
- `POST /xrpc/ai.gftd.houki.ingestText` — ingest text snippet
- `GET /xrpc/ai.gftd.houki.getDocument?documentId=...` — fetch document + metadata
- `GET /xrpc/ai.gftd.houki.listDocuments?authorDid=...` — paginated documents

### Rules & Bundles (Slice 2)
- `POST /xrpc/ai.gftd.houki.extractRules` — LLM-extract compliance rules
- `GET /xrpc/ai.gftd.houki.listRules?ruleSeq=...` — paginated rules
- `GET /xrpc/ai.gftd.houki.getRuleBundle?bundleId=...` — fetch bundle
- `GET /xrpc/ai.gftd.houki.listRuleBundles?registrarDid=...` — paginated bundles
- `POST /xrpc/ai.gftd.houki.registerRuleBundle` — cross-actor bundle registration

## Setup

```bash
cd 60-apps/ai-gftd-project-houki/xrpc-adapter
npm install
```

## Development

```bash
npm run dev
# Worker listens on http://localhost:8787
```

## Deploy

```bash
wrangler deploy
# Deploys to houki.etzhayyim.com/xrpc/*
```

See ADR-2605210000 for design context.
