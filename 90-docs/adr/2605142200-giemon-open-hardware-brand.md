---
id: adr-2605142200-giemon-open-hardware-brand
title: "Giemon オープンハードウェアブランド確立"
status: active
doc_type: adr
topic: open-robo-brand
authoritative: true
last_verified: 2026-05-14
---

# ADR-2605142200 — Giemon オープンハードウェアブランド確立

**Status**: Accepted  
**Date**: 2026-05-14  
**Authors**: Jun Kawasaki  
**Supersedes**: —  
**Amended by**: ADR-2605142300 (Kaigo 応用プラットフォーム追加)

---

## Context

`60-apps/etzhayyim-project-open-robo` は当初「ArmCrawler JP」という製品名で設計・文書化された。
ブランドを **Giemon（ギエモン）** として統一し、製品ラインナップを体系化するため本 ADR を策定する。

ブランド名は田中久重（「からくり儀右衛門」）に由来。日本のものづくり精神とオープンソース哲学の統合を象徴する。

---

## Decision

### ブランド体系

| レイヤー | 名称 | 説明 | 状態 |
|---|---|---|---|
| ブランド | **Giemon** | 統一ブランド。全製品ラインに共通 | 確定 |
| 製品 1 | **Giemon Otete** | 6軸アーム + クローラー組立キット（初代） | 発売中 |
| 製品 2 | **Giemon Hitogata** | 2足歩行ヒューマノイド（17軸, 285mm） | 設計中 |
| 製品 3 | **Giemon Caterpillar** | 重装甲デュアルトラック UGV（380mm, LiDAR+ステレオカメラ） | 設計中 |
| 応用 | **Giemon Kaigo** | 3製品を介護・住宅・Well-Being に統合するプラットフォーム (ADR-2605142300) | 開発中 |

「おてて」は幼児語で手・腕を意味し、アームロボットの親しみやすさを表現する。  
「人型」は文字通り人間型ロボットを指す。  
「キャタピラー」は無限軌道（クローラー）型 UGV。

### ドメイン

- 統一ドメイン: `giemon.etzhayyim.com`（旧 `armcrawler.etzhayyim.com` から移行）
- SvelteKit appview nanoid route: `op3nr0b0.etzhayyim.com`（変更なし）
- 介護応用: `kaigo.etzhayyim.com` (nanoid: `kg8r2m5n`)

### 3D ビューア (kami-app-giemon WASM)

`giemon.etzhayyim.com/viewer.htm?model=arm|hitogata|caterpillar` で 3 モデル切替。
WASM バンドル 226KB、WebGPU/WebGL2 対応。

| WASM エントリ | 説明 |
|---|---|
| `run_giemon_v1` | Otete: アルミフレーム + 6 サーボ + クローラー |
| `run_giemon_hitogata_v1` | Hitogata: 17軸 2 足歩行、全高 285mm |
| `run_giemon_caterpillar_v1` | Caterpillar: 380mm UGV、LiDAR ドーム + ステレオカメラ + IMU/GPS |

`kaigo.etzhayyim.com` は同 WASM を iframe で共有（ビルド成果物重複なし）。

### 製品サイト構成（giemon.etzhayyim.com）

| URL | 内容 | 状態 |
|---|---|---|
| `/` | ランディングページ (3 製品タブ + 3D ビューア + Specs + BOM + Pricing) | ✅ 実装済 |
| `/product` | 製品詳細・DH パラメータ・HAT 仕様・SW スタック | ✅ 実装済 |
| `/product/specs` | 全スペック表（6 カテゴリ、60+ 行） | ✅ 実装済 |
| `/product/bom` | オープン BOM・GitHub ソースリンク | ✅ 実装済 |
| `/assembly` | ステップ組立マニュアル（6 ステップ） | 🔲 未実装 |
| `/firmware` | quickstart / ROS2 / API リファレンス | 🔲 未実装 |
| `/education` | 教育機関向け 3-pack ページ | 🔲 未実装 |
| `/buy` | 購入チャンネルハブ | 🔲 未実装 |
| `/blog` | 技術ブログ（mdsvex） | 🔲 未実装 |

### オープンハードウェアライセンス

| 対象 | ライセンス |
|---|---|
| ハードウェア設計（STEP/KiCad） | CERN-OHL-S v2 |
| ソフトウェア / ファームウェア | Apache License 2.0 |
| ドキュメント | CC BY-SA 4.0 |

---

## Naming Rules（LLM coding guardrail）

| 旧称 | 新称 | 適用範囲 |
|---|---|---|
| ArmCrawler / ArmCrawler JP | Giemon Otete | 全ドキュメント・コード |
| ArmCrawlerHAT | Otete HAT | 基板名称 |
| armcrawler_ros2 | otete_ros2 | ROS2 パッケージ名 |
| github.com/.../armcrawler-jp | github.com/.../otete | GitHub リポジトリ |
| Humanoid | Hitogata | 次期製品呼称 |
| humanoid (code) | hitogata | 変数・ID・WASM エントリ |

`firmware/armcrawler/` ディレクトリパスのリネームは別 PR で実施（ビルドパス影響調査後）。

---

## Consequences

- SEO: `armcrawler.etzhayyim.com` から `giemon.etzhayyim.com` へ CF DNS 301 リダイレクト設定が必要（未対応）
- Makuake / Kickstarter URL: `makuake.com/project/otete`、`kickstarter.com/projects/etzhayyim/otete`
- 将来の Hitogata 製品は同一 `etzhayyim-project-open-robo` リポジトリ配下に `appview/hitogata-hp/` として追加
- Caterpillar 製品は同 `appview/caterpillar-hp/` として追加
- kaigo.etzhayyim.com が介護向け 3D ビューアとして giemon.etzhayyim.com WASM を iframe で共有

---

## References

- `60-apps/etzhayyim-project-open-robo/CLAUDE.md`
- `60-apps/etzhayyim-project-open-robo/appview/open-robo-hp/`
- `40-engine/kami-engine/kami-app-giemon/src/lib.rs`
- ADR-2605142300 — Giemon Kaigo 介護応用プラットフォーム
- `30-graph/graph-schema/sql_migrations/20260514150000_*`（tsukuru CAD/PCB スキーマ）
