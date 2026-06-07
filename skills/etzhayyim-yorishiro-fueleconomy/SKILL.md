---
name: etzhayyim-yorishiro-fueleconomy
description: Drive the fueleconomy yorishiro (kami: www.fueleconomy.gov) via MCP tools, XRPC, or in-process kotodama actor calls.
charter_purposes: ["grant"]
transport: openapi-v3
adr: 2605211900
---

# etzhayyim-yorishiro-fueleconomy

依代 (vessel) wrapping the **www.fueleconomy.gov** kami so that agents can drive
it through the etzhayyim substrate. The same op surface is exposed three
ways:

1. **Lexicon** at `00-contracts/lexicons/ai/etzhayyim/yorishiro/fueleconomy/*.json` (XRPC + kotodama-host-sdk consumers)
2. **Pregel cell** at `40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_fueleconomy/cell.py` (in-cluster Murakumo runtime)
3. **MCP server** at `40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-fueleconomy-mcp/` (stdio + Streamable HTTP)

## Tools

- `download_vehicles_csv` — Download the full EPA vehicles dataset as CSV

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
