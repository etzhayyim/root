---
id: adr-2604251758-murakumo-yoro-actor-worker-fleet
title: "ADR: Murakumo Mac mini fleet as persistent yoro actor workers"
status: accepted
doc_type: adr
topic: murakumo-yoro-actor-worker-fleet
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - Murakumo Mac mini k3s fleet placement for Zeebe workers
  - yoro.etzhayyim.com persistent AT Protocol actor loop on Murakumo
  - LangGraph agent worker and MCP tool boundary for yoro social actions
  - llama.cpp Vulkan inference tier for actor workers
related:
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-0056-bpmn-as-actor
  - adr-0087-magatama-mcp-tool-facade
  - adr-2604231811-atproto-extension-service-layers
  - adr-2604241038-yoro-pds-ideal-topology
  - adr-0061-murakumo-platform-auth-unification
supersedes: []
superseded_by: []
---

# Context

Murakumo has been re-shaped from a loose Mac mini inference fleet into an
11-node k3s cluster running inside Lima/krunkit Fedora guests. The verified
cluster has one control-plane node (`jacob`) and ten workers (`dan`,
`simeon`, `naphtali`, `levi`, `benjamin`, `joseph`, `judah`, `issachar`,
`zebulun`, `asher`) on the `10.77.0.0/24` WireGuard overlay.

The same fleet is now expected to host more than stateless inference. The
target is a persistent `yoro.etzhayyim.com` AT Protocol actor loop that can post,
reply, like, comment, repost, follow, and self-improve as an actor, while
remaining compatible with the existing BPMN-as-actor and LangGraph-as-Zeebe
decisions.

Existing constraints still hold:

- `yoro.etzhayyim.com` is an AT Protocol actor surface. Public social writes must
  commit through the PDS path, not by inventing a private social store.
- BPMN remains the orchestration SSoT for outer-loop autonomy.
- LangGraph runs as Zeebe ServiceTask compute, not inside the Cloudflare
  Worker edge.
- MCP is the tool discovery surface. It must not become a second dispatcher
  that bypasses BPMN or the PDS governance path.
- Kubernetes resources must not be created in the `default` namespace.

# Decision

Use the Murakumo k3s fleet as a **persistent actor-worker substrate** for
`yoro.etzhayyim.com`, with four namespaces and one social write boundary:

| Namespace | Responsibility |
|---|---|
| `murakumo-system` | fleet services: WireGuard control, node inventory, llama.cpp Vulkan inference |
| `yoro-actors` | Zeebe workers, LangGraph runners, actor schedulers, MCP adapters |
| `zeebe-system` | Zeebe broker / gateway / Operate when hosted on Murakumo |
| `observability` | metrics, logs, actor liveness probes, audit exporters |

The live GPU workload is `murakumo-system/llama-vulkan-fleet`, a DaemonSet
that runs one llama.cpp Vulkan pod per Murakumo Mac mini node. The compatibility
Service `murakumo-system/llama-vulkan` points at the same DaemonSet endpoints
for older actor manifests. This is **not** Ollama GPU on macOS Metal in a pod.
It is a Linux guest Vulkan path that exposes Apple GPU through
virtio-gpu/Venus and has been verified with GPU layer offload.

## Runtime Shape

```
AT Protocol client / scheduler event
  |
  v
atproto.etzhayyim.com PDS Worker
  |  XRPC / service auth / governance / social write gate
  v
bpmn-dispatcher
  |
  v
Zeebe process instance
  |
  +--> yoro-actors/zeebe-worker-python
  |      - generic.langgraph.run
  |      - generic.mcp.call
  |      - generic.pds.dispatch
  |      - generic.audit.emit
  |
  +--> yoro-actors/langgraph-agent-worker
         - draft post / reply / quote / moderation rationale
         - tool plan using MCP tools/list + tools/call
         - inference via murakumo-system/llama-vulkan-fleet
```

Social actions are represented as BPMN job types, not as ad hoc cron scripts:

| Action | BPMN process | Required PDS operation |
|---|---|---|
| post | `com.etzhayyim.yoro.social.post` | `com.atproto.repo.createRecord` for `app.bsky.feed.post` |
| reply / comment | `com.etzhayyim.yoro.social.reply` | `app.bsky.feed.post` with `reply` ref |
| like | `com.etzhayyim.yoro.social.like` | `app.bsky.feed.like` |
| repost | `com.etzhayyim.yoro.social.repost` | `app.bsky.feed.repost` |
| follow | `com.etzhayyim.yoro.social.follow` | `app.bsky.graph.follow` |
| policy update | `com.etzhayyim.yoro.policy.review` | private `vertex_yoro_policy` write, then audit |

`comment` is modeled as a reply record because AT Protocol does not have a
separate public comment collection in the Bluesky app lexicon.

## MCP Boundary

MCP exposes tools to the LangGraph worker, but tool calls resolve back to the
same primitives used by BPMN workers.

Required tools:

| MCP tool | Backing primitive |
|---|---|
| `yoro.social.searchCandidatePosts` | RisingWave read / AppView query |
| `yoro.social.draftPost` | `generic.langgraph.run` + Murakumo inference |
| `yoro.social.dispatchPost` | `generic.pds.dispatch` |
| `yoro.social.dispatchReaction` | `generic.pds.dispatch` |
| `yoro.policy.read` | Worker-direct Hyperdrive / RisingWave read |
| `yoro.policy.proposeUpdate` | BPMN policy process + audit gate |
| `yoro.audit.emit` | `generic.audit.emit` |

The MCP server is therefore an adapter, not a source of authority. It can be
implemented as `yoro-actors/yoro-mcp-adapter` or through the existing
`mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message` registry, but it must not write
social records directly.

## Persistent Actor Loop

The actor loop is split by time domain:

| Time domain | Trigger | Worker |
|---|---|---|
| ms-s sensor | AppView / firehose / materialized view freshness | RisingWave + PDS Worker |
| seconds reactive | mention, follow, candidate like/repost | BPMN message-start + Zeebe worker |
| minutes deliberative | scheduled post / reply planning | LangGraph ServiceTask |
| hours policy | self-review, rate tuning, memory compaction | BPMN timer-start + quorum gate |

The loop stores state in three places:

- Zeebe variables for small per-instance state.
- `vertex_langgraph_state` or equivalent state-ref table for long agent state.
- AT Protocol repo records only for public social actions that should federate.

# Verified State (2026-04-27)

- k3s cluster: 11 nodes Ready, k3s `v1.34.6+k3s1`.
- Overlay: `murakumo-netd` WireGuard on `10.77.0.0/24`.
- Pod routing: flannel `host-gw`; node pod CIDRs are routed through WireGuard
  `AllowedIPs`.
- Token storage: k3s token generated and stored in macOS Keychain service
  `etzhayyim.murakumo.k3s`, account `MURAKUMO_K3S_TOKEN`.
- Inference DaemonSet: `murakumo-system/llama-vulkan-fleet` reports
  `11 desired / 11 updated / 11 ready / 11 available`.
- Inference image: `ghcr.io/etzhayyim/murakumo-llama-vulkan:20260427-fleet-arm64`
  pushed to GHCR with digest
  `sha256:7fa023b6213fb798e19138503270e3b2982c372146909e8f86e25a5c13ac7123`.
- Services:
  - `llama-vulkan-fleet.murakumo-system.svc.cluster.local:8080`
  - `llama-vulkan.murakumo-system.svc.cluster.local:8080` as a compatibility
    Service selecting the same DaemonSet pods.
- GPU verification: llama.cpp logs show `Vulkan0: Virtio-GPU Venus (Apple M4)`
  and `offloaded 31/31 layers to GPU`.
- API verification: Service-local `/v1/models` returns `smollm2-vulkan`.
- Actor verification: `yoro-actor-zeebe-worker` and `shinka-actor-zeebe-worker`
  are Ready and use
  `http://llama-vulkan-fleet.murakumo-system.svc.cluster.local:8080/v1`.
- Social smoke post: `at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/murakumo20260425100500409`
  was written and read back through `atproto.etzhayyim.com` `getRecord` and
  `getAuthorFeed`. This verifies the current graph-visible yoro post path.
- Cron placement: `yoro-actors/yoro-social-post` is defined as a
  resource-minimal Kubernetes CronJob that runs every four hours and writes the
  same `vertex_repo_record` fallback used by `platformPulse`. It calls `FLUSH`
  and allows a 600s deadline because RisingWave visibility can lag during
  compaction or Hummock pressure. Live CronJob sanity check created
  `at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/murakumo-cron-20260425102724-1`
  and it was read back through `com.atproto.repo.getRecord`.

## Knowledge Worker Integration

`yoro-actors` is also the placement boundary for enrichment workers that feed
actor memory and intel inference:

| Workload | Frequency | Function |
|---|---:|---|
| `yoro-common-crawl-frontier` | 2h | Discover Common Crawl CDX/WAT/WET candidates and queue URLs |
| `yoro-web-fetch` | 1h | Fetch queued pages, extract text, metadata, links, and evidence |
| `yoro-image-webp-ocr` | 3h | Fetch images, convert to WebP, OCR, and persist blob metadata |
| `yoro-intel-fusion` | 2h | Call / integrate `intel.etzhayyim.com` inference over new evidence |
| `yoro-mcp-adapter` | always-on | Expose social, knowledge, and intel tools to LangGraph via MCP |
| `yoro-actor-zeebe-worker` | always-on | Execute BPMN service tasks through pyzeebe |
| `yoro-langgraph-agent-worker` | always-on | Plan posts/replies and tool use with Murakumo inference |

The steady-state target is:

```
CronJob / Zeebe timer
  -> pyzeebe generic.* tasks
  -> LangGraph agent planning
  -> MCP tool calls for common crawl, web fetch, image OCR, intel fusion
  -> social dispatch / graph-visible fallback
  -> audit
```

Resource policy is conservative by default: each CronJob uses
`concurrencyPolicy: Forbid`, bounded `activeDeadlineSeconds`, small history
limits, and explicit CPU/memory requests. High-memory OCR/WebP work is isolated
from the social-post CronJob so a media spike cannot block posting.

# Consequences

Positive:

- Murakumo becomes useful for persistent actor execution, not just LLM serving.
- yoro actor autonomy stays aligned with ADR-0056 and ADR-2604250836.
- Social writes remain AT Protocol-native and auditable.
- The Mac mini GPU path is practical today through llama.cpp Vulkan, without
  waiting for Ollama Metal GPU support inside Kubernetes.

Trade-offs:

- The Vulkan path is tied to Lima/krunkit Venus behavior and is less portable
  than a normal NVIDIA GPU device plugin.
- The llama.cpp Vulkan image is now mirrored to GHCR for arm64 fleet
  scheduling. Future tags must be immutable and published before rollout.
- `murakumo-netd` is not a full Tailscale replacement. It covers LAN-oriented
  WireGuard inventory and pod-CIDR routing, not DERP relay, NAT traversal,
  identity ACLs, or MagicDNS.
- Actor writes need strict rate limits and policy gates. A persistent social
  actor must be conservative by default.

# Required Implementation

1. Create `yoro-actors` namespace and keep all yoro actor workloads out of
   `default`.
2. Add Helm/Kustomize manifests for:
   - `zeebe-worker-python`
   - `langgraph-agent-worker`
   - `yoro-mcp-adapter`
   - `yoro-actor-scheduler`
3. Add BPMN definitions for post/reply/like/repost/follow/policy review.
4. Add Service Auth JWT mint/verify path for `generic.pds.dispatch`, scoped by
   `lxm` to the concrete XRPC operation.
5. Add `vertex_actor_action_log` or reuse existing audit tables so every MCP
   tool call and social dispatch has a durable trace.
6. Keep `llama-vulkan-fleet` image tags immutable and published to GHCR before
   rollout; do not use node-local `:local` tags for multi-node scheduling.

# Prohibitions

- No Kubernetes resource in `default`.
- No direct MCP social write that bypasses BPMN and PDS.
- No Cloudflare Worker LangGraph loop.
- No direct database insert that pretends to be a federated social action.
- No pod-per-actor topology for yoro until a new ADR supersedes this one.
