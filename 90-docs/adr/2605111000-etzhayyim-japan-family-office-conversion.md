---
id: adr-2605111000-etzhayyim-japan-family-office-conversion
title: etzhayyim Japan株式会社 シングルファミリープライベートオフィス化
status: proposed
doc_type: adr
topic: corporate-governance
authoritative: true
last_verified: 2026-05-11
authoritative_for:
  - corporate-action-gj-ca-2026-001
  - family-office-registration
---
# ADR-2605111000: etzhayyim Japan株式会社 シングルファミリープライベートオフィス化

**Date**: 2026-05-11
**Status**: draft → (approved pending 株主総会決議) → filed → registered
**Decider**: 河崎純真 (CEO / 代表取締役)
**Stakeholders**: 中村明子 (COO), k.bakshi (CLO)

---

## Context

etzhayyim Japan株式会社 (法人番号 9007-2846, did:web:etzhayyim.com) の定款第２条（目的）は
創業時に策定された23項目（介護・障害福祉・IT受託・職業紹介等）のままであり、
現在の実態（河崎家の資産管理・投資・承継）と乖離している。

加えて:
- 旧第22号「投資顧問業」の文言が残存しており、金融商品取引法上の不要リスクがある
- 法人の対外ポジションが不明確（介護会社か IT 会社か、という説明コスト）
- 中村明子COOが2026年3月に整理した「会社手続き簡略化リスト」（役員任期・招集通知・押印廃止）との合流機会がある

## Decision

定款第２条を全面変更し、**シングルファミリープライベートオフィス専用の6項目**に置き換える。

### 変更後 第２条（目的）

```
１．自己の資産の管理、運用及び保全に関する業務
２．有価証券、デジタルアセット及び暗号資産の保有、運用管理及び売買
３．不動産の取得、保有、管理及び処分
４．国内外の会社の株式又は持分の取得及び保有並びに当該会社の経営管理
５．資産の承継並びに相続及び事業承継の計画立案及び実行に関する業務
６．前各号に附帯関連する一切の業務
```

### 合流する変更（中村リスト）

| # | 変更内容 | 登記 | 登録免許税 |
|---|---------|------|----------|
| ① | 事業目的変更（本件） | 必要 | ¥30,000 |
| ② | 役員任期2年→10年 | 必要 | ¥30,000 |
| ③ | 招集通知期間 2週間→3日 | 不要 | — |
| ④ | 議事録押印廃止 | 不要 | — |

**登記費用合計: ¥60,000**（①②を同一申請に合流）

## Rationale

### 「自己の計算による」を使わない理由

e-mokuteki.com の投資関連定款594件を調査した結果、この修飾語の使用例は**0件**。
法令文・協会規則には登場するが、定款条項の修飾語としての実務前例がない。
投資助言業を目的から「書かない」だけで同等の規制区別が達成可能であり、
修飾語を追加する必要はない（詳細: `_working/family-office-registration/05-yoyo-legal-references.md`）。

### 金融規制ポジション

| 活動 | 要登録か |
|------|---------|
| 自己の上場株・債券・投信を売買・保有 | 不要（自己資産、金商法28条） |
| BTC等デジタルアセットの保有・売買 | 不要（自己保有、資金決済法） |
| スタートアップへの直接投資（株式取得） | 不要（自己勘定） |
| 自己所有不動産の管理・売却 | 不要（自己保有物件のみ、宅建業法） |
| 投資助言・投資運用業（他人のため） | 登録必要（金商法29条）→ **目的から除外** |

## Implementation

### 書類体系

| ファイル | 内容 |
|---------|------|
| `_working/family-office-registration/00-README.md` | プロジェクト概要・フロー |
| `01-teikan-shinkyu-taisho.md` | 新旧対照表（全23項目→6項目） |
| `02-kabunushi-sokai-gijiroku.md` | 臨時株主総会議事録草稿 |
| `03-touki-shinseisho.md` | 変更登記申請書草稿（東京法務局千代田出張所宛） |
| `04-taisho-documents.md` | 対外文書（会社概要JP/EN・LinkedIn・web） |
| `05-yoyo-legal-references.md` | 法令根拠・用例集（8ソース） |
| `06-teams-message-draft.md` | 取締役会Teams通知記録（送信済 2026-05-11） |

### Kotoba/Datomic トラッキング

```sql
-- メインレコード
SELECT * FROM vertex_corporate_action WHERE action_code = 'GJ-CA-2026-001';

-- 変更項目（登記要/不要・ステータス）
SELECT item_code, item_type, requires_registration, status
FROM vertex_corporate_action_item
WHERE action_vid LIKE '%GJ-CA-2026-001%'
ORDER BY item_code;

-- 登記進捗サマリ
SELECT action_code, action_status, total_items, registered_items,
       requires_reg_items, total_tax_jpy
FROM mv_corporate_action_status
WHERE action_code = 'GJ-CA-2026-001';
```

### スキーマ

- `30-graph/graph-schema/migrations/20260511100000_vertex_corporate_action.ts` — DDL
- `30-graph/graph-schema/migrations/20260511110000_seed_corporate_action_gj_fo_2026.ts` — シードデータ

### deps.toml

```toml
[etzhayyim_agent.identity]
business_type = "single-family-private-office"
corporate_action_code = "GJ-CA-2026-001"
corporate_action_status = "draft"  # draft → approved → filed → registered
business_purpose_registered = false  # 登記完了後 true へ
```

## Consequences

### 完了後に必要なアクション

1. **株主総会決議**: 書面決議（会社法318条）で全株主の同意書取得 → 議事録作成
2. **司法書士依頼**: 変更登記申請書 + 議事録を法務局に提出（決議日から2週間以内）
3. **登記完了確認**: 履歴事項全部証明書（法務局窓口 or オンライン ¥600）取得
4. **更新**:
   - `deps.toml [etzhayyim_agent.identity].business_purpose_registered = true`
   - `deps.toml [etzhayyim_agent.identity].corporate_action_status = "registered"`
   - 本ADR status を `registered` に更新
   - `vertex_corporate_action` の `status`, `registration_date` を更新
   - 取引金融機関へ会社概要届出書を更新

### 対外文書

- 会社概要（JP/EN）: `04-taisho-documents.md` 参照
- etzhayyim.com/about: 更新要
- LinkedIn company page: 更新要

## Related

- `_working/family-office-registration/` — 全書類 SSoT
- `deps.toml [etzhayyim_agent.identity]` — 法人設定 SSoT
- `ADR-2604251215` — etzhayyim agent authority bounds
- `vertex_corporate_action` — RW ガバナンス記録 SSoT
