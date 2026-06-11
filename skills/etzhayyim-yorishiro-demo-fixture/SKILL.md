---
name: etzhayyim-yorishiro-demo-fixture
description: Drive the demo-fixture yorishiro (kami: bin:demo-fixture) via MCP tools, XRPC, or in-process kotodama actor calls.
charter_purposes: ["grant"]
transport: binary-cli
adr: 2605211900
---

# etzhayyim-yorishiro-demo-fixture

依代 (vessel) wrapping the **bin:demo-fixture** kami so that agents can drive
it through the etzhayyim substrate. The same op surface is exposed three
ways:

1. **Lexicon** at `00-contracts/lexicons/ai/etzhayyim/yorishiro/demo-fixture/*.json` (XRPC + kotodama-host-sdk consumers)
2. **Pregel cell** at `40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_demo-fixture/cell.py` (in-cluster Murakumo runtime)
3. **MCP server** at `40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-demo-fixture-mcp/` (stdio + Streamable HTTP)

## Tools

- `greet` — Print a greeting for NAME.
- `head` — Read up to MAX_LINES from INPUT_PATH and write to OUTPUT_PATH.

## JSON output

Every tool returns a JSON object:

```json
{ "exitCode": <number>, "stdout"?: <string>, "stderr"?: <string>, "error"?: <string> }
```

`error` is set only when the binary could not be launched at all
(missing on PATH, timeout, spawn failure). Otherwise the binary's exit
code, stdout, and stderr are reported verbatim.

## Charter purposes

This yorishiro is restricted to: `grant`. Calls that
would imply a non-listed purpose are rejected at the lexicon validator
seam. See ADR-2605192115 §4.
