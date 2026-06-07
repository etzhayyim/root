// browser/emit-cell-py.ts — L2 emitter (Python Pregel cell, playwright sync_api).
//
// Browser-only yorishiri spawn a headless browser per invocation. Playwright's
// sync API is launched inside the cell, the step sequence is replayed, and
// the result is harvested via the manifest's extract array. The browser
// binary must be present on the cell runtime (`playwright install chromium`).
//
// The cell remains stateless across invocations — Playwright contexts are
// not shared. For high-traffic browser-only yorishiri, a separate browser
// pool service would be the next refactor; for the typical "read a page
// once" use case, per-invocation spawn is acceptable.

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { BrowserKamiManifest, BrowserOp, BrowserStep } from "./types.js";

export interface EmitArgs {
  repoRoot: string;
  name: string;
  purposes: readonly string[];
  manifest: BrowserKamiManifest;
}

export function emitBrowserCell(args: EmitArgs): { path: string; readmePath: string } {
  const cellDir = join(args.repoRoot, "40-engine/kotoba/crates/kotoba-kotodama/cells", `yorishiro_${args.name}`);
  mkdirSync(cellDir, { recursive: true });
  const cellPath = join(cellDir, "cell.py");
  writeFileSync(cellPath, renderCell(args), "utf-8");
  const readmePath = join(cellDir, "README.md");
  writeFileSync(readmePath, renderReadme(args), "utf-8");
  writeFileSync(join(cellDir, "cells.toml.fragment"), renderFragment(args), "utf-8");
  writeFileSync(join(cellDir, "__init__.py"), "", "utf-8");
  return { path: cellPath, readmePath };
}

function renderCell(args: EmitArgs): string {
  const className = pascal(args.name) + "State";
  const purposesPy = JSON.stringify([...args.purposes]);
  const opsCode = args.manifest.ops.map((op) => renderOpNode(op)).join("\n\n");
  const opNames = args.manifest.ops.map((op) => snake(op.name));
  const firstOp = args.manifest.ops[0]?.name ?? "noop";

  return `"""
Yorishiro: ${args.name} (kami: ${args.manifest.kami.id})
Generator: @etzhayyim/yorishiro v0.1.0 (browser-only mode)
Per ADR-2605211900 + ADR-2605202200.

Transport: browser-only
Base URL : ${args.manifest.kami.base_url}
Charter purposes: ${args.purposes.join(", ")}

The cell spawns Playwright's sync_api per invocation, replays the
manifest's step sequence, and extracts text/attributes per the manifest.
The browser binary must be installed on the cell runtime:

    pip install playwright
    playwright install chromium

Hand edits are overwritten by \`yorishiro regen ${args.name}\`. Extend the
kami manifest instead.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph


YORISHIRO_NAME = "${args.name}"
YORISHIRO_KAMI = "${args.manifest.kami.id}"
YORISHIRO_BASE_URL = "${args.manifest.kami.base_url}"
YORISHIRO_PURPOSES = tuple(${purposesPy})


class ${className}(TypedDict, total=False):
    op: str
    input: dict[str, Any]
    ok: bool
    extracted: dict[str, Any]
    error: str


def _ensure_playwright() -> tuple[Any, Any] | tuple[None, str]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        return None, "playwright not installed (pip install playwright && playwright install chromium)"
    return sync_playwright, None  # type: ignore[return-value]


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
        "input": event.get("input", {}) or {},
    }


def thread_id_from_event(event: dict[str, Any]) -> str:
    key = json.dumps(
        {"op": event.get("op"), "input": event.get("input")},
        sort_keys=True,
        default=str,
    )
    return f"yorishiro-{YORISHIRO_NAME}-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def healthz() -> dict[str, Any]:
    pw, err = _ensure_playwright()
    return {
        "ok": pw is not None,
        "yorishiro": YORISHIRO_NAME,
        "kami": YORISHIRO_KAMI,
        "base_url": YORISHIRO_BASE_URL,
        "purposes": list(YORISHIRO_PURPOSES),
        "ops": ${JSON.stringify(args.manifest.ops.map((o) => o.name))},
        "playwright": "available" if pw is not None else err,
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

function renderOpNode(op: BrowserOp): string {
  const steps = (op.steps as BrowserStep[]).map((s) => renderStep(s)).join("\n");
  const extracts = (op.extract ?? [])
    .map((e) => {
      const sel = JSON.stringify(e.selector);
      const key = JSON.stringify(e.output_key);
      // 16-space indent so the extracts live inside the inner try:
      //   with pw_factory() as p:
      //       browser = …
      //       try:
      //           ctx = …
      //           page = …
      //           <steps at 16>
      //           <extracts at 16>      ← here
      //       finally: …
      if (e.multiple) {
        return `                extracted[${key}] = page.locator(${sel}).all_text_contents()`;
      }
      if (e.attribute) {
        return `                extracted[${key}] = page.locator(${sel}).first.get_attribute(${JSON.stringify(e.attribute)})`;
      }
      return `                extracted[${key}] = page.locator(${sel}).first.text_content()`;
    })
    .join("\n");

  return `def ${snake(op.name)}_node(state: dict[str, Any]) -> dict[str, Any]:
    """${escapeMl(op.description || op.summary || op.name)}"""
    inp = dict(state.get("input") or {})
    pw_factory, err = _ensure_playwright()
    if pw_factory is None:
        return {**state, "ok": False, "error": err or "playwright unavailable"}
    extracted: dict[str, Any] = {}
    try:
        with pw_factory() as p:
            browser = p.chromium.launch(headless=True)
            try:
                ctx = browser.new_context()
                page = ctx.new_page()
${steps}
${extracts || "                pass"}
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001 — browser failures surface to state.error
        return {**state, "ok": False, "extracted": extracted, "error": str(exc)}
    return {**state, "ok": True, "extracted": extracted}`;
}

function renderStep(s: BrowserStep): string {
  switch (s.kind) {
    case "goto":
      return `                page.goto(${JSON.stringify(s.url_template)})`;
    case "wait_for":
      return `                page.wait_for_selector(${JSON.stringify(s.selector)}, timeout=${s.timeout_ms ?? 5000})`;
    case "fill":
      return `                page.fill(${JSON.stringify(s.selector)}, str(inp.get(${JSON.stringify(s.value_input_key)}, "")))`;
    case "click":
      return `                page.click(${JSON.stringify(s.selector)})`;
    case "select":
      return `                page.select_option(${JSON.stringify(s.selector)}, str(inp.get(${JSON.stringify(s.value_input_key)}, "")))`;
    case "sleep_ms":
      return `                page.wait_for_timeout(${s.ms})`;
    case "scroll_to":
      return `                page.locator(${JSON.stringify(s.selector)}).first.scroll_into_view_if_needed()`;
    default:
      return `                # unknown step kind`;
  }
}

function renderReadme(args: EmitArgs): string {
  const ops = args.manifest.ops
    .map((o) => `| \`${o.name}\` | ${oneLine(o.summary || o.description || o.name)} |`)
    .join("\n");
  return `# yorishiro_${args.name}

Pregel cell for the **${args.name}** yorishiro (kami: \`${args.manifest.kami.id}\`,
base URL: \`${args.manifest.kami.base_url}\`).

Per ADR-2605211900 + ADR-2605202200. Generated by \`@etzhayyim/yorishiro\` in
**browser-only** mode.

## Ops

| Op | Summary |
|---|---|
${ops}

## Runtime requirements

\`\`\`bash
pip install playwright
playwright install chromium
\`\`\`

Per invocation the cell launches a headless Chromium, replays the
manifest's step sequence, harvests the extract selectors, and tears
the browser down. For high-traffic yorishiri, swap in a long-lived
browser pool service (out of scope for the L2 PoC).

## Regenerate

\`\`\`bash
yorishiro regen ${args.name}
\`\`\`
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
# browser-only yorishiri additionally require:
#   pip install playwright
#   playwright install chromium
# on the cell runtime. Cell-runner discovers this fragment automatically
# (ADR-2605211900 D4 + cell_runner_main.load_cell_registry).

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
