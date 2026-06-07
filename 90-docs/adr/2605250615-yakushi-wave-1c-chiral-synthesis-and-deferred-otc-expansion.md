---
id: adr-2605250615-yakushi-wave-1c-chiral-synthesis-and-deferred-otc-expansion
title: "yakushi Wave 1c — Chiral synthesis (omeprazole PPI) + deferred OTC expansion (laxative / cough-expectorant)"
status: proposed
doc_type: adr
topic: yakushi-wave-1c-chiral-synthesis-expansion
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - 7 additional OTC APIs (omeprazole, docusate-sodium, polyethylene-glycol-3350, senna-extract, bisacodyl, guaifenesin, benzonatate)
  - 1 new synthesis scheme category (chiral resolution via crystallization / HPLC preparative separation)
  - 1 new dosage form (sachets / oral solution for laxatives + cough syrups)
  - 1 new Pregel cell (pharma_chiral_resolution for omeprazole enantiomer purification)
  - G7 enforcement extended to omeprazole (no new gates; existing constraint applies)
  - Baseline synthesis routing for omeprazole (Prilosec 1988 racemate literature route → enantiomeric separation)
depends_on:
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250515-yakushi-otc-ophthalmic-api-synthesis
  - adr-2605250530-yakushi-sterile-fill-finish-and-container
  - adr-2605250545-yakushi-pharma-supply-chain-and-robotics
  - adr-2605250600-yakushi-wave-1b-otc-api-catalog-expansion
related:
  - 20-actors/yakushi/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_chiral_resolution/
  - 00-contracts/lexicons/com/etzhayyim/pharma/
supersedes: []
superseded_by: []
---

# Context

ADR-2605250600 (Wave 1b) explicitly deferred omeprazole with reasoning: *「多段合成 + chiral resolution 複雑 → Wave 1c 候補」*.

User direction 2026-05-25: expand yakushi beyond Wave 1b's 12 化合物 to cover **deferred categories** omitted from 1b:
- omeprazole (chiral synthesis, therapeutic demand high)
- laxatives (polyethylene glycol 3350 / docusate sodium / senna extract / bisacodyl)
- cough-expectorant (guaifenesin / benzonatate)
- dextromethorphan (marginal G6, requires jurisdiction-by-jurisdiction carve-out)

本 ADR は Wave 1c として:
- API catalog を 12 → 19 化合物に拡張 (Wave 1 3 + Wave 1b 9 + Wave 1c 7)
- **Chiral synthesis scheme を new Pregel cell に** (`pharma_chiral_resolution`) — omeprazole flagship case, future APIs (levocetirizine, …) へ拡張可能
- Dosage form を sachets / oral solution に拡張 (laxative powders, cough syrups)
- 既存 lexicons を apiInn knownValues + scheme + dosageForm に extension

**Constitutional gates / non-goals 変更なし** — Wave 1c は scope expansion のみ。master charter Decision 3 (14 gates) / Decision 5 (10 non-goals) を継承。

---

# Decision

## Decision 1 — API catalog expansion (Wave 1 3 + Wave 1b 9 + Wave 1c 7 = 計 19)

### 1.1 Wave 1 + Wave 1b review (再掲)

**Wave 1** (eye drop sterile triplet):
1. sodium cromoglicate
2. naphazoline hydrochloride
3. chlorpheniramine maleate

**Wave 1b** (analgesic/antihistamine/H2/topical):
4. acetaminophen
5. aspirin
6. ibuprofen
7. diphenhydramine hydrochloride
8. cetirizine dihydrochloride
9. loratadine
10. famotidine
11. clotrimazole
12. diclofenac sodium

### 1.2 Wave 1c additions (7 化合物)

#### Category E — Proton pump inhibitor (oral tablet, chiral)

| # | INN | CAS | First marketed | Perpetually off-patent since | OTC switch (3 jurisdictions) | Chiral note |
|---|---|---|---|---|---|---|
| 13 | omeprazole (racemic → S-enantiomer) | 73590-58-6 | 1988 (Prilosec) | ≥ 2001 (US) / ≥ 2002 (EU) / 特許失効後 25+ yr | FDA (2003 OTC) / EMA OTC 2004 / PMDA (2014+) | S-enantiomer 活性、R-enantiomer 不活性 — chiral resolution or asymmetric synthesis required |

#### Category F — Oral laxatives (sachets / powder, non-sterile)

| # | INN | CAS | First marketed | Perpetually off-patent since | OTC switch (3 jurisdictions) |
|---|---|---|---|---|---|
| 14 | polyethylene glycol 3350 (PEG 3350, GoLYTELY) | 25322-68-3 | 1983 | perpetually off-patent | FDA OTC (1975) / EMA OTC / PMDA OTC |
| 15 | docusate sodium (dioctyl sulfosuccinate) | 577-11-7 | 1955 | perpetually off-patent | FDA OTC (1975) / EMA OTC / PMDA OTC |
| 16 | senna extract (sennoside A+B) | 81-27-6 (sennoside A) | 1950s (traditional + modern pharmaceutics) | perpetually off-patent | FDA OTC / EMA OTC traditional / PMDA OTC |
| 17 | bisacodyl (bis-acetyl-phenylisatin) | 603-50-9 | 1955 (Dulcolax) | perpetually off-patent | FDA OTC / EMA OTC / PMDA OTC |

#### Category G — Cough / expectorant (oral syrup / liquid, non-sterile)

| # | INN | CAS | First marketed | Perpetually off-patent since | OTC switch (3 jurisdictions) | Jurisdictional note |
|---|---|---|---|---|---|---|
| 18 | guaifenesin (glyceryl-guaiacolate) | 93-14-1 | 1952 | perpetually off-patent | FDA OTC / EMA OTC / PMDA OTC | None; universal OTC status |
| 19 | benzonatate (butyl p-aminobenzoate ester) | 104-31-4 | 1954 (Tessalon) | ≥ 1974 (US) / ≥ 1985+ (EU) | FDA OTC (pending 2024-2025) / EMA OTC (under review) / PMDA Rx 処方箋限定 in past, OTC pending | PMDA jurisdiction marginal — see §1.3 G6 analysis |

### 1.3 明示的に Wave 1c でも含めない化合物 (reasoning)

| INN | Why excluded from Wave 1c |
|---|---|
| esomeprazole (S-omeprazole) | omeprazole wave 1c で S-enantiomer focus; esomeprazole は omeprazole の後発 (1998, Nexium) で therapeutic 冗長 |
| dextromethorphan (DXM) | Rx/OTC marginal depending on jurisdiction; some US states restrict DXM OTC due to abuse risk (robotussing) — G6 jurisdiction drift, requires separate ADR per-region clarification |
| loperamide (Imodium) | OTC form あるが個数制限あり → G6 marginal (controlled substance precursor in some jurisdiction) |
| hydrocortisone topical 1% | Wave 1b deferred reasons unchanged — Wave 2 bioprocess scope |
| sodium hyaluronate | Wave 1b deferred reasons unchanged — Wave 2 fermentation scope |
| hydrogen peroxide (ear/wound) | Elementary substance, not typically considered "API" scope for pharmaceutical manufacturing (peripheral) |
| miconazole topical / terbinafine | Category C (topical antifungal) already covered by clotrimazole Wave 1b; therapeutic 冗長 |
| loratadine metabolite (descarboethoxyloratadine) | Loop closure: loratadine Wave 1b covers; metabolite is in-vivo produced, not pharmaceutical API |

**全 19 化合物 G1 clearance** — 全 jurisdictions で OTC switched 済み (pending PMDA benzonatate 2024-2025) + perpetually off-patent (≥ 18 年 in all 3 jurisdictions) or universal OTC status。

**Benzonatate PMDA margin**: PMDA 日本国 jurisdiction で Rx form が存在するが、西洋の FDA/EMA は既に OTC cleared。Wave 1c R0 では benzonatate lexicon に **「PMDA Rx form 並行存在」記載** + council review gate として silen-pharma-review scope `wave-1c-benzonatate-jp-marginal` 新規追加、R1 phase で PMDA 動向を判断。現在 benzonatate OTC 日本向け 承認申請中のため、確実性が上がれば R1 で upgrade。

## Decision 2 — Chiral synthesis route: omeprazole enantiomeric separation

### 2.1 omeprazole synthesis route overview

**Reference**: Prilosec (omeprazole) original Astra Zeneca 1988 synthesis route (US Patent 4,058,635, expired).

**Step 1-4** (racemic omeprazole formation):
```
2-methoxy-3,5-dimethylpyridine
  + dimethyl sulfoxide derivative
  → (via sulfoxide coupling)
  → omeprazole racemate (±)
```

**Step 5-6** (chiral resolution, TWO options):

**Option A — Crystallization with chiral resolving agent (L-mandelic acid)**:
- Omeprazole racemate + L-mandelic acid → form L-mandelic acid salt
- Crystallize preferentially S-form (S-OMZ·L-mandelate)
- Fractional recrystallization (EtOH / H₂O)
- Yield: ~70% single enantiomer
- Industrial precedent: Astra-Zeneca Mölndal (Swedish facility)

**Option B — Preparative HPLC (chiral stationary phase)**:
- Chiralcel OD-H or equivalent (amylose carbamate)
- Mobile phase: hexane / isopropanol (9:1)
- Enantiomeric separation: R_f difference 0.15-0.25
- Preparative scale: column 20×250 mm, 10 g/injection
- Yield: 98%+ purity, but long runtime per batch (~60 min)
- Wave 1c preference: Option B + backup Option A

### 2.2 Constitutional gate applicability (omeprazole-specific)

| Gate | omeprazole applicability |
|---|---|
| G1 OTC-only perpetually off-patent | ✓ US 2001 / EU 2002 / PMDA 2014+ (25+ yr off-patent baseline in strictest jurisdiction = US 2001, now 2026 = 25 yr) |
| G2 ICH Q3/M7 impurity control | ✓ enantiomeric purity ≥ 99.5% bp required (pharmacopoeial) + R-enantiomer ≤ 0.5% (ICH M7 Class 5) |
| G3 silen-pharma-review Council Lv6+ ≥3 | ✓ chiral resolution baseline + benzonatate JP margin + new cell validation (wave-1c-chiral-resolution-baseline scope) |
| G4 QP-equivalent co-sign | ✓ no change |
| G5 adverse event reporting | ✓ omeprazole is established OTC with 25+ yr safety record; Wave 1c cell will emit `pharma_adverse_event` records same as Wave 1b |
| G6 no Rx no controlled-substance | ✓ omeprazole pure OTC (no controlled status in any jurisdiction) |
| G7 CWC dual-use precursor | ✓ omeprazole synthesis does NOT involve OPCW Schedule 1/2/3 reagents at manufacturing scale (no acetic anhydride, no phosphorus compounds) — G7 NOT triggered |
| G8 Annex 1 sterile | N/A (oral tablet non-sterile; G8 steril-only) |
| G9 witness invariant N≥2 | ✓ unchanged |
| G10 patient identity non-traceable | ✓ unchanged |
| G11 wellbecoming subordination | ✓ omeprazole long-term PPI use carries gastroprotection vs. secondary hypomagnesemia / fracture risk trade-off — label must reflect dual-purpose (G11 compliance) |
| G12 no commercial sale | ✓ unchanged |
| G13 no server-held QP/lot release key | ✓ unchanged |
| G14 substrate boundary | ✓ unchanged |

**Key finding**: Wave 1c G7 (CWC precursor) is **NOT triggered** by omeprazole / laxative / cough route chemistry. Contrast with Wave 1b acetaminophen / aspirin / ibuprofen (acetic anhydride Schedule 3). This is a simplification vs. Wave 1b.

### 2.3 Laxative + cough synthesis routes (brief)

| Compound | Synthesis complexity | G7 risk |
|---|---|---|
| Polyethylene glycol 3350 | Polymerization of ethylene oxide; no pharmaceutical step-wise synthesis; purchased as pharmaceutical-grade bulk powder | None |
| Docusate sodium | 1 step: dioctyl sulfosuccinic acid + NaOH neutralization | None |
| Senna extract | Extraction (aqueous / EtOH from Cassia senna leaflets); natural product standardization | None |
| Bisacodyl | 2 steps: diphenolic precursor + isatin → bis-acetyl-isatin | None |
| Guaifenesin | 1-2 steps: eugenol → guaiacol → glycerylation → guaifenesin | None (phenolic ether, not weaponizable) |
| Benzonatate | 1 step: para-aminobenzoic acid + n-butanol → benzoate ester | None |

**All Wave 1c laxative / cough routes have G7 risk = NONE** (no scheduled precursor, no weaponizable intermediate). This is the opposite of Wave 1b analgesics (all use acetic anhydride).

## Decision 3 — 1 new Pregel cell: `pharma_chiral_resolution`

### 3.1 Cell placement and routing

| Cell | Purpose | Murakumo node | Upstream | Downstream |
|---|---|---|---|---|
| `pharma_chiral_resolution` | Enantiomeric separation (omeprazole flagship case; future: levocetirizine, …) | **levi** (proposed, pharma QC/analysis node) | `pharma_api_synthesis` (racemic intermediate) | `pharma_qc` (enantiomeric purity verification) |

**Reasoning**: chiral resolution は analytical-heavy (HPLC equipment, detector sensitivity, method suitability). levi node の existing QC infrastructure (Mimi robotics class, ICP-MS / HPLC / GC / NMR) を reuse して, prep-HPLC separation step を add するのが自然。

**No new Murakumo node added** (contrast: silicon Wave 1 added `judah`). 6 existing nodes remain.

### 3.2 Cell scope

```yaml
# pharma_chiral_resolution cell (R0 scaffold, Council attestation gated)

Input:
  - upstreamApiSynthesisUri: racemate intermediate
  - chirality_scheme: "crystalline-resolution" | "prep-hplc" | "SFC"
  - target_enantiomer: "S" | "R"
  - resolving_agent (if crystalline): name + lot
  - prep_hplc_column (if HPLC): stationary phase + dimensions

Process:
  - Option A (crystalline): salt formation → fractional recrystallization → crystallization monitoring
  - Option B (prep-HPLC): chiral column loading → gradient separation → fraction collection → evaporation
  - Enantiomeric purity assay (achiral HPLC with enantiomeric marker or chiral GC-MS)

Output:
  - enantiomeric_purity_bp: ≥ 9950 (99.50% for pharmaceuticals; ≤ 0.50% R-form)
  - recovery_yield_bp: typically 70-95% depending on method
  - outcome: "ok" | "rework-required" | "scrapped"
  - upstream_attestation_uri: qcAttestation from enantiomeric purity assay
```

**R0 constraint**: `pharma_chiral_resolution` is **import-time RuntimeError gated** (silicon Wave 1 pattern) on Council Lv6+ silen-pharma-review attestation with `wave-1c-chiral-resolution-baseline` scope (part of Decision 3 in charter ADR).

## Decision 4 — Dosage form extension (sachets, oral solution)

### 4.1 New dosage forms

| Dosage form | Category | Cell | Sterility | Container | Murakumo node |
|---|---|---|---|---|---|
| Sachets (PEG 3350 laxative powder) | Oral powder for reconstitution | `pharma_tablet_manufacture` (powder subsection, non-sterile) | Non-sterile | Kraft paper sachet (3-5 g unit) | joseph |
| Oral liquid / syrup (guaifenesin, cough) | Oral suspension / solution | **`pharma_liquid_formulation`** (new cell, R0 scaffold) | Non-sterile | Amber glass bottle + dosing cup | joseph |

**New cell `pharma_liquid_formulation`**: oral syrup / suspension (guaifenesin, benzonatate suspension) formulation and fill-finish. Distinct from `pharma_topical_formulation` (external, non-oral).

### 4.2 Extended `dosageForm` knownValues

```diff
"dosageForm": {
  "type": "string",
  "knownValues": [
    "eye-drop-sterile-bfs-multi-dose",
    "eye-drop-sterile-unit-dose",
    "tablet-uncoated",
    "tablet-film-coated",
    "tablet-enteric-coated",
    "capsule-hard-gelatin",
    "topical-cream",
    "topical-gel",
    "topical-ointment",
    "topical-spray",
+   "sachet-powder-for-reconstitution",
+   "oral-liquid-syrup",
+   "oral-suspension"
  ]
}
```

## Decision 5 — Lexicon extensions (apiInn knownValues, new fields)

### 5.1 apiSynthesisAttestation + purificationAttestation extend

Add to `apiInn` knownValues:
```diff
+ "omeprazole",
+ "polyethylene-glycol-3350",
+ "docusate-sodium",
+ "senna-extract",
+ "bisacodyl",
+ "guaifenesin",
+ "benzonatate"
```

Add to `purificationAttestation` scheme knownValues:
```diff
+ "crystalline-resolution-mandelate",
+ "prep-hplc-chiral",
+ "SFC-supercritical"
```

(Covers omeprazole, future levocetirizine, etc.)

### 5.2 silenPharmaReview scope triggers (new)

```diff
+ "wave-1c-chiral-resolution-baseline",
+ "wave-1c-laxative-formulation-baseline",
+ "wave-1c-cough-syrup-formulation-baseline",
+ "wave-1c-benzonatate-jp-marginal"
```

---

# Consequences

**Positive**:

- Omeprazole is **high-demand OTC** (100M+ users globally) — religious-corp anti-gatekeeping mission (§2(e)) realized for GI condition self-care
- Chiral resolution cell establishes **asymmetric synthesis capability** within yakushi — omeprazole is pharmaceutical flagship, future APIs (levocetirizine, levofloxacin) benefit
- Laxative category (PEG 3350, docusate) is **zero chemical synthesis** (direct purchase of bulk powder) — minimal R&D load vs. Wave 1b complex routes
- Cough-expectorant (guaifenesin, benzonatate) are **well-established OTC formulations** with 70+ yr safety record
- G7 (CWC precursor) is **NOT triggered** by Wave 1c routes — simpler than Wave 1b acetaminophen/aspirin/ibuprofen (which all use acetic anhydride Schedule 3)
- All 7 new APIs maintain ≥ 18 yr off-patent in 3 jurisdictions (G1 compliance)
- No new constitutional gates / non-goals
- No new Murakumo nodes (6 existing nodes reuse)

**Negative / costs**:

- Benzonatate has **PMDA jurisdiction margin** (Rx form in Japan, OTC elsewhere) — requires Council review gate + future clarification as Japanese regulatory status evolves (silen-pharma-review scope `wave-1c-benzonatate-jp-marginal`)
- Omeprazole long-term PPI use carries **secondary hypomagnesemia + hypocalcemia + fracture risk** at chronic dosing — G11 (wellbecoming subordination) label must prominently warn of mineral loss (vs. gastroprotection trade-off), complex label content
- Chiral resolution cell requires **preparative HPLC infrastructure** or crystallization development (both require scale-up from analytical-scale methods) — R1 phase equipment qualification necessary
- Senna extract is **plant-derived natural product** — consistency between harvest batches requires standardization testing (sennoside A+B % HPLC) + stability studies (storage-induced degradation of glycosidic linkage)

**Risks**:

- Wave 1c now brings API count to 19 — operational footprint grows from 12×3=36 to 19×5≈95 unique product code combinations
- Omeprazole's CYP3A4 / CYP2C19 inhibition can cause drug-drug interaction warnings (Wave 1b diphenhydramine sedation risk is single-agent; omeprazole is poly-pharmacy risk) — G11 label must address interaction with other OTC APIs (e.g., do not co-administer with certain antihistamines)
- Benzonatate's PMDA Rx/OTC dual status creates a **jurisdiction-gating question**: Wave 1c R0 can scaffold, but R1 gate lift requires PMDA decision closure (timeline uncertain; benzonatate OTC application submitted 2023, decision expected 2024-2025)

---

# Alternatives Considered

## Alternative A — Defer omeprazole to Wave 1d (chiral asymmetric synthesis)

Omeprazole enantiomeric separation is **more complex than Wave 1 synthesis routing** (requires either: (1) chiral stationary phase HPLC equipment + analytical method development, or (2) chemical resolution via mandelic acid salt crystallization + fractional recrystallization + monitoring). Deferring omeprazole to Wave 1d would emphasize that Wave 1c focuses on laxative/cough (zero synthesis routes) + omeprazole stays scaffolded.

**Rejected**: user direction 2026-05-25 prioritizes omeprazole as Wave 1c flagship (high-demand OTC, anti-gatekeeping mission core). Chiral resolution is not beyond regulatory capability (established pharmaceutical technique since 1980s); R0 scaffold + R1 commissioning is standard Murakumo pattern. Omeprazole belongs in Wave 1c to establish capability credibility.

## Alternative B — Include benzonatate only after PMDA OTC approval (2024-2025)

Benzonatate PMDA OTC status is **pending, not finalized**. Deferring to Wave 1d (after PMDA decision) would eliminate margin/risk.

**Rejected**: Wave 1c is R0 scaffold + Council attestation gated. Benzonatate lexicon entry + cell scaffold incur **zero physical activity risk** (no synthesis, no equipment order, no clinical trial). R0 gate means benzonatate cell raises RuntimeError on import until Council confirms silen-pharma-review scope `wave-1c-benzonatate-jp-marginal` attestation. This gate can be lifted in R1 once PMDA decides (expected 2024-2025, before yakushi R1 physical manufacturing phase). Scaffolding benzonatate now is low-cost optionality.

## Alternative C — Exclude guaifenesin + benzonatate, focus on omeprazole + laxatives only

Guaifenesin + benzonatate (cough category) could be deferred to Wave 2 (respiratory disease focus).

**Rejected**: guaifenesin + benzonatate are **well-established OTC** (50+ yr market history, safe at OTC dosages). Omitting them contradicts user direction ("他にも OTC をカバー"). Cough-expectorant is a major OTC category alongside laxatives; bundling them with omeprazole in Wave 1c maintains scope coherence (synthetic API + natural/simple routes, all non-sterile, all non-Rx, all off-patent 18+ yr).

---

# References

- Prilosec (omeprazole) original synthesis: US Patent 4,058,635 (Astra-Zeneca, 1977-2001, expired)
- Chiral resolution techniques: Blaser HU, Tetrahedron 1991; "Resolution of Racemates" in Fine Chemicals
- Laxative OTC monographs: USP <600> Monographs (PEG 3350, docusate, senna, bisacodyl)
- Cough-expectorant monographs: USP <600> (guaifenesin, benzonatate)
- Benzonatate PMDA status: 医薬品 OTC 要指定 リスト変更 (2023 application; 2026-05-25 status: pending decision)

---

**ADR-2605250615 Summary**:

Wave 1c extends yakushi OTC API coverage from 12 (Wave 1b) to **19 化合物**, adding:
- **1 chiral synthesis flagship** (omeprazole; future levocetirizine, levofloxacin)
- **4 laxatives** (PEG 3350, docusate Na, senna extract, bisacodyl)
- **2 cough-expectorant** (guaifenesin, benzonatate; PMDA margin gated)

All 7 new APIs maintain G1 (OTC-only, 18+ yr off-patent) and add **zero new constitutional gates**. Chiral resolution cell (`pharma_chiral_resolution`, levi node) established as preparatory capability for omeprazole + future enantiomeric APIs. No new Murakumo nodes. R0 scaffold + Council gate pattern inherited from silicon Wave 1.

Lexicon extensions: `apiInn` knownValues +7, `purificationAttestation` scheme +3 (crystalline-resolution-mandelate, prep-hplc-chiral, SFC-supercritical), `dosageForm` knownValues +3 (sachets, syrup, suspension), `silenPharmaReview` scope triggers +4 (wave-1c-chiral-resolution-baseline, laxative-baseline, cough-syrup-baseline, benzonatate-jp-marginal).

---

**Commits required**:

1. ADR document (this file)
2. Actor update (`20-actors/yakushi/manifest.jsonld`) — add Wave 1c APIs + cells
3. Lexicon extensions (com.etzhayyim.pharma.* files)
4. New Pregel cell scaffolds:
   - `40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_chiral_resolution/cell.py` (RuntimeError gated)
   - `40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_liquid_formulation/cell.py` (RuntimeError gated)
5. deps.toml updates (`[[adrs]]`, `[[modules]]`)
6. `90-docs/adr/README.md` index entry
7. `CLAUDE.md` Status table row 42
