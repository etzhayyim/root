---
id: adr-2605010000
title: RunPod RTX 6000 Ada single-pod unification — ComfyUI + vLLM + LiteLLM 同居 (LLM inference SSoT)
status: active
doc_type: adr
topic: inference
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - RunPod compute backend topology for animeka / mangaka / shinshi ComfyUI / image generation pipelines
  - ComfyUI gateway routing (50-infra/cloudflare/workers/comfyui/wrangler.jsonc UPSTREAM_URL)
  - shinshi photoreal upstream (60-apps/etzhayyim-project-shinshi/.../wrangler.jsonc COMFY_POD_URL)
  - Custom RunPod image build pipeline (50-infra/runpod/vllm-gemma-image/, .github/workflows/runpod-vllm-gemma-image.yml)
related:
  - adr-2604282100  # LLM benchmark gemma4 default
  - adr-2604292130  # llm.etzhayyim.com runpod pass-through
  - adr-2605080600-langgraph-server-granian-l3-runtime  # resident LangGraph organism actors may use Murakumo as L8 somatic inference
  - adr-2604231328-animeka-bpmn-l40s-pipeline  # animeka 12-stage pipeline
  - adr-2604281600  # shinshi melina pipeline
  - adr-2605211000  # supersedes this ADR for LLM text inference path
supersedes: []
superseded_by:
  - adr-2605211000  # LLM text inference path — Vultr A16-16Q keiei-llm-pool (2026-05-21)
notes: |
  Supersedes the planned-but-never-implemented [[migrations]]
  llm-bench-volume-attach-6000ada (deps.toml, 2026-04-28). The migration
  entry itself is marked status=superseded with superseded_by pointing
  to runpod-6000ada-unified-pod-2605010000.

  2026-05-21 partial supersession: LLM text inference path is superseded by
  ADR-2605211000 (Vultr A16-16Q keiei-llm-pool). This ADR remains authoritative
  for ComfyUI / SDXL / video generation (RunPod Secure pod, when supply restores).
  LLM_CHAT_COMPLETIONS_URL and etzhayyim_LLM_URL in zeebe-worker now point to
  keiei-litellm in-cluster — do NOT revert to RunPod pod URL on pod restore.
---

# Context

`animeka.etzhayyim.com`, `mangaka.etzhayyim.com`, `shinshi.etzhayyim.com` 等の生成 pipeline は 2 系統のバックエンドに依存していた:

| 用途 | バックエンド | 状態 (2026-04-30) |
|---|---|---|
| LLM (chat / structured JSON / planning) | Murakumo Mac mini fleet (LiteLLM @ judah:4000) | 動作中だが 17s 帰り (cold) — judah → Ollama gemma4-e4b の serial path |
| LLM (高品質 32B クラス) | `llm.etzhayyim.com` (CF Worker `etzhayyim-runpod` → RunPod Serverless `3fctheq51haikt`) | gemma4:26b-a4b-it-q4_K_M (Ollama on serverless), 421 jobs success, $19/day standby |
| 画像生成 (SDXL) | RunPod pod `r127r1ab2arjg8` (RTX 6000 Ada, EU-SE-1) | 2026-04-29 頃 terminate、`comfyui.etzhayyim.com` upstream 死亡 |

User の方針 (2026-04-30):
> animeka, mangaka, shinshi などでは murakumo を使わずに runpod の 6000 ada で一本化

> animage, wan, waireal などは pod じゃないと安定して動かない

要件:
- ComfyUI (Animagine XL / waiREALCN_v150 / 将来 WAN/Flux) は **pod** で常駐 (serverless では cold start + VRAM 占有制約で品質崩壊)
- LLM も **同 pod** に co-locate (Murakumo 並走 / serverless 二重化を排除)
- 単一 pod で boot が速く、再起動時の cold start を image layer に閉じ込める

# Decision

**RunPod RTX 6000 Ada Generation 48 GB Secure 単一 pod に ComfyUI + vLLM + LiteLLM を pre-built image で co-locate**。Murakumo / serverless / 旧 6000 Ada (EU-SE-1) を全て退役。

> **2026-05-17 DC 移行 + Secure SUPPLY_CONSTRAINT**: US-KS-2 GPU pool 完全在庫切れ → US-WA-1 に移行。volume `p9riuzhrvf` (US-KS-2) 削除、新規 volume `om0lfbfmvg` (US-WA-1, 250 GB) 作成。pod `numnfxlu2qx7s2` を deploy したが SSH タイムアウト (image pull 失敗の疑い) → terminate。**その後 RTX 6000 Ada Secure が全 DC で SUPPLY_CONSTRAINT** (US-WA-1/TX-3/GA-1/OR-1/CA-1/CA-MTL-1/EU-SE-1/EU-NL-1 全滅)。containerRegistryAuth `cmnr5ls0c00dtl707ehmglpul` (ghcr-etzhayyim-v2) のトークンを 2026-05-17 に更新済み。Secure cloud が復旧次第 `comfyui-l40s/scripts/up.sh` を再実行すること。現在 **ComfyUI / LLM / LiteLLM エンドポイントすべて DOWN**。

## LLM inference SSoT (CRITICAL, 2026-05-07 reaffirmed)

**LLM 推論の正本 = この ADR の RunPod pod (`ghcr.io/etzhayyim/runpod-vllm-gemma:latest` on RTX 6000 Ada)。Murakumo は LLM 推論経路として想定しない。** Mac mini fleet (`murakumo.etzhayyim.com`, judah:4000 LiteLLM) は LLM 推論 SSoT から外す。

> **pod なし (2026-05-17 現在)**: RTX 6000 Ada Secure SUPPLY_CONSTRAINT 全 DC。Secure cloud 復旧後に新 pod ID が払い出される。`runpod-podid-update-checklist` に従って zeebe-worker / shinshi / training Helm values の URL を更新すること。Volume `om0lfbfmvg` (US-WA-1) は存在するがモデル未ダウンロード。

**禁止 (新規コードに対する不変条件)**:
- pymagatama / agent loop / projector / BPMN handler から `murakumo.etzhayyim.com` / `murakumo-serve.etzhayyim.com` / `magatama-llm8cf4ai` / `LLM_SERVICE` service binding に対する LLM call を新規追加する
- RunPod が cold / 障害状態の時に Murakumo を automatic fallback として呼ぶ (silent fail で degraded response を返すか、明示的に `503 ServiceUnavailable` を返すこと)
- LLM 用の new env var (`MURAKUMO_*`, `LLM_FALLBACK_*`) を default true で配るか、Worker secret に投入する
- `MURAKUMO_DEFAULT_MODEL` を「Murakumo の default」と読む実装。これは命名が legacy で残るが意味は **「LLM SSoT (= RunPod) の default model alias」** に再定義 (rename は future kaizen)

**例外 (ADR-2605080600)**:

Resident artificial-organism actors are not generic GenAI pipelines. For this
class only, LangGraph Server may route inference to the Murakumo Mac mini fleet
as the **L8 Somatic Inference Layer** when all conditions hold:

- the actor identity, checkpoint, memory, and objective state remain in DID +
  LangGraph thread + Kotoba/Datomic
- Murakumo is used only as an OpenAI-compatible inference organ, not as the
  authoritative actor subject
- the route is explicit (`LLAMA_BASE_URL` / `etzhayyim_LLM_URL`) and observable
- there is no silent fallback from RunPod to Murakumo for animeka / mangaka /
  shinshi / generic production GenAI paths

This exception does not change the public `llm.etzhayyim.com` SSoT for generation
pipelines. It only defines the resident organism loop described by
ADR-2605080600.

**残存する legacy 経路 (要 cleanup, code follow-up)**:
- `50-infra/cloudflare/workers/atproto/src/agent/infer.ts:412` `callMurakumo()` — RunPod fail 時の fallback 経路。**削除**して `503` 化する
- `50-infra/cloudflare/workers/atproto/src/agent/flow-runner.ts:833` の `MURAKUMO_DEFAULT_MODEL` reference — alias 名は維持しつつ docstring で SSoT 再定義
- `MURAKUMO_SERVICE` service binding がある全 Worker で削除可能性を確認

**Murakumo Mac mini fleet の今後** (LLM 以外の用途):
- 削減候補。LLM が SSoT から外れた以上、4 node 常時稼働の正当化は弱い
- 残す場合は明示的に「development sandbox / local model 実験」と再定義し、production traffic を流さない

## Topology

```
Pod <NEW_ID> (RTX 6000 Ada 48 GB, US-WA-1, comfyui-etzhayyim, $0.77/hr)  ← 未払い出し (2026-05-17 SUPPLY_CONSTRAINT)
│  (旧: numnfxlu2qx7s2 terminated、旧: 58pvflvw9w6nt3 US-KS-2、旧: vyp99t9px7h4dl US-KS-2)
│
├─ Image: ghcr.io/etzhayyim/runpod-vllm-gemma:latest
│         (FROM runpod/comfyui:latest + /opt/venv-vllm + /opt/start-llm.sh)
│         ENTRYPOINT /start.sh wraps base /start.sh.original (ComfyUI/sshd/jupyter bg)
│         → 45s sleep → exec /opt/start-llm.sh → vLLM :8000 → LiteLLM :4000
│
├─ /workspace  (Network Volume om0lfbfmvg, 250 GB, US-WA-1)  ← 2026-05-17 更新
│  ├─ runpod-slim/ComfyUI/models/checkpoints/
│  │    ├─ animagine-xl-4.0.safetensors  (6.5 GB, anime SDXL)
│  │    └─ waiREALCN_v150.safetensors    (6.5 GB, realistic SDXL — v50 substituted as v150)
│  └─ .hf-cache/                          (gemma-4-26B-A4B-it bf16 weights, 49 GB)
│
├─ Service :8188 — ComfyUI 0.18.2
│    Public URL: https://<NEW_ID>-8188.proxy.runpod.net  ← DOWN (pod なし)
│    Front: comfyui.etzhayyim.com (CF Worker etzhayyim-comfyui-2604221600)
│    VRAM: ~10-12 GiB peak per model
│
├─ Service :8000 — vLLM 0.19.1 (CUDA 12.x)
│    Model: google/gemma-4-26B-A4B-it (MoE 26B total / A4B active)
│    Quantization: --quantization fp8 (runtime, 26 GiB VRAM)
│    --max-model-len 4096 --gpu-memory-utilization 0.70 --enforce-eager
│    Public URL: https://<NEW_ID>-8000.proxy.runpod.net  ← DOWN
│
└─ Service :4000 — LiteLLM 1.55.0 proxy
     Public URL: https://<NEW_ID>-4000.proxy.runpod.net  ← DOWN
     8 alias all → openai/google/gemma-4-26B-A4B-it on 127.0.0.1:8000
       gemma-4-26b-a4b-it / gemma4-27b / gemma4-runpod
       gemma-4-e4b-it / gemma-4-e2b-it / gemma3:27b
       tier0-general / tier0-structured (pymagatama llm.py 互換)
```

**VRAM budget (48 GB 上限)**:
- vLLM gemma4-26B-A4B FP8: ~26 GiB
- ComfyUI active SDXL model: ~10-12 GiB peak
- KV cache + reserve: ~10 GiB
- 合計 ~46-48 GiB (gpu-memory-utilization 0.70 で 33.6 GiB を vLLM 上限)

将来 WAN 5B (~14 GiB) や Flux dev (~12 GiB) を ComfyUI に追加する場合は、vLLM 側を gemma-4-E4B-it (~5 GiB FP8) に縮小して ComfyUI に 35 GiB 振る。

## Caller routing

```
animeka.etzhayyim.com (thin CF Worker b7b7f6b2)
  → dispatcher.etzhayyim.com/xrpc/com.etzhayyim.animeka.* (HTTPS via CF)
    → bpmn-dispatcher (mitama-udf VKE) → Zeebe broker
      → zeebe-worker pod (pymagatama:0.3.11-amd64)
        → generic.llm.chat / generic.llm.json handler
          → LLM_CHAT_COMPLETIONS_URL = https://<NEW_ID>-4000.proxy.runpod.net/v1/chat/completions  ← DOWN
            → LiteLLM :4000 → vLLM :8000 → gemma-4-26B-A4B-it
        → generic.comfyui.call handler
          → comfyui.etzhayyim.com (CF Worker)
            → UPSTREAM_URL = https://<NEW_ID>-8188.proxy.runpod.net  ← DOWN

shinshi.etzhayyim.com (CF Worker 0df83283)
  → seedScenesWithImagesReal (photoreal SDXL)
    → COMFY_POD_URL = https://<NEW_ID>-8188.proxy.runpod.net  ← DOWN
  → com.etzhayyim.apps.shinshi.generateVideo (Wan video)
    → dispatcher.etzhayyim.com → Zeebe → shinshi.video.render
```

# Alternatives considered

## A. 2 pods (ComfyUI 専用 + LLM 専用)

- Pros: 役割分離、ComfyUI に 48 GB フル割当 (WAN/Flux 同時 load 可)
- Cons: $1.11/hr × 24 × 30 = $800/mo (vs unified $555/mo)
- 採用せず: VRAM の現実的余裕は同居でも確保可能、月 $245 削減効果大

## B. ComfyUI on pod + LLM on serverless (etzhayyim-llm-gemma4-runpod を継続)

- Pros: serverless は idle scale-to-zero で burst-friendly、421 jobs 既に成功実績
- Cons: workersStandby=2 で $19/日 = $576/mo (pod ほぼ同額)、cold start が generation flow を阻害、別 model alias 系統の二重管理
- 採用せず: User 方針「Murakumo を遣わずに 6000 ada で一本化」と整合せず、serverless 退役

## C. 同居 image を `vllm/vllm-openai:v0.19.1` 基底にして ComfyUI を後乗せ

- Pros: vLLM 公式 image なので ABI 完璧
- Cons: sshd / ComfyUI の Python deps を全部自前で焼く必要、`runpod/comfyui:latest` の良いところ (sshd, jupyter, filebrowser, /opt/comfyui-baked) が再現できない
- 採用せず: 当初試したが (commit `cbf0c025` 直前)、ENTRYPOINT が vllm のみで sshd が無く debug 不能、ComfyUI install 工数重い

## D. 既存 ADR-2604282100 path (Network Volume `3zgavabooi` を attach + Gemma4-31B compressed-tensors)

- 当初計画。実装段階で:
  - `3zgavabooi` は EU-SE-1 のみで作成済、6000 Ada 在庫が EU-SE-1 で枯渇 → US-KS-2 で `p9riuzhrvf` 新規作成 (250 GB)。`3zgavabooi` は 2026-05-07 削除 (orphan, −$14/mo)
  - Gemma4-31B (33B dense bf16 ~66 GiB) は 48 GB に乗らない (compressed-tensors で 4-bit ~17 GiB だが in-memory KV + ComfyUI 同居で margin 不足)
  - Gemma-4-26B-A4B-it に切替 — MoE active 4B で gemma4-31B より速く、品質は同等水準
- ADR-2604282100 は LLM benchmark の意思決定 (model 選定) として保持、infra topology は本 ADR で更新

# Secrets Management (macOS Keychain primary)

すべてのシークレットは **macOS Keychain** (`security` コマンド) で管理する。`.env` や shell 変数へのハードコード禁止。

```bash
# RunPod API key
security add-generic-password -s "etzhayyim.runpod" -a "RUNPOD_API_KEY" -w "<key>" -U

# HuggingFace token (gated models: FLUX, gemma-4, Seedance 2)
security add-generic-password -s "etzhayyim.hf" -a "HF_TOKEN" -w "<tok>" -U

# Cloudflare Tunnel token (comfyui-etzhayyim tunnel)
security add-generic-password -s "etzhayyim.cloudflare" -a "COMFYUI_TUNNEL_TOKEN" -w "<token>" -U

# SSH public key for pod access (RunPod AUTHORIZED_KEYS)
security add-generic-password -s "etzhayyim.runpod" -a "SSH_PUBKEY" -w "$(cat ~/.ssh/id_ed25519.pub)" -U
# id_rsa.pub は id_ed25519.pub がない場合の自動フォールバック (scripts/_lib.sh ssh_pubkey())

# RunPod container registry auth (ghcr.io pull)
# containerRegistryAuth: cmnr5ls0c00dtl707ehmglpul (RunPod console の Container Registry Auth ID)
# これは RunPod 側で保存済み — ローカル Keychain 不要
```

**`scripts/_lib.sh` の Keychain loader**:
- `runpod_key()` → `security find-generic-password -s etzhayyim.runpod -a RUNPOD_API_KEY -w`
- `hf_token()` → `security find-generic-password -s etzhayyim.hf -a HF_TOKEN -w`
- `ssh_pubkey()` → Keychain `etzhayyim.runpod/SSH_PUBKEY` → fallback `~/.ssh/id_ed25519.pub` → fallback `~/.ssh/id_rsa.pub`

# Image build

`50-infra/runpod/vllm-gemma-image/`:
- `Dockerfile` — `FROM runpod/comfyui:latest`、venv に vllm 0.19.1 + flashinfer --no-deps + litellm[proxy]==1.55.0、`/start.sh` wrapper を bake
- `start-llm.sh` — vLLM serve + LiteLLM proxy 起動、`source ~/.bashrc` は呼ばない (base bashrc が非対話 tty で hang する)
- `litellm_config.yaml` — 8 alias config

`.github/workflows/runpod-vllm-gemma-image.yml` で `push` 時に GH Actions が `linux/amd64` build + ghcr.io へ push (image visibility=private、RunPod は `containerRegistryAuth cmnr5ls0c00dtl707ehmglpul` で pull)。

# Critical conventions

新規 [[conventions]] 追加 (deps.toml):

1. **`vllm-cuda12x-compat`** (priority 7.0, 訂正): `pip install vllm==0.19.1` 後に `--force-reinstall torch` を **してはいけない**。vLLM wheel の `_C.abi3.so` が同梱 torch (2.10.0+cu128) の CXX11 ABI に依存しており、別 torch で上書きすると `undefined symbol _ZN3c106ivalue14ConstantString6create...` ImportError で起動不能。flashinfer は `--no-deps` で torch 上書き防止。

2. **`runpod-proxy-browser-ua-required`** (priority 8.0, NEW): `*.proxy.runpod.net` は CF 経由で配信され default Python urllib UA を 403 block する。Python caller は browser UA (Chrome/129) 必須。`pymagatama/llm.py` は対応済。CF Worker `comfyui.etzhayyim.com` / `llm.etzhayyim.com` 経由なら UA 制約なし (CF→CF egress)。

3. **`runpod-podid-update-checklist`** (priority 6.0, NEW): pod 再作成時に sed 一括更新する箇所:
   - `50-infra/cloudflare/workers/comfyui/wrangler.jsonc` `UPSTREAM_URL` → `wrangler deploy`
   - `50-infra/vultr/mitama-udf-pool/templates/zeebe-worker.yaml` `LLM_CHAT_COMPLETIONS_URL` + `etzhayyim_LLM_URL` → `helm upgrade --reuse-values` + `kubectl rollout restart deploy/zeebe-worker`
   - `60-apps/etzhayyim-project-shinshi/.../wrangler.jsonc` `COMFY_POD_URL` (+ src/app.ts default fallback) → `etzhayyim deploy`
   - watchdog plist `~/Library/LaunchAgents/com.etzhayyim.runpod-comfyui.plist` は **bootout 維持** (旧 GPU_TYPE_ID で 4090 auto-respawn する)

# Cost

| 項目 | $/hr | $/mo |
|---|---|---|
| Pod 6000 Ada Secure US-WA-1 | $0.77 | $554 |
| Network Volume `om0lfbfmvg` 250 GB US-WA-1 | — | $17.50 |
| **合計 (pod 稼働時)** | | **$571.50/mo** |

旧構成 (4090 + serverless standby + Murakumo overhead): ~$1100/mo → **月 $528 削減**。

> **2026-05-17 現在**: Pod なし ($0/hr)、Volume のみ課金 ($17.50/mo)。RTX 6000 Ada Secure SUPPLY_CONSTRAINT で待機中。Secure cloud 復旧後 up.sh 再実行で $571.50/mo 再開。

退役済 resources:
- pod `r127r1ab2arjg8` (旧 6000 Ada EU-SE-1)
- pod `58pvflvw9w6nt3` (旧 6000 Ada US-KS-2, terminated 2026-05-17)
- pod `vyp99t9px7h4dl` (旧 6000 Ada US-KS-2, terminated)
- pod `numnfxlu2qx7s2` (US-WA-1, terminated 2026-05-17 — SSH timeout、image pull 失敗疑い。containerRegistryAuth は更新済み)
- pod `mshg2dj2dvexga` `tmngllqks3dqsq` `7hka9do0c2yiw8` `nwtteuc6e93su0` `dj6gqc8pufvxmc` `kagm6olwzyngdm` `yrdtjersjhjtha` `8rzva8z3f6bqit` (4090 transit pods, all terminated)
- volume `43k3uq9ldn` (EUR-IS-1, deleted)
- volume `bskaa2wrjo` (EUR-IS-1, 100 GB, deleted 2026-05-07)
- volume `p9riuzhrvf` (US-KS-2, 250 GB, deleted 2026-05-17 — DC GPU 全在庫切れ)
- serverless `etzhayyim-llm-gemma4-runpod` (`3fctheq51haikt`, workersStandby=0、ID 残置で緊急 fallback 可)

# Verification

## 最終正常確認 (2026-05-01)

| 項目 | 結果 (旧 pod `58pvflvw9w6nt3`) |
|---|---|
| vLLM :8000 chat/completions | ✅ "OK" 1.8s |
| LiteLLM :4000 alias | ✅ "PONG" 1.8s |
| comfyui.etzhayyim.com upstream.reachable | ✅ true 346ms |
| shinshi seedScenesWithImagesReal | ✅ 832×1216 PNG 1.16 MB |

## 現状 (2026-05-17)

| 項目 | 状態 |
|---|---|
| ComfyUI (:8188) | ❌ DOWN (pod なし) |
| vLLM (:8000) | ❌ DOWN (pod なし) |
| LiteLLM (:4000) | ❌ DOWN (pod なし) |
| Volume `om0lfbfmvg` | ✅ 存在 (モデル未 DL) |
| Registry auth `cmnr5ls0c00dtl707ehmglpul` | ✅ トークン更新済み |
| zeebe-worker `LLM_CHAT_COMPLETIONS_URL` | ⚠️ 旧 pod URL 設定済み (要 Helm upgrade after restore) |
| RTX 6000 Ada Secure | ❌ 全 DC SUPPLY_CONSTRAINT |

# Open follow-ups (deps.toml [[migrations]] 別エントリ)

1. **`animeka-chat-zeebe-pickup-2605010000`** (open, severity medium): `com.etzhayyim.animeka.chat` の `generic.llm.chat` job が Zeebe broker queue で pickup されない (CF Worker 25s timeout)。LLM URL とは独立、Zeebe / pyzeebe handler の signature 問題の可能性。

2. **`shinshi-photoreal-post-auth-2605010000`** (open, severity low): photoreal 画像生成 + blob upload は OK だが、最終的な AT Record post (`app.bsky.feed.post` as path-DID) で 401。`sdk.pds.dispatch` 経由に切替か Service Auth JWT 手動付与で修復可。

# Future kaizen

- WAN 5B 動画 + Flux dev 12B を ComfyUI に追加する際は vLLM を E4B (5 GiB) に縮小、ComfyUI に 35 GiB 振る
- 6000 Ada 在庫が他 DC で復活したら、地理冗長として 2 nd pod (動画 / 画像 dedicated) を spawn 可
- shinshi-melina cron の 30 min 周期を Zeebe BPMN timer-start `R/PT30M` に移行 (k8s CronJob 排除)
