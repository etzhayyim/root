# ai-gftd-project-open-robo

**Giemon** — 日本製オープンハードウェアロボットキットブランド。からくり儀右衛門 (田中久重) に由来。
初代製品: Giemon Otete (6軸アーム + クローラー)。将来: Hitogata, Quad 等に拡張予定。

## Scope

| 成果物 | パス | 状態 |
|---|---|---|
| BOM + 部品調達仕様書 | `bom/BOM-v1.md` | ✅ 作成済 |
| 機械設計仕様 + DH パラメータ | `cad-spec/mechanical-spec-v1.md` | ✅ 作成済 |
| HAT 回路図仕様 (KiCad) | `cad-spec/hat-schematic-spec-v1.md` | ✅ 作成済 |
| 組立説明書 | `docs/assembly-manual-v1.md` | ✅ 作成済 |
| Makuake / Kickstarter 商品文 | `marketing/crowdfunding-copy.md` | ✅ 作成済 |
| Amazon JP 商品ページ骨格 | `marketing/amazon-listing.md` | ✅ 作成済 |
| 公式サイト構成案 | `marketing/website-ia.md` | ✅ 作成済 |
| ICS3.5 サーボドライバー | `firmware/armcrawler/servo/ics_driver.py` | ✅ 作成済 |
| 逆運動学ソルバー | `firmware/armcrawler/kinematics/ik.py` | ✅ 作成済 |
| クローラードライバー | `firmware/armcrawler/crawler/motor_driver.py` | ✅ 作成済 |
| ROS2 ノード群 | `firmware/armcrawler/ros2/` | ✅ 作成済 |
| tsukuru CAD/PCB 設計フロースキーマ | `30-graph/graph-schema/sql_migrations/20260514150000_*` | ✅ 作成済 |

## Key Design Decisions

- SBC: Raspberry Pi 5（4GB）— UK設計・英国Sony工場製造。他の全部品は日本調達・日本製造
- アーム: 6軸 + グリッパー、KONDOまたはFutaba RS485バスサーボ
- クローラー: マブチモーター + タミヤTC-01互換トラック機構
- 構造体: ミスミアルミ押出し + Meviyカスタム切削部品
- 制御基板: ローム / 東芝ドライバIC使用、国内基板メーカー製造
- 電源: パナソニック18650セル

## SSoT

全テーブルデータ・製造パートナーリストは `bom/BOM-v1.md`。
