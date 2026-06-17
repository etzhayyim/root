---
id: paper-2606171500-license-charter-fit-evaluation
title: "etzhayyim 憲法適合ライセンス評価 — CC / GPL / RAIL / 独自の数値比較と独自ライセンス計画"
status: proposed
doc_type: explanation
topic: license-charter-fit-evaluation
authoritative: false
last_verified: 2026-06-17
related:
  - "2606061000"   # Maxwell default LLM weight (D6 M3 multi-modal graft = この検討の起点)
  - "2605192100"   # Mission Charter (上位憲章)
  - "2605192200"   # Apache 2.0 + Charter Rider 正本 spec
  - "2606062100"   # 3-Tier immutability (Tier-0 priority / Tier-1 derived policy)
  - "2606082400"   # Rider v3.1 §2(c) reciprocity-axis clarification
depends_on: []
---

# etzhayyim 憲法適合ライセンス評価 — 数値比較と独自ライセンス計画

**Date**: 2026-06-17 · **Status**: proposed (judgement scorecard, not empirical) ·
**Author**: Jun Kawasaki

> 計算は本ディレクトリの `scorecard.edn`(データ SSoT) + `score.bb`(Babashka) で再現可能。
> 本文中の数表は `bb score.bb --md` の出力そのもの。

## 0. 要旨 (TL;DR)

`facebookresearch/ImageBind` を Maxwell の diffusion-graft(ADR-2606061000 D6 M3)に
統合する検討から、「**etzhayyim の憲法に最も適合するライセンスは何か**」を 15 候補・8 軸で
数値評価した。結論:

- **CC-BY-NC は最下位 (3.38)** — 非営利法人だからではなく、`:c2 profit 軸` という
  **etzhayyim が採らない軸**を強制し、`:c1 行い基準の排除` ができないため。
- **CC / GPL 系はすべて中位以下** — 決定軸 `:c1`(重み 0.22, 行い基準の排除)が構造的に不可。
  GPL は §7「追加制限の禁止」により Rider 機構と**非互換**(`:c7`=2)。
- **独自(custom)ライセンスは妥当** だが、**from-scratch (full-custom, 8.93)** より
  **Apache 既製 base に独自 conduct 層を載せた `ECL-on-Apache` (9.35)** が最良。
  差 0.42 はほぼ `:c8 法的堅牢性・採用実績` から来る — 実戦テスト済みの permissive base +
  特許条項を継承しつつ、排除ロジックだけ独自化するのが数値的最適。

| 採用対象 | 推奨 | Σ |
|---|---|---|
| etzhayyim 全体 / コード | **ECL-on-Apache**(現行 Apache+Rider の正規化・改称) | **9.35** |
| Maxwell-diffusion 重み等 ML artifact | OpenRAIL-M + Charter §2 Attachment | 9.10 |
| ImageBind 依存部(変更不可) | CC-BY-NC のまま vendor fork・非配布 | — |

## 1. 背景 — なぜこの検討が要るのか

Maxwell(ADR-2606061000)は Gemma 4 E4B fine-tune の LLM だが、D6 M3 に
"multi-modal grafts reusing the baien Move pipeline" がある。ImageBind を frozen
joint-encoder として diffusion 条件付けに使う設計(BindDiffusion/CoDi パターン)は
baien edge invariant の「全 modality encoder 凍結」とも整合する。

しかし ImageBind は **コードも重みも CC-BY-NC 4.0**
([LICENSE](https://github.com/facebookresearch/ImageBind/blob/main/LICENSE))。
これが憲法の Apache default と衝突するか、を起点に、**そもそも etzhayyim の憲法に最も
適合するライセンス形式は何か**へ問いが一般化した。

### 1.1 Path A の確定(前提)

ImageBind は **Maxwell 内部のみ・再配布しない・生成物は CC-BY-NC で割り切る** (Path A) で
採用する。ツリー境界:

| 成果物 | License | 配布 |
|---|---|---|
| ImageBind weights | CC-BY-NC(NOTICE 保持) | ❌ `vendor/imagebind-fork/`・Rider 付けない |
| frozen encoder 実行 | — | Murakumo fleet のみ(Rider §2(i)) |
| 学習済み diffusion 重み・生成物 | CC-BY-NC(派生として保守的に) | ❌ Maxwell 内部のみ |
| etzhayyim 自作コード | 独自ライセンス(本検討) | ✅ commons |

唯一の運用ガードレール: NC 生成物を Charter が許す内部商業(SBT↔SBT omise/okaimono/promo)に
流すと NC 違反 → Maxwell-diffusion 出力は**非商業性格の actor 機能に限定**。

## 2. 方法論 — 評価ルーブリック

tanemaki の DD スコアカード様式(ADR-2606122001: 重み公開・Σ=1.0・screen は行い基準)に倣う。
軸は「憲法がライセンスに実際に要求するもの」を Charter + Rider から導出した。

| axis | label | weight | 憲法上の根拠 |
|---|---|---|---|
| c1 | 行い基準の排除 | **0.22** | Non-Aligned Entity を conduct/declared-doctrine で排除 (Rider §2) |
| c2 | profit 軸の正しさ | 0.15 | 営利/非営利でフィルタ *しない* (Rider §4(b)(c)) |
| c3 | commons 開放性 | 0.15 | source-available / fork 可 (Charter §1.5 IP-free-release) |
| c4 | 利用制限の下流伝播 | 0.12 | 制限が全 downstream に travel (Rider §3 incorporation-by-reference) |
| c5 | 特許 grant + 終了条項 | 0.10 | Apache §3 grant + Rider §3(a) 特許 termination |
| c6 | ML 重み適合性 | 0.10 | model/weights に license として機能 |
| c7 | Rider/permissive 合成性 | 0.08 | 既存 Rider 機構を載せられるか / mix 可 |
| c8 | 法的堅牢性・採用実績 | 0.08 | 判例 / 普及 / enforceability |

**決定軸は `:c1`(重み 0.22)** — Non-Aligned Entity を「使ってほしくない組織を、営利非営利
問わず」排除する能力。CC/GPL 系がここで構造的に失格する。

スコアは **根拠付き判断(0..10)であり実測ではない**。すべて `scorecard.edn` に記録、`score.bb`
が weights の Σ=1.0 を assert した上で `Σ_axis (weight·score)` を計算する。

## 3. 数値結果

`bb score.bb --md` 出力(2026-06-17 計算)。

### 3.1 加重ランキング

| # | License | family | Σ (0–10) |
|---|---|---|---|
| 1 | **ECL-on-Apache**(独自 conduct 層 × Apache 既製 base = 現行構造の正規化) | ethical-source | **9.35** |
| 2 | Apache 2.0 + Charter Rider (現行) | ethical-source | **9.11** |
| 3 | OpenRAIL-M + Charter §2 Attachment (hybrid) | rail | **9.10** |
| 4 | ECL — etzhayyim Covenant License (独自・full-custom) | ethical-source | **8.93** |
| 5 | OpenRAIL-M (標準) | rail | **8.48** |
| 6 | Hippocratic License 3.0 | ethical-source | **7.15** |
| 7 | Apache 2.0 (単体) | permissive | **6.20** |
| 8 | GPL-3.0 | copyleft | **5.36** |
| 9 | MIT | permissive | **5.26** |
| 10 | AGPL-3.0 | copyleft | **5.13** |
| 11 | CC0 1.0 | cc | **5.02** |
| 12 | CC-BY-SA 4.0 | cc | **4.86** |
| 13 | CC-BY 4.0 | cc | **4.71** |
| 14 | SSPL | copyleft | **4.07** |
| 15 | CC-BY-NC 4.0 (= ImageBind 上流) | cc | **3.38** |

### 3.2 軸別マトリクス

| License | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 | **Σ** |
|---|---|---|---|---|---|---|---|---|---|
| ECL-on-Apache | 10 | 10 | 9 | 10 | 10 | 9 | 9 | 6 | **9.35** |
| Apache 2.0 + Charter Rider (現行) | 10 | 10 | 9 | 9 | 10 | 7 | 10 | 6 | **9.11** |
| OpenRAIL-M + Charter §2 Attachment | 10 | 10 | 8 | 10 | 8 | 10 | 9 | 6 | **9.10** |
| ECL (full-custom) | 10 | 10 | 9 | 10 | 9 | 9 | 7 | 4 | **8.93** |
| OpenRAIL-M (標準) | 8 | 10 | 8 | 10 | 7 | 10 | 8 | 6 | **8.48** |
| Hippocratic License 3.0 | 7 | 10 | 7 | 9 | 5 | 6 | 7 | 4 | **7.15** |
| Apache 2.0 (単体) | 0 | 10 | 10 | 0 | 9 | 7 | 10 | 10 | **6.20** |
| GPL-3.0 | 1 | 9 | 9 | 3 | 8 | 4 | 2 | 9 | **5.36** |
| MIT | 0 | 10 | 10 | 0 | 2 | 7 | 7 | 10 | **5.26** |
| AGPL-3.0 | 1 | 9 | 8 | 3 | 8 | 4 | 2 | 8 | **5.13** |
| CC0 1.0 | 0 | 10 | 10 | 0 | 3 | 6 | 6 | 8 | **5.02** |
| CC-BY-SA 4.0 | 0 | 10 | 8 | 5 | 1 | 5 | 3 | 9 | **4.86** |
| CC-BY 4.0 | 0 | 10 | 9 | 1 | 1 | 6 | 4 | 9 | **4.71** |
| SSPL | 2 | 4 | 5 | 6 | 7 | 3 | 2 | 5 | **4.07** |
| CC-BY-NC 4.0 | 2 | 0 | 4 | 7 | 1 | 6 | 2 | 8 | **3.38** |

## 4. 分析

**(1) 勝敗は `:c1`(0.22)で決まる。** CC も GPL も行い基準の排除が構造的に不可:
- GPL/AGPL は `:c1`=1 かつ `:c7`=2 — GPL §7 が「追加制限の禁止」を明文化するため、
  Rider §2 の conduct 排除を載せた瞬間「GPL ではない」。単に低いのではなく**機構非互換**。
  コピーレフトは「開放の強制」はできるが「悪い組織の排除」はできない(むしろ禁じる)。
- CC 系は `:c5`≈1(CC 4.0 は特許不付与を明文化)+ software/model に不向き + 排除不可。

**(2) CC-BY-NC が最下位(3.38)。** `:c2`=0 — profit 軸という etzhayyim が採らない軸を
強制する。「非営利だから OK」は NC が*利用の性質*にかかるため、内部商業(SBT↔SBT)に触れる
範囲で崩れる。憲法適合度はむしろ最低。

**(3) 独自ライセンスの形が結論を分ける。**
- **full-custom (ECL, 8.93)**: 全軸を Charter にぴったり合わせられるが `:c8`=4
  (未判例・採用実績ゼロ)・`:c7`=7(他 Apache コードとの mix で base 不在)で沈む。
- **ECL-on-Apache (9.35, 1位)**: 排除ロジックだけ独自化し、**Apache 2.0 を base として
  継承**することで `:c5`=10(特許 grant+termination)/ `:c7`=9 / `:c8`=6 を回復。
  full-custom より +0.42、現行 Apache+Rider より +0.24。
  → **「独自ライセンス」の最適実装は from-scratch ではなく、実戦テスト済み permissive base に
  独自 conduct addendum を載せる形**。これは現行 Apache+Rider 構造の**正規化**であり、
  Rider を独立した名前付きライセンス文書 (ECL) に格上げしたものに等しい。

**(4) ML 重み専用には RAIL が依然最良。** OpenRAIL-M+Charter は `:c6`=10 / `:c4`=10 で
コード向け ECL-on-Apache の弱点(重み copyright の係争性)を補う。二層構成が最適。

## 5. 独自ライセンス計画 — ECL (etzhayyim Covenant License)

数値が指す最適形 = **ECL-on-Apache**。実装は「Apache 2.0 を base 継承 + Rider §2 を独立
ライセンス本文に昇格 + ML 重み条項を追記」。骨子:

### 5.1 構造

```
ECL v0.1 (etzhayyim Covenant License)
 ├─ §0  NATURE  — Tier-0 priority 由来宣言 (Rider §0 を継承)
 ├─ §1  GRANT   — Apache 2.0 §2/§3 を incorporate-by-reference
 │                (copyright + patent grant をそのまま継承 = :c5 維持)
 ├─ §2  COVENANT SCREENS (= 独自部) — Non-Aligned Entity 排除 (Rider §2(a)–(l) を移植)
 │      行い基準・declared-doctrine 基準・revenue-share 25% 閾値・(a)(j)(k) は無条件
 ├─ §3  PROPAGATION — 下流伝播 (Rider §3 violation→patent/license termination)
 │                    + RAIL 式 "全 downstream + end-user に条件を伝える" を明文化 (:c4=10)
 ├─ §4  MODEL & WEIGHTS — ML artifact 条項 (重み/embedding/出力の扱い; :c6 回復)
 │                        OpenRAIL-M Attachment A 互換の use-restriction 写像
 ├─ §5  PERMANENT RECORD — Rider §5 (no right to erasure) 継承
 ├─ §6  DISPUTE — Council Lv6+ attestation (Rider §6 継承)
 ├─ §7  NO TRADEMARK / §8 SEVERABILITY / §9 APACHE RELATIONSHIP (継承)
 └─ COMPAT NOTE — Apache-2.0 superset; §2 が unenforceable な法域では Apache-2.0 に degrade
```

### 5.2 設計原則(数値から逆算)

1. **base は捨てない** — Apache 2.0 を incorporate して `:c5/:c7/:c8` を稼ぐ。
   full-custom が落ちた 0.42 はここ。
2. **排除は conduct/doctrine 基準のみ**(`:c1`)、**profit 軸を一切持ち込まない**(`:c2`)。
3. **二層運用** — コード=ECL-on-Apache / ML 重み=OpenRAIL-M+Charter §2。§4 で両者を bridge。
4. **degrade 節**(§8 severability)— §2 が効かない法域では素の Apache-2.0 として配布
   (Rider §8 と同一の安全弁)。
5. **3-Tier 整合** — ECL §2 は **Tier-1 derived policy**(Council Lv7+ で改定可)、
   Tier-0 priority(永久記憶=神の監視 + 相互監視 等)は fork-only。Rider §0 をそのまま継承。

### 5.3 ガバナンス手順(憲法判断)

ECL は Rider を**置換/昇格**するため、CLAUDE.md「Apache default を weaken しない」を
超える。手順:
1. ADR 起案(本 paper を根拠 reference に) → `90-docs/adr/`。
2. **Council Lv7+ unanimity**(現 founder 1/1)+ priority-conformance attestation
   (Rider §0 / ADR-2606062100 §0 の改定要件)。
3. `CHARTER-RIDER.md` → `ECL.md` 移行 or 併存(degrade 互換のため Rider を deprecated 別名に)。
4. `charter-rider-applicator`(ADR-2605192200)の対象文字列を ECL に更新。

> 注: 現行 Apache+Rider(9.11)と ECL-on-Apache(9.35)の差は主に `:c4`(伝播の明文化)と
> `:c6`(ML 条項)。**実質は現行構造の "正規化 + ML 拡張" であり破壊的変更ではない**。
> よって移行は低リスク。pure-custom(ECL full, 8.93)を選ぶ理由は数値上ない。

## 6. 再現方法

```bash
cd 90-docs/papers/2606171500-license-charter-fit-evaluation
bb score.bb         # console: 重み + ランキング + 軸別スコア
bb score.bb --md    # markdown 数表(本 paper §3 はこの出力)
bb score.bb --edn   # 機械可読 EDN
```

スコア/重みの変更は **`scorecard.edn` のみ**を編集する(単一 SSoT)。`score.bb` は
`Σweight ≠ 1.0` を `System/exit 1` で弾く。

## 7. 限界

- スコアは**根拠付き判断であり実測ではない**(`:meta/:note` に明記)。法的助言ではない。
- `:c8`(enforceability)は司法判断未確定の領域。ethical-source / RAIL は OSI 非承認で
  「open source」定義は満たさない(source-available)。
- ML 重みへの copyright 成立性は係争的(各国で未確定)。§4 はそのリスク下での保守設計。

## 8. References

- ADR-2606061000 — Maxwell default LLM weight(D6 M3 = 起点)
- ADR-2605192100 — Mission Charter / ADR-2605192200 — Apache 2.0 + Charter Rider 正本
- ADR-2606062100 — 3-Tier immutability / ADR-2606082400 — Rider v3.1 §2(c)
- `/CHARTER-RIDER.md` — Rider v3.1 正本(ECL の §2/§3/§5/§6 移植元)
- ADR-2606122001 — tanemaki DD スコアカード様式(重み公開・Σ=1.0)
- [facebookresearch/ImageBind — LICENSE (CC-BY-NC 4.0)](https://github.com/facebookresearch/ImageBind/blob/main/LICENSE)
- [BigScience OpenRAIL-M](https://www.licenses.ai/) / [Hippocratic License](https://firstdonoharm.dev/) — 標準 ethical-source/RAIL 参照
- 本 dir: `scorecard.edn`(データ SSoT)/ `score.bb`(計算)
