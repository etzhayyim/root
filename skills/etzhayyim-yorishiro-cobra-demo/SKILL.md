---
name: etzhayyim-yorishiro-cobra-demo
description: Drive the cobra-demo yorishiro (kami: bin:cobra-demo) via MCP tools, XRPC, or in-process kotodama actor calls.
charter_purposes: ["grant"]
transport: binary-cli
adr: 2605211900
---

# etzhayyim-yorishiro-cobra-demo

依代 (vessel) wrapping the **bin:cobra-demo** kami so that agents can drive
it through the etzhayyim substrate. The same op surface is exposed three
ways:

1. **Lexicon** at `00-contracts/lexicons/ai/etzhayyim/yorishiro/cobra-demo/*.json` (XRPC + kotodama-host-sdk consumers)
2. **Pregel cell** at `40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_cobra-demo/cell.py` (in-cluster Murakumo runtime)
3. **MCP server** at `40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-cobra-demo-mcp/` (stdio + Streamable HTTP)

## Tools

- `cobra_demo` — Demo cobra CLI used by the yorishiro source-repo fixture.
- `greet` — Print a greeting.
- `render` — Render output to file or stdout.

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
