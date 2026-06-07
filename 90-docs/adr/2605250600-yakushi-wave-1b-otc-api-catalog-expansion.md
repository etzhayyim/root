---
id: adr-2605250600-yakushi-wave-1b-otc-api-catalog-expansion
title: "yakushi Wave 1b — OTC API catalog expansion (analgesic / oral antihistamine / H2 antagonist / topical) + 2 new dosage forms (oral tablet + topical cream-gel)"
status: proposed
doc_type: adr
topic: yakushi-wave-1b-otc-expansion
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - 9 additional OTC APIs across 4 therapeutic categories (analgesic+antipyretic / oral H1 antihistamine / H2 antagonist / topical)
  - 2 new dosage forms (oral solid tablet, topical cream-gel-ointment)
  - 2 new Pregel cells (pharma_tablet_manufacture, pharma_topical_formulation)
  - Extension of existing 5 lexicons (apiSynthesisAttestation, purificationAttestation, qcAttestation, fillFinishAttestation, lotAttestation) with new INN knownValues + `dosageForm` field on fillFinish + lot
  - G1 / G2 / G7 enforcement inherited from master charter — NO constitutional change to gates or non-goals
  - Per-API perpetually-off-patent date verification (oldest 1893 acetaminophen / newest 1988 loratadine; all ≥ 18 yr off-patent in 3 jurisdictions)
depends_on:
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250515-yakushi-otc-ophthalmic-api-synthesis
  - adr-2605250530-yakushi-sterile-fill-finish-and-container
  - adr-2605250545-yakushi-pharma-supply-chain-and-robotics
related:
  - 20-actors/yakushi/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_tablet_manufacture/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_topical_formulation/
  - 00-contracts/lexicons/com/etzhayyim/pharma/
supersedes: []
superseded_by: []
---

# Context

ADR-2605250500/515/530/545 (Wave 1) は OTC 抗アレルギー点眼薬 triplet (sodium cromoglicate + naphazoline HCl + chlorpheniramine maleate) を yakushi の **最低リスク starting reference target** に固定した。

User direction 2026-05-25 (current session): *「他にも OTC になっているもの をカバー」*。

意図: yakushi の §2(e) anti-gatekeeping mission を **眼科 OTC のみに留めず**、より広い therapeutic coverage (鎮痛・抗ヒスタミン・胃酸抑制・皮膚科) に拡張する。前提として **constitutional gates G1..G14 + non-goals N1..N10 を一切 weaken しない** (全 14 gate / 10 non-goal は master charter §Decision 3 + 5 で確定済)。

本 ADR は Wave 1b extension として:
- API catalog を 3 → 12 化合物に拡張
- Dosage form を sterile eye drop 1 種 → sterile eye drop + 経口固形 (oral tablet) + 外用半固形 (topical cream/gel/ointment) の 3 種に拡張
- 2 新 Pregel cells を追加 (`pharma_tablet_manufacture`, `pharma_topical_formulation`) ― 既存 fill-finish cell は sterile-only に scope 限定
- 既存 5 lexicons の `apiInn` knownValues + `dosageForm` field を extension

**新規 constitutional gate / non-goal の追加なし**。本 ADR は scope expansion のみで、Decision 3 (14 gates) + Decision 5 (10 non-goals) + Decision 6 (substrate) + Decision 7 (Murakumo placement) を継承する。

# Decision

## Decision 1 — API catalog expansion (Wave 1 3 化合物 + Wave 1b 9 化合物 = 計 12)

### 1.1 Wave 1 reference triplet (再掲、変更なし)

| # | INN | CAS | Wave |
|---|---|---|---|
| 1 | sodium cromoglicate | 15826-37-6 | 1 (eye drop) |
| 2 | naphazoline hydrochloride | 550-99-2 | 1 (eye drop) |
| 3 | chlorpheniramine maleate | 113-92-8 | 1 (eye drop) |

### 1.2 Wave 1b additions (9 化合物)

#### Category A — Systemic analgesic / antipyretic (oral tablet)

| # | INN | CAS | First marketed | Perpetually off-patent since | OTC switch (3 jurisdictions) |
|---|---|---|---|---|---|
| 4 | acetaminophen (paracetamol) | 103-90-2 | 1893 | 全 jurisdiction perpetually off-patent | PMDA / FDA / EMA 全 OTC |
| 5 | aspirin (acetylsalicylic acid, ASA) | 50-78-2 | 1897 (Bayer) | 全 perpetually | PMDA / FDA / EMA 全 OTC |
| 6 | ibuprofen | 15687-27-1 | 1969 (Boots) | ≥ 1985 | PMDA / FDA (1984) / EMA (UK 1983) 全 OTC |

#### Category B — Oral H1 antihistamine (oral tablet)

| # | INN | CAS | First marketed | Perpetually off-patent since | OTC switch (3 jurisdictions) |
|---|---|---|---|---|---|
| 7 | diphenhydramine hydrochloride | 147-24-0 | 1946 | 全 perpetually | PMDA / FDA / EMA 全 OTC |
| 8 | cetirizine dihydrochloride | 83881-52-1 | 1987 | ≥ 2007 (US) / ≥ 2009 (exclusivity expiry) | PMDA (2017) / FDA (2007) / EMA 全 OTC |
| 9 | loratadine | 79794-75-5 | 1988 | ≥ 2002 (US) / ≥ 2008 (EU exclusivity expiry) | PMDA (2017) / FDA (2002) / EMA 全 OTC |

#### Category C — Oral H2 antagonist (oral tablet)

| # | INN | CAS | First marketed | Perpetually off-patent since | OTC switch (3 jurisdictions) |
|---|---|---|---|---|---|
| 10 | famotidine | 76824-35-6 | 1986 | ≥ 2006 | PMDA / FDA (1995) / EMA 全 OTC |

#### Category D — Topical (cream / gel)

| # | INN | CAS | First marketed | Perpetually off-patent since | OTC switch (3 jurisdictions) |
|---|---|---|---|---|---|
| 11 | clotrimazole (topical 1% cream) | 23593-75-1 | 1969 (Bayer) | ≥ 1989 | PMDA / FDA (1986) / EMA 全 OTC |
| 12 | diclofenac sodium (topical 1% gel) | 15307-79-6 | 1973 oral / ≥ 1990s topical | ≥ 1985 (oral) / topical OTC continuous | PMDA / FDA (2007 topical) / EMA 全 OTC topical |

**全 12 化合物 G1 clearance** — 全 jurisdictions PMDA + FDA + EMA で OTC switched 済み + perpetually off-patent (≥ 18 年 in all 3 jurisdictions の最厳格基準を全合致)。

**N2 / N3 / N6 clearance** — Rx-only / controlled substance / biologic / new molecular entity 該当ゼロ。

### 1.3 明示的に Wave 1b では含めない化合物 (reasoning)

| INN | Why excluded from Wave 1b |
|---|---|
| pseudoephedrine | 米国 methamphetamine precursor controlled (CMEA 2005) → G6 抵触 (controlled substance jurisdictional drift) |
| codeine | 全 jurisdiction Rx → N2 直接抵触 |
| dextromethorphan | 一部 jurisdiction (一部州・国) 制限 → G6 marginal、別 ADR で再評価 |
| loperamide | 一部 jurisdiction 個数制限 (overdose risk) → §2(h) wellbecoming marginal |
| omeprazole / esomeprazole (PPI) | 多段合成 + chiral resolution 複雑 → Wave 1c 候補 (別 ADR) |
| hydrocortisone 1% topical | steroid 多段合成 or fermentation 必要 → Wave 2 (bioprocess capability 確立後) |
| sodium hyaluronate / hypromellose / PVA (lubricant eye drops) | bioprocess (Streptococcus 発酵) or 半合成 cellulose 誘導体 → Wave 2 (bioprocess capability 後) |
| naproxen | Wave 1b で ibuprofen がカバー、therapeutic 冗長 |
| miconazole | clotrimazole が代表でカバー、therapeutic 冗長 |
| tetrahydrozoline / oxymetazoline (nasal decongestant) | naphazoline Wave 1 で α-agonist class カバー、therapeutic 冗長 |

## Decision 2 — 2 新 dosage form + 2 新 Pregel cells

### 2.1 新 dosage form

| Dosage form | Cell | Sterility | Container | Murakumo node (proposed) |
|---|---|---|---|---|
| **Oral solid tablet** | `pharma_tablet_manufacture` | non-sterile (microbial limit only) | PTP blister + bottle | joseph (commissioning leader; sibling of sterile-fill — non-sterile clean room class C) |
| **Topical cream / gel / ointment** | `pharma_topical_formulation` | non-sterile for intact skin; sterile required only for ophthalmic / wound / mucosal | aluminum tube + jar | simeon (kuni-umi commissioning; sibling of container cell) |

### 2.2 既存 sterile fill-finish の scope 確定

`pharma_sterile_fill_finish` は **sterile dosage forms only**:
- eye drops (Wave 1 triplet)
- sterile ophthalmic ointment (Wave 1b 外側、deferred)
- nasal spray sterile (deferred)
- 注射 (Rx scope, N2 排除)

`pharma_tablet_manufacture` / `pharma_topical_formulation` は **non-sterile** (G8 Annex 1 sterile process validation 適用外、ただし microbial limit USP <61>/<62> 適用)。

### 2.3 Decision 7 (master charter Murakumo placement) extension

| Cell (Wave 1b 追加) | Murakumo node (proposed) | Reasoning |
|---|---|---|
| `pharma_tablet_manufacture` | joseph (commissioning) | clean room class C — sterile より一段低い grade、joseph の commissioning 拡張 |
| `pharma_topical_formulation` | simeon (kuni-umi commissioning) | container と隣接、aluminum tube filling と整合 |

既存 6 ノード再利用、Wave 1b でも新ノード追加なし (silicon Wave 1 の `judah` 追加と対照的)。

## Decision 3 — 既存 5 lexicons の extension

`apiInn` knownValues に Wave 1b 9 化合物を追加 (新規 lexicon は作らない、既存延長):

```diff
  "apiInn": {
    "type": "string",
    "knownValues": [
      "sodium-cromoglicate",
      "naphazoline-hydrochloride",
-     "chlorpheniramine-maleate"
+     "chlorpheniramine-maleate",
+     "acetaminophen",
+     "aspirin",
+     "ibuprofen",
+     "diphenhydramine-hydrochloride",
+     "cetirizine-dihydrochloride",
+     "loratadine",
+     "famotidine",
+     "clotrimazole",
+     "diclofenac-sodium"
    ]
  }
```

`fillFinishAttestation` + `lotAttestation` に `dosageForm` field 新設:

```diff
+ "dosageForm": {
+   "type": "string",
+   "knownValues": [
+     "eye-drop-sterile-bfs-multi-dose",
+     "eye-drop-sterile-unit-dose",
+     "tablet-uncoated",
+     "tablet-film-coated",
+     "tablet-enteric-coated",
+     "capsule-hard-gelatin",
+     "topical-cream",
+     "topical-gel",
+     "topical-ointment",
+     "topical-spray"
+   ]
+ }
```

`fillFinishAttestation` の `sterileFilterIntegrityPassed` / `ccitResult` / `sterilityResult` を sterile dosage forms に対してのみ required にする (non-sterile では omitted)。

`silenPharmaReview` の `scope` knownValues に Wave 1b 関連 trigger を追加:

```diff
+ "wave-1b-api-addition",
+ "wave-1b-dosage-form-tablet-attestation",
+ "wave-1b-dosage-form-topical-attestation",
+ "tablet-press-equipment-qualification",
+ "topical-mixer-equipment-qualification",
+ "non-sterile-microbial-limit-baseline"
```

## Decision 4 — Synthesis route summary (full per-compound monograph references in USP/JP)

| Compound | Synthesis steps | Key reagent risk | Reference |
|---|---|---|---|
| Acetaminophen | 1 step: p-aminophenol + Ac₂O → APAP | acetic anhydride OPCW Schedule 3 (G7 same as DSCG) | USP/JP monograph |
| Aspirin | 1 step: salicylic acid + Ac₂O → ASA | acetic anhydride OPCW Schedule 3 (G7 same) | Bayer 1897 + USP/JP |
| Ibuprofen | Hoechst-Celanese 3 steps: isobutylbenzene + Ac₂O → 4-isobutylacetophenone → 1-(4-isobutylphenyl)ethanol → carbonylation → ibuprofen | acetic anhydride (Step 1) + CO + Pd catalyst | Hoechst US 4242 193 (1981) — process expired |
| Diphenhydramine HCl | 2 steps: benzhydryl bromide + 2-(dimethylamino)ethanol → diphenhydramine → HCl salt | benzhydryl bromide (毒劇法 劇物) | Parke-Davis 1946 + USP/JP |
| Cetirizine 2HCl | 2 steps from 1-(4-chlorobenzhydryl)piperazine: + ethyl chloroacetate → ester → hydrolysis → cetirizine + 2 HCl | piperazine 中間体 | UCB 1987 + USP/EP |
| Loratadine | 6+ steps from 2-cyanomethylpyridine (chemistry detailed in R1 ADR if Wave 1b-1 promoted) | multi-step, Grignard, hetero coupling | Schering 1988 + USP/EP |
| Famotidine | 5 steps from guanidine + amidoxime route | thiazole intermediates | Yamanouchi 1986 + USP/JP |
| Clotrimazole | 1 step: 2-chlorobenzhydryl chloride + imidazole → clotrimazole | bromine/HCl gas handling | Bayer 1969 + USP/JP |
| Diclofenac sodium | Smiles rearrangement 3 steps from 2,6-dichlorodiphenylamine | chlorinated aromatic intermediates | Geigy 1965 + USP/JP |

**G7 enforcement extends to acetaminophen + aspirin + ibuprofen** — DSCG と同じ acetic anhydride (OPCW Schedule 3) Step 1。

**G2-safety extends to clotrimazole** — Br₂ / HCl gas handling 中間体は 高圧ガス保安法 + 毒劇法、危険物取扱主任者 DID co-sign 要 (master charter G7 拡張)。

## Decision 5 — QC suite extension (non-sterile dosage forms)

Wave 1 (eye drop sterile) と共通: HPLC purity / IR / NMR / KF / ICP-MS Q3D / GC headspace Q3C / 微生物学的試験 USP <61>/<62>。

Wave 1b 追加 (non-sterile):
- **Dissolution test** USP <711> (tablet — 30/60/120 min release ≥ 80%)
- **Content uniformity** USP <905> (tablet — ≤ 6.0% RSD)
- **Friability** USP <1216> (tablet uncoated — ≤ 1.0% mass loss)
- **Hardness** (informational, not pharmacopoeial monograph for OTC tablet)
- **Disintegration** USP <701> (tablet — ≤ 30 min uncoated, ≤ 60 min film-coated)
- **Viscosity** (topical — cone-plate rheometer; spec per product)
- **pH** (topical — within target range; consistency lot-to-lot)
- **Microbial limit** USP <61>/<62> (TAMC / TYMC / 特定 microorganisms)

Sterility / endotoxin / CCIT は sterile dosage forms のみ — non-sterile では NA。

## Decision 6 — Excipients (Wave 1b 新規)

| Dosage form | 主要 excipient | Pharmaceutical grade | Source |
|---|---|---|---|
| Tablet | lactose monohydrate / microcrystalline cellulose / starch / croscarmellose Na / magnesium stearate / talc | USP/EP/JP grade | adherent-aligned supplier 経由 (procurement) |
| Tablet coating | hypromellose film coating / titanium dioxide / iron oxide pigment (optional) | USP/EP/JP | 同上 |
| Topical cream | white petrolatum / mineral oil / cetyl alcohol / propylene glycol / cetomacrogol / water | USP/EP/JP | 同上 |
| Topical gel | carbomer 940 / sodium hydroxide (pH neutralization) / propylene glycol / water | USP/EP/JP | 同上 |
| Topical ointment | white petrolatum / mineral oil / lanolin (optional) | USP/EP/JP | 同上 |

`pharma_raw_material` cell が excipient 入庫を扱う (master charter §Decision 7 既存 placement)。

## Decision 7 — Constitutional gates inheritance (no changes)

| Gate (master charter §Decision 3) | Wave 1b 適用 |
|---|---|
| G1 OTC-only perpetually off-patent 3 jurisdictions | ✓ 9 全化合物確認 (§1.2 表) |
| G2 ICH Q3/M7 不純物全合致 | ✓ extended QC suite (Decision 5) |
| G3 silen-pharma-review Council Lv6+ ≥3 | ✓ Decision 3 末尾 scope knownValues extension |
| G4 QP-equivalent co-sign per lot | ✓ unchanged |
| G5 adverse event public reporting | ✓ unchanged — `pharma_adverse_event` + `pharma_post_market_surveillance` 全 dosage form 横断 |
| G6 no Rx no controlled-substance | ✓ Wave 1b 全 化合物 OTC switched 確認、pseudoephedrine / codeine / dextromethorphan 等 excluded |
| G7 CWC dual-use precursor | ✓ acetic anhydride 拡張 (acetaminophen + aspirin + ibuprofen) |
| G8 Annex 1 sterile process validation | ✓ sterile dosage form のみ適用 — tablet / topical は適用外 (非該当) |
| G9 witness invariant N≥2 | ✓ unchanged |
| G10 patient identity non-traceable | ✓ unchanged |
| G11 wellbecoming subordination label | ✓ extended — diphenhydramine sedation warning, ibuprofen GI warning, etc. |
| G12 no commercial sale | ✓ unchanged |
| G13 no server-held QP/lot release key | ✓ unchanged |
| G14 substrate boundary | ✓ unchanged |

| Non-goal (master charter §Decision 5) | Wave 1b 適用 |
|---|---|
| N1 no new molecular entity | ✓ unchanged |
| N2 no Rx no controlled-substance | ✓ Wave 1b excluded list (§1.3) で enforcement |
| N3 no biologics / cell therapy / gene therapy | ✓ unchanged — hydrocortisone (Wave 2 候補) も Wave 1b 範囲外 |
| N4 no commercial sale | ✓ unchanged |
| N5 no advertising | ✓ unchanged |
| N6 no patent fence-building | ✓ unchanged |
| N7 no insurance / employer / state AE coupling | ✓ unchanged |
| N8 no animal testing in-house | ✓ unchanged |
| N9 no frontier model targeting | ✓ unchanged |
| N10 no vendor revenue path | ✓ unchanged |

# Consequences

**Positive**:

- yakushi の §2(e) anti-gatekeeping coverage が眼科 OTC のみから **systemic analgesic + 抗ヒスタミン + GI + 皮膚科** に拡張、religious-corp adherent self-care 自給能力が大幅に向上
- 全 9 化合物 ≥ 18 年 (1893..1988 1st marketed) の OTC safety record で §2(f) multi-gen safety 評価最低リスク維持
- 2 新 dosage form (tablet, topical) で eye drop sterile 以外の **non-sterile pharmaceutical manufacturing capability** を religious-corp 内に確立 — Annex 1 sterile capability (R2 gate) と independently 進行可能
- 既存 6 Murakumo node 再利用、新ノード追加なし
- 既存 lexicon の knownValues extension のみで対応、新 lexicon 増加なし (8 lexicon 維持)
- 14 gates + 10 non-goals に変更なし — constitutional review surface unchanged

**Negative / costs**:

- API 数が 3 → 12 に増加 — 各 API の DMF (Drug Master File) 相当文書を religious-corp 内で perpetually maintain する documentation load 増加
- ibuprofen Hoechst-Celanese route は Pd 触媒 + CO ガス取扱必要 — 高圧ガス保安法 (CO) + 触媒 metal recovery 必要 (G7 safety 拡張)
- loratadine 6+ ステップは Wave 1 max complexity を超える — R1 phase で Wave 1b-1 として benchtop synthesis を別 phase に切り出す可能性
- topical 半固形製剤は化学的に sterile より単純だが、**physical stability** (phase separation, viscosity drift) の long-term stability 試験が多種 excipient combinations で必要
- diphenhydramine の sedation 警告 + ibuprofen の GI / renal 警告 + acetaminophen の hepatotoxicity (Reye 症候群 children) 警告 ― 各 dosage form label content (G11) が複雑化、`pharma_packaging` cell の label scanner template baseline (silen-pharma-review trigger) が API ごとに必要

**Risks**:

- 12 化合物 + 3 dosage form の組合せ matrix (12 × 3 = 36 一意 product code 上限) で operation footprint が R2 → R3 transition で複雑化、Council Lv6+ supermajority による Wave 1b-1 (oral analgesic) / Wave 1b-2 (oral antihistamine) / Wave 1b-3 (oral H2) / Wave 1b-4 (topical) の phased rollout が現実的になる可能性
- aspirin の Reye 症候群 (小児 < 18 yr) + acetaminophen の 過量肝障害 (single-dose 4 g 超) は label / 添付文書で詳細警告が必要 — G11 enforcement scope expansion
- ibuprofen は妊娠後期 (third trimester) の動脈管早期閉鎖リスク警告必要 — wellbecoming subordination G11 multi-gen 影響側面
- topical diclofenac は systemic exposure 低いが photosensitivity 警告必要

# Alternatives Considered

## A. Wave 1b で API catalog を全部 (PPI / steroid / lubricant も含めて) 一括追加

Rejected. PPI (omeprazole) は chiral resolution / 多段合成複雑、hydrocortisone は steroid 合成 or fermentation 必要、sodium hyaluronate は bioprocess (Streptococcus 発酵) — これらは religious-corp 内に **bioprocess + chiral chromatography capability** が無い R0-R2 時点では実装困難。Wave 2 (bioprocess capability 確立後) carve-out で別 ADR。

## B. Wave 1b を Rx-OTC switch 候補 (codeine, dextromethorphan) も含める

Rejected. G6 (no Rx no controlled-substance) は constitutional gate、Wave 1b extension は gate を一切 weaken しない方針 (§Decision 7)。codeine 全 jurisdiction Rx で N2 直接抵触、dextromethorphan は marginal で別 ADR 検討。

## C. Wave 1b を 4 化合物 (acetaminophen + aspirin + ibuprofen + clotrimazole) に絞る

Considered. Therapeutic category 数を 2 (analgesic + 抗真菌) に縮小、scope minimal で確実。Rejected: oral antihistamine (diphenhydramine + cetirizine + loratadine) は Wave 1 eye drop antihistamine の **systemic 補完** として therapeutic logical で、3 化合物追加コストが low (oral tablet 単一 dosage form 内で同一 cell)。

## D. 2 新 cell を作らず、`pharma_sterile_fill_finish` を generic `pharma_fill_finish` に rename して dosage form 分岐

Rejected. sterile dosage form の Annex 1 sterile process validation (G8) と non-sterile dosage form の microbial limit suite は **異なる constitutional gate** で評価される (G8 sterile 適用 vs. non-sterile 適用外) ため、cell を分けて gate を per-cell に明確化する方が constitutional traceability cleaner。silicon Wave 1 が `silicon_litho` と `silicon_metrology` を separate cell にした pattern と整合。

## E. Wave 1b を別 actor (`yakushi-sub` or `kusurigi`) として分離

Rejected. yakushi は **religious-corp first-party pharmaceutical R&D** の Tier-B actor。dosage form 拡張は同一 actor scope 内、別 actor 化は ontology drift。

# References

- ADR-2605250500 (yakushi master charter — parent; all 14 gates + 10 non-goals inherited unchanged)
- ADR-2605250515 (Wave 1 API synthesis — synthesis route reference pattern)
- ADR-2605250530 (Wave 1 sterile fill-finish — sterile dosage form scope definition)
- ADR-2605250545 (Wave 1 supply chain + robotics — excipient + raw material gate)
- USP-NF current edition — per-compound monographs (12 compounds)
- JP 第十八改正 — 各論
- EP 11.0 — 各論
- USP <701> Disintegration / <711> Dissolution / <905> Content Uniformity / <1216> Friability — tablet QC
- USP <61> / <62> Microbial Limit — non-sterile dosage form QC
- ICH Q3A/Q3B/Q3C/Q3D/M7 — 不純物 (inherited)
- Hoechst US 4242 193 (1981, expired) — ibuprofen Hoechst-Celanese route
- UCB 1987 patent (expired ≥ 2007) — cetirizine
- Schering 1988 patent (expired ≥ 2008 EU exclusivity) — loratadine
- Yamanouchi 1986 patent (expired ≥ 2006) — famotidine
- Bayer 1967 patent (expired ≥ 1987) — clotrimazole
- Geigy 1965 patent (expired ≥ 1985) — diclofenac
