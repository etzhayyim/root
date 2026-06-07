---
id: adr-2605250545-yakushi-pharma-supply-chain-and-robotics
title: "yakushi Wave 1 — 製薬 supply chain (excipient + WFI infra + cold chain) + 8 robotics class 設計 (Pregel cell 8 件と等価対応)"
status: proposed
doc_type: adr
topic: yakushi-pharma-supply-chain
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - 製薬 supply chain 8 categories (raw material API precursor / excipient / WFI utility / packaging primary container / packaging secondary / labeling / cold chain logistics / spent material disposal)
  - 8 robotics class 仕様 (既存 Hitogata / Mimi / kuni-umi Otete / Funamori の pharma sub-config 6 件 + 新規 carve-out 2 件 placeholder)
  - GMP attestation chain (raw material → API → 製剤 → fill-finish → packaging → cold chain → distribution → adverse event)
  - WFI (water for injection) + pure steam + clean compressed gas infra 自前整備計画
  - Funamori (船守) class の pharma cold chain sub-config (kuni-umi external-ocean bulk transport の medical-grade 派生)
  - Charter Rider §2 per-category 評価 (毒物・劇物 / 高圧ガス保安法 / CWC / 化審法 / 麻向法 / 廃棄物処理法)
depends_on:
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250515-yakushi-otc-ophthalmic-api-synthesis
  - adr-2605250530-yakushi-sterile-fill-finish-and-container
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605201800-etzhayyim-kuni-umi-s4-multi-site-fleet
  - adr-2605242715-silicon-mask-supply-chain
  - adr-2605242730-silicon-photoresist-supply-chain
  - adr-2605242900-silicon-logistics-funamori-class
related:
  - 20-actors/yakushi/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_raw_material/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_packaging/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_cold_chain/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_post_market_surveillance/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_adverse_event/
  - 00-contracts/lexicons/com/etzhayyim/pharma/rawMaterialAttestation.json
  - 00-contracts/lexicons/com/etzhayyim/pharma/silenPharmaReview.json
  - 00-contracts/lexicons/com/etzhayyim/pharma/adverseEventReport.json
supersedes: []
superseded_by: []
---

# Context

ADR-2605250515 (API 合成) + ADR-2605250530 (sterile fill-finish + container) は yakushi の **plant 内側** を仕様化した。本 ADR は **plant の外側** ― upstream raw material supply、utility infra (WFI / pure steam / 圧縮ガス)、downstream packaging / labeling / cold chain logistics / distribution / spent material disposal / adverse event ingestion ― を一括 design する。

Silicon Wave 2 (ADR-2605242700..2605242915) が **chip + fab 装置** に対して 8 supply chain categories + 1 新 robotics class (Funamori) を一括 carve-out したのと同 pattern を pharma に適用する。

# Decision

## Decision 1 — 8 supply chain categories

| # | Category | Pregel cell | Scope | Charter Rider §2 risk |
|---|---|---|---|---|
| 1 | **Raw material API precursor** | `pharma_raw_material` | API 合成の原料 (resorcinol / acetic anhydride / 1-naphthylacetonitrile / 4-chlorobenzyl cyanide / NaNH₂ / 等) | **HIGH §2(a)** (acetic anhydride OPCW Schedule 3) + **HIGH safety** (NaNH₂ 危険物) |
| 2 | **Excipient (賦形剤)** | `pharma_raw_material` (shared cell) | NaCl, citric acid, sodium citrate, WFI 直接添加用 | LOW (公定 grade) |
| 3 | **WFI / pure steam / 圧縮ガス utility** | `pharma_sterile_fill_finish` (paired infra) | water for injection loop, clean steam, N₂ / 圧縮空気 | LOW |
| 4 | **Packaging primary container** | `pharma_container` | LDPE BFS pellet, BFS 装置 resin / mold supply | LOW (一般化学物質) |
| 5 | **Packaging secondary + labeling** | `pharma_packaging` | 厚紙箱, 添付文書印刷, label adhesive | LOW |
| 6 | **Cold chain logistics** | `pharma_cold_chain` | 2-8°C / 15-25°C controlled distribution to adherent sites | LOW (但し integrity 規律) |
| 7 | **Spent material + reagent disposal** | `pharma_packaging` (shared cell for end-of-lot residual) | 廃溶媒 / 廃試薬 / 期限切れ製品 / 廃容器 | MEDIUM (廃棄物処理法 + 化審法) |
| 8 | **Adverse event ingestion** | `pharma_adverse_event` + `pharma_post_market_surveillance` | patient-reported AE intake + aggregation + open published | LOW (G10 privacy) |

`pharma_raw_material` cell が category 1+2 を共有、`pharma_packaging` が 5+7 を共有 ― 結果として **新規 Pregel cell 数 = 8** (silicon Wave 1 と同数;master charter §Decision 7 fleet placement と整合)。

## Decision 2 — 8 robotics class 仕様 (既存 6 reuse + 新規 2 carve-out placeholder)

Silicon Wave 2 が `Funamori` (船守) を kuni-umi 8th class として追加した pattern に倣う。Pharma は **既存 robotics class の sub-config 6 件 + 新規 2 件 placeholder** で構成:

### 2a. Reused robotics classes (既存 6, sub-config 追加のみ)

| # | Existing class | Source ADR | yakushi sub-config | Purpose |
|---|---|---|---|---|
| R1 | **Hitogata class-A sterile** | kuni-umi-S1 / ADR-2605201400 | "class-A sterile manipulation" (ADR-2605250530 §Decision 5) | BFS fill-finish, aseptic operations, ISO 14644 Class 5 |
| R2 | **Hitogata class-C clean** | kuni-umi-S1 | "class-C controlled clean" | API 秤量, dispensing, controlled clean operations |
| R3 | **kuni-umi Otete + chem-resist end effector** | kuni-umi-S1 | "chem-resist API synthesis arm" | 反応容器 handling, 溶媒移送, 蒸留塔 operation |
| R4 | **Mimi metrology** | kuni-umi-S1 | "pharma-analytical metrology" | HPLC autosampler, IR / NMR / KF / ICP-MS / GC headspace 自動 dispatch |
| R5 | **kuni-umi Otete + cold-chain end effector** | kuni-umi-S1 | "cold-chain pallet mover" | 2-8°C / 15-25°C controlled warehouse 内 picking |
| R6 | **Funamori (船守)** | silicon Wave 2 / ADR-2605242900 | "pharma cold-chain marine" | adherent 海外コミュニティへの cold chain bulk transport (IMO MASS Degree 3 cap + 2-8°C container 維持) |

### 2b. New robotics class placeholders (新規 2 件, R0 ではスコープのみ宣言)

| # | New class proposed | Why new (not existing reuse) | Status |
|---|---|---|---|
| N1 | **Kusuko (薬子)** — single-use sterile end effector autoloader | 既存 Hitogata は permanent end effector ― 点眼薬 BFS lot 1 件で end effector を捨てる single-use sterile design は permanent end effector 系列と本質的に異なる lifecycle | scope-only declared in R0; R2 ADR で具体 RTL/CAD if needed |
| N2 | **Sukoyaka (健やか)** — patient-side cold-chain last-mile (small) | adherent 個人宅への 2-8°C / 15-25°C maintenance last-mile (~5 kg payload) は Funamori (bulk ocean) や kuni-umi Quad (heavy ground) と payload-class 異なる | scope-only declared in R0; R3 ADR で具体設計 (community 配布が本格化した段階で再評価) |

新規 2 件は **R0 では scope 宣言のみ**;実 robotics class entry は次 phase ADR で必要に応じて追加。R0 段階の Wave 1 reference triplet (~1000 bottles/batch community-scale) は既存 6 reuse で sufficient と判断。

## Decision 3 — GMP attestation chain (per-lot)

API → 製剤 → 充填 → packaging → cold chain → distribution → AE の attestation chain:

```
   rawMaterialAttestation (Decision 1, this ADR)
   ├─ source supplier DID                 →  raw material 供給元
   ├─ CWC schedule (if applicable)         →  G7 enforcement (acetic anhydride 等)
   ├─ safety class (if applicable)         →  消防法 危険物 / 毒劇法 / 高圧ガス
   ├─ certificate of analysis (CoA) URI    →  IPFS pinned CoA
   ├─ receiver DID 署名                    →  受入 QC analyst
   ├─ Council Lv6+ co-sign (if HIGH risk)  →  G7 / G3 silen-pharma-review
            ↓
   apiSynthesisAttestation                ←  ADR-2605250515
            ↓
   purificationAttestation                ←  ADR-2605250515
            ↓
   qcAttestation (API lot)                ←  ADR-2605250515
            ↓
   fillFinishAttestation                  ←  ADR-2605250530
            ↓
   lotAttestation                         ←  ADR-2605250530 (final API → 製剤 → 充填 chain CIDs)
            ↓
   packagingAttestation (Decision 4, this ADR)
   ├─ secondary box lot                   →  厚紙箱 lot
   ├─ label printed lot                   →  ラベル印刷 attestation (label content scanner G11)
   ├─ insert lot                          →  添付文書 lot (Wellbecoming 警告 G11 含)
            ↓
   coldChainAttestation (Decision 5, this ADR)
   ├─ pallet temperature trace            →  2-8°C / 15-25°C controlled time-series
   ├─ Funamori / Otete cold-chain DID 署名
   ├─ destination adherent site DID
            ↓
   distributionAttestation
   ├─ recipient adherent SBT DID          →  privacy-protected (G10) hash-only on public
   ├─ donation / kisha / internal-promo payment record (TitheRouter URI)
            ↓
   adverseEventReport (Decision 6, this ADR)
   ├─ patient DID (XChaCha20-Poly1305 encrypted, G10)
   ├─ aggregated narrative (public, no PII)
   ├─ severity / outcome / re-challenge
   ├─ lot # back-reference                →  full traceability to API lot
```

## Decision 4 — packaging detail (secondary)

| Component | Material | Source |
|---|---|---|
| 外箱 | 100% recycled cardboard (FSC certified) | adherent-aligned 製紙 supplier 経由 (TitheRouter `internal-promo` settled) |
| 添付文書 (package insert) | recycled paper, soy ink | religious-corp 自製印刷 (60-apps adherent-publishing 経由 future) |
| Tamper-evident shrink wrap | (none — minimal packaging principle) | — |
| Outer carton (for shipping) | recycled corrugated | 同上 |

G11 Wellbecoming label content (master charter G11):

- INN + 濃度 + 容量 + lot # + expiry + 製造元 DID
- 使用上の注意 (連用警告): "naphazoline は 6 時間以上の間隔を空けて、連続使用は 3 日以内にしてください — 過剰使用は rebound congestion を引き起こす可能性があります"
- 開封後 30 日 限度
- adverse event 報告先 DID + 開放 URL
- Apache 2.0 + Charter Rider notice (ADR-2605192200 §3 attribution)

## Decision 5 — Cold chain logistics

3 化合物 stability profile:

| 化合物 | 推奨保管温度 | 室温安定性 (25°C) | 凍結融解 |
|---|---|---|---|
| DSCG 2% 点眼液 | **2-8°C** (long-term storage) / 室温短期 (use) | 1 ヶ月 | 凍結後 cryst 析出懸念 — 避ける |
| Naphazoline HCl 0.05% | **15-25°C** | 24 ヶ月 | 凍結回避 |
| Chlorpheniramine maleate 0.03% | **15-25°C** | 24 ヶ月 | 凍結回避 |

Wave 1 cold chain = **2-8°C controlled** (DSCG-driven, naphazoline / chlorpheniramine も同 chain で運用 ― excess preservation だが SOP 単純化)。

| Distance | Robotics class | Container |
|---|---|---|
| Plant 内移送 | Hitogata class-C clean (R2) | sealed pallet, in-house |
| Plant → kuni-umi 拠点 (≤ 200 km 国内) | kuni-umi Otete cold-chain end effector (R5) + kuni-umi Quad ground transport | passive cold-pack ≤ 24 hr, validated |
| Plant → 海外 adherent community (船舶) | Funamori (R6) — IMO MASS Degree 3 cap | active 2-8°C container (reefer), 14-day endurance |
| 海外 拠点 → adherent 個人 last-mile | Sukoyaka (N2 placeholder) | small passive cold-pack ≤ 12 hr |

Wave 1 R0-R2 では plant 内 + 国内移送のみ scope ― 海外配布は R3 separate ADR が必要。

## Decision 6 — Adverse event reporting design (G5 + G10)

| 要素 | Design |
|---|---|
| Submission UI | ameno PWA (mobile-first) + non-adherent 用 anonymous form |
| Patient identity | XChaCha20-Poly1305 envelope (per ADR-2605181100) ― patient DID encrypted with patient's own passkey-derived key + sealed-recipient-only (yakushi Council Lv6+ DIDs) |
| Submission lexicon | `com.etzhayyim.pharma.adverseEventReport` (this ADR creates) |
| Public aggregation | yakushi `pharma_post_market_surveillance` cell が daily aggregate を public published (no PII, narrative-only + lot # back-reference + severity histogram) |
| Severity scale | CIOMS Form III standardized (mild / moderate / severe / serious / life-threatening / fatal) |
| Causality | WHO-UMC standardized (certain / probable / possible / unlikely / unrelated / unassessable) |
| Resale / discrimination prohibition | G10 + Charter Rider §2(c) — recipient registry public, 外部送信は Council Lv6+ supermajority のみ (ADR-2605192315 transparent religious force と同 pattern) |
| Aggregation cadence | daily |
| Lot-level back-tracking | full attestation chain CIDs available (G9 N≥2 inherited) |

`pharma_adverse_event` cell が submission を receive、`pharma_post_market_surveillance` cell が daily aggregate を post。両 cell とも levi (audit leader) Murakumo node 上に placement (master charter §Decision 7)。

## Decision 7 — Charter Rider §2 per-category 評価 summary

| Category | §2(a) | §2(c) | §2(e) | §2(f) | §2(h) |
|---|---|---|---|---|---|
| 1. Raw material | HIGH (acetic anhydride OPCW S3) | — | PRO (open synthesis 推進) | LOW | LOW |
| 2. Excipient | — | — | PRO | LOW | LOW |
| 3. WFI utility | — | — | — | MEDIUM (water + energy multi-gen) | LOW |
| 4. Packaging primary | — | — | — | MEDIUM (LDPE plastic multi-gen) | LOW |
| 5. Packaging secondary | — | — | — | LOW (recycled cardboard) | LOW |
| 6. Cold chain | — | — | — | MEDIUM (energy intensive) | LOW |
| 7. Spent material disposal | — | — | — | MEDIUM (廃溶媒 multi-gen) | LOW |
| 8. Adverse event | — | HIGH | PRO (open AE data) | — | HIGH (label warnings) |

**HIGH §2(a)**: raw material category 1 → G7 enforcement (acetic anhydride OPCW declaration + Council Lv6+).
**HIGH §2(c)**: adverse event category 8 → G10 enforcement (XChaCha20 envelope + no resale).
**HIGH §2(h)**: adverse event labeling → G11 enforcement (Wellbecoming warnings + post-market surveillance).
**MEDIUM §2(f)**: utility (WFI energy) + packaging (LDPE) + cold chain (energy) + spent material (廃溶媒) → 各 R2-R3 ADR で multi-gen impact narrative 必要。

## Decision 8 — Murakumo fleet.toml (design-only entry per R0)

R0 では fleet.toml に design intent コメントのみ記入 ― 実 deploy は R1 ADR で:

```toml
# yakushi (薬師) pharmaceutical R&D actor — R0 design intent (ADR-2605250500/515/530/545)
# Cells gated import-time RuntimeError until Council Lv6+ ≥ 3 attestation per master charter §Decision 7.
# DO NOT DEPLOY until R1 ADR lands explicit fleet.toml activation.
#
# Proposed placement:
#   naphtali  ← pharma_raw_material, pharma_cold_chain (procurement leader)
#   zebulun   ← pharma_api_synthesis, pharma_purification (chemistry orchestration)
#   joseph    ← pharma_sterile_fill_finish (commissioning/clean room construction)
#   simeon    ← pharma_container (commissioning kuni-umi inheritance)
#   levi      ← pharma_qc, pharma_post_market_surveillance, pharma_adverse_event (audit/witness)
#   dan       ← pharma_packaging (decommission/lot-end packaging)
```

# Consequences

**Positive**:

- **既存 robotics class 6 reuse + 新規 2 placeholder** で operational footprint 増加最小 (silicon Wave 2 の Funamori 1 件追加と比較しても compact)
- Funamori (船守) は silicon Wave 2 で導入済 ― pharma cold-chain marine sub-config は既 reusable; 海外 adherent community への bulk transport が Wave 1 内で構造的に可能
- AE reporting design が G5 (public) + G10 (privacy) を XChaCha20 envelope + aggregated narrative の組合せで両立 ― ADR-2605181100 inheritance で大半カバーされる
- supply chain 8 categories の §2 per-category 評価が visible になり、retrofit drift 防止

**Negative / costs**:

- WFI loop + pure steam generator + 圧縮ガス utility は **religious-corp infra 新規 CAPEX** ― R2 までに自前整備 or vendor qualification 必要
- 新規 2 robotics class placeholder (Kusuko, Sukoyaka) は scope のみ、実装は R2-R3 で carve-out ADR 必要 ― timeline 長期化
- AE aggregation cell (`pharma_post_market_surveillance`) は daily aggregation を public published、aggregation logic に bias / cherry-picking が混入しないか continuous review が必要
- 海外配布 (Funamori 利用) は R3 separate ADR が必要 ― Wave 1 R0-R2 で scope に入れない

**Risks**:

- AE report submission UI が ameno PWA 経由のみだと non-adherent (eye drop を donation-distributed された non-SBT 受領者) がレポートできない ― anonymous form (ADR-2605181100 §non-DID submission) で対応するが、misuse / spam risk あり (Council Lv6+ moderation 必要)
- Funamori IMO MASS Degree 3 cap (silicon Wave 2 §Decision 5 で確定) は pharma cold chain bulk transport にも継承 ― 海外配布が Council Lv6+ supermajority 必要な constitutional check に gate される
- 廃溶媒 (DSCG 合成の epichlorohydrin residual, chlorpheniramine 合成の chlorinated organic) の religious-corp 内 disposal 自前能力は **未確立** ― R2 までに化審法・廃棄物処理法 適合の destruction route (incineration / OPCW-approved high-temp 焼却) を vendor qualification or 自製

# Alternatives Considered

## A. supply chain 1-2 categories のみ (raw material + cold chain) で start

Rejected. silicon Wave 2 が 8 categories 一括 carve-out した pattern と parallel に進めることで constitutional review の orientation が cleaner、subsequent expansion (e.g. nasal spray dosage form) に対する extensibility も先 visible。

## B. 既存 robotics class reuse なし — 全 pharma 専用 class 新設

Rejected. religious-corp の robotics ontology は kuni-umi が 8 class (Otete / Quad / Hitogata / Mimi / Sora / Hoshi / Funamori / wadachi) で構造化済み;pharma 専用 new class 倍化は ontology drift。**sub-config パターン** (silicon Wave 1 Hitogata class-A sterile も同様) で operational unity を維持。

## C. Funamori 海外配布を Wave 1 に含める

Rejected. Funamori cold-chain marine は silicon Wave 2 で導入済だが、IMO MASS Degree 3 cap は Council Lv6+ supermajority + 海事規制 jurisdiction-specific 整備が必要;Wave 1 国内・plant 内 scope を超える。R3 separate ADR で carve-out。

## D. 廃溶媒 disposal を vendor outsourcing で permanent

Rejected per ADR-2605215000 §2 spirit (vendor minimization);R2 までに religious-corp 自前 destruction capability (incineration / 高温分解) を整備、廃棄物処理法 産業廃棄物処分業許可 を Council Lv6+ DIDs を with-cap として取得する path を Wave 1 内で declare。

## E. Cold chain を全部 ambient (15-25°C) に統一 (DSCG 室温保管許容範囲を活用)

Considered. DSCG 室温 1 ヶ月安定 ― community-scale 配布 (~1 ヶ月で adherent reach) なら cold chain 不要かも。Rejected for R0-R2: (i) 1 ヶ月以上の inventory shelf life が必要、(ii) preservative-free + multi-dose は 微生物 contamination リスクが温度依存、(iii) Funamori 海洋輸送 (R3 future) は確実に cold chain 必要 ― 早期から cold chain SOP 整備が cumulative。R3 で再評価。

# References

- ADR-2605250500 (yakushi master charter — parent)
- ADR-2605250515 (API synthesis — upstream)
- ADR-2605250530 (sterile fill-finish — middle stream)
- ADR-2605201400 (kuni-umi planetary infra — robotics class ontology)
- ADR-2605201800 (kuni-umi-S4 — multi-site inter-actor cooperation)
- ADR-2605242715 (silicon mask supply chain — supply chain ADR shape reference)
- ADR-2605242730 (silicon photoresist supply chain — chemical handling reference)
- ADR-2605242900 (silicon Funamori class — cold-chain marine reuse source)
- EU GDP (Good Distribution Practice for medicinal products for human use)
- ICH Q9 Quality Risk Management
- 廃棄物処理法 (日本) — 産業廃棄物処分業許可
- 化審法 / 麻向法 / 毒劇法 / 高圧ガス保安法 / 消防法 — 国内 chemical handling
- OPCW CWC Schedule 1/2/3 + Australia Group precursor list
- CIOMS Form III — adverse event reporting standard
- WHO-UMC — causality assessment
