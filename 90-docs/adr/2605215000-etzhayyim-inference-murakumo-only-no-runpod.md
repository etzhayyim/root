---
id: adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
title: "ADR-2605215000: etzhayyim inference is Murakumo-fleet-only — RunPod is constitutionally prohibited"
status: superseded
doc_type: adr
topic: etzhayyim-inference-murakumo-only-no-runpod
authoritative: false
last_verified: 2026-06-17
priority: 7.0
axis: infrastructure
weight: 0.60
priority_note: "Hard constitutional invariant — no commercial GPU rental for religious-corp"
authoritative_for:
  - "Inference substrate boundary for etzhayyim religious-corp"
  - "RunPod prohibition for all religious-corp workloads"
  - "kotodama RunPod coupling audit and Step 8 cutover scope"
depends_on:
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605202345-evo-x2-gpu-pod-fleet-integration
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
related:
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605202100-etzhayyim-kotodama-cell-runner-launchd
  - 2605182312-local-bring-up-murakumo-gemma4
supersedes: []
superseded_by:
  - "2606172359"   # 憲法改正: Murakumo-only を撤廃, compute 調達を目的関数で評価 (Murakumo は default-preferred に降格)
---

# ADR-2605215000: etzhayyim inference is Murakumo-fleet-only — RunPod is constitutionally prohibited

> **SUPERSEDED 2026-06-17 by ADR-2606172359.** The categorical "Murakumo-only / no
> commercial GPU" invariant is repealed. Compute sourcing is now assessed by the ECL
> objective function (lock-in / transparency / carbon); the Murakumo fleet remains the
> DEFAULT and PREFERRED path (high-scoring), but it is no longer a hard ban. This ADR
> is retained for history.

**Status**: superseded
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

---

# Context

## Background

The etzhayyim substrate boundary has been progressively articulated across four prior ADRs:

| ADR | Rule established |
|---|---|
| ADR-2605172000 | No Kotoba/Datomic / no centralized DB — AT MST + IPFS + Base L2 |
| ADR-2605191346 | No Vultr VKE / no commercial K8s — Mac mini Murakumo fleet is Tier 1 |
| ADR-2605202345 | EVO-X2 (Radeon 8060S, 192.168.1.70) is the GPU inference backend for the fleet |
| ADR-2605214000 | No VKE, Murakumo mesh replaces VKE CNI, Lexicon port rules formalized |

None of these ADRs explicitly addressed **commercial GPU rental services** (RunPod, Lambda Labs, CoreWeave, Vast.ai, etc.) as a category. The inference substrate question was left partially open: EVO-X2 was declared the GPU inference backend (ADR-2605202345), but RunPod was not formally prohibited.

## The Problem

The vendor codebase `40-engine/kotoba/crates/kotoba-kotodama/py` (kotodama) was authored for `etzhayyim.com`'s commercial SaaS product where RunPod is legitimately used for paid SaaS workloads. Approximately 20 files contain RunPod coupling across multiple layers:

- **LLM inference routing** (`llm.py`, `chat.py`, `projector.py`, `karma_resident.py`) — RunPod Pod / Serverless endpoints hardcoded as defaults or primary routes
- **ComfyUI / image generation** (`zeebe_worker_main.py`, `mangaka.py`, `voxelforge/runpod_client.py`) — RunPod Serverless /runsync as the image generation backend
- **Training / eval delegation** (`training_run.py`, `training_http_server.py`) — `runpod_handler()` function, `_delegate_to_runpod()` helper, RunPod Serverless wire format
- **Satellite analysis** (`primitives/maps_sentinel.py`) — RunPod Serverless as the GPU analysis backend for Sentinel-1/2 imagery
- **Cost model** (`primitives/billing.py`) — RunPod 6000 Ada / H100 NVL pricing constants
- **Business logic comments** (`kaisya_ai_org.py`, `kaisya_master.py`, `etzhayyimcojp_company_ops.py`) — "RunPod 6000 Ada is LLM SSoT" embedded in docstrings
- **SDK model registry** (`sdk/kotodama-host-sdk/src/llm-model-registry.ts`) — "gemma4-runpod" / "tier0-runpod" model entries

These references are **vendor business logic** appropriate for `etzhayyim.com`'s paid SaaS operation. However, when etzhayyim religious-corp invokes kotodama modules, it must not route traffic to commercial GPU rental infrastructure.

## The Constitutional Directive

On 2026-05-21 the governing authority issued:

> **"etzhayyim では runpod は使わない. murakumo fleet のみ"**
> (etzhayyim does NOT use RunPod. Murakumo fleet only.)

This directive is structurally parallel to ADR-2605191346's "no commercial K8s" rule and ADR-2605172000's "no centralized DB" rule. It elevates "no commercial GPU rental" to a **hard architectural invariant** — not a preference.

---

# Decision

## §1 Inference SSoT for etzhayyim religious-corp

**etzhayyim* に属する全推論ワークロードは Murakumo fleet のみで実行する。**

### §1.1 Authoritative inference stack

| Layer | Component | Endpoint |
|---|---|---|
| **Primary LLM / image / audio** | LiteLLM gateway on EVO-X2 | `http://192.168.1.70:4000` (LAN, bearer key) |
| **Heavy LLM (70B class)** | EVO-X2 Ollama (llama3.3:70b, ROCm gfx1151) | `http://192.168.1.70:11434` (LAN, no auth) |
| **Image / video generation** | EVO-X2 ComfyUI | `http://192.168.1.70:8188` (LAN) |
| **Per-node LLM fallback** | Each Mac mini Ollama gemma3:4b | `http://127.0.0.1:11434` (loopback) |

EVO-X2 is the **sole** GPU inference backend per ADR-2605202345 §D1. The LiteLLM gateway at `192.168.1.70:4000` is the OpenAI-compatible abstraction layer for all religious-corp LLM calls.

### §1.2 Forbidden inference patterns for etzhayyim

The following are **constitutionally prohibited** for all code paths invoked under etzhayyim governance:

| Forbidden pattern | Reason |
|---|---|
| `api.runpod.ai` / `*.proxy.runpod.net` | Commercial GPU rental (this ADR) |
| OpenAI API direct (not via LiteLLM proxy) | Commercial API dependency — allowed only via LiteLLM proxy with religious-corp budget guard |
| Anthropic API direct from vendor billed key | Consent capability boundary — religious-corp calls via `@etzhayyim/sdk` XRPC consent |
| Vertex AI direct | Commercial cloud inference |
| AWS Bedrock direct | Commercial cloud inference |
| Linode GPU / Lambda Labs / CoreWeave / Vast.ai | Commercial GPU rental |
| Any `*.proxy.<commercial-provider>.net` | Commercial GPU proxy |

### §1.3 Env var mapping for RunPod → Murakumo redirect

When a kotodama module reads a RunPod URL from env and etzhayyim invokes it, the operator MUST set:

```bash
# LLM inference
RUNPOD_LLM_URL="http://192.168.1.70:4000/v1/chat/completions"
etzhayyim_LLM_URL="http://192.168.1.70:4000/v1/chat/completions"
LLM_PRIMARY_URL="http://192.168.1.70:4000/v1/chat/completions"

# ComfyUI / image generation
COMFYUI_URL="http://192.168.1.70:8188"
RUNPOD_COMFYUI_URL="http://192.168.1.70:8188"

# Training pod (if religious-corp runs training — see §2 VENDOR-ONLY classification)
TRAINING_POD_BASE_URL="http://192.168.1.70:8003"  # if a training HTTP server runs on EVO-X2

# TRELLIS / voxelforge (see §2 VENDOR-ONLY classification)
RUNPOD_TRELLIS_URL="http://192.168.1.70:5000"    # only if TRELLIS is deployed on EVO-X2
```

The env var swap is the **REDIRECT** verdict mechanism (see §2).

---

## §2 kotodama split classification

Each kotodama RunPod-coupled file is assigned one of three verdicts, using the same framework as ADR-2605214000 §2.

### §2.1 Substrate-fit conditions (updated)

A module is fit for religious-corp use without rewrite if ALL five conditions hold:

1. No direct commercial DB (Kotoba/Datomic / Postgres / Kysely) write — AT MST + IPFS + Base L2 only
2. No Stripe / PayPal / fiat payment processor
3. No Vultr VKE / commercial K8s scheduling dependency
4. **No RunPod / no commercial GPU rental** ← NEW (this ADR)
5. No vendor billing key that would route charges to etzhayyim.com

### §2.2 Verdict definitions

| Verdict | Meaning | Required action |
|---|---|---|
| **REDIRECT** | An env URL swap is sufficient. LiteLLM gateway already abstracts the backend; no code change needed in kotodama. | Set env vars per §1.3 before invoking. |
| **VENDOR-ONLY** | The module implements vendor (`etzhayyim.com`) business logic that etzhayyim does not invoke. Mark with module-level `# ETZHAYYIM: vendor-only — do not invoke from religious-corp` docstring / import guard. No rewrite needed; religious-corp callers must avoid these paths. | Add import guard; ensure no etzhayyim cell calls this. |
| **REIMPLEMENT** | The capability is needed by religious-corp but the implementation has RunPod as a hard structural assumption (not just an env URL). A religious-corp variant must be designed for Murakumo fleet. | Itemise redesign target in companion PYKOTODAMA-MIGRATION-NOTES.md. |

### §2.3 Itemised kotodama audit

The full table is in the companion `PYKOTODAMA-MIGRATION-NOTES.md`. Summary by verdict:

**REDIRECT (env URL swap sufficient):**
- `llm.py` — `_RUNPOD_LLM_URL` / `_etzhayyim_LLM_URL` / `RUNPOD_LLM_MODEL` are already env-overridable; point at `192.168.1.70:4000`
- `chat.py` — `_LLM_PRIMARY_URL` env-overridable; point at LiteLLM gateway
- `projector.py` — delegates to `llm.call_tier` which is env-overridable
- `business_person.py:1595` — delegates to `llm.call_tier`; docstring mention only
- `kaisya_ai_org.py` / `kaisya_master.py` — comment "RunPod 6000 Ada is LLM SSoT"; actual routing via `llm.call_tier` which is env-driven
- `etzhayyimcojp_company_ops.py` — same pattern as kaisya_*
- `langgraph_graphs/webya_site_generation.py` — comment only; routes via `llm.call_tier`
- `billing.py` — cost constants; religious-corp billing uses Murakumo cost constants (this ADR adds the obligation to replace them in any religious-corp billing context)

**VENDOR-ONLY (do not invoke from religious-corp):**
- `training_http_server.py` — H100 NVL training pod HTTP server; religious-corp has no H100 NVL
- `training_run.py` — `runpod_handler()` / `_delegate_to_runpod()` / `_run_eval_heavy_benches()` — vendor training pipeline; religious-corp training is a future separate design
- `voxelforge/runpod_client.py` — TRELLIS + ComfyUI via RunPod 6000 Ada pod; voxelforge is vendor 3D product
- `pyproject.toml` — RunPod commentary in dependency comments; vendor deployment context
- `tests/test_training_run_pod_client.py` — tests the vendor training delegation flow; religious-corp does not test RunPod HTTP wire format
- `tests/test_yoro_social.py:57` / `primitives/yoro_social.py:93` — Karmada / murakumo-k3s topology strings describe the vendor cluster; test fixtures for vendor topology, not religious-corp target
- `tests/test_maps_sentinel_pure_helpers.py` — docstring notes RunPod dependency; the pure helper tests themselves are safe but the production map_sentinel.runpod.analyze task is VENDOR-ONLY
- `primitives/karma_resident.py:17` — "runpod" substrate selection option in docstring; religious-corp organism runtime uses Murakumo only (substrate="murakumo")

**REIMPLEMENT (religious-corp variant needed):**
- `zeebe_worker_main.py` — routes ComfyUI jobs via RunPod Serverless /runsync structurally; religious-corp Zeebe worker variant must route to `192.168.1.70:8188` via LAN ComfyUI directly (no Serverless wrapper needed)
- `primitives/mangaka.py:22` — `COMFYUI_POD_URL` env is RunPod-defaulted; REDIRECT if env set, but the docstring and default must be replaced
- `primitives/maps_sentinel.py` — `task_maps_sentinel_runpod_analyze` is structurally RunPod Serverless; religious-corp variant runs Sentinel-1/2 analysis via MLX or ONNX on Mac mini (or EVO-X2 ROCm). Full REIMPLEMENT: new `task_maps_sentinel_murakumo_analyze` function
- `sdk/kotodama-host-sdk/src/llm-model-registry.ts` — `gemma4-runpod` / `tier0-runpod` entries; religious-corp SDK variant must remove these entries and add `gemma4-evo-x2` / `tier0-evo-x2` pointing at LiteLLM gateway

**REDIRECT (env + minor comment update):**
- `primitives/otakiage.py:950` — "RunPod cold-start" comment only; no routing change needed; comment updated to "EVO-X2 warm fleet" in etzhayyim variant
- `sdk/kotodama-host-sdk/src/llm-model-types.ts:21` — "CF Workers AI / RunPod" comment in JSDoc; no routing change; doc update only

---

## §3 Itemised audit — see companion document

The line-by-line audit table (File | Line(s) | Current | Target | Verdict | Reason) is maintained in:

```
40-engine/kotoba/crates/kotoba-kotodama/py/PYKOTODAMA-MIGRATION-NOTES.md
```

This companion document is the **single source of truth for the Step 8 cutover sub-list** for kotodama RunPod decoupling.

---

## §4 Step 8 cutover deferral

**Do not rename or rewrite any kotodama file today.**

Per repo-root `CLAUDE.md` §Status row 8, the 220-file `amanomibashira` → `etzhayyim` cutover is gated on legal registration. The kotodama RunPod decoupling is a **sub-task of Step 8**, not a separate standalone operation.

Today's deliverables are:
1. This ADR (paper-only decision record)
2. `PYKOTODAMA-MIGRATION-NOTES.md` (itemised audit companion)

The per-file changes (env var guard additions, REIMPLEMENT targets) happen during the Step 8 cutover wave, in one atomic PR, along with the `amanomibashira` → `etzhayyim` renames.

---

## §5 Status amendments to existing ADRs

This ADR **extends** (does not supersede) the following:

| ADR extended | Extension |
|---|---|
| ADR-2605191346 | Adds "no commercial GPU rental" as a parallel prohibition alongside "no commercial K8s". The substrate-sovereignty invariant now covers both compute orchestration and inference layers. |
| ADR-2605202345 | Declares EVO-X2 / LiteLLM gateway as the **sole** GPU inference SSoT for religious-corp — not one option among several. Forecloses RunPod as an alternative path. |
| ADR-2605214000 §2 condition 4 | Makes RunPod explicit in the substrate-fit condition list. The prior text was "commercial cloud dependency"; this ADR names RunPod specifically as an instance of that category. |

---

# Consequences

1. **Architectural sovereignty closure for inference**: etzhayyim now has a complete substrate sovereignty claim across K8s (ADR-2605191346), database (ADR-2605172000), and inference (this ADR). No tier of the stack routes through commercial cloud infrastructure. The sovereignty perimeter is closed for Tier 1 compute.

2. **Vendor kotodama remains operative for etzhayyim.com**: etzhayyim.com's kotodama with RunPod stays fully operational for paid SaaS workloads. The two codebases run in parallel forever. This ADR does not require etzhayyim.com to change anything. The split is a consent capability boundary — religious-corp callers must route through etzhayyim-specific env config and avoid VENDOR-ONLY paths.

3. **Some religious-corp features need successor implementations**: `maps_sentinel.py` L7/L8 satellite analysis (Sentinel-1/2 GPU analysis) requires a Murakumo-native rewrite. The target is MLX-based inference on Mac mini (Apple Silicon) or EVO-X2 ROCm (gfx1151) for ONNX/PyTorch models. This is a new engineering effort; the capability is not available on the Murakumo fleet today and must be tracked as a follow-up ADR.

4. **Audit itemisation gives Step 8 a concrete sub-list**: The companion `PYKOTODAMA-MIGRATION-NOTES.md` provides a file-by-file, line-by-line cutover plan. Step 8 can execute the kotodama RunPod decoupling from that document alone without re-auditing the codebase.

5. **Risk — EVO-X2 single point of failure**: All GPU inference is currently concentrated on one EVO-X2 machine at `192.168.1.70`. If EVO-X2 is unavailable, all image/video generation is unavailable and LLM inference degrades to per-node gemma3:4b (Ollama on each Mac mini). Mitigation: the per-node Ollama fallback keeps text LLM functional. Medium-term mitigation: a second EVO-X2 class machine (or Mac mini M4 Max 128 GB) as replica. Long-term: NPU (AMD XDNA, 50 TOPS) as a third inference path once Ryzen AI SDK integration completes (tracked in ADR-2605202345 open questions).

---

# Alternatives Considered

## A1. Keep RunPod for religious-corp with consent capability

Proposal: Allow etzhayyim to use RunPod under a consent-capability XRPC gate — the commercial billing flows to etzhayyim.com, and etzhayyim receives inference as a "donated service".

**Reject**: This is the same slippery-slope pattern that ADR-2605191346 §2 rejected for commercial K8s. A consent-capability wrapper does not change the structural dependency: etzhayyim's inference availability would be contingent on etzhayyim.com maintaining RunPod subscriptions. The religious-corp's operational autonomy is undermined. Substrate sovereignty requires that etzhayyim can operate the inference tier independently of any commercial vendor's willingness to continue service.

## A2. Move to a different commercial GPU rental (Lambda Labs, CoreWeave, Vast.ai)

Proposal: Replace RunPod with a different commercial GPU rental service that does not have the same proxy-UA fingerprinting issues.

**Reject**: The objection is not to RunPod specifically but to the category "commercial GPU rental". Any commercial provider creates the same dependency structure: operational availability contingent on commercial relationship, pricing subject to vendor change, data sovereignty unclear. The EVO-X2 (already owned hardware, LAN-only, no DID, no AT membership requirement) eliminates all three failure modes. The architectural objection is to the category, not the brand.

## A3. Build a separate religious-corp GPU cluster on rented bare-metal

Proposal: Rent dedicated bare-metal GPU servers (Hetzner GPU, OVH Advance servers) under etzhayyim's name rather than using shared GPU cloud. This would be "etzhayyim's own metal".

**Reject**: Rented bare-metal is still a commercial dependency. The religious-corp would be dependent on Hetzner/OVH's willingness to continue service, their pricing decisions, and their data center location. The Mac mini fleet + EVO-X2 (already owned, on-premises, no recurring cloud cost) is structurally superior for the religious-corp's operational independence. Future hardware expansion should be owned hardware: additional EVO-X2 class machines or Mac mini M4 Max units, purchased outright.

---

# References

- ADR-2605191346: etzhayyim is Vultr-free — Murakumo Mac-mini fleet as the only Tier-1 substrate (parallel "no commercial" invariant for K8s)
- ADR-2605172000: etzhayyim/root open apps MUST be kotoba (substrate boundary establishing pattern)
- ADR-2605202345: EVO-X2 GMKtec integration — GPU inference pod (EVO-X2 as sole GPU inference backend)
- ADR-2605214000: etzhayyim Murakumo mesh, no VKE, Lexicon port rules (most recent substrate ADR; this ADR is its successor for the inference layer)
- ADR-2605192415: Religious-Corp Daemon Architecture (Murakumo cell placement)
- ADR-2605202100: kotodama-cell-runner launchd (Murakumo fleet operational pattern)
- Sister document: `40-engine/kotoba/crates/kotoba-kotodama/py/PYKOTODAMA-MIGRATION-NOTES.md` (itemised audit companion, Step 8 cutover sub-list)
- Vendor parallel repo: `etzhayyim-apps-etzhayyimcojp/` — RunPod legitimately used for etzhayyim.com paid SaaS; do not modify
