// binary/emit-cell-py.ts — L2 emitter (Python Pregel cell, subprocess-based).

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { BinaryArg, BinaryOp, KamiManifest } from "./types.js";

export interface EmitArgs {
  repoRoot: string;
  name: string;
  purposes: readonly string[];
  manifest: KamiManifest;
}

export function emitBinaryCell(args: EmitArgs): { path: string; readmePath: string } {
  const cellDir = join(args.repoRoot, "40-engine/kotoba/crates/kotoba-kotodama/cells", `yorishiro_${args.name}`);
  mkdirSync(cellDir, { recursive: true });
  const cellPath = join(cellDir, "cell.py");
  writeFileSync(cellPath, renderCell(args), "utf-8");
  const readmePath = join(cellDir, "README.md");
  writeFileSync(readmePath, renderReadme(args), "utf-8");
  const fragPath = join(cellDir, "cells.toml.fragment");
  writeFileSync(fragPath, renderFragment(args), "utf-8");
  // Empty __init__.py so importlib can resolve `yorishiro_<name>.cell`
  // once cell_runner prepends 40-engine/kotoba/crates/kotoba-kotodama/cells/ to sys.path.
  writeFileSync(join(cellDir, "__init__.py"), "", "utf-8");
  return { path: cellPath, readmePath };
}

function renderCell(args: EmitArgs): string {
  const className = pascal(args.name) + "State";
  const purposesPy = JSON.stringify([...args.purposes]);
  const opsCode = args.manifest.ops.map((op) => renderOpNode(args.manifest, op)).join("\n\n");
  const firstOp = args.manifest.ops[0]?.name ?? "noop";
  const opNames = args.manifest.ops.map((op) => snake(op.name));

  return `"""
Yorishiro: ${args.name} (kami: ${args.manifest.kami.id})
Generator: @etzhayyim/yorishiro v0.1.0 (binary-cli mode)
Per ADR-2605211900 + ADR-2605202200.

Transport: binary-cli
Binary   : ${args.manifest.kami.binary}
Charter purposes: ${args.purposes.join(", ")}

The cell shells out to a local binary via subprocess. The binary MUST be
present on the cell runtime's PATH (or supplied as an absolute path in
the kami manifest). Argv is constructed as a list — never via a shell
string — to keep injection vectors closed.

This file is generator output. Hand edits are overwritten by
\`yorishiro regen ${args.name}\`. Extend the kami manifest instead.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from typing import Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph


YORISHIRO_NAME = "${args.name}"
YORISHIRO_KAMI = "${args.manifest.kami.id}"
YORISHIRO_BINARY = "${args.manifest.kami.binary}"
YORISHIRO_PURPOSES = tuple(${purposesPy})


class ${className}(TypedDict, total=False):
    op: str
    args: dict[str, Any]
    exit_code: int
    stdout: str
    stderr: str
    error: str


def _resolve_binary(binary: str) -> str | None:
    if "/" in binary:
        return binary
    return shutil.which(binary)


def _run(argv: list[str], timeout: int) -> tuple[int, str, str, str | None]:
    bin_path = _resolve_binary(argv[0])
    if not bin_path:
        return -1, "", "", f"binary not found on PATH: {argv[0]}"
    try:
        proc = subprocess.run(
            [bin_path, *argv[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr, None
    except subprocess.TimeoutExpired as exc:
        return -1, "", "", f"timeout after {exc.timeout}s"
    except Exception as exc:  # noqa: BLE001 — binary failures surface to state.error
        return -1, "", "", str(exc)


${opsCode}


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    g = StateGraph(${className})
${args.manifest.ops.map((op) => `    g.add_node(${JSON.stringify(op.name)}, ${snake(op.name)}_node)`).join("\n")}

    def _router(state: ${className}) -> str:
        op = state.get("op") or ${JSON.stringify(firstOp)}
        return op if op in {${args.manifest.ops.map((o) => JSON.stringify(o.name)).join(", ")}} else ${JSON.stringify(firstOp)}

    g.add_conditional_edges(START, _router, {
${args.manifest.ops.map((op) => `        ${JSON.stringify(op.name)}: ${JSON.stringify(op.name)},`).join("\n")}
    })
${args.manifest.ops.map((op) => `    g.add_edge(${JSON.stringify(op.name)}, END)`).join("\n")}

    return g.compile(checkpointer=checkpointer)


# ── kotodama cell-runner contract (ADR-2605202200) ───────────────────────────


def state_from_event(event: dict[str, Any]) -> ${className}:
    return {
        "op": event.get("op", ${JSON.stringify(firstOp)}),
        "args": event.get("args", {}) or {},
    }


def thread_id_from_event(event: dict[str, Any]) -> str:
    key = json.dumps(
        {"op": event.get("op"), "args": event.get("args")},
        sort_keys=True,
        default=str,
    )
    return f"yorishiro-{YORISHIRO_NAME}-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "yorishiro": YORISHIRO_NAME,
        "kami": YORISHIRO_KAMI,
        "binary": YORISHIRO_BINARY,
        "binary_resolved": _resolve_binary(YORISHIRO_BINARY),
        "purposes": list(YORISHIRO_PURPOSES),
        "ops": ${JSON.stringify(args.manifest.ops.map((o) => o.name))},
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

function renderOpNode(_manifest: KamiManifest, op: BinaryOp): string {
  // Render argv construction inline so the cell stays auditable.
  const argvLines = renderArgvBuilder(op).split("\n").map((l) => l && "    " + l).join("\n");
  return `def ${snake(op.name)}_node(state: dict[str, Any]) -> dict[str, Any]:
    """${escapeMl(op.description || op.summary || op.name)}"""
    args = dict(state.get("args") or {})
    argv: list[str] = [YORISHIRO_BINARY]
${argvLines}
    code, out, err, fatal = _run(argv, timeout=${op.timeout_seconds ?? 60})
    if fatal:
        return {**state, "exit_code": code, "stdout": out, "stderr": err, "error": fatal}
    return {**state, "exit_code": code, "stdout": out, "stderr": err}`;
}

function renderArgvBuilder(op: BinaryOp): string {
  // Flags first (so ordering is stable and predictable), then positionals
  // by ascending position. Positionals with default=None and not provided
  // are skipped; required positionals raise via the lexicon validator
  // upstream — we still tolerate missing here and let the binary complain.
  const lines: string[] = [];
  const flags = op.argv.filter((a): a is Extract<BinaryArg, { kind: "flag" }> => a.kind === "flag");
  const positionals = op.argv
    .filter((a): a is Extract<BinaryArg, { kind: "positional" }> => a.kind === "positional")
    .sort((a, b) => a.position - b.position);

  for (const f of flags) {
    const key = JSON.stringify(f.name);
    if (f.type === "boolean") {
      lines.push(`if bool(args.get(${key})):`);
      lines.push(`    argv.append(${JSON.stringify(f.flag)})`);
    } else {
      lines.push(`if args.get(${key}) is not None and args.get(${key}) != "":`);
      if (f.separator === "=") {
        lines.push(`    argv.append(${JSON.stringify(f.flag + "=")} + str(args[${key}]))`);
      } else {
        lines.push(`    argv.append(${JSON.stringify(f.flag)})`);
        lines.push(`    argv.append(str(args[${key}]))`);
      }
    }
  }
  for (const p of positionals) {
    const key = JSON.stringify(p.name);
    const def = p.default !== undefined ? JSON.stringify(String(p.default)) : "None";
    lines.push(`pos = args.get(${key}, ${def})`);
    lines.push(`if pos is not None and pos != "":`);
    lines.push(`    argv.append(str(pos))`);
  }
  return lines.join("\n");
}

function renderReadme(args: EmitArgs): string {
  const ops = args.manifest.ops
    .map((o) => `| \`${o.name}\` | ${oneLine(o.summary || o.description || o.name)} |`)
    .join("\n");
  return `# yorishiro_${args.name}

Pregel cell for the **${args.name}** yorishiro (kami: \`${args.manifest.kami.id}\`,
binary: \`${args.manifest.kami.binary}\`).

Per ADR-2605211900 + ADR-2605202200. Generated by \`@etzhayyim/yorishiro\`
v0.1.0 in **binary-cli** mode.

## Ops

| Op | Summary |
|---|---|
${ops}

## Runtime requirements

The \`${args.manifest.kami.binary}\` binary must be available on the
cell runtime's PATH (or supplied as an absolute path in the kami
manifest at \`00-contracts/kami/${args.name}.kami.json\`). The cell
verifies this via \`shutil.which()\` at the start of every invocation
and returns \`error: "binary not found on PATH"\` if missing.

## Lexicon SSoT

\`00-contracts/lexicons/ai/etzhayyim/yorishiro/${args.name}/<op>.json\`

## MCP exposure

\`40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-${args.name}-mcp/\` (stdio + Streamable HTTP)

## Regenerate

\`\`\`bash
yorishiro regen ${args.name}
\`\`\`

## Cell-runner registration

See \`cells.toml.fragment\` in this directory.

## Claude Desktop / Codex CLI

\`\`\`json
{
  "mcpServers": {
    "etzhayyim-yorishiro-${args.name}": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/repo/40-engine/kotoba/crates/kotoba-kotodama/mcp/yorishiro-${args.name}-mcp/src/cli.ts"]
    }
  }
}
\`\`\`

The binary itself does NOT need to be on the MCP host machine if you
intend the MCP server to dispatch to a remote runtime. For the simple
local-binary case shown above, \`${args.manifest.kami.binary}\` must be
on the host's PATH.
`;
}

function renderFragment(args: EmitArgs): string {
  const firstOp = args.manifest.ops[0]?.name ?? "noop";
  const nsid = `ai.etzhayyim.yorishiro.${args.name}.${firstOp}`;
  const cellName = pascal(args.name);
  let h = 0;
  for (let i = 0; i < args.name.length; i++) h = (h * 31 + args.name.charCodeAt(i)) >>> 0;
  const port = 13030 + (h % 970);
  return `# cells.toml fragment for the Yorishiro${cellName}Cell.
#
# Append to 50-infra/cluster/murakumo/cell-runner/cells.toml when the
# cell-runner is wired to discover yorishiri cells under
# 40-engine/kotoba/crates/kotoba-kotodama/cells/yorishiro_*/cell.py (ADR-2605202200 + 2605211900).
# binary-cli yorishiri additionally require ${args.manifest.kami.binary} on
# the cell runtime's PATH.

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
  return s.split(/[-_]/).filter(Boolean).map((p) => p[0]!.toUpperCase() + p.slice(1)).join("");
}
function snake(s: string): string {
  return s.replace(/([a-z0-9])([A-Z])/g, "$1_$2").replace(/[-]/g, "_").toLowerCase();
}
function oneLine(s: string): string {
  return s.replace(/\s+/g, " ").trim().slice(0, 120);
}
function escapeMl(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, " ");
}
