---
id: adr-2605220000-shinshi-tiktok-video-pipeline
title: "shinshi — TikTok-style Vertical Short Video Pipeline (I2V + voice + BGM + caption + NSFW labels)"
status: proposed
doc_type: adr
topic: shinshi-tiktok-video-pipeline
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - shinshi 動画生成パイプライン (TikTok 縦動画 9:16, 15-25s, hook+payoff 構造)
  - I2V 採用モデル (Wan 2.2 I2V 14B fp8, 既存 video_render primitive を再利用)
  - 日本語キャラ音声 (Style-Bert-VITS2, character speaker LoRA)
  - BGM 生成 (Stable Audio Open, MIT 互換)
  - SFX 生成 (AudioLDM2 もしくは Stable Audio Open trim)
  - mux / caption / loudnorm 規定 (ffmpeg + libass, 9:16 1080×1920 H.264)
  - 配置: visual = LAN 192.168.1.22 ComfyUI、audio = SJC `mitama-udf` Python pod
  - NSFW self-label 適用 (post + caption + voice)
  - Per-clip 容量・所要時間見積もり
priority: 7.5
axis: pipeline
weight: 0.75
extends:
  - adr-2605010000-runpod-6000ada-unified-pod
related:
  - adr-2605180000-lawfirm-product-focus-bmc-lean
  - adr-2605091600-plasmid-graft-horizontal-tool-acquisition
priority_note: |
  shinshi は Priority 2 product (lawfirm P1 / shinshi P2 / animeka P3, ADR
  2605180000)。静止画 (`scene_bulk_seed`) と単発 i2v (`video_render` 既存) は
  動いているが、TikTok / Reels / YouTube Shorts 流入を狙うには「縦 + 短尺 +
  hook + 音声 + BGM + caption」の 5-shot 構造が必要。本 ADR はそこを最小コスト
  (既存 Wan 2.2 + LAN GPU を流用) で組む決定を記す。
---

## Goal

shinshi.etzhayyim.com の model DID から、**TikTok / Reels / YouTube Shorts に直接転用できる縦短尺動画 (9:16, 15-25s)** を `scene_bulk_seed` と同じ LangGraph フローで自動生成する。1 clip = 5 shot + voice + BGM + SFX + caption の mux 済 H.264 mp4 を PDS blob として post する。

## Scope

**In scope**:

- LangGraph 新規 graph `shinshi.video.tiktokShort` (lg-shinshi に追加)
- 5-shot 構造 (hook 1.5s → 4 main shots → CTA 2s, 計 25s)
- Wan 2.2 I2V を per-shot ドライバとして再利用 (既存 `kotodama.primitives.shinshi_video`)
- 音声生成 (TTS + BGM + SFX)
- ffmpeg mux + caption overlay
- PDS uploadBlob → feed.post + embed.video + NSFW selfLabel
- 既存 `_SCENE_LABELS_{PHOTOREAL,ANIME}` を shot script ジェネレータの種に再利用

**Out of scope** (別 ADR):

- 横長 / 1:1 / 1080p 60fps 用 stream マスター
- live streaming
- 音声 only (ポッドキャスト形式) ※必要なら別 graph
- 商用 BGM ライブラリ (AudioCraft Music / Suno API) — license 上 monetize 阻害
- HunyuanVideo / CogVideoX 採用 — 既存 Wan で十分、増設 VRAM 圧迫を避ける

## Executive Summary

| 項目 | 採用 |
|---|---|
| Keyframes | SDXL `animagine-xl-4.0` (既存 `scene_bulk_seed`) を 5 枚生成 |
| I2V | **Wan 2.2 I2V 14B fp8** (既存 `shinshi_video.py` primitive をそのまま 5 回呼ぶ) |
| Voice (JP) | **Style-Bert-VITS2** + character speaker LoRA |
| BGM | **Stable Audio Open** (MIT relicensable) |
| SFX | **AudioLDM2-Music** (transitions のみ、4 cue) |
| Mux | ffmpeg + libass (concat + xfade + amix + drawtext + loudnorm -14 LUFS) |
| 出力 | H.264 1080×1920 @ 30fps, ~10-15MB / 25s clip |
| 配置 | visual = LAN 192.168.1.22、audio = SJC `mitama-udf` Python pod (CPU 中心、MusicGen を回す pod だけ GPU) |
| Throughput | 1 clip ≈ 10 min (cold) / 8 min (warm) |

## Decision

### D1. Graph 構造 (`shinshi.video.tiktokShort`)

```
plan_script
   ├─ LLM (vLLM tier0): model profile + scene labels → JSON script
   │  {hook_text, payoff_text, shots:[5×{keyframe_prompt, motion_prompt,
   │   duration, caption_jp}], bgm_brief, voice_text_jp}
   ↓
keyframes  (parallel 5)
   ├─ scene_bulk_seed の build_anime/photoreal workflow をそのまま、
   │   解像度を 768×1344 vertical に固定
   ↓
i2v_shots  (sequential 5, 既存 Wan 2.2 i2v primitive)
   ├─ each keyframe → 4s @ 24fps 1280×720 vertical mp4
   ├─ 連続性は IPAdapter で前 shot last frame を注入
   ↓ ┐
voice_synth  (Style-Bert-VITS2, ~20s narration)
   ↓ ┤
bgm_synth   (Stable Audio Open, 25s, mood = bgm_brief)
   ↓ ┤
sfx_synth   (AudioLDM2-Music, ×4 transition cues)
   ↓ ┘
quality_gate  (motion smoothness + duration ≈ 25s ±2 + LUFS in [-16,-12])
   ↓
mux_compose   (ffmpeg)
   ↓
blob_upload   (PDS uploadBlob video/mp4)
   ↓
pds_post      (feed.post + embed.video + selfLabels:[nsfw,sexual])
```

**Checkpoint**: `thread_id = f"{slug}:tiktok:{epoch_30m}"`。Wan 2.2 が落ちても per-shot で resume。

### D2. Shot タイミング (25s baseline)

| t (s) | duration | shot | 内容 | overlay |
|---|---|---|---|---|
| 0.0 | 1.5s | HOOK | full body close-up, dramatic pose | drawtext "見て" or character handle |
| 1.5 | 4.5s | SHOT 1 | cosplay reveal, full body | voice opening |
| 6.0 | 4.5s | SHOT 2 | close-up portrait, expression | voice continuation |
| 10.5 | 4.5s | SHOT 3 | action / dynamic pose | none |
| 15.0 | 4.5s | SHOT 4 | environment / B-roll | small caption |
| 19.5 | 3.0s | SHOT 5 | climax pose | drawtext outro |
| 22.5 | 2.5s | CTA | static frame | "follow @{handle}" |

`xfade` で 0.3s クロスフェード、6 segments × ~4s ≈ 25s。

### D3. Model 採用根拠

#### D3.1 I2V: Wan 2.2 14B fp8

- 既に LAN ComfyUI に配線済み (`kotodama.primitives.shinshi_video`)
- Apache 2.0、商用 OK
- 4-6s @ 720×1280 が GPU 1 枚で実用域
- HunyuanVideo 13B も候補だが VRAM 重く mangaka と競合悪化

#### D3.2 Voice: Style-Bert-VITS2

- Apache 2.0
- 日本語キャラ音声 zero-shot + speaker LoRA
- CPU でも 20s 文を ~10s で合成 (Mac M-series で実測級)
- VOICEVOX は商用利用条件がキャラごとに違うため自動運用には不向き
- F5-TTS は英語/中国語特化、日本語は二番手

#### D3.3 BGM: Stable Audio Open

- Stability AI、MIT 化可能 (community release)
- 30s 程度のループ生成が可能 (~6GB VRAM)
- MusicGen-medium は **CC-BY-NC** で monetize 阻害 → 採用見送り
- Suno / Udio API は外部依存 + NSFW 制限

#### D3.4 SFX: AudioLDM2-Music

- transitions (whoosh / shutter / impact) 4 cue
- 1-2s クリップ、cache 化可能 (固定 4 種を pre-render)

#### D3.5 Mux: ffmpeg + libass

- 既存 Python pod の依存に追加
- `xfade`, `amix`, `loudnorm`, `drawtext`, `subtitles=ass` で完結
- WebCodecs / WASM 代替は要らない (server side で十分)

### D4. 配置 (placement)

| サブシステム | 場所 | 理由 |
|---|---|---|
| Keyframes (SDXL) | LAN 192.168.1.22 ComfyUI | 既存配線、warm cache |
| I2V (Wan 2.2) | LAN 192.168.1.22 ComfyUI | 同上 |
| Voice (Style-Bert-VITS2) | SJC `mitama-udf` Python pod (CPU) | LAN GPU 開放、CPU で十分 |
| BGM (Stable Audio Open) | SJC `mitama-udf` GPU pod (新規 or 共用) | GPU 必須、LAN と分離して mangaka と競合避ける |
| SFX (AudioLDM2) | SJC GPU pod (BGM 同居 OK) | 同上 |
| Mux (ffmpeg) | LangGraph node 内 (`lg-shinshi` pod CPU) | 軽い |

**主な分割理由**: mangaka が LAN ComfyUI を継続的に使うため、shinshi の I2V 以外を SJC 側に逃がす。

### D5. NSFW labeling

- `app.bsky.feed.post` `labels.selfLabels`: `["nsfw", "sexual"]` (既存 `_post_scene` 規約継承)
- caption (`drawtext`) は age-restrict 文言を含めない (アルゴリズム的にショート上位露出を妨げる) — selfLabel で抑制し、yoro 側の `ContentLabel.svelte` が age gate を担う
- voice 内容も NG word filter を通す (LLM プロンプトで guardrail)

### D6. Quality gate

| 指標 | 合格基準 |
|---|---|
| Duration | 22.5 ≤ d ≤ 27.5s |
| Loudness | -16 LUFS ≤ integrated ≤ -12 LUFS (TikTok 推奨域) |
| Motion smoothness | per-shot mean optical flow magnitude in [2.0, 20.0] (静止 / 暴れ過ぎを弾く) |
| Audio peak | true peak ≤ -1 dBTP |
| Voice intelligibility | Whisper transcribe → CER ≤ 25% (LangGraph node 内) |
| File size | ≤ 50MB (PDS uploadBlob 上限) |

不合格時は `quality_gate=quarantine`、`error=quality-quarantine:{reasons}`。

### D7. Capacity / cost

Single clip (25s, cold cache):

| Stage | Time | GPU | Notes |
|---|---|---|---|
| plan_script (LLM) | 2-4s | shared | vLLM tier0 |
| 5× keyframes (SDXL) | 5×20s = 100s | LAN | parallel possible |
| 5× I2V (Wan 2.2) | 5×90s = 450s | LAN | sequential, queue contention with mangaka |
| voice_synth (VITS2) | 10-15s | CPU | |
| bgm_synth (Stable Audio Open) | 30-45s | SJC GPU | |
| sfx_synth (AudioLDM2) | 4×5s = 20s | SJC GPU | cacheable |
| mux | 8-12s | CPU | |
| upload + post | 3-5s | — | |
| **Total cold** | **≈10 min** | | |
| **Warm cache** | **≈8 min** | | model swap saved |

Daily target: 247 models × 1 clip = 247 clips。LAN GPU 1 枚 24h で
理論最大 144 clips / day (10 min slot)。**2 日に 1 ローテーション** が現実線。
重要 model のみ毎日生成 + tail は週次に分散させる cron policy が必要。

容量: 1 clip 12MB × 247 = ~3GB / round-trip。月 ~45GB の追加 blob。

## Comparison / Rationale

### 視覚モデル

| 候補 | License | VRAM | 品質 | 採用 |
|---|---|---|---|---|
| **Wan 2.2 I2V 14B fp8** | Apache 2.0 | 14GB | 720p smooth | **✓** |
| HunyuanVideo 13B | Apache 2.0 | 24GB+ | 1080p best | ✗ (VRAM 圧迫) |
| CogVideoX-5B | Apache 2.0 | 12GB | 720p ok | ✗ (Wan 上位) |
| LTX-Video | Open RAIL | 8GB | 速いが低品質 | ✗ |
| AnimateDiff v3 | varies | 4GB | SDXL ベース ok | ✗ (短尺 + 連続性弱い) |
| Runway / Kling API | proprietary | — | 最高 | ✗ ($/clip + NSFW NG) |

### Voice モデル

| 候補 | License | 日本語 | キャラ造形 | 採用 |
|---|---|---|---|---|
| **Style-Bert-VITS2** | Apache 2.0 | ✓ | speaker LoRA + emotion | **✓** |
| VOICEVOX | character ごと | ✓ | 商用条件複雑 | ✗ |
| GPT-SoVITS | MIT | ✓ | zero-shot clone | △ (clone 元の権利問題) |
| F5-TTS | CC-BY-NC | 二番手 | zero-shot clone | ✗ (NC) |
| Bark | MIT | 一応 | 非言語 OK | ✗ (品質ムラ) |
| XTTS-v2 | non-commercial | ok | clone | ✗ (NC) |

### BGM モデル

| 候補 | License | 品質 | 30s ループ | 採用 |
|---|---|---|---|---|
| **Stable Audio Open** | community / MIT 化可 | 良 | ◯ | **✓** |
| MusicGen-medium | CC-BY-NC | 高 | ◯ | ✗ (monetize NG) |
| MusicGen-small | MIT | 中 | ◯ | △ (品質劣る、fallback) |
| AudioLDM2-Music | CC-BY-NC | 中 | ◯ | ✗ (SFX のみ採用) |
| Suno / Udio API | proprietary | 最高 | ◯ | ✗ (NSFW NG + $) |

## Exceptions

- 既存 `video_render` graph (単発 i2v 1 clip) は維持。本 ADR は **追加 graph**
  `shinshi.video.tiktokShort` を提供するもので、置き換えではない。
- LAN ComfyUI が落ちたら graph 全停止 (single host)。冗長化は本 ADR スコープ外
  (`mitama-shinshi-pool` 復活 or SJC GPU pod を fallback として用意するのは別 ADR)。
- 既存 `scene_bulk_seed` の 5 scene labels は **静止画用** に最適化されている。
  TikTok graph は **shot script generator** が別途 5 shot を組み立てる
  (動きやすい構図、cosplay reveal の順序、hook 適性) ため、静止画 labels の流用は
  prompt seed としてのみ。

## Implementation outline (follow-up)

1. **Lexicon JSON** を 4 件作成 (`00-contracts/lexicons/com/etzhayyim/apps/shinshi/`):
   - `videoTikTokGenerate.json` (procedure, input: slug + style + duration)
   - `videoTikTokGet.json` (query, input: postUri)
   - `videoTikTokScript.json` (record schema, 5-shot script payload)
   - `videoTikTokLabel.json` (record, NSFW + caption metadata)
2. **lg-shinshi**:
   - 新 graph `lg_shinshi/graphs/video_tiktok_short.py`
   - `langgraph.json` の `graphs` に追加
3. **kotodama**:
   - `primitives/shinshi_voice.py` (Style-Bert-VITS2 client + speaker LoRA cache)
   - `primitives/shinshi_bgm.py` (Stable Audio Open client)
   - `primitives/shinshi_mux.py` (ffmpeg helpers + caption ass writer)
4. **SJC pod**:
   - 新 helm chart or `mitama-udf-pool` 拡張で Stable Audio Open + AudioLDM2 を GPU pod に追加
   - Style-Bert-VITS2 は CPU sidecar
5. **Quality gate**:
   - `quality.py` に `score_video_bytes` 追加 (Whisper CER + LUFS + optical flow)
6. **CF Worker (shinshi appview)**:
   - feed が `embed.video` を resolve できることを確認 (`50-infra/cloudflare/workers/atproto/src/pds-app.ts` の `resolveEmbed` で `app.bsky.embed.video` ハンドリング済)
7. **deps.toml**:
   - `[[migrations]] shinshi-tiktok-video-pipeline` を追加して P0-P4 タスクトラッキング

## References

- ADR-2605010000: RunPod 6000 Ada Unified Pod (現行 LLM/I2V 配置)
- ADR-2605180000: lawfirm Product Focus BMC Lean (shinshi P2 位置付け)
- ADR-2605211800: mangaka Native ComfyUI Page Pipeline (LAN ComfyUI 共用先)
- `60-apps/etzhayyim-project-shinshi/lg/CLAUDE.md`: 既存 lg-shinshi 配線
- `60-apps/etzhayyim-project-shinshi/CLAUDE.md`: shinshi 全体 (write path / blob / ContentLabel)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/shinshi_video.py`: 既存 Wan 2.2 I2V primitive
- Wan 2.2 weights: Alibaba PAI, Apache 2.0
- Style-Bert-VITS2: <https://github.com/litagin02/Style-Bert-VITS2>
- Stable Audio Open: Stability AI community release
- TikTok video specs: 9:16, ≤ 60s, H.264, AAC, ≤ 287.6 Mbps (実用 1080×1920 / 30fps / ~10 Mbps)
