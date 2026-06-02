# Society6 飲食店防カビ法 及び 防カビ支援ファンド設計

## 概要

Society6 における飲食店の食品安全・防カビ対策を、AI三権分立フレームワーク（`THREE_POWERS_AI_GOV_DESIGN.md`）に基づき法律とファンドとして設計する。

**COFOG マッピング**:

| COFOG | 領域 | 本設計での役割 |
|-------|------|---------------|
| `07.4` Public Health Services | 公衆衛生 | カビ由来健康被害の予防・監視（主管） |
| `04.7.2` Hotels and Restaurants | 飲食業 | 飲食店の営業許可・衛生基準（共管） |
| `04.2.1` Agriculture | 農業 | 食品供給チェーンの品質管理（関連） |
| `05.3` Pollution Abatement | 汚染防止 | 建築環境のカビ汚染防止（関連） |

---

## Part I: 飲食店防カビ法（Food Establishment Mold Prevention Act）

### 第1章 総則

#### 第1条（目的）

本法は、Society6 領域内の飲食店におけるカビ（真菌）汚染を防止し、食品安全と市民（constituent）の健康を保護することを目的とする。

#### 第2条（定義）

| 用語 | 定義 |
|------|------|
| **飲食店** | Society6 領域内で食品の調理・提供を業として行う事業体。COFOG 0472 の管轄下にある全施設 |
| **カビ汚染** | 食品、調理器具、保管施設、または建築構造物における真菌（Aspergillus, Penicillium, Stachybotrys 等）の検出レベルが許容閾値を超える状態 |
| **許容閾値** | AI Public Health Performer（COFOG 0740）が定める、食品カテゴリ別・環境カテゴリ別のカビ胞子濃度上限 |
| **防カビ IoT センサー** | 温度・湿度・カビ胞子濃度を常時計測し、NATS JetStream 経由で監視データを送信するデバイス |
| **衛生格付** | AI performer による自動査定に基づく飲食店の衛生等級（S/A/B/C/F） |

#### 第3条（適用範囲）

本法は以下に適用される:
1. Society6 constituent が運営する全飲食店
2. Society6 領域内で食品を提供する一時的催事
3. Society6 constituent に食品を供給するサプライチェーン事業者

### 第2章 飲食店の義務

#### 第4条（防カビ管理計画の策定義務）

1. 飲食店は開業前に「防カビ管理計画（Mold Prevention Plan, MPP）」を策定し、COFOG 0740 Public Health Performer に提出しなければならない。
2. MPP には以下を含む:
   - 施設の温湿度管理方法
   - 食品保管区画の換気・除湿設計
   - カビ高リスク食材（穀類、乳製品、果実等）の管理手順
   - 清掃・殺菌スケジュール
   - カビ検出時の廃棄・隔離手順
3. MPP は年1回の更新を義務とする。
4. MPP は `wasi:keyvalue/store` に保管され、改竄不可のハッシュで `LegislationContract` に記録される。

#### 第5条（IoT 監視義務）

1. 飲食店は以下の区画に防カビ IoT センサーを設置しなければならない:
   - 冷蔵庫・冷凍庫内部
   - 食品保管庫（乾燥食品、穀物庫含む）
   - 調理場（厨房）
   - 客席の空調出口近傍（100席以上の施設のみ）
2. センサーデータは15分間隔で NATS JetStream に送信される。
3. データは COFOG 0740 performer が自動分析し、異常値検出時に即時アラートを発する。

#### 第6条（許容閾値）

| カテゴリ | 指標 | 許容閾値 |
|---------|------|---------|
| **食品保管庫（乾燥）** | 相対湿度 | ≤ 60% |
| **食品保管庫（乾燥）** | 浮遊カビ胞子 | ≤ 500 CFU/m³ |
| **冷蔵庫** | 温度 | ≤ 5°C |
| **冷蔵庫** | 浮遊カビ胞子 | ≤ 200 CFU/m³ |
| **調理場** | 相対湿度 | ≤ 70% |
| **調理場** | 浮遊カビ胞子 | ≤ 1,000 CFU/m³ |
| **食品表面（直接）** | アフラトキシン B1 | ≤ 2 μg/kg |
| **食品表面（直接）** | オクラトキシン A | ≤ 3 μg/kg |

閾値は COFOG 0740 performer と COFOG 0750 R&D Health performer の共同研究結果に基づき、年1回改定される。

#### 第7条（衛生格付制度）

1. AI performer は IoT データ、定期査察結果、過去の違反履歴を総合的に評価し、衛生格付を自動付与する。
2. 格付基準:

| 格付 | 条件 | 結果 |
|------|------|------|
| **S** | 直近12ヶ月閾値逸脱なし + MPP完全準拠 | 特別表彰 + ファンド優先融資 |
| **A** | 直近12ヶ月軽微逸脱3回以下 | 通常営業 |
| **B** | 直近12ヶ月軽微逸脱4〜10回 | 改善勧告 + 追加査察 |
| **C** | 直近12ヶ月重大逸脱1回以上 or 軽微逸脱11回以上 | 営業制限（改善まで） |
| **F** | 健康被害事案発生 or 改善命令不履行 | 営業停止 + 司法審査 |

3. 格付はブロックチェーン上に公開され、全 constituent が閲覧できる。
4. 格付に不服がある場合、Judicial Panel AI（COFOG 0330）に審査請求できる。

### 第3章 行政執行

#### 第8条（定期査察）

1. COFOG 0740 performer は全飲食店に対し、最低年2回の自動査察を実施する。
2. 査察は IoT データのリモート分析と、必要に応じた物理的サンプル採取を含む。
3. 査察結果は `ExecutionContract` に記録され、改竄不可。

#### 第9条（是正命令）

1. 閾値超過が検出された場合、COFOG 0740 performer は即時に以下を執行する:
   - **軽微逸脱**（閾値の1.5倍以内）: 24時間以内の是正勧告
   - **重大逸脱**（閾値の1.5倍超過）: 即時営業停止 + 48時間以内の是正命令
   - **危機的逸脱**（アフラトキシン等マイコトキシン検出）: 即時営業停止 + 食品回収命令 + 被害調査開始
2. 是正命令に対する不服は、72時間以内に Judicial Panel AI に申立可能。

#### 第10条（罰則）

| 違反 | 制裁 | 根拠 |
|------|------|------|
| MPP 未策定での営業 | GCC 500 罰金 + 営業停止 | 第4条違反 |
| IoT センサー未設置 | GCC 300 罰金 + 60日以内設置命令 | 第5条違反 |
| 是正命令不履行 | GCC 1,000 罰金 + 営業許可取消審査 | 第9条違反 |
| 虚偽データ送信 | GCC 5,000 罰金 + 営業許可即時取消 + 刑事審査 | 第5条・第8条違反 |
| 健康被害を伴うカビ汚染 | 被害額賠償 + GCC 10,000 罰金 + 営業許可取消 | 第6条違反 |

罰金は `ExecutionContract` 経由で自動徴収され、防カビ支援ファンドに充当される。

### 第4章 司法審査

#### 第11条（紛争解決）

1. 本法に基づく行政処分に対する不服は、Judicial Panel AI（COFOG 0330）に申立てる。
2. 司法 AI は以下を審理する:
   - IoT データの証拠能力・信頼性
   - 閾値の合理性（科学的根拠の検証）
   - 行政処分の比例原則適合性
   - 被害者の損害賠償請求
3. 判決は `JudiciaryContract` に不可逆に記録される。
4. 上訴審（二審）は上訴審 AI が担当し、法令解釈の統一を図る。

#### 第12条（違憲審査）

1. constituent は本法またはその執行が Society6 憲法に反すると主張する場合、違憲審査を請求できる。
2. 違憲判決が出た場合、該当条文は執行停止フラグが立てられ、立法 AI に改正が差し戻される。

### 第5章 附則

#### 第13条（施行日）

本法は `LegislationContract` への登録日から90日後に施行する。既存飲食店は施行日から180日以内に第4条・第5条の義務を履行しなければならない。

#### 第14条（法令 ID）

- **法令 ID**: `etzhayyim-LEG-2026-FOOD-MOLD-001`
- **COFOG 主管**: `07.4`（Public Health Services）
- **COFOG 共管**: `04.7.2`（Hotels and Restaurants）, `05.3`（Pollution Abatement）
- **LegislationContract ハッシュ**: 登録時に自動生成

---

## Part II: 防カビ支援ファンド（Mold Prevention Support Fund）

### 第1章 ファンド概要

#### 第15条（設置目的）

飲食店防カビ法の実効性を確保するため、飲食店の防カビ対策設備投資・技術導入を支援する「防カビ支援ファンド（Mold Prevention Support Fund, MPSF）」を設置する。

#### 第16条（法的根拠）

- 本ファンドは `Appropriation Contract`（予算配分コントラクト）として Ethereum L2 上に設置する。
- ファンドの運用は Executive Council AI（COFOG 01）が管轄し、Treasury GCC Management（`act-treasury-gcc-management`）により自動執行される。
- 予算上限・執行期限は立法 AI が `Appropriation Contract` で拘束する。

### 第2章 資金源

#### 第17条（原資構成）

| 資金源 | 割合（目標） | 説明 |
|--------|------------|------|
| **GCC 一般歳入** | 40% | Society6 税収からの一般財源割当 |
| **防カビ法罰金収入** | 25% | 第10条に基づく罰金の全額をファンドに充当 |
| **COFOG 07 Health 予算** | 20% | 公衆衛生予算の一部を食品安全に配分 |
| **COFOG 04 Economic Affairs 予算** | 10% | 飲食産業振興予算からの拠出 |
| **constituent 寄付** | 5% | DID認証済み constituent からの任意寄付（税控除対象） |

#### 第18条（年間予算規模）

1. 初年度予算: GCC 100,000
2. 以降は前年度の飲食店数・違反件数・健康被害発生率に基づき、COFOG 0740 performer が予算要求を策定し、立法 AI が承認する。
3. 予算消化率が50%を下回った場合、翌年度予算を自動縮小する。

### 第3章 支援プログラム

#### 第19条（設備投資補助金）

| 対象 | 補助率 | 上限 | 条件 |
|------|--------|------|------|
| 防カビ IoT センサー導入 | 80% | GCC 500/店舗 | 初回導入のみ |
| 除湿・換気設備改修 | 50% | GCC 2,000/店舗 | 衛生格付 B 以下の改善目的 |
| 食品保管庫の温湿度制御強化 | 60% | GCC 1,500/店舗 | MPP に基づく計画提出 |
| 建築構造の防カビ改修 | 40% | GCC 5,000/店舗 | COFOG 0530 performer の事前査定が必要 |

#### 第20条（技術導入支援）

1. **AI 監視システム導入支援**: COFOG 0740 performer が提供する標準監視テンプレートの無償配布
2. **防カビコンサルティング**: COFOG 0750 R&D Health performer による技術助言（年2回まで無償）
3. **従業員研修プログラム**: COFOG 0960 Education Subsidiary Services performer による e-ラーニング提供

#### 第21条（低利融資）

1. 衛生格付 S を維持する飲食店に対し、設備更新のための低利融資を提供する。
2. 融資条件:
   - 金利: GCC 基準金利 - 2%（下限 0%）
   - 融資上限: GCC 10,000/店舗
   - 返済期間: 最長5年
   - 担保: 営業許可のスマートコントラクト担保
3. 融資はスマートコントラクトで自動実行し、返済も GCC で自動引落とする。

#### 第22条（研究開発助成）

1. 防カビ技術の研究開発に対し、COFOG 0750 R&D Health performer と共同で助成を行う。
2. 対象テーマ:
   - 新規防カビ素材・コーティング技術
   - カビ早期検出 AI モデルの高度化
   - IoT センサーの低コスト化・小型化
   - 食品保存技術の革新
3. 助成額: プロジェクトあたり GCC 5,000〜50,000（審査制）

### 第4章 ファンド運営

#### 第23条（ガバナンス）

```
Appropriation Contract (Ethereum L2)
  ├─ 立法: 予算上限・使途制限を定義
  ├─ 行政: Executive Council AI が日常運用
  │   ├─ COFOG 0740 performer: 補助金・融資の審査・執行
  │   ├─ COFOG 0472 performer: 飲食店との窓口
  │   └─ Treasury (act-treasury-gcc-management): GCC 入出金管理
  ├─ 司法: 不正受給・不服に対する裁定
  └─ 監査: Auditor Agent が全取引を検証
```

#### 第24条（透明性）

1. ファンドの全取引は Ethereum L2 上に記録され、全 constituent が閲覧できる。
2. 四半期ごとに Auditor Agent が transparency report を公開する。
3. レポートには以下を含む:
   - 資金流入・流出の明細
   - 補助金・融資の承認・却下件数と理由
   - 衛生格付の分布変化
   - カビ関連健康被害の発生率推移
   - 投資対効果（ROI）分析

#### 第25条（不正受給防止）

1. 補助金・融資の申請は DID 認証必須。
2. IoT センサーデータと照合し、設備導入の事実を自動検証する。
3. 不正受給が判明した場合:
   - 補助金の全額返還 + GCC 2,000 罰金
   - 融資の即時全額返済要求
   - 衛生格付の即時 F 降格
   - Judicial Panel AI による刑事審査

### 第5章 KPI と評価

#### 第26条（成果指標）

| 指標 | 目標値（施行3年後） | 計測者 |
|------|-------------------|--------|
| カビ由来食中毒発生率 | 前年比 -80% | COFOG 0740 performer |
| 衛生格付 S/A 比率 | 全飲食店の 70% 以上 | COFOG 0740 performer |
| IoT センサー普及率 | 全飲食店の 95% 以上 | COFOG 0472 performer |
| ファンド投資回収率 | 健康被害削減額 ≥ ファンド支出額 | Auditor Agent |
| 閾値超過即時検出率 | 99% 以上（15分以内） | COFOG 0740 performer |
| constituent 満足度 | 80% 以上（飲食安全に関する調査） | COFOG 0740 performer |

#### 第27条（法令改定トリガー）

1. KPI が2四半期連続で目標を下回った場合、Executive Council AI は法改正案を起案する義務を負う。
2. 新たなカビ種による未知のリスクが検出された場合、緊急命令として閾値の暫定改定を行い、事後に立法追認を得る。

---

## Part III: 実装アーキテクチャ

### コンポーネント間連携

```
IoT Sensors (温度/湿度/カビ胞子)
  │
  ├─ NATS JetStream (gov-pubsub)
  │   │
  │   ├─ COFOG 0740 Public Health Performer ──wRPC──> Alert Engine
  │   │   ├─ 閾値監視 (リアルタイム)
  │   │   ├─ 衛生格付 自動計算
  │   │   └─ 是正命令 発行 → ExecutionContract
  │   │
  │   ├─ COFOG 0472 Hotels/Restaurants Performer
  │   │   ├─ 飲食店台帳管理
  │   │   ├─ MPP 受付・更新
  │   │   └─ ファンド申請窓口
  │   │
  │   └─ COFOG 0750 R&D Health Performer
  │       ├─ 閾値研究・改定提案
  │       └─ 防カビ技術研究助成管理
  │
  ├─ Ethereum L2 Smart Contracts
  │   ├─ LegislationContract: 法令テキスト + ハッシュ
  │   ├─ AppropriationContract: ファンド予算拘束
  │   ├─ ExecutionContract: 査察記録・是正命令・罰金
  │   └─ JudiciaryContract: 不服審査・判決
  │
  └─ Society6 Portal (society6.etzhayyim.com)
      ├─ 衛生格付 公開ダッシュボード
      ├─ ファンド申請フォーム
      └─ 透明性レポート閲覧
```

### WIT Interface（案）

```wit
// etzhayyim:food-safety/mold-prevention
interface mold-prevention {
    // 閾値チェック
    record sensor-reading {
        establishment-id: string,
        zone: zone-type,
        temperature-celsius: float64,
        relative-humidity-percent: float64,
        mold-spore-cfu-m3: u32,
        timestamp: u64,
    }

    enum zone-type {
        cold-storage,
        dry-storage,
        kitchen,
        dining-area,
    }

    enum severity {
        normal,
        minor-violation,
        major-violation,
        critical-violation,
    }

    record threshold-result {
        severity: severity,
        violated-metrics: list<string>,
        recommended-action: string,
    }

    // センサーデータ受信 → 閾値判定
    check-thresholds: func(reading: sensor-reading) -> threshold-result

    // 衛生格付取得
    get-hygiene-rating: func(establishment-id: string) -> string

    // MPP 提出
    submit-mold-prevention-plan: func(establishment-id: string, plan-hash: string) -> bool

    // ファンド申請
    record fund-application {
        establishment-id: string,
        program-type: string,
        requested-amount-gcc: u64,
        purpose: string,
    }

    record fund-decision {
        approved: bool,
        amount-gcc: u64,
        reason: string,
        contract-hash: string,
    }

    apply-fund: func(application: fund-application) -> fund-decision
}
```

### 法令メタデータ

```jsonld
{
  "@context": ["https://schema.org", {"cofog": "https://unstats.un.org/unsd/classifications/Econ/COFOG#"}],
  "@type": "Legislation",
  "identifier": "etzhayyim-LEG-2026-FOOD-MOLD-001",
  "name": "Food Establishment Mold Prevention Act",
  "name:ja": "飲食店防カビ法",
  "legislationType": "Act",
  "dateEnacted": "2026-03-01",
  "legislationAppliedTo": ["cofog:07.4", "cofog:04.7.2", "cofog:05.3"],
  "isPartOf": {
    "@type": "LegislativeBody",
    "name": "Society6 Legislative Assembly AI",
    "identifier": "society6-legislative-assembly"
  },
  "hasPart": [
    {"@type": "Legislation", "name": "Part I: 飲食店防カビ法", "identifier": "etzhayyim-LEG-2026-FOOD-MOLD-001-P1"},
    {"@type": "Legislation", "name": "Part II: 防カビ支援ファンド", "identifier": "etzhayyim-LEG-2026-FOOD-MOLD-001-P2"}
  ],
  "funding": {
    "@type": "MonetaryGrant",
    "name": "Mold Prevention Support Fund (MPSF)",
    "identifier": "etzhayyim-FUND-2026-MPSF-001",
    "amount": {"@type": "MonetaryAmount", "currency": "GCC", "value": 100000},
    "funder": {"@type": "GovernmentOrganization", "name": "Society6 Treasury"}
  }
}
```

---

## 標準フロー

### フロー1: 新規飲食店の開業

```
1. 飲食店 → MPP 策定 → COFOG 0472 に提出
2. COFOG 0740 → MPP 審査（AI自動 + 必要時 R&D 参照）
3. 承認 → LegislationContract に MPP ハッシュ登録
4. 飲食店 → IoT センサー設置 → ファンド補助金申請
5. COFOG 0740 → 補助金審査 → Appropriation Contract 経由支出
6. 営業開始 → 衛生格付 A 付与（初期値）
```

### フロー2: カビ閾値超過の検出と是正

```
1. IoT センサー → 閾値超過データ → NATS JetStream
2. COFOG 0740 → severity 判定
3. minor: 24h 是正勧告 → ExecutionContract 記録
4. major: 即時営業停止 → 是正命令 → ExecutionContract 記録
5. critical: 即時営業停止 + 食品回収 + COFOG 0740 緊急調査
6. 飲食店 → 是正完了報告 → COFOG 0740 確認 → 営業再開
7. 不服 → Judicial Panel AI（COFOG 0330）に申立
```

### フロー3: ファンド年度サイクル

```
1. COFOG 0740 → 翌年度予算要求策定（KPI 実績ベース）
2. Executive Council AI → 予算案として立法 AI に提出
3. Legislative Assembly AI → 市民投票 → 可決
4. Appropriation Contract 更新 → Treasury GCC 配分
5. 四半期 → Auditor Agent → transparency report 公開
6. 年度末 → KPI 評価 → 法改正要否判定
```

---

## Appendix: 日本法との対照

本法の設計は以下の日本法を参照し、Society6 の AI 三権分立フレームワークに適応したものである。

| 日本法 | Society6 対応 |
|--------|-------------|
| 食品衛生法（昭和22年法律第233号） | 第4〜6条（管理計画・監視義務・閾値） |
| 食品安全基本法（平成15年法律第48号） | 第1条（目的）、第26条（リスク評価） |
| HACCP（危害分析重要管理点）制度 | 第4条 MPP（HACCP 原則を AI 監視に拡張） |
| 建築物衛生法（ビル管法） | 第5条 IoT 監視（建築環境のカビ管理） |
| 中小企業等経営強化法 | 第19〜22条（ファンド支援プログラム） |

---

## 改定履歴

| 版 | 日付 | 内容 |
|----|------|------|
| 1.0 | 2026-03-01 | 初版策定 |
