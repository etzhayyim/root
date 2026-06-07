---
id: adr-2605131900-organism-mcp-xrpc-proxy-phase-h
title: "Phase H — Organism Actor MCP Handlers Proxied to lg-organism Pod via XRPC"
status: active
doc_type: adr
topic: organism-actors
authoritative: true
last_verified: 2026-05-13
authoritative_paths:
  - 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/mcp_dispatch.py
  - 50-infra/prod/main.tf
  - 50-infra/vultr/cloudflared/bpmn-dispatcher-tunnel.yaml
  - 50-infra/vultr/mitama-udf-pool/values.yaml
  - 50-infra/vultr/mitama-udf-pool/templates/dispatcher.yaml
---

# ADR 2605131900: Phase H — Organism Actor MCP Handlers Proxied to lg-organism Pod

## Context

Phase G (`f507c072cb2`, 2026-05-13 17:11 JST) removed ~550 LOC of dead Zeebe infrastructure from `dispatcher_main.py` — routing fork, watcher loop, SSE path, `_list_pending_defs_sync`, BPMN deploy helpers. All 28,647 `vertex_bpmn_lexicon_binding` rows unified to `routing_target='langgraph'`.

Previously the 14 organism actor MCP handlers (saikin/ki/koke) were registered in `mcp_dispatch.py` via `register_actor_by_convention()` and executed in-process within the bpmn-dispatcher pod. The lg-organism pod (`lg-organism.mitama-udf.svc.cluster.local:8000`) already serves these actors via LangGraph but was unused by the MCP dispatch path.

## Decision

**Phase H**: The 14 organism NSID handlers are moved from in-process execution to XRPC proxies that POST to the lg-organism pod.

### Implementation

`mcp_dispatch.py` additions:

```python
_LG_ORGANISM_BASE = "http://lg-organism.mitama-udf.svc.cluster.local:8000"

_LG_ORGANISM_ACTORS: dict[str, list[str]] = {
    "saikin": ["probeEnvironment", "transferSignal", "formColony", "handoffToKi", "lyse"],
    "ki": ["absorb", "synthesize", "bloom", "ring"],
    "koke": ["scanRawSignals", "fixSignal", "classifyFixation", "handoffToHakkou", "handoffToSaikin"],
}

def _make_organism_proxy(nsid: str) -> McpHandler:
    url = f"{_LG_ORGANISM_BASE}/xrpc/{nsid}"
    async def _proxy(**arguments: Any) -> dict[str, Any]:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=arguments or {}) as resp:
                data = await resp.json()
                if not isinstance(data, dict) or "output" not in data:
                    raise RuntimeError(f"lg-organism {nsid} unexpected response: {data!r}")
                return data["output"]
    return _proxy
```

`build_default_handlers()` calls `_build_organism_handlers()` first, registering 14 proxies before the convention-based in-process handlers.

### Call chain

```
MCP client
  → POST https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message
  → CF Tunnel → bpmn-dispatcher Service (mitama-udf)
  → mcp_dispatch._proxy(nsid=com.etzhayyim.apps.saikin.probeEnvironment)
  → POST http://lg-organism.mitama-udf.svc.cluster.local:8000/xrpc/com.etzhayyim.apps.saikin.probeEnvironment
  → LangGraph node (lg-organism pod)
  → response.output unwrapped → MCP result
```

`atproto.etzhayyim.com` remains the AT Protocol PDS / DID / OAuth surface only. Public
MCP traffic must use `mcp.etzhayyim.com`; edge workers and SvelteKit BFF shims set
`AGENTGATEWAY_MCP_ROUTER_URL=https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message`.
The public hostname terminates at Cloudflare and is tunneled to the
`bpmn-dispatcher` k8s Service, which then routes MCP tool calls to
`mcp_dispatch.py` and pod-side LangServer/LangGraph runtimes (`lg-organism` for
saikin/ki/koke in Phase H). Do not route MCP calls through `atproto.etzhayyim.com`
except for legacy compatibility checks.

### Image

`ghcr.io/etzhayyim/kotodama:phase-h2-20260513192230-amd64@sha256:592ca26c2bfee942e1ccdeccfdeb7c383a4b870f44c585db199443c2c09ef2bb`

## Crash Postmortem (deployment blocker)

During rollout, both Phase H and H2 pods crashed with:

```
File ".../site-packages/kotodama/dispatcher_main.py", line 56, in <module>
    from pyzeebe import ZeebeClient, create_insecure_channel
ModuleNotFoundError: No module named 'pyzeebe'
```

**Root cause**: A manually-applied ConfigMap `bpmn-dispatcher-patch` (not in Helm chart) was mounted at `/usr/local/lib/python3.11/site-packages/kotodama/dispatcher_main.py`, overlaying the installed file with an old version that still had `from pyzeebe import...` at line 56. The Phase H image did not install pyzeebe (removed from `pyproject.toml` in `1ca30f3c290`), so the stale import crashed.

Debug pods on the same node succeeded because they had no volumeMount and saw the clean installed file.

**Fix**:
```bash
kubectl patch deployment bpmn-dispatcher -n mitama-udf --type=json -p='[
  {"op": "remove", "path": "/spec/template/spec/volumes/0"},
  {"op": "remove", "path": "/spec/template/spec/containers/0/volumeMounts/0"}
]'
kubectl delete configmap bpmn-dispatcher-patch -n mitama-udf
```

**Prevention**: ConfigMap hot-patches of site-packages files are fragile and invisible to Helm. If a live patch is needed, add it to the Helm chart template so it is tracked and versioned. For `dispatcher_main.py` changes, rebuild the image instead.

## Verification

```
kubectl exec -n mitama-udf bpmn-dispatcher-7d9b446bbf-zhpwv -- python3 -c "
from kotodama.mcp_dispatch import build_default_handlers
h = build_default_handlers()
proxies = [k for k in h if any(k.startswith(f'com.etzhayyim.apps.{a}.') for a in ['saikin', 'ki', 'koke'])]
print('Total:', len(h), 'Proxies:', len(proxies))
"
# → Total: 133 Proxies: 14

# E2E call
POST /xrpc/com.etzhayyim.mcp.message
{"method":"tools/call","params":{"name":"com.etzhayyim.apps.saikin.probeEnvironment","arguments":{}}}
# → 200 {"result": {"signalCount": 0, "signals": [], "nextRoute": "no_signals"}}
```

## Consequences

- Organism actors now execute in the lg-organism pod (LangGraph runtime) rather than in-process within bpmn-dispatcher
- MCP handler count: 133 total (14 proxies + 119 in-process)
- lg-organism pod is now a required dependency for organism MCP calls
- `mcp.etzhayyim.com` is the public MCP/XRPC router hostname; `atproto.etzhayyim.com` is not
  the MCP router.
- Phase G cleanup + Phase H proxy together complete the organism actor decoupling from bpmn-dispatcher in-process execution
