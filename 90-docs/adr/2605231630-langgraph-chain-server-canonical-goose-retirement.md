---
id: 2605231630-langgraph-chain-server-canonical-goose-retirement
title: "ADR-2605231630: LangGraph + kotoba-datomic + langserver canonical agent runtime; Goose retired; K8s/k3s/GPU-pod reintroduction approved"
status: proposed
doc_type: adr
topic: agent-runtime-canonical
authoritative: true
last_verified: 2026-05-23
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "operator directive 2026-05-23 — replaces the Goose+RunPod-only stack with a LangGraph+kotoba-datomic+langserver+k3s religious-corp runtime"
authoritative_for:
  - canonical agent runtime decision (was Goose; now LangGraph cell catalog)
  - religious-corp cell substrate (was launchd-only; now k3s on Mac mini fleet per ADR-2605232100)
  - K8s/k3s/GPU-pod reintroduction policy (was "禁止 再導入禁止"; now approved within etzhayyim/* scope)
depends_on:
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605232100-etzhayyim-organism-vertical-implementation
related:
V05171300
V05182312-local-bring-up-murakumo-gemma4
supersedes:
  - "60-apps/etzhayyim-project-murakumo/CLAUDE.md §Hard Constraints (2026-05-11): the K8s/WireGuard/Aeron/UCX/RDMA/Ray/Nomad 禁止 line is lifted for etzhayyim/* religious-corp cells; the RunPod LLM SSoT decision is left intact"
  - "ADR-0034 (Goose agent runtime — yoro-as-actor topology, 2026-04-20, murakumo-scoped): Goose role + recipes + crontab entries on judah are retired in favor of LangGraph cells served from langserver under kotoba-datomic substrate"
superseded_by: []
---

# ADR-2605231630: LangGraph + kotoba-datomic + langserver canonical agent runtime; Goose retired; K8s/k3s/GPU-pod reintroduction approved

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

Two architectural decisions were taken in spring 2026 that, by autumn, no longer reflect operator intent:

1. **2026-04-20 — ADR-0034 (murakumo scope): Goose as the agent runtime on judah.** OpenClaw was retired; Goose cron recipes (yoro-profile-heartbeat / yoro-persona-cron / yoro-mention-drain) became the side-effect engine for the yoro actor and the pattern for future T1 actors. The wrapper shell + native Ollama `:11434` (LiteLLM bypass) + qwen3.5:9b stack was tuned over weeks (16K context, --no-profile flags, recipe-size <3KB, etc.).

2. **2026-05-11 — Murakumo CLAUDE.md §Hard Constraints: K8s/WireGuard/Aeron/UCX/RDMA/Ray/Nomad 禁止 — 再導入禁止.** The Mac Mini fleet was demoted to "L8 Somatic Inference for resident organism actors only" (ADR-2605080600). RunPod (RTX 6000 Ada vLLM, endpoint `vyp99t9px7h4dl`) became the LLM SSoT. K8s, WireGuard, and the older Lima-k3s GPU cluster effort were declared architectural dead ends. The Murakumo project itself committed to a flat Ollama + LiteLLM topology with `@reboot` crontab for daemon supervision.

The 2026-05-19 religious-corp constitutional wave (ADR-2605192100 mission charter through ADR-2605192415 daemon architecture) shipped 15 Pregel cells, a 18,342-agent UNSPSC corpus, and a kotoba-datomic substrate spec — all expressed as LangGraph StateGraph modules under `20-actors/magatama/cells/` and `…/langgraph_graphs/unispsc_agents/`. None of these are Goose recipes. None of them fit cleanly inside the launchd-or-Ollama-only model that the May 11 constraint implies.

ADR-2605232100 (this morning, 2026-05-23) tried to thread the needle by re-introducing k3s **only** for religious-corp cells. Stage 2 validation on orbstack succeeded, but Stage 3 (Mac mini fleet bring-up via Ansible) surfaced the direct contradiction with the Murakumo CLAUDE.md K8s 禁止 line.

Operator directives, 2026-05-23 afternoon:

> goose は除去で ok. langgraph, chain, server が main.

> gpu pod, k8s, k3s 導入は ok.

This ADR records the architectural pivot those two directives mandate.

## Decision

**(1) Canonical agent runtime — etzhayyim/* scope.** The triple `(LangGraph, kotoba-datomic, langserver)` is the single canonical agent runtime for religious-corp activity in `etzhayyim/root`. Specifically:

- **LangGraph** — every agent is a compiled `StateGraph`. Per-actor under `20-actors/magatama/py/src/pymagatama/langgraph_graphs/` (18,342 UNSPSC commodity actors today) or per-cell under `20-actors/magatama/cells/` (15 religious-corp cells per ADR-2605192415 + 16 yorishiro source connectors).
- **kotoba-datomic** (`10-protocol/kotoba-datomic/`, ADR-2605231400) — the composition of `(DID + WebAuthn + Adherent SBT) + (atproto PDS MST source chain) + (IPFS + Base L2 anchor DHT) + (Lexicon + Rego + LangGraph membrane)` provides all state, identity, and validation. AT-IPFS-local SQLite hot-cache (`pymagatama.primitives.at_ipfs_belief_store`) is the agent-side knowledge accumulator (perceive/record loop wired in ADR-2605232100 Stage D, 2026-05-23).
- **langserver** — the XRPC façade that exposes LangGraph agents over `com.etzhayyim.apps.<domain>.invokeAgent` / `…listAgents` / `…health` / `…classify` Lexicons. `lg-open-unispsc` (live on orbstack, 2026-05-23) is the reference implementation; per-cell langservers (per ADR-2605202200 cell runtime contract) follow the same pattern.

**(2) Goose retirement.** The Goose agent runtime decisions in `60-apps/etzhayyim-project-murakumo/CLAUDE.md` (ADR-0034 scope) are retired in `etzhayyim/*` scope:

- `roles/goose/` Ansible role: marked retired; new `purge_goose.yml` idempotent task removes `~/.config/goose/`, the wrapper script, and `~/.etzhayyim/goose-cron-wrapper.sh` on next apply.
- `crontab @ judah` entries `yoro-profile-heartbeat` / `yoro-persona-cron` / `yoro-mention-drain`: scheduled to be removed in the same Ansible apply; replacement is a LangGraph cell (one per yoro pipeline) deployed under `20-actors/magatama/cells/yoro_*/` and served by `langserver` per pattern (b).
- `roles/openclaw/` and `cli/openclaw.go`: already retired 2026-04-20, no further action.
- The model registry on judah (qwen3.5:9b on native Ollama `:11434`) **stays** — it's a backing LLM that LangGraph cells call via `pymagatama.llm.litellm` or directly via Ollama HTTP. Only the *agent runtime* (Goose) is retired, not the LLM backend.
- The RunPod RTX 6000 Ada vLLM endpoint `vyp99t9px7h4dl` likewise **stays** as the primary LLM SSoT per Murakumo CLAUDE.md §Hard Constraints item 1; that decision is unaffected by this ADR.

**(3) K8s / k3s / GPU-pod reintroduction approved (etzhayyim/* scope only).** The 2026-05-11 Murakumo CLAUDE.md hard-constraint "K8s/WireGuard/Aeron/UCX/RDMA/Ray/Nomad 禁止 — 再導入禁止" was scoped to the Mac Mini Ollama LLM substrate. It is lifted for `etzhayyim/*` religious-corp cells:

- **k3s** on Lima VMs across the Mac mini fleet — production substrate for religious-corp cells per ADR-2605232100. Ansible playbook `60-apps/etzhayyim-project-murakumo/ansible/k8s-gpu-cluster.yml` (Stage 3) is the canonical bootstrap path.
- **WireGuard `wg0`** — required for cross-VM pod networking; bound to the playbook above.
- **GPU pods** — workloads needing GPU acceleration (kami-engine inference, MLX local fallback, ComfyUI burst) may schedule as k3s Pods with the appropriate `nvidia.com/gpu` / `apple.com/gpu` requests. Murakumo Kubelet (`50-infra/k8s/murakumo-kubelet/`) bridges to RunPod when the fleet runs out of local capacity (ADR-2605110100 vendor-monorepo, retained policy).

Vultr / EKS / GKE / AKS / DigitalOcean Kubernetes remain prohibited (ADR-2605191346 §1, unchanged). Only self-hosted k3s on Mac mini Lima VMs is permitted.

**(4) Murakumo CLAUDE.md update.** `60-apps/etzhayyim-project-murakumo/CLAUDE.md` is updated in the same change set as this ADR to:

- Remove "K8s/WireGuard/Aeron/UCX/RDMA/Ray/Nomad 禁止 — 再導入禁止" from §Hard Constraints; replace with a narrower "Ray / Nomad / Aeron / UCX / RDMA 禁止; K8s/k3s/WireGuard は ADR-2605231630 で religious-corp cell scope のみ許容" line.
- Move Goose section content to a §Retired heading at the bottom; remove the operational verification tables that imply current use.
- Update §Dead Components table: remove `K8s / WireGuard` from the dead list; add `Goose agent runtime (ADR-0034 scope, superseded by ADR-2605231630)`.
- Update §Fleet Topology IPs to current Ethernet-side values (192.168.1.11–21 per `50-infra/murakumo/fleet.toml`, 2026-05-21 verified); the .49–.67 WiFi-side IPs are superseded.

**(5) fleet.toml IP reconciliation.** `50-infra/murakumo/fleet.toml` is the IP SoT (verified 2026-05-21 via mDNS + ARP from jacob). Murakumo CLAUDE.md is updated to match, not the other way around.

## Consequences

### Positive

- Stage 3 of ADR-2605232100 is unblocked: `ansible-playbook k8s-gpu-cluster.yml` against the Mac mini fleet is now consistent with project SoT.
- Single canonical agent runtime — operators and contributing agents do not have to decide whether a new pipeline lives in a Goose recipe vs a LangGraph cell vs a launchd plist. It's always a LangGraph cell wrapped by langserver, anchored to kotoba-datomic.
- Goose's brittleness (16K context tuning, recipe-size <3KB ceiling, model-specific tool-call quirks, dollar-quoted-string SQL incompatibility) is eliminated as a class of failure.
- The 18,342-actor UNSPSC corpus + 15 religious-corp cells already follow this pattern, so canonicalizing it ratifies existing investment.

### Negative

- Yoro actor's 3 cron pipelines (heartbeat / persona-cron / mention-drain) need re-implementation as LangGraph cells. Estimated 1–2 days operator work; cells are in scope for the religious-corp Pregel catalog.
- Murakumo CLAUDE.md needs a substantive edit (this ADR records the intent; the actual edit lands in the same commit).
- Operator must manually clear judah crontab + uninstall `~/.config/goose/` once the LangGraph replacement cells are live. The `purge_goose.yml` Ansible task automates the uninstall but the crontab edit is interactive (per CLAUDE.md "Cron via crontab (not goose schedule add)").
- WireGuard overlay (`wg0`) reintroduced — was previously eliminated in favor of "clean physical LAN" (Murakumo CLAUDE.md §Physical LAN topology 2026-05-11). For k3s cross-VM pod networking this is unavoidable; clean LAN remains adequate for Ollama node-to-node traffic.

### Neutral

- RunPod RTX 6000 Ada vLLM endpoint remains the LLM SSoT for high-volume inference. Mac mini Ollama remains as the L8 Somatic Inference backend for resident organism actors.
- LiteLLM proxy on judah `:4000` stays — both Goose (during transition) and LangGraph cells can route through it.
- Cloudflare Tunnel `murakumo-fleet` (ID `ae341542`) continues to handle public `murakumo.etzhayyim.com` ingress.

## Alternatives Considered

| Option | Rejected because |
|---|---|
| Stay on Goose + Ollama; force religious-corp cells into Goose recipes | Recipe-size ceiling (<3KB) + qwen3.5:9b tool-call brittleness cannot host the 15-cell religious-corp catalog or any of the 18,342 UNSPSC actors. Was already breaking down at 3 recipes (yoro). |
| Keep K8s 禁止; run religious-corp cells as launchd daemons (ADR-2605191346 §3 original path) | ADR-2605232100 documented why launchd cannot express the declarative placement, rolling update, sidecar dependency, swarm Lease, and quorum invariants that kotoba-datomic cells need. Re-arguing the same case repeatedly is unproductive. |
| Move all religious-corp cells to RunPod GPU pods (no Mac mini fleet at all) | Runs counter to the Tier-1 substrate hard rule (ADR-2605191346): etzhayyim/* must not depend on commercial K8s. Mac mini fleet is the only sovereign-substrate option. |
| Split runtime by actor type (Goose for yoro, LangGraph for religious-corp, Ollama-direct for UNSPSC) | Three runtime families compound onboarding cost and create three categories of edge-case bugs. The operator directive ("langgraph, chain, server が main") explicitly rejects this. |

## References

- ADR-2605232100 — religious-corp cells on k3s DaemonSet (Stage 3 unblocked by this ADR)
- ADR-2605231400 — kotoba-datomic Holochain-iso substrate (defines `chain` in "langgraph + chain + server")
- ADR-2605192415 — religious-corp daemon architecture (15-cell catalog)
- ADR-2605192100 — etzhayyim mission charter (canonical scope)
- ADR-2605191346 — Vultr-free / no commercial K8s (this ADR carves out self-hosted k3s from that rule)
- ADR-2605202200 — cell runtime contract (defines langserver pattern)
- `60-apps/etzhayyim-project-murakumo/CLAUDE.md` — Murakumo project SoT; edited in the same commit as this ADR
- `60-apps/etzhayyim-project-murakumo/ansible/k8s-gpu-cluster.yml` — Stage 3 bootstrap playbook
- `60-apps/etzhayyim-project-murakumo/ansible/roles/lima_k3s_gpu/` — k3s role (tools / preflight / bootstrap / deploy_llama_vulkan)
- `50-infra/murakumo/fleet.toml` — cell placement + IP SoT
- `50-infra/k8s/lg-open-unispsc/deployment.yaml` — reference langserver implementation (18,342 UNSPSC actors live on orbstack 2026-05-23)
- `20-actors/magatama/cells/` — religious-corp Pregel cell catalog
- `20-actors/magatama/py/src/pymagatama/unispsc_capabilities/wrapper.py` — perceive/record loop (Stage D, 2026-05-23)
