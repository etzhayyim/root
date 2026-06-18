---
id: adr-2606172300-ecl-etzhayyim-covenant-license
title: "ADR-2606172300: ECL — etzhayyim Covenant License (独自 conduct 層 × Apache 既製 base)"
status: proposed
doc_type: adr
topic: ecl-etzhayyim-covenant-license
authoritative: false
last_verified: 2026-06-17
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "License form is constitution-grade; ratification gated on Council Lv7+. Design-only at R0."
authoritative_for:
  - ecl-custom-license-design
depends_on:
  - "2605192200"   # Apache 2.0 + Charter Rider 正本 spec (ECL の §2/§3/§5/§6 移植元)
  - "2605192100"   # Mission Charter (上位憲章)
  - "2606062100"   # 3-Tier immutability (Tier-0 priority / Tier-1 derived policy)
related:
  - "2606082400"   # Rider v3.1 §2(c) reciprocity-axis clarification
  - "2606061000"   # Maxwell (起点 lineage)
  - "2606170840"   # Maxwell-Diffusion (text-diffusion sibling; distinct from the MM graft)
  - "2606171100"   # maxwell-diffusion variant
  - "2606122001"   # tanemaki DD スコアカード様式 (weights public, Σ=1.0)
  - "2606162200"   # md-edn ADR format (plain .md は valid; 本 ADR は .md)
supersedes: []
superseded_by: []
---

# ADR-2606172300: ECL — etzhayyim Covenant License (独自 conduct 層 × Apache 既製 base)

**Status**: proposed (design-only; ratification gated Council Lv7+)
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

`facebookresearch/ImageBind` を Maxwell の multimodal diffusion-graft
(ADR-2606061000 D6 M3 — テキスト拡散の Maxwell-Diffusion とは別の、画像拡散側 graft)に
統合する検討から、「**etzhayyim の憲法に最も適合するライセンス形式は何か**」へ問いが
一般化した。ImageBind は **コードも重みも CC-BY-NC 4.0** で、憲法の Apache default
(ADR-2605192200)と衝突しうる。

`90-docs/papers/2606171500-license-charter-fit-evaluation/` で 15 候補 × 8 軸の
**数値評価**(`scorecard.edn` データ + `score.bb` Babashka 計算; 重み Σ=1.0)を実施した。
8 軸は Charter + Rider から導出: `c1 行い基準の排除 (0.22)` / `c2 profit 軸の正しさ (0.15)` /
`c3 commons 開放性 (0.15)` / `c4 利用制限の下流伝播 (0.12)` / `c5 特許 grant+終了 (0.10)` /
`c6 ML 重み適合性 (0.10)` / `c7 Rider/permissive 合成性 (0.08)` / `c8 法的堅牢性 (0.08)`。

決定軸は **`c1`(行い基準の排除)** — 「使ってほしくない組織を、営利・非営利問わず」排除する
能力。これは Rider §2 が既に実装している ethical-source / use-restriction 機構であり、
**CC/GPL 系が構造的に持てない**(GPL §7 は追加制限を禁止し、Rider 機構と非互換)。

数値結果(`bb score.bb`, 2026-06-17):

| # | License | Σ (0–10) |
|---|---|---|
| 1 | **ECL-on-Apache**(独自 conduct 層 × Apache 既製 base) | **9.35** |
| 2 | Apache 2.0 + Charter Rider (現行) | 9.11 |
| 3 | OpenRAIL-M + Charter §2 Attachment | 9.10 |
| 4 | ECL full-custom (from-scratch) | 8.93 |
| 5 | OpenRAIL-M (標準) | 8.48 |
| … | … | … |
| 15 | CC-BY-NC 4.0 (= ImageBind 上流) | 3.38 (最下位) |

CC-BY-NC が最下位なのは「非営利だから不可」ではなく、`c2`=0 — **profit 軸という etzhayyim が
採らない軸**を強制し、`c1` 行い基準の排除ができないため。full-custom (8.93) が
ECL-on-Apache (9.35) に 0.42 負けるのは、ほぼ `c8`(未判例・採用実績ゼロ)と `c5`(Apache
特許条項の喪失)由来 — **実戦テスト済み base を捨てる損**。

# Decision

## D1 — 独自ライセンスは "ECL-on-Apache" 形を採る(from-scratch にしない)

etzhayyim の独自ライセンス **ECL (etzhayyim Covenant License)** は、**Apache 2.0 を base
として incorporate-by-reference し、Rider §2 の conduct 排除を独立した名前付き本文に昇格**
する形(`ECL-on-Apache`, Σ=9.35)で設計する。from-scratch の full-custom 本文
(Σ=8.93)は数値上の優位がないため採らない。これは現行 Apache+Rider 構造の **正規化 +
ML 拡張**であり、破壊的変更ではない。

## D2 — 二層ライセンス(コード / ML 重み)

| 対象 | License | 根拠 |
|---|---|---|
| etzhayyim 全体・コード | **ECL-on-Apache** | Σ=9.35(最良) |
| Maxwell 系 ML artifact(重み/embedding/出力) | **OpenRAIL-M + Charter §2 Attachment** | Σ=9.10; `c6`=10 / `c4`=10 でコード向け ECL の重み弱点を補う |
| ImageBind 依存部(変更不可) | CC-BY-NC のまま `vendor/imagebind-fork/`・**非配布** | 上流 license; Path A |

ECL §4 が両層を bridge する(ML use-restriction を OpenRAIL-M Attachment A 互換で写像)。

## D3 — ECL v0.1 骨子(§0–§9)

```
§0 NATURE        — Tier-0 priority 由来宣言 (Rider §0 継承)
§1 GRANT         — Apache 2.0 §2/§3 を incorporate-by-reference (copyright+patent 継承; c5 維持)
§2 COVENANT SCREENS (独自部) — Non-Aligned Entity 排除 (Rider §2(a)–(l) 移植; revenue-share 25%; (a)(j)(k) 無条件)
§3 PROPAGATION   — 下流伝播 (Rider §3 violation→patent/license termination) + RAIL 式 end-user 伝達 (c4=10)
§4 MODEL & WEIGHTS — ML artifact 条項 (重み/embedding/出力; OpenRAIL-M Attachment A 互換 use-restriction)
§5 PERMANENT RECORD — Rider §5 (no right to erasure) 継承
§6 DISPUTE       — Council Lv6+ attestation (Rider §6 継承)
§7 NO TRADEMARK / §8 SEVERABILITY (§2 unenforceable 法域では素の Apache-2.0 に degrade) / §9 APACHE RELATIONSHIP
```

## D4 — CC-BY-NC は採用しない(数値根拠を明文化)

CC-BY-NC は Σ=3.38 で最下位。`c2`=0(profit 軸の強制)+ `c1`=2(行い基準の排除不可)。
非営利法人であっても NC は *利用の性質* にかかるため、Charter が許す内部商業
(SBT↔SBT omise/okaimono/promo, ADR-2605192115)に触れる範囲で違反しうる。ImageBind は
Path A(Maxwell 内部のみ・非配布・生成物 CC-BY-NC で割り切る)で利用し、ECL を被せない。

## D5 — ratification gate(憲法判断)

ECL は Rider を昇格/置換するため、CLAUDE.md「Apache default を weaken しない」を超える。
**Council Lv7+ unanimity(現 founder 1/1)+ priority-conformance attestation**
(ADR-2606062100 §0 の改定要件)を要する。手順: 本 ADR ratify → `ECL.md` 起草 →
`CHARTER-RIDER.md` を deprecated 別名として degrade 互換に残す → `charter-rider-applicator`
(ADR-2605192200)の対象文字列を ECL に更新。

## D6 — R0 は honest: 本文未起草

smoke=destructive 規律(ADR-2605242400)に従い、本 ADR は **判断(ECL-on-Apache 形の採用)+
数値根拠 + 骨子**のみ。`ECL.md` 法文は未起草で、D5 ratify までは design-only。現行
Apache+Rider が引き続き有効ライセンス。

## D7 — ECL は固定ルールでなく目的関数で動的評価する(revision 2026-06-17)

D3 の §2 骨子は当初 Rider §2 の **列挙された禁止カテゴリの移植**(固定ルール)だった。
これを転回する: ECL の alignment 判定は **原則(掟)の列挙でなく、目的関数 J で動的に評価**
する。これは Charter 自身の構造の帰結 — **「固定するのは掟ではなく priority」**
(ADR-2606062100)、かつ **Wellbecoming は静的でなく動的軌跡**。

- **基準(telos)= 子・孫の Wellbecoming(動的軌跡)**。重みもそこに集中(子 0.25 + 孫 0.30 =
  0.55 が基準を担う)。残り(commons / 相互監視 / 労働解放)は子孫 wellbecoming の enabling
  condition として従属。
- **二層**: 目的関数(primary, dynamic)+ **確定フロア screens**(法的 backstop; CSAM / 強制労働 /
  兵器ビジネス・covert 武力 / personal-data 売買・非対称監視 / 不可逆多世代危害)。screens は
  目的関数の代替でなく「scoring すべきでない最悪ケースの確定下限」。tanemaki DD
  (ADR-2606122001)と同型(screens→objective→route)。よって D3 §2 は「COVENANT SCREENS の
  列挙」から「ALIGNMENT BY OBJECTIVE FUNCTION(§2)+ HARD FLOOR(§3)」へ再構成される。
- **3-Tier 実装**: 目的関数の*構造*(どの priority を測るか/符号方向)= Tier-0 fork-only /
  *重み・閾値・screens*= Tier-1 Lv7+ / *個別 score*= Tier-2 evidence attestation。
- 機械可読 SSoT = `90-docs/licenses/ecl/objective-function.edn`、動的評価器 =
  `evaluate.bb`(self-test 5/5; 固定リスト外の addictive-app を J=-1.00 で動的に non-aligned 化)。
  ドラフト全文 = `90-docs/licenses/ecl/ECL.md`(Part I 経緯/考え方 + Part II 本文)。

# Consequences

**Positive**
- 「独自ライセンス」を、数値が指す最適形(Apache base 継承 + 独自 conduct 層)で確定。
  full-custom の落とし穴(`c8`/`c5`)を回避。
- コード/ML の二層を明文化し、ImageBind(CC-BY-NC)を Path A 境界に隔離。
- 評価が `scorecard.edn` + `score.bb` で再現可能 — 将来のスコア改定は単一 SSoT 編集で追従。

**Negative / honest limits**
- ECL 法文は未起草(D6)。ratify は Council Lv7+ 案件(D5)。
- スコアは判断であり実測ではない。`c8`(enforceability)は司法未確定; ethical-source/RAIL は
  OSI 非承認(source-available)。
- ML 重みへの copyright 成立性は係争的; §4 はそのリスク下の保守設計。

# Alternatives Considered

- **現行 Apache+Rider 維持(9.11)**。妥当だが `c4`(伝播明文化)/ `c6`(ML 条項)で
  ECL-on-Apache に劣る。ECL は実質その正規化なので移行低リスク。
- **ECL full-custom / from-scratch (8.93)**。全軸を Charter に合わせられるが `c8`=4 /
  `c7`=7 で沈む。数値上の採用理由なし。
- **OpenRAIL-M 単体 (8.48)**。ML には良いが `c1`=8(Charter 固有の排除を標準リスト外に
  追い出す)。Charter §2 Attachment を載せた hybrid(9.10)を ML 層に採るのが上位互換。
- **CC-BY-NC (3.38)**。D4 の通り profit 軸の異物。不採用。

# References

- `90-docs/papers/2606171500-license-charter-fit-evaluation/` — 数値評価 paper + `scorecard.edn` + `score.bb`
- ADR-2605192200 — Apache 2.0 + Charter Rider 正本(ECL 移植元)
- ADR-2605192100 — Mission Charter / ADR-2606062100 — 3-Tier immutability / ADR-2606082400 — Rider v3.1
- ADR-2606061000 — Maxwell(起点)/ ADR-2606170840 / 2606171100 — Maxwell-Diffusion(テキスト拡散 sibling)
- ADR-2606122001 — tanemaki DD スコアカード様式
- `/CHARTER-RIDER.md` — Rider v3.1 正本
- [facebookresearch/ImageBind — LICENSE (CC-BY-NC 4.0)](https://github.com/facebookresearch/ImageBind/blob/main/LICENSE)
