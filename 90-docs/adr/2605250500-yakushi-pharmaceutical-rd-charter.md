---
id: adr-2605250500-yakushi-pharmaceutical-rd-charter
title: "yakushi (薬師) pharmaceutical R&D charter — religious-corp first-party API + sterile fill-finish + supply chain (OTC ophthalmic triplet as Wave 1 reference)"
status: proposed
doc_type: adr
topic: yakushi-pharma-charter
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - yakushi actor identity (name, DID pattern, tier) — religious-corp first-party pharmaceutical R&D
  - Charter Rider §2 clearance reasoning for OTC OTC small-molecule pharmaceuticals
  - 4-phase roadmap R0 → R3 with explicit Council-attestation gating per phase
  - Pharmaceutical-specific constitutional gates G1..G14 (non-negotiable)
  - Non-goals N1..N10 (constitutional, not subject to incremental drift)
  - Wave 1 reference target = OTC antihistamine eye drop triplet (cromoglicate Na + naphazoline HCl + chlorpheniramine maleate)
  - Sub-ADR registry (ADR-2605250515 / 2605250530 / 2605250545)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605192400-etzhayyim-eros-gore-council-judging
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605231500-kotoba-datomic-projection
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605242715-silicon-mask-supply-chain
related:
  - 20-actors/yakushi/                              # this ADR creates this tree
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_*/              # this ADR creates the 8 pharma Pregel cells
  - 00-contracts/lexicons/com/etzhayyim/pharma/     # this ADR creates the 8 pharma Lexicons
  - 50-infra/murakumo/fleet.toml                    # cell placement (Phase R1+ post-Council)
supersedes: []
superseded_by: []
---

# Context

## ADR-2605192100 §1.5 は「new technology and intellectual property の free release to charter-aligned others」を mission として宣言した

その mission は今、`baien` (LLM), `kuni-umi` (utility infra), `iwakura/fuigo` (silicon), `wadachi` (mobility), `tsukuru` (fab) という actor 群で物理 substrate を段階的に open 化している。

ただし **生命の最も intimate な substrate ― 医薬品** はまだ覆われていない。

ADR-2605192100 が宣言する「人類の構造的労働解放」「Wellbecoming (動的軌跡)」「多世代 priority」は、現代社会において **医薬品アクセスの脱・特権化** を強く含意する。Charter Rider §2(e) は specialist gatekeeping (「監督適切性を超えた知識アクセスの人工的制限」) を Non-Aligned 行為として明示している。**医薬品の合成・精製・QC・製剤化の knowledge は、religious-corp が open-source として再生産する正当な対象**。

## 抗アレルギー OTC 点眼薬 triplet が Wave 1 reference target である理由

| 化合物 | 初登場 | 役割 | 特許状況 | 合成複雑度 |
|---|---|---|---|---|
| **クロモグリク酸ナトリウム** (sodium cromoglicate, DSCG) | 1965 (Fisons / 英国) | mast cell stabilizer | 全 jurisdiction で perpetually off-patent | 中 (4,6-diacetylresorcinol + epichlorohydrin → 2× chromone-2-carboxylate → di-Na salt) |
| **ナファゾリン塩酸塩** (naphazoline HCl) | 1942 (Ciba / Switzerland) | α-adrenergic vasoconstrictor | 全 jurisdiction で perpetually off-patent | 低 (1-naphthylacetonitrile + ethylenediamine → imidazoline; HCl 塩化) |
| **クロルフェニラミンマレイン酸塩** (chlorpheniramine maleate) | 1949 (Schering) | first-generation H1 antagonist | 全 jurisdiction で perpetually off-patent | 中 (2-(4-chlorophenyl)-2-(2-pyridyl)acetonitrile → N,N-dimethyl-3-aminopropyl alkylation → maleate 塩化) |

この 3 化合物は:

1. **全て 80 年近い safety record を持つ generic OTC API** ― Charter Rider §2(f) multi-generational harm が懸念する「foreseeably 25 年後への irreversible 損失」とは正反対の category (むしろ multi-generational safety が確立済み)
2. **PMDA / FDA / EMA の OTC switch が全 jurisdiction で完了**しており、特殊な処方箋規制対象外
3. **合成経路が文献に open で、TLC + HPLC + IR + NMR の四点 QC で identity / purity を確定できる**規模 ― 厳格な GMP 自動化を religious-corp が自前で組み上げる R&D template として最適
4. **adherent 人口に多発しうる季節性アレルギー結膜炎** (花粉症結膜炎、ハウスダスト) の主要治療薬であり、religious-corp の self-care 自給能力に直結する

つまり **「religious-corp が自前で薬を作る」最も控えめな最初の証明**として、この triplet を Wave 1 reference に置く。

## 一方で薬は弾より遥かに deontologically 慎重を要する

薬は:

- **薄い therapeutic window** (naphazoline 例: 推奨 0.05% で 1-2 drops/eye、6 hr 以上の reapply 警告 ― rebound congestion / rhinitis medicamentosa)
- **不純物が直接 patient 副作用に転化** (chlorpheniramine の 4-chlorophenyl alkyl chloride 中間体は genotoxic 不純物 (PGI) クラス — ICH M7 限度 1.5 µg/day)
- **製造ロット間 variation が patient outcome に影響** (cromoglicate の sodium salt 水和数、粒度分布が点眼後 bioavailability に影響)
- **adverse event signal の検出と open reporting** が "release-and-forget" を許さない

したがって yakushi は: **「Apache 2.0 + Charter Rider を医療規制 (PMDA Drug Master File, FDA DMF, EMA CEP, ICH Q1/Q3/M7, USP/JP 公定書) の中に重ねた最初の religious-corp actor」** として固有のガバナンス層を持つ必要がある。

## Charter Rider §2 全 clearance 分析

| 条項 | 判定 | 根拠 |
|---|---|---|
| §2(a) WEAPONS AND MILITARY | **CLEAR** | OTC 点眼薬は治療薬。但し §2(a) の chemical weapons (CWC) precursor 二次利用リスクは原料側に残るため G7 で別途 gate (e.g. naphazoline の 1-naphthylacetonitrile 中間体は CWC 非該当だが、kg-scale 取扱いの透明性は要請) |
| §2(b) SPECULATIVE FINANCE | **CLEAR** | 該当なし |
| §2(c) SURVEILLANCE CAPITALISM | **CLEAR** | adverse event reporting は患者 DID 自署で encrypted、再販ターゲティング禁止 (G10) |
| §2(d) FOSSIL FUEL EXTRACTION (NEW) | **CLEAR** | 該当なし。但し 原料の petrochemical 起源は §2(d) ongoing 例外、§2(f) で別途 multi-gen 影響を点検 |
| §2(e) SPECIALIST GATEKEEPING | **PRO-CLEAR — actively counters §2(e)** | yakushi の存在意義そのものが §2(e) (i)(ii) (medical knowledge artificial restriction) の constitutional counter-action。**ただし「legitimate technical safety oversight by qualified practitioners」例外は active** ― QP (Qualified Person, EU) / 製造管理者 (PMDA) 相当の専門家 review を Council Lv6+ に co-sign 義務 (G6) |
| §2(f) MULTI-GENERATIONAL HARM | **CLEAR** | 3 化合物とも 80 年級 multi-generational safety 確立。但し新規化合物・新規剤形は ADR-2605250515 §Phase Gate ごとに別 review |
| §2(g) STRICT INDIVIDUALIST ONTOLOGY | **CLEAR** | 該当なし |
| §2(h) WELLBECOMING SUBORDINATION VIOLATION | **CLEAR with G11 gate** | naphazoline rebound congestion は label-warned で addictive design ではないが、yakushi は (i) 過剰連用 prevention の patient education を製品同梱、(ii) addiction risk 高い剤形 (e.g. opioid) は別 carve-out で別 ADR を要求 |
| §2(i) COMMERCIAL GPU RENTAL | **CLEAR** | inference は全て Murakumo fleet 経由 (e.g. HPLC peak deconvolution、QC anomaly detection) |

**総合**: Charter Rider §2 全条項 clearance。むしろ §2(e) の constitutional 推進力として yakushi は positively 整合する。

# Decision

## Decision 1 — religious-corp は自前で OTC 小分子 API + 製剤 + supply chain を所有する actor `yakushi` を確立する

| 設計対象 | 仮称 | 役割 | サブ ADR |
|---|---|---|---|
| API 合成 (Wave 1) | (3 化合物) | cromoglicate Na + naphazoline HCl + chlorpheniramine maleate の合成・精製・QC | ADR-2605250515 |
| Sterile fill-finish + primary container | (eye drop BFS bottle) | blow-fill-seal 5 mL multi-dose 滴下容器 / sterile fill 工程 / preservative-free 設計 / dropper tip | ADR-2605250530 |
| Supply chain + 8 robotics specs | (excipient, packaging, cold chain) | 賦形剤 / 等張化剤 / pH 緩衝剤 / 保存料 / 二次包装 / cold chain 物流 / GMP 文書 | ADR-2605250545 |

## Decision 2 — actor identity

| Field | Value |
|---|---|
| Actor name | `yakushi` |
| Japanese | 薬師 (やくし) — pharmacist / healer の歴史名。8 世紀典薬寮 (Tenyakuryō) 系譜の現代 echo |
| Display name | `薬師 (yakushi)` |
| Tier (ADR-2605192415 §B) | **B** (per-domain leader; sibling of `kuni-umi`, `wadachi`, `tsukuru`, `iwakura`, `fuigo`) |
| Path-based DID | `did:web:etzhayyim.com:yakushi` |
| Per-API DID pattern | `did:web:etzhayyim.com:yakushi:api:<inn-slug>` (e.g. `:api:sodium-cromoglicate`) |
| Per-lot DID pattern | `did:web:etzhayyim.com:yakushi:lot:<lotId>` |
| Per-product DID pattern | `did:web:etzhayyim.com:yakushi:product:<productCode>` |
| Repo location | `20-actors/yakushi/` |
| Lexicon namespace | `com.etzhayyim.pharma.*` (NOTE: actor 名 ≠ lexicon namespace ― silicon と同じ命名 — `com.etzhayyim.silicon.*` for `iwakura`/`fuigo`/`tsukuru`) |
| License | Apache 2.0 + Charter Compliance Rider v2.0 |

「薬師」は **Yakushi Nyorai** (Medicine Buddha) の echo を持つが、etzhayyim は ADR-2605192100 §1.6 で declared された synthetic religion ― Buddhist tradition の medicinal motif を Tree of Life (Ezekiel 47:12「leaves for healing」) と統合的に解釈し、専有しない (§1.6 八百万的多源宗教観)。

## Decision 3 — Constitutional gates (G1..G14, NON-NEGOTIABLE)

| # | Gate | Source ADR | Enforcement point |
|---|---|---|---|
| **G1** | **3 jurisdictions (PMDA / FDA / EMA) 全てで OTC switch 済み・perpetually off-patent な化合物のみ Wave 1** ― 新規分子・処方箋規制対象は別 ADR と Council Lv6+ supermajority (≥4-of-7) attestation を要求 | this ADR §1 + ADR-2605192230 | `yakushi.recordApiSelection` lexicon gate |
| **G2** | **ICH Q3A/Q3B/Q3C/Q3D/M7 不純物限度の全合致**(genotoxic impurity 1.5 µg/day、heavy metal ICP-MS、residual solvent GC-headspace、elemental impurity) ― 各 lot で QC 自署 | ADR-2605250515 §QC | `pharma_qc` cell 自動 reject |
| **G3** | **silen-pharma-review — Council Lv6+ ≥3 multisig**(silicon Wave 1 §2(a)(c) の silen-force-review に倣う):新規 API / 新規剤形 / 新規工場 / 新規 jurisdictional launch の commit ごとに Council 3 名以上の attestation を要求 | this ADR §3 (new pattern) + ADR-2605192230 | `silenPharmaReview` lexicon gate |
| **G4** | **QP (Qualified Person, EU) / 製造管理者 (PMDA) 相当の有資格者 co-sign**:各 lot の release は QP-equivalent DID で署名 ― §2(e) "legitimate technical safety oversight" 例外に対応 ― Council Lv6+ がその QP の qualification を attestation する | ADR-2605192200 §2(e) | `pharma_lot_attestation` lexicon |
| **G5** | **Adverse event public reporting**:patient self-reported AE は `com.etzhayyim.pharma.adverseEventReport` (XChaCha20-Poly1305 encrypted patient identity + public aggregated narrative) として MST に常時 open published、再販ターゲティング・保険差別利用 prohibited | ADR-2605181100 + ADR-2605192200 §2(c) | `pharma_adverse_event` cell + 受信時 lexicon validator |
| **G6** | **No prescription-only / no controlled-substance**:OTC switched ed のみ。CSA Schedule I-V、麻薬・向精神薬取締法、UN 1961 単一条約 scheduled の化合物は別 ADR を要求 ― 今回の 3 化合物は全 clear | this ADR + 国内法 | `yakushi.recordApiSelection` filter |
| **G7** | **CWC dual-use precursor monitoring**:OPCW Chemical Weapons Convention Schedule 1/2/3 / Australia Group / 国内輸出管理 precursor の取扱 transparent published, kg-scale 以上の入庫は Council Lv6+ 通知。3 化合物 Wave 1 では現状非該当だが、将来の expansion 用に gate を先置き | ADR-2605192200 §2(a) + this ADR | `pharma_raw_material` cell + receiveAttestation |
| **G8** | **Sterile process validation (USP <797> / JP 6.13 / ICH Q9 / Annex 1)**:点眼薬 sterile fill-finish の bioburden / endotoxin / sterility test を ISO 14644 Class A 環境で実施、3-batch consecutive validation を Council attestation 前提 | ADR-2605250530 §Decision 5 | `pharma_sterile_fill_finish` cell + Annex 1 attestation lexicon |
| **G9** | **Witness invariant N ≥ 2**:`recordApiSynthesis` / `recordPurification` / `recordFillFinish` / `recordLotRelease` は ≥ 2 独立 DID 署名 (process operator + QP-equivalent ; or operator + adjacent automated witness sensor) ― N=1 は auto-escalate to Council | inherited from ADR-2605201400 §5 | MST listener |
| **G10** | **patient identity の non-traceable**:adverse event / clinical observation の patient DID は XChaCha20-Poly1305 envelope (per ADR-2605181100)、aggregated narrative のみ public、再販マーケティング・保険・雇用 discrimination 利用 all reject | ADR-2605181100 + ADR-2605192200 §2(c) | lexicon schema + recipient registry |
| **G11** | **Wellbecoming subordination check**:rebound congestion / addiction / cognitive impairment 等の wellbecoming risk を product label に明示、過剰連用 detection telemetry を adherent SBT-opt-in で持つ (opt-out 自由) | ADR-2605192200 §2(h) | label scanner lint + `pharma_post_market_surveillance` cell |
| **G12** | **No commercial sale model**:adherent への配布は `donation` / `kisha` / `internal-promo` / `grant` 経由のみ。`subscription` / `purchase` for non-adherent は ADR-2605192115 §4 (non-profit 領収書) carve-out 内のみ | ADR-2605192115 §3 | TitheRouter payment-purpose filter |
| **G13** | **No server-held QP key / lot release key**:QP-equivalent / 製造管理者 / Council 署名鍵は人間 custody (passkey / hardware token)、religious-corp Worker / pod に platform-held private key 不可 | ADR-2605231525 | `e7m verify` 9th invariant |
| **G14** | **Substrate boundary**:substrate client は `@etzhayyim/sdk` 経由のみ。lot / API / adverse event の primary write store は MST + IPFS + Base L2 anchor。RW/Postgres は `kotoba-datomic-projection` の hot-path read のみ許容 (例えば lot batch query) | ADR-2605172000 + ADR-2605231500 | `e7m verify` |

## Decision 4 — Phased roadmap

各 R-phase は別 ADR を要求。**R0 (this ADR) は scaffold + design only、physical 化合物の dispense / 試薬発注 / 装置発注は一切伴わない**。

| Phase | Scope | Council attestation 要件 | 物理活動 | Status |
|---|---|---|---|---|
| **R0 (this ADR + 3 sub-ADRs)** | 4 ADR + actor scaffold + 8 lexicon + 8 pharma_* Pregel cells (全 import-time RuntimeError gate) + Murakumo fleet.toml の design-only entry | 公開 review 30 日 + Council Lv6+ ≥ 3 sign-off (this charter) | **なし** ― scaffold ファイルのみ | proposed |
| **R1** | benchtop synthesis (≤ 1 g scale, 大学化学実験室相当) ― 3 化合物それぞれの reference synthesis を IPFS published、HPLC/IR/NMR identity confirmation | R0 ratified + 1 QP-equivalent on Council + 設備 (反応容器 / クロマト / 分析機器) 設計 attestation | **R1 ADR + 別 commit** (実験設備の手配・操作は ADR の中で human-supervised PoC として narrated) | ⏳ separate ADR |
| **R2** | pilot-scale GMP-equivalent batch (≤ 100 g API) ― ICH Q3 全不純物プロファイル ・ 3-batch consistency ・ stability protocol 開始 | R1 ratified + Council 5-of-7 Safe + 1 PMDA-equivalent 製造管理者 on Council + Annex 1 sterile facility 整備 attestation | **R2 ADR + 別 commit** | ⏳ separate ADR |
| **R3** | community-scale OTC eye drop production (adherent + community 規模、~1000 bottles / batch) ― QP release / GMP audit / adverse event monitoring full operational | R2 ratified + 公開 review 60 日 + 当該 jurisdiction の薬事手続 (PMDA OTC switched API は届出ベース、ただし製造業許可 + GMP 適合性調査) | **R3 ADR + 別 commit**;jurisdiction ごとに別 sub-ADR | ⏳ separate ADR |

## Decision 5 — Non-goals (constitutional, explicit)

| # | Non-goal | Why |
|---|---|---|
| N1 | **新規分子の de novo design / discovery / clinical trial** | yakushi は **既知 generic OTC API の自前再生産** が範囲。新薬開発は別 carve-out + 別 ADR + 多年 multi-gen 影響レビュー (§2(f)) |
| N2 | **Prescription-only (Rx) / controlled-substance** | G6;OTC switched API のみ |
| N3 | **Biologics / cell therapy / gene therapy** | 小分子 API 範囲。biologics 以降は別 actor / 別 ADR が必要 (germline modification は §2(f) 直接抵触) |
| N4 | **Commercial sale to general public for-profit** | G12;adherent donation/kisha/internal-promo + ADR-2605192115 §4 non-profit 領収書 carve-out のみ |
| N5 | **Direct-to-consumer advertising / SNS-targeted promotion** | ADR-2605192115 §2 + Charter Rider §2(c) |
| N6 | **Pharmaceutical patent fence-building (defensive or offensive)** | Apache 2.0 + Charter Rider のみ。`gen-distilled` 系の 2-phase distill と同じ ― すべて open published |
| N7 | **Insurance / employer / state への patient adverse event 売却・連動** | G10 + Charter Rider §2(c) |
| N8 | **Animal testing in-house** ― 既存文献ベース + in-silico + 既存 generic safety record で必要十分な範囲のみ実施;新規 in-vivo testing は別 ADR と Wellbecoming review (§2(h)) を要求 | §2(f) + §2(h);3 化合物 Wave 1 は 80 年級既存 safety で N8 ベース運用可能 |
| N9 | **Frontier-beating pharmaceutical design model targeting** | ADR-2605241900 baien edge-target invariant inheritance;QC / impurity-prediction の AI 補助は edge tier に限定 |
| N10 | **Vendor (etzhayyim.com) revenue path** | yakushi inference は ADR-2605215000 Murakumo only;§2(i) inherited |

## Decision 6 — Substrate (binding)

yakushi は kuni-umi/wadachi と同じ substrate 境界を継承:

- **Primary write store** — AT MST + IPFS + Base L2 anchor via `@etzhayyim/sdk`
- **Hot-path read** — `kotoba-datomic-projection` 許容 (lot 検索、stability time-series, AE aggregation) ― deterministically rebuildable + `// kotoba-datomic-projection` marker
- **Payments** — USDC on Base L2 + `TitheRouter.route()` (10% Tithe);用途 `donation` / `kisha` / `grant` / `tithe` / `internal-promo` (SBT↔SBT) のみ
- **QP / 製造管理者 key custody** — onboard secure element / passkey / hardware token (G13)
- **Identity** — path-based DID (§Decision 2)
- **Inference** — Murakumo fleet only (LiteLLM 127.0.0.1:4000 + EVO-X2 + Mac mini gemma); commercial GPU rental 不可 (§2(i))

## Decision 7 — Murakumo fleet placement (Phase R1+ post-Council)

R0 では `50-infra/murakumo/fleet.toml` に design-only entry のみ (cell が import-time RuntimeError で gated)。R1 で Council attestation 後に実 deployment。

| Cell | 提案 Murakumo node | 理由 |
|---|---|---|
| `pharma_raw_material` | naphtali (UNSPSC procurement leader; raw material attestation の自然な拡張) | 既存 procurement orchestration の延長 |
| `pharma_api_synthesis` | zebulun (chemistry leader / 反応合成 orchestration) | 反応 monitoring; HPLC/NMR raw stream subscribe |
| `pharma_purification` | zebulun | synthesis pair |
| `pharma_qc` | levi (audit leader, witness invariant pair) | QC = analytical witness ― witness invariant N≥2 を auto enforce |
| `pharma_sterile_fill_finish` | joseph (commissioning leader / clean room construction の延長) | Annex 1 sterile facility ↔ kuni-umi commissioning と隣接 |
| `pharma_container` | simeon (kuni-umi commissioning) | BFS bottle 製造装置 commissioning |
| `pharma_packaging` | dan (decommission leader / packaging = lot 終端) | lot release & secondary packaging |
| `pharma_cold_chain` | naphtali (procurement / logistics) | cold chain logistics = procurement 経路の物流レイヤ |
| `pharma_post_market_surveillance` | levi (audit / AE witness) | adverse event aggregation = audit |
| `pharma_adverse_event` | levi | same |

(Murakumo fleet.toml の実 entry は R1 ADR で land;この ADR では design intent のみ)

# Consequences

**Positive**:

- religious-corp の self-care / multi-generational liberation mission に「医薬品アクセス open 化」を初めて explicitly carve out;§2(e) の constitutional counter-action 推進力が visible
- 3 化合物 (cromoglicate / naphazoline / chlorpheniramine) は 80 年級 multi-gen safety record で §2(f) clearance が最も静か ― Wave 1 reference として最低リスク
- 14 constitutional gates と 10 non-goals が **capability landing 前** に visible になり、retrofit drift を防止 (wadachi / silicon Wave 1 と同 pattern)
- Murakumo fleet 既存 node (naphtali/zebulun/joseph/simeon/levi/dan) を再利用、新 node 追加なし ― silicon Wave 1 の `judah` 新 node 追加と対照的に operational footprint が小さい
- sub-ADR 3 本 (2605250515 / 2605250530 / 2605250545) が API / 製剤 / supply chain を分割するため、 individual review が並列化可能

**Negative / costs**:

- 医療規制 (PMDA / FDA / EMA) 適合は constitutional invariant の外側で発生する work load ― G4 (QP co-sign) を担う human resource が必要;Council Lv6+ にこの qualification を持つ adherent が R1 までに少なくとも 1 名整備されねば R1 deploy 不能
- adverse event reporting (G5) は public published 性質上、yakushi が distributed する各 batch の使用者の側に reporting 義務を生む ― この義務を SBT↔SBT internal donation に乗せる仕組みは R3 ADR で別 design 必要
- 3 化合物の合成中間体は genotoxic impurity 警告 (G2) を含む ― 例えば chlorpheniramine 合成中の 4-chlorobenzyl chloride は ICH M7 Class 1B mutagen 該当;handling protocol の operator safety standard が religious-corp 内に lacking
- sterile fill-finish (G8) は Annex 1 (2023 改訂) の最新 GMP 要求を取り込む必要;BFS 装置の輸入もしくは自前設計 ― ADR-2605250530 で扱うが、cost / lead-time は R2 deploy のクリティカルパス

**Risks**:

- G6 / N2 / N3 / G1 が "OTC 既知化合物 only" を強制 ― これは故意の自制であり、Council Lv6+ supermajority + 30-day public objection で superseded 可能 (ADR-2605172600 governance) だが、weakening 試行は constitutional pattern として visible になる
- G4 (QP co-sign) が単一 person bottleneck になり得る ― R3 までに ≥ 2 名の QP-equivalent on Council を整備しないと release が dependent fail
- G10 (patient AE 非追跡性) と G5 (AE 公開) の同時運用は cryptographic 細工が必要 (XChaCha20 envelope + aggregated 公開 narrative);ADR-2605181100 inheritance で大半カバーされるが、AE 特有の lexicon schema は新規

# Alternatives Considered

## A. yakushi を kuni-umi のサブフェーズとして埋め込む (S6 化学物質生産)

Rejected. kuni-umi は physical utility infrastructure (電気 / 水 / 通信 / 鉄道) ;医薬品は **patient body 内に投与される** 性質が他 utility と本質的に異なり、Annex 1 sterile / ICH Q3 不純物 / QP release / adverse event reporting というガバナンス層が kuni-umi cell catalog を倍化する。silicon (iwakura/fuigo/tsukuru) が kuni-umi 直下ではなく独立 actor として scaffold された理由と同じ。

## B. 「pharma」をそのまま actor 名にする (英語 functional)

Rejected. religious-corp actor 命名 convention は Japanese metaphor (kuni-umi / wadachi / iwakura / fuigo / tsukuru / joucho / ameno / yobel) を持つ。`pharma` は role を describe するが substantive な domain claim を持たない。`yakushi` (薬師) は (i) 8 世紀典薬寮 (Tenyakuryō) 系譜の **国家機関ではない薬の生産・配布の伝統**、(ii) Yakushi Nyorai (薬師如来) の **medicine-as-religious-practice** の echo を持つ ― 両方 religious-corp の構造的 framing に合う。

## C. iyashinoki (癒しの樹) ― より直接的に Tree of Life echo

Considered close-runner. `iyashinoki` (癒しの樹 ― "healing tree") は etzhayyim/עץ חיים = Tree of Life の最も直接的な現代日本語 echo であり、Ezekiel 47:12 の non-eschatological 「leaves are for healing」と完全に整合する。Rejected for `yakushi` のみ理由は: (i) `yakushi` の方が **pharmaceutical 専門性** が言語的に明確 (`iyashinoki` は traditional medicine / shamanic も含む広範な healing を意味し得る)、(ii) `yakushi` は historical 典薬寮 (Tenyakuryō) の **institutional 系譜** を持ち、religious-corp の actor 命名の institutional 性 (kuni-umi / tsukuru) と整合する。`iyashinoki` は将来の伝統医学・自然療法 carve-out に reserved とする。

## D. Wave 1 を 1 化合物に絞る (e.g. naphazoline のみ)

Rejected. 3 化合物 triplet は **互いに synergistic な OTC 抗アレルギー点眼薬の臨床 standard formulation** であり、別個に作って patient に compounding を強いるのは Wellbecoming subordination (§2(h)) 違反に近い。3 化合物同時 carve-out は scope を増やすが、cumulative safety record が 3 化合物とも 80 年級なため §2(f) 評価は変わらない。

## E. design-only ADR (wadachi pattern) ― scaffold は別 commit

Rejected per user direction. silicon Wave 1 (iwakura/fuigo/tsukuru) は ADR + scaffold + lexicon + cell を 1 commit で land した。pharma も同 pattern を選択。reasoning: (i) 8 cells + 8 lexicons が design に対して self-evident な scaffold で、design review と scaffold review を分離する value が低い、(ii) cells は全て import-time RuntimeError gate で physical 活動を遮断しているため scaffold 自体は safe、(iii) reviewer が ADR と scaffold を同時に見られる方が design intent が伝わる。

## F. Wave 1 に prescription Rx を含める (e.g. ophthalmic antibiotics + 抗炎症)

Rejected. G6 / N2 の constitutional 自制を Wave 1 で曲げる incentive がない。OTC triplet で community-scale 自給能力を実証してから Rx carve-out を別 ADR で議論する方が、religious-corp の self-care substrate 構築という mission 上自然な順序。Rx は jurisdiction ごとに 処方箋発行権限 (Council adherent 中の medical license 保有者の有無) という別の governance 課題を引き込むため、initial scope を complicate する。

# References

- ADR-2605192100 (etzhayyim Mission Charter — §1.5 free release of technology, §1.13 Wellbecoming, §1.6 synthetic religion)
- ADR-2605192115 (economic substrate non-profit — G12)
- ADR-2605192200 (Charter Compliance Rider v2.0 — §2(a)(c)(e)(f)(h) gate sources, §2(e) "legitimate technical safety oversight" 例外)
- ADR-2605192230 (Charters Compliance Registry attestation — G1, G3 enforcement)
- ADR-2605192315 (Transparent Religious Force — G3 pharma echo: silen-pharma-review pattern)
- ADR-2605192400 (Eros/Gore content policy)
- ADR-2605192415 (religious-corp daemon architecture — Tier-B classification, Murakumo placement pattern)
- ADR-2605201400 (kuni-umi planetary infra — witness invariant N≥2 inheritance G9)
- ADR-2605181100 (encrypted confidentiality substrate — G10)
- ADR-2605172000 (RW-free substrate — G14)
- ADR-2605231500 (kotoba-datomic-projection — hot-path read carve-out)
- ADR-2605231525 (no-server-key invariant — G13)
- ADR-2605242500 (baien silicon charter — silen-force-review pattern as silen-pharma-review parent)
- ADR-2605242715 (silicon mask supply chain — supply chain ADR shape reference)
- ADR-2605250515 (sub-ADR: OTC ophthalmic API synthesis, this wave)
- ADR-2605250530 (sub-ADR: sterile fill-finish + container, this wave)
- ADR-2605250545 (sub-ADR: pharma supply chain + 8 robotics specs, this wave)
