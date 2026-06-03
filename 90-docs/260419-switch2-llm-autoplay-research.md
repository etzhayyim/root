# Switch 2 LLM Autoplay 研究メモ

作成日: 2026-04-19
ステータス: 調査 / PoC 前段階
用途: 研究用途で Nintendo Switch 2 のゲームを LLM に自動プレイさせる構成検討

## 目的

Switch 2 のゲーム画面を VLM に認識させ、LLM が生成した action を Pro Controller プロトコル経由で本体に送り返すループを構築する。ターン制 / slow-paced タイトルでの agent behavior / strategic reasoning 研究を想定。

## 全体構成

```
[Switch 2] --HDMI--> [capture card] --USB--> [PC]
                                              |
                                        OpenCV / ffmpeg
                                              |
                                         VLM API (Claude Opus 4.7 / GPT-4o)
                                              |
                                        action tokens (JSON)
                                              |
                                     [Pico / Linux BlueZ host]
                                              |
                                 ---USB-C HID / Bluetooth HID---
                                              |
                                         [Switch 2]
```

- action schema: 離散ボタン (`A`/`B`/`X`/`Y`/`L`/`R`/`ZL`/`ZR`/`+`/`-`/`HOME`/`CAPTURE`/dpad) + stick `(lx, ly, rx, ry) ∈ [-1, 1]`
- frame rate: VLM 推論 1–3s が支配 → ターン制 / ADV / 探索系向き、リアルタイム格ゲー不可

## Pro Controller プロトコル エミュレーション

### Path A: Bluetooth HID 偽装 (Linux + BlueZ)

- OSS: [`joycontrol`](https://github.com/mart1nro/joycontrol), [`NXBT`](https://github.com/Brikwerk/nxbt)
- BlueZ `input` plugin を disable → SDP record に Pro Controller の VID/PID (`0x057E/0x2009`) + HID descriptor 登録 → L2CAP PSM `0x11`/`0x13` で接続
- Switch 側 `0x01` subcommand (device info / SPI flash read / IMU enable / rumble / player LED) に正しく応答必須
- SPI flash の stick calibration 領域 (`0x603D~`) を偽造するのが実装の要
- 一次資料: [`dekuNukem/Nintendo_Switch_Reverse_Engineering`](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)

### Path B: USB HID 偽装 (有線、最も安定)

- Raspberry Pi Pico / Teensy 4.0 / Arduino Pro Micro で USB gadget として Pro Controller descriptor を送出
- 参考実装: `mizuyoukanao/Switch-Fightstick`, `progmem/Switch-Fightstick`
- Bluetooth ハンドシェイク回避できて実装軽量。Switch 2 の Pro Controller 2 は USB-C なので有線が自然

### Path C: ESP32 単体

- [`hrvach/ESP32_NINTENDO_SWITCH_CONTROLLER`](https://github.com/hrvach/ESP32_NINTENDO_SWITCH_CONTROLLER) 系
- 単体完結だが Switch 2 の新 pairing (物理ボタン同期要求) に未追従の可能性

## Switch 2 特有の注意事項

- 発売は 2025-06。コントローラ認証に暗号チャレンジが追加されたとの報告あり (2026-04 時点で reverse engineering 進行中)
- 既存 `joycontrol` / `NXBT` は Switch 2 で **そのままでは繋がらない可能性が高い**
- short-term 戦術:
  1. Switch 1 タイトルで PoC → 認識・行動ループの研究価値を先に確立
  2. USB-C 有線 HID (Pro Controller 2) 経路で Switch 2 対応を優先 — 無線より認証回避が楽な可能性
  3. Switch 2 Bluetooth 対応は GBAtemp / dekuNukem repo の issue tracker を継続監視

## PoC Milestone

| # | 内容 | 判定基準 |
|---|---|---|
| M1 | HDMI capture → VLM に 1 frame 送信 → 状態記述取得 | JSON で `{screen, menu, hp}` 等が返る |
| M2 | Pico USB HID で Switch 1 に A ボタン入力 | メニュー遷移を目視確認 |
| M3 | M1 + M2 を 1 ループに統合 (Switch 1 ADV) | LLM が自律でタイトル画面突破 |
| M4 | Switch 2 USB-C 有線で M2 再現 | Pro Controller 2 として認識 |
| M5 | Switch 2 Bluetooth で M2 再現 | 認証突破確認 |

## 開いている技術課題

- Switch 2 の controller 認証チャレンジの詳細 (RSA? HMAC? 鍵配布経路?)
- Pro Controller 2 の追加ボタン (C ボタン / GameChat) の HID report layout
- capture card のレイテンシ (HD60 X で ~60ms、研究許容範囲か要測定)
- VLM の UI 認識精度 — 日本語メニュー / 小さいテキストでの OCR 性能比較必要

## 関連研究 / 参考プロジェクト

- [`SIMA (Google DeepMind)`](https://deepmind.google/discover/blog/sima-generalist-ai-agent-for-3d-virtual-environments/) — 3D game 汎用エージェント
- [`Voyager (MineDojo)`](https://voyager.minedojo.org/) — Minecraft LLM agent、skill library 構築
- [`Cradle`](https://github.com/BAAI-Agents/Cradle) — 汎用 computer-use agent、画面認識 + キー入力ループの先例

## 本リポジトリとの関連

現状 `[[projects]]` 配下に該当プロジェクトなし。将来 PoC を本格化する場合は `60-apps/etzhayyim-project-<name>/` を起こすか、単独リポジトリで実験するのが妥当。graph 投影は不要 (外部ゲーム機なので AT Protocol repo に書く意味が薄い)。
