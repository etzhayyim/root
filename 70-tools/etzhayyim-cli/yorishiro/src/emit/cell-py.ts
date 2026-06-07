// emit/cell-py.ts — L2 emitter. Produces a single kotodama Pregel cell.py
// conforming to the runtime contract from ADR-2605202200:
//   - build_graph(checkpointer) -> CompiledStateGraph
//   - state_from_event(event) -> State
//   - thread_id_from_event(event) -> str
//   - healthz() -> dict
//
// One StateGraph node per op. Each node performs the kami HTTP call via
// stdlib urllib (no external runtime dependency) and writes the response
// into the state. The cell is read-side stateless — anchor responsibility
// belongs to the calling cell (D6 in ADR-2605211900).

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { NormalizedOp } from "../openapi/parse.js";

export interface EmitCellArgs {
  repoRoot: string;
  name: string;
  kami: string;
  baseUrl: string;
  transport: string;
  purposes: readonly string[];
  ops: readonly NormalizedOp[];
}

export interface EmittedCell {
  path: string;
  readmePath: string;
}

export function emitCell(args: EmitCellArgs): EmittedCell {
  const cellDir = join(args.repoRoot, "40-engine/kotoba/crates/kotoba-kotodama/cells", `yorishiro_${args.name}`);
  mkdirSync(cellDir, { recursive: true });

  const cellPath = join(cellDir, "cell.py");
  writeFileSync(cellPath, renderCellPy(args), "utf-8");

  const readmePath = join(cellDir, "README.md");
  writeFileSync(readmePath, renderCellReadme(args), "utf-8");

  // cells.toml fragment — picked up by cell_runner's load_cell_registry()
  // auto-discovery (no manual merge into the central cells.toml needed).
  const fragmentPath = join(cellDir, "cells.toml.fragment");
  writeFileSync(fragmentPath, renderCellsTomlFragment(args), "utf-8");

  // Empty __init__.py so `importlib.import_module("yorishiro_<name>.cell")`
  // resolves (cell_runner prepends 40-engine/kotoba/crates/kotoba-kotodama/cells/ to sys.path).
  writeFileSync(join(cellDir, "__init__.py"), "", "utf-8");

  return { path: cellPath, readmePath };
}

function renderCellPy(args: EmitCellArgs): string {
  const className = pascal(args.name) + "State";
  const purposesPy = JSON.stringify([...args.purposes]);
  const opsCode = args.ops.map((op) => renderOpNode(op)).join("\n\n");
  const opNames = args.ops.map((op) => snake(op.opName));
  const routerCases = args.ops
    .map((op) => `        "${op.opName}": ${snake(op.opName)}_node,`)
    .join("\n");

  return `"""
Yorishiro: ${args.name} (kami: ${args.kami})
Generator: @etzhayyim/yorishiro v0.1.0
Per ADR-2605211900 (yorishiro external-actor bridge) + ADR-2605202200
(kotodama cell.py runtime contract).

Transport: ${args.transport}
Base URL : ${args.baseUrl}
Charter purposes: ${args.purposes.join(", ")}

This file is generator output. Hand edits will be overwritten by
\`yorishiro regen ${args.name}\` — extend the kami OpenAPI spec instead.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, TypedDict
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph


YORISHIRO_NAME = "${args.name}"
YORISHIRO_KAMI = "${args.kami}"
YORISHIRO_BASE_URL = "${args.baseUrl.replace(/"/g, '\\"')}"
YORISHIRO_PURPOSES = tuple(${purposesPy})
USER_AGENT = f"etzhayyim-yorishiro-{YORISHIRO_NAME}/0.1"


class ${className}(TypedDict, total=False):
    # routing
    op: str

    # arbitrary kami input (one set of keys per op — kept loose because
    # OpenAPI parameter shape varies. Validation belongs to the L1
    # lexicon + parseLexiconInput at the XRPC/MCP seam).
    params: dict[str, Any]
    body: dict[str, Any]

    # kami output
    http_status: int
    json: dict[str, Any]
    body_raw: str
    error: str


def _http_call(method: str, url: str, params: dict[str, Any], body: dict[str, Any] | None) -> tuple[int, str]:
    filtered = {k: v for k, v in params.items() if v is not None and v != ""}
    qs = urlencode(filtered, doseq=True)
    full_url = f"{url}?{qs}" if qs else url
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    data: bytes | None = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(full_url, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 — kami failures surface to state.error
        return 0, str(exc)


def _attempt_json(text: str) -> dict[str, Any] | None:
    try:
        out = json.loads(text)
        if isinstance(out, dict):
            return out
        return {"value": out}
    except (json.JSONDecodeError, ValueError):
        return None


${opsCode}


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    g = StateGraph(${className})
${args.ops.map((op) => `    g.add_node("${op.opName}", ${snake(op.opName)}_node)`).join("\n")}

    def _router(state: ${className}) -> str:
        op = state.get("op") or ${JSON.stringify(args.ops[0]?.opName ?? "noop")}
        return op if op in {${args.ops.map((o) => `"${o.opName}"`).join(", ")}} else ${JSON.stringify(args.ops[0]?.opName ?? "noop")}

    g.add_conditional_edges(START, _router, {
${args.ops.map((op) => `        "${op.opName}": "${op.opName}",`).join("\n")}
    })
${args.ops.map((op) => `    g.add_edge("${op.opName}", END)`).join("\n")}

    return g.compile(checkpointer=checkpointer)


# ── kotodama cell-runner contract (ADR-2605202200) ───────────────────────────


def state_from_event(event: dict[str, Any]) -> ${className}:
    """Map an MST / XRPC event payload into the cell's TypedDict state."""
    return {
        "op": event.get("op", ${JSON.stringify(args.ops[0]?.opName ?? "")}),
        "params": event.get("params", {}) or {},
        "body": event.get("body", {}) or {},
    }


def thread_id_from_event(event: dict[str, Any]) -> str:
    """Deterministic thread id so duplicate events deduplicate at the checkpointer."""
    key = json.dumps(
        {
            "op": event.get("op"),
            "params": event.get("params"),
            "body": event.get("body"),
        },
        sort_keys=True,
        default=str,
    )
    return f"yorishiro-{YORISHIRO_NAME}-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "yorishiro": YORISHIRO_NAME,
        "kami": YORISHIRO_KAMI,
        "purposes": list(YORISHIRO_PURPOSES),
        "ops": ${JSON.stringify(args.ops.map((o) => o.opName))},
    }


__all__ = [
    "${className}",
    "build_graph",
    "state_from_event",
    "thread_id_from_event",
    "healthz",
${opNames.map((n) => `    "${n}_node",`).join("\n")}
]
`;
}

function renderOpNode(op: NormalizedOp): string {
  return `def ${snake(op.opName)}_node(state: dict[str, Any]) -> dict[str, Any]:
    """${escapeMl(op.description || op.summary || op.opName)}"""
    params = dict(state.get("params") or {})
    body = state.get("body") or None
    path = "${op.pathTemplate}"
    for key in list(params.keys()):
        token = "{" + key + "}"
        if token in path:
            path = path.replace(token, str(params.pop(key)))
    url = f"{YORISHIRO_BASE_URL}{path}"
    status, text = _http_call("${op.httpMethod}", url, params, body if isinstance(body, dict) and body else None)
    out: dict[str, Any] = {**state, "http_status": status}
    if status == 0:
        out["error"] = text
        return out
    if status >= 400:
        out["error"] = text[:1000]
        out["body_raw"] = text
        return out
    if "${op.responseContentType}" == "application/json":
        parsed = _attempt_json(text)
        if parsed is not None:
            out["json"] = parsed
            return out
    out["body_raw"] = text
    return out`;
}

function renderCellReadme(args: EmitCellArgs): string {
  const opList = args.ops
    .map((o) => `| \`${o.opName}\` | \`${o.httpMethod}\` \`${o.pathTemplate}\` | ${oneLine(o.summary || o.description)} |`)
    .join("\n");
  return `# yorishiro_${args.name}

Pregel cell for the **${args.name}** yorishiro (kami: \`${args.kami}\`).

Per **ADR-2605211900** (yorishiro external-actor bridge) +
**ADR-2605202200** (kotodama cell.py runtime contract).

Generator: \`@etzhayyim/yorishiro\` v0.1.0
Transport: \`${args.transport}\`
Base URL : \`${args.baseUrl}\`
Charter purposes: \`${args.purposes.join(", ")}\`

## Ops

| Op | HTTP | Summary |
|---|---|---|
${opList}

## Lexicon SSoT

\`00-contracts/lexicons/ai/etzhayyim/yorishiro/${args.name}/<op>.json\`

## MCP exposure

\`40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-${args.name}-mcp/\` (stdio + Streamable HTTP)

## Regenerate

\`\`\`bash
yorishiro regen ${args.name}
\`\`\`

Hand edits to \`cell.py\` are overwritten on regen — extend the kami
OpenAPI spec at \`00-contracts/openapi/kami/${args.name}.openapi.json\` instead.

## Cell-runner registration

The cells.toml fragment \`cells.toml.fragment\` in this directory is the
authoritative entry for the Murakumo cell-runner. Append it to
\`50-infra/cluster/murakumo/cell-runner/cells.toml\` once the cell-runner
supports \`40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_*/cell.py\` discovery
(ADR-2605202200 wiring).

## Claude Desktop / Codex CLI

\`\`\`json
{
  "mcpServers": {
    "etzhayyim-yorishiro-${args.name}": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/repo/40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-${args.name}-mcp/src/cli.ts"],
      "env": { "YORISHIRO_${args.name.toUpperCase()}_BASE_URL": "${args.baseUrl}" }
    }
  }
}
\`\`\`

Use \`tsx\` rather than \`node\` if the host does not auto-resolve \`.ts\`.
`;
}

function renderCellsTomlFragment(args: EmitCellArgs): string {
  // Pick the first op's NSID as the default XRPC trigger. Multi-op yorishiri
  // can fan out via the cell's internal router (state["op"]).
  const firstOp = args.ops[0]?.opName ?? "noop";
  const nsid = `ai.etzhayyim.yorishiro.${args.name}.${firstOp}`;
  const cellName = pascal(args.name);
  // Deterministic healthz port from a hash of the yorishiro name to avoid
  // collisions across yorishiri (range 13030-13999 per fleet.toml convention).
  let h = 0;
  for (let i = 0; i < args.name.length; i++) h = (h * 31 + args.name.charCodeAt(i)) >>> 0;
  const port = 13030 + (h % 970);
  return `# cells.toml fragment for the Yorishiro${cellName}Cell.
#
# Append to 50-infra/cluster/murakumo/cell-runner/cells.toml when the
# cell-runner is wired to discover yorishiri cells under
# 40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_*/cell.py (ADR-2605202200 + 2605211900).
#
# Until then, this fragment lives alongside the cell so that the wiring
# intent is part of the cell's source of truth, not lost to a future
# scavenger hunt.

[[cell]]
name = "Yorishiro${cellName}Cell"
module = "yorishiro_${args.name}.cell"
entry = "build_graph"
node = "*"
trigger = { kind = "xrpc", nsid = "${nsid}" }
healthz_port = ${port}
adr = ["2605211900", "2605202200"]
`;
}

function pascal(s: string): string {
  return s
    .split(/[-_]/)
    .filter(Boolean)
    .map((p) => p[0]!.toUpperCase() + p.slice(1))
    .join("");
}

function snake(s: string): string {
  return s
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/[-]/g, "_")
    .toLowerCase();
}

function oneLine(s: string): string {
  return s.replace(/\s+/g, " ").trim().slice(0, 120);
}

function escapeMl(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, " ");
}
