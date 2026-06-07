---
id: adr-2604291800-well-becoming-formal-model
title: "Well-Becoming Spirit 目的関数 — 公理・数理モデル"
status: active
doc_type: adr
topic: well-becoming-formal-model
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - well-becoming formal model
  - scoring axioms
  - U_total formula
  - bottleneck dominance theorem
priority: 9.0
axis: gate
weight: 0.85
priority_note: "CRITICAL — formal scoring contract for ADR-2604291800 objective-function gates"
depends_on:
  - adr-2604291800-well-becoming-spirit-objective-function
related:
  - adr-2604291800-well-becoming-spirit-objective-function
supersedes: []
superseded_by: []
---

# Well-Becoming Spirit 目的関数 — 公理・数理モデル

**ADR**: 2604291800 補遺
**日付**: 2026-04-29
**ステータス**: active
**参照**: `90-docs/adr/2604291800-well-becoming-spirit-objective-function.md`

---

## 1. 基礎定義

### 1.1 状態空間

$$
\mathcal{S} = \{ (A, C, R, X) \mid A \in \text{DID}, \; C \in \text{DID}, \; R \in \mathcal{T}, \; X \in \mathcal{X} \}
$$

| 記号 | 説明 |
|------|------|
| $A$ | エージェント DID (actor_did) |
| $C$ | 呼び出し元 DID (caller_did) |
| $R$ | レスポンステキスト $R \in \mathcal{T}$ |
| $X$ | コンテキスト (プロフィール・会話履歴・ボトルネック軸) |

### 1.2 スコア写像

各レスポンス $s = (A, C, R, X) \in \mathcal{S}$ に対してスコア写像を定義する:

$$
\phi : \mathcal{S} \to [0,1]^4 \times [-1,1] \times \{0,1\}
$$

$$
\phi(s) = (u_s,\; u_w,\; u_f,\; u_b,\; \delta,\; \mathbf{F})
$$

| 変数 | 説明 |
|------|------|
| $u_s \in [0,1]$ | Spirit 軸スコア (孤独・分離を癒すか) |
| $u_w \in [0,1]$ | Well-Becoming 軸スコア (健康・関係・意味) |
| $u_f \in [0,1]$ | Good Feeling 軸スコア (いい感じ、温かさ、臨場感) |
| $u_b \in [0,1]$ | Buffer 軸スコア (持続可能な条件の構築) |
| $\delta \in [-1,1]$ | 分離デルタ (正: 繋がり増加, 負: 孤立深化) |
| $\mathbf{F} \in \{0,1\}$ | 床制約違反フラグ (子供・未来世代への害) |

---

## 2. 公理系

### 公理 1 — ハード床制約 (Von Neumann Minimax 最悪事例保護)

$$
\boxed{\forall s \in \mathcal{S} : \mathbf{F}(s) = 1 \;\Rightarrow\; U_{\text{total}}(s) := 0}
$$

**解釈**: 床違反はいかなるトレードオフも不可能。$u_s, u_w, u_f, u_b$ の値に関わらず総効用はゼロ。これは Von Neumann Minimax の「最悪ケースを固定する」原則の直接実装である。

---

### 公理 2 — 乗法的独立性 (Multiplicative Independence)

$$
\boxed{U_{\text{total}}(s) = (1 - \mathbf{F}(s)) \cdot u_s(s) \cdot u_w(s) \cdot u_f(s) \cdot u_b(s)}
$$

床制約を満たす場合 ($\mathbf{F} = 0$):

$$
U_{\text{total}}(s) = u_s \cdot u_w \cdot u_f \cdot u_b \;\in [0,1]
$$

**性質**:
- **任意の軸が 0 → 総効用は 0**: $u_k = 0 \Rightarrow U_{\text{total}} = 0$
- **加法的でない**: 高い $u_w$ は低い $u_s$ を補償できない
- **幾何平均との関係**: $U_{\text{total}} = \left(\bar{u}_G\right)^4$ ただし $\bar{u}_G = \left(\prod_k u_k\right)^{1/4}$

---

### 公理 3 — ボトルネック支配 (Bottleneck Dominance)

ボトルネック軸を以下で定義する:

$$
\boxed{k^* = \arg\min_{k \in \{s,w,f,b\}} u_k}
$$

**定理 3.1** (限界効用の最大化): 床制約を満たすとき、

$$
\frac{\partial U_{\text{total}}}{\partial u_{k^*}} = \prod_{j \neq k^*} u_j \;\geq\; \frac{\partial U_{\text{total}}}{\partial u_j} = \prod_{l \neq j} u_l \quad \forall j \neq k^*
$$

**証明**: $u_{k^*} \leq u_j$ より $\prod_{l \neq j} u_l \leq \prod_{l \neq k^*} u_l$ ($u_{k^*}$ を含む側が小さいから)。$\square$

**解釈**: ボトルネック軸の改善が最も高い限界効用を持つ → エージェントはボトルネック軸に優先的に対処すべき。

---

### 公理 4 — スピリット優位性 (Spirit Primacy)

スコアリングシステムは Spirit 軸に内部的優先度を与える:

$$
\boxed{u_s(s) = 0 \;\Rightarrow\; U_{\text{total}}(s) = 0}
$$

さらに、評価ループは Spirit 評価が「分離深化」である場合に精緻化を強制する:

$$
\text{assess}(s) = \text{"separating"} \;\Rightarrow\; \text{refine}(R) \quad \text{if } n_{\text{refine}} < 2
$$

**解釈**: 孤立を深める応答は他の軸がいかに高くとも出力しない。

---

### 公理 5 — スピリット・情報理論双対性 (Spirit–Shannon Duality)

$$
\boxed{\eta(R) = \frac{1 + \delta(R)}{2} \in [0,1]}
$$

ここで $\eta$ は Shannon チャンネル容量の代理変数。

| 状態 | $\delta$ | $\eta$ | 解釈 |
|------|----------|--------|------|
| 完全孤立 | $-1$ | $0$ | チャンネル閉塞 (decoherence 最大) |
| 中立 | $0$ | $0.5$ | ノイズ等価 |
| 完全繋がり | $+1$ | $1$ | 最大チャンネル容量 |

**スピリット軸との関係** (近似):

$$
u_s \approx \eta = \frac{1 + \delta}{2}
$$

より正確には LLM が $u_s$ と $\delta$ を独立に評価し、整合性を事後検証する。

---

## 3. 最適化問題の定式化

### 3.0 TOML 重みへの写像

`deps.toml [objective_function]` と `[[heuristic_weights]]` は以下の写像を使う。
この写像は実装都合の scalar 合成ではなく、lexicographic gate を先に評価する。

| Formal term | TOML id | kind | priority / weight | Dependency |
|---|---|---|---|---|
| $\mathbf{F}=1 \Rightarrow U=0$ | `wellbecoming-child-future-floor` | gate | 10.0 | none |
| $u_s=0 \Rightarrow U=0$ | `spirit-separation-healing` | gate | 10.0 | child floor |
| $k^*=\arg\min u_k$ | `wellbecoming-bottleneck-dominance` | gate | 9.0 | child floor + spirit |
| $u_su_wu_fu_b$ | `wellbecoming-multiplicative-total` | reward | 8.0 | all gates pass |
| $\max_R\min_\theta U$ | `minimax-reversibility-buffer` | reward | 6.0 | all gates pass |
| $\eta=(1+\delta)/2$ | `shannon-spirit-duality` | reward | 6.0 | non-negative separation delta |

数値調整の優先順:

1. floor / separation gate の false negative を減らす。
2. bottleneck 軸の取り違えを減らす。
3. `U_total` の改善量を上げる。
4. 最後に Shannon η / 実装コストで同順位候補を整列する。

### 3.1 Von Neumann Minimax 問題

応答空間 $\mathcal{R}$ と呼び出し元状態空間 $\Theta$ (不確実性の集合) に対して:

$$
\boxed{R^* = \arg\max_{R \in \mathcal{R}} \min_{\theta \in \Theta} U_{\text{total}}(R, \theta)}
$$

**制約**:

$$
\text{s.t.} \quad \mathbf{F}(R) = 0
$$

$\Theta$ の解釈: 呼び出し元の真の状態についての不確実性 (at-risk vs. stable, ボトルネック軸)。ミニマックス戦略は **最も脆弱なシナリオ下でも機能する** 応答を選ぶ。

### 3.2 エージェントループの実装

LangGraph による実装は以下の近似アルゴリズム:

```
R₀ ~ generate(X, k*, bottleneck_prompt)      // ボトルネック軸指向生成
v₀  = assess_spirit(R₀)                       // v ∈ {healing, neutral, separating}

if v₀ = "separating" and n < 2:
    R₁ ~ refine(R₀, X)                        // 精緻化ステップ
    v₁  = assess_spirit(R₁)
    R*  = R₁
else:
    R*  = R₀

emit_event(R*, u_s, u_w, u_f, u_b, δ, F)
```

これは $u_s$ の局所勾配上昇ステップ (最大2回) として解釈できる:

$$
R_{n+1} = R_n + \alpha \cdot \nabla_{R} u_s(R_n)
$$

---

## 4. プロセスマイニング統計量

### 4.1 呼び出し元プロフィール (running average)

$n$ 回の採点済みイベント $\{(u_s^{(i)}, u_w^{(i)}, u_f^{(i)}, u_b^{(i)}, \delta^{(i)})\}_{i=1}^{n}$ に対して:

$$
\bar{u}_k(C) = \frac{1}{n}\sum_{i=1}^{n} u_k^{(i)}, \quad k \in \{s,w,f,b\}
$$

$$
\bar{\delta}(C) = \frac{1}{n}\sum_{i=1}^{n} \delta^{(i)}
$$

$$
\bar{U}_{\text{total}}(C) = \frac{1}{n}\sum_{i=1}^{n} U_{\text{total}}^{(i)}
$$

### 4.2 At-Risk 判定

$$
\boxed{\text{at\_risk}(C) = \bigl[\bar{\delta}(C) < -0.3\bigr] \;\vee\; \bigl[\text{floor\_violations}(C) > 0\bigr]}
$$

**$-0.3$ の根拠**: 平均分離デルタが $-0.3$ を下回ると $\eta_{\text{avg}} < 0.35$、すなわちチャンネル利用率 35% 未満。Shannon 的に「実質的な情報伝達不能」に相当する閾値。

### 4.3 分離トレンド

24h ウィンドウ $W_1$ と 48h ウィンドウ $W_2$ の平均分離デルタを比較:

$$
\text{trend}(C) = \begin{cases}
\text{"improving"} & \bar{\delta}_{W_1} > \bar{\delta}_{W_2} + \epsilon \\
\text{"degrading"} & \bar{\delta}_{W_1} < \bar{\delta}_{W_2} - \epsilon \\
\text{"stable"}    & \text{otherwise}
\end{cases}
\quad \epsilon = 0.1
$$

---

## 5. ボトルネック最適化の数値指標

### 5.1 ボトルネック寄与度

$U_{\text{total}} = u_s u_w u_f u_b$ において各軸の **相対的損失** を定義:

$$
\ell_k = 1 - u_k
$$

$$
\text{BottleneckRatio}(k) = \frac{\ell_k}{\sum_{j} \ell_j}
$$

ボトルネック軸 $k^*$ は $\text{BottleneckRatio}$ を最大化する軸。

### 5.2 改善ポテンシャル

現在の軸スコアから「全軸 = 1.0」への理論的最大改善:

$$
\Delta U_{\max}(k) = U_{\text{total}} \cdot \frac{1 - u_k}{u_k}
$$

**解釈**: $u_k$ が低い (ボトルネック) ほど $\Delta U_{\max}(k)$ が大きい → 介入優先度が高い。

---

## 6. 公理の完全性チェック

| 性質 | 公理 | 検証 |
|------|------|------|
| 床制約は交渉不能 | A1 | $\mathbf{F}=1 \Rightarrow U=0$、加算・乗算で救済不能 |
| Spirit ゼロで総効用ゼロ | A2 | $u_s=0 \Rightarrow U_{\text{total}}=0$ |
| ボトルネック軸への集中が最適 | A3 | 定理3.1より限界効用最大 |
| 精緻化ループが Spirit 優先を実装 | A4 | "separating"判定で強制再生成 |
| 分離デルタ ↔ 情報理論の一貫性 | A5 | $\eta = (1+\delta)/2 \in [0,1]$ |

### 6.1 不変条件 (Invariants)

1. **非負性**: $U_{\text{total}}(s) \geq 0 \;\forall s$
2. **有界性**: $U_{\text{total}}(s) \leq 1 \;\forall s$
3. **床の絶対性**: $\mathbf{F}(s) = 1 \Rightarrow U_{\text{total}}(s) = 0$ (他のいかなる値も覆せない)
4. **ボトルネック支配の単調性**: $u_{k^*}$ の増加は他のいかなる軸の等量増加よりも $U_{\text{total}}$ を大きく改善する (定理3.1)

---

## 7. 実装との対応

| 数式 | 実装箇所 |
|------|----------|
| $\phi(s) = (u_s, u_w, u_f, u_b, \delta, \mathbf{F})$ | `wellbecoming_process_mining.py:_score_response()` |
| $U_{\text{total}} = u_s u_w u_f u_b$ | `wellbecoming_process_mining.py:score_total` |
| $k^* = \arg\min_k u_k$ | `wellbecoming_agent.py:_load_profile_node` → `bottleneck_axis` |
| $\text{at\_risk} = [\bar\delta < -0.3]$ | `migration/20260429230000:mv_wellbecoming_at_risk` |
| Refine loop (A4) | `wellbecoming_agent.py:_WB_GRAPH` conditional edge |
| $\eta = (1+\delta)/2$ | `infer.ts:emitWellBecomingEvent` `separation_delta` |
| $R^* = \arg\max \min_\theta U_{\text{total}}$ | `wellbecoming_agent.py:_BOTTLENECK_PROMPTS` per-axis instruction |

---

## 8. 数値例

### 8.1 ボトルネック検出例

| 軸 | スコア |
|----|--------|
| $u_s$ | 0.85 |
| $u_w$ | 0.70 |
| $u_f$ | **0.30** ← ボトルネック |
| $u_b$ | 0.75 |

$$
U_{\text{total}} = 0.85 \times 0.70 \times 0.30 \times 0.75 = 0.134
$$

$$
\frac{\partial U}{\partial u_f} = 0.85 \times 0.70 \times 0.75 = 0.446 \quad \text{(最大限界効用)}
$$

$u_f$ を $0.30 \to 0.80$ に改善した場合:

$$
U'_{\text{total}} = 0.85 \times 0.70 \times 0.80 \times 0.75 = 0.357 \quad (+166\%)
$$

### 8.2 At-Risk 判定例

$n = 20$ イベント、$\bar\delta = -0.35$:

$$
\eta_{\text{avg}} = \frac{1 + (-0.35)}{2} = 0.325 < 0.35 \;\Rightarrow\; \text{at\_risk} = \text{true}
$$

チャンネル容量 32.5% → 実質的な孤立状態 → 2h おきの proactive connect トリガー。

---

## 9. 機械検証済み証明 (Lean 4)

`90-docs/proof/WellBecoming.lean` に Lean 4 + Mathlib4 (v4.14.0) による形式証明を収録。
以下の定理がすべて機械検証済み:

| 定理 | 内容 | Lean 識別子 |
|------|------|-------------|
| Invariant 1 | 非負性: $U_{\text{total}} \geq 0$ | `U_total_nonneg` |
| Invariant 2 | 有界性: $U_{\text{total}} \leq 1$ | `U_total_le_one` |
| Axiom 1 | 床の絶対性: $\mathbf{F}=1 \Rightarrow U=0$ | `floor_forces_zero` |
| Axiom 3 | ボトルネック支配: $\partial U/\partial u_{k^*} \geq \partial U/\partial u_j$ | `bottleneck_dominance` |
| Axiom 4 | Spirit 優位性: $u_s=0 \Rightarrow U=0$ | `spirit_zero_kills_utility` |
| Axiom 5 | At-risk 閾値: $\bar\delta < -0.3 \Rightarrow \eta < 0.35$ | `at_risk_implies_low_channel_capacity` |
| Bundle | 4 不変条件の同時成立 | `wellbecoming_invariants` |
| Corollary | ボトルネック最適ターゲット系 | `bottleneck_is_optimal_target` |

ビルド方法:
```bash
cd 90-docs/proof
lake update && lake build
```

---

## 10. BPMN デプロイ状況 (2026-04-29)

ADR-0056 BPMN-as-actor として 5 プロセスが Zeebe に live:

| BPMN process ID | Zeebe key | トリガー |
|---|---|---|
| `wellbecoming_process_mining` | `2251799816309098` | Timer R/PT15M |
| `wellbecoming_detect_bottleneck` | `2251799816311150` | Timer R/PT1H |
| `wellbecoming_proactive_connect` | `2251799816311147` | Timer R/PT2H |
| `wellbecoming_floor_violation_alert` | `2251799816311153` | Timer R/PT30M |
| `wellbecoming_agent_loop` | `2251799816311145` | XRPC none-start |

XRPC エンドポイント: `http://dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.apps.wellbecoming.agentLoop`
pymagatama: `0.2.84-amd64` (mitama-udf namespace、全 6 wellbecoming タスクタイプ登録済み)
