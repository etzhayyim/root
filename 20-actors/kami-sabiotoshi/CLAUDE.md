# ai-gftd-project-kami — kami.etzhayyim.com / worlds.etzhayyim.com

**KAMI** — wgpu + KNP + hecs + KAMI Interface による次世代ゲームエンジン + 対話的ゲーム制作ワークベンチ。29 ゲーム (22 Godot + 6 Brainrot + 1 Suika) を KAMI Islands に移行済み。共通世界 "KAMI World" 上でユーザー制作ゲームが共存。**ログイン不要 (Guest Mode)** で world 作成・プレイ可能。Minecraft/Fortnite/Roblox 風テンプレートから即座に 3D ワールドを生成し、WebGPU でブラウザ内プレイ。

## Guest Mode (CRITICAL)

**kami.etzhayyim.com はログイン不要で利用可能。** Anonymous guest DID (`did:web:kami.etzhayyim.com:guest:*`) で world 作成・プレイ・マルチプレイ参加ができる。

| Feature | Guest | Logged In |
|---|---|---|
| Browse worlds | Yes | Yes |
| Play worlds (WebGPU WASD) | Yes | Yes |
| Create from template | Yes | Yes |
| AI prompt generation | Yes | Yes |
| Publish to KAMI Worlds | Yes | Yes |
| Persistent save | Ephemeral | Permanent |

### World Templates

| Template | Style | Content |
|---|---|---|
| `minecraft` | Survival Craft | Grass/dirt/stone layers, trees, cave, water pool, ores, villager NPC |
| `fortnite` | Battle Royale | Large arena, buildings, ramps, walls, loot chests, storm circle, boss NPC |
| `roblox` | Obby Course | Colorful jump platforms, coins, lava kill brick, spinner obstacle, guide NPC |
| `flat` | Creative | Empty flat world with spawns and portal |

### Guest Commands

| Command | App | Description |
|---|---|---|
| `guest-create-island` | workbench | Create island + auto-generate scene from template |
| `guest-generate-island` | workbench | Regenerate scene (template or LLM) |
| `browse-worlds` | workbench | List all published worlds (no auth) |
| `get-world-scene` | workbench | Get scene JSON-LD for playing (no auth) |
| `guest-join` | world | Join island session as guest |
| `guest-leave` | world | Leave island session |

## Architecture

| 項目 | 値 |
|---|---|
| Engine | **KAMI Engine** (`40-engine/kami-engine/`) — 7 Rust crates, 103+ tests, ~8500 行 |
| Workbench | `kami.etzhayyim.com` — Island CRUD, LLM scene 生成, AssetHub cross-actor, Publish, **Guest Mode** (Tier 1) |
| World | `worlds.etzhayyim.com` — Hub Island, Portal registry, matchmaking, **Guest Join** (Tier 1) |
| Runtime | `kami-rt.etzhayyim.com` — Actor lifecycle, physics sync |
| WIT | `gftd:kami@1.0.0` (`wit/kami/package.wit`) — island, scene, asset-bridge, actor-sync, **character**, publish, **catalog**, **player**, **ranking**, **emote**, **economy**, **physics**, **trigger**, **npc**, **inventory**, **terrain**, **pokoa**, **gacha**, **actor-conversation**, **call-effect** (21 interfaces)。`gftd:kami-coloring@1.0.0` (`wit/coloring/package.wit`) — canvas-lifecycle, color-graph, collab-session。`gftd:kami-battle-royale@1.0.0` (`wit/battle-royale/package.wit`) — match-lifecycle, ranked-queue, match-state。`gftd:kami-suika@1.0.0` (`wit/suika/package.wit`) — game-lifecycle, merge-physics, leaderboard |
| Character | **Nintendo Mii-style parametric avatar** (`gftd:kami/character@1.0.0`)。yoro Agent 作成時に使用。SVG プレビュー + wgpu 3D レンダリング |
| Persistence | W Protocol Event Stream (operational) + MDAG CAS (scene) + SQL (analytics) |
| W Protocol Event Stream | Write: `WRecord()` → yata SQL direct (SHA-256 content CID)。Read: `G()` (SQL) |
| **Lexicon** | `ai.gftd.apps.kami.*` — dot-notation kind で自動マッピング (`kami.islandDef` → `ai.gftd.apps.kami.islandDef`)。`40-engine/kami-engine/kami-game/src/wproto.rs` が authoritative kind 定数 |
| Scene Format | **JSON-LD** (`@context`, `@type`, `@id`) — `IslandScene` + `CharacterDef` + `CharacterAppearance`。後方互換 (plain JSON も parse 可) |
| Games | 29 games → 29 KAMI Islands (22 Godot + 6 Brainrot + 1 Suika, published + portals registered) |
| **Brainrot** | 6 Brainrot ゲーム + 6 キャラクター (Skibidi/Sigma/Ohio/Grimace/Rizz/Fanum)。Mii-style パラメトリック avatar |
| **Battle Royale** | `royale.kami.etzhayyim.com` — 100-player BR with storm, building, loot, ranked seasons, **6 Brainrot POIs** |
| BR WIT | `gftd:kami-battle-royale@1.0.0` (`wit/battle-royale/package.wit`) |
| **2D Side-Scroll** | Orthographic camera on 3D PBR pipeline. `camera_mode: "orthographic-side"` in scene JSON-LD. Z-depth layers + parallax. `sprite.rs` for Sprite2D → Plane conversion |

## CRITICAL: Game Runtime Architecture — Rust WASM + JSON-LD

→ `gftd dodaf tv1 query --id ai-gftd-project-kami-game-runtime-architecture-rust-wasm-+-j` / MCP `gftd.dodaf.tv1.query`

# ゲームロジック変更 (incremental)
cd 40-engine/kami-engine
cargo build -p kami-game              # ~5-15s

# WASM rebuild
wasm-pack build kami-web --target web  # ~40-90s (incremental)

# JSON-LD シーン変更
# → ビルド不要、ブラウザ reload のみ
```

### 既存ゲームの移行

| ゲーム | 現状 | 移行先 |
|---|---|---|
| ketsu-gorilla | `ketsu-game.htm` (inline JS Canvas 2D) | `kami-game/src/ketsu.rs` + `scenes/ketsu-gorilla-jungle.jsonld` |
| suika | HTML Canvas | `kami-game/src/suika.rs` + scene jsonld |
| kaede-world | HTML Canvas (2D side-scroll) | `kami-game/src/kaede.rs` + scene jsonld (`orthographic-side`) |
| 22 Godot games | island_gen → static scene | `kami-game/src/` + scene jsonld (段階移行) |
| 6 Brainrot games | island_gen → static scene | `kami-game/src/brainrot/` + scene jsonld |

### Version Management (KAMI Engine Games)

| フィールド | 場所 | 用途 |
|---|---|---|
| `version` | `magatama.jsonld` | デプロイバージョン (`gftd deploy` → `/_app/meta`) |
| `engine_version` | `40-engine/kami-engine/Cargo.toml` workspace | KAMI Engine バージョン (全 crate 共通) |
| `scene_version` | scene JSON-LD `@id` suffix | シーンデータバージョン (CID で管理) |
| `game_version` | `kami-game/Cargo.toml` | ゲームロジックバージョン |

## W Protocol Lexicon (CRITICAL)

**KAMI の全 AT Record は `ai.gftd.apps.kami.*` namespace。** dot-notation kind (`kami.{recordType}`) で `RecordMapper` が自動マッピング。

| Kind (W Protocol) | AT Collection NSID | WIT Source | 永続化 |
|---|---|---|---|
| `kami.islandDef` | `ai.gftd.apps.kami.islandDef` | `gftd:kami/island` | AT Record (MDAG) |
| `kami.portal` | `ai.gftd.apps.kami.portal` | `gftd:kami/island` | AT Record |
| `kami.sceneVersion` | `ai.gftd.apps.kami.sceneVersion` | `gftd:kami/scene` | AT Record (CID ref) |
| `kami.character` | `ai.gftd.apps.kami.character` | `gftd:kami/character` | AT Record (immutable meme) |
| `kami.buildResult` | `ai.gftd.apps.kami.buildResult` | `gftd:kami/publish` | AT Record |
| `kami.publishResult` | `ai.gftd.apps.kami.publishResult` | `gftd:kami/publish` | AT Record |
| `kami.matchSummary` | `ai.gftd.apps.kami.matchSummary` | `gftd:kami-battle-royale/match-lifecycle` | AT Record |
| `kami.playerResult` | `ai.gftd.apps.kami.playerResult` | `gftd:kami-battle-royale/match-lifecycle` | AT Record |
| `kami.rankedProfile` | `ai.gftd.apps.kami.rankedProfile` | `gftd:kami-battle-royale/ranked-queue` | AT Record |
| `kami.seasonInfo` | `ai.gftd.apps.kami.seasonInfo` | `gftd:kami-battle-royale/ranked-queue` | AT Record |
| `kami.killEvent` | `ai.gftd.apps.kami.killEvent` | `gftd:kami-battle-royale/match-state` | AT Record (feed) |
| `kami.evolution` | `ai.gftd.apps.kami.evolution` | `brainrot_mesh` / `island_gen` | AT Record (stage transition) |
| `kami.game.score` | `ai.gftd.apps.kami.game.score` | telemetry | AT Record |
| `kami.game.transaction` | `ai.gftd.apps.kami.game.transaction` | telemetry | AT Record |
| `kami.listing` | `ai.gftd.apps.kami.listing` | `gftd:kami/catalog` | AT Record |
| `kami.collection` | `ai.gftd.apps.kami.collection` | `gftd:kami/catalog` | AT Record |
| `kami.playerProfile` | `ai.gftd.apps.kami.playerProfile` | `gftd:kami/player` | AT Record |
| `kami.achievement` | `ai.gftd.apps.kami.achievement` | `gftd:kami/player` | AT Record |
| `kami.achievementUnlock` | `ai.gftd.apps.kami.achievementUnlock` | `gftd:kami/player` | AT Record |
| `kami.playSession` | `ai.gftd.apps.kami.playSession` | `gftd:kami/player` | AT Record |
| `kami.leaderboard` | `ai.gftd.apps.kami.leaderboard` | `gftd:kami/ranking` | AT Record |
| `kami.leaderboardEntry` | `ai.gftd.apps.kami.leaderboardEntry` | `gftd:kami/ranking` | AT Record |
| `kami.seasonPass` | `ai.gftd.apps.kami.seasonPass` | `gftd:kami/ranking` | AT Record |
| `kami.itemDef` | `ai.gftd.apps.kami.itemDef` | `gftd:kami/economy` | AT Record |
| `kami.trade` | `ai.gftd.apps.kami.trade` | `gftd:kami/economy` | AT Record |
| `kami.emoteDef` | `ai.gftd.apps.kami.emoteDef` | `gftd:kami/emote` | AT Record |
| `kami.emoteGrant` | `ai.gftd.apps.kami.emoteGrant` | `gftd:kami/emote` | AT Record |
| `kami.emoteLoadout` | `ai.gftd.apps.kami.emoteLoadout` | `gftd:kami/emote` | AT Record |
| `kami.game.emotePlay` | `ai.gftd.apps.kami.game.emotePlay` | telemetry | AT Record (analytics) |
| `kami.game.collision` | `ai.gftd.apps.kami.game.collision` | `gftd:kami/physics` | AT Record (audit) |
| `kami.triggerZone` | `ai.gftd.apps.kami.triggerZone` | `gftd:kami/trigger` | AT Record |
| `kami.game.triggerEvent` | `ai.gftd.apps.kami.game.triggerEvent` | `gftd:kami/trigger` | AT Record (analytics) |
| `kami.dialogueContext` | `ai.gftd.apps.kami.dialogueContext` | `gftd:kami/actor-conversation` | AT Record |
| `kami.dialogueOutcome` | `ai.gftd.apps.kami.dialogueOutcome` | `gftd:kami/actor-conversation` | AT Record |
| `kami.dialogueVote` | `ai.gftd.apps.kami.dialogueVote` | `gftd:kami/actor-conversation` | AT Record (council) |
| `kami.npcDef` | `ai.gftd.apps.kami.npcDef` | `gftd:kami/npc` | AT Record |
| `kami.game.npcInteraction` | `ai.gftd.apps.kami.game.npcInteraction` | `gftd:kami/npc` | AT Record (analytics) |
| `kami.questDef` | `ai.gftd.apps.kami.questDef` | `gftd:kami/npc` | AT Record |
| `kami.questProgress` | `ai.gftd.apps.kami.questProgress` | `gftd:kami/npc` | AT Record |
| `kami.game.inventoryEvent` | `ai.gftd.apps.kami.game.inventoryEvent` | `gftd:kami/inventory` | AT Record (analytics) |
| `kami.terrainConfig` | `ai.gftd.apps.kami.terrainConfig` | `gftd:kami/terrain` | AT Record |
| `kami.game.terrainEdit` | `ai.gftd.apps.kami.game.terrainEdit` | `gftd:kami/terrain` | AT Record (analytics) |
| `kami.pokoaTrainer` | `ai.gftd.apps.kami.pokoaTrainer` | `gftd:kami/pokoa` | AT Record |
| `kami.game.pokoaBattle` | `ai.gftd.apps.kami.game.pokoaBattle` | `gftd:kami/pokoa` | AT Record (analytics) |
| `kami.game.pokoaCapture` | `ai.gftd.apps.kami.game.pokoaCapture` | `gftd:kami/pokoa` | AT Record (analytics) |
| `kami.game.pokoaEvolve` | `ai.gftd.apps.kami.game.pokoaEvolve` | `gftd:kami/pokoa` | AT Record (analytics) |
| `kami.gachaBanner` | `ai.gftd.apps.kami.gachaBanner` | `gftd:kami/gacha` | AT Record |
| `kami.game.gachaRoll` | `ai.gftd.apps.kami.game.gachaRoll` | `gftd:kami/gacha` | AT Record (analytics) |
| `kami.suika.game` | `ai.gftd.apps.kami.suika.game` | `gftd:kami-suika/game-lifecycle` | AT Record |
| `kami.suika.score` | `ai.gftd.apps.kami.suika.score` | `gftd:kami-suika/leaderboard` | AT Record |
| `kami.ketsu_gorilla.game` | `ai.gftd.apps.kami.ketsu_gorilla.game` | `gftd:kami-ketsu-gorilla/game-lifecycle` | AT Record |
| `kami.ketsu_gorilla.score` | `ai.gftd.apps.kami.ketsu_gorilla.score` | `gftd:kami-ketsu-gorilla/leaderboard` | AT Record |
| `kami.ketsu_gorilla.slap` | `ai.gftd.apps.kami.ketsu_gorilla.slap` | `gftd:kami-ketsu-gorilla/gorilla-ai` | AT Record |
| `kami.callEffect` | `ai.gftd.apps.kami.callEffect` | `gftd:kami/call-effect` | AT Record |
| `kami.callEffectActive` | `ai.gftd.apps.kami.callEffectActive` | `gftd:kami/call-effect` | AT Record |

**使い方 (TS Native):**
```go
// Island 作成
rkey, _ := magatama.WRecord("kami.islandDef", islandPayload)

// Character mint (immutable)
rkey, _ := magatama.WRecord("kami.character", characterPayload)

// Match 結果記録
rkey, _ := magatama.WRecord("kami.matchSummary", matchPayload)
rkey, _ := magatama.WRecord("kami.playerResult", playerPayload)

// Social post (Bluesky Lexicon)
magatama.ATPost("New island published!", &magatama.ATPostOpts{...})

// Emote 定義 (catalog)
rkey, _ := magatama.WRecord("kami.emoteDef", emoteDefPayload)

// Emote 付与 (player inventory)
rkey, _ := magatama.WRecord("kami.emoteGrant", emoteGrantPayload)

// Emote 再生イベント (telemetry)
rkey, _ := magatama.WRecord("kami.game.emotePlay", emotePlayPayload)

// Video call effect preset 作成
rkey, _ := magatama.WRecord("kami.callEffect", callEffectPayload)

// Video call active effect 設定
rkey, _ := magatama.WRecord("kami.callEffectActive", activePayload)
```

**非永続 (KNP real-time):** `actor-state-update`, `storm-state`, `bus-state`, `emote-broadcast` は KNP Channel で配信。AT Record に書かない。

## KAMI Engine (`40-engine/kami-engine/`)

| Crate | 役割 | Tests |
|---|---|---|
| `kami-core` | KAMI Interface (Column/Frame/Delta) + Actor + hecs ECS + GameClock | 3 |
| `kami-knp` | KNP (custom UDP) + channels + ChaCha20 + session + server/client + WebTransport | 2 |
| `kami-render` | wgpu renderer + PBR shader (WGSL) + camera + mesh (cube/sphere/plane/glTF) + pipeline + shadow + logo + **texture** (GPU tex + mipmap + fallback) + **splat** (3DGS data + PLY/.splat loader + compute sort + billboard pipeline) | 20 |
| `kami-voxel` | **Volume layer** — Dense / Sparse / Octree voxel representations。全生成源の中間表現 | 4 |
| `kami-sdf` | **Generation: SDF** — Signed Distance Function primitives (sphere/box/cylinder/capsule/torus) + CSG boolean (union/difference/intersection/smooth-union) + density field sampling | 5 |
| `kami-nerf` | **Generation: NeRF** — Pre-trained density grid loader + trilinear sampling + color → VoxelVolume | 2 |
| `kami-scad` | **Generation: Procedural** — OpenSCAD subset parser + CSG evaluator + pipeline orchestrator (scad→sdf→volume→mesh/glb) | 16 |
| `kami-mesher` | **Output: Mesh** — Marching Cubes + Greedy Meshing。VoxelVolume → LoadedMesh (GPU-ready) | 2 |
| `kami-gltf` | **Output: glTF** — Binary glTF 2.0 (.glb) writer。LoadedMesh → Vec<u8> | 1 |
| `kami-game` | physics (Rapier) + input + NPC AI + inventory + economy + triggers + prediction + arena + addons (C5-C15) + gameshell + scene (JSON-LD) + island_gen (29 games) + wproto Event Stream + **battle_royale** (storm/loot/building/100p/26 POIs) + **ranked** (MMR/ELO/seasons) + **voxel** (16^3 chunks, greedy mesh, KAMI Column sync) + **terrain** (heightmap, LOD, noise gen) | 167 |
| `kami-engine` | Integration: game loop + ECS snapshot → delta → KNP wire | 2 |
| `kami-web` | wasm-bindgen + WebGPU browser entry — `run()` (orbit demo) + `run_with_scene(canvas, json)` (WASD first-person) + `run_embed(canvas, json)` (orbit, embed mode) + pointer lock + keyboard input | wasm32 only |
| `kami-demo` | Native render (1000 PBR cubes) + multiplayer (server/client) | verified |
| `kami-game-sdk` | **DEPRECATED** — Canvas 2D game engine。新規ゲームは kami-game Rust crate + kami-web WebGPU を使用すること。既存利用は段階移行 | 1.0.0 (deprecated) |

## CRITICAL: Game Design Principles (7 原則)

→ `gftd dodaf tv1 query --id ai-gftd-project-kami-game-design-principles-7-原則` / MCP `gftd.dodaf.tv1.query`

## Published Islands (29 games)

| # | Game | Island ID | Genre |
|---|---|---|---|
| 1 | Agar Arena | `isl-2299ef2280` | action |
| 2 | Slither World | `isl-22c0058040` | action |
| 3 | Diep Tanks | `isl-22e9725c00` | action |
| 4 | Mope Wilderness | `isl-230da071c0` | action |
| 5 | Splix Territory | `isl-2328822880` | action |
| 6 | Hole Devourer | `isl-234a7bab00` | action |
| 7 | Paper Conquest | `isl-236a5f1ec0` | action |
| 8 | Wings Dogfight | `isl-2398cdb780` | action |
| 9 | Zombs Defense | `isl-23b3a02c00` | action |
| 10 | Snake Classic | `isl-23ca92ce40` | arcade |
| 11 | Color Zen | `isl-23e9ecedc0` | puzzle |
| 12 | Match 3 | `isl-240974d400` | puzzle |
| 13 | Infinite Dive | `isl-24278e8440` | arcade |
| 14 | Dungeon Quest | `isl-2446e8a3c0` | rpg |
| 15 | Kyber Frontier | `isl-24644b3900` | rpg |
| 16 | Idol Manager | `isl-2481fa1980` | sandbox |
| 17 | Club Tycoon | `isl-249d375dc0` | sandbox |
| 18 | Love and Glitch | `isl-24b6c96300` | puzzle |
| 19 | Card Showdown | `isl-24d56c6780` | strategy |
| 20 | Alchemist Lab | `isl-24f55f1d80` | sandbox |
| 21 | Conquest | `isl-2512b27080` | strategy |
| 22 | Agency | `isl-252ed49680` | sandbox |
| 23 | Skibidi Arena | `urn:kami:island:skibidi` | brainrot |
| 24 | Sigma Grindset | `urn:kami:island:sigma` | brainrot |
| 25 | Ohio Final Boss | `urn:kami:island:ohio` | brainrot |
| 26 | Grimace Shake | `urn:kami:island:grimace` | brainrot |
| 27 | Rizz Academy | `urn:kami:island:rizz` | brainrot |
| 28 | Fanum Tax | `urn:kami:island:fanum` | brainrot |
| 29 | Suika Merge | `su1k4gm3` | puzzle |
| 30 | Kaede World | `k43d3gm3` | rpg |
| 31 | Goriketsu Dash!! | `k3t5g0r1` | chase |

## App Components (`wasm/`)

| Component | nanoid | Domain | Worker |
|---|---|---|---|
| **kami-workbench** | `k4m1w0rk` | `kami.etzhayyim.com` | `magatama-kami` |
| **kami-world** | `k4m1w0ld` | `worlds.etzhayyim.com` | `magatama-worlds` |
| **kami-runtime** | `k4m1r0nt` | `kami-rt.etzhayyim.com` | `magatama-kami-rt` |
| **kami-royale** | `k4m1r0yl` | `royale.kami.etzhayyim.com` | `magatama-kami-royale` |
| **kami-coloring** | `cbn8gf7x` | `color-by-number.etzhayyim.com` | `magatama-kami-coloring` |
| **kami-suika** | `su1k4gm3` | `suika.kami.etzhayyim.com` | `magatama-su1k4gm3` |
| **kami-kaede** | `k43d3gm3` | `kaede.kami.etzhayyim.com` | `magatama-k43d3gm3` |
| **kami-ketsu-gorilla** | `k3t5g0r1` | `ketsu-gorilla.kami.etzhayyim.com` | `magatama-k3t5g0r1` |

## Scene Format (CRITICAL): JSON-LD

**シーンデータは JSON-LD 形式を標準とする。** `@context`, `@type`, `@id` で Linked Data メタデータを付与。既存の plain JSON も後方互換で parse 可能 (全 JSON-LD フィールドは `serde(default)`)。

```jsonld
{
  "@context": "https://gftd.co.jp/ns/kami/scene",
  "@type": "IslandScene",
  "@id": "urn:kami:island:{slug}",
  "name": "...",
  "genre": "brainrot",
  "description": "...",
  "max_players": 50,
  "characters": [{ "@type": "KamiCharacter", "id": "...", "appearance": {...} }],
  "entities": [...],
  "ambient_color": [0.03, 0.03, 0.05],
  "sun_direction": [-1.0, -2.0, -1.0],
  "sun_intensity": 3.0
}
```

| 型 | `@type` 値 | 用途 |
|---|---|---|
| `IslandScene` | `IslandScene` | 通常 Island シーン |
| `BattleRoyaleScene` | `BattleRoyaleScene` | BR マップ (POI + storm) |
| `CharacterDef` | `KamiCharacter` | Mii-style パラメトリックキャラクター |

**ルール:**
- 新規シーンデータは `.jsonld` 拡張子で `scenes/` に配置
- `generate_all_islands()` / `generate_br_map()` は JSON-LD メタデータを自動付与
- `run_with_scene(canvas, scene_jsonld)` で JSON-LD シーンをブラウザ内プレイ
- `CharacterDef` は `gftd:kami/character` WIT の `character-appearance` に 1:1 対応

## 2D Side-Scroll Mode (Orthographic Camera)

**KAMI Engine supports 2D side-scrolling games via orthographic camera projection on the existing 3D PBR pipeline.** No separate 2D renderer — same wgpu pipeline, constrained camera.

### How It Works

| Aspect | 3D Mode (default) | 2D Side-Scroll Mode |
|---|---|---|
| Camera | Perspective, free fly | Orthographic, fixed Z, follow player X/Y |
| Input | WASD + mouse look + pointer lock | Arrow/WASD horizontal + Space jump |
| Entities | 3D meshes in world space | Textured Plane quads at Z-depth layers |
| Parallax | N/A | Automatic via Z-depth layer `parallax` factor |
| Activation | `camera_mode` absent or `"perspective"` | `camera_mode: "orthographic-side"` in scene JSON-LD |

### Scene JSON-LD Fields (2D)

| Field | Type | Description |
|---|---|---|
| `camera_mode` | `string` | `"orthographic-side"` for 2D side-scroll |
| `viewport` | `{width, height, pixels_per_unit}` | Viewport dimensions and scale |
| `layers` | `[{name, z, parallax, color?}]` | Z-depth layers for parallax |
| Entity `layer` | `string` | Layer name reference for Z-depth placement |

### Z-Depth Layer Convention

```
Z = -5.0  Background (sky)        parallax 0.2x
Z = -3.0  Far background           parallax 0.4x
Z = -2.0  Far decor (trees)       parallax 0.6x
Z =  0.0  Platforms (ground)      parallax 1.0x
Z =  1.0  Actors (player/monsters) parallax 1.0x
Z =  2.0  Foreground              parallax 1.3x
Z =  5.0  HUD overlay             parallax 0.0 (fixed)
```

### Sprite2D (`kami-game/src/sprite.rs`)

2D sprite → `SceneEntity` (Plane mesh + material) conversion. Sprites are textured quads rendered by the existing PBR pipeline.

### KAMI Islands Using 2D Mode

| Island | nanoid | Mode | Genre |
|---|---|---|---|
| Kaede World | `k43d3gm3` | `orthographic-side` | rpg (MapleStory-style) |

## Brainrot Content

**6 Brainrot ゲーム + 6 キャラクター + 6 BR POI。** `Genre::Brainrot` で island_gen がプロシージャル 3D シーンを自動生成。

### Brainrot Characters (Mii-style パラメトリック)

| ID | Name | Role | Body | Hair | Accessory | Skin |
|---|---|---|---|---|---|---|
| `char-skibidi-commander` | Skibidi Commander | boss | stocky | buzz | sunglasses | hue=0.08 |
| `char-sigma-male` | Sigma Grindset | npc | athletic | spiky | sunglasses | hue=0.06 |
| `char-ohio-boss` | Ohio Final Boss | boss | tall | mohawk | mask | hue=0.0 |
| `char-grimace` | Grimace | boss | stocky | bald | none | hue=0.75 (purple) |
| `char-rizz-master` | Rizz Master | npc | slim | wavy | earring | hue=0.07 |
| `char-fanum` | Fanum Tax Collector | npc | average | afro | hat | hue=0.07 |

### Brainrot 3D Structures (プロシージャル)

| Structure | Composition | Location |
|---|---|---|
| Giant Toilet (Skibidi HQ) | cube×4 (bowl+tank+lid+head) | center |
| Sigma Gym | cube×2 + sphere×4 (base+throne+dumbbells) | northeast |
| Ohio Obelisk | cube×7 (pillar + 6 floating damage cubes) | northwest |
| Grimace Blob | sphere×2 + plane×8 (body+head+puddles) | southwest |
| Rizz Stage | cube×2 (podium+stage) | southeast |
| Fanum Market | cube×6 (stall + 5 food crates) | east |

### Brainrot BR POIs (26 total = 20 classic + 6 brainrot)

| POI | Center | Type | Loot | Description |
|---|---|---|---|---|
| Skibidi Sewers | (350, 0, 350) | Landmark | 0.8 | Underground toilet network, tight corridors |
| Sigma Summit | (-450, 30, 500) | Landmark | 0.6 | Mountain gym, high ground advantage |
| Ohio Outpost | (700, 0, -400) | Military | 0.9 | Anomaly zone, floating damage cubes, top loot |
| Grimace Grotto | (-300, -5, 600) | Landmark | 0.5 | Purple swamp cave, slow+damage puddles |
| Rizz Resort | (500, 0, 500) | City | 0.9 | Luxury district, high building density |
| Fanum Food Court | (-600, 0, -300) | Town | 0.7 | Consumable-heavy loot, food crate HP/shield |

## Brainrot Evolution (CRITICAL) — Pokémon-style multi-stage model transform

**各 brainrot agent は 2-5 段階の discrete evolution を持つ。進化すると 3D model が不可逆に変形。** Gate = Well-Becoming social rank + domain achievement の AND 条件。

| Character | Stages | Forms | Scale Range |
|---|---|---|---|
| **Skibidi** | 4 (0-3) | Mini Toilet → Skibidi Soldier → Skibidi Tank → Skibidi Titan | 0.6 → 3.0 |
| **Sigma** | 5 (0-4) | Scrawny Kid → Gym Bro → Sigma Male → Gigachad → Sigma Ascended | 0.7 → 1.5 |
| **Ohio** | 3 (0-2) | Ohio Anomaly → Ohio Nightmare → Ohio Eldritch | 1.0 → 4.0 |
| **Grimace** | 4 (0-3) | Purple Puddle → Grimace Blob → Grimace Tide → Grimace Singularity | 0.5 → 2.5 |
| **Rizz** | 3 (0-2) | Awkward Kid → Rizz Master → Rizz Sensei | 0.8 → 1.1 |
| **Fanum** | 4 (0-3) | Street Kid → Tax Collector → Tax Baron → Fanum Mogul | 0.8 → 1.4 |

### Evolution Gate (AND 条件)

| Stage Gate | Social Gate (Well-Becoming) | Domain Gate (game-specific) |
|---|---|---|
| → Stage 1 | Kyu 4-5 | Game-specific milestone (boss kills, streak, recipes, etc.) |
| → Stage 2 | Kyu 1-3 | Cross-game cross-actor achievement |
| → Stage 3+ | Dan 1-5 | Ecosystem-wide achievement (全 brainrot cross-actor 実績等) |

### Model Transform (mesh 変化例)

- **Skibidi**: toilet → toilet+torso → mega toilet+camera heads+treads → fortress+obelisk towers+orbital heads
- **Sigma**: slim body → athletic+dumbbell → athletic+barbell → stocky+jaw+throne → tall+aura orbs+armor
- **Grimace**: flat blob → blob+eyes → mega blob+4 satellites → hollow shell+void core+vortex arms

### Cross-Game Stage Dependencies

Final stage 進化は他 game の stage を要求。1 体だけ先行進化できない — ecosystem 連動。

### Implementation

- `brainrot_mesh.rs`: `BrainrotCharacter` enum + `brainrot_evolution_mesh(character, stage, phase)`
- `island_gen.rs`: `BrainrotEvolution` + `brainrot_evolution_chains()`
- AT Record: `ai.gftd.apps.kami.evolution` (stage transition 記録)
- Social: ATPost で進化 announce → ATLike → engagement 加速

## File Structure

```
60-apps/ai-gftd-project-kami/
├── CLAUDE.md
│                                        ← KAMI Engine は 40-engine/kami-engine/ に移動済み
├── scenes/                              ← JSON-LD scene data
│   ├── brainrot-island.jsonld           (Brainrot Island — 6 zones + 6 characters)
│   ├── brainrot-battle-royale.jsonld    (BR Brainrot Edition — 6 POIs + characters)
│   ├── kaede-world.jsonld               (Kaede World — 2D side-scroll RPG, orthographic-side)
│   └── ketsu-gorilla-jungle.jsonld      (Goriketsu Dash!! — chase game, SDF gorilla)
├── docs/
│   ├── kami-engine-design.md            ← Phase roadmap (Phase 1-9 complete)
│   └── kami-game-workbench-design.md
├── wit/
│   ├── kami/package.wit                 (gftd:kami@1.0.0)
│   ├── battle-royale/package.wit        (gftd:kami-battle-royale@1.0.0)
│   ├── coloring/package.wit             (gftd:kami-coloring@1.0.0)
│   ├── suika/package.wit                (gftd:kami-suika@1.0.0)
│   └── ketsu-gorilla/package.wit        (gftd:kami-ketsu-gorilla@1.0.0)
└── wasm/
    ├── ai-gftd-wasm-kami-workbench-k4m1w0rk/
    ├── ai-gftd-wasm-kami-world-k4m1w0ld/
    ├── ai-gftd-wasm-kami-runtime-k4m1r0nt/
    ├── ai-gftd-wasm-kami-royale-k4m1r0yl/   (Battle Royale ranked mode)
    ├── ai-gftd-wasm-kami-coloring-cbn8gf7x/  (Color-by-number game)
    ├── ai-gftd-wasm-kami-suika-su1k4gm3/     (Suika merge puzzle game)
    ├── ai-gftd-wasm-kami-kaede-k43d3gm3/     (Kaede World — 2D side-scroll RPG)
    └── ai-gftd-wasm-kami-ketsu-gorilla-k3t5g0r1/  (Goriketsu Dash!! — chase game)
```
