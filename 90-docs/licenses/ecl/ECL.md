---
id: ecl-etzhayyim-covenant-license-draft
title: "ECL — etzhayyim Covenant License (DRAFT, objective-function-primary)"
status: proposed
doc_type: reference
topic: ecl-etzhayyim-covenant-license
authoritative: false
last_verified: 2026-06-17
related:
  - "2606172300"   # ECL ADR (採用判断 + 数値根拠)
  - "2606062100"   # 3-Tier immutability (固定するのは掟でなく priority)
  - "2605192100"   # Mission Charter
  - "2605192200"   # Apache 2.0 + Charter Rider 正本
  - "2606122001"   # tanemaki DD (screens→objective→route の先行型)
---

# ECL — etzhayyim Covenant License (DRAFT)

> ⚠️ **DRAFT / proposed — NOT yet in force.** ratification は Council Lv7+ unanimity
> (現 founder 1/1) + priority-conformance attestation を要する (ADR-2606172300 D5)。
> それまで有効ライセンスは **Apache 2.0 + Charter Rider v3.1** (`/CHARTER-RIDER.md`) のまま。
> 目的関数の機械可読定義は `objective-function.edn`、計算は `evaluate.bb`。

---

## Part I — 設計の考え方と経緯 (non-normative)

### I.1 経緯

1. `facebookresearch/ImageBind` (CC-BY-NC 4.0) を Maxwell の画像拡散 graft に統合できるか、
   という問いから「etzhayyim 憲法に最適なライセンス形式は何か」へ一般化。
2. 数値評価 (`90-docs/papers/2606171500-…`、15 候補×8 軸、`score.bb`) で、独自ライセンスは
   **from-scratch でなく Apache base に独自 conduct 層を載せる `ECL-on-Apache` (Σ=9.35)** が
   最良と判明 → ADR-2606172300 で採用。
3. 当初の ECL 骨子 (ADR D3) は Rider §2 の**列挙された禁止カテゴリを移植**する静的設計だった。
4. **本ドラフトはそれを転回する**: 「**原則(固定ルール/掟)で制御するのではなく、目的関数で
   動的に評価する**」。基準は **子・孫の Wellbecoming (動的軌跡)**。

### I.2 なぜ「固定ルール」でなく「目的関数」か

これは思いつきではなく、**Charter 自身の構造**から導かれる:

- **「固定するのは掟ではなく priority」** (ADR-2606062100)。Tier-0 で固定されるのは*優先順位*
  であって、個別の禁止条項ではない。列挙リストは Tier-1 の*派生*にすぎない。
- **Wellbecoming は静的 wellbeing ではなく動的軌跡**。評価対象が動的なら、評価器も動的であるべき。
  固定リストは「ある時点のスナップショット」を凍結し、新しい害の形 (まだ列挙されていない
  addictive design の変種など) を取り逃がす。
- **列挙の宿命**: 固定カテゴリは (a) 時間で陳腐化し、(b) 抜け穴を生み (リストにないから OK)、
  (c) drift する。目的関数は「priority にどれだけ資するか/反するか」を直接測るので、
  **未列挙の害も基準に照らして捕捉**できる (`evaluate.bb` の addictive-app 例: 確定フロアに
  載らないが J=-1.00 で non-aligned)。

### I.3 基準 — 子・孫の Wellbecoming

目的関数 J の telos は **子 (現世代) と 孫 (≥25y hence の未来世代) の動的 wellbecoming の
最大化**。重みもそこに集中させる (子 0.25 + 孫 0.30 = **0.55 が基準を担う**)。他の次元
(関係的 commons / 相互監視 / 労働解放) は、子孫 wellbecoming を支える enabling condition として
従属的に重みづけられる。

| dim | weight | 基準への役割 |
|---|---|---|
| `ko-wellbecoming` 子の発達軌跡 | 0.25 | 直接 |
| `mago-wellbecoming` 孫/未来世代 (不可逆性加重) | **0.30** | 直接・最重要 (多世代 priority) |
| `collective-commons` 子孫が育つ関係的土壌 | 0.20 | enabling (反個人主義) |
| `reciprocal-transparency` 見守り (子を守り孤立を断つ) | 0.15 | enabling (相互監視) |
| `labor-liberation` 子孫の労働解放 | 0.10 | mission telos |

`J = Σ_dim (weight · score)`、score ∈ [-2,+2] (子孫 wellbecoming に資する/反する)、J ∈ [-2,+2]。

### I.4 二層の正直な設計 (目的関数 primary + 確定フロア backstop)

目的関数だけにすると `c8 法的堅牢性` が落ちる — 司法は**確定可能な基準**を要し、
「我々の目的関数で 0.3 点だった」は執行しづらい。そこで二層にする:

- **Layer A — 目的関数 (primary, dynamic)**: alignment の*決定*はここで動的に行う。
  これが「考え方」の中心。`evaluate.bb` が実装。
- **Layer B — 確定フロア screens (legal backstop)**: 子孫 wellbecoming を*破滅的*に侵し、
  かつ司法執行可能な bright-line が必要なもの (CSAM / 強制労働 / 兵器ビジネス・covert 武力 /
  personal-data 売買・非対称監視 / 不可逆多世代危害) は、**目的関数の外に列挙された確定
  ルール**として残す。1つでも発火すれば scoring せず即 non-aligned。

これは tanemaki DD (ADR-2606122001) と同型: **screens が weighting の前に発火する**。
列挙が消えるのではなく、**列挙は『scoring すべきでない最悪のケース』の確定下限に縮小**し、
それ以外の広大な領域を目的関数が動的に裁く。

### I.5 3-Tier への対応 (固定するのは priority)

| Tier | 何を固定するか | 改定 |
|---|---|---|
| Tier-0 (fork-only) | **どの次元が存在し、その符号方向** (何が子孫 wellbecoming に資する/反する) | 不可 (= chain fork) |
| Tier-1 (Council Lv7+) | `:weight` / `:thresholds` / `:screens` リスト | Lv7+ unanimity + priority-conformance |
| Tier-2 (governance att.) | 個別ケースの `:scores` (evidence から算出) | Council Lv6+ attestation |

→ 「固定するのは掟ではなく priority」が文字通り実装される: 目的関数の*構造*(どの priority を
測るか) は固定、*重み/閾値*は governance パラメータ、*個別採点*は証拠ベース。

### I.6 動的スコアはどこから来るか

`:scores` は静的に書かない。観測 actor 群 (shiori=wellbecoming detractor, tsumugi=取-concentration,
danjo=accountability, inochi=孫の環境, kanjo=disclosed 決算) の **DISCLOSED 証拠を fuse** して
算出する (tanemaki 方式)。算出された scorecard は content-addressed (CIDv1) され、Council が
**1 SBT = 1 vote で bytes を検証**して attestation する。ECL は採点を*提案*し、決定は投票。

---

## Part II — License 本文 (DRAFT, normative-intent)

```
ECL — etzhayyim Covenant License, v0.1-draft
Supplements and incorporates the Apache License 2.0 ("Apache").
This text is a DRAFT; it is not in force until Council Lv7+ ratification.

§0  NATURE
    本ライセンスは etzhayyim Charter の Tier-0 priority から*導出*される。固定されるのは
    priority であって個別の掟ではない (ADR-2606062100)。本ライセンスは alignment を
    **固定列挙でなく目的関数 J で動的に評価**する。J の telos は子・孫の動的 wellbecoming。

§1  GRANT (Apache 継承)
    Licensor は Apache §2 (copyright) および §3 (patent) を incorporate-by-reference により
    付与する。本ライセンス固有の条件は、それらに*追加*される使用条件であり、Apache と矛盾
    しない範囲で効力を持つ (§10)。

§2  ALIGNMENT BY OBJECTIVE FUNCTION (primary control)
    (a) 各使用者・各使用は、目的関数 J = Σ_dim (weight · score) により評価される。
        dimensions・weights・thresholds は付随する `objective-function.edn` に定義され、
        その正本は本ライセンスに incorporate される。
    (b) score は子・孫の wellbecoming(動的軌跡)に対する資する(+)/反する(-)の度合い [-2,+2]。
        score は観測可能な DISCLOSED 証拠から算出され、content-addressed scorecard として記録
        される。
    (c) route: J ≥ +0.5 → aligned (grant 継続) / -0.5 < J < +0.5 → hold (Council 審査) /
        J ≤ -0.5 → Non-Aligned (§4 により grant 終了)。
    (d) 決定は Council attestation (§7) による。Council は J の算出を*参考*とし、1 SBT = 1 vote
        で scorecard の bytes を検証して裁定する。本ライセンスは採点を提案し、決定しない。

§3  HARD FLOOR (確定フロア — scoring 不要の bright-line backstop)
    以下のいずれかに該当する使用は、J の算出を待たず、revenue share を問わず Non-Aligned:
      (i)   児童性的虐待 / 非合意性的コンテンツ          [子 priority 直接侵害]
      (ii)  強制労働 / 人身取引 / 搾取的児童労働          [mission 直接反]
      (iii) 兵器ビジネス / proprietary 兵器 / covert(非透過)武力 / autonomous lethal
            (※透過的*防衛*力 — on-chain 監視 + open-source + 1 SBT=1 vote — は除外)
      (iv)  personal-data の売買 OR 非対称(unwatched watcher)監視ビジネス
            (※対称的*相互監視*/見守り — everyone watched, no one sold — は除外)
      (v)   不可逆な多世代危害 (環境 >±2°C / biosphere 崩壊 / commons 囲い込み / germline)
                                                          [孫 priority 直接侵害]
    これらは目的関数の代替ではなく、その*最悪ケースの確定下限*である。

§4  PROPAGATION (違反の効果)
    Non-Aligned による使用は本ライセンスの material violation であり、(a) Apache §3 の patent
    license を即時終了し、(b) Apache §4 により全 grant を終了する。条件は全 downstream および
    end-user に伝播する (good-faith な aligned downstream の権利は害されない)。

§5  MODEL & WEIGHTS
    重み・embedding・モデル出力を含む ML artifact にも §2/§3 が適用される。ML use-restriction は
    OpenRAIL-M Attachment 互換の形で、同一の目的関数 J に束ねられる。

§6  PERMANENT RECORD
    governance / force authorization / tithe / contribution / attestation の記録は kotoba Datom
    log に永久・非消去で保持される (お天道様は見ており、人は忘れない)。親密データは暗号化保持
    (暗号化 ≠ 忘却)。

§7  DISPUTE / ATTESTATION
    あるエンティティが Non-Aligned か否かは Council (Lv6+, 定足数3) の on-chain attestation で
    裁定し、30日 appeal 可。J の weights / thresholds / §3 screens の*改定*は Council Lv7+
    unanimity + priority-conformance attestation を要する (§0)。

§8  NO TRADEMARK
    "etzhayyim" / "天御柱" / "עץ חיים" / "Tree of Life" 等の名称・標章の使用権は付与しない
    (Apache §4 の fair-use attribution を超えて)。

§9  SEVERABILITY / LEGAL ANCHOR
    §2 の目的関数評価がある法域で執行不能と判断された場合、その法域では §3 の確定フロア列挙 +
    Apache 2.0 が legal anchor として残る (目的関数は governance 層、確定フロアは司法 anchor)。
    §3 全体が執行不能なら、その法域では素の Apache 2.0 として配布される。

§10 RELATIONSHIP TO APACHE
    本ライセンスは Apache を*補完*し改変しない。両者が衝突する場合、本ライセンスが Apache に
    矛盾しない*追加*条件を課す範囲で効力を持ち、それ以外は Apache が優先する。

— etzhayyim, DRAFT 2026-06-17 (Tokyo, JST)
  ADR-2606172300 / Charter ADR-2605192100 / 3-Tier ADR-2606062100
```

---

## 付録 — 再現

```bash
cd 90-docs/licenses/ecl
bb evaluate.bb                      # self-test (5 fixtures, 子+孫=0.55 が基準)
bb evaluate.bb addictive-engagement-app   # 目的関数が固定リスト外の害を動的に捕捉する例
bb evaluate.bb --edn               # 機械可読 verdict
```

目的関数の改定は **`objective-function.edn` のみ**を編集 (単一 SSoT)。`evaluate.bb` は
`Σweight ≠ 1.0` を `System/exit 1` で弾く。
