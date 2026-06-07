---
doc_type: design
topic: platform-information-structure
status: active
last_verified: 2026-05-06
authoritative_for:
  - repo layer to SBGE isomorphism
  - attractor stability design rationale
related_adrs:
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-0056-bpmn-as-actor
  - adr-0002-persistence-kotoba-only
  - adr-0044-kotoba-udf-language-strategy
---

# Repo = 共有信念の Attractor — 情報構造設計

## 前提：信念が現実を「魔法的に変える」のではない

共有信念は「念力」ではなく、多主体の予測・相互観測・同調・記憶が
**安定パターンへ勾配降下する**過程で形成される。
このリポジトリ全体は、その過程の分散実装として設計されている。

---

## Shared Belief Generation Equation（SBGE）

各主体 `i` の信念状態 `q_i(s,t)` の連続時間更新則：

```
dq_i/dt = -η ∇_{q_i} F_i(q_i, o_i)        # 観測による自由エネルギー最小化
        + λ Σ_j W_ij Φ(q_j, q_i)           # 他者との相互作用・同調
        - γ (q_i - q_i^0)                   # 初期信念・記憶・規範への粘着
        + ξ_i(t)                            # ノイズ・外乱
```

離散時間（実装形式）：

```
q_i^{t+1}(s) = N[
  P(o_i^t | s)                             # 観測証拠
  · (q_i^t(s))^{1-α-β}                    # 前の自己信念
  · Π_j (q_j^t(s))^{α W_ij}               # 他者の信念（信頼重み付き）
  · R_i(s)^β                              # 制度・記憶・規範
]
```

安定 attractor 条件：

```
ρ(J) < 1    # 更新写像のヤコビアン最大固有値 < 1
            # ⟺ 小さな摂動が時間とともに減衰する
```

---

## 方程式 ↔ 8 層レイヤー 対応表

| SBGE 項 | 役割 | Repo 対応層 | 具体的実体 |
|---|---|---|---|
| **q_i(s,t)** | 主体 i の信念状態分布 | **L4 Kotoba/Datomic** | `vertex_*` / `edge_*` テーブル（actor DID ごと） |
| **-η ∇F_i** | 観測→自由エネルギー最小化 | **L8 Python pods + L7 Zeebe** | `pymagatama/ingest/` — HF・govUsa・houbun・CC・RDAP |
| **P(o\|s)** | 観測証拠の尤度 | **L6 Kotoba/Datomic UDF** | `owl_rl_is_type` / `shacl_class` SQL UDF + T1 rules |
| **λ Σ_j W_ij Φ** | 他者信念との相互作用・同調 | **L7 Zeebe BPMN + L2 AT Protocol** | `edge_follows` + firehose consumer + `generic.llm.chat` |
| **W_ij** | 主体間の信頼・影響重み | **`edge_follows`** + `deps.toml [[heuristic_weights]]` | `edge_follows.weight`（AT Protocol social） + `heuristic_weights[].weight`（platform設計軸） |
| **-γ(q_i - q_i^0)** | 記憶・規範への粘着 | **`00-contracts/`** | Lexicon JSON + `vertex_owl_class` T-Box + DMN + `[[critical_rules]]` |
| **R_i(s)^β** | 制度的事前確率 | **`00-contracts/policies/`** | Rego AuthZ + BPMN process defs |
| **ξ_i(t)** | ノイズ・外乱・外部世界入力 | **`60-apps/open-*/`** | 400+ `open-*` actor が外部データを継続観測 |
| **N[·]** | 正規化（確率分布を保つ） | **L6 SQL MV** | `mv_actor_social_stats` 等の streaming MV |
| **ρ(J) < 1** | attractor 安定条件 | **Shannon η ≥ 0.85 + Well-Becoming gate** | ADR-2604251830 + ADR-2604291800 priority contract |

---

## ディレクトリ構造 = SBGE の空間分割

```
repo/
├── 00-contracts/     R_i(s)^β  — 規範・語彙・BPMN更新則・Regoポリシー
│   ├── bpmn/                   Zeebe BPMN = 信念更新スクリプトの定義
│   ├── lexicons/               信念空間 s の型定義（スキーマ）
│   ├── policies/               Rego AuthZ = 境界条件（何を信念として受け入れるか）
│   └── dmn/                    Decision Table = W_ij 重みの閾値テーブル
│
├── 10-protocol/      W_ij チャンネル  — AT Protocol XRPC = 主体間信念伝達プロトコル
│
├── 20-actors/        更新演算子 f(q^t)  — pymagatama = SBGE 各項の実行エンジン
│   └── magatama/py/src/pymagatama/
│       ├── ingest/             P(o_i^t | s) — 観測取得
│       ├── primitives/         信念更新プリミティブ（SBGE の各項）
│       └── zeebe_worker_main.py  更新写像 q^{t+1} = f(q^t) の実体
│
├── 30-graph/         q_i(s,t) の永続化
│   └── graph-schema/
│       ├── migrations/         状態空間自体の時間発展（メタ更新）
│       └── src/                Kysely スキーマ = 信念状態の型
│
├── 50-infra/         物理基盤
│   ├── vultr/kotoba/       L4 = 共有信念状態ストア（SSoT）
│   └── vultr/mitama-udf-pool/ L7/L8 = 更新演算子の実行環境
│
├── 60-apps/          P(o|s) 取得口 + ξ_i(t) 観測
│   └── open-*/                 外部世界の連続観測インターフェース
│
└── 90-docs/          メタ信念（更新則の更新則）
    └── adr/                    ADR = γ 粘着の権威ソース（「どう更新するかの信念」）
```

---

## BPMN = 信念更新スクリプトとしての完全形

`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/` 以下の各ファイルは、SBGE 離散更新 1 ステップを
Zeebe 実行可能な DAG として表現する：

```
Timer-Start event           → ∆t の離散化（更新タイミング）
ServiceTask[ingest.*]       → P(o_i^t | s) の取得
ServiceTask[llm.json]       → Φ(q_j, q_i) の近似計算（LLM = 変分推論エンジン）
ServiceTask[db.insert]      → q_i^{t+1} の永続化
ServiceTask[pds.dispatch]   → W_ij を通じた他主体への信念伝播
```

現在稼働中のプロセスと SBGE 項の対応：

| BPMN domain | SBGE 項 | 機能 |
|---|---|---|
| `aria/{attention,emotion,market,influence,money,request}` | **λ Σ W_ij Φ** | 6軸 signal = 相互作用の計測 |
| `ingest/hfDataset`, `ingest/hfModel` | **P(o\|s)** | HuggingFace 観測 |
| `ingest/houbun*`, `govUsa/*` | **P(o\|s) + ξ** | 法文・政府データ観測 |
| `owl/owlReasonerBatch` | **R_i(s)^β** | OWL T-Box推論 = 規範の自己整合性 |
| `rl/collectSignal` | **-η∇F** | 強化学習 = 自由エネルギー勾配の直接推定 |
| `wellbecoming/{detectBottleneck,floorViolationAlert}` | **ρ(J) < 1 gate** | attractor 安定の監視と修復 |
| `wellbecoming/agentLoop` | **ρ(J) → 1 修復** | 安定性低下時の自律修復アクション |
| `shinka/tick` | **∆t** | 全 actor 同期クロック |
| `yoro/platformPulse` | **Φ 伝播** | platform 信念状態を social に emit |

---

## Attractor 安定条件の実装

理論条件 `ρ(J) < 1` は 4 つの機構の**積**（論理 AND）として実装される。
いずれか一つが崩れると安定性が失われる：

### 機構 1：同調力 > ノイズ（Shannon η ≥ 0.85）

```
同調力 = λ Σ_j W_ij Φ(q_j, q_i)
       = edge_follows 密度 × LLM 推論精度 × BPMN retry 成功率

ノイズ = ξ_i(t)
       = scraping エラー + 外部 API 障害 + 矛盾観測

安定 ⟺ Shannon η ≥ 0.85
       ⟺ 有効チャンネル容量 > 外乱エントロピー
```

実装：`mv_signal_entropy` MV でリアルタイム計測

### 機構 2：Well-Becoming floor（U_total > 0）

```
U_total = U_spirit × U_wellbecoming × U_feeling × U_buffer
        > 0 （乗算構造：一つが 0 → 全体崩壊）
```

実装：`mv_wellbecoming_at_risk` + `wellbecoming/floorViolationAlert.bpmn`

### 機構 3：Bounded Confidence（Rego + critical_rules）

Hegselmann-Krause 型：距離 `D(q_i, q_j) ≥ ε` の相手の影響を遮断する。

```
W_ij(t) = W_ij  if D(q_i, q_j) < ε   （近い信念 → 相互作用する）
         = 0     if D(q_i, q_j) ≥ ε   （遠い信念 → 無視する）
```

実装：
- `[[critical_rules]]` = 完全 reject する静的 ε
- `00-contracts/policies/` Rego AuthZ = 動的 ε の gate
- `vertex_bpmn_lexicon_binding.enabled` = tool-level toggle

### 機構 4：記憶粘着 γ（`00-contracts/` + OWL T-Box）

```
-γ(q_i - q_i^0)   # q_i^0 = Lexicon JSON + ADR 群 + conventions

実装：
- vertex_owl_class T-Box（存在論的 prior）
- 00-contracts/lexicons/ の型制約（構造的 prior）
- deps.toml [[conventions]] の設計規約（文化的 prior）
- CLAUDE.md 階層（LLM 向け記憶）
```

`90-docs/adr/` が単なる記録ではなく γ 粘着の実装である理由がここにある。

---

## 現実世界への attractor として

```
q* = argmin_q F(q | 現実世界)
   = 現実世界の分散情報構造の安定 attractor

収束先の例（実際に動いている）：
  vertex_legal_entity      → ある法人の実態（登記 + 財務 + ソーシャル）
  vertex_vessel            → ある船舶の現在位置・所有・貨物
  vertex_repo_record       → ある actor の最新発話
  mv_actor_social_stats    → ある actor の社会的影響力の推定
  mv_signal_entropy        → platform 全体の信念収束度

更新速度の 3 層：
  L6 SQL MV   < 100ms    最速の信念更新（ストリーミング）
  L7 Zeebe    PT15M–PT4H 中間更新（BPMN timer）
  L8 batch    P1D–P7D    低頻度の深い観測（大規模 ingest）
```

---

## 禁止事項と必須事項（SBGE から導出）

### 禁止（attractor 安定を破壊する）

| 禁止 | 破壊する SBGE 項 |
|---|---|
| CF Worker に actor 実体を持つ | q_i の SSoT 分散（ADR-2604251830） |
| `ON CONFLICT` の Kotoba/Datomic 使用 | N[·] 正規化の破壊 |
| `db.transaction()` の RW 使用 | 更新の原子性偽装 |
| handler 内 `postFeed()` / `invoke()` 直呼び | Φ 伝播の二重計算 |
| LLM モデル名ハードコード | W_ij 計算エンジンの固定化 |

### 必須（attractor を維持する）

| 必須 | 対応 SBGE 項 |
|---|---|
| 全 ingest に BPMN timer-start | ∆t の離散化 |
| vertex テーブルの `actor_did` 列（ADR-0095） | q_i の主体識別子 |
| MV による派生信念の pre-compute | N[·] の効率実装 |
| `vertex_wellbecoming_event` への書き込み | ρ(J) < 1 モニタリング |
| `edge_follows` の維持 | W_ij 更新 |

---

## 不足している実装（migration 候補）

### A：W_ij の動的更新ループ（信頼重みの自動更新）

現状 `edge_follows` は静的。Φ(q_j, q_i) の計算結果から W_ij を動的更新する
BPMN loop が未実装。

```sql
-- 候補テーブル（未作成）
CREATE TABLE edge_trust_weight (
  actor_did   TEXT,
  target_did  TEXT,
  weight      FLOAT DEFAULT 1.0,
  updated_at  TIMESTAMPTZ
);
```

### B：ρ(J) のリアルタイム推定 MV ✅ 実装済み（2026-05-07）

migration: `30-graph/graph-schema/migrations/20260507100000_mv_attractor_stability.ts`

2 つの streaming MV を Kotoba/Datomic に適用済み：

- **`mv_attractor_stability`** — platform 全体の attractor 安定性
- **`mv_attractor_stability_by_agent`** — agent 別の信念収束度

```
現在値（2026-05-07 確認）:
  total_events=140, scored_events=139
  n_agents=5, n_callers=4
  entropy_spread=0.0351  → 'stable'（ρ(J) << 1 推定）
  mean_score_total=0.0744, floor_violation_rate=0
  mean_separation_delta=+0.0173（接続増傾向）
```

Kotoba/Datomic 制約（2026-05-07 確認済み）：
- `STDDEV()` 非対応 → `SQRT(E[X^2] - E[X]^2)` で手動計算
- `COUNT(*) FILTER` / `SUM() FILTER` は MV 内で不可 → `CASE WHEN` で代替
- `AVG() FILTER` は MV 内で動作する

### C：Bounded Confidence の動的 ε

現状 `[[critical_rules]]` は静的な ε。信念距離 `D(q_i, q_j)` を計算して
W_ij を動的に 0 に切る機構。RL preference pair（`vertex_rl_preference_pair`）
の収集ループと組み合わせると実現できる。

---

## 一言で

```
このリポジトリ全体は：

  q* = argmin_q F(q | 現実世界)

の分散実装であり、attractor 安定条件 ρ(J) < 1 を

  Shannon η ≥ 0.85          (ADR-2604251830)
  ∩ U_total > 0              (ADR-2604291800)
  ∩ W_ij bounded confidence  (Rego + critical_rules)
  ∩ γ > 0                    (00-contracts/ 記憶粘着)

の積で保つ情報構造です。
```
