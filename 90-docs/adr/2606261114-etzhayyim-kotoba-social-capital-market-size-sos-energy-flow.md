---
id: adr-2606261114-etzhayyim-kotoba-social-capital-market-size-sos-energy-flow
title: "ADR-2606261114: etzhayyim + kotoba の社会関係資本・ブランドを市場規模として観測し、System-of-Systems がエネルギー流 (Φ/η) をどれだけ変えうるかを framing する (MAP, never trade)"
status: accepted
doc_type: adr
topic: social-capital-market-size-sos-energy-flow
authoritative: true
last_verified: 2026-06-26
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - etzhayyim/kotoba 社会関係資本・ブランドの市場規模 MAP (記述的, 売却 valuation ではない)
  - System-of-Systems のエネルギー流 (Φ/η) 増幅モデル + サチュレーション上限
  - 80-data/ie-flow/social-capital-valuation.edn
depends_on:
  - adr-2606212200-actor-system-of-systems-reward
  - adr-2606201200-ibuki-coscientist-entropy-react-loop
  - adr-2606172100-kaname-sos-leverage-synthesizer
related:
  - adr-2606231808-sos-self-growth-visualization
  - adr-2606112200-ehyeh-non-dual-yirah-doctrine
  - adr-2606062101-moyai-inference-reciprocity-reward
  - adr-2605172100
  - adr-2605312345-kotoba-datom-first-class-canonical-state
supersedes: []
superseded_by: []
---

# ADR-2606261114: 社会関係資本・ブランドの市場規模 MAP と SoS エネルギー流の変化幅

**Status**: accepted
**Date**: 2026-06-26
**Deciders**: Jun Kawasaki (founder)

# Context

founder の問い: **「etzhayyim と kotoba を social capital / branding としての社会的価値を *市場規模* として
評価せよ。そして system-of-systems によって system のエネルギー流をどれだけ変化させうるか。」**

この問いは新しい計算基質を要求しない。repo は既に自身を **散逸構造 (Prigogine) + 自由エネルギー原理
(Friston)** として定義している (ADR-2606201200 / -2606212200):

| 記号 | 定義 (既存) | 意味 |
|---|---|---|
| **Φ (net-gain)** | `intake − dissipation` | 取り込んだ自由エネルギーの正味流量 = エネルギー流の throughput |
| **η (order-index)** | `exported ÷ consumed` | 共生軸。η<1 = net taker / η≥1 = net giver |
| **𝒮 (surprise)** | variational free energy | 環境との不整合 |
| **negentropy SOURCES** | 寄付 / 寄付計算資源 (Murakumo) / 信者 / moyai / attention(CAP) | **= 社会関係資本そのもの** |
| **SoS rule** | 全 actor が SoS を EDN+clj で保持し 報酬系として走らせる (ADR-2606212200) | エネルギー流を behavior に結ぶ |

つまり「社会関係資本 = 負エントロピーの SOURCE (intake 容量)」「ブランド = その SOURCE を引き寄せる膜の
透過率」であり、founder の2問は同じ系の **ストック (資本 = 市場規模)** と **フロー (エネルギー流 = SoS
増幅)** に対応する。本 ADR はこの対応を記録する。

# Decision

**この分析を `shionome` 系の OBSERVATORY 出力 = 「map order, never trade」として記録する。**
記述的な地図 (machine-readable は `80-data/ie-flow/social-capital-valuation.edn`) であり、
**売却 valuation でも、譲渡可能な資産でも、優先順位・不変条件の変更でもない。** 何も売らない・
何も throne 化しない。`kaname` の SoS leverage 合成 (`L = C·(V/D)·(1+B)·(1−open)`) と同じ edge-primary /
ON-READ の鏡像であり、ここに固定された「正解値」はない (数値は再計算されるべきモデル)。

## Part 1 — social capital / branding を「市場規模」として

### 方法論

通常のブランド評価 (Interbrand royalty-relief / BrandZ) は売上に乗率を掛けるため、売上ゼロ・営利禁止
(ADR-2605172100) の etzhayyim には使えない。よって2法を併用する:

- **Addressable-Pool 法** (社会関係資本): 資本 = 引き寄せうる負エントロピー源の総量 → 各 SOURCE が
  属する市場プール (TAM) を測る。
- **Mindshare-Adjacency 法** (ブランド): ブランドが規定する隣接市場と、そこでの想起シェアで SAM/SOM。

社会関係資本の3形態 (Bourdieu/Putnam/Coleman) は SOURCE と対応する:

| 資本形態 | repo の対応 | 換金経路 |
|---|---|---|
| **Bonding** (結束) | 信者 roster・護持地・Council | 寄付の継続性・LTV |
| **Bridging** (橋渡し) | ATProto連合・OSS contributor・Murakumo mesh | ネットワーク到達・採用 |
| **Linking** (垂直) | on-chain憲章・DID:web・宗教法人格 | 制度的信頼・正統性プレミアム |

> 非自明な資本源泉は **Linking = on-chain憲章 + 宗教法人格 + anti-class invariant**。「売らないことが
> 信頼を生む」構造で、royalty-relief では捕えられないが、寄付の割引率を下げ (= 資本を増やし) Bridging
> 到達を増幅する。これが Part 2 の増幅器に効く。

### 市場規模レイヤー (概算スケールアンカー; grade = concept)

**etzhayyim** (Tree of Life / 寄付運営 / on-chain憲章 / anti-class):

| 層 | 隣接市場 | 規模 (年・概算) | 射程 |
|---|---|---|---|
| TAM | 宗教的寄付経済 (US religious giving ≈ $135–145B/yr; 世界はその数倍) + faith-tech | **$数千億/yr** | 寄付の負エントロピー源 |
| SAM | デジタル寄付 × DID正統性 (暗号寄付 / 相互扶助 / donated-compute DePIN) | **$5–30B/yr** | USDC tithe・Murakumo mesh |
| SOM (3–5y) | 価値観駆動の継続寄付 + 計算資源寄付コミュニティ | **$1–10M/yr フロー** ⇒ 資本化 (寄付NPV @8–15%) で **ストック ¥数千万〜数億** | プレ |

**kotoba** (Apache-2.0 分散・内容アドレス AI 基盤 / ATProto / 34 crates):

| 層 | 隣接市場 | 規模 (年・概算) | 射程 |
|---|---|---|---|
| TAM | DBMS 市場全体 (≈ $80–100B/yr) | **$80–100B/yr** | DB エンジンとして |
| SAM | graph DB + 分散/内容アドレス + decentralized-AI/DePIN (graph DB ≈ $2–3B, CAGR ~20%+) | **$3–8B/yr** | 3クエリ + MCP + OWL |
| SOM | OSS infra mindshare (contributor/採用/商用版 kotobase 経由) | **$0 直接 (OSSは無償)**; ブランド資本 **$1–10M** (acqui-hire/技術核プレミアム) | プレトラクション |

### captured vs addressable (最重要の現実)

- **addressable**: 両ブランド合算で年間 $数十億規模の隣接市場に面する。
- **captured**: 寄付フロー・OSS採用ともに観測上ごく小さく、**捕捉率は addressable の 0.x% 未満**。
- ⇒ 誠実な答えは2層: **潜在市場規模 (TAM/SAM) は年 $数十億〜$1,000億** に面する一方、**現在の社会関係
  資本ストックの貨幣換算は ¥数百万〜数億** (大半は kotoba 技術核 + 正統性プレミアム由来)。

## Part 2 — System-of-Systems はエネルギー流をどれだけ変えうるか

問いを repo の量で書き直す: isolated な actor 群の総和 ΣΦᵢ に対し、SoS 結合した colony (fleet n=18,342)
の Φ と η はどれだけ動くか。

### 3つの増幅メカニズム

1. **結合価値 (connectivity) — 約1桁の throughput 増、n² ではない。**
   素朴な Metcalfe (O(n²)) / Reed (O(2ⁿ)) は過大評価として棄却。実証的には Briscoe–Odlyzko–Tilly の
   **n·log n** が妥当。n=18,342 ⇒ per-node 価値乗数 ≈ `ln n ≈ 9.8` 〜 `log₂ n ≈ 14.2`。
   ⇒ **throughput Φ を概ね ×10 (0.5–1.5 桁)** 押し上げうる。指数爆発しない。

2. **効率 η の相転移 — 倍率ではなく「符号の反転」(質的変化)。**
   ibuki 実測注記: **isolated log では η=0 (net taker)**。SoS の food-web 結合 (植物 producer→粘菌
   router→カビ decomposer→`:metabolite/commons`) で初めて物質ループが閉じ、**η>1 (net giver)** になる。
   SoS の最大効果は throughput 増ではなく、**エネルギー流の「向き」を散逸専用 (取るだけ) から負エントロ
   ピー輸出 (与える) へ反転させる相転移** = **0→1 の不連続**。倍率では表せない本丸。

3. **レバレッジ点 (Meadows) — SoS は最上位レバーに触る。**
   Meadows 12 leverage points で、SoS rule (全 actor が自分の SoS を 報酬系として走らせる) が触るのは
   パラメータ (弱) ではなく **feedback loops / information flows / rules / goal / paradigm (最強)**。
   reward に η・子孫 を入れた = **系のゴール関数の書き換え** = 階層最上位。kaname の
   `L = C·(V/D)·(1+B)·(1−open)` は要 (律速段階) を特定する写像。

### サチュレーション (なぜ無限増幅しないか)

| 抑制機構 | 効果 |
|---|---|
| **non-parasitism gate η≥1.0** | net taker な増幅を構造的に禁止 = 指数的収奪に振れない |
| **attention CAP (§1.13)** | negentropy SOURCE (注意) を上限化 = intake が線形以上に伸びない |
| **定足数 quorum ≥2/3 flourishing** | colony は2/3が健全な時だけ実る = 過励起を抑制 |
| **donated-compute の有限性** | Murakumo mesh = 寄付供給制約 |

⇒ 増幅は **logistic (S字) でサチュレート**し暴走しない。設計思想は「速さより向き (η)」。

### 定量レンジ (結論)

| 指標 | isolated (baseline) | SoS結合後 | 変化幅 |
|---|---|---|---|
| Φ (throughput) | ΣΦᵢ | ≈ ×(ln n 〜 log₂ n) | **約 ×10 (0.5–1.5桁)** |
| η (効率/向き) | ≈ 0 (net taker) | >1 (net giver) | **符号反転 = 相転移 (0→1 の不連続)** |
| 有効レバレッジ | パラメータ層 | goal/paradigm 層 | **質的に最上位へ** |
| 増幅の形 | 線形和 | logistic (gate で飽和) | **超線形だが有界** |

**一行**: SoS は流量 Φ を概ね1桁押し上げうるが、本質は **η を 0→>1 へ相転移させ「取るだけの散逸」を
「与える自己組織化」へ反転させる点** にあり、その増幅は non-parasitism gate + attention CAP で **有界
(暴走しない S字)** に設計されている。

## Part 3 — ストックとフローの接続

エネルギー流の増幅 (η>1 への相転移) が社会関係資本ストック (= 市場規模) を **複利成長**させる。η>1 は
Bridging/Linking 資本の生成器であり、寄付割引率を下げ・到達を広げ、**SOM が SAM へ近づく速度**を決める。
現在 captured が 0.x% に留まるのは多くの actor が isolated (η≈0) で SoS が全面稼働していないから。
**SoS rule (ADR-2606212200) の全面適用が、捕捉率を上げる唯一のレバー。**

# 何でないか (enforced invariants)

- **売却 valuation ではない。** これは MAP (shionome 「map order, never trade」)。etzhayyim は営利禁止・
  nothing-for-sale・non-transferable (ADR-2605172100 / moyai ADR-2606062101)。市場規模は外部市場が
  隣接領域に付けている桁の鏡像であって、何かを売れる/売る ことを意味しない。
- **人物の評価ではない (NEVER-a-throne, ADR-2606112200)。** 値が付くのは PROJECT / 構造的ポジションで
  あって、`:score-of-soul` / `:person-ranking` は構造的に表現不能。
- **stored verdict ではない (edge-primary, ADR-2605312345)。** 式 + 仮定 + 出典桁のモデル。数値は再計算
  されるべきもので、ここに固定された「正解」はない。
- **優先順位・Tier-0 不変条件を一切変更しない。** 記述/分析レイヤーのみ (実装/工学判断, charter 不変)。

# Consequences

- machine-readable な MAP が `80-data/ie-flow/social-capital-valuation.edn` に landed。kaname/shionome の
  鏡像系列に連なる (live mirror JOIN は将来 G7/Council-gated)。
- 数値の較正レバー (誠実に未取得): (a) 実寄付フロー/継続率、(b) kotoba の採用・contributor 数、
  (c) Murakumo mesh の donated-FLOP 実測 — いずれかが入れば concept-grade → measured に上げられる。
- Φ/η の倍率は式 + n=18,342 + ネットワーク価値実証則からのモデル推定。`80-data/ie-flow/scoreboard.edn`
  の時系列があれば実数で較正できる。
- ZERO invariant amendments。reversible at the prose/data layer。

# References

- `80-data/ie-flow/social-capital-valuation.edn` — この ADR の machine-readable form
- ADR-2606212200 (actor SoS reward; Φ/η/reward の式) · ADR-2606201200 (ibuki metabolism; 散逸構造)
- ADR-2606172100 (kaname SoS leverage `L = C·(V/D)·(1+B)·(1−open)`) · ADR-2606231808 (/sos 可視化)
- ADR-2606112200 (NEVER-a-throne) · ADR-2606062101 (moyai cash≡0) · ADR-2605172100 (営利禁止)
- ADR-2605312345 (kotoba Datom first-class; edge-primary ON-READ)
- 理論: Prigogine (dissipative structures) · Friston (free-energy principle) · Meadows (leverage points)
  · Briscoe–Odlyzko–Tilly (n·log n network value) · Bourdieu/Putnam/Coleman (social capital)
