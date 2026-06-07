---
id: doc-260429-animeka-r0-recovery-state
title: "animeka.etzhayyim.com R0 recovery — 2026-04-29 handoff state"
status: active
doc_type: how-to
topic: animeka-pipeline-recovery
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - animeka.etzhayyim.com pipeline recovery from 2026-04-26→2026-04-29 outage
  - R2 (Misaki character LoRA) staged work-in-progress
  - pyzeebe Channel-close intermittent bug (workaround documented)
related:
  - adr-2604231328-animeka-bpmn-l40s-pipeline
  - adr-0094-kotoba-stable-three-node-topology
---

# Goal

Concise resume document for the agent (human or LLM) picking up the
animeka.etzhayyim.com pipeline recovery work after a session close on
2026-04-29. Captures: what's fixed, what's open, what's staged
locally, and the exact next checks / actions.

This is **handoff state**, not architectural reference. Permanent
design lives in ADR-2604231328 (animeka 12-stage BPMN + RunPod ComfyUI
pipeline; Vultr fallback retired 2026-05-09) — read that first.

# Outage timeline

| Date  / time (UTC) | Event |
|---|---|
| 2026-04-26 22:44Z | Last successful autopilot cut (`3mkgmz6yjo22e` on bsky) |
| 2026-04-26 ~23Z   | comfyui.etzhayyim.com gateway break-glass key rotated; pyzeebe `Bearer pod-inline` no longer matches → all comfyui.call return 401 |
| 2026-04-28 14:47Z | Last 401 cutRunner audit before broker died |
| 2026-04-28 ~14:50Z | Zeebe broker zeebe-0 starts OOMKilling (1.5Gi limit insufficient under live workload) |
| 2026-04-28 12:48Z (= 21:48 +0900) | Code fix `fbf6b86f` on branch — adds `x-kotodama-verified: true` to `task_generic_comfyui_call` matching shinshi_video pattern |
| 2026-04-28 15:46Z | PR #1159 merged → main has the comfyui internal-trust shim |
| 2026-04-28 22:48Z | kotodama image 0.2.71 deployed (contains the shim) |
| 2026-04-28 23:13Z | Broker yaml fix committed (`fa74bc7f3d5`, 1.5Gi → 4Gi mem + JVM Xmx 768m → 2g) |
| 2026-04-29 04:17Z | `kubectl apply -f zeebe.yaml` — broker rolls to 4Gi, partitions recover |
| 2026-04-29 04:26Z | Worker pod re-rolled, gRPC channel reset |
| 2026-04-29 04:30Z | Manual `animeka_autopilot` instance fired via `kubectl exec` + `pyzeebe.create_process_instance` — but no audit row appeared |
| 2026-04-29 04:38Z | v6 image build push w/ `_t as t` ImportError in `primitives/handotai.py:375` → CrashLoopBackOff |
| 2026-04-29 04:50Z | v7 image fixes the import → pod healthy, 0 restart |
| 2026-04-29 05:05Z | Session closed at this state — autopilot R/PT15M timer still dead, audit gap continues |

# What is fixed (verified in production)

1. **comfyui gateway 401** — root cause: pyzeebe sent `Bearer pod-inline`
   while the gateway's `COMFYUI_API_KEY` env had been rotated to a
   different secret. Fix: send `x-kotodama-verified: true` header
   instead, matching the existing pattern in
   `shinshi_video.py:_comfy_headers` (lines 60-71). Same gateway,
   already in production for shinshi for 6+ days, so no new attack
   surface. Code is on `main` since PR #1159, image since 0.2.71.
2. **Zeebe broker OOMKilled** — 1.5Gi limit hit by RocksDB + Atomix +
   gRPC native arenas under animeka workload. Bumped to 4Gi limit /
   2Gi JVM heap. Yaml on `main` (`fa74bc7f3d5`), cluster updated
   2026-04-29 04:17Z, 0 restart since.

# What is open

## Open PR — #1160 (`260429-misaki-lora-wiring` branch)

3 commits on top of main, all single-file changes to
`50-infra/runpod/comfyui-l40s/adapter/openai-comfyui-adapter.py`:

1. `feat(comfyui-adapter): LoraLoader auto-injection for character LoRAs`
2. `fix(comfyui-adapter): scan loras dir at startup, skip injection if missing`
3. `feat(comfyui-adapter): mode dispatcher for video synthesis`

Behavior after merge + adapter restart on RunPod pod:

- Prompt with `misaki` (word-boundary, case-insensitive) auto-injects
  LoraLoader if `misaki_animagine_v1.safetensors` is in
  `/workspace/comfyui/ComfyUI/models/loras/`.
- Missing LoRA file → graceful fallback to no-LoRA workflow (no
  ComfyUI hard-error). Verified by 5/5 sanity tests locally.
- `/v1/videos/generations` dispatches on `mode` body field
  (`slideshow` / `image2video` / `composite`). Real Wan 2.2 5B / Seedance 2
  workflow not yet wired; image2video and composite gracefully fall
  back to slideshow synthesis. Response carries `X-Adapter-Mode` and
  `X-Adapter-Real-Wan: false` so BPMN audit can tell what really ran.

Merge needs a manual adapter restart on the pod
(`tmux kill-session adapter; cd /workspace; tmux new-session -d -s adapter '...'`)
to pick up the new code.

## R2 — Misaki character LoRA training (RUNBOOK ready, user-side execution pending)

Local artifacts (will be lost on workstation restart — move them to a
checked-in dir or B2 if the session ends without training):

```
/tmp/misaki-ref/                    # 10 references (832x1216 PNGs + .txt captions)
/tmp/misaki-lora/                   # Kohya SDXL training tree
  ├── img/10_misaki/{ref-01..10}.{png,txt}
  ├── config.toml                   # rank 16, alpha 8, AdamW8bit, 750 steps, ~1.5h
  ├── README.md                     # dataset card + integration guide
  └── RUNBOOK.sh                    # idempotent: upload / setup / train / monitor / deploy / status
/tmp/misaki-lora.zip                # 13 MB bundle of the above
```

Pod info (RunPod API, 2026-04-29):

```
pod_id     r127r1ab2arjg8  (comfyui-etzhayyim-6000ada, RTX 6000 Ada 48 GiB)
ssh_host   195.26.233.87
ssh_port   51592
ssh_user   root
ssh_key    ~/.ssh/id_ed25519  (or `etzhayyim.runpod` keychain SSH_PUBKEY)
workspace  /workspace
```

Steps (run from local):

```bash
bash /tmp/misaki-lora/RUNBOOK.sh upload    # ~30s rsync
bash /tmp/misaki-lora/RUNBOOK.sh setup     # Kohya install if missing (~5min first time)
bash /tmp/misaki-lora/RUNBOOK.sh train     # tmux 'misaki-train' starts; ~1.5h
bash /tmp/misaki-lora/RUNBOOK.sh status    # poll progress
bash /tmp/misaki-lora/RUNBOOK.sh deploy    # cp .safetensors → ComfyUI loras/
```

After deploy, restart the comfyui adapter on the pod so PR #1160's
`_scan_available_loras()` picks up the new file.

Caveat: training and ComfyUI generation share the 6000 Ada VRAM
(~22 GiB Wan + 5.5 GiB Ollama + ~14 GiB training-time peak). Run training
when autopilot is paused, or accept GPU contention.

## Autopilot R/PT15M timer is dead

Symptom: 14h+ since the last `autopilot` audit row even though both
broker and worker are healthy. Manual fire of `animeka_autopilot`
via `pyzeebe.create_process_instance` succeeded (returned a fresh
`process_instance_key`) but the first task — `Task_GenScene`
(`generic.llm.chat`) — never ran (no Task_Audit row, no LLM logs).

Hypotheses, ranked:

1. **Timer state lost during the OOM cycle** — Zeebe broker held the
   R/PT15M timer in a partition that didn't recover cleanly. Fix: re-deploy
   `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/animeka/autopilot.bpmn` (and
   re-register in `vertex_bpmn_process_def`) so the broker re-creates
   the timer subscription.
2. **Process instance dispatched but worker stream paused** — pyzeebe
   poller hit `RESOURCE_EXHAUSTED` for non-animeka task types in a
   loop and the gRPC client back-off held the activate stream open
   without delivering animeka jobs. Fix: filtered subscriptions or a
   reconnect on first 503.
3. **Variable mismatch** — autopilot.bpmn `Task_GenScene` expects
   variables that are absent on a `create_process_instance` call from
   gRPC (vs. a timer-fired one). Less likely; the manual call passed
   `variables={}` and the LLM task has no required vars per the
   ioMapping.

Next-actor checks (10 min):

```bash
# 1. Confirm broker has 0 active process instances of animeka_autopilot
kubectl exec -n mitama-udf deploy/zeebe-worker -c zeebe-worker -- \
  python3 -c "
import asyncio
from pyzeebe.channel import create_insecure_channel
from pyzeebe.grpc_internals.zeebe_process_adapter import ZeebeProcessAdapter
async def m():
    ch = create_insecure_channel('zeebe-gateway:26500')
    a = ZeebeProcessAdapter(ch)
    r = await a.create_process_instance(bpmn_process_id='animeka_autopilot', version=-1, variables={})
    print(r)
asyncio.run(m())
"

# 2. If still no audit in 5 min — re-deploy the BPMN
# (TODO: write a `etzhayyim bpmn redeploy animeka_autopilot` runbook;
#  for now use the bpmn-dispatcher resync handler if available)
```

## pyzeebe Channel-close intermittent bug

Symptom: under broker back-pressure or after a broker restart,
pyzeebe's gRPC channel transitions to "Channel is closed" and stops
processing jobs without exiting the python process. K8s liveness
doesn't catch it because the process is still alive.

Workaround: `kubectl delete pod` to force a fresh container with a
fresh channel. Re-occurred on both v5 (`20260429-v5-amd64`) and
v7 (`20260429-v7-amd64`) images, so it's not specific to the recent
image churn.

Permanent fix options (not yet implemented):

1. Add a livenessProbe that grep the worker log for "Zeebe worker
   was stopped" or that hits `localhost:8815/health` (the pyzeebe
   server endpoint) to catch dead sockets.
2. Patch the worker to register a channel-state callback and `os._exit(1)`
   when the channel transitions to SHUTDOWN.
3. Upgrade pyzeebe to a version with built-in reconnect on
   `DEADLINE_EXCEEDED` / `UNAVAILABLE`.

Track as: `pyzeebe-channel-close-recovery` — separate from animeka R0.

## v6 image regression — `ImportError: _t`

`20260429-v6-amd64` failed at startup with
`ImportError: cannot import name '_t' from 'kotodama.zeebe_worker_main'`
at `primitives/handotai.py:375`. v7 fixed it but the buggy source was
never pushed to a tracked branch, so we can't audit the fix retro
(no diff to learn from). If the same regression returns, ask the
build-time author to push the buggy state to a debug branch first.

# Roadmap (R3–R7) — not started, listed for resume context

| # | What | Why | Rough scope |
|---|---|---|---|
| R3 | Layout stage rebuild — replace draw with ControlNet-depth + scribble compose | Stage 4 currently produces sketchbook drawings, not animation layouts | 4h workflow + adapter |
| R4-2 | Real Wan 2.2 5B i2v + composite ComfyUI workflow | R4-1 (PR #1160 mode dispatcher) is MVP slideshow fallback only | 1d, needs custom node verification on pod |
| R5 | Stage 8 autoTrace lineart-controlnet + 2-tone palette quantize | Cel-shade vs. illustration look | 1d |
| R6 | ckpt switching: Pony v6 / Mappa LoRA / Science SARU LoRA | Style breadth beyond Animagine XL 4.0 | 4h adapter + dataset |
| R7 | kami-postfx integration (camera move + glow + chromatic aberration) | OP/MV grade composite | 2d |

# Visual QA baseline (2026-04-28, pre-fix)

`/tmp/animeka-qa/` had 14 sample images covering 4 cuts × 4 stages
(storyboard / layout / keyframe / background) from the last successful
autopilot run on 2026-04-26. Findings:

- Storyboard: catastrophic (4-up grid corruption, score 1/10)
- Layout: missing function (sketchbook drawings, not layouts, 2/10)
- Keyframe: variable (4/10 avg, best case 6.5/10 — Cut C dusk cherry blossom)
- Background: only stage that approaches pro (7/10, Shinkai-influenced
  concept art quality)

Compared to NARUTO / 呪術廻戦 / ダンダダン bench: 0/14 cuts pass.
Closest to OP/MV-grade: BG-only static (~18% match). No motion = no
MV/OP evaluation possible until R4-2 ships.

These are stale (pre-401, pre-fix); resume work should re-baseline
once R0 verifies and R2 LoRA is integrated.

# References

- ADR-2604231328 — animeka 12-stage BPMN + Vultr L40S ComfyUI pipeline
- PR #1159 (merged) — comfyui internal-trust shim (R0)
- PR #1160 (open) — LoRA wiring + graceful fallback + video mode dispatcher
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/animeka/{autopilot,cutRunner,generateInbetween,renderComposite}.bpmn`
- `50-infra/runpod/comfyui-l40s/adapter/openai-comfyui-adapter.py`
- `etzhayyim-root/50-infra/vultr/zeebe/zeebe.yaml` — broker resource budget
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py:1936` — `task_generic_comfyui_call`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/shinshi_video.py:60` — established x-kotodama-verified pattern
