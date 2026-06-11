---
id: adr-2605142300-giemon-kaigo-care-platform
title: "Giemon Kaigo — ロボット介護応用プラットフォーム設計"
status: active
doc_type: adr
topic: kaigo-platform
authoritative: true
last_verified: 2026-05-14
---

# ADR-2605142300 — Giemon Kaigo 介護応用プラットフォーム

**Status**: Accepted
**Date**: 2026-05-14
**Authors**: Jun Kawasaki
**Supersedes**: —
**Amends**: ADR-2605142200 (Giemon ブランド体系に Kaigo 応用を追加)

---

## Context

Giemon ロボット（Otete / Hitogata / Caterpillar）は教育・研究向けキットとして設計されているが、
その技術特性（6軸アーム、ヒューマノイド動作、自律巡回）は在宅介護の課題（ADL 補助・リハビリ・見守り）に
直接応用できる。日本では 2025 年時点で 65 歳以上人口が 29.3% を超えており、在宅介護ロボット需要は急増している。

同時に、既存の介護プラットフォームは「欠損モデル」（できないことを評価して給付する受動型）に依存しており、
当事者の能力・意欲・社会参加を育てる視点が欠如している。

本 ADR は `kaigo.etzhayyim.com`（`etzhayyim-project-kaigo`）の応用プラットフォームとして Giemon ロボットを位置づけ、
アーキテクチャを確定する。

---

## Decision

### 製品・ロボット役割分担

| ロボット | 介護応用役割 | 主な機能 |
|---|---|---|
| **Giemon Otete** | 在宅 ADL 支援ロボット | 服薬管理・物品搬送（可搬 500g）・見守り巡回・遠隔操作・転倒物検知 |
| **Giemon Hitogata** | リハビリ・交流ロボット | 17軸動作誘導・認知トレーニング・AI 会話・活動ログ記録・ケアマネレポート |
| **Giemon Caterpillar** | 自律見守り UGV | SLAM 巡回・転倒検知（AI）・夜間 IR カメラ・緊急通報・Nav2 自律走行 |

### アーキテクチャ

```
kaigo.etzhayyim.com (SvelteKit 5 / CF Worker kg8r2m5n)
├── 3D ビューア               ← iframe: giemon.etzhayyim.com/viewer.htm?model=arm|hitogata|caterpillar
├── 住宅改修支援モジュール      ← フロントエンド試算 + XRPC calcHousingReformBenefit
├── 介護保険ナビ               ← フロントエンド静的 + XRPC estimateCareCost
├── Well-Becoming ケアサークル ← kaigo.etzhayyim.com:circle 経路 (Well-Being 5 軸)
└── Murakumo AI 会話          ← Opus 4.6 via MURAKUMO_SERVICE binding
```

**3D ビューア共有**: `giemon.etzhayyim.com` の WASM バンドル（`kami_app_giemon.{js,wasm}` 226KB）を
`kaigo.etzhayyim.com` 側の iframe で cross-origin 利用。WASM の重複デプロイなし。

### 介護保険制度対応

#### 住宅改修費給付（介護保険第7条）

| 項目 | 値 |
|---|---|
| 給付上限 | 20 万円（1 回限り、転居・要介護度大幅変化で再給付可） |
| 自己負担 | 1〜3 割（所得に応じて） |
| 対象工事 | 手すり・段差解消・床材変更・引き戸改修・洋式トイレ化・スロープ |
| AI 試算 | `calcHousingReformBenefit(care_level, total_cost_jpy)` → `{covered, benefit, copay, selfPay}` |

#### 居宅サービス月額支給限度額

| 要介護度 | 月額上限 (円) |
|---|---|
| 1 | 50,320 |
| 2 | 105,310 |
| 3 | 167,650 |
| 4 | 197,050 |
| 5 | 270,480 |

### Well-Becoming モデル（欠損 → 能力成長）

公的介護の「欠損モデル」に対し、kaigo.etzhayyim.com は **Well-Becoming 5 軸**で能力成長を計測する。

| 軸 | 測定源 |
|---|---|
| Engagement | ロボット巡回頻度・サークル参加・外出日数 |
| Competence | capability proficiency・ロボット操作習熟度 |
| Contribution | 時間銀行 deposit・知恵アーカイブ |
| Growth | 新活動挑戦率・Hitogata リハビリ達成率 |
| Resilience | Caterpillar バイタルデータ安定性・サポートバッファ |

詳細: `60-apps/etzhayyim-project-kaigo/CLAUDE.md`

### 料金プラン

| プラン | 月額 | 主な対象 |
|---|---|---|
| Basic | ¥9,800 | 個人・家族（AIナビのみ、ロボット不要） |
| Robot Pro | ¥29,800 | Giemon ロボット保有世帯・施設小規模導入 |
| Facility | 要相談 | 介護施設・病院・自治体 |

### XRPC エンドポイント

| NSID | 種別 | 説明 |
|---|---|---|
| `com.etzhayyim.apps.kaigo.getProduct` | query | プラットフォーム製品情報 |
| `com.etzhayyim.apps.kaigo.calcHousingReformBenefit` | query | 住宅改修費給付額試算 |
| `com.etzhayyim.apps.kaigo.estimateCareCost` | query | 月額介護費用目安 |

### Path-based DID エージェント（kaigo.etzhayyim.com）

| Agent DID | 役割 |
|---|---|
| `did:web:kaigo.etzhayyim.com:capability` | Well-Being 能力マップ |
| `did:web:kaigo.etzhayyim.com:mutual_care` | ケア交換記録 |
| `did:web:kaigo.etzhayyim.com:time_bank` | 時間銀行（非貨幣） |
| `did:web:kaigo.etzhayyim.com:circle` | ケアサークル（近隣互助 5-8人） |
| `did:web:kaigo.etzhayyim.com:vitality` | バイタリティ 3 軸 |
| `did:web:kaigo.etzhayyim.com:mentorship` | 知恵伝承 + Opus 4.6 アーカイブ |
| `did:web:kaigo.etzhayyim.com:journey` | ライフジャーニー（成長物語） |

---

## Consequences

- `giemon.etzhayyim.com` と `kaigo.etzhayyim.com` は **独立した CF Worker デプロイ** を維持するが、
  WASM 3D ビューアは giemon.etzhayyim.com 側に一元化し iframe で共有。
- WAM NET 介護施設データ収集は `cmd_collect_wam_facilities` XRPC コマンドで実装予定。
- 介護保険費用の試算は参考値であり、実際の給付額は市区町村の審査で確定する旨を UI に明示済み。
- LLM ケアプラン提案は Murakumo Opus 4.6 を使用。医療・介護の診断・処方ではないことを免責事項に記載。

---

## References

- ADR-2605142200 — Giemon オープンハードウェアブランド確立
- `60-apps/etzhayyim-project-kaigo/CLAUDE.md`
- `60-apps/etzhayyim-project-kaigo/appview/kaigo-hp/`
- `giemon.etzhayyim.com/viewer.htm` (WASM 3D ビューア共有元)
- 厚生労働省 WAM NET: 介護サービス情報公表システム
- 介護保険法第 7 条（住宅改修費給付）
