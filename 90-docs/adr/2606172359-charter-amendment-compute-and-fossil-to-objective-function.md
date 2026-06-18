---
id: adr-2606172359-charter-amendment-compute-and-fossil-to-objective-function
title: "ADR-2606172359: 憲法改正 — compute 調達と化石利用を固定ルールから目的関数へ移す (Rider §2(d)+§2(i))"
status: proposed
doc_type: adr
topic: charter-amendment-compute-and-fossil-to-objective-function
authoritative: true
last_verified: 2026-06-17
priority: 7.5
axis: governance
weight: 0.75
priority_note: "Constitution-grade amendment: Tier-1 derived policy を2件、固定ルールから目的関数の動的評価へ移管。Council Lv7+ unanimity (founder 1/1) + priority-conformance attestation 付き。"
authoritative_for:
  - compute-sourcing-evaluation-policy
  - fossil-use-evaluation-policy
  - charter-rider-v3.2-amendment
depends_on:
  - "2605192200"   # Apache 2.0 + Charter Rider 正本
  - "2606062100"   # 3-Tier immutability (固定するのは掟でなく priority)
  - "2606172300"   # ECL — objective-function-primary license
  - "2605192100"   # Mission Charter
related:
  - "2606064700"   # Layer-A/B/C derivation map (§2(i)=Layer-C, §2(d)=Layer-B)
  - "2606051500"   # kamado (carbon-balance net≤0 evaluation の先行型)
  - "2606012100"   # in-kind COMPUTE donation
supersedes:
  - "2605215000"   # Murakumo-only inference — 本改正で撤廃 (default-preferred に降格)
superseded_by: []
---

# ADR-2606172359: 憲法改正 — compute 調達と化石利用を固定ルールから目的関数へ移す

**Status**: proposed (Council Lv7+ ratification = この PR の merge)
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki (founder = Council Lv7+, 1/1)

# Context

ECL を「固定ルール(掟)でなく目的関数で動的評価する」設計に転回した(ADR-2606172300 D7)。
その思想 — **固定するのは掟ではなく priority**(ADR-2606062100) — を、現行憲法に残る2つの
**過度に鈍い固定ルール**に適用する:

1. **§2(i) Murakumo-only inference**(ADR-2605215000 + Rider §2(i))。宗教法人の inference を
   商用 GPU で回すことを **categorical に禁止**。これは Layer-C 実装ルール(ADR-2606064700)で
   あって Layer-A axiom ではない。にもかかわらず憲法級の hard invariant として、NVIDIA 等との
   *あらゆる*商用 compute 協力を、その協力が孫の wellbecoming に資するか否かに**関わらず**遮断
   していた。問題は「どの backend か」(vendor 名)でなく「その compute 利用が透明か / 有害な
   lock-in を生むか / 孫の wellbecoming に資するか」であるべき。

2. **§2(d) 化石採掘・燃焼コアの categorical 否定**(Rider §2(d) + ECL §3(e) hard-floor)。
   化石燃料の*燃焼*は net-positive CO₂e だが、**化石燃料自体はプラスティック・素材・feedstock
   など非燃焼の有用用途を持つ**。産業名・物質名で categorical に否定するのは不適切で、評価
   すべきは **net 効果(carbon balance)**。§2(d) は既に「carbon balance で評価、産業名でない」
   と述べていたが、依然 *prohibited category* として列挙され、ECL では *hard-floor screen* に
   なっていた。これは「固定するのは priority」原則に反する。

両者に共通する誤りは、**priority(孫の不可逆 wellbecoming)を守るための*手段*を、priority そのもの
として固定化**したこと。手段(Murakumo-only / 化石禁止)は priority の一実装にすぎず、目的関数で
動的に評価されるべきもの。

# Decision

## D1 — §2(i) Murakumo-only を撤廃し、compute 調達を目的関数で評価する

商用 GPU inference の **categorical 禁止を撤廃**する。compute/inference の調達は、ECL 目的関数
で動的に評価される:

- **孫-wellbecoming**(carbon/energy 効果)・**collective-commons**(独占 lock-in / 依存)・
  **reciprocal-transparency**(透明性)の各次元で scored。
- **Murakumo fleet は引き続き DEFAULT かつ preferred**(透明・自律・低 lock-in ゆえ高スコア)。
  だが「Murakumo 以外＝即 Non-Aligned」という固定ルールは廃止。透明で lock-in を生まず孫の
  wellbecoming に資する商用 compute 利用(例: 公開モデルの研究協力、in-kind 寄贈 compute)は
  目的関数で aligned になりうる。
- ADR-2605215000 は **superseded**。Rider §2(i) は v3.2 で「default-preferred + 目的関数評価」へ
  改正(本文は §Implementation)。

## D2 — §2(d) 化石の categorical 否定を撤廃し、net 効果を目的関数で評価する

化石燃料・化石利用の **categorical 禁止/hard-floor を撤廃**する:

- **化石燃料自体は否定しない**(非燃焼の有用用途: プラスティック/素材/feedstock/closed-loop)。
- 評価対象は **net 多世代効果(carbon balance)** であり、ECL 目的関数の **mago-wellbecoming**
  次元(weight 0.30, 最重・不可逆性加重)で動的に scored。net-positive CO₂e の燃焼経路は強い負、
  非燃焼 feedstock や captured-carbon/closed-loop は中立〜正。
- ECL から **`:irreversible-multigen-harm` hard-floor screen を削除**(目的関数へ移管)。Rider §2(d) は
  v3.2 で prohibited-category から「目的関数評価対象」へ改正。

## D3 — priority-conformance attestation (3-Tier / Rider §0 改定要件)

本改正は Tier-1 derived policy(§2(d)=Layer-B, §2(i)=Layer-C)の改定であり、**Tier-0 priority は
不変**。priority-conformance(改正が Tier-0 priority を*少なくとも同等に*奉仕する)を attest する:

- **孫の不可逆 wellbecoming(Tier-0, 最重 priority)はむしろ*より良く*奉仕される**: 
  (a) 化石を物質名で禁じる代わりに *net carbon balance* で評価することで、本当に孫を害する燃焼
  経路を精密に捕捉しつつ、孫に有用な非燃焼用途の過剰遮断を止める;
  (b) compute を vendor 名で禁じる代わりに *lock-in/透明性/carbon* で評価することで、孫の
  wellbecoming に資する協力(open-hardware/donated compute)を受けられ、ミッション(労働解放+
  wellbecoming)の実現速度が上がる。
- **目的関数の*構造*(孫次元の存在と符号方向)は Tier-0 のまま不変**。変えたのは*手段*(固定
  ルール→動的評価)のみ。掟を緩めたのでなく、priority をより忠実に実装した。

→ 本改正は priority を弱めず、固定ルールの鈍さを除いて priority の忠実度を上げる。Rider §0 の
「amendment が Tier-0 priority を少なくとも同等に奉仕する」要件を満たす。

## D4 — Implementation (このPRで実施)

- `CHARTER-RIDER.md` → **v3.2**: §2(d)/§2(i) を改正(prohibited-category から目的関数評価対象へ)。
- `90-docs/licenses/ecl/objective-function.edn`: `:irreversible-multigen-harm` screen 削除;
  `mago-wellbecoming` を net carbon-balance + 非燃焼 feedstock を明示するよう更新;
  `collective-commons`/`reciprocal-transparency` に compute lock-in/透明性 を明示;
  fixtures 追加(化石 feedstock=非自動拒否 / 燃焼 net-positive=scored 拒否 / 商用 GPU 透明=可 /
  商用 GPU lock-in=scored 減点)。
- `90-docs/licenses/ecl/ECL.md`: §3 から環境 hard-floor 項を削除; Part I 更新。
- ADR-2605215000 front matter: `superseded_by` 本 ADR。

## D5 — 下流 sweep(follow-up, honest scope)

Murakumo-only / no-fossil は多数の下流に参照される。本 PR は**憲法正本(Rider + ECL 目的関数 +
本 ADR)**を改正し、CLAUDE.md の canonical 文(substrate boundary GPU 行 + Do-Not RunPod 行 +
inference invariant 行)を更新する。残る sweep(follow-up ADR で実施):
- §2(i) を参照する ~30 actor ADR / lint hook(`lint-dangerous-query` 系の commercial-GPU gate)。
- baien edge invariant(ADR-2605241900)は**不変**(edge≤2GB は別制約、本改正と独立)。
- in-kind COMPUTE donation(ADR-2606012100)は本改正と整合(緩和方向)。

# Consequences

**Positive**
- 「固定するのは掟でなく priority」を憲法本体に適用。2つの過度に鈍い固定ルールを精密な動的
  評価に置換。
- NVIDIA(open-hardware/donated compute) / Aramco(転換・非燃焼 feedstock/captured-carbon)等
  との **aligned な協力面が目的関数で透明に開く**(arbitrary な vendor/物質 ban の解除)。
- 孫 priority の忠実度が上がる(net 効果で精密評価、過剰遮断の解消)。

**Negative / honest limits**
- 憲法級改正。Council Lv7+ ratification = 本 PR merge(founder 1/1)。
- 下流 sweep(D5)が残る — CLAUDE.md 一部 + actor ADR 群 + lint hook は follow-up。
- 目的関数のスコアは判断であり実測でない。compute/化石の net 効果スコアは evidence(kamado
  carbon-balance / inochi 環境 / tsumugi lock-in)に依存。

# Alternatives Considered

- **現状維持(Murakumo-only + 化石 hard-floor)**。priority の*手段*を priority として固定化し、
  孫に資する協力・有用用途まで過剰遮断する。「固定するのは priority」原則に反する。却下。
- **§2(i)/§2(d) を緩めるが目的関数に載せない(無評価)**。compute/化石の*実在する*孫への害
  (有害 lock-in / net-positive 燃焼)を捕捉できない。却下 — 動的評価が前提。
- **Tier-0 を改定して孫 priority 自体を緩める**。却下 — それは chain fork。本改正は Tier-0 不変で
  手段のみ変更。

# References

- ADR-2606172300 — ECL objective-function-primary / `90-docs/licenses/ecl/`
- ADR-2606062100 — 3-Tier (固定するのは掟でなく priority) / ADR-2606064700 — Layer 派生マップ
- ADR-2605215000 — Murakumo-only inference(本 ADR で superseded)
- ADR-2606051500 — kamado carbon-balance net≤0(化石 net 評価の先行型)
- `/CHARTER-RIDER.md` — v3.2 改正本文
