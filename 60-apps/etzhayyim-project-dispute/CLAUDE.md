# dispute.etzhayyim.com — 紛争・恫喝対策 Intelligence

業務委託紛争における虚偽請求・恫喝の証拠保全、支払証憑管理、法的対応支援。

## Architecture

| 項目 | 値 |
|---|---|
| **Runtime** | Single Worker (`d1sp7t3x`) |
| **UI** | yoro (zero frontend) |
| **Data** | SQL graph (kagami) |
| **Classification** | `restricted` (当事者 + 法務のみ) |
| **Domain** | `dispute.etzhayyim.com` / `d1sp7t3x.etzhayyim.com` |

## Path-Based DIDs

```
did:web:dispute.etzhayyim.com                          # controller
did:web:dispute.etzhayyim.com:case:{case_id}           # 紛争ケース
did:web:dispute.etzhayyim.com:counterparty:{hash}      # 相手方 (FNV-1a hash)
did:web:dispute.etzhayyim.com:counsel:{counsel_id}     # 顧問弁護士
```

## Collections (W Protocol Event Stream)

| Collection | Description |
|---|---|
| `com.etzhayyim.apps.dispute.caseRecord` | 紛争ケースメタデータ |
| `com.etzhayyim.apps.dispute.evidence` | 証拠 (メール, 振込記録, 契約書) — Blake3 hash |
| `com.etzhayyim.apps.dispute.payment` | 支払済証憑 (銀行振込明細, 請求書) |
| `com.etzhayyim.apps.dispute.threat` | 恫喝・脅迫記録 (分類 + severity + 法的根拠) |
| `com.etzhayyim.apps.dispute.response` | 対応記録 (送付済み回答, 内容証明) |
| `com.etzhayyim.apps.dispute.timeline` | 時系列イベントログ (裁判用) |

## Commands

| Command | Description |
|---|---|
| `create-case` | 紛争ケース新規作成 |
| `ingest-email` | メール取込 → Blake3 hash + CAS + LLM 自動分類 |
| `attach-payment` | 支払済証憑紐付け (振込明細, 請求書) |
| `classify-threat` | Murakumo LLM → 脅迫分類 + 法的根拠マッピング |
| `draft-response` | 回答文案生成 (内容証明向け) |
| `escalate-counsel` | 弁護士エスカレーション (timeline + evidence 一式) |
| `generate-timeline` | 時系列証拠一覧生成 (訴訟用) |
| `get-case` | ケース詳細取得 |
| `list-evidence` | 証拠一覧 |

## Threat Classification

| classification | 説明 | 法的根拠例 |
|---|---|---|
| `false_claim` | 虚偽請求 | 民法703条(不当利得) |
| `intimidation` | 恫喝 | 刑法222条(脅迫) |
| `defamation` | 名誉毀損 | 刑法230条(名誉毀損) |
| `trespass_threat` | 押しかけ予告 | 刑法130条(住居侵入) |
| `business_interference` | 業務妨害 | 刑法233条(信用毀損・業務妨害) |

## Severity

| Level | Score | 基準 |
|---|---|---|
| 0 | low | 不快だが違法性低い |
| 1 | medium | 脅迫的言辞 |
| 2 | high | 具体的脅迫 (住所特定, 押しかけ予告) |
| 3 | critical | 犯罪予告, 実害発生 |

## Evidence Integrity

- 全証拠に Blake3 content hash (改竄検出)
- CAS (Content-Addressable Storage) に原文格納
- timestamp は取込時刻 + 原文記載時刻の dual record

## Graph Relationships

```
DisputeCase -[:HAS_EVIDENCE]-> Evidence
DisputeCase -[:HAS_PAYMENT]-> Payment
DisputeCase -[:HAS_THREAT]-> Threat
DisputeCase -[:HAS_RESPONSE]-> Response
DisputeCase -[:TIMELINE_EVENT]-> Timeline
Threat -[:SUPPORTED_BY]-> Evidence
Payment -[:PROVES_FULFILLMENT]-> DisputeCase
```

## WIT Export

- `etzhayyim:dispute-resolution/case-management@1.0.0`
- `etzhayyim:dispute-resolution/evidence-preservation@1.0.0`
