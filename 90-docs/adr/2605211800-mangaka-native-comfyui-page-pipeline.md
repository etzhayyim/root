---
id: adr-2605211800-mangaka-native-comfyui-page-pipeline
title: "mangaka — ComfyUI-Native Page Pipeline (custom nodes + universal renderer + surgical patch)"
status: active
doc_type: adr
topic: mangaka-native-page-pipeline
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - Mangaka custom ComfyUI nodes (Mangaka* family)
  - Universal arc-page renderer (render-arc01-page.py)
  - LangGraph wrap (mangaka_render_episode_page)
  - Surgical per-panel patch workflow
  - Vertical Japanese bubble + corner anchor + stub tail convention
  - Right-to-left manga reading-order layout
  - Per-character LoRA chain selection per panel
priority: 8.5
axis: pipeline
weight: 0.85
extends:
  - adr-2605202225-mangaka-comfyui-langgraph-pipeline
priority_note: |
  This ADR captures the SECOND half of the mangaka pipeline: how to
  go from "a folder of installed ComfyUI nodes + checkpoints" (ADR
  2605202225) to "a printable manga page that reads as a real
  Japanese comic." The path is to build the page as ONE ComfyUI
  workflow — generate every panel, composite them onto a page
  canvas, then layer vertical-Japanese speech bubbles + manga SFX
  + UI mockups on top via project-specific custom nodes. The
  workflow is parametric: a universal renderer reads the
  ghost-hacker arc 0-1 manifest and emits the workflow for any of
  46 pages. A LangGraph node exposes the renderer to Studio.
implementation_notes: |
  Custom node pack (60-apps/etzhayyim-project-mangaka/lg/comfy_custom_nodes/
  MangakaTextOverlay/) installed by
  lg/scripts/install-mangaka-text-overlay-node.ps1 +
  lg/scripts/install-mangaka-ec-mockup.ps1 +
  lg/scripts/install-mangaka-phone-paste.ps1. All nodes are PIL-based
  (no model load), pure Python on the ComfyUI host's embedded
  python_embeded interpreter. Node list:

    MangakaPageCanvas        blank A4 manga page (1280x1817)
    MangakaPanelPaste        resize+center-crop panel into a page bbox + border
    MangakaTextOverlay       stroked text at (x,y) — simple SFX
    MangakaSpeechBubble      legacy anchor bubble (kept for compat)
    MangakaMangaBubble       v4 — panel-corner anchor, short stub tail,
                              vertical Japanese (auto-wrap into columns
                              flowing right-to-left), 5 styles (normal /
                              shout / thought / whisper / narration),
                              optional overflow past panel edge,
                              centered text, no speaker label, wider
                              column width (font_size+8)
    MangakaSFX               styled SFX — bold Yu Gothic, rotation,
                              stroke, optional radial motion lines
    MangakaECMockup          portrait smartphone screen mockup (phone
                              bezel + notch + status bar + browser
                              chrome + URL bar + screentone-shaded
                              sneaker hero + red countdown + product
                              title + strikethrough price + 5-star
                              widget + CTA button + home indicator)
    MangakaPhoneScreenPaste  paste an EC mockup onto a generated
                              "hands holding phone" panel at a screen
                              bbox with rotation + soft drop shadow

  Universal renderer (lg/scripts/render-arc01-page.py):
    Reads image-gen-manifest.json + character profiles + character
    LoRAs and emits a single ComfyUI workflow JSON for one page.

    compute_layout(panels)
      Group by panelLayout.gh:row; within each row distribute the
      1200px available width by SIZE_UNIT (small=1 / medium=2 /
      large=3 / spread=6). Panels lay out RIGHT TO LEFT so the
      manifest's panel 1 lands at the right of its row.

    panel_prompt(panel, focused_char)
      Stacks: char_tag_prompt(LoRA token) + shot + visual + setting
      (PAGE_ENVIRONMENT[pageNum]) + tone + style. Negative prompt
      filters out "laptop, desktop computer, futuristic device,
      glowing blue rectangle, cyan light box, neon device,
      holographic" to keep insert-shot artifacts in check.

    LoRA chain selection
      Build per-character model_refs (animagine-xl-4.0 + one
      LoraLoaderModelOnly per needed character at strength 0.85).
      Per-panel pick by focusedCharacters[0]; fallback to plain
      checkpoint when no LoRA is registered for the focal character.

    Latin -> katakana
      "Akira" → "アキラ", "Yuto" → "ユウト", "Ren" → "レン",
      "Nei" → "ネイ", "Mei" → "メイ", "Saki" → "サキ", "nue" →
      "ヌエ", "Chise" → "チセ", "Kaname" → "カナメ", "Holonium" →
      "ホロニウム". Applied at bubble emit so 縦書き columns stay
      aligned with constant character width.

    Bubble dimensions for vertical-first manga
      chars_per_col target = 6; min_height = 6 * line_h + padding;
      width = font_size + 8 + 28 (single column baseline). Forces
      a TALL+NARROW silhouette so multi-column right-to-left text
      reads as proper 縦書き instead of horizontal multi-line.

    Bubble auto-place
      Top-right panel -> top-right bubble + down-left tail (toward
      panel centre). Subsequent bubbles in the same panel flip
      top<->bottom. Style = shout if dialogue contains !, ?, !?, !？.

  Surgical per-panel patch
    Re-rolling a single panel without losing the rest of the page:
      LoadImage(prev_page_final)
        -> KSampler new panel
          -> MangakaPanelPaste over the target bbox (erases the
              previous panel + its baked-in bubble)
            -> MangakaMangaBubble fresh on the new panel
              -> SaveImage
    11 nodes, ~25s on AMD Radeon 8060S ROCm 7.2 vs ~100s for a
    full page re-render. Used to fix page 4's panel-2 cyan-glow
    device regression without disturbing panels 1/3/4.

  LangGraph wrap (mangaka_render_episode_page)
    Pregel: plan(page_num 0..45 validation) -> build(import the
    universal renderer via importlib + call build_workflow(n)) ->
    submit -> poll. Returns status / prompt_id / page_filename /
    image_b64 / elapsed_ms / n_panels / n_nodes. Registered in
    both langgraph.json and langgraph.dev.json so Studio (Vultr
    pod) and `langgraph dev` (local) can both list it.

  Resume / batch convention
    The CLI accepts --range a,b,c, --all, --resume (skip pages
    whose /tmp/gh-arc0-1-pNN-final.png already exists), and
    --skip-existing. Used so an LAN ComfyUI host going to sleep
    mid-batch doesn't waste compute on re-renders.

  Verified per-page outputs as of 2026-05-21:
    page 0 (Yuto pre-title hook, 4 panels, env=bedroom)        107s ok
    page 1 (Nei+Ren classroom, 7 panels, env=classroom)        193s ok
    page 2 (sneaker discussion, 8 panels, mixed chars)         203s ok
    page 3 (Ren+Nei street walking, 7 panels, env=city street) 188s ok
    page 4 (Yuto room v12 surgical, 4 panels, smartphone+EC)   ~110s ok
---

# mangaka — ComfyUI-Native Page Pipeline

## Status

active. Authoritative for the second half of the mangaka pipeline (page composition + bubbles + SFX + UI mockups + surgical patch + universal arc renderer + LangGraph wrap). The first half (host install + LoRA training + base custom-node packs) stays in **adr-2605202225-mangaka-comfyui-langgraph-pipeline**.

## Context

ADR-2605202225 left the pipeline at the panel level: each domain record (character / scene / panel / 3D asset / video) had a typed LangGraph wrapper that built a ComfyUI workflow for ONE panel. Composing 4-11 panels into a manga page was a Python post-process on the Mac side — PIL paste + simple text overlay. That worked, but the resulting pages didn't read as Japanese manga: the bubbles were horizontal multi-line, tails extended to character faces, panel size and reading order were uniform, the smartphone EC insert was an abstract paint blob, and the page assembly was happening outside ComfyUI (so it couldn't be re-triggered from Studio).

This ADR records the path that closed the gap: native ComfyUI custom nodes for every manga-specific composition step, a universal page renderer driven by the ghost-hacker arc 0-1 manifest, a LangGraph wrap exposing the renderer to Studio, and a surgical per-panel patch workflow for iterative edits.

## Decision

Build the manga page as ONE ComfyUI workflow. Generate each panel via SDXL + the appropriate per-character LoRA, composite onto a page canvas, then overlay vertical-Japanese speech bubbles + styled SFX + UI mockups via custom Mangaka* nodes. The output PNG is the final page — no Mac-side PIL post-process.

## Pipeline shape (per page)

```
CheckpointLoaderSimple animagine-xl-4.0
   ├── LoraLoaderModelOnly yuto_persona.safetensors @ 0.85
   ├── LoraLoaderModelOnly ren_persona.safetensors @ 0.85
   └── LoraLoaderModelOnly nei_persona.safetensors @ 0.85
                            (per character needed on the page)

per panel (varies by panelLayout.gh:row / gh:size):
   CLIPTextEncode(char tags + shot + visual + setting + tone + style)
   CLIPTextEncode(negative)
   EmptyLatentImage(aspect-aware, 1216x832 for spread/landscape else 832x1216)
   KSampler(model = matching LoRA chain, seed = pageNum*100000 + idx*1009,
            steps=28, cfg=6.0, dpmpp_2m_sde+karras)
   VAEDecode

MangakaPageCanvas(1280x1817)
   for each panel slot computed by compute_layout():
     MangakaPanelPaste(page, panel, x, y, w, h, border_width=3 | 0 for bleed)

MangakaSFX(...) overflow OK             # page-level SFX overlays
MangakaSFX(...) motion lines
...
MangakaMangaBubble(text, panel_x, panel_y, panel_w, panel_h,
                   anchor=corner, tail_dir=stub, width=narrow,
                   min_height=tall, vertical=True, style=normal|shout,
                   outline_width=4, overflow=6)
   for each dialogue on each panel

SaveImage  -> mangaka-page-arc01-pNN_NNNNN.png
```

For the page-4 insert (smartphone EC site), `MangakaECMockup` draws a portrait phone UI in PIL (no SDXL invocation needed) and `MangakaPhoneScreenPaste` composites it onto a "hands holding phone" generated panel with a small rotation + soft drop shadow.

## Composition contract

| Step | Owner | Output |
|---|---|---|
| Layout | `compute_layout(panels)` | per-panel bbox right-to-left |
| Prompt | `panel_prompt()` | char + shot + visual + setting + tone + style |
| Model | per-character LoRA chain at strength 0.85 | conditioned model |
| Bubble place | `_bubble_anchor_for_slot()` + di-stack | corner + tail direction |
| Bubble shape | `MangakaMangaBubble` style enum | normal / shout / thought / whisper / narration |
| SFX place | hard-coded per-page (current) | (x, y) with overflow OK |
| EC mockup | `MangakaECMockup` + `MangakaPhoneScreenPaste` | composited onto panel 3 of page 4 |

## Surgical per-panel patch

Use case: a single panel needs to be re-rolled (e.g. a weird device artifact) without disturbing the others.

```
LoadImage(prev_page_final.png)               # 2 KB metadata
  -> CheckpointLoaderSimple + LoraLoader(target char)
  -> KSampler + VAEDecode                    # one panel
  -> MangakaPanelPaste(page=prev, panel=new, target bbox)
  -> MangakaMangaBubble(repaint at target bbox)
  -> SaveImage
```

11 nodes, ~25 s vs ~100 s for a full page. The panel-2 bubble that was baked into the previous composite is erased by the paste (it sits inside the panel bbox); a fresh one is painted on top.

## Trade-offs / Limitations

| Concern | Status |
|---|---|
| Vertical text rendering with mixed Latin / Japanese | Solved by Latin→katakana substitution at bubble emit time. Edge cases (long Latin runs) still wrap unevenly. |
| Panel 3 web UI (EC site) | Animagine XL is anime-style and can't render readable browser chrome; PIL `MangakaECMockup` replaces SDXL generation for that one insert. |
| LoRA chain non-determinism | Same seed produces ≈ same image on AMD ROCm but with small variance. Hence the "surgical patch" path: load the previous final and only re-roll the panel that needs to change. |
| Multi-character panels (e.g. page 19 Yuto + Ren) | Current renderer picks the first focused character only. Two-LoRA blend at strength 0.5 each is a follow-up. |
| SFX automation | Currently SFX overlays are written per-page in the script. A future pass should derive SFX from `sceneSubject` + `props` (`Notification Sound` + `smartphone` → `ピロン`). |

## Verification

| Page | Panels | LoRA | Env | Time | Notes |
|---|---|---|---|---|---|
| 0 | 4 | Yuto | bedroom night | 107 s | first universal-renderer run |
| 1 | 7 | Nei + Ren | classroom | 193 s | per-panel LoRA select working |
| 2 | 8 | (mixed, fallback) | classroom | 203 s | no LoRA path verified |
| 3 | 7 | Ren + Nei | city street | 188 s | environment hint visible |
| 4 | 4 | Yuto | bedroom + smartphone | ~110 s (v10) / 25 s (v12 surgical) | EC mockup + phone screen paste |

`mangaka_render_episode_page` LangGraph node tested against page 0 — same workflow JSON as the CLI.

## Forward-only

- New ComfyUI custom nodes go under `lg/comfy_custom_nodes/MangakaTextOverlay/nodes.py` and re-install via the host-side `install-mangaka-*.ps1` scripts.
- New per-page environment hints belong in `PAGE_ENVIRONMENT` in `render-arc01-page.py`.
- New character LoRAs: drop the .safetensors into the host's `models/loras/` and add an entry to `CHAR_LORA` in the renderer.
- The Mac-side PIL post-process (`ghost-hacker-arc0-1-p[03|04]*.py`) is deprecated — kept in the repo for reference but new pages should go through the universal renderer.

## Related ADRs

- adr-2605202225-mangaka-comfyui-langgraph-pipeline — install + LoRA training + base custom-node packs (Tier 1-5)
- adr-0036-write-only-derived-architecture — Tier 2 domain writes for the eventual Studio integration
- adr-2605091800-pruning-protocol — when pages get retired / superseded
