---
id: ecl-license-dir-readme
title: "ECL — etzhayyim Covenant License (draft + objective function)"
status: proposed
doc_type: reference
topic: ecl-etzhayyim-covenant-license
authoritative: false
last_verified: 2026-06-17
related:
  - "2606172300"
---

# ECL — etzhayyim Covenant License (draft)

独自ライセンス **ECL** のドラフト一式。**原則(固定ルール)で制御せず、目的関数で動的に
評価する** — 基準は **子・孫の Wellbecoming(動的軌跡)**。

> ⚠️ DRAFT / proposed — 未発効。発効には Council Lv7+ unanimity (ADR-2606172300 D5)。
> それまで有効ライセンスは Apache 2.0 + Charter Rider v3.1 (`/CHARTER-RIDER.md`)。

| ファイル | 役割 |
|---|---|
| `ECL.md` | 設計の考え方・経緯 (Part I, 非規範) + ライセンス本文ドラフト (Part II) |
| `objective-function.edn` | 目的関数 J の機械可読 SSoT (dimensions / weights / screens / thresholds / fixtures) |
| `evaluate.bb` | J の動的評価器 (screens→objective→route) + self-test |

## 使い方

```bash
cd 90-docs/licenses/ecl
bb evaluate.bb                            # 5 fixtures self-test (子+孫=0.55 が基準)
bb evaluate.bb addictive-engagement-app   # 固定リスト外の害を目的関数が動的に捕捉
bb evaluate.bb --edn                      # 機械可読 verdict
```

## 設計の核

- **固定するのは掟でなく priority** (ADR-2606062100) → 目的関数の*構造*(どの priority を測るか)
  は Tier-0 固定、*重み/閾値*は Tier-1、*個別採点*は Tier-2 evidence。
- **二層**: 目的関数 (primary, dynamic) + 確定フロア screens (法的 backstop; CSAM/強制労働/
  兵器ビジネス/非対称監視/不可逆多世代危害)。tanemaki DD と同型 (screens→objective→route)。
- **基準 = 子・孫 wellbecoming**: 子 0.25 + 孫 0.30 = 0.55。残りは enabling condition。

詳細は `ECL.md` Part I、採用判断と数値根拠は ADR-2606172300 と
`90-docs/papers/2606171500-license-charter-fit-evaluation/`。
