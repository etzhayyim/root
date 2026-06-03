> **DEPRECATED**: Actor migrated to `20-actors/isekai/actor-manifest.jsonld` (T1 MCP-Compose). This project wasm/*/src/app.ts is retained as T3 fallback only.
>
> **Engine migration (2026-04-18)**: ISEKAI WebGPU client is mid-migration from legacy `kami-web::run_with_scene` (1.85 MB monolith) to per-game crate `kami-app-isekai` (221 KB, Builder SDK + shared kami-pipelines). See `40-engine/kami-engine/ARCHITECTURE.md` + `[[migrations]] kami-app-per-game-topology-2026-04`.
>
> | URL | Bundle | Engine path |
> |---|---|---|
> | `isekai.etzhayyim.com/` | kami_web 1.85 MB (legacy) | `kami-web::run_with_scene` — full voxel+NPC+Pokoa gameplay |
> | `isekai.etzhayyim.com/v2.htm` | kami_app_isekai 261 KB | `kami-app-isekai::run_isekai_v2` — builder composition + streaming terrain + multi-species vegetation + water + **streaming voxels (mine/place with particle FX) + gravity/jump + 3-axis AABB wall collision + greedy-meshed blocks**. NPC / Pokoa capture pending migration |
> | `isekai.etzhayyim.com/quarry-walk-v2.htm` | kami_app_quarry_walk 199 KB | 2nd reference game validating shared `kami-pipelines` reuse |
> | `isekai.etzhayyim.com/v3-demos.htm#scene=0..10` | same kami_app_isekai | **v3 DEC physics demo harness + Nintendo-style visual layer** (2026-04-19) — 11 scenes isolate one phenomenon each: 0 heat / 1 moisture / 2 wind / 3 projection / 4 walls+vorticity / 5 Maxwell EM / 6 fire propagation / 7 water extinguish / 8 gravity rain / 9 wind drag / 10 gravity·fire·water·wind coupled. Runtime HUD publishes pos/yaw/pitch/fps to `window.__kami_hud_isekai`. Perf stack: active-region clip + 30 Hz DEC tick + multigrid projection + LOD on Field/Edge/FaceVisAdapter. Nintendo layer: AtlasVisAdapter (16 procedural sprite slots: flame/water/sparkle/shock_wave/wind_swirl/…) + spring-anim (bob/pulse/wiggle/pop-in) + FieldIconMap shared heat/moisture→icon rules + Web Audio SFX (coin on ignition, tick on EM ring, pop on splash, whoosh on vortex) + atlas sparkle-LOD (15–40 m collapse, >40 m cull). Entry `run_isekai_v2_scene(canvas_id, scene_id)` |
> | `isekai.etzhayyim.com/v3-demos.htm#scene=12` | kami_web 2.26 MB | **VRM character locomotion demo** (2026-04-20, M1+M2+M3) — scene 12 bypasses `run_isekai_v2_scene` and loads `kami-web::run_embed_vrm` (ADR-0031 sanctioned additive extension). Default VRM = pixiv/three-vrm `VRM1_Constraint_Twist_Sample.vrm`. Controls: WASD walk (2 m/s, 1.2 Hz leg cycle, 25° swing) / Shift+WASD run (4.5 m/s, 2.0 Hz, 35° swing + 6° forward lean) / Space jump (7 m/s impulse, 20 m/s² gravity, grounded re-entry check) / mouse drag third-person orbit / wheel zoom. Pose selection: air > run > walk > idle, authored as Euler-degree bone-rotation tuples applied per-frame to `VRM_SKIN_STATE.pose_overrides` using VRM 1.0 humanoid names (leftUpperLeg / rightUpperArm / spine / chest / head etc.). Root TRS composed into each batch `instance_buffer` every frame via `Mat4::from_translation * Mat4::from_rotation_y * base_transform` |

# etzhayyim-project-isekai — isekai.etzhayyim.com

**ISEKAI** — Minecraft voxel sandbox + Pokoa creature collection + Brainrot meme chaos。KAMI Engine WebGPU で異世界転生オープンワールド。Guest Mode でログイン不要プレイ。

## Architecture

| 項目 | 値 |
|---|---|
| Engine | **KAMI Engine** (`40-engine/kami-engine/`) — wgpu + hecs + Rapier 3D + KNP |
| Domain | `isekai.etzhayyim.com` (vanity), `is3k41w0.etzhayyim.com` (nanoid) |
| Runtime | Single Worker (TS Native + host-sdk) |
| UI | `game` mode — yoro profile hero 9:16 iframe |
| WIT | `etzhayyim:isekai@1.0.0` (`wit/isekai/package.wit`) — 5 interfaces |
| Persistence | W Protocol Event Stream (AT Record) + KNP real-time (non-persistent) |
| Scene | JSON-LD (`scenes/*.jsonld`) — procedural biome islands |

## Guest Mode

| Feature | Guest | Logged In |
|---|---|---|
| Explore overworld | Yes | Yes |
| Mine/craft voxel blocks | Yes | Yes |
| Catch wild Pokoa | Yes | Yes |
| Brainrot events | Yes | Yes |
| Save world | Ephemeral | Permanent |
| Trade Pokoa | No | Yes |
| Leaderboard | No | Yes |

## Game Design — 3 Pillars

### Pillar 1: Minecraft Voxel Sandbox (kami-voxel + kami-mesher)

- Procedural overworld: 6 biomes (plains, forest, desert, tundra, nether, skibidi-dimension)
- 16^3 chunk system (Sparse voxel → greedy mesh)
- Block types: dirt, stone, wood, ore, crystal, brainrot-block (animated)
- Mining + crafting + building
- Day/night cycle → wild Pokoa spawn rates change

### Pillar 2: Pokoa Creature Collection (etzhayyim:kami/pokoa)

- 151 base species + 6 Brainrot legendaries
- Type system: 18 standard types + `brainrot` hidden type
- Wild encounters in tall grass / caves / water
- Turn-based battle: 4 moves per Pokoa, type effectiveness, catch mechanics
- Evolution: level-based + item-based + friendship-based
- Pokoa follow player in overworld (party lead visible)

### Pillar 3: Brainrot Meme Chaos

- 6 Brainrot NPCs roam the overworld as random events
  - **Skibidi Toilet** — ambush encounter, spawns in bathrooms/caves
  - **Sigma Male** — appears at mountain peaks, philosophical dialogue
  - **Ohio Boss** — raid boss, 100 HP, drops rare loot
  - **Grimace Shake** — heals all Pokoa but causes `confusion` status
  - **Rizz Master** — charm NPC, gives friendship evolution items
  - **Fanum Tax** — steals random item from inventory, must chase to recover
- Brainrot Dimension: portal opened by collecting 6 Brainrot Shards
- Brainrot legendary Pokoa: catchable only in Brainrot Dimension

### Brainrot Legendary Pokoa

| Species | Type | Ability | Catch Location |
|---|---|---|---|
| Skibidion | Water/Brainrot | Toilet Flush (AOE water) | Skibidi Sewers |
| Sigmalord | Psychic/Brainrot | Sigma Stare (paralyze) | Sigma Summit |
| Ohiodon | Dark/Brainrot | Ohio Final Boss (1-hit KO chance) | Ohio Wasteland |
| Grimaceon | Poison/Fairy | Shake Heal (full team heal, self confuse) | Grimace Cave |
| Rizzler | Fairy/Brainrot | Rizz Charm (force switch) | Rizz Palace |
| Fanumoth | Ghost/Brainrot | Tax Steal (steal held item) | Fanum Market |

## W Protocol Lexicon

| Kind (W Protocol) | AT Collection NSID | WIT Source | 永続化 |
|---|---|---|---|
| `isekai.worldState` | `com.etzhayyim.isekai.worldState` | `etzhayyim:isekai/open-world` | AT Record |
| `isekai.chunkData` | `com.etzhayyim.isekai.chunkData` | `etzhayyim:isekai/voxel-terrain` | AT Record |
| `isekai.craftRecipe` | `com.etzhayyim.isekai.craftRecipe` | `etzhayyim:isekai/crafting` | AT Record |
| `isekai.brainrotEvent` | `com.etzhayyim.isekai.brainrotEvent` | `etzhayyim:isekai/brainrot-event` | AT Record |
| `isekai.creatureRoster` | `com.etzhayyim.isekai.creatureRoster` | `etzhayyim:isekai/creature` | AT Record |
| `isekai.game.battle` | `com.etzhayyim.isekai.game.battle` | `etzhayyim:kami/pokoa` | AT Record (analytics) |
| `isekai.game.capture` | `com.etzhayyim.isekai.game.capture` | `etzhayyim:kami/pokoa` | AT Record (analytics) |
| `isekai.game.craft` | `com.etzhayyim.isekai.game.craft` | `etzhayyim:isekai/crafting` | AT Record (analytics) |
| `isekai.game.brainrotEncounter` | `com.etzhayyim.isekai.game.brainrotEncounter` | `etzhayyim:isekai/brainrot-event` | AT Record (analytics) |
| `isekai.complianceDep` | `com.etzhayyim.isekai.complianceDep` | compliance graph | AT Record |

**非永続 (KNP real-time):** player position, voxel edit stream, battle animation state, brainrot NPC movement

## Compliance — Patent/Lawsuit Dependency Graph

**Microsoft/Mojang (Minecraft) + Nintendo/TPC (Pokémon) 特許・訴訟・trade dress を SQL ノードで管理。各ノードに mitigation 戦略を記録。**

| ID | Type | Risk | Mitigation |
|---|---|---|---|
| US10232272B2 | Patent (procedural gen) | Medium | Value noise (not Perlin), fixed chunk grid |
| US9956475B2 | Patent (block edit) | High | DDA raycast (public domain 1987), greedy mesh (MIT 2012) |
| US20190329143A1 | Patent (creature capture) | Medium | Original type system (brainrot type), crafted balls |
| US10549210B2 | Patent (multiplayer sync) | Low | KNP protocol, W Protocol AT Records |
| JP6789012B2 | Patent (block UI) | Low | Standard FPS crosshair (prior art: Infiniminer 2009) |
| Nintendo v Palworld | Lawsuit | — | Original species, crafted balls, no throwing animation |
| Minecraft trade dress | Trade dress | — | PBR rendering, SDF characters, brainrot aesthetic |

**登録**: `com.etzhayyim.isekai.registerCompliance` コマンドで全ノードを graph に投入
**照会**: `com.etzhayyim.isekai.getCompliance` で risk level フィルタ可能

## KAMI Engine Integration

### Rust WASM (kami-game crate)

```rust
// 40-engine/kami-engine/kami-game/src/isekai.rs
pub struct IsekaiGame {
    world: VoxelWorld,          // kami-voxel Sparse chunks
    pokoa_system: PokoaSystem,  // creature roster + battle state
    brainrot: BrainrotEvents,   // NPC spawn + event timer
    player: PlayerState,        // position, inventory, party
    time_of_day: f32,           // 0.0–1.0 day cycle
}

impl IsekaiGame {
    pub fn new(scene: &IslandScene) -> Self { /* procedural world gen */ }
    pub fn update(&mut self, input: &InputState, dt: f32) { /* tick all systems */ }
    pub fn entities(&self) -> Vec<EntityUpdate> { /* ECS → render bridge */ }
}
```

### Scene Format

```json
{
  "@context": "https://etzhayyim.com/ns/kami/scene",
  "@type": "IslandScene",
  "@id": "kami:island/isekai-overworld-v1",
  "genre": "sandbox",
  "camera_mode": "first-person",
  "world_seed": 42,
  "biomes": ["plains", "forest", "desert", "tundra", "nether", "skibidi-dimension"],
  "spawn_point": [0, 64, 0],
  "pokoa_spawn_table": { "plains": ["grass-types"], "forest": ["bug-types"], "cave": ["rock-types"] },
  "brainrot_npc_spawns": ["skibidi", "sigma", "ohio", "grimace", "rizz", "fanum"]
}
```

## LOD System (Level of Detail)

**Distance-based voxel LOD + SDF character resolution scaling。kami-engine-sdk に TypeScript 型定義。**

| LOD | 距離 (blocks) | Voxel Mesh | SDF Resolution | 頂点数/chunk |
|---|---|---|---|---|
| **LOD 0** | 0–32 | Full greedy mesh (16^3) | 32 | ~800-2000 |
| **LOD 1** | 32–64 | 2×2×2 down-sample → 8^3 greedy | 16 | ~100-400 |
| **LOD 2** | 64–128 | 4×4×4 down-sample → 4^3 greedy | 8 | ~20-80 |
| **LOD 3** | 128+ | Single dominant-color cube | — | 24 |

- **更新間隔**: 10 フレーム毎に全チャンクの距離を再評価
- **Block edit 時**: 該当チャンクを即座に LOD 0 に昇格、remesh
- **頂点削減**: 全チャンク LOD 0 (~50K-100K verts) → LOD 適用 (~11K-22K verts, **75-80% 削減**)

### SDK 型定義

`40-engine/kami-engine/kami-engine-sdk/src/lib/types/engine.ts`:
- `VoxelLodConfig` — thresholds, updateInterval, forceLod
- `SdfLodConfig` — thresholds, baseResolution
- `LodConfig` — combined
- `BlockType` enum, `ChunkCoord`, `PlayerPhysicsState`, `SkyState`, `PerfMetrics`, `IsekaiGameState`

## Build & Deploy

```bash
# Legacy client (1.85 MB monolithic kami-web, isekai.etzhayyim.com/)
cd 40-engine/kami-engine
cargo build -p kami-game
wasm-pack build kami-web --target web

# v2 client (221 KB per-game crate, isekai.etzhayyim.com/v2.htm — PREFERRED for new work)
cd 40-engine/kami-engine
wasm-pack build kami-app-isekai --target web --release
# Copy pkg/* into
#   60-apps/.../etzhayyim-wasm-isekai-is3k41w0/svelte/{static,build}/v2/

# Domain agent (TS Native, unchanged)
cd 60-apps/etzhayyim-project-isekai/wasm/etzhayyim-wasm-isekai-is3k41w0
etzhayyim build
etzhayyim deploy

# Scene edit (legacy path only)
# Edit scenes/isekai-overworld.jsonld → browser reload
```
