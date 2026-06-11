# etzhayyim-project-awai

**URL**: https://awai.etzhayyim.com
**Performer ID**: `ku9ndz8y`
**Port**: 21090

## Overview

Earth-scale 3D Gaussian Splatting viewer. WebP images → SfM → 3DGS training → PLY/splat/ksplat output → kotodama WIT storage → Threlte (Three.js + Svelte) globe rendering.

## Architecture

```
Browser (awai.etzhayyim.com)
  ├─ HTML/JS/CSS → awai.etzhayyim.com (static delivery)
  └─ API → 1.etzhayyim.com/xrpc → Envoy Gateway
              ↓
       App: awai-component (TS Native)
              ├─ performer/rdbms (ClickHouse RDBMS) → awai-splat-meta (splat/job/placement metadata)
              ├─ NATS Object Store  → awai-splat-data (PLY/splat/ksplat binary)
              └─ kotodama fileserver    → svelte/build bundled static assets
```

## Component

| Component | nanoid | World | Port | Image |
|---|---|---|---|---|
| awai-component | ku9ndz8y | etzhayyim-gaussian-splat-provider | 21090 | ghcr.io/etzhayyim/awai-component |

## WIT Interface

**Source of Truth**: `60-apps/etzhayyim-project-awai/wit/gaussian-splat/package.wit`

```
etzhayyim:gaussian-splat@0.1.0
├─ interface types       — training-status, splat-format, geo-coordinate, quaternion, geo-bounds, ...
└─ interface gaussian-splat
    ├─ upload-images       — WebP batch upload → image-batch
    ├─ start-training      — image-batch → training-job (SfM + 3DGS)
    ├─ get-training-status — poll training progress (0-100%, PSNR)
    ├─ cancel-training     — abort running job
    ├─ get-splat           — fetch splat metadata by ID
    ├─ list-splats         — filtered listing with pagination
    ├─ delete-splat        — remove splat + data
    ├─ download-splat      — get binary data (PLY/splat/ksplat)
    ├─ place-splat         — geo-place splat (WGS84 + quaternion + scale)
    ├─ list-placements     — spatial query (bounding box, visibility)
    ├─ remove-placement    — unplace from scene
    └─ update-placement    — move/rotate/scale placement
```

## Proto (XRPC)

`proto/etzhayyim/awai/v1/awai.proto` — synced from WIT.
`buf generate` → Connect-ES TypeScript client for Svelte frontend.

## Storage Layout

### KV State (ClickHouse RDBMS)

| Key pattern | Value |
|---|---|
| `batch:{batch-id}` | JSON: image-batch metadata |
| `job:{job-id}` | JSON: training-job state |
| `splat:{splat-id}` | JSON: splat metadata |
| `placement:{placement-id}` | JSON: placement with geo-coordinate |
| `idx:splat:label:{prefix}` | JSON: splat ID index by label |
| `idx:placement:splat:{splat-id}` | JSON: placement IDs for a splat |
| `idx:placement:geo:{tile-key}` | JSON: placement IDs in geo tile |

### NATS Object Store (bucket: `awai-splat-data`)

| Key pattern | Content |
|---|---|
| `img:{batch-id}/{n}.webp` | Raw WebP input images |
| `splat:{splat-id}.ply` | PLY point cloud output |
| `splat:{splat-id}.splat` | Compressed splat format |
| `splat:{splat-id}.ksplat` | Compressed ksplat format |

## Frontend (Threlte)

Svelte + Threlte (Three.js) application:

- **Globe renderer**: Earth sphere with satellite/aerial imagery tiles
- **Splat renderer**: `@mkkellogg/gaussian-splats-3d` or `gsplat.js` for WebGL Gaussian Splat rendering
- **Geo-placement**: WGS84 → Three.js coordinate transform (ECEF)
- **Camera controls**: OrbitControls with smooth zoom from globe to street level
- **Upload UI**: Drag-and-drop WebP images → batch upload → training progress
- **Placement editor**: Click-to-place splats on globe, drag/rotate/scale handles

### Key Svelte dependencies

```
@threlte/core        — Three.js + Svelte integration
@threlte/extras      — Orbit controls, helpers
three                — Three.js core
@mkkellogg/gaussian-splats-3d — WebGL Gaussian Splat renderer
@connectrpc/connect-web       — XRPC-Web client
```

## Capabilities

| Capability | Purpose |
|---|---|
| wasi:http/incoming-handler | Serve HTTP requests |
| wasi:http/outgoing-handler | External API calls |
| performer/rdbms | ClickHouse RDBMS backing table |
| etzhayyim:store/store | Object store (bucket: awai-splat-data) |
| etzhayyim:cdn/cdn | CDN provider (legacy, retired) |

## Build & Deploy

```bash
# Build Svelte frontend
cd 60-apps/etzhayyim-project-awai/wasm/etzhayyim-wasm-awai-ku9ndz8y/svelte
pnpm install && pnpm build

# Build + Push + Deploy
cd ..
etzhayyim build
etzhayyim deploy --smoke-url https://awai.etzhayyim.com/health
```

## Prohibitions

- XRPC for inter-component calls
- `go:embed static` — use static delivery bundled static delivery
- Independent CSS — use Tailwind + @etzhayyim/design-system only
