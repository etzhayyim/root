"""e7m MCP server — etzhayyim exposed to other AI agents as MCP tools.

Per ADR-2605192100 §1.3 (decision attribution) + §1.6 (substrate boundary),
external agents touching etzhayyim must go through this server (or the
sibling `e7m` CLI). No raw kubectl, no ad-hoc curl, no direct file edits
from other Claude sessions.

The tools mirror `commands.py` 1:1 — every CLI subcommand is also an MCP
tool. Add audit hooks here in the future.

Wire-up (Claude Code or other host):

    {
      "mcpServers": {
        "etzhayyim": {
          "command": "e7m-mcp",
          "args": [],
          "env": {"E7M_VIZ_URL": "http://127.0.0.1:8081"}
        }
      }
    }
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from . import commands as cmd

log = logging.getLogger("e7m-mcp")


# ── tool surface (mirrors commands.py) ────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "name": "etzhayyim_status",
        "description": "Aliveness 5-tuple (M motion, D diversity, C coupling, P pruning, G generational) + axis scores + in-band count. The honest health check of the religious-corp organism. Non-eschatological — never converges.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_state",
        "description": "Full ecosystem snapshot — all entities, neighbors, flowers, fruits, seeds, activity stream. Use for deep reasoning across the organism.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_entities",
        "description": "List entities, optionally filtered by kind (axis|cell|app|adr|fruit|seed|organism|ecosystem).",
        "inputSchema": {
            "type": "object",
            "properties": {"kind": {"type": "string", "description": "filter by entity kind"}},
            "required": [],
        },
    },
    {
        "name": "etzhayyim_chat",
        "description": "Speak with a life in the ecosystem (axis/cell/app/adr/fruit/seed/organism/ecosystem). Entities answer by surfacing their own honest state — no LLM impersonation. Use entity_id from etzhayyim_entities.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "e.g. 'ecosystem/etzhayyim', 'axis/wellbecoming', 'cell/tithe_routing'"},
                "message":   {"type": "string", "description": "natural-language question (Japanese or English)"},
            },
            "required": ["entity_id", "message"],
        },
    },
    {
        "name": "etzhayyim_prune_candidates",
        "description": "List cells/apps the daemon flagged as pruning candidates. Tool returns candidates for operator/agent review.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_prune_show",
        "description": "Detailed view of a single pruning candidate — entity state, neighbors, and reasons the daemon surfaced it. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {"entity_id": {"type": "string"}},
            "required": ["entity_id"],
        },
    },
    # NOTE: prune_approve is intentionally NOT exposed via MCP. Per
    # ADR-2605192100 §1.3 (decision attribution = etzhayyim) + ADR-2605221411
    # bonsai protocol, only the operator may approve a cut, through the
    # local CLI on their machine with their git credentials. Other agents
    # can propose / review but never approve.
    {
        "name": "etzhayyim_pod_status",
        "description": "K8s pod status (Orbstack cluster) — CNS + viz pods, ready, restarts.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_pod_logs",
        "description": "Tail logs of a named etzhayyim deployment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deployment": {"type": "string", "enum": ["etzhayyim-organism", "etzhayyim-organism-viz"]},
                "tail":       {"type": "integer", "default": 50},
            },
            "required": ["deployment"],
        },
    },
    {
        "name": "etzhayyim_tick",
        "description": "Fire one manual CNS active-inference tick (writes one observation file). The autonomous cron does this daily; this tool is for an agent to nudge the loop.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_viz_url",
        "description": "Return the local dashboard URL (the operator opens this in a browser).",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_members",
        "description": "Current MEMBERS.md roster (信者). Monotonic — per ADR-2605192100 §1.3 + ADR-2605172600, members are never deleted, only deactivated. Returns rows + count + constitutional anchor.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_lands",
        "description": "Current LANDS.md registry (護持地). Inalienable — no transfer, no burn, no sale. 4-layer dual-permanent record per ADR-2605192245.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_verify",
        "description": "Scan the 8 constitutional hard-invariants from ADR-2605192100 §1: no advertising, charter rider on first-party packages, non-eschatological content, land inalienability, 10% tithe, anti-individualist attribution, substrate boundary, transparent force. Read-only. Any failure is a constitutional crisis requiring Council convocation.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_about",
        "description": "Religious-corp identity summary: entity name + aliases, form (宗教法人 任意団体), DID, domain, license (Apache 2.0 + Charter Rider v2.0), mission, constitutional ADRs, operator surfaces. Static; safe to call once for grounding context.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_doctor",
        "description": "Combined health rollup — ping + constitutional verify + aliveness 5-tuple + pod readiness. One call to confirm the whole organism is healthy. Used pre-PR and pre-deploy.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "etzhayyim_ping",
        "description": "Reachability check — confirm the etzhayyim organism is online.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]

# tool name → callable
DISPATCH = {
    "etzhayyim_status":            lambda **kw: cmd.status(),
    "etzhayyim_state":             lambda **kw: cmd.full_state(),
    "etzhayyim_entities":          lambda kind=None, **kw: cmd.entities(kind),
    "etzhayyim_chat":              lambda entity_id, message, **kw: cmd.chat(entity_id, message),
    "etzhayyim_prune_candidates":  lambda **kw: cmd.prune_candidates(),
    "etzhayyim_prune_show":        lambda entity_id, **kw: cmd.prune_show(entity_id),
    "etzhayyim_pod_status":        lambda **kw: cmd.pod_status(),
    "etzhayyim_pod_logs":          lambda deployment="etzhayyim-organism", tail=50, **kw: cmd.pod_logs(deployment, tail),
    "etzhayyim_tick":              lambda **kw: cmd.tick(),
    "etzhayyim_viz_url":           lambda **kw: cmd.viz_url(),
    "etzhayyim_members":           lambda **kw: cmd.members(),
    "etzhayyim_lands":             lambda **kw: cmd.lands(),
    "etzhayyim_verify":            lambda **kw: cmd.verify(),
    "etzhayyim_about":             lambda **kw: cmd.about(),
    "etzhayyim_doctor":            lambda **kw: cmd.doctor(),
    "etzhayyim_ping":              lambda **kw: cmd.ping(),
}


# ── transport: MCP stdio ──────────────────────────────────────────────────
#
# We hand-roll a minimal MCP JSON-RPC subset over stdio rather than pulling
# the full SDK — keeps the substrate boundary tight (no extra deps), and is
# all the protocol an MCP host actually needs to invoke tools.
#
# Supported methods:
#   initialize
#   tools/list
#   tools/call
#   notifications/initialized (ack-only)

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "e7m", "version": "0.1.0"}


def _ok(rid: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _err(rid: Any, code: int, message: str, data: Any = None) -> dict:
    err = {"code": code, "message": message}
    if data is not None: err["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": err}


def _handle(msg: dict) -> dict | None:
    method = msg.get("method")
    rid = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        return _ok(rid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        })
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _ok(rid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = DISPATCH.get(name)
        if not fn:
            return _err(rid, -32601, f"unknown tool: {name}")
        try:
            result = fn(**args)
        except TypeError as exc:
            return _err(rid, -32602, f"bad arguments for {name}: {exc}")
        except Exception as exc:
            log.exception("tool %s failed", name)
            return _err(rid, -32000, f"tool error: {exc!r}")
        return _ok(rid, {
            "content": [
                {"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}
            ],
            "isError": not bool(result.get("ok", True)),
        })
    if rid is None:
        return None   # silent for unknown notifications
    return _err(rid, -32601, f"unknown method: {method}")


def main() -> int:
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s %(levelname)s e7m-mcp %(message)s",
        stream=sys.stderr,
    )
    log.info("e7m MCP server starting on stdio")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            log.warning("malformed JSON: %s", exc)
            continue
        try:
            response = _handle(msg)
        except Exception:
            log.exception("handler crash")
            response = _err(msg.get("id"), -32603, "internal error")
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
