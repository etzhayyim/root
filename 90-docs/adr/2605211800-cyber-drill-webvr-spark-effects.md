---
id: adr-2605211800-cyber-drill-webvr-spark-effects
title: "cyber-drill VR — Spark Gaussian backdrop + per-node visual effects + narration-gated choice reveal"
status: active
doc_type: adr
topic: cyber-drill-webvr-visual-stack
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - cyber-drill.etzhayyim.com VR visual stack (room shell + spark backdrop + per-node effects)
  - choice-card reveal UX contract (narration-gated, fade-in + scale pop)
  - selection deadline policy (30s post-narration, inaction auto-fire)
  - cyber-drill scenario authoring contract (IncidentNode.effects)
  - @etzhayyim/kami-engine-sdk/webvr public surface for incident drills
  - @etzhayyim/kami-engine-sdk/spark scene-attachable splat layer API
priority: 7.4
axis: experience-pipeline
weight: 0.74
priority_note: |
  cyber-drill is the first vendor product riding the kami-cine 8-stage
  pipeline end-to-end at a non-trivial visual fidelity. The visual stack
  decisions baked here (toon room + Gaussian backdrop + per-node effects +
  narration-gated UX) are the contract every subsequent scenario inherits.
depends_on:
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605092800-kami-gsplat-preview-bake-pipeline
  - adr-2605202225-mangaka-comfyui-langgraph-pipeline
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
related:
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
supersedes: []
superseded_by: []
---

# Context

`60-apps/etzhayyim-project-cyber-drill/` ships smartphone-first WebVR OT
cybersecurity training scenarios on top of `@etzhayyim/kami-engine-sdk`.
The first scenario — semiconductor + electronic-materials chemical
plant incident — exercises every stage of the kami-cine pipeline
(`etzhayyim:kami-cine@1.0.0`) and is the vendor's first real visual product
beyond LLM-driven text/image artefacts.

Prior to this ADR the cyber-drill scene had:

- Toon-shaded box room with reverse-backface outline (Stage 5 lite).
- Procedural primitive props (`BoxGeometry`/`CylinderGeometry`).
- Choice cards visible the instant a node opened.
- A 10-second deadline that started immediately, racing the narration.
- No per-scenario visual differentiation beyond the `LocationKind`.

QA feedback was consistent: visuals felt flat (no atmosphere), choices
appeared before the user finished hearing the brief, and identical
locations rendered identically regardless of dramatic context (an
unfolding ransomware attack should not look like a recovery briefing).

# Decision

The cyber-drill VR visual stack is locked at **four concentric layers**,
each owned by a distinct API surface:

1. **Room shell** (toon room + 4 walls + ceiling + outline) — produced
   by `@etzhayyim/kami-engine-sdk/webvr::mountIncidentScene` using
   `MeshToonMaterial` with a 3-step gradient texture (`NearestFilter`,
   floor band lifted to 50%). Per-`LocationKind` palette.

2. **Spark Gaussian backdrop** — per-`LocationKind` procedural 3DGS
   cloud (~3-5k splats) attached via
   `@etzhayyim/kami-engine-sdk/spark::createSplatCloudLayer(camera,
   cloud, opts)`. Additive blending, painter sort each frame,
   foveation 0.15, opacity multiplier 1.4. Clouds:
   - `scadaRoom`     — monitor halos + amber LEDs + blue haze
   - `cleanroom`     — HEPA mist + cyan stepper silhouettes
   - `chemicalYard`  — reactor embers + rising steam + sodium ambient
   - `serverRoom`    — rack LED clusters + dim teal ambient
   - `executiveRoom` — warm sunset haze + table reflection
   - `press`         — flash bursts + pink ambient
   - `utilityRoom`   — steel cabinets + grey ambient

3. **Per-node visual effects** — 7-effect registry in
   `@etzhayyim/kami-engine-sdk/webvr::buildNodeEffect(kind, opts)`,
   stacked per `IncidentNode.effects`:
   | kind | use |
   |---|---|
   | `redAlarm`        | active incident, critical / high |
   | `orangeSmoke`     | chemical fire / runaway |
   | `dataLeak`        | exfiltration / lateral movement |
   | `pressFlash`      | press conference / cover-up failure |
   | `dawnLight`       | post-incident success / board reporting |
   | `greenCheck`      | recovery confirmed |
   | `monitorFlicker`  | SCADA alarm bank cycling |

4. **Cine pipeline artifacts** (Stage 1-4 worldModel/usdScene/
   neuralGeom/temporalField, Stage 5-6 neuralRender/diffusionPass)
   from the `CineBridge` — surfaced as the briefing-pill metadata
   (camera hint + mood palette) and the side panel illustration
   PNG. Mock by default; pod-backed when `endpoint` is configured.

## UX contract

- **Briefing slides in immediately** (easeOutCubic, 280ms) so the user
  reads context while listening.
- **Choices hidden until narration ends**. On `speak()` `onEnd`,
  reveal animates `scale 0.78→1.0 + opacity 0→1` over 380ms
  `easeOutBack`.
- **Selection countdown 30s**, armed by the same `speak()` `onEnd`
  callback — never races the narration. Color drains
  orange → amber → red.
- **Inaction auto-fire**: on deadline, the renderer picks the first
  choice whose label/hint matches `/様子見|観察|待機|保留|隠蔽|遅延|wait|observe|delay|hold/i`,
  modelling the cybersec drill principle that hesitation is the
  worst-graded option.

## Authoring contract (cyber-drill scenarios)

Every `IncidentNode` declares its dramatic cues at author time:

```ts
{
  id: 'chemRunaway',
  stage: 'contain',
  severity: 'critical',
  location: 'chemicalYard',
  effects: ['orangeSmoke', 'redAlarm'],
  cine: { prompt: '…' },
  choices: [...],
  briefing: '…',
}
```

The scene renderer reads only `location` + `effects[]` to compose the
3D experience. KPI deltas, references, and grades live on the choice
record (unchanged). Adding a new effect kind goes through
`node-effects.ts` + `NodeEffectKind` (centralised so all scenarios can
opt in once a new effect is registered).

# Comparison

Alternatives considered:

1. **Full photogrammetry per location** — would have required real
   site captures (impossible: customer NDA, no fab-floor access).
   Procedural Gaussian splats give a "looks-3D-scanned" hint without
   needing a real cloud.

2. **WebGPU PBR** with HDRi + IBL — would look better but
   `kami-engine-sdk` peer-deps Three.js (not the `kami-render` Rust
   wgpu pipeline); pulling the Rust path in for one project would
   triple the SDK install footprint. Toon + spark layer hits the
   target gestalt at ~120 KB JS budget.

3. **Per-node fully-bespoke Three.js scenes** (one scene per node) —
   rejected as O(N) authoring cost. The effect-registry approach
   keeps node authoring at ~5 lines (`effects: [...]`) while still
   producing visibly different scenes.

4. **Choice cards visible during narration with click-disabled** —
   tested; users tap-spammed during narration anyway. Hard-hiding
   the cards eliminates the racing.

# Exceptions

- Terminal nodes (`success` / `partial` / `failure`) render the
  outcome card **immediately** without the narration gate, so a
  failure outcome reads as a clear ending rather than a paused
  decision.
- The diagnostic magenta sphere (`webvr-scene.ts` early init) stays
  in until the first `update()` completes — useful for the empty
  WebGL surface debug path; not visible in normal operation.

# References

- SDK code:
  - `40-engine/kami-engine/kami-engine-sdk/src/lib/webvr/`
  - `40-engine/kami-engine/kami-engine-sdk/src/lib/spark/`
- Scenario data:
  - `60-apps/etzhayyim-project-cyber-drill/scenarios/semiconductor-chem-plant.ts`
- Commit lineage:
  - `152c5f5068e` initial webvr runtime + cyber-drill scaffold
  - `9e38fbb218a` spark backdrop + 7 effects + narration-gated reveal
- Boundary: cyber-drill is vendor-only per ADR-2605172400 (3-axis
  split: liability/custody/settlement all vendor). NOT eligible for
  the etzhayyim/root open-org mirror.
