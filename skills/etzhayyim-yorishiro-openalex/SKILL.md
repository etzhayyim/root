---
name: etzhayyim-yorishiro-openalex
description: Drive the openalex yorishiro (kami: api.openalex.org) via MCP tools, XRPC, or in-process kotodama actor calls.
charter_purposes: ["grant","kisha"]
transport: openapi-v3
adr: 2605211900
---

# etzhayyim-yorishiro-openalex

依代 (vessel) wrapping the **api.openalex.org** kami so that agents can drive
it through the etzhayyim substrate. The same op surface is exposed three
ways:

1. **Lexicon** at `00-contracts/lexicons/ai/etzhayyim/yorishiro/openalex/*.json` (XRPC + kotodama-host-sdk consumers)
2. **Pregel cell** at `40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_openalex/cell.py` (in-cluster Murakumo runtime)
3. **MCP server** at `40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-openalex-mcp/` (stdio + Streamable HTTP)

## Tools

- `search_works` — Search OpenAlex works (papers, preprints)
- `search_authors` — Search OpenAlex authors

## JSON output

Every tool returns a JSON object:

```json
{ "httpStatus": <number>, "json"?: <object>, "body"?: <string>, "error"?: <string> }
```

`json` is present iff the kami returned `application/json` and the body
parsed; otherwise the raw response is in `body`. `httpStatus` is `0` if
the kami could not be reached at all.

## Charter purposes

This yorishiro is restricted to: `grant, kisha`. Calls that
would imply a non-listed purpose are rejected at the lexicon validator
seam. See ADR-2605192115 §4.
