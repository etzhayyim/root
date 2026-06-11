# etzhayyim-project-seigen-cue

Seigen DID actor for constraint governance.

## Goal
- Define hard limits and immutability rules as CUE.
- Persist policy artifacts in graph storage with Cypher.
- Enforce violations as build errors from CLI or MCP.

## Scope
- Provider: Cloudflare
- Product: Pipelines
- Baseline limits date: 2026-04-06

## Architecture
- `policy/cue/cloudflare-pipelines-limits.cue`: canonical policy schema/rules
- `policy/cypher/*.cypher`: graph persistence/read templates
- `70-tools/70-tools/70-tools/70-tools/70-tools/70-tools/scripts/lint/seigen-cue-lint.mjs`: CI/build linter (exit 1 on error)
- `70-tools/70-tools/70-tools/scripts/seigen/seigen-did-actor.mjs`: CLI + MCP actor interface

## CLI
```bash
pnpm run lint:seigen:pipelines
node 70-tools/70-tools/70-tools/scripts/seigen/seigen-did-actor.mjs lint --config rules/compliance/seigen/cloudflare-pipelines.input.example.json
node 70-tools/70-tools/70-tools/scripts/seigen/seigen-did-actor.mjs cypher-upsert --policy-id cf.pipelines.limits --version 2026-03-27
```

## MCP (stdio)
```bash
node 70-tools/70-tools/70-tools/scripts/seigen/seigen-did-actor.mjs mcp
```

Then send JSON lines:
```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"seigen.validate","arguments":{"configPath":"rules/compliance/seigen/cloudflare-pipelines.input.example.json","locale":"ja"}}}
```

## Publish Checklist
- Add this project metadata to your registry/index.
- Wire `pnpm run lint:seigen:pipelines` into required CI checks.
- Optionally set `SEIGEN_ENFORCE_CUE=1` to require local `cue vet` pass.
