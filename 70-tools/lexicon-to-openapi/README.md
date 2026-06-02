# @etzhayyim/lexicon-to-openapi

Generate OpenAPI 3.0 specifications from AT Protocol Lexicon JSON files.

## Purpose

This tool converts AT Protocol Lexicon documents (structured JSON schemas) into machine-readable OpenAPI 3.0 specifications. This enables:

- **API Documentation**: Auto-generated, human-readable API docs from lexicon sources
- **Client SDK Generation**: Use OpenAPI-to-SDK tools (openapi-generator, etc.)
- **Tooling**: IDE completion, API testing clients (Postman, Insomnia, etc.)
- **Validation**: Contract-first API design and conformance checking

## Installation

```bash
npm install --save-dev @etzhayyim/lexicon-to-openapi
```

Or use directly from the monorepo:

```bash
cd 70-tools/lexicon-to-openapi
npm run build
```

## Usage

### CLI

```bash
# Generate from default directories
npx lexicon-to-openapi

# Specify custom paths
npx lexicon-to-openapi <LEXICON_ROOT> <OUTPUT_DIR>

# Example
npx lexicon-to-openapi 00-contracts/lexicons/com/etzhayyim 90-docs/openapi
```

**Behavior**:
- Recursively scans each top-level actor namespace directory under `LEXICON_ROOT`
- Collects all `.json` files with `lexicon: 1` and `id` fields
- Generates one OpenAPI spec per actor (e.g., `kiyo.openapi.json`)
- Writes to `OUTPUT_DIR`

### Programmatic

```typescript
import { lexiconsToOpenApi } from "@etzhayyim/lexicon-to-openapi";

const spec = lexiconsToOpenApi(
  [
    {
      lexicon: 1,
      id: "com.etzhayyim.kiyo.getPaper",
      defs: { main: { type: "query", /* ... */ } }
    }
  ],
  {
    title: "Kiyo XRPC API",
    version: "0.1.0",
    baseUrl: "https://kiyo.etzhayyim.com"
  }
);

// spec is a valid OpenAPI 3.0.3 object
console.log(JSON.stringify(spec, null, 2));
```

## Lexicon to OpenAPI Mapping

| Lexicon | OpenAPI |
|---------|---------|
| `type: "query"` | `GET /xrpc/{lexicon.id}` |
| `type: "procedure"` | `POST /xrpc/{lexicon.id}` |
| `type: "record"` | Component schema (not an endpoint) |
| `parameters` (query def) | `parameters` array in operation |
| `input.schema` (procedure) | `requestBody.content[encoding]` |
| `output.schema` | `responses.200.content[encoding]` |

### Properties

- `type: "ref"` → `$ref: "#/components/schemas/TypeName"`
- `type: "union"` + `refs: [...]` → `oneOf: [{$ref: ...}, ...]`
- `type: "array"` → `type: "array"` + `items: {...}`
- `type: "object"` → nested `properties`
- `minimum`, `maximum`, `maxLength`, etc. → OpenAPI equivalents
- `enum`, `knownValues` → preserved as `enum`, `x-knownValues`

## Limitations

- Lexicon `encoding` field is used as-is for MIME type (e.g., `"application/json"`)
- Record types are registered as component schemas, not as endpoints
- Complex types (union with `$type` discriminators) are flattened to `oneOf`
- No automatic OpenAPI security schemes (auth must be added post-generation)

## Example Output

For lexicon:
```json
{
  "lexicon": 1,
  "id": "com.etzhayyim.kiyo.getPaper",
  "defs": {
    "main": {
      "type": "query",
      "description": "Get paper metadata",
      "parameters": {
        "type": "params",
        "properties": { "paperId": { "type": "string" } },
        "required": ["paperId"]
      },
      "output": {
        "encoding": "application/json",
        "schema": { "type": "object", "properties": { "title": { "type": "string" } } }
      }
    }
  }
}
```

Generates OpenAPI:
```json
{
  "openapi": "3.0.3",
  "info": { "title": "Kiyo XRPC API", "version": "0.1.0" },
  "servers": [{ "url": "https://kiyo.etzhayyim.com" }],
  "paths": {
    "/xrpc/com.etzhayyim.kiyo.getPaper": {
      "get": {
        "summary": "Get paper metadata",
        "operationId": "com.etzhayyim.kiyo.getPaper",
        "parameters": [{
          "name": "paperId",
          "in": "query",
          "required": true,
          "schema": { "type": "string" }
        }],
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": { "type": "object", "properties": { "title": { "type": "string" } } }
              }
            }
          }
        }
      }
    }
  }
}
```

## License

Apache 2.0 (part of etzhayyim/root)
