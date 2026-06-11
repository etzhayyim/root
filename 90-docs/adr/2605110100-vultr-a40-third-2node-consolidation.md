---
id: adr-2605110100-vultr-a40-third-2node-consolidation
title: "Vultr A40 1/3 × 2 node consolidation (RW + ComfyUI + keiei-llm)"
status: proposed
doc_type: adr
topic: vultr-a40-2node-consolidation
authoritative: true
last_verified: 2026-05-11
authoritative_for:
  - Vultr VKE node-pool topology after Kotoba/Datomic + ComfyUI + keiei-llm consolidation
  - per-node placement of GPU consumers under 2-slice constraint (3 consumers / 2 GPUs)
  - dual-container GPU-sharing pattern for keiei-llm E2B+E4B
  - migration phases + rollback
related:
  - adr-0094-kotoba-stable-three-node-topology
  - adr-0048-kotoba-vultr-b2-primary
  - adr-2604231328-animeka-bpmn-l40s-pipeline
  - adr-2605101200-ai-cxo-roles-lsp-resident
  - adr-2605102100-keiei-llm-vultr-cpu-inference
---

# ADR 2605110100 — Vultr A40 1/3 × 2 node consolidation

Status: **Blocked by Vultr VKE GPU unlock** (2026-05-11, iter135).
Vultr support ticket: **UKO-46CXG** (filed 2026-05-11, requesting
vcg-a16-* and vcg-a40-* plan enablement for VKE node pools).
Originally proposed iter131 with target SKU `vcg-a40-8c-40g-16vram × 2`
in lax; that SKU is not in lax inventory (only vcg-a40-1c-5g-2vram).
iter134 pivoted target to `vcg-a16-6c-64g-16vram × 2 (sjc)` which is
in inventory but blocked by the unlock requirement above.

Operating Entity: etzhayyim (sole principal).
Vendor: etzhayyim Japan株式会社 (engineering capacity).

## 0. Blockers (iter135)

1. **lax region GPU inventory empty** for our target SKUs: only
   `vcg-a40-1c-5g-2vram` (2 GB VRAM) available — useless for SDXL or E4B.
   Confirmed via `GET /v2/regions/lax/availability?type=vcg`.
2. **Cloud GPU plans require Vultr support unlock for VKE node pools.**
   API attempts to create new VKE clusters or add node pools with
   vcg-* plans return 500 with explicit message
   `Please open a support request for access to this product`.
   Filed ticket UKO-46CXG.

Workaround paths (until UKO-46CXG resolves):
- **(B)** plain Vultr Cloud GPU instance (`vcg-a16-6c-64g-16vram` in sjc)
  + self-hosted k3s + ComfyUI Helm release. Migrates to VKE later.
- **(C)** RunPod 24×7 maintained at $580/mo (no migration).

The Phase 1–5 plan in §7 + the chart code in `50-infra/vultr/keiei-llm-pool/`
+ `50-infra/vultr/comfyui-pool/` remain valid; only Phase 0 is blocked.

## 1. Decision

Replace the current split estate

- 2 × `vhf-16c-58gb` (Kotoba/Datomic + Mitama / cohort / langgraph + keiei-llm CPU)
- 1 × RunPod RTX 6000 Ada ($0.77/hr, 24×7) for ComfyUI

with a single Vultr VKE node pool

- **2 × `vcg-a40-8c-40g-16vram`** (each = 8 vCPU / 40 GiB RAM / NVIDIA A40 1/3 slice = 16 GB VRAM, $0.575/hr from Vultr UI 2026-05-11)

co-locating Kotoba/Datomic compute, ComfyUI SDXL inference, and the
keiei-llm Phase-1 GPU pods on the same pool. The 3rd GPU consumer
(keiei-llm has E2B + E4B = 2 models, plus ComfyUI = 3 total) is
absorbed by **co-locating E2B + E4B as two containers in a single pod
that requests one `nvidia.com/gpu`** and shares the slice's 16 GB
VRAM.

## 2. Why 2 nodes 1/3 instead of 3 nodes 1/4

Both alternatives were sized in iter130–131 against the same
workload set. Confirmed Vultr UI prices (2026-05-11):

| | 2 × vcg-a40-8c-40g-16vram | 3 × vcg-a40-6c-30g-12vram (1/4) |
|---|---|---|
| $/hr per node | $0.575 | ~$0.43 (extrapolation) |
| $/mo total compute | **$839** | ~$942 |
| $/mo with storage | **~$890** | ~$988 |
| Total RAM | 80 GiB | 90 GiB |
| Total vCPU | 16 | 18 |
| GPU slices | 2 | 3 |
| GPU consumers fit | 3 (E2B+E4B share one slice) | 3 (1-per-node clean) |
| RW HA (compute hostname anti-affinity) | ✓ | ✓ |
| 1-node failure radius | larger (5 components per node) | smaller (3-4 per node) |
| Per-slice VRAM | 16 GB (more KV-cache room for E4B) | 12 GB |
| Operational complexity | dual-container GPU pod | per-pod 1:1 |

The 2-node plan is **~$98/mo cheaper**, has **larger per-slice VRAM**
(allowing E4B at ctx 8192 with comfortable KV headroom), but bears
**larger per-node failure radius** and **GPU-sharing complexity**.
We accept these because the keiei-llm dual-pod pattern is well-defined
(both processes share `CUDA_VISIBLE_DEVICES=0` inside one pod
sandbox; LiteLLM upstream just points at two ports on the same
Service) and because RW operates degraded-but-correct on a single
compute pod during the recovery window.

## 3. Per-node placement

| Node | RW workloads | GPU consumer | Other | Budget (request) |
|---|---|---|---|---|
| **A** (8c / 40Gi / 16GB VRAM) | compute-1 (1c / 20Gi) + meta (0.5c / 4Gi) + compactor (0.25c / 2Gi) | **ComfyUI** (2c / 4Gi / 1× nvidia.com/gpu) | Mitama / cohort (1c / 3Gi) + system (0.5c / 2Gi) | 5.25c / 35Gi / 16GB |
| **B** (8c / 40Gi / 16GB VRAM) | compute-2 (1c / 20Gi) + metastore PG (0.5c / 2Gi) + frontend (0.2c / 1Gi) | **keiei-llm dual** (E2B + E4B in single pod, 6c / 12Gi / 1× nvidia.com/gpu) | LiteLLM (0.2c / 1Gi) + Mitama (0.5c / 2Gi) + system (0.5c / 2Gi) | 8.9c / 38Gi / 9.6GB used |

Node B is at **~95% vCPU request** and **~95% RAM request** — minimal
headroom. PriorityClass ordering (§5 rule 4) means kubelet evicts
keiei-llm E4B before any RW component under memory pressure. If
sustained memory pressure is observed in production, demote E4B to a
PVC-backed scratch model (load-on-demand) and free its 8 GiB request.

VRAM accounting (Node B GPU slice, 16 GB):

| Container | Weights | KV cache (ctx 8192) | Subtotal |
|---|---:|---:|---:|
| llama-server-e2b (gemma-4-E2B-it Q4_K_M) | ~3.0 GB | ~0.6 GB | ~3.6 GB |
| llama-server-e4b (gemma-4-E4B-it Q4_K_M) | ~5.0 GB | ~1.0 GB | ~6.0 GB |
| **Total resident** | | | **~9.6 GB / 16 GB** |
| Reserved headroom (sysfs / fragmentation / KV growth) | | | ~6.4 GB |

## 4. Cost

| | $/mo |
|---|---:|
| 2 × vcg-a40-8c-40g-16vram (compute) | **$839.50** |
| B2 RW Hummock state | $46 |
| Vultr block storage — RW metastore PG (50 GiB) | ~$5 |
| Cloudflare Tunnel (existing, free) | $0 |
| ComfyUI / keiei-llm GGUFs / fetch caches (live on 740 GiB local NVMe per node) | $0 |
| **Consolidated total** | **~$890** |

vs current ~$1,261 (2 × vhf-16c-58gb $640 + RunPod 6000 Ada 24×7
$571.50 + storage $50): **−$371 / mo (−29%)**.

Honest caveat: per `50-infra/runpod/comfyui-l40s/README.md`, the
RunPod ComfyUI baseline could be cut to ~$26/mo by switching to
on-demand mode (~40 hours / month). If that frugal mode were
re-enabled the current effective cost drops to ~$717/mo and this
consolidation becomes ~+$170/mo more expensive but unifies the
operational surface and unlocks 24×7 ComfyUI + E4B GPU inference.

## 5. Hard rules

1. **GPU exclusivity at the pod boundary.** Vultr A40 1/3 instances
   expose exactly **1 `nvidia.com/gpu`** per node. The keiei-llm dual
   pod must request `nvidia.com/gpu: 1` on the pod (not per-container)
   and rely on the device plugin's pod-sandbox semantics to make the
   GPU visible to both containers via `NVIDIA_VISIBLE_DEVICES=all`
   (auto-set by the device plugin). Only one such GPU pod per node.
2. **RW compute anti-affinity preserved.** The 2 RW compute pods MUST
   land on different nodes (existing
   `app.kubernetes.io/component=compute` hostname anti-affinity in
   `50-infra/vultr/kotoba/values.yaml`). With this 2-node pool,
   anti-affinity is satisfied iff each compute pod claims its own
   node. Surviving 1-node failure operates in **single-compute-pod
   degraded mode** until the pool is restored to 2 nodes.
3. **No RW DDL during the migration.** ADR-0094 Kotoba/Datomic Smooth
   Scaling Gate. Heavy DDL / scale-down / bulk ingest forbidden
   between Phase 1 (RW restored on new pool) and Phase 5 (old pool
   drained). Pre-flight `rw-health-gate.sh` MUST report healthy at
   the start and end of each phase.
4. **PriorityClass ordering.**
   - `keiei-cxo-data` (RW compute / meta / metastore PG): priority **1000**
   - `keiei-cxo-default` (Mitama / cohort / langgraph / LiteLLM / E2B): priority **500**
   - `keiei-cxo-best-effort` (E4B / ComfyUI): priority **100**
   Under Node B memory pressure, kubelet evicts E4B first, then E2B,
   then Mitama. RW data path is never preempted by GPU consumers.
5. **No pod-level vGPU sharing across pods.** If a future workload
   wants the same GPU as the keiei-llm pod, it co-locates as a 3rd
   container in that pod, not as a separate pod. Two pods both
   requesting `nvidia.com/gpu: 1` on the same node is impossible
   (device plugin will not double-allocate).
6. **VRAM budget conservatism.** ctx_size is 8192 by default; raising
   to 16384 doubles KV cache and busts the 16 GB slice. Any ctx
   change requires re-checking §3 VRAM accounting and updating the
   chart's `.Values.models[].contextSize`.
7. **Single bearer rotation path preserved.** `keiei-llm-auth` Secret
   continues triple duty (each llama-server `--api-key-file`, LiteLLM
   master_key, LiteLLM `UPSTREAM_BEARER`). GPU mode does not change
   the auth shape.
8. **RW metastore PG MUST live on Longhorn.** `storageClassName: longhorn`
   with `numberOfReplicas: 2`. Direct Vultr block-storage attachment
   for `metastore-pg-data` PVC is forbidden in this 2-node topology
   because single-attach reattach time (~5–10 min) violates the
   degraded-mode budget when Node B fails. Hummock state stays on B2
   (unchanged from ADR-0048).

## 6. Image + flags

| Workload | Image | Key flags |
|---|---|---|
| keiei-llm-e2b (in dual pod, port 8080) | `ghcr.io/ggml-org/llama.cpp:server-cuda` | `--model /model/gemma-4-E2B-it-Q4_K_M.gguf --n-gpu-layers 99 --ctx-size 8192 --threads 2 --port 8080 --api-key-file /etc/keiei-llm/auth/bearer` |
| keiei-llm-e4b (in dual pod, port 8081) | same | `--model /model/gemma-4-E4B-it-Q4_K_M.gguf --n-gpu-layers 99 --ctx-size 8192 --threads 2 --port 8081 --api-key-file /etc/keiei-llm/auth/bearer` |
| LiteLLM (separate pod, CPU) | `ghcr.io/berriai/litellm:main-stable` | unchanged; model_list points at `keiei-llm-gpu:8080` and `:8081` |
| ComfyUI (separate pod, GPU node A) | `ghcr.io/etzhayyim/comfyui:cu124` (build mirror of RunPod image) | SDXL 1024×1024, fp16, 1× `nvidia.com/gpu` |

`--threads 2` because GPU does the work and CPU contention with RW
compute on the same node is the real risk on 8-vCPU hardware.

## 6a. Vultr managed applications (VKE add-ons, iter132 addendum)

The consolidated cluster enables a curated set of Vultr managed apps:

| App | Version | Status | Why |
|---|---|---|---|
| **NVIDIA GPU Operator** | 26.3.0 | **install (required)** | driver + device plugin + DCGM + NFD + container toolkit. Without this `nvidia.com/gpu: 1` never appears on A40 nodes. |
| **kube-state-metrics** | 5.25.1 | install (recommended) | Pod restart / OOM / unschedulable / PVC binding metrics. Picked up by `prometheus_cross_namespace_scrape = true`. |
| **Longhorn** | 1.7.1 | **install (recommended)** | **Mitigates 2-node design's biggest risk** — RW metastore PG PVC orphaning on Node B failure. Longhorn 2-replica failover ~30 s vs Vultr block-storage single-attach ~5–10 min. Cost: ~0.5 vCPU / 2 GiB / node. |
| Cert-Manager | 1.16.2 | install (cheap, reserve) | Held for future in-cluster ingress with TLS. |
| Cert-Manager Vultr Webhook | 0.4.1 | skip | Cloudflare DNS is SSoT. |
| AMD GPU-Operator / AMD Network Operator | — | skip | Wrong vendor. |
| NVIDIA Network Operator | 24.1.0 | skip | InfiniBand / RDMA only relevant for multi-node GPU training. |
| Exascaler CSI | 2.7.0 | skip | HPC parallel FS, over-engineered. |
| Rook Ceph | 1.15.3 | skip | 2-node Ceph quorum is fragile; Longhorn lighter. |

§3 placement was iter131-tight on Node B RAM. Adding Longhorn (~0.5c
/ 2Gi per node) requires trimming E4B from 4c/8Gi to **3c/10Gi**
(GPU does the work, `--threads 2`) and shifting bulk Mitama workers
onto Node A. The updated total is `Node A: 6.25c / 37Gi`, `Node B:
6.4c / 40Gi`. Node B remains 100% RAM-allocated; PriorityClass
ordering (§5 rule 4) holds.

The metastore PG PVC migrates from Vultr block-storage CSI
(`storageClassName: vultr-block-storage`) to Longhorn
(`storageClassName: longhorn`, replicas=2). Migration uses
`pg_dump | pg_restore` per RUNBOOK Phase 1c — a clean cutover, not a
volume-format conversion.

## 7. Migration phases (see RUNBOOK)

| Phase | Goal | Reversible? | Estimated downtime |
|---|---|---|---:|
| **0** | Provision 2-node `vcg-a40-8c-40g-16vram` pool, label `pool=keiei-a40`. **Install Vultr managed apps**: NVIDIA GPU Operator + kube-state-metrics + Longhorn + Cert-Manager (UI: Compute → Kubernetes → Applications). Verify `nvidia.com/gpu` resource on each node (`kubectl describe node | grep nvidia.com/gpu` → `1`). Verify Longhorn UI healthy with both nodes registered. | yes | 0 |
| **1** | Add new pool to RW Helm `nodeSelector` tolerance; cordon old vhf nodes; let RW reschedule onto new pool (compute pods migrate one at a time, anti-affinity-preserving) | yes (drop tolerance, re-cordon) | ~5 min RW degraded per compute pod move |
| **2** | Helm upgrade keiei-llm-pool with `gpu.enabled=true`; deploy dual pod on Node B + LiteLLM on either node | yes (helm rollback) | 0 (additive — old CPU pods still serve until cutover) |
| **3** | Build/push `ghcr.io/etzhayyim/comfyui:cu124`, deploy ComfyUI Helm chart on Node A, copy SDXL checkpoints from RunPod NV → local NVMe via rsync | yes (RunPod still alive) | 0 (additive) |
| **4** | Cut `comfyui.etzhayyim.com` Worker `UPSTREAM_URL` env from RunPod → Vultr; flip keiei daemon plist `etzhayyim_LLM_URL` to keiei-llm.etzhayyim.com (or keep port-forward until CF Worker exclusion) | yes (Worker var flip back) | <1 min |
| **5** | Drain + delete `vhf-16c-58gb` pool, terminate RunPod `comfyui-etzhayyim-unified`, archive RunPod ansible role | partially (cluster recreate from B2 + RunPod re-spin needed for full revert) | 0 if Phase 4 healthy |

Detailed step-by-step in
`50-infra/vultr/keiei-llm-pool/MIGRATION-RUNBOOK-A40-2NODE.md`.

## 8. Anti-goals

- **Not** sharing 1 GPU between separate pods. Vultr exposes one
  device per VM; only intra-pod container sharing is supported.
- **Not** reducing RW compute resources to fit smaller nodes. RW's
  `requests: 1000m / 20Gi` floor is tied to the streaming MV memory
  guardrails (`30-graph/graph-schema/CLAUDE.md §MV Memory Safety`).
- **Not** moving non-GPU workloads (Mitama / cohort / langgraph) to
  RunPod. Vultr VKE remains the home for stateful + control-plane
  workloads.
- **Not** running multiple GPU workloads per node via vGPU
  time-slicing or MPS. Vultr's vGPU profile does not support MIG.
- **Not** abandoning the RTX 6000 Ada path for multimodal CXO
  review. When CXO graphs gain vision/PDF understanding, the GPU pool
  upgrades to a `vcg-a40-12c-60g-24vram` (1/2 A40) per node or returns
  to RunPod 6000 Ada — a separate ADR amendment.

## 9. Rollback

Each phase has its own rollback (RUNBOOK §Rollback). Aggregate worst
case: re-create the 2 × `vhf-16c-58gb` pool, restore RW from the most
recent `rw-meta-backup` CronJob snapshot
(`b2://etzhayyim-nats/.../kotoba/state/backup/{id}.snapshot`),
re-spin the RunPod `comfyui-etzhayyim-unified` pod from the existing
template, point `comfyui.etzhayyim.com` Worker `UPSTREAM_URL` back to
RunPod. Recovery window: ~45 min if hourly meta snapshot is current,
longer if Hummock SST replay is needed.

## 10. Cross-references

- ADR-0094 — Kotoba/Datomic smooth scaling gate
- ADR-0048 — RW Vultr + B2 cutover (storage layer unaffected)
- ADR-2604231328 — RunPod ComfyUI (this ADR amends the §Why RunPod table)
- ADR-2605102100 — keiei-llm CPU inference (this ADR completes its §6 Phase 4)
- 50-infra/vultr/kotoba/scaling-contract.yaml — pre-flight gate
- 50-infra/vultr/keiei-llm-pool/MIGRATION-RUNBOOK-A40-2NODE.md — operator playbook
- 50-infra/vultr/keiei-llm-pool/values.yaml — `.Values.gpu.enabled` toggle
