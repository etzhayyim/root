# KAMI Engine SDK

Svelte 5 SDK for KAMI Engine applications.

This package contains reusable UI components, headless builders, data presets, and embed helpers used by KAMI Engine apps:

- VRM character viewer components for Svelte
- headless builders for morph, bone, motion, part, voice, and emotion control
- Genko manga editor components and stores
- trackpad and document bridge helpers
- manufacturing and robotics planning helper types/functions
- **Pixar-class scene graph authoring** — OpenUSD + MaterialX + OSL +
  OpenEXR + OCIO + OIIO + OpenVDB + RenderMan (`hdPrman`) /
  Blender Cycles (`cycles-osl`) — emits a `RenderBundle` consumed by
  the kami-cine 8-stage pipeline (ADR-2605231600)

## Install

```bash
pnpm add @etzhayyim/kami-engine-sdk svelte three
```

`three` and `@pixiv/three-vrm` are peer dependencies. Install `@pixiv/three-vrm` when using VRM-specific viewer features.

## Usage

```svelte
<script lang="ts">
  import { VrmViewer, createVrmEngine } from '@etzhayyim/kami-engine-sdk';

  const engine = createVrmEngine();
</script>

<VrmViewer {engine} />
```

Import narrower modules when you only need one surface:

```ts
import { createVrmEngine } from '@etzhayyim/kami-engine-sdk/builders';
import { genkoEmbedHTML } from '@etzhayyim/kami-engine-sdk/genko';
import { kamiTrackpadHTML } from '@etzhayyim/kami-engine-sdk/trackpad';
import type { Document } from '@etzhayyim/kami-engine-sdk/document';
```

### Pixar-class render bundle

```ts
import { buildSceneGraph } from '@etzhayyim/kami-engine-sdk/scene-graph';
import { buildRenderBundle, DEFAULT_AOV_SET } from '@etzhayyim/kami-engine-sdk/render-job';
import { MANGAKA_V5_OCIO } from '@etzhayyim/kami-engine-sdk/ocio';
import { KamiCineClient } from '@etzhayyim/kami-engine-sdk/kami-cine';

const spec = buildSceneGraph({
  scene_slug: 'yuto-bedroom',
  panel_idx: 0,
  shot_cat: 'CU',
  tone_tag: 'contemplative',
  narrative: { focal_character: 'Yuto', overall_tension: 0.3 },
});

const bundle = buildRenderBundle({
  scene_graph: spec,
  manifest: {
    schema_version: 1,
    delegate: 'cycles-osl', // or 'hdPrman' for RenderMan
    resolution: { width: 1216, height: 832 },
    samples_per_pixel: 64,
    seed: 12345,
    camera_prim: '/World/Camera',
    exr: {
      frame_pattern: 'render.####.exr',
      frame_start: 1, frame_end: 1, fps: 24,
      width: 1216, height: 832, compression: 'zip',
      aovs: DEFAULT_AOV_SET.map(aov => ({ aov })),
    },
    ocio: MANGAKA_V5_OCIO,
    encode: { codec: 'h264', container: 'mp4', fps: 24, crf: 18 },
  },
});

const client = new KamiCineClient();
const result = await client.runMangakaPanel(bundle, {
  subject_ref: 'at://mng4k4x1.gftd.ai/ai.gftd.mangaka.page/abc',
  page_rkey: 'abc',
  prompt: 'Yuto reading at desk, late night, warm lamp',
  panels: [{ panel_rkey: 'panel-0' }],
});
```

The bundle wraps an emitted USDA 1.0 stage, a MaterialX 1.39 XML
material network, OSL shader bindings (catalog refs only — `.osl`
sources live on the render pod), OpenVDB asset references,
OpenEXR multi-layer AOV spec, OCIO display transform chain, and
OpenImageIO post-op pipeline. The `RenderJobManifest.delegate` field
switches between `hdPrman` (Pixar RenderMan), `cycles-osl` (Blender
Cycles with OSL — license-free substitute), `hdStorm` (USD preview),
`hdEmbree` (CPU ray tracer), and the mangaka v5 `comfyui-controlnet`
path. See ADR-2605231600 for the full design.

## Development

```bash
pnpm install
pnpm run check
pnpm run test
pnpm run build
```

The build uses `svelte-package` and writes `dist/`.

## License

Apache-2.0
