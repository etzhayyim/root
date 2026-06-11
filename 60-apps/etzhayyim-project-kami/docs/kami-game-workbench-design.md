# KAMI — Game Creation Workbench + Shared World Platform

`kami.etzhayyim.com` — Godot + Actor Model ベースのゲーム制作ワークベンチ。ユーザーが対話的にゲームを設計・制作し `games.etzhayyim.com` に投稿する。共通世界 "KAMI World" 上で Minecraft/Fortnite/Roblox のようにユーザー制作ゲームが共存する。

## 概要

| 要素 | 定義 |
|---|---|
| **KAMI Workbench** | kami.etzhayyim.com — 対話的ゲーム制作ツール (canvas mode) |
| **KAMI World** | 共有永続世界。ユーザー制作ゲームが "Island" として接続される |
| **games.etzhayyim.com** | 公開配信面。KAMI から publish されたゲームのアーケード |
| **assethub.etzhayyim.com** | 3D/2D/Audio/Live2D アセット。KAMI Workbench から直接参照・配置 |

## Architecture: Godot + Actor Model

### Godot as Runtime

Godot 4.x Web Export が全ゲームの実行基盤。

```
KAMI Workbench (kami.etzhayyim.com)
  ├─ Scene Editor ← Godot scene tree (.tscn) を対話的に構築
  ├─ Script Editor ← GDScript / Visual Script (node-based)
  ├─ Asset Browser ← assethub.etzhayyim.com cross-actor 連携
  ├─ World Preview ← Godot Web Export (iframe sandbox)
  └─ Publish Pipeline ← games.etzhayyim.com へ投稿
```

### Actor Model (kotodama:actor WIT)

全ゲームエンティティは `kotodama:actor/virtual-actor@1.0.0` 上の Actor。

| Actor 種別 | 説明 | WIT interface |
|---|---|---|
| **PlayerActor** | プレイヤーキャラクター。input → state → render | `virtual-actor` + `actor-state` (user scope) |
| **NPCActor** | NPC。behavior tree + LLM dialogue (murakumo) | `virtual-actor` + `agent` (converse) |
| **WorldActor** | Island/Room の永続状態。terrain, weather, time-of-day | `virtual-actor` + `actor-state` (global scope) |
| **ItemActor** | アイテム/オブジェクト。物理 + インタラクション | `virtual-actor` + `inventory` |
| **EconomyActor** | 経済システム。通貨・取引・マーケット | `virtual-actor` + `economy` |

### Actor ↔ Godot Binding

```
Godot Node (client-side)
  ↕ etzhayyim_bridge addon (C1: Wasm↔JS)
    ↕ W Protocol (yata-wrpc, 583µs)
      ↕ App Actor (server-side)
        ↕ W Protocol Event Stream (operational state)
        ↕ Cypher graph (analytics: play count, social graph)
```

- **Client-authoritative**: 位置・アニメーション (低遅延優先)
- **Server-authoritative**: 経済・インベントリ・スコア (不正防止)
- **Hybrid**: 物理シミュレーション (client prediction + server reconciliation)

## KAMI World — 共有世界設計

### コンセプト

Minecraft の「サーバー」、Fortnite の「Island」、Roblox の「Experience」に相当する概念を **Island** と定義。

```
KAMI World (永続共有世界)
  ├─ Hub Island (ロビー、ポータル、ランキング)
  ├─ User Island A ← ユーザー A が KAMI Workbench で制作
  ├─ User Island B ← ユーザー B が制作
  ├─ Official Island X ← etzhayyim 公式ゲーム
  └─ ...
```

### Island 構造

```
Island {
  island_id:   nanoid
  owner_did:   AT Protocol DID (制作者)
  title:       string
  description: string
  genre:       enum { action, puzzle, rpg, sandbox, social, racing, rhythm, strategy }
  max_players: u32
  world_seed:  u64
  scene_tree:  CAS CID (Godot .tscn → MDAG)
  scripts:     list<CAS CID> (GDScript → MDAG)
  assets:      list<AssetRef> (assethub.etzhayyim.com 参照)
  state:       enum { draft, testing, published, archived }
  portal_pos:  Vec3 (Hub Island 上の Portal 位置)
}
```

### World Topology

```
                    ┌────────────────┐
                    │   Hub Island   │
                    │  (ロビー/ポータル) │
                    └───┬───┬───┬────┘
               Portal   │   │   │   Portal
          ┌─────────────┘   │   └─────────────┐
          ▼                 ▼                   ▼
    ┌───────────┐    ┌───────────┐       ┌───────────┐
    │ Island A  │    │ Island B  │  ...  │ Island N  │
    │ (RPG)     │    │ (Puzzle)  │       │ (Sandbox) │
    └───────────┘    └───────────┘       └───────────┘
```

- **Portal**: Hub Island 上の 3D オブジェクト。触れると対象 Island にシームレス遷移
- **Hub Island**: 全プレイヤーが最初に接続する共有空間。ランキングボード、ショップ、ポータル広場
- **Cross-Island**: W Protocol channel で Island 間チャット・フレンドリスト共有

### Persistence (3 層)

| 層 | 用途 | 技術 |
|---|---|---|
| **HOT** | プレイ中の Actor state | W Protocol Event Stream (`WRecord` + `G()`) |
| **WARM** | Island scene tree, scripts | MDAG CAS (B2 Arrow IPC) |
| **COLD** | Analytics, leaderboard history | Cypher graph (yata.etzhayyim.com) |

## KAMI Workbench — 対話的制作フロー

### UI Mode: custom (miniapp)

```toml
[ui]
mode = "custom"    # Scene Editor は Svelte miniapp
accent = "#f59e0b"
icon = "⛩️"
```

### Workbench 画面構成 (Mobile-First)

```
┌─────────────────────────┐
│  ⛩️ KAMI Workbench       │  ← SuperAppTabBar
├─────────────────────────┤
│ [Scene] [Script] [Asset]│  ← Tab 切り替え (ActionSheet)
├─────────────────────────┤
│                         │
│   Scene Tree Viewer     │  ← ドラッグ&ドロップでノード配置
│   (2D/3D viewport)      │  ← Godot WebGL preview
│                         │
├─────────────────────────┤
│  Inspector Panel        │  ← 選択ノードのプロパティ編集
│  Transform / Material   │
│  Script attach          │
├─────────────────────────┤
│ [Preview] [Test] [Publish]│ ← Action buttons
└─────────────────────────┘
```

### 制作フロー

```
1. Create Island
   → ジャンル選択 + テンプレート (assethub から starter kit)
   → Island metadata 生成 (nanoid, DID binding)

2. Scene Edit
   → Node tree 編集 (2D: Sprite, TileMap / 3D: MeshInstance, Area)
   → assethub.etzhayyim.com からアセットドラッグ配置
   → Transform (position, rotation, scale) をインスペクタで調整

3. Script
   → GDScript エディタ (Monaco / CodeMirror in miniapp)
   → Visual Script (node-based, Unreal Blueprint 風)
   → Actor binding: `@actor("PlayerActor")` annotation → WIT actor 自動生成

4. Test
   → Godot Web Export → iframe sandbox preview
   → マルチプレイテスト (W Protocol channel で招待)
   → cross-actor: QA agent (ISCO 2519) 自動テスト

5. Publish → games.etzhayyim.com
   → scene_tree + scripts を MDAG CAS commit
   → asset 参照を assethub CID で固定
   → games.etzhayyim.com の Island カタログに登録
   → Hub Island に Portal 自動生成
```

## AssetHub 連携

### Cross-actor Integration

```go
// KAMI → assethub.etzhayyim.com cross-actor 呼び出し
app.Command("", "browse-assets", cmdBrowseAssets,
    kotodama.AsAgentTool("Browse game assets from AssetHub"),
    kotodama.WithCapabilityTags("asset", "game-creation"),
)

func cmdBrowseAssets(ctx *kotodama.AppContext, body []byte) ([]byte, error) {
    var args struct {
        Query    string `json:"query"`
        Type     string `json:"asset_type"` // 3d_model, audio, image, texture, animation, live2d
        Format   string `json:"format"`     // glb, gltf, png, ogg, ...
        Limit    int    `json:"limit"`
    }
    json.Unmarshal(body, &args)

    // cross-actor: assethub の SearchAssets tool を呼ぶ
    result, err := kotodama.Invoke("", "SearchAssets", body)
    if err != nil { return nil, err }
    return result, nil
}
```

### Asset 参照モデル

```
AssetRef {
  asset_id:      string         // assethub asset_id
  blob_key:      string         // R2 blob key (CDN direct)
  asset_type:    string         // 3d_model | audio | image | texture | animation | live2d
  format:        string         // glb | gltf | png | ogg | ...
  thumbnail_url: string         // preview 表示用
  license:       string         // creative-commons | proprietary | ...
}
```

- KAMI Workbench で配置されたアセットは `AssetRef` として Island scene に埋め込み
- Godot runtime は `blob_key` → B2 CDN URL でランタイムロード
- アセット改変は Fork (assethub で `VARIANT_OF` 関係を作成)

## App 構成

### Components

| Component | nanoid | 役割 |
|---|---|---|
| **kami-workbench** | `k4m1w0rk` | Workbench UI + Island CRUD + publish pipeline |
| **kami-world** | `k4m1w0ld` | Shared World server。Hub Island + Portal 管理 + matchmaking |
| **kami-runtime** | `k4m1r0nt` | Godot WASM runtime ホスト。Actor lifecycle + physics sync |

### kami-workbench Commands

```go
var app = kotodama.NewApp(kotodama.AppDef{
    ID:          "k4m1w0rk",
    Name:        "kami-workbench",
    Description: "Interactive game creation workbench",
})

func init() {
    // Island CRUD
    app.Command("", "create-island", cmdCreateIsland,
        kotodama.AsAgentTool("Create new game island"),
        kotodama.WithCapabilityTags("game", "creation"),
    )
    app.Command("", "update-island", cmdUpdateIsland,
        kotodama.AsAgentTool("Update island metadata/scene"),
        kotodama.WithCapabilityTags("game", "creation"),
    )
    app.Command("", "list-islands", cmdListIslands,
        kotodama.AsAgentTool("List user's islands"),
        kotodama.WithCapabilityTags("game", "discovery"),
    )

    // Scene editing
    app.Command("", "save-scene", cmdSaveScene,
        kotodama.AsAgentTool("Save island scene tree to CAS"),
        kotodama.WithCapabilityTags("game", "scene"),
    )
    app.Command("", "save-script", cmdSaveScript,
        kotodama.AsAgentTool("Save GDScript to CAS"),
        kotodama.WithCapabilityTags("game", "script"),
    )

    // Asset integration
    app.Command("", "browse-assets", cmdBrowseAssets,
        kotodama.AsAgentTool("Browse game assets from AssetHub"),
        kotodama.WithCapabilityTags("asset", "game-creation"),
    )
    app.Command("", "attach-asset", cmdAttachAsset,
        kotodama.AsAgentTool("Attach AssetHub asset to island scene"),
        kotodama.WithCapabilityTags("asset", "scene"),
    )

    // Build & Publish
    app.Command("", "build-export", cmdBuildExport,
        kotodama.AsAgentTool("Build Godot Web Export for island"),
        kotodama.WithCapabilityTags("game", "build"),
    )
    app.Command("", "publish-island", cmdPublishIsland,
        kotodama.AsAgentTool("Publish island to games.etzhayyim.com"),
        kotodama.WithCapabilityTags("game", "publishing"),
    )
    app.Command("", "test-island", cmdTestIsland,
        kotodama.AsAgentTool("Launch test session for island"),
        kotodama.WithCapabilityTags("game", "testing"),
    )

    // W Protocol
    kotodama.HandleWCommit(handleWCommit)
    app.Handle("", method, handler, opts...)(handleConversationTask)
    app.Serve()
}
func main() {}
```

### W Protocol Event Stream Records

```sql
-- Islands (制作プロジェクト)
CREATE TABLE IF NOT EXISTS islands (
    island_id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL DEFAULT 'anon',
    user_id TEXT NOT NULL DEFAULT 'anon',
    actor_id TEXT NOT NULL DEFAULT '',
    owner_did TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    genre TEXT NOT NULL DEFAULT 'sandbox',
    max_players INTEGER DEFAULT 16,
    world_seed INTEGER DEFAULT 0,
    scene_cid TEXT DEFAULT '',       -- MDAG CAS CID
    scripts_json TEXT DEFAULT '[]',  -- list<CAS CID>
    assets_json TEXT DEFAULT '[]',   -- list<AssetRef>
    state TEXT DEFAULT 'draft',      -- draft | testing | published | archived
    portal_x REAL DEFAULT 0.0,
    portal_y REAL DEFAULT 0.0,
    portal_z REAL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Island versions (publish 履歴)
CREATE TABLE IF NOT EXISTS island_versions (
    version_id TEXT PRIMARY KEY,
    island_id TEXT NOT NULL,
    org_id TEXT NOT NULL DEFAULT 'anon',
    user_id TEXT NOT NULL DEFAULT 'anon',
    actor_id TEXT NOT NULL DEFAULT '',
    scene_cid TEXT NOT NULL,
    scripts_json TEXT NOT NULL,
    assets_json TEXT NOT NULL,
    export_cid TEXT DEFAULT '',  -- Godot Web Export artifact CAS CID
    published_at TEXT NOT NULL,
    FOREIGN KEY (island_id) REFERENCES islands(island_id)
);

-- Asset references (Island ↔ AssetHub binding)
CREATE TABLE IF NOT EXISTS island_assets (
    island_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    org_id TEXT NOT NULL DEFAULT 'anon',
    user_id TEXT NOT NULL DEFAULT 'anon',
    actor_id TEXT NOT NULL DEFAULT '',
    blob_key TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    node_path TEXT DEFAULT '',  -- Godot scene tree path
    transform_json TEXT DEFAULT '{}',
    PRIMARY KEY (island_id, asset_id, node_path),
    FOREIGN KEY (island_id) REFERENCES islands(island_id)
);
```

### W Protocol Channels

```toml
[space]
name = "KAMI World"
description = "Game creation workbench + shared world"
join_rule = "public"
history_visibility = "world-readable"

[[space.channels]]
name = "creations"
kind = "public"
description = "New island creations and updates"
default = true

[[space.channels]]
name = "playtesting"
kind = "public"
description = "Playtest invitations and feedback"

[[space.channels]]
name = "world-events"
kind = "public"
description = "KAMI World global events and announcements"
```

## Shared World Engine — Actor Model Detail

### Actor Lifecycle (Godot ↔ Server)

```
Player connects to Island
  → kami-world: matchmaking → assign Island instance
    → kami-runtime: spawn PlayerActor (virtual-actor)
      → Godot client: instantiate player scene
        → etzhayyim_bridge: bind to server actor

Game loop (16ms tick):
  Client → input events → etzhayyim_bridge
    → W Protocol (yata-wrpc) → kami-runtime
      → PlayerActor.invoke("move", {x, y, z})
        → WUpdate: update position
        → W Protocol broadcast → all clients in Island
          → Godot: interpolate remote players
```

### Multi-Island Architecture

```
kami-world (k4m1w0ld)
  ├─ Hub Island DO  ← 常時起動, portal registry
  ├─ Island-A DO    ← on-demand (sleep to $0)
  ├─ Island-B DO    ← on-demand
  └─ Matchmaker     ← player count balancing
```

- 各 Island は独立した DO instance (W Protocol Event Stream で状態管理)
- Hub Island は常時起動。他の Island は DO hibernation で sleep to $0
- Island 間移動は Portal → kami-world matchmaker → 新 DO instance に接続
- `kotodama:cloudflare/durable-object-websocket` で低遅延リアルタイム通信

### Godot Addons (games.etzhayyim.com 既存 + KAMI 追加)

| Addon | ID | 用途 | 出典 |
|---|---|---|---|
| `etzhayyim_bridge` | C1 | Wasm↔JS 通信 | 既存 (games) |
| `etzhayyim_social` | C5 | チャット, プレゼンス | 既存 (games) |
| `etzhayyim_leaderboard` | C6 | スコア, ランキング | 既存 (games) |
| `etzhayyim_economy` | C7 | 通貨, 取引 | 既存 (games) |
| `etzhayyim_engagement` | C8 | ログインボーナス, ミッション | 既存 (games) |
| `etzhayyim_inventory` | C9 | アイテム, スキン | 既存 (games) |
| `etzhayyim_gacha` | C10 | ガチャ | 既存 (games) |
| `etzhayyim_energy` | C11 | スタミナ | 既存 (games) |
| `etzhayyim_telemetry` | C12 | テレメトリ | 既存 (games) |
| **`etzhayyim_world`** | **C13** | **Island 接続, Portal, マルチプレイ同期** | **KAMI 新規** |
| **`etzhayyim_actor`** | **C14** | **Actor binding (server-authoritative entities)** | **KAMI 新規** |
| **`etzhayyim_assethub`** | **C15** | **AssetHub runtime loader (CDN fetch + cache)** | **KAMI 新規** |

## Publish Pipeline: KAMI → games.etzhayyim.com

```
1. save-scene / save-script
   → MDAG CAS commit (scene tree + scripts)
   → WUpdate: islands.scene_cid = new CID

2. build-export
   → Godot Web Export (headless build via murakumo agent)
   → artifact → R2 (export_cid)
   → WRecord: island_versions

3. publish-island
   → cross-actor: games.etzhayyim.com "register-game" tool
     → WRecord: game catalog
     → Hub Island: Portal 自動配置 (portal_x/y/z)
   → W Protocol WSend: "creations" channel
     → card type: application/vnd.etzhayyim.card.island-published
   → island.state = "published"

4. games.etzhayyim.com 上で
   → Island カタログに表示
   → Player が Portal から直接 join
   → Leaderboard / Achievements 自動連携 (kotodama:game WIT)
```

## WIT Extension (KAMI Domain)

`60-apps/etzhayyim-project-kami/wit/` に配置:

```wit
package etzhayyim:kami@1.0.0;

/// Island management for KAMI World.
interface island {
    record island-def {
        island-id: string,
        owner-did: string,
        title: string,
        description: string,
        genre: string,
        max-players: u32,
        world-seed: u64,
        scene-cid: string,
        state: string,
    }

    record portal {
        island-id: string,
        position: tuple<f32, f32, f32>,
        label: string,
    }

    create-island: func(def: island-def) -> result<island-def, string>;
    get-island: func(island-id: string) -> result<island-def, string>;
    list-portals: func() -> list<portal>;
    join-island: func(island-id: string, player-did: string) -> result<string, string>;
}

/// Scene tree serialization for Godot ↔ CAS.
interface scene {
    record scene-node {
        name: string,
        node-type: string,
        transform-json: string,
        children: list<scene-node>,
        script-cid: option<string>,
        asset-ref: option<string>,
    }

    save-tree: func(island-id: string, root: scene-node) -> result<string, string>;
    load-tree: func(cid: string) -> result<scene-node, string>;
}

/// AssetHub runtime bridge.
interface asset-bridge {
    record asset-ref {
        asset-id: string,
        blob-key: string,
        asset-type: string,
        format: string,
    }

    resolve-asset: func(asset-id: string) -> result<asset-ref, string>;
    resolve-batch: func(asset-ids: list<string>) -> list<asset-ref>;
}
```

## Migration: umu → kami

1. `etzhayyim-project-umu` の docs, games, wasm を `etzhayyim-project-kami` に統合
2. 既存 kami actor-naming は `kami-workbench` の内部機能として吸収 (Island/Actor 命名)
3. ドメイン: `umu.etzhayyim.com` → `kami.etzhayyim.com`
4. games.etzhayyim.com は公開配信面として維持 (変更なし)

## 差別化: Minecraft / Fortnite / Roblox との比較

| 特徴 | Minecraft | Fortnite | Roblox | **KAMI** |
|---|---|---|---|---|
| Engine | Custom Java | Unreal | Luau/Custom | **Godot (OSS)** |
| Script | Java mods | Verse | Luau | **GDScript + Visual Script** |
| Actor model | なし | なし | 簡易 | **kotodama:actor WIT (full)** |
| Asset market | なし | Store | Creator Store | **assethub.etzhayyim.com (open)** |
| Identity | Microsoft | Epic | Roblox | **AT Protocol DID** |
| Messaging | In-game | In-game | In-game | **W Protocol (E2E encrypted)** |
| Monetization | Marketplace | V-Bucks | Robux | **kotodama:game/economy (Gems)** |
| AI NPC | なし | なし | 簡易 | **murakumo LLM + Actor** |
| Persistence | Server files | Epic cloud | Roblox cloud | **W Protocol Event Stream + MDAG CAS + B2** |
| Cost model | Server hosting | Epic pays | Roblox takes 75% | **Sleep to $0 (DO hibernation)** |
| Federation | なし | なし | なし | **W Protocol MDAG federation** |
