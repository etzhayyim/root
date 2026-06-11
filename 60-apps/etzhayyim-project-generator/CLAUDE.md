# etzhayyim-project-generator

Multimodal AI Content Generator — text, text-to-image (t2i), text-to-video (t2v), and image-to-video (i2v) generation via OpenRouter integration.

**URL**: `https://generator.etzhayyim.com`

## Architecture

```
Browser (generator.etzhayyim.com)
  ├─ HTML/JS/CSS → generator.etzhayyim.com (static delivery)
  └─ API → etzhayyim.com/g3nrt0rx/xrpc → Envoy Gateway
              ↓
       App: generator-component (TS Native)
              ├─ text-gen → openrouter-provider (cluster-internal :21090)
              ├─ image-gen → OpenRouter image models (DALL-E 3, SDXL, Flux)
              ├─ video-gen → OpenRouter video models (Veo 2, Sora, Runway)
              └─ animate-gen → OpenRouter animate models (SVD, Kling)
```

## Components

| Component | Type | Nanoid | Endpoint |
|-----------|------|--------|----------|
| `etzhayyim-wasm-generator-g3nrt0rx` | TS Native App | `g3nrt0rx` | `https://etzhayyim.com/g3nrt0rx/xrpc` |

## WIT Interfaces

Source of truth: `60-apps/etzhayyim-project-generator/wit/generator/package.wit`

| Interface | Package | Description |
|-----------|---------|-------------|
| `text-gen` | `etzhayyim:generator@0.1.0` | Chat completions via OpenRouter |
| `image-gen` | `etzhayyim:generator@0.1.0` | Text-to-image (t2i) generation |
| `video-gen` | `etzhayyim:generator@0.1.0` | Text-to-video (t2v) async generation |
| `animate-gen` | `etzhayyim:generator@0.1.0` | Image-to-video (i2v) async animation |

## OpenRouter Integration

Text generation routes through the cluster-internal `openrouter-provider` at `http://openrouter-provider.kotodama-system.svc.cluster.local:21090/v1`.

Image/video generation calls OpenRouter multimodal endpoints directly via `wasi:http/outgoing-handler` with the API key from `wasi:config/store`.

### Native Provider

- Location: `60-apps/etzhayyim-project-generator/provider/openrouter/`
- Exports: `etzhayyim:openrouter/chat@0.1.0`
- Namespace: `kotodama-runtime`

### Default Models

| Modality | Model | Provider |
|----------|-------|----------|
| text | `anthropic/claude-sonnet-4-6` | OpenRouter → Anthropic |
| t2i | `openai/dall-e-3` | OpenRouter → OpenAI |
| t2v | `google/veo-2` | OpenRouter → Google |
| i2v | `stability/stable-video-diffusion` | OpenRouter → Stability AI |

## Proto Definition

`proto/etzhayyim/generator/v1/generator.proto` — synced from WIT (WIT is source of truth).

## KV Key Schema

| Key Pattern | Value |
|-------------|-------|
| `gen:task:{taskId}` | Async generation task state (t2v/i2v) |
| `gen:task-idx:{orgId}` | Task index per org |
| `gen:asset:{assetId}` | Generated asset metadata |

## Directory Structure

```
60-apps/etzhayyim-project-generator/
├── CLAUDE.md
├── PROJECT.jsonld
├── OWNERS
└── wasm/etzhayyim-wasm-generator-g3nrt0rx/
    ├── wit/world.wit
    ├── deploy config
    └── proto/                          # Symlink or copy from proto/etzhayyim/generator/v1/
```

## Static Delivery

- Domain: `generator.etzhayyim.com`
- `svelte/build/` は fileserver component に同梱して static delivery で公開

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-generator/wasm/etzhayyim-wasm-generator-g3nrt0rx
etzhayyim build
etzhayyim deploy --smoke-url https://g3nrt0rx.etzhayyim.com/health
```

## Conventions

- **pnpm** only (never npm)
- Tailwind CSS + `@etzhayyim/design-system` + `@etzhayyim/appshell`
- Auth headers: `Authorization: Bearer <JWT>`, `X-etzhayyim-ORG-ID`, `X-etzhayyim-USER-ID`
- XRPC-first: no hardcoded nanoid URLs
- Async operations (t2v/i2v): submit → poll pattern with KV-backed state
