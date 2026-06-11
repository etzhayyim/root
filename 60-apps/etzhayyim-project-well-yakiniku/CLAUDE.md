# etzhayyim-project-well-yakiniku

Camera-based Yakiniku Cooking Advisor. iPad 卓上カメラで肉・魚・野菜の焼き加減をリアルタイム判定し、部位ごとの最適な焼き方・薬味の相性を音声＋ビジュアルで案内する App agent。

## Design Principle: Vision-First Cooking Advisor + Print Integration

**カメラ映像 → Vision LLM 判定 → リアルタイム焼きガイド + 印刷用お肉札生成**

| Domain | Role | Description |
|---|---|---|
| `yakiniku.etzhayyim.com` | Cooking Advisor | iPad 卓上: カメラ映像からの焼き加減判定、焼き方ガイド、薬味レコメンド |

## Architecture

- **Runtime**: TS Native + Lexicon Contract
- **nanoid**: `yk1n1ku7`
- **Vision AI**: murakumo.etzhayyim.com (`qwen3-vl-8b`) — カメラフレームの肉部位認識・焼き加減判定
- **Backend**: App (部位DB、焼きレシピ、薬味マッピング、印刷テンプレート)
- **Transport**: Matrix protocol (command/conversation)

## Component

| Component | Folder | Domain | Description |
|---|---|---|---|
| yakiniku-component | `etzhayyim-wasm-yakiniku-yk1n1ku7` | yakiniku.etzhayyim.com | Vision advisor + print API |

## Food Categories

| Category | Examples |
|---|---|
| 牛 (Beef) | カルビ, ハラミ, タン, サーロイン, ミスジ, ザブトン, イチボ, シンシン |
| 豚 (Pork) | バラ, ロース, トントロ, カシラ, ホルモン |
| 鶏 (Chicken) | モモ, ムネ, セセリ, ボンジリ, 砂肝, レバー, ハツ |
| 魚 (Fish) | エビ, イカ, ホタテ, サーモン, シシャモ |
| 野菜 (Vegetables) | ネギ, ピーマン, シイタケ, トウモロコシ, カボチャ, ナス, タマネギ |

## Heat Source Types

| Type | Key | Characteristics |
|---|---|---|
| 炭火 (Charcoal) | `charcoal` | 遠赤外線、高温、香り付き、火力ムラあり |
| ガス (Gas) | `gas` | 安定火力、温度調整容易、均一加熱 |
| 鉄板 (Iron Plate) | `iron_plate` | 蓄熱性高、面焼き、油回り |

## Vision Analysis Pipeline

```
iPad Camera (front-facing, table mount)
  → MediaStream API → canvas frame capture (2fps)
    → base64 encode → POST /xrpc/yakiniku.v1.YakinikuService/AnalyzeFrame
      → murakumo.etzhayyim.com qwen3-vl-8b (vision)
        → { items: [{ cut, doneness, heat_source, action, condiments }] }
          → Matrix room event (cooking log)
          → UI overlay update (timer, flip alert, done alert)
```

## Print Integration (ISCO/ISIC 連携)

お肉の札（meat card）印刷機能。部位ごとの焼き方・薬味・イラストを含むカードを生成。

| Feature | Description |
|---|---|
| Meat Card | 部位名、推奨焼き時間、裏返しタイミング、相性薬味、イラスト |
| Print Format | A6/A7 サイズ、テーブル札向けレイアウト |
| ISCO 連携 | ISCO-7323 (印刷仕上げ工) — レイアウト・仕上げ品質 |
| ISIC 連携 | ISIC-C/1812 (印刷業) — 印刷工程管理 |
| Illustration | 部位のイラスト + 焼き加減の色味グラデーション |

### Meat Card Content

```
┌─────────────────────────┐
│  🥩 ハラミ (Skirt Steak) │
│  ─────────────────────  │
│  [部位イラスト]          │
│                         │
│  焼き方: 強火 → 中火     │
│  片面: 90秒 → 裏返し     │
│  仕上げ: レア〜ミディアム │
│                         │
│  相性薬味:               │
│  ・レモン汁              │
│  ・わさび                │
│  ・ネギ塩ダレ            │
│                         │
│  炭火🔥 ガス🔥 鉄板🔥   │
│  ◎      ○      ○       │
└─────────────────────────┘
```

## WIT Interfaces (etzhayyim:yakiniku@0.1.0)

| Interface | Description |
|---|---|
| `etzhayyim:yakiniku/vision` | カメラフレーム解析 — 部位認識、焼き加減判定、アクション推奨 |
| `etzhayyim:yakiniku/recipe` | 部位別焼きレシピ — 時間、温度、裏返しタイミング、熱源別調整 |
| `etzhayyim:yakiniku/condiment` | 薬味マッピング — 部位×熱源ごとの最適薬味・タレ |
| `etzhayyim:yakiniku/print` | 印刷用 meat card 生成 — SVG/PDF テンプレート、ISCO-7323 連携 |

## Capabilities

| Capability | Provider | Purpose |
|---|---|---|
| wasi:http/incoming-handler | http-server | Serve HTTP (iPad UI + API) |
| wasi:http/outgoing-handler | http-client | Call murakumo.etzhayyim.com (Vision LLM) |
| etzhayyim:agent/agent | agent-provider | LLM conversation for cooking advice |

## sql graph Tables

| Table | Key Columns | Purpose |
|---|---|---|
| `yakiniku_cuts` | `cut_id`, `category`, `name_ja`, `name_en`, `doneness_levels`, `timing_json` | 部位マスター |
| `yakiniku_condiments` | `condiment_id`, `name_ja`, `pairings_json` | 薬味マスター |
| `yakiniku_sessions` | `session_id`, `room_id`, `items_json`, `started_at` | 焼肉セッション履歴 |
| `yakiniku_print_cards` | `card_id`, `cut_id`, `template_svg`, `generated_at` | 印刷済み meat card |

## Doneness Levels

| Level | Japanese | Internal Temp | Visual Cue |
|---|---|---|---|
| `rare` | レア | 52-55°C | 表面焼色、中心赤 |
| `medium_rare` | ミディアムレア | 55-60°C | 薄ピンク中心 |
| `medium` | ミディアム | 60-65°C | ピンクほぼなし |
| `well_done` | ウェルダン | 70°C+ | 全体茶色 |
| `charred` | 焦げ | — | 黒焦げ（警告） |

## Build & Deploy

```bash
cd wasm/etzhayyim-wasm-yakiniku-yk1n1ku7
etzhayyim build
etzhayyim deploy --smoke-url https://yk1n1ku7.etzhayyim.com/health
```
