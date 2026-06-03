---
id: adr-2604231328-animeka-bpmn-l40s-pipeline
title: "ADR-2604231328: animeka 12-stage BPMN + RunPod L40S ComfyUI pipeline"
status: active
doc_type: adr
topic: anime-production-pipeline
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - animeka.etzhayyim.com 12-stage production orchestration
  - LLM / image / video / audio primitive routing for anime production
  - BPMN process identity for each of the 12 stages
related:
  - adr-0004-write-only-derived-architecture
  - adr-0081-worker-direct-hyperdrive-persistence
  - adr-0050-animeka-comfyui-pattern1-vultr-l40s
  - adr-0056-bpmn-as-actor
supersedes: []
superseded_by: []
amends:
  - adr-0050-animeka-comfyui-pattern1-vultr-l40s
---

# Context

ADR-0050 originally provisioned animeka onto a single Vultr L40S 48GB ComfyUI backend
(image + video + audio + Qwen 2.5 7B mid-tier LLM) and explicitly declared
"no Zeebe — animeka has its own agent loop". Five days later ADR-0056
promoted **BPMN-as-actor** (Zeebe 8.6 + 7 generic primitives + dispatcher)
to production for all T1/T2 actors.

Running animeka on a bespoke orchestrator while every other T1/T2 actor
uses Zeebe means animeka pays the per-actor cost that ADR-0056 exists
to eliminate: bespoke LLM plumbing, no uniform observability, no shared
retry/timer primitives. Empirically, the ad-hoc path also went offline
2026-04-22 when the Linode GPU was retired — `etzhayyim-project-llm`
references were deleted but no fallback wiring was added, leaving the
12-stage pipeline in ~15% completion (inbetweener interpolate only).

The question: should animeka adopt the same BPMN-as-actor surface as the
other 14 deployed actors, using the ComfyUI backend that ADR-0050
already provisioned for image / video / audio, and Claude / Qwen / Murakumo
for the three LLM tiers?

# Decision

Adopt BPMN-as-actor for all 12 animeka production stages. Amend ADR-0050
to remove the "no Zeebe" clause — animeka's orchestration layer is now
ADR-0056; animeka's compute backend remains ADR-0050 Pattern 1.

## 1. Architectural invariants

| Layer | SSoT | Applies |
|---|---|---|
| Compute — image / video / audio | `comfyui.etzhayyim.com` CF Worker → **RunPod Serverless Endpoint** (`v9si0sflsm0gh0`, `runpod/worker-comfyui:latest`, RTX 4090 EUR-IS-1, scale-to-zero) attached to Network Volume `43k3uq9ldn` with Animagine XL cached; Pod Pattern 1 retained as hot-replay fallback | ADR-0050 Pattern 1 + 2026-04-23/24 addenda below |
| Compute — LLM | 3-tier: fast=Murakumo / mid=L40S Qwen 2.5 7B / deep=Claude Sonnet 4.5 | ADR-0050 §3 |
| Orchestration | Zeebe 8.6 LTS on mitama-udf K8s + bpmn-dispatcher | ADR-0056 |
| Storage | Hyperdrive + Kysely → RisingWave `vertex_animeka_*` | ADR-0081 |
| Social derive | `magatama.jsonld` `derive` rule (handler = single domain write, social fires via derive) | ADR-0004 |
| Stage handoff | `magatama.jsonld` `derive` rule emits XRPC invoke of the next stage's NSID at commit time | this ADR |
| Auth | Zeebe worker Secret holds `COMFYUI_API_KEY` (sk_live_*, scope `comfyui:generate`) + `ANTHROPIC_API_KEY` + `MURAKUMO_URL` | ADR-0022 / ADR-0023 |

## 2. One new primitive

ADR-0056 publishes seven generic primitives. Animeka needs exactly one more:

| Primitive | Signature | Behavior |
|---|---|---|
| `generic.comfyui.call` | `(route, body, outputFormat, timeoutSec)` → `{status, blobCid, meta, latencyMs}` | POSTs JSON to `comfyui.etzhayyim.com{route}` (`/v1/images/generations`, `/v1/images/edits`, `/v1/videos/generations`, `/v1/audio/speech`, `/v1/audio/music`, `/v1/chat/completions`). Binary responses are SHA-256 hashed + uploaded to `blobs/anonymous/{sha256}` via the PDS `uploadBlob` path (ADR-0081 blob convention). JSON responses are returned verbatim. Auth header `Authorization: Bearer ${COMFYUI_API_KEY}` injected by the worker, not BPMN-authored. |

### Video backend catalog (`/v1/videos/generations`)

The comfyui.etzhayyim.com upstream on the L40S exposes the following video models via the `model` body field. Default is **Seedance 2** as of 2026-04-23 — ByteDance's Seedance 2 gives the best character-identity retention across long interpolations and the most faithful camera-move rendering for the compositing step.

| Model id | Source | Use | Notes |
|---|---|---|---|
| `seedance2` | ByteDance Seedance 2 (open checkpoint) | **i2v default** for inbetween + composite | Strong identity lock, smooth 24fps, ~2-3 min per 2s clip on L40S |
| `wan5b` | WAN 5B (per commit `e217cc72f06`) | i2v fallback | Already vendored; tends to drift on >16-frame interpolations |
| `animatediff` | AnimateDiff SDXL motion module v3 | Short loops (2-4 s) | Lower VRAM, faster than seedance2 for < 2 s clips |
| `svd` | Stable Video Diffusion 1.1 XT | Narrow use (25-frame 1024×576) | Retained for experiment; identity drift on anime style |

Callers override the default via the `videoBackend` input on `generateInbetween` / `renderComposite`. The worker passes `model` unchanged to ComfyUI; the upstream workflow on L40S dispatches to the correct ComfyUI node graph per model id.

No other new primitive. `generic.llm.chat` already accepts `tier`; routing is internal to `pymagatama.llm.call_tier`. Timeouts: ComfyUI video calls can run 3-5 min; the worker uses `timeout_ms = 600_000` for `generic.comfyui.call` specifically.

## 3. 12 stages → 12 BPMN processes

One BPMN file per stage. Filenames: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/animeka/{stage}.bpmn`. Each stage registers as one `vertex_bpmn_process_def` row + one `vertex_bpmn_lexicon_binding` row (per ADR-0056 canonical vertex_id scheme).

| # | NSID | Primitive chain | HITL gate |
|---|---|---|---|
| 1 | `com.etzhayyim.animeka.generateScript` | llm.chat(deep) → llm.json → db.insert (script + N scene rows) → pds.dispatch (social) → audit.emit | — |
| 2 | `com.etzhayyim.animeka.breakdownScene` | db.select → llm.json(mid) → db.insert × N cut rows → audit.emit | — |
| 3 | `com.etzhayyim.animeka.generateStoryboard` | db.select → llm.chat(deep) → comfyui.call × 3 (Animagine 512²) → db.insert × 3 storyboard (status=draft) → audit.emit | **✓** pick 1 of 3 |
| 4 | `com.etzhayyim.animeka.generateLayout` | db.select → llm.json → comfyui.call (ControlNet-depth 1024²) → db.insert layout → audit.emit | **✓** approve |
| 5 | `com.etzhayyim.animeka.generateKeyframes` | db.select → llm.json (key-pose plan) → comfyui.call (ControlNet-pose + IPAdapter char-ref) × N → db.insert × N keyframe → audit.emit | **✓** approve |
| 6 | `com.etzhayyim.animeka.generateInbetween` | llm.json (easing plan) → comfyui.call (Seedance 2 i2v default; WAN 5B / AnimateDiff / SVD via `videoBackend`) → db.insert × N inbetween → audit.emit | — |
| 7 | `com.etzhayyim.animeka.designColorModel` | llm.chat(deep) → comfyui.call → db.insert colorModel → audit.emit | — (once per character) |
| 8 | `com.etzhayyim.animeka.autoTrace` | comfyui.call (lineart-controlnet + palette-cond inpaint) → db.insert colorTrace → audit.emit | — |
| 9 | `com.etzhayyim.animeka.generateBackground` | db.select → llm.chat → comfyui.call (FLUX or Animagine 1920×1080) → db.insert background → audit.emit | — |
| 10 | `com.etzhayyim.animeka.renderComposite` | llm.json (FX stack) → comfyui.call (Seedance 2 default for camera moves; WAN 5B / AnimateDiff via `videoBackend`) → db.insert composite → audit.emit | — |
| 11 | `com.etzhayyim.animeka.generateSoundCue` | fanout: speech (SBV2) / sfx (StableAudio) / bgm (MusicGen) via comfyui.call × N → db.insert × N soundCue → audit.emit | — |
| 12 | `com.etzhayyim.animeka.publishEpisode` | db.select all cuts → comfyui.call (final ffmpeg stitch) → db.insert master → pds.dispatch (PV social post) → audit.emit | **✓** final review |

HITL is expressed as a human update to the upstream record's status (e.g. `storyboard.status=approved`). The next stage's derive rule (§4) watches for that commit.

## 4. Stage handoff via `magatama.jsonld` derive rules

Animeka's `derive.rules[]` is rewritten to 11 entries. Each rule invokes the next stage's XRPC NSID on commit, so the `/cuts` UI never needs to chain stages in JavaScript.

| Upstream commit | Invokes |
|---|---|
| `scene.create` (status=ready) | `animeka.breakdownScene` |
| `cut.create` | `animeka.generateStoryboard` |
| `storyboard.update` (status=approved) | `animeka.generateLayout` |
| `layout.update` (status=approved) | `animeka.generateKeyframes` + `animeka.generateBackground` (parallel) |
| `keyframe.pair_committed` | `animeka.generateInbetween` |
| `colorModel.update` (status=ready) | `animeka.autoTrace` (fanout over keyframes) |
| `colorTrace.ready ∧ background.ready` | `animeka.renderComposite` |
| `cut.update` (status=approved) | `animeka.generateSoundCue` |
| `episode.update` (status=ready) | `animeka.publishEpisode` |

## 5. HITL gate policy

Gates live at stages 3 (storyboard candidate select), 4 (layout approve), 5 (keyframe approve), 12 (final review). All other stages are fully automated. Directorial review authority is preserved at the creative-decision points (shot/layout/acting/cut); mechanical stages (inbetween/finish/bg/composite/sound) run without approval.

## 6. Pattern 1 serial constraint

MVP accepts L40S serial execution. Rough budget: 1 episode ≈ 60 cuts × (~30s image + ~3 min video + ~10s audio) ≈ 4 L40S-hours. If sustained daily throughput exceeds 2-3 episodes the Pattern 2 upgrade (A100 80GB + L40S, ADR-0050 §Alternatives) is already drafted; retarget is a single `UPSTREAM_URL` change per route.

## 6b. Compute provider (2026-04-23 addendum — supersedes Vultr-only §1)

Vultr L40S on-demand ($1.671/hr) and 36mo prepaid ($0.848/hr = $611/mo) are both uneconomic for our 40-pod-hour/month target (10 episodes × 4 h). Price survey 2026-04-23:

| Provider | SKU | $/hr | 40 h/mo | Notes |
|---|---|---|---|---|
| Vultr Cloud GPU on-demand | L40S 48GB | $1.671 | $67 | current scaffold |
| Vultr Cloud GPU 36mo prepaid | L40S 48GB | $0.848 | $611 (always on only) | 3-year lock |
| **RunPod Community Cloud** | **L40S 48GB** | **$0.86** | **$34** ✅ | ✨ **primary** |
| RunPod Secure Cloud | L40S 48GB | $0.89 | $36 | SLA fallback |
| Hyperstack | L40S 48GB | $0.85 | $34 | Terraform provider, EU |
| Vast.ai (spot) | L40S 48GB | $0.40–0.70 | $16–28 | Docker, flaky availability |
| Lambda Labs | L40S 48GB | $1.10 | $44 | enterprise, A100/H100 focus |

**Decision**: Primary = **RunPod Community L40S** via GraphQL API + Pattern 1 Lite up/down. 2026-05-09 update: Vultr ComfyUI fallback was removed because the Vultr estate no longer has GPU nodes; the former `50-infra/vultr/comfyui-l40s/` module and its detached 100 GB block volume were deleted.

**Migration**: `50-infra/runpod/comfyui-l40s/scripts/{up,down,status}.sh` uses the RunPod GraphQL API directly (no official Terraform provider as of 2026-04). The Ansible playbook at `60-apps/etzhayyim-project-comfyui/ansible/` runs against the RunPod pod via `$ANSIBLE_HOST`.

**Cost delta**: $67/mo (Vultr on-demand Pattern 1 Lite) → **$34/mo (RunPod Community + same Lite cycle)** = **49% reduction** while keeping full 48 GB VRAM and all of ADR-0050 §5 model catalog.

**Network Volume**: RunPod persists models on a 100 GB Network Volume (~$0.07/GB/mo = **$7/mo**) that survives pod teardown. First `up.sh` run populates it; subsequent warm starts skip model download.

## 6c. Serverless migration (2026-04-24 addendum — Phase Δ3, **superseded by §6d same day**)

> **Status (2026-04-24T05:25Z onward)**: Superseded by §6d. The
> RunPod Serverless Endpoint `v9si0sflsm0gh0` documented below was
> **destroyed** after cold-start instability: `IN_QUEUE` states
> persisted 40+ minutes on `runpod/worker-comfyui` image pulls,
> flashboot did not kick in consistently within the 30 s idle
> window for serial BPMN stages, and animeka production work was
> blocked. Reverted to Pattern 2 (24/7 pod `n911oglid03v5n` with
> launchd watchdog) + co-located text-gen on the same pod. All
> downstream callers (`comfyui.etzhayyim.com` CF Worker, pyzeebe
> `generic.comfyui.call`) no longer target `api.runpod.ai/v2/...`
> — they hit `n911oglid03v5n-8000.proxy.runpod.net` via the pod
> adapter. Serverless template + endpoint IDs below are retained
> for historical reference only.

The pod-based Pattern 1 Lite proved workable ($34/mo for 40 h/mo RunPod Community L40S) but three live-ops findings pushed us to RunPod Serverless instead:

1. **L40S Community supply is volatile** — 4 DCs returned `SUPPLY_CONSTRAINT` across the 2026-04-23 session (US-CA-2, AP-JP-1, OC-AU-1, EUR-IS-1). A40 Secure (\$0.47/hr) was our fallback but has no FP8 native (forces Seedance 2 BF16 = 2× slower).
2. **The GPU pool RunPod assigns is not the base SKU we bid on** — RTX 4090 Secure landed on a 16 vCPU / 62 GiB premium box at **\$0.69/hr (\$508/mo 24/7)** rather than the base \$0.39/hr advertised. `MIN_VCPU` / `MIN_MEMORY_GB` tune the floor but RunPod picks the SKU from its availability pool and we can't cap the ceiling.
3. **Our workloads are bursty** — animeka is mostly weekend / ad-hoc generation, ~40 h active/mo. The breakeven vs Serverless (scale-to-zero, \$0.00031/s L40S) is ~450 h/mo = 63 % uptime. Below that, Serverless is cheaper *and* resilient to supply churn.

**Adopted**: RunPod Serverless Endpoint as primary ComfyUI backend.

| | Pattern 1 Lite (Pod) | Pattern 2 Watchdog (24/7 Pod) | **Serverless (chosen)** |
|---|---|---|---|
| \$/month (40 h active) | \$34 + \$7 volume | \$508 + \$7 volume | **\$15 + \$7 volume = \$22** |
| \$/month (100 h active) | \$85 + \$7 | \$508 + \$7 | \$112 + \$7 = \$119 |
| Cold start | 5–10 min (Ansible + model DL) | 0 (always on) | 60–180 s first call (worker image pull); 5–15 s flashboot after |
| Availability | subject to supply constraints | requires 24/7 slot | **zero idle cost, spin on demand** |
| GPU variance | host SKU assigned at up time | same | RunPod picks any matching GPU per job |

**Deployed state (2026-04-24)**:
- Template `ww4y20b2s7` (image `runpod/worker-comfyui:latest`, category NVIDIA, 20 GB container disk)
- Endpoint `v9si0sflsm0gh0` (workersMin=0, workersMax=1, idleTimeout=30 s, flashboot=true, RTX 4090, EUR-IS-1)
- Network Volume `43k3uq9ldn` attached at `/runpod-volume` (Animagine XL 4.0 6.94 GB cached from Phase Δ2)
- Endpoint URL: `https://api.runpod.ai/v2/v9si0sflsm0gh0/{runsync,run,status/<id>,health}`

**Adapter fan-out**:
- `comfyui.etzhayyim.com` CF Worker (`50-infra/cloudflare/workers/comfyui/src/index.ts`): `/v1/images/generations` translates OpenAI → ComfyUI workflow → Serverless `/runsync`. Returns `{data:[{b64_json}]}`. Retains OpenAI-compat for LiteLLM / openai-python.
- pyzeebe `generic.comfyui.call` (`20-actors/magatama/py/src/pymagatama/zeebe_worker_main.py`): detects Serverless mode when `COMFYUI_URL` contains `api.runpod.ai`, runs the same workflow builder + `/runsync` + `/status` poll + base64 decode + PDS uploadBlob, returns `{blobCid, meta, latencyMs, executionTimeMs, delayTimeMs}`.

**Cost projection (anime-production burst)**:
- 1 episode ≈ 60 cuts × (~30 s image + ~3 min video + ~10 s audio) = 4 L40S-hours compute
- Serverless L40S \$0.00031/s × 3600 × 4 = \$4.46 / episode + \$7/mo volume
- 10 episodes/mo = **\$52/mo**, 3 eps/mo = **\$20/mo**

**Known ergonomic trade-offs**:
- First request per worker = cold start 60–180 s (`runpod/worker-comfyui` image is ~8 GB).
- BPMN stages that run serially through the pipeline (e.g. generateStoryboard → generateLayout → generateKeyframe × N) incur cold start only once if requests are within the 30 s idle window. Beyond that, workers recycle.
- Multi-character LoRA fine-tunes (not yet in scope) would need baked into the checkpoint tree on the Network Volume.

**Supporting scripts**:
- `50-infra/runpod/comfyui-l40s/scripts/serverless.sh {create|info|test|destroy}` — full lifecycle via REST API.
- State persisted to `~/.etzhayyim/runpod-watchdog/serverless.env` (TEMPLATE_ID + ENDPOINT_ID).

## 6d. Text-gen LLM colocation on RunPod (2026-04-24 addendum — Phase Δ4)

Post-Serverless-migration field testing revealed a second blocker at the
text-gen layer. BPMN `generic.llm.chat` + `generic.llm.json` both called
`llm.call_tier(...)` from `pymagatama.llm`, which pointed at Vultr
Serverless Inference (`api.vultrinference.com/v1/chat/completions`).
Three issues, in order of severity:

1. `tier="deep"` was referenced by generateScript / generateStoryboard
   / generateBackground XML but absent from `TIER_MODELS`. `resolve_model`
   raised `LlmError("unknown tier: 'deep'")`; the handler caught it and
   returned `{"error": ...}` — the output mapping `source="=content"`
   then produced `draftText: null` silently. The BPMN process continued
   to audit + insert with empty strings, emitting a `vertex_bpmn_audit`
   row that looked successful from above.
2. Vultr's aliases for its highest-quality models (`Kimi-K2.6`,
   `Qwen3.5-397B-A17B-FP8`) returned `choices[0].message.content = null`
   on long-form Japanese prose; the only usable text came from
   `Devstral-2-123B-Instruct-2512`, which Vultr silently aliases to
   `MiniMax-M2.7` and wraps in `<think>…</think>` reasoning — eating
   the 3k-token budget before emitting script text.
3. `api.vultrinference.com` has a measured 30s+ hang-then-recover
   pattern under sustained load (logged empirically 2026-04-22 in
   `pymagatama.llm` header comment).

**Adopted**: co-locate text-gen on the existing RunPod L40S pod via
Ollama. Qwen2.5-7B-Instruct-Q5_K_M (~5.4 GiB VRAM) loads alongside
ComfyUI's ~7 GiB, leaving ~11 GiB headroom on the RTX 4090. Ollama
binds to port 8001 (tmux-detached, survives SSH disconnect), reachable
externally at `https://n911oglid03v5n-8001.proxy.runpod.net/v1/chat/completions`.

`pymagatama.llm` gains a `TIER_ENDPOINT_OVERRIDES` table keyed by tier
(default: `deep` / `mid` / `classifier` / `structured` / `fast`) that
rewires `call_tier` per-tier without touching callers. The override
also bumps per-attempt timeout to 120s (vs default 20s) to cover
RunPod cold-load (60-90s on first request after scale-from-zero).

Two subtle landmines were addressed in the same commit:

- `proxy.runpod.net` sits behind Cloudflare and returns `error code:
  1010` to python/urllib's default UA. A standard Chrome desktop UA
  + `Accept: application/json` keeps requests acceptable across all
  endpoints (benign for Vultr, required for RunPod).
- The animeka BPMN XMLs referenced `org_id` / `user_id` / `actor_id`
  columns on `vertex_animeka` that were not in the deployed schema.
  `generic.db.insert` failed with `Bind error: Column org_id not found`,
  returned `{"error": ..., "inserted": 0}`; the output mapping
  `=inserted` only captured `0`, so the surrounding process continued
  and emitted its audit row. Stripped the three keys from all 13
  animeka BPMNs and re-seeded via the dispatcher F5 watcher
  (`UPDATE vertex_bpmn_process_def SET "xml"=…, deployed_at=NULL`).
  Note: `xml` is a RisingWave reserved keyword — quoted identifier
  required in the UPDATE statement.

**End-to-end verified 2026-04-24T06:39Z**:

```
POST https://dispatcher.etzhayyim.com/xrpc/com.etzhayyim.animeka.generateScript
{ episodeId, episodeTitle, synopsis, targetSceneCount: 8 }

→ ok=true, instanceKey=…, latencyMs=12969
  variables.draftModel     = "qwen2.5:7b-instruct-q5_K_M"
  variables.draftTextLen   = 696  (8-scene Japanese screenplay)
  variables.structured     = { scenes: [ 8 entries {sceneNum,
                                       location, timeOfDay, action,
                                       dialogue, charactersAppearing[]}
                                     ] }
  variables.inserted       = 1    (vertex_animeka row persisted)
  variables.emitted        = true (audit row written)

SELECT * FROM vertex_animeka
WHERE vertex_id = 'at://did:web:animeka.etzhayyim.com/
                    com.etzhayyim.animeka.script/ep-1776928323916-1-v1'
→ 1 row, title "春、始発駅で待つ彼女", stage "script", desc_len 696
```

**Cost impact**: near-zero. RunPod L40S pod is already running 24/7
(Pattern 2 watchdog, ADR §6c addendum — we opted against Serverless
after cold-start instability). Adding Ollama consumes ~5.4 GiB of
the pre-paid 24 GiB VRAM and ~1 vCPU — $0 incremental.

**Known quality ceilings**:
- Qwen2.5-7B occasionally slips to Chinese on structured JSON
  extraction (observed scenes[].location = "无人车站" when the draft
  was in Japanese). Mitigation for Phase Δ4.1: append explicit
  "OUTPUT IN JAPANESE ONLY" to the Task_Structure system prompt in
  the 13 animeka BPMN XMLs. Not blocking.
- 120s timeout covers first-call cold-load but not GPU contention
  under burst load (RunPod ComfyUI run while Ollama inference in
  flight). First tests show ComfyUI txt2img at 832×1216 shares the
  GPU cleanly with Ollama inference; monitor under multi-stage
  concurrent runs.

**`generic.pds.dispatch` from BPMN** initially appeared to require a
Service Auth JWT mint layer — PDS returned 403 on `app.bsky.feed.post`
from the Vultr k8s worker pod despite the `x-magatama-verified`
internal-trust header. Empirically isolated to the CF edge: the WAF
rejects python/urllib's default User-Agent with an HTML error page
*before* the handler runs (same root cause as the RunPod proxy 1010
we hit on Ollama and the ComfyUI adapter). A standard Chrome UA in
`task_generic_pds_dispatch` + `task_generic_comfyui_call`'s uploadBlob
path clears the WAF; no Service Auth mint needed (internal-trust via
atproto.etzhayyim.com already resolves the caller correctly from the
header).

Second `generic.pds.dispatch` bug: `Task_Announce` was dispatching to
`/xrpc/app.bsky.feed.post` with `{did, text}`. `app.bsky.feed.post` is
a record *type*, not a procedure NSID, so PDS had nothing to route to
(404 → 522 after the WAF was bypassed). Corrected payload shape:

```
type:    com.atproto.repo.createRecord
payload: {
  repo:       workDid,
  collection: "app.bsky.feed.post",
  record:     { "$type": "app.bsky.feed.post", text, createdAt }
}
```

**BPMN publishEpisode live 2026-04-24T07:38Z**:

```
POST dispatcher.etzhayyim.com/xrpc/com.etzhayyim.animeka.publishEpisode
→ announceStatus = 200
  announceBody.uri = at://did:web:animeka.etzhayyim.com/
                    app.bsky.feed.post/3mk7zhexkls24
  body text = "🎬 #1 春、始発駅で待つ彼女 公開
               watch → https://animeka.etzhayyim.com/at/an1m3k4x.etzhayyim.com/
                       com.etzhayyim.animeka.episode/ep-1776928323916-1"
```

Worker-side `cmdPublishEpisode` (`sdk.pds.createRecord`) still works
and is retained as a manual-trigger fallback, but the canonical path
is now dispatcher → BPMN → Zeebe → pds primitive → PDS.

**Image-stage blob persistence (Stage 3 / generateStoryboard, 2026-04-24T07:19Z)**:

```
POST dispatcher.etzhayyim.com/xrpc/com.etzhayyim.animeka.generateStoryboard
  in:  cutId, cutSummary, candidateNum, characters
  out: blobCid      = bafkreidbdd2a…ueguelqx6y (PDS content-addressed)
       blobMeta     = { mimeType: image/png, size: 254482 }
       renderMs     = 4450
       inserted     = 1 (vertex_animeka row)
       emitted      = true (audit row)
  wire: LLM (Qwen 7B on RunPod) 2s → ComfyUI (Animagine XL 4.0 on
        RunPod L40S, 512×512 × 22 steps) 3s → PDS uploadBlob (internal
        trust + browser UA) → Hyperdrive INSERT → Task_Audit emit
```

Row confirmed in `vertex_animeka` with `image_cid =
bafkreidbdd2a…ueguelqx6y` — the UI can render this via
`https://cdn.etzhayyim.com/b/{cid}` once `/cuts` timeline is updated.

BPMN XMLs patched 2026-04-24 to map Task_Render's `blobCid` output
into the DB's stage-appropriate column:

| BPMN                    | column      |
|-------------------------|-------------|
| generateStoryboard      | image_cid   |
| generateLayout          | image_cid   |
| generateKeyframe        | image_cid   |
| designColorModel        | image_cid   |
| autoTraceCut            | image_cid   |
| generateBackground      | bg_cid      |
| renderComposite         | master_cid  |
| generateInbetween       | master_cid  |
| generateSoundCue        | master_cid  |

Worker image: `ghcr.io/etzhayyim/pymagatama:c3d9fc3d830-pds-ua`. Env
on `zeebe-worker` Deployment (namespace `mitama-udf`):

```
COMFYUI_URL=https://n911oglid03v5n-8000.proxy.runpod.net
COMFYUI_API_KEY=pod-inline      # adapter is unauth; primitive requires non-empty
COMFYUI_BLOB_REPO=did:web:an1m3k4x.etzhayyim.com
```

Pod-side adapter: `50-infra/runpod/comfyui-l40s/adapter/openai-comfyui-adapter.py`,
168 LoC stdlib-only, tmux-hosted on port 8000. Ollama Qwen2.5-7B-Q5
serving text on port 8001. Both survive pod restarts via tmux + systemd
hooks.

## 7. Registration mechanics

## 7. Registration mechanics (renumbered from §7)

Exactly 24 INSERTs land in one migration (`20260423160000_animeka_bpmn_registrations.ts`): 12 `vertex_bpmn_process_def` + 12 `vertex_bpmn_lexicon_binding` rows. The F5 watcher in `bpmn-dispatcher` ships the XML to Zeebe within 30 s of commit. After that, `POST https://dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.animeka.<stage>` is live.

## 8. /cuts UI alignment

- Each of the 12 stage cards renders a **Generate** button that XRPC-POSTs the stage NSID for the current cut.
- A 12-segment **progress strip** reads `vertex_repo_commit` where `collection='com.etzhayyim.bpmn.audit'` and actor matches the stage invocation; the strip shows `{queued / running / done / failed}` per stage.
- Preview thumbs read `blob_cid` from the corresponding `vertex_animeka_*` row and render `https://cdn.etzhayyim.com/b/{cid}`.
- The current broken in-Worker chat UI is replaced with a thin XRPC call to `com.etzhayyim.animeka.chat`, which is itself a BPMN process wrapping `generic.llm.chat` (mid tier default, `?tier=deep` for director critique).

## 9. animeka Worker scope

The animeka CF Worker retains:
- XRPC surface for the 12 NSIDs (thin proxies forwarding to `dispatcher.etzhayyim.com`)
- Hono router + Svelte CSR host (`/cuts`, `/episodes/*`, `/works/*`)
- ATRecord writer for CRUD (addCut / updateCutStage / submitRetake / etc.)
- `onCommit` reactive intake for the subscribeRepos collections already registered

It sheds:
- Ad-hoc `generateInbetween` / `autoTrace` / `renderComposite` stub handlers
- In-Worker LLM calls to the retired `etzhayyim-project-llm` endpoint
- `ensureActorDids`-based 12-actor orchestration (retained as a DID registry, but the agent work is owned by BPMN processes, not the actor DID Workers)

# Consequences

## Positive

- /cuts completion jumps from ~15% to ~85% on merge. 11 of 12 stages automate; 4 HITL checkpoints retain directorial authority.
- One orchestration layer for all actors in the platform (animeka, yabai, bot, watch, …). Observability, retry, timer scheduling are uniform.
- Zero new Worker code per stage; zero new pods; one new primitive.
- L40S GPU spend is already sunk (ADR-0050); this ADR activates that capacity for the 11 newly-automated stages.
- Pattern 2 escape hatch remains a `UPSTREAM_URL` flip.

## Negative / risks

- BPMN XML authoring is verbose (12 × ~80 LoC). Mitigation: each file is templated on the 3 reference patterns (simple / XOR / fanout) already in `etzhayyim-root/00-contracts/bpmn/`.
- Dispatcher timeout must be raised for video routes (currently 60 s, the video path needs 600 s). Mitigation: per-task `timeout_ms` override is already supported (`zeebe_worker_main.py:909`); we add an `async` hint in the binding row for the dispatcher to return a process-instance id rather than await.
- L40S is a single point of failure for animeka compute. Mitigation: same as ADR-0050 §Negative — Vultr SLA 99.95% + snapshot schedule; Pattern 2 removes the SPOF.
- IPAdapter multi-character consistency tops out ~80% visual coherence; a LoRA per character would improve this but is out of scope. Logged as a known quality ceiling for Phase 1.
- Dispatcher is a shared bottleneck; an animeka burst could crowd out other actors. Monitor p95 latency; HPA up if necessary.

## Operational

- Migration: `[[migrations]] animeka-bpmn-pipeline-phase1` in `deps.toml`.
- Schema migration: `30-graph/graph-schema/migrations/20260423160000_animeka_bpmn_registrations.ts`.
- Integration test: `70-tools/scripts/test/animeka-pipeline-integration.py` — 1 episode dry-run (stages 1-12 end-to-end, scaled to 1 cut).
- Drift audit: `python 70-tools/scripts/contract/audit-bpmn-actors.py --strict` must be green before and after the registration commit.
- Rollback: DELETE the 12 binding rows (NSIDs go 404) and DELETE the 12 process-def rows (Zeebe unships). `_alive` not used (per root §Persistence).

# Alternatives Considered

| Option | Why rejected |
|---|---|
| Keep animeka's bespoke agent loop, wire a replacement LLM endpoint | Reproduces ADR-0056's rejected per-actor pattern. Animeka would be the only post-0056 actor not on Zeebe. |
| Move only LLM to BPMN, keep image/video/audio local to animeka Worker | Splits the orchestration surface. One retry/timer/observability model is worth more than the small HTTP-hop savings. |
| Wait for Pattern 2 before activating stages 3-12 | Delays 85% of the user-visible completion for a cost optimization. Pattern 1 is sufficient for MVP episode throughput. |
| Inline ComfyUI calls into `generic.http.fetch` | `generic.http.fetch` truncates response bodies at 4 KB (see `zeebe_worker_main.py:690`); it cannot return multi-MB image/video/audio blobs. A dedicated primitive with blob-upload semantics is correct. |
| Use Vultr Serverless Inference instead of Pattern 1 | Catalog lacks Animagine XL / Pony / AnimateDiff / SVD / WAN 5B (ADR-0050 §Alternatives); same rejection stands. |
| Full autonomy (0 HITL gates) | Removes monitor/director authority. Japanese anime production convention preserves approval at shot / layout / acting / final; we keep 4 gates. |

# References

- ADR-0050 animeka + ComfyUI Pattern 1: `90-docs/adr/0050-animeka-comfyui-pattern1-vultr-l40s.md`
- RunPod infra module: `50-infra/runpod/comfyui-l40s/`
- ADR-0056 BPMN-as-actor: `90-docs/adr/0056-bpmn-as-actor.md`
- ADR-0004 Write-only derived: `90-docs/adr/0004-write-only-derived-architecture.md`
- ADR-0081 Worker-direct Hyperdrive: `90-docs/adr/0081-worker-direct-hyperdrive-persistence.md`
- Dispatcher: `20-actors/magatama/py/src/pymagatama/dispatcher_main.py`
- Worker primitive host: `20-actors/magatama/py/src/pymagatama/zeebe_worker_main.py`
- Reference BPMN patterns: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/{llm/chat,yabai/triagePoc,bot/reviewAndPost}.bpmn`
- animeka app module: `60-apps/etzhayyim-project-animeka/appview/etzhayyim-wasm-animeka-an1m3k4x/`
