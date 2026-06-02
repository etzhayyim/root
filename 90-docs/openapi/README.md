# OpenAPI 3.0 Specifications

Auto-generated OpenAPI 3.0 specifications from AT Protocol Lexicon documents.

## Overview

One `.openapi.json` spec per actor namespace under `00-contracts/lexicons/com/etzhayyim/`. Each spec documents all XRPC endpoints (queries, procedures) and record types for that actor.

## Tool

Generated using `@etzhayyim/lexicon-to-openapi` (70-tools/lexicon-to-openapi/).

## Specs

208 specs total, one per namespace:
- `actor.openapi.json`, `agent.openapi.json`, ... `yoro.openapi.json`
- Each contains `paths` (XRPC endpoints), `components.schemas` (record types)
- `baseUrl` set to `https://{actor}.etzhayyim.com`

## Regenerate

```bash
npx tsx 70-tools/lexicon-to-openapi/src/cli.ts 00-contracts/lexicons/com/etzhayyim 90-docs/openapi
```

## Usage

Use with OpenAPI tools (openapi-generator, openapitools, Swagger UI, etc.) to:
- Generate client SDKs in any language
- Validate XRPC requests/responses
- Generate API documentation
