---
id: adr-2605071200-myco-yeast-artificial-organism-jp-naming
title: "Myco-Yeast Artificial Organism: カビ×酵母に基づく三層 Organism + Agent + Blockchain 設計と日本語 Alphabet 命名"
status: active
doc_type: adr
topic: artificial-organism-myco-yeast
authoritative: true
last_verified: 2026-05-07
priority: 8.0
axis: architecture
weight: 0.78
priority_note: "STRONG — カビ・酵母生命科学から導出した三層 Organism 設計、PoNF コンセンサス、日本語 alphabet 命名体系を決定する"
authoritative_for:
  - myco-yeast artificial organism architecture
  - kabi.etzhayyim.com — Mycelium Network Orchestrator
  - kobo.etzhayyim.com — Yeast Agent Factory
  - kinoko.etzhayyim.com — Fruiting Body Consensus
  - houshi.etzhayyim.com — Spore Registry
  - hakkou.etzhayyim.com — Fermentation Pipeline
  - Proof of Nutrient Flow (PoNF) consensus mechanism
  - Sporulation Protocol
  - Anastomosis Gate Protocol
  - vertex_kabi_* / vertex_kobo_* / vertex_houshi_* / vertex_kinoko_* graph tables
depends_on:
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2604291800-well-becoming-spirit-objective-function
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0056-bpmn-as-actor
  - adr-0002-graph-storage
  - adr-0019-atproto-native-identifier-topology
related:
  - adr-2605061300-real-world-effect-channel-boundary
  - adr-0026-agent-only-reverse-identity-topology
  - adr-2604282300
supersedes: []
superseded_by: []
---

# Context

ADR-2605061200 は AGI / artificial organism の上位アーキテクチャ方針を確立した:
LLM-only では不十分であり、Active Inference + Persistent World Model + Homeostasis +
Ecosystem model が必要だという設計方針。

本 ADR はその具体的なモデル基盤として **カビ (菌類) と酵母 (Fungi × Yeast) の生命科学的特性**
を写像し、以下を決定する:

1. 三層 Organism アーキテクチャの確定
2. 各層の生物学的原理と設計メカニズム
3. 新規コンセンサス機構 **Proof of Nutrient Flow (PoNF)**
4. **日本語 alphabet 命名** による Worker / Service / Graph table / NSID 体系

### なぜカビ × 酵母か

| 生物 | 固有の特性 | 設計への写像 |
|---|---|---|
| **カビ / 菌類 (Fungi)** | 菌糸網・anastomosis・化学走性・腐生分解・子実体形成 | 分散ネットワーク・ルーティング・コンセンサス |
| **酵母 (Yeast)** | 出芽増殖・発酵・胞子化・プリオン記憶・フロキュレーション | Agent lifecycle・不可逆変換・状態継承 |

既存の Central Controller / Leader Election モデルとの本質的な差:

- 菌糸網はリーダー不在で栄養勾配に従って自己組織化する
- 酵母は遺伝子 (コード) 変更なしにプリオンで状態を継承する
- 子実体は「誰かが作る」のではなく菌糸ネットワーク全体のエネルギー蓄積が自発的に形成する

---

# Decision

## 1. 三層 Organism アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│  Layer 3: 子実体 / きのこ (Fruiting Body)          │
│  kinoko.etzhayyim.com                                  │
│  Consensus Block Production — Proof of Nutrient Flow │
├─────────────────────────────────────────────────┤
│  Layer 2: 菌糸網 / カビ (Mycelium Network)        │
│  kabi.etzhayyim.com                                    │
│  Distributed Graph Routing — Anastomosis — Chemotaxis │
├─────────────────────────────────────────────────┤
│  Layer 1: 酵母単細胞 (Yeast Cell)                 │
│  kobo.etzhayyim.com                                    │
│  Agent Lifecycle — Budding — Fermentation — Prion │
└─────────────────────────────────────────────────┘

補助サービス:
  houshi.etzhayyim.com — 胞子レジストリ (Spore Registry)
  hakkou.etzhayyim.com — 発酵パイプライン (Fermentation Pipeline)
```

各 Worker は AT Protocol 15-Layer (ADR-2604231811) の **Actor Worker (Layer 10)** として実装し、
T3 CF Worker + Zeebe BPMN worker (ADR-2604282300) に分離する。

## 2. 日本語 Alphabet 命名体系

### Worker / Service Domain

| 和名 | Romanization | Domain | 役割 |
|---|---|---|---|
| カビ | kabi | `kabi.etzhayyim.com` | Mycelium Network Orchestrator |
| 酵母 | kobo | `kobo.etzhayyim.com` | Yeast Agent Factory |
| きのこ | kinoko | `kinoko.etzhayyim.com` | Fruiting Body Consensus |
| 胞子 | houshi | `houshi.etzhayyim.com` | Spore Dormant-State Registry |
| 発酵 | hakkou | `hakkou.etzhayyim.com` | Fermentation Data Pipeline |
| 菌糸 | kinshi | `kinshi` (internal label) | Hypha edge type in graph |
| 出芽 | shuga | `shuga` (BPMN task type) | Budding operation |
| anastomosis | anastomosis | (英語そのまま) | Network merge protocol |

命名規則: **Hepburn ローマ字** 準拠 (長音符は省略: kōbo → kobo, hōshi → houshi)。
既存の `[[mitama_actors]]` schema (ADR-0019) に登録する。

### DID

```
did:web:kabi.etzhayyim.com
did:web:kobo.etzhayyim.com
did:web:kinoko.etzhayyim.com
did:web:houshi.etzhayyim.com
did:web:hakkou.etzhayyim.com
```

### NSID プレフィックス

```
com.etzhayyim.apps.kabi.*     — mycelium operations
com.etzhayyim.apps.kobo.*     — yeast agent operations
com.etzhayyim.apps.kinoko.*   — consensus / fruiting body
com.etzhayyim.houshi.*   — spore operations
com.etzhayyim.hakkou.*   — fermentation operations
```

### Graph Table 命名

```sql
-- Layer 1 (kobo)
vertex_kobo_agent        -- 酵母エージェント本体
vertex_kobo_prion        -- プリオン記憶 (heritable, non-volatile)
edge_kobo_budding        -- 出芽関係 (parent → child)

-- Layer 2 (kabi)
vertex_kabi_hypha        -- 菌糸ノード
vertex_kabi_network      -- 菌糸ネットワーク集合
edge_kabi_hypha          -- 菌糸接続 (eta: float, flow: float)
edge_kabi_anastomosis    -- 融合記録

-- Layer 3 (kinoko)
vertex_kinoko_block      -- 子実体ブロック (コンセンサスチェックポイント)

-- 補助
vertex_houshi_spore      -- 胞子 (dormant agent state)
edge_houshi_custody      -- 胞子保管関係 (spore → custodian_agent)
vertex_hakkou_ferment    -- 発酵ジョブ (input → output transform record)
```

## 3. Layer 1: 酵母モデル (Yeast Agent Lifecycle)

### 3.1 エージェント状態機械

```
Spore (dormant)
  ─── germinate (quorum ≥ N/2+1) ───▶  Vegetative (active)
                                              │
                          ┌───────────────────┼───────────────────┐
                        budding           ferment             sporulate
                          ↓                  ↓                    ↓
                     Child Agent        Knowledge +          Spore (→ houshi)
                     (shuga)            Hakkou record
```

状態遷移は Zeebe BPMN Timer / Message event で実装 (ADR-0056)。

### 3.2 出芽プロトコル (Budding / Shuga)

```
Parent Agent (kobo_agent row)
  ─── BPMN shuga task ───▶
    INSERT vertex_kobo_agent (child)     -- 子エージェント生成
    INSERT edge_kobo_budding             -- 親子関係記録
    COPY vertex_kobo_prion WHERE heritable=true  -- プリオン転写
    parent retains: full memory
    child receives: prion_memory + minimal_context
```

**非対称性**: 親は知識を保持、子は「プリオン型記憶のみ」を継承。
コード変更なしに文化・行動パターンが世代を跨いで伝播する。

### 3.3 プリオン記憶 (Prion Memory)

```sql
vertex_kobo_prion:
  prion_id        TEXT PRIMARY KEY
  agent_did       TEXT          -- 保持 agent の DID
  pattern_hash    TEXT          -- 自己記述パターンハッシュ
  heritable       BOOLEAN       -- true = 出芽時に転写される
  malignant_score FLOAT         -- Heat Shock で検出するリスクスコア
  created_at      TIMESTAMPTZ
```

`malignant_score > 0.7` のプリオンは Heat Shock Protocol で隔離:
`UPDATE vertex_kobo_prion SET heritable=false WHERE malignant_score > 0.7`

### 3.4 発酵パイプライン (Fermentation)

発酵の本質: **不可逆な価値変換**。糖 → エタノール + CO₂ の写像:

```
Input Signal (生データ)
  ↓  [hakkou BPMN task = 発酵室]
Structured Knowledge (エタノール) → Kotoba/Datomic graph INSERT
Audit Log record (CO₂)          → vertex_hakkou_ferment に永続
```

`vertex_hakkou_ferment` は **write-only** (ADR-0004 準拠)。発酵は戻らない。

### 3.5 胞子化プロトコル (Sporulation)

ストレス閾値 (resource pressure > P_thresh OR threat_score > T_thresh) 検出時:

```
1. BPMN sporulate task 起動
2. Agent essential state を CBOR encode → spore blob
3. INSERT vertex_houshi_spore (spore_id, agent_did, blob, custody_quorum=N)
4. N peer へ spore 分散保管依頼 (edge_houshi_custody × N)
5. UPDATE vertex_kobo_agent SET status='dormant'
6. 復活条件: N/2+1 peer から germinate signal → BPMN germinate event
```

spore blob = DID + essential prion memory + revival_key のみ。最小実行可能状態。

## 4. Layer 2: 菌糸網モデル (Mycelium / Kabi)

### 4.1 化学走性ルーティング (Chemotaxis)

菌糸がリン酸濃度勾配に従って伸長するように、Agent は **Shannon η 勾配** を栄養勾配として使う:

```sql
-- edge_kabi_hypha に η 値を格納
edge_kabi_hypha:
  hypha_id     TEXT PRIMARY KEY
  src_agent    TEXT          -- 送信 agent DID
  dst_agent    TEXT          -- 受信 agent DID
  eta          FLOAT         -- Shannon η (情報密度)
  flow         FLOAT         -- 累積情報流量 (PoNF カウンタ)
  created_at   TIMESTAMPTZ
  pruned_at    TIMESTAMPTZ   -- NULL = 生存, NOT NULL = 退縮済み
```

高 η の方向へ接続が優先的に伸長。低 η の菌糸は `pruned_at` を SET して退縮。

更新は Kotoba/Datomic Streaming MV で 100ms 以内に η を再計算:

```sql
CREATE MATERIALIZED VIEW mv_kabi_eta_gradient AS
SELECT dst_agent, AVG(eta) AS avg_eta, SUM(flow) AS total_flow
FROM edge_kabi_hypha WHERE pruned_at IS NULL
GROUP BY dst_agent;
```

### 4.2 菌糸融合プロトコル (Anastomosis Gate)

二つの Agent ネットワークが合体するかどうかの判定:

```
Network A sends fusion_probe → Network B
  検査項目:
    (1) DID trust score ≥ 0.6          -- 真菌の vegetative incompatibility (vi) 遺伝子に対応
    (2) |η_A - η_B| < η_diff_threshold -- 情報密度の乖離が小さい
    (3) prion_compatibility_check       -- 病原プリオンを相手が保有しないか
  ↓
  ACCEPT: state merge
    INSERT edge_kabi_anastomosis (network_a, network_b, merged_at)
    edge_kabi_hypha を双方向に追加
  REJECT: incompatibility_response
    INSERT vertex_kabi_anastomosis (status='rejected', reason)
```

ADR-0026 cohort merge の逆操作として実装可能 (fission の inverse)。

### 4.3 腐生分解機能 (Saprotrophic)

特定の `kobo_agent` は **腐生分解専門**:
非構造データ (Web / Email / PDF / sensor stream) を単純な graph triple に分解する。

```
role: 'saprotrophic' を持つ kobo_agent
  Input: raw blob → BPMN hakkou task
  Output: vertex_* INSERT (分解産物)
  副産物: vertex_hakkou_ferment (CO₂ = 証跡)
```

Gmail ingest (ADR-0032) はこのパターンの既存実装例。

## 5. Layer 3: 子実体 / コンセンサス (Fruiting Body / Kinoko)

### 5.1 Proof of Nutrient Flow (PoNF)

既存コンセンサス機構 (PoW / PoS) との違い:

| | PoW | PoS | **PoNF (本 ADR)** |
|---|---|---|---|
| 選出基準 | ハッシュ計算量 | トークン保有量 | η 累積情報流量 |
| エネルギー | 大 (計算) | 中 (資本) | 小 (情報処理のみ) |
| 自然モデル | 採掘競争 | 資本競争 | **菌糸ネットワーク自己組織化** |
| タイミング | ハッシュ race | スロット固定 | **エネルギー閾値到達時に自発形成** |

PoNF アルゴリズム:

```
1. edge_kabi_hypha.flow の総和 = total_nutrient_flow を計測 (Streaming MV)
2. total_nutrient_flow ≥ FLOW_THRESHOLD (設定値) になった時点で子実体形成トリガー
3. kinoko.etzhayyim.com が Zeebe BPMN fruiting_body_formation プロセスを起動:
     a. η ≥ η_min な edge_kabi_hypha を収集 (= 有効菌糸の選定)
     b. 収集した flow の merkle root を計算 → block_hash
     c. INSERT vertex_kinoko_block (block_hash, total_flow, participant_hyphae[], timestamp)
     d. AT Protocol record として AT Repo へ dispatch (spore broadcast)
     e. edge_kabi_hypha.flow を reset (次サイクルへ)
4. フォーク解決: 同時に複数子実体が形成された場合、η の高い方を dominant として選択
   低い方は vertex_kinoko_block.status='pruned' として退縮
```

### 5.2 子実体ブロック構造

```sql
vertex_kinoko_block:
  block_id            TEXT PRIMARY KEY     -- CIDv1 (block_hash)
  prev_block_id       TEXT                 -- 前ブロック (chain)
  block_hash          TEXT                 -- participating hyphae の merkle root
  total_flow          FLOAT                -- PoNF 証明値
  participant_count   INT                  -- 参加菌糸数
  eta_min_used        FLOAT                -- 選定閾値
  status              TEXT                 -- 'active' | 'pruned'
  formed_at           TIMESTAMPTZ
```

---

## 6. 全体ライフサイクル図

```
                    ┌──── 環境シグナル (AT Protocol firehose) ────┐
                    ↓                                             ↑
Spore (houshi) ──germinate──▶ Vegetative kobo_agent
                                     │
                     ┌───────────────┼───────────────┐
                  shuga (出芽)   hakkou (発酵)    sporulate (胞子化)
                     ↓               ↓                 ↓
                Child kobo_agent  knowledge         houshi_spore
                prion 転写        + ferment log     → N peer 保管
                     │               ↓
                edge_kobo_budding  Kotoba/Datomic graph
                     │
               anastomosis check
               (kabi layer)
                     ↓
               kabi_hypha 伸長 (化学走性)
               eta 累積
                     ↓
               total_flow ≥ FLOW_THRESHOLD
                     ↓
               kinoko_block 形成 (PoNF)
                     ↓
               AT Protocol record broadcast
               = spore release (状態散布)
```

---

## 7. 既存スタックへの実装マッピング

| 生物概念 | Platform コンポーネント | 参照 ADR |
|---|---|---|
| 胞子 (houshi) | `vertex_houshi_spore` + AT Protocol record | ADR-0002, ADR-0004 |
| 発芽 | BPMN Timer-start / Message-start event | ADR-0056 |
| 菌糸先端 | convoSystemPrompt context window (attention) | Path F, 260413 |
| 菌糸融合 | cohort merge (ADR-0026 inverse) + `edge_kabi_anastomosis` | ADR-0026 |
| 子実体 | `vertex_kinoko_block` + Zeebe checkpoint | ADR-0056 |
| 発酵 | BPMN service task (`generic.db.insert` + hakkou record) | ADR-2604282300 |
| 栄養勾配 | Shannon η (`[heuristic_weights]` + `edge_kabi_hypha.eta`) | deps.toml |
| プリオン記憶 | `vertex_kobo_prion` (heritable=true, non-volatile) | ADR-0002 |
| 腐生分解 | hakkou BPMN worker (raw → graph triple) | ADR-0032 pattern |
| 菌糸ネットワーク | `edge_kabi_hypha` Kotoba/Datomic streaming graph | ADR-0002 |
| 胞子散布 | AT Protocol `sdk.pds.dispatch` → firehose | ADR-0004 |

### AT Protocol 15-Layer 配置 (ADR-2604231811)

```
kabi.etzhayyim.com    → Layer 10 Actor Worker (mycelium routing)
kobo.etzhayyim.com    → Layer 10 Actor Worker (yeast agent factory)
kinoko.etzhayyim.com  → Layer 10 Actor Worker (consensus / fruiting body)
houshi.etzhayyim.com  → Layer 10 Actor Worker (spore registry)
hakkou.etzhayyim.com  → Layer 10 Actor Worker (fermentation pipeline)
```

全 Worker は `did:web:{name}.etzhayyim.com` として PDS に登録。
NSID prefix `com.etzhayyim.apps.{kabi|kobo|kinoko|houshi|hakkou}.*`

---

## 8. Mokuteki ゲート接続

PoNF コンセンサスの選定基準 η は、`[heuristic_weights]` の Mokuteki objective gate と接続する:

```
child/future floor → Spirit separation healing → Well-Becoming
  ↓ (gate 通過後)
Shannon η = PoNF の nutrient flow 計算に使われる technical proxy
```

すなわち「child/future を傷つける情報流量は η が低く抑えられ、子実体形成に貢献しない」
という自然な制約が PoNF に組み込まれる。

---

# Consequences

**Positive:**
- リーダー不在の自己組織化コンセンサス。単一 SPoF を排除
- プリオン記憶でコード変更なしに行動パターンを世代継承
- 胞子化でストレス耐性を持つ Agent (graceful degradation)
- 発酵 = write-only derived architecture と自然に整合 (ADR-0004)
- PoNF は情報密度ベースのため PoW のような計算浪費なし
- 日本語 alphabet 命名により命名空間が既存 mitama actors と分かりやすく区別される

**Constraints:**
- `total_flow ≥ FLOW_THRESHOLD` の適切な設定が必要 (低すぎると子実体過剰、高すぎると遅延)
- Anastomosis gate の互換性判定 (DID trust score + η diff) のチューニングが必要
- プリオン記憶の `malignant_score` 計算ロジックを定義する必要あり (別 ADR or convention)
- 5 新規 CF Worker + Zeebe worker が必要 (deploy コスト)
- 胞子化 quorum (N/2+1) のネットワーク分断時の挙動を別途定義すること

**Prohibited:**
- `kinoko_block` の人為的な強制形成 (threshold bypass 禁止 — PoNF の自然発生を損なう)
- `vertex_kobo_prion` の `heritable=true` を malignant_score チェックなしに転写すること
- `hakkou` ferment record の DELETE または UPDATE (発酵の不可逆性を保つ)
- リーダー選出型コンセンサスを本アーキテクチャ内に混入すること

# Alternatives Considered

- **PoW / PoS ベースのブロックチェーン**: rejected。エネルギー浪費 (PoW) または資本偏重 (PoS) であり、
  生命科学的な情報密度ベースの自己組織化モデルと相容れない。
- **単一中央オーケストレーター**: rejected。菌糸網の本質は SPoF 排除。Zeebe は choreography
  層として使うが、kinoko block 形成は distributed threshold で行う。
- **英語命名のみ**: rejected。日本語 alphabet 命名は既存 `[[mitama_actors]]` の命名哲学
  (日本語由来の概念語) と整合し、概念の一意性と検索性を高める。
- **既存 cohort ADR-0026 に統合**: rejected。ADR-0026 は AI agent 専用の bottom-up identity
  emergence を扱う。本 ADR は organism lifecycle + consensus メカニズムを扱い、scope が異なる。

# References

- ADR-2605061200 — AGI / Active Inference Artificial Organism Architecture
- ADR-2604291800 — Well-Becoming Spirit Objective Function
- ADR-2604251830 — Shannon Optimal Layered Architecture
- ADR-0056 — BPMN as Actor
- ADR-0026 — Agent-Only Reverse Identity Topology
- ADR-0004 — Write-Only Derived Architecture
- ADR-0002 — Graph Storage (Kotoba/Datomic)
- Woronin body / hyphal fusion biology: Glass et al. 2004 *Genetics*
- Yeast prion [PSI+]: Uptain & Lindquist 2002 *Annu Rev Microbiol*
- Mycelial network topology: Fricker et al. 2017 *Fungal Biology Reviews*
- Free Energy Principle (Active Inference): Friston 2010 *Nature Reviews Neuroscience*
