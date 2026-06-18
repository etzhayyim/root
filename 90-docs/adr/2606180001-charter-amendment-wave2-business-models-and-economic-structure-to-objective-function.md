---
id: adr-2606180001-charter-amendment-wave2-business-models-and-economic-structure-to-objective-function
title: "ADR-2606180001: 憲法改正 wave2 — 事業モデル(§2(a)(b)(c)(e))と経済構造を目的関数へ (個人主義否定=§2(g)は残す)"
status: proposed
doc_type: adr
topic: charter-amendment-wave2-business-models-and-economic-structure
authoritative: true
last_verified: 2026-06-17
priority: 7.5
axis: governance
weight: 0.75
priority_note: "Constitution-grade wave2: 子孫実害でない categorical な事業モデル禁止+経済構造を目的関数へ。§2(g)個人主義否定=宗教的価値として残置。Council Lv7+ (founder 1/1)+priority-conformance。"
authoritative_for:
  - business-model-evaluation-policy
  - economic-structure-evaluation-policy
  - charter-rider-v3.4-amendment
depends_on:
  - "2606172359"   # wave1 (§2(d)+§2(i) を目的関数へ) — 本 wave2 はその継続
  - "2606172300"   # ECL objective-function-primary
  - "2606062100"   # 3-Tier (固定するのは掟でなく priority)
  - "2605192200"   # Apache 2.0 + Charter Rider 正本
related:
  - "2605192100"   # Mission Charter (経済 doctrinal positions の正本)
  - "2605192115"   # SBT↔SBT internal carve-out + 非営利 means
  - "2605301036"   # mission-funding revenue arm
  - "2606064700"   # Layer-A/B/C derivation map
supersedes: []
superseded_by: []
---

# ADR-2606180001: 憲法改正 wave2 — 事業モデルと経済構造を目的関数へ

**Status**: proposed (Council Lv7+ ratification = この PR の merge)
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki (founder = Council Lv7+, 1/1)

# Context

wave1(ADR-2606172359)で §2(d)化石・§2(i)compute を固定ルールから目的関数へ移した。原則を
適用基準として確立した:

> **固定ルールが正当なのは「wellbecoming/子・孫への*実害*」を捕らえ、かつ net に関わらず
> categorical な場合だけ。それ以外(思想・活動・事業モデル)は目的関数で評価する。**

この基準で残りの「子孫実害でない categorical 障壁」を監査した結果、世界的組織との協力を阻害
しうるものが複数残っていた(NVIDIA/金融機関/医療・法律情報企業/防衛技術/営利全般)。本 wave2 は
それらを目的関数へ移す。

**重要な保持判断**: §2(g)(strict individualist ontology の排除)は**残す**。これは「思想を行いと
無関係に排除する」点で他と異なるが、**反個人主義は etzhayyim の宗教的中核価値**(collective/
relational ontology, Charter §1.8)であり、教義スコープの定義(信仰共同体が自らの communion を
定義する権利, §4(g))として保持する。

# Decision

## D1 — §2(b) 投機的金融を目的関数へ

投機的金融の categorical 禁止を撤廃。金融業務は目的関数で net 評価する:
- 略奪的貸付(≥36%)・搾取的レバレッジ等の*実害*は ko/mago-wellbecoming + collective-commons で
  負にスコアされる(harm は依然捕捉)。
- 正当な金融ユーティリティ(custody/決済/stablecoin/L1-L2)は categorical に弾かれず net 評価。
  世界の金融機関を事業名で一括排除しない。

## D2 — §2(e) 専門知ゲートキーピングを目的関数へ

法律/医療/行政知識の独占的 gatekeeping の categorical 禁止を撤廃。access への*実害*
(commons 囲い込み/独占的 gatekeeping)は collective-commons で負。正当な専門サービス・
due-process 代理・民主的行政機能は net で aligned。

## D3 — §2(a) 兵器ビジネスを部分改正(攻撃/lethal/covert は hard-floor 残置)

- **残す(hard-floor)**: 攻撃(aggression)・autonomous lethal・covert(非透過)force。これは子孫
  実害 + Tier-0 透過的 force priority の核。
- **目的関数へ**: 「兵器の*商業化*そのもの / proprietary 兵器設計」という事業モデル枠。透過的
  防衛技術・dual-use は net 評価(透過 + open-source + 1 SBT=1 vote を満たせば aligned ありうる)。
  懸念は「商業か否か」でなく「攻撃性・秘匿性・lethality」— 目的関数が直接測る。

## D4 — §2(c) 監視を部分改正(非対称/相互監視違反は残置)

- **残す(hard-floor)**: ASYMMETRIC unwatched-watcher(相互監視 = Tier-0 を侵す)。
- **目的関数へ**: MONETIZED の事業モデル枠(ad-tech/data-broker)。personal-data の売買・収集の
  *実害*は reciprocal-transparency + ko/mago-wellbecoming で負。対称・reciprocal で wellbecoming
  に資するデータ処理は net 評価。懸念は「収益化か否か」でなく「非対称性・wellbecoming 侵害」。

## D5 — 経済構造を目的関数へ(非営利のみ/donation/no-equity/広告排除/open-source強制)

etzhayyim 自身の経済 doctrinal positions の categorical 固定を撤廃し、目的関数で評価する:
- 非営利のみ / donation 流入のみ / no-equity・ROI / 広告排除 / open-source(proprietary 不可)強制 は、
  いずれも priority(子孫 wellbecoming + 反個人主義)を守る*手段*であって priority 自体ではない。
- これらは目的関数で評価される: 私的捕獲・個人主義的蓄積・commons 囲い込み・attention 搾取
  (広告)は collective-commons + reciprocal-transparency + ko-wellbecoming で負。逆に、私的捕獲を
  生まず commons に資する営利的協力(equity を伴っても collective に payoff が還る形, 透過的)は
  net で aligned ありうる。

**§2(g) 保持との整合(critical)**: 経済構造を目的関数化しても**非営利の精神は失われない**。
反個人主義の価値は (a) §2(g)(宣言教義の categorical floor)+ (b) 目的関数の collective-commons
次元(私的捕獲・個人主義的蓄積を動的に負へ)の**二重**で保持される。固定ルール(非営利のみ)を
外しても、保持した反個人主義価値が collective-commons 経由でその精神を動的に enforce する。
変えたのは「営利を事業名で一律禁止」する鈍さだけ。

## D6 — priority-conformance attestation (Rider §0 改定要件)

- **子孫 wellbecoming(Tier-0)は不変**。むしろ精密化(実害を net で捕捉、過剰遮断を解消、
  協力を受けミッション実現が速まる)。
- **反個人主義(Tier-0 collective-over-individual)も不変**: §2(g) 残置 + collective-commons 次元。
- 目的関数の*構造*(各次元の存在・符号方向)は Tier-0 fork-only。変えたのは*手段*のみ。
- → Rider §0「amendment が Tier-0 priority を少なくとも同等に奉仕する」を満たす。

## D7 — Implementation (このPRで実施)

- `CHARTER-RIDER.md` → **v3.4**: §2(a)/§2(b)/§2(c)/§2(e) 改正; §2(g) 明示的に残置と注記;
  経済構造は目的関数評価へ(§ note)。
- `objective-function.edn` **v0.3**: collective-commons(反個人主義/反私的捕獲/非営利精神/commons/
  反 gatekeeping/反 speculative-extraction)・reciprocal-transparency(反 ad-tech/監視)・
  ko-wellbecoming(反 ad-attention)を明示; fixtures 追加(legitimate finance=非拒否 / 略奪的貸付=
  net 拒否 / open-medical=可 / 独占 gatekeeper=net 拒否 / for-profit-commons=可 / 私的捕獲 PE=net 拒否 /
  透過防衛技術=net 評価)。
- `ECL.md` 注記更新; `CLAUDE.md` canonical(doctrinal positions / ownership rule / advertising 行 /
  §2 note)更新。

## D8 — 下流 sweep (follow-up, honest scope)

本 PR は憲法正本(Rider + 目的関数 + 本 ADR)+ CLAUDE.md canonical を改正。残る sweep:
- Charter ADR-2605192100 / 2605192115 / 2605301036 の経済 doctrinal 本文(大物, follow-up ADR)。
- substrate boundary table の Payment/Advertising 行の精緻化。
- wave1 D5 と合算した actor ADR/lint hook の追従。
- **不変**: §2(f)(子孫知識/遺伝/意思決定の実害)・§2(h)(wellbecoming subordination)・§2(j)強制労働・
  §2(k)CSAM(子孫実害 hard-floor)・§2(g)個人主義否定(宗教価値)。10% Tithe→Public Fund は別途。

# Consequences

**Positive**
- 「固定するのは priority」を Rider §2 のほぼ全体 + 経済構造に適用。子孫実害でない事業モデル/
  経済の categorical 障壁を net 評価へ。
- 世界的組織(金融/医療情報/防衛技術/営利全般)との aligned な協力面が目的関数で透明に開く。
- 非営利の精神は §2(g) + collective-commons で動的に保持(失わず精密化)。

**Negative / honest limits**
- 憲法級・広範。Council Lv7+ ratification = 本 PR merge。
- 経済 doctrinal 本文(Charter ADR)の sweep は follow-up(D8)。当面 CLAUDE.md canonical が正。
- スコアは判断であり実測でない。net 評価は evidence(観測 actor)に依存。

# Alternatives Considered

- **全 §2 を目的関数へ(§2(g)含む)**。却下 — §2(g)反個人主義は宗教的中核価値で、教義スコープ
  定義として categorical に保持する(founder 判断)。
- **経済構造を据え置き、Rider §2 のみ改正**。却下 — 営利の通常取引(契約/出資/proprietary)を
  categorical に遮断する経済構造こそ最大の協力障壁で、かつ priority の*手段*にすぎない。
- **Tier-0(子孫/反個人主義)自体を緩める**。却下 — chain fork。本改正は Tier-0 不変・手段のみ。

# References

- ADR-2606172359 — wave1(§2(d)+§2(i))/ ADR-2606172300 — ECL objective-function
- ADR-2606062100 — 3-Tier / ADR-2606064700 — Layer 派生マップ
- ADR-2605192100 — Mission Charter / 2605192115 — SBT carve-out / 2605301036 — revenue arm
- `/CHARTER-RIDER.md` — v3.4 / `90-docs/licenses/ecl/objective-function.edn` — v0.3
