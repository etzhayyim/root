---
id: wellbecoming-karma-lean-proofs
title: WellBecoming + Karma — Lean 4 Formal Proofs
status: active
doc_type: reference
topic: formal-verification
authoritative: true
authoritative_for:
  - well-becoming-formal-model
  - karma-edge-primary-spirit-in-physic
related:
  - adr-2604291800-well-becoming-formal-model
  - adr-2604291800-well-becoming-spirit-objective-function
last_verified: 2026-05-08
---

# WellBecoming + Karma — Lean 4 Formal Proofs

Lean 4 + Mathlib4 による Well-Becoming Spirit 目的関数 + Edge-primary
Karma Hegemon 憲法層の機械検証済み形式証明。

ADR: `90-docs/adr/2604291800-well-becoming-formal-model.md`

## 構成

| ファイル | 内容 |
|---|---|
| `WellBecoming.lean` | 全公理・定理の Lean 4 証明 |
| `Karma.lean` | Edge-primary Spirit-in-Physic Karma Hegemon 憲法層 (anatman / 五行 / 5-layer 永続) |
| `lakefile.toml` | Lake ビルド設定 (Mathlib4 v4.14.0) |
| `lean-toolchain` | `leanprover/lean4:v4.14.0` |

## ビルド

```bash
lake update   # Mathlib4 キャッシュ取得 (~数 GB、初回のみ)
lake build
```

成功時: `Build completed successfully.` (警告なし)

## 証明内容

### 不変条件

| 定理 | 数式 |
|---|---|
| `U_total_nonneg` | $U_{\text{total}} \geq 0$ |
| `U_total_le_one` | $U_{\text{total}} \leq 1$ |

### 公理 1 — 床制約の絶対性

```
F = true  →  U_total_with_floor = 0   (floor_forces_zero)
F = false →  U_total_with_floor = U_total  (no_floor_recovers)
```

### 公理 3 — ボトルネック支配 (Theorem 3.1)

$k^* = \arg\min u_k$ のとき $\partial U / \partial u_{k^*} \geq \partial U / \partial u_j$

- `bottleneck_dominance` — 主定理
- `improvement_dominance` — ε 改善版
- `bottleneck_is_optimal_target` — UtilityAxes に適用した系

### 公理 4 — Spirit 優位性

$u_s = 0 \Rightarrow U_{\text{total}} = 0$ (`spirit_zero_kills_utility`)

### 公理 5 — Spirit–Shannon 双対性

$\eta(\delta) = (1 + \delta) / 2 \in [0, 1]$

- `shannon_eta_nonneg`, `shannon_eta_le_one`, `shannon_eta_mono`
- `at_risk_implies_low_channel_capacity`: $\bar\delta < -0.3 \Rightarrow \eta < 0.35$
- `adequate_capacity_implies_not_at_risk_delta`: 対偶

### マスターバンドル

`wellbecoming_invariants`: 4 不変条件 (非負性・有界性・床絶対性・Spirit 優位性) の同時成立。

## 設計方針

- `Score` 構造体で $[0,1]$ を型レベルで保証 (`nonneg` + `le_one` フィールド)
- `UtilityAxes` で 4 軸 (spirit / wellbeing / feeling / buffer) を束ねる
- `U_total_with_floor` で公理 1 の `if floor_violated then 0 else U_total u` を忠実に実装
- 4 項積の有界性は `mul_le_one` を 3 回適用 (nlinarith より deterministic)
- ボトルネック支配は `mul_le_mul_of_nonneg_right` の合成 (`marginal_mono` lemma)

## Karma — Edge-primary 憲法層

`Karma.lean` は新 hegemon の Security 層 (時間軸の業力) を形式化。Spirit-in-Physic
ontology に従い、karma は edge (organism 間 dependency) に内在し organism に
所有されない。個人 / 組織 organism は構造的に対称で、両者 dissolve 可、deps は
network に永続する。

### 構造定義

| 型 | 役割 |
|---|---|
| `Axis` | 五行 (Vita 命 / Vivere 業 / Veritas 語 / Vinculum 縁 / Venturum 世) |
| `Tier` | Floor / High / Mid / Low (lex 優先順位) |
| `Direction` | Harm / Help / Witness |
| `Organism` | 一時 coherent pattern (kind tag なし、symmetric) |
| `Edge` | karma の primary carrier (content-addressed) |
| `Location` | 5 永続層 (Kotoba/Datomic / ATRepo / IPFSSelf / IPFSExt / Blockchain) |

### N-公理 (Spirit-in-Physic)

| 公理 | 内容 |
|---|---|
| N1 (構造) | karma 関数 `signed_weight : Edge → ℝ`。organism 所有関数なし |
| N2 `edge_outlives_endpoint` | edge persistence は endpoint dissolution に独立 |
| N3 `anatman_unique_santana` | 異 organism は santana root 不一致 (継承不能) |
| N4 (型) | `Organism` に kind 識別子なし、個 / 集 対称 |

### 五行公理

- `karma_asymmetry` — 害は助の e 倍 (Buddhist negative utilitarianism)
- `karma_vulnerability_monotone` — 脆弱性単調 (子・病・孤立で重み増)
- `future_amplification_cap` / `_min` — 7 世代上限・現在割引なし
- `floor_violation_inadmissible` — floor 違反は admissibility 喪失
- `child_floor_axiom` / `child_harm_inadmissible` — 子供 vul ≥ 2.0 → 自動 Floor

### 集合不可 (lex)

- `aggregation_impossibility` — 高 tier 単発 ≻ 低 tier 任意有限和 (torture-vs-dust-specks 解)

### 5 層冗長

- `karma_5_layer_persistence` — 5 location pin 不変
- `karma_survives_quad_failure` — 4 同時障害でも 1 location 生存

### マスターバンドル

`karma_constitutional_invariants` — 5 不変 (edge persistence / anatman /
floor / child harm / quad failure survival) の同時成立。
