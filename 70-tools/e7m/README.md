# e7m — etzhayyim operator surface

Two entrypoints, one chokepoint:

| Surface | Audience | Binary |
|---|---|---|
| **CLI** | human operator, quick checks | `e7m` |
| **MCP server** | other AI agents (Claude Code in another session, Cursor, etc.) | `e7m-mcp` |

Per ADR-2605192100 §1.3 (decision attribution = etzhayyim) + §1.6 (substrate
boundary), agents that are not the operator **must** touch etzhayyim only
through these two surfaces — never via raw `kubectl`, ad-hoc `curl`, or
direct file edits. Audit, RBAC, and rate-limiting can later be added in
one place (`commands.py`) without retro-fitting clients.

## Install

```bash
cd 70-tools/e7m
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

The CLI talks to the viz pod over `$E7M_VIZ_URL` (default `http://127.0.0.1:8081`).
You'll need a port-forward running:

```bash
kubectl --context orbstack -n etzhayyim-organism port-forward svc/etzhayyim-organism-viz 8081:8081
```

## CLI

```bash
e7m ping                                # is the organism online?
e7m status                              # aliveness 5-tuple + axis scores
e7m state                               # full snapshot (JSON)
e7m entities --kind axis                # list axes (or cell|app|adr|fruit|seed|...)
e7m chat ecosystem/etzhayyim 自己紹介して
e7m chat axis/wellbecoming 次は?
e7m chat seed/inalienable-land どこへ運ぶ?
e7m prune                               # operator pruning candidates
e7m viz open                            # browser to dashboard
e7m pod status                          # k8s pod liveness
e7m pod logs etzhayyim-organism --tail 50
e7m tick                                # nudge one CNS active-inference tick
e7m --json status                       # machine-readable mode for any subcommand
```

## MCP

Wire into Claude Code (`~/.claude/mcp.json` or project-level
`.claude/mcp.json`):

```json
{
  "mcpServers": {
    "etzhayyim": {
      "command": "e7m-mcp",
      "args": [],
      "env": { "E7M_VIZ_URL": "http://127.0.0.1:8081" }
    }
  }
}
```

Tools exposed (all prefixed `etzhayyim_`):

- `etzhayyim_ping` — reachability
- `etzhayyim_status` — aliveness + axes (compact)
- `etzhayyim_state` — full snapshot
- `etzhayyim_entities` — list / filter
- `etzhayyim_chat` — speak with a life
- `etzhayyim_prune_candidates` — operator review surface
- `etzhayyim_pod_status` · `etzhayyim_pod_logs`
- `etzhayyim_tick` — fire one CNS tick
- `etzhayyim_viz_url`

The MCP server speaks JSON-RPC over stdio (protocol `2024-11-05`). It is
hand-rolled (no extra deps beyond `httpx` + `rich`) to honor the substrate
boundary lints.

## Substrate-boundary stance

`commands.py` is the only file in the repo that calls `kubectl` or `httpx` on
behalf of "other agents". When the substrate-boundary lint scans for
prohibited surfaces, it can whitelist this file and forbid such calls
elsewhere. The chokepoint is the enforcement.
