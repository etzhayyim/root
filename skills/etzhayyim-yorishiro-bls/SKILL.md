---
name: etzhayyim-yorishiro-bls
description: Drive the bls yorishiro (kami: api.bls.gov) via MCP tools, XRPC, or in-process kotodama actor calls.
charter_purposes: ["grant"]
transport: openapi-v3
adr: 2605211900
---

# etzhayyim-yorishiro-bls

依代 (vessel) wrapping the **api.bls.gov** kami so that agents can drive
it through the etzhayyim substrate. The same op surface is exposed three
ways:

1. **Lexicon** at `00-contracts/lexicons/ai/etzhayyim/yorishiro/bls/*.json` (XRPC + kotodama-host-sdk consumers)
2. **Pregel cell** at `40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_bls/cell.py` (in-cluster Murakumo runtime)
3. **MCP server** at `40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-bls-mcp/` (stdio + Streamable HTTP)

## Tools

- `fetch_timeseries` — Fetch BLS timeseries data

## JSON output

Every tool returns a JSON object:

```json
{ "httpStatus": <number>, "json"?: <object>, "body"?: <string>, "error"?: <string> }
```

`json` is present iff the kami returned `application/json` and the body
parsed; otherwise the raw response is in `body`. `httpStatus` is `0` if
the kami could not be reached at all.

## Charter purposes

This yorishiro is restricted to: `grant`. Calls that
would imply a non-listed purpose are rejected at the lexicon validator
seam. See ADR-2605192115 §4.
