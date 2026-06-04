---
id: adr-2605202225-mangaka-comfyui-langgraph-pipeline
title: "mangaka.etzhayyim.com — ComfyUI Generation Pipeline via LangGraph + Studio Embed"
status: active
doc_type: adr
topic: mangaka-comfyui-pipeline
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - mangaka.etzhayyim.com image / 3D / video / page generation pipeline
  - studio.etzhayyim.com → ComfyUI dispatch contract
  - LangGraph wrapper convention for ComfyUI workflows (build → submit → poll)
  - ComfyUI workflow library install convention (`scripts/install-mangaka-comfy-workflow.py`)
  - Quality-pack install convention (`scripts/install-comfy-quality-pack.ps1`)
priority: 8.0
axis: pipeline
weight: 0.80
priority_note: |
  Mangaka domain pipeline maps every record kind (character, environment,
  panel, page, video, 3D asset) onto either (a) a typed LangGraph wrapper
  that builds an API-format ComfyUI workflow JSON and dispatches it, or
  (b) a native ComfyUI workflow JSON installed in the user's workflow
  library so the artist can edit it in the embedded ComfyUI tab.
implementation_notes: |
  Tier 1+2+3 install executed on 192.168.1.70 (Windows 11 Pro, NUCBOX_EVO-X2,
  AMD Radeon 8060S, ROCm 7.2.1, ComfyUI 0.21.1, Python 3.12.10) on 2026-05-21
  via SSH key auth (Mac id_ed25519 -> Windows administrators_authorized_keys).
  Quirks captured by repair scripts (lg/scripts/repair-tier2.ps1 lineage):
   - install-comfy-quality-pack.ps1 needed non-ASCII chars stripped for PowerShell 5
     Shift-JIS console (commit 723e1febb53).
   - Windows OpenSSH on the host does NOT bundle git, so the IPAdapter custom node
     was fetched as a release zip instead of `git clone`.
   - InsightFace antelopev2 URLs from MonsterMMORPG/tools 404; switched to the
     official deepinsight/insightface v0.7 release zip.
   - `insightface` Python package needs Visual C++ to build from source (no
     compiler on this host) — installed via the Gourieff/Assets precompiled
     wheel insightface-0.7.3-cp312-cp312-win_amd64.whl.
   - Wheel was built against numpy 1.x; with numpy 2.4.4 the import surfaced
     `numpy.dtype size changed` ABI error. Downgraded to numpy 1.26.4 — opencv /
     tifffile emit pip dep warnings but still work at runtime.
   - cv2.pyd locked while ComfyUI was running; pip install needed a stop -> install
     -> relaunch cycle. SSH-spawned children inherit the SSH session and die on
     disconnect, so the relaunch goes through a one-shot Scheduled Task
     (`ComfyUI-OneShot`, schtasks /sc ONCE + /run trick) for true detachment.
   - IPAdapter UnifiedLoader "PLUS" preset needs CLIP-ViT-H-14-laion2B-s32B-b79K
     (~2.4 GB), not just the CLIP-ViT-bigG-14 the script installs.
   - panel_hq end-to-end verified: yuki ref -> Illustrious-XL-v0.1 + IPAdapter
     PLUS (weight 0.55) + ControlNet Union Canny (strength 0.35) ->
     1024x1536 PNG in 67s, character identity preserved (visor + bob cut + cyan
     palette).
   - Tier 5 (anime quality stabilization, 2026-05-21): PuLID v1.1 + Pony
     Diffusion V6 XL (LyliaEngine mirror) + sdxl-vae-fp16-fix + Flux.1 [dev]
     Q4_K_S GGUF + T5XXL fp8 + CLIP-L + Flux VAE (Comfy-Org Lumina
     repackage — BFL gate workaround) + ComfyUI-GGUF + TRELLIS + CharacterGen
     custom nodes. PuLID needs facexlib/timm/einops/ftfy/filterpy/lmdb pip,
     installed --no-deps to dodge opencv conflict. WAI-NSFW-Illustrious +
     AutismMix Pony are Civitai-exclusive (HF mirrors gated/404) — skip.
     Flux smoke verified: 1024x1536 manga ink in 180s, dramatically cleaner
     than SDXL pipeline.
depends_on:
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
related:
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605152100-etzhayyim-github-org-boundary
supersedes: []
superseded_by: []
---

# Context

mangaka.etzhayyim.com produces three artefact families per the existing record
schema (`com.etzhayyim.mangaka.{character,environment,panel,page,asset,...}`):

- **2D images** at three scopes — character design sheet, environment
  establishing shot, single panel, whole page.
- **3D models** for re-pose / camera-controlled reference (`asset` kind).
- **Short animation clips** for chapter PVs.

Prior to this ADR every stage of the kami-cine pipeline
(`cine_generate_scene` / `cine_generate_panel`) was synthetic — the
LangGraph nodes wrote stub CIDs and only the diffusionPass at stage 6
optionally called the production ComfyUI gateway. The studio at
`studio.etzhayyim.com` had no UI binding to the actual ComfyUI workflow editor,
and the gateway path required a sk_live_ API key that not all artists
had minted.

The LAN ComfyUI at `http://192.168.1.70:8188` ships 753 node types
including TripoSR, Hunyuan3D-2, ControlNet, IPAdapter loaders, Hy3D
texturing, multiple SDXL checkpoints (`animagine-xl-4.0`,
`waiIllustriousSDXL_v160`). This is enough surface to drive every stage
end-to-end without the gateway, provided we (a) bind LangGraph to the
ComfyUI HTTP API directly, (b) make the workflow JSON SSoT-editable in
the embedded editor, (c) install the higher-quality model packs the
artist needs for production output.

# Decision

## D1 — Three-layer pipeline

| Layer | Wire | Purpose |
|---|---|---|
| **L1 — Studio Svelte SPA** (`studio.etzhayyim.com`) | HTTP `/api/*` → langgraph dev `:2024` | UI: Pregel DAG view (@xyflow/svelte), Mermaid view, embedded ComfyUI iframe view, per-graph Input panel, SSE-driven stage colouring + inline image / video / page gallery. |
| **L2 — LangGraph wrappers** (`lg/lg_mangaka/graphs/*.py`) | LangGraph Pregel + `lg_mangaka.comfy_runner` | Typed dispatch: each graph maps a domain record (character, scene, panel, page, …) onto an API-format ComfyUI workflow JSON via `lg_mangaka.comfy_workflows.<kind>_workflow(...)`. Three super-step pattern: `build → submit → poll`. Page graph adds `plan` (upload shared ref) and `composite` (PIL pasting onto a manga page canvas with bbox layout). |
| **L3 — ComfyUI** (`http://192.168.1.70:8188`) | HTTP `/prompt`, `/history`, `/view`, `/upload/image`, `/userdata/workflows/*` | Workflow execution. The LangGraph workflows above are the same API-format JSON the embedded editor displays after `install-mangaka-comfy-workflow.py` POSTs them into `userdata/workflows/`. |

## D2 — Graph catalogue (31 total registered, 11 mangaka-specific)

Naming convention: `mangaka_generate_{record_kind}[_{variant}]`.

| Graph | Maps to | Pipeline |
|---|---|---|
| `mangaka_generate_character` | `com.etzhayyim.mangaka.character` | 1-pass SDXL, batch_size=N views |
| `mangaka_generate_character_3d` | character + 3D asset (TripoSR) | TripoSR mesh → SaveGLB |
| `mangaka_generate_character_hy3d` | character + 3D asset (Hunyuan3D-2) | Hy3D textured PBR mesh → SaveGLB/USDZ |
| `mangaka_generate_scene` | `com.etzhayyim.mangaka.environment` | 1-pass landscape establishing shot |
| `mangaka_generate_panel` | `com.etzhayyim.mangaka.panel` | 2-pass composition + ink refine (denoise=0.45) |
| `mangaka_generate_panel_stable` | panel + character ref | img2img 2-pass from encoded ref latent |
| `mangaka_generate_panel_hq` | panel + character ref | IPAdapter FaceID v2 + ControlNet Union (canny) + empty latent — true identity preservation |
| `mangaka_generate_page` | `com.etzhayyim.mangaka.page` | plan → render every panel → PIL composite |
| `cine_generate_scene` | kami-cine stages 1-4 | (legacy) USD / neural geom stubs + ComfyUI preview |
| `cine_generate_panel` | kami-cine stages 5-6 | (legacy) panel render + diffusion refine |
| `cine_generate_video` | N-frame batch | per-frame Send fan-out + ffmpeg encode |
| `comfy_run` | (passthrough) | raw API-format workflow JSON → /prompt |

The `_hq` variant supersedes `_stable` for production once the Tier 1+2
quality pack is installed (ControlNet Union + IPAdapter FaceID v2).

## D3 — Workflow library installation

`scripts/install-mangaka-comfy-workflow.py` POSTs GUI-format workflow
JSON to ComfyUI's `userdata/workflows/` endpoint. Installs four files:

- `mangaka-cine.json` (alias `mangaka-panel.json`) — 12-node 2-pass panel
- `mangaka-character.json` — 7-node character sheet, batch=2
- `mangaka-scene.json` — 7-node establishing-shot

Workflows show up in the embedded ComfyUI editor's Workflows panel and
are editable visually. The API-format equivalents are dispatched by the
LangGraph wrappers above — same logical pipeline, two surfaces.

## D4 — Quality pack (Windows ComfyUI host)

`scripts/install-comfy-quality-pack.ps1` is run on the ComfyUI host
(currently `192.168.1.70`, Windows) and downloads / git-clones:

| Tier | Adds | Enables |
|---|---|---|
| 1 | `controlnet-union-sdxl-promax.safetensors` (~2.5 GB) | Canny + Depth + OpenPose + Tile + Scribble — all from one file |
| 2 | IPAdapter Plus + FaceID v2 + InsightFace antelopev2 + CLIP-ViT-bigG + `ComfyUI_IPAdapter_plus` custom node | Face identity preservation across panels |
| 3 | Illustrious-XL v0.1 + NoobAI-XL v1.1 (~14 GB) | Sharper manga line work than animagine-xl-4.0 |
| 4 | Hy3D folder pre-create | Auto-DL of `tencent/Hunyuan3D-2` weights (~6 GB) on first Hy3D queue |

Script is idempotent (skips existing files) and stages installs via
`-Tier 1,2` flags. ComfyUI must be restarted after install.

## D5 — Quality-jump defaults (param-only, no new models)

`comfy_workflows.py` builders use SDXL-native defaults:

| Param | Old | New |
|---|---|---|
| resolution | 832×1216 / 1216×832 | **1024×1536 / 1536×1024** |
| steps | 18-22 | **28-32** |
| sampler | `euler` / `dpmpp_2m` | **`dpmpp_3m_sde_gpu` + `karras`** |
| cfg | 6.5-7.0 | **7.5-8.0** |
| panel_stable base_denoise | 0.65 | **0.5** |
| DEFAULT_CKPT | `animagine-xl-4.0` | **`waiIllustriousSDXL_v160`** (env COMFY_DEFAULT_CKPT override) |
| positive prompts | flat | gain `(masterpiece, best quality)` anchor |
| negative prompts | flat | weighted `(low quality:1.4), (worst quality:1.4), ...` |

Verified end-to-end against the existing `waiIllustriousSDXL_v160`
checkpoint: scene_workflow output went from abstract blob to crisp
anime-illustration in 47 seconds at 1536×1024.

## D6 — Studio UI conventions

- **DAG panel** has three tabs: **Nodes** (@xyflow/svelte Pregel DAG with
  live SSE-driven node colouring + Send fan-out ×N badges), **Mermaid**
  (top-down flow diagram), **ComfyUI** (iframe of the ComfyUI editor at
  `?comfy=` override; defaults to `http://192.168.1.70:8188`).
- **Input panel** has per-graph `DEFAULT_INPUTS` skeletons keyed on
  `graph_id`; updated when the artist clicks a graph in the sidebar.
- **Stages panel** renders the SSE updates stream — each delta becomes
  a stage card. The `preview()` function recognises four payload shapes:
  `panel_results[].imageInlineB64` (per-panel galleries),
  `videoInlineB64` (mp4 player), `page_image_inline_b64` (composited
  page), and `images[]` (raw comfy_run outputs).
- **SSE block splitter** uses `/\r?\n\r?\n/` to handle the CRLF
  separators langgraph dev emits — was the silent failure that made
  stages appear stuck in `pending` despite work completing.

# Consequences

## Positive

- Every mangaka domain record kind has a named LangGraph graph that
  takes the record's fields verbatim and dispatches to ComfyUI; the
  artist no longer has to write workflow JSON by hand.
- The same workflow JSON lives in two places (LangGraph builder +
  ComfyUI workflow library) but is generated by the same Python
  template — single source of truth.
- Page composition produces a finished 1280×1817 manga page from a
  panels list in ~13 s/panel + ~50ms composite.
- Quality jump from the param-only changes alone delivered a visible
  improvement; the install pack unlocks the next tier (identity
  consistency, ControlNet-anchored composition).

## Negative

- LangGraph wrappers and the GUI workflow files can drift if a
  ComfyUI-side edit isn't reflected back into `comfy_workflows.py`.
  Mitigated by treating the Python builder as the source of truth and
  re-running `install-mangaka-comfy-workflow.py` after any change.
- The PowerShell install script assumes the operator runs it on the
  ComfyUI host directly (no remote shell). Manager-API path is blocked
  because ComfyUI-Manager isn't installed.
- Hy3D / Hunyuan3D auto-DL happens lazily on first node use — a 6 GB
  download can stall a Studio Run for several minutes. Pre-warming
  Tier 4 is recommended before the first artist session.

## Operational

- Studio backend = `langgraph dev` (in-memory checkpointer, port 2024).
  Production studio pod (`lg-mangaka-studio` in `mitama-udf` namespace)
  is unaffected — same graphs, postgres checkpointer, k8s scheduler.
- ComfyUI host environment variable contract:
  `COMFY_POD_URL` (raw pod), `COMFYUI_URL` (gateway), `COMFYUI_API_KEY`
  (sk_live_ for gateway), `COMFY_DEFAULT_CKPT` (override default).

# Alternatives Considered

1. **Stay on the gateway path** (`comfyui.etzhayyim.com` CF Worker → fleet).
   Rejected: the gateway is a thin OpenAI-compat shim; it can't drive
   IPAdapter, ControlNet, or Hy3D because they require workflow-level
   composition the OpenAI surface doesn't expose. The wrapper-+-direct
   path lets us send arbitrary multi-node workflows.
2. **Generate full pages in a single ComfyUI workflow** (regional
   prompting, tiled diffusion). Rejected for v1: tiled diffusion +
   regional masking pushes the workflow node count past 60 and slows
   debug iteration. PIL composite at the LangGraph layer is faster to
   reason about and lets each panel's seed / framing / character ref
   be independent.
3. **Install ComfyUI-Manager** to drive node + model installs remotely
   via HTTP. Deferred: requires user action to install the manager
   custom node first, and the PowerShell script delivers the same
   outcome with one less step.
4. **Use the existing `cine_generate_*` graphs as the primary path**
   instead of adding the typed `mangaka_generate_*` family. Rejected:
   the cine graphs encode kami-cine's 8-stage pipeline (worldModel
   through encode) which is a heavier abstraction than mangaka needs.
   The typed family is closer to the domain records and renders in
   ~15 s vs the cine graphs' ~30 s.

# References

- `60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/comfy_workflows.py` —
  workflow JSON builders (SSoT).
- `60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/comfy_runner.py` —
  shared submit / poll / upload helpers.
- `60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/graphs/` — 11 typed
  graph files.
- `60-apps/etzhayyim-project-mangaka/lg/scripts/install-mangaka-comfy-workflow.py`
  — workflow library installer (POSTs GUI JSON to ComfyUI).
- `60-apps/etzhayyim-project-mangaka/lg/scripts/install-comfy-quality-pack.ps1`
  — Windows host model + custom-node installer.
- `60-apps/etzhayyim-project-mangaka/appview-studio/etzhayyim-wasm-studio-stdk2024/svelte/src/routes/+page.svelte`
  — Studio SPA.
- `60-apps/etzhayyim-project-mangaka/appview-studio/etzhayyim-wasm-studio-stdk2024/svelte/src/lib/{NodeGraph,PregelNode}.svelte`
  — @xyflow/svelte Pregel DAG renderer.
- `60-apps/etzhayyim-project-mangaka/CLAUDE.md` — mangaka project guide.
- Session commits 8cd1d02 → e4ef249 (8 commits) — incremental landing
  of the pipeline.
