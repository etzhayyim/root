---
id: yakushi-omeprazole-chiral-poc
title: Omeprazole S-enantiomer benchtop PoC protocol (Route A + Route B)
status: reference
doc_type: how-to
topic: yakushi/pharmaceutical/chiral-synthesis
authoritative: false
last_verified: 2026-05-25T00:00:00Z
depends_on:
  - ADR-2605250630
---

# Omeprazole S-enantiomer benchtop PoC protocol

**Scope:** Two parallel synthesis routes for ≤1g omeprazole S-enantiomer separation, targeting ≥99.5% enantiomeric purity (ICH M7 Class 5).
**Phase:** Wave 1c R1 (Council attestation required before execution).

## Route A: Crystalline-Resolution-Mandelate via L-Mandelic Acid Salt

### Objective

Separate racemic omeprazole into S-enantiomer via salt crystallization with L(-)-mandelic acid resolving agent. Expected yield: 65–75% S-enantiomer recovery.

### Materials

| Item | Supplier | Catalog | Grade | Quantity | Storage |
|---|---|---|---|---|---|
| Racemic omeprazole | Sigma-Aldrich | H0891-5G | ≤0.02 EU/mL endotoxin | 0.5 g | RT, desiccant |
| L(-)-Mandelic acid | Sigma-Aldrich | M4256-25G | ≥99% optical purity | 0.3 g | RT, desiccant |
| Ethyl acetate | Fisher Scientific | E195-1 | HPLC grade ≥99.5% | 20 mL | RT, anhydrous bottle |
| Diethyl ether | Fisher Scientific | E138-1 | ACS grade ≥99% | 50 mL | RT, peroxide-free check required |
| Glacial acetic acid | Sigma-Aldrich | 320099-1L | ACS grade ≥99.7% | 5 mL | RT, brown bottle |

**Endotoxin check:** Perform LAL (Limulus Amebocyte Lysate) test on racemic omeprazole stock if unknown supplier (HVAC particle filter risk in warehouse storage).

### Equipment

- 100 mL round-bottom flask
- Magnetic stir bar (8 mm, egg-shaped)
- Reflux condenser + thermometer adapter
- Digital thermometer (-20 to +110°C)
- Vacuum distillation apparatus (optional, for solvent recovery)
- Büchner funnel + filter paper (Whatman GF/A, 0.45 µm pore size)
- Rotary evaporator (R-200, Buchi, or equivalent)
- Optical rotation polarimeter (Bellingham+Stanley ADP220) — **critical for S-enantiomer confirmation**

### Procedure

#### Step 1: Salt formation (30 min at 60–70°C)

1. Dissolve 0.5 g racemic omeprazole in 15 mL hot ethyl acetate (EtOAc) @ 65°C with stirring
2. Add 0.3 g L(-)-mandelic acid (1:1.2 molar ratio, ~1.97 mmol omeprazole : ~2.36 mmol mandelic acid)
3. Maintain stirring @ 60–70°C for 30 min; solution becomes pale yellow
4. **Expected:** Slight cloudiness indicates salt nucleation beginning (do NOT cool yet)

#### Step 2: Cooling crystallization (4 h @ 25°C)

1. Remove from heat; allow to cool to room temperature over 4 h with **slow magnetic stirring** (100 RPM)
2. **Do NOT induce crystallization by seeding** — let salt precipitate naturally
3. After 4 h, white crystals should form on flask walls and suspension visible in supernatant
4. Stop stirring; rest at 25°C for 16 h undisturbed

**Expected crystal morphology:** Needle-like white crystals (L-(–)-omeprazole L-mandelate salt).

#### Step 3: Isolation and washing (30 min)

1. Vacuum filter through Whatman GF/A paper; collect crystals
2. Wash crystals with 5 mL cold EtOAc (pre-chilled @ 4°C) — **do NOT over-wash** (excess washing removes S-enantiomer resolution)
3. Air-dry crystals on filter paper @ RT for 30 min under N₂ stream (optional: accelerate drying)
4. **Weight recorded:** ~0.35–0.40 g (crude S-enantiomer salt)

#### Step 4: Enantiomeric purity assessment (optical rotation)

1. Dissolve ~50 mg dried salt in 5 mL CHCl₃ (chloroform, ≥99% spectroscopic grade)
2. Measure optical rotation [α]₂₀ᴰ (sodium D-line, 589 nm, 20°C, 1 dm cell)
3. **Expected for S-omeprazole:** [α]₂₀ᴰ = +50° to +54° (literature +52° ± 2°)
   - If result is **between +50° and +54°:** enantiomeric purity **≥99%** (acceptable for PoC; proceed to HPLC confirmation)
   - If result is **+45° to +49°:** enantiomeric purity **~97–98%** (acceptable; refine crystallization conditions for future iterations)
   - If result is **<+45°** or **negative:** contamination or racemic mixture (STOP; troubleshoot solvent or temperature control)

#### Step 5: HPLC chiral purity confirmation (orthogonal assay)

(See Route B HPLC method below; same Chiralcel OD-H column.)

**Expected result:** Area% S-enantiomer **≥99.50%** (ICH M7 Class 5 compliance).

### Calculations & Yield

- **Molecular weight omeprazole:** 345.42 g/mol
- **Molecular weight L-mandelic acid:** 152.15 g/mol
- **Salt complex estimate:** ~1.1:1 stoichiometry (omeprazole:mandelic acid complex in solid state)

**Crude yield calculation:**
- Input: 0.5 g racemic = ~1.45 mmol total (0.725 mmol S + 0.725 mmol R)
- Collected: 0.35 g salt ≈ 0.70 mmol × 0.5 = 0.35 mmol S-enantiomer recovered
- **S-enantiomer yield = 0.35/0.725 = 48% of S input** (typical for first crystallization)
- **Overall yield (both enantiomers) = 0.35 g / 0.5 g = 70%** (within 65–75% target)

### Deliverable

`purificationAttestation` Lexicon record (MST record):
```json
{
  "upstreamApiSynthesisUri": "at://...",
  "scheme": "crystalline-resolution-mandelate",
  "target_enantiomer": "S",
  "resolving_agent": "L-mandelic acid",
  "operatorDid": "did:...",
  "witnessDid": "did:...",
  "enantiomeric_purity_bp": 9950,
  "recovery_yield_bp": 7000,
  "outcome": "ok"
}
```

---

## Route B: Prep-HPLC-Chiral via Chiralcel OD-H Column

### Objective

Upscale Route A output or perform direct separation of 1g racemic omeprazole via preparative HPLC, targeting ≥99.5% enantiomeric purity and 70–95% recovery.

### Equipment

- Agilent 1260 Infinity II (or equivalent prep-HPLC system)
- Pump module: binary solvent delivery, ≥10 mL/min capacity
- Injection valve: 500 µL loop or larger
- Detector: UV @ 280 nm (omeprazole λmax)
- Fraction collector: automated, triggered by peak apex detection
- Column: Chiralcel OD-H, 250 mm × 10 mm I.D., 5 µm particle size (Daicel)
- Column oven: 25°C ± 0.5°C (critical for baseline stability)

**Alternative column (orthogonal assay):** Chiralpak IC-3, 250 mm × 10 mm I.D., 3 µm (for SFC cross-check at R1.5).

### Mobile Phase Composition

**Standard:**
- 80% n-hexane (HPLC grade, ≥99% purity)
- 20% isopropanol (IPA, HPLC grade, ≥99.9% purity)
- Optional: 1% trifluoroacetic acid (TFA, ≥99%, for baseline separation enhancement)

**Mixing note:** Prepare fresh daily; hexane is volatile — store with dry ice or under N₂ atmosphere.

### HPLC Method Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Flow rate | 4.5 mL/min | Baseline resolution R_s ≥2.5 without TFA; 4.0–5.0 mL/min range acceptable |
| Temperature | 25°C | Chiralpak selectivity optimal @ 25°C; avoid >30°C (resolution loss) |
| Injection volume | 50 µL | 1 mg/mL omeprazole in hexane/IPA = 50 µg per injection; scale to 100–200 µL for prep scale |
| Detection | UV 280 nm | Omeprazole λmax 280 nm (ε ~5,000 M⁻¹cm⁻¹ in hexane/IPA); bandwidth 4 nm |
| Run time | 35 min | R-enantiomer retention ~25 min, S-enantiomer ~18 min; 10-min post-run purge |
| Baseline separation goal | R_s ≥2.5 | 50% valley rule: valley ≥50% of peak height indicates baseline resolution |

### Analytic HPLC (Diagnostic run, 1 mg/mL racemic)

**Purpose:** Confirm separation quality before prep-scale injection.

1. Prepare 1 mg/mL racemic omeprazole in mobile phase (hexane/IPA 80:20)
2. Inject 50 µL; run @ 4.5 mL/min, 25°C
3. **Expected retention times:**
   - S-enantiomer: ~18 min
   - R-enantiomer: ~25 min
   - Resolution R_s = (t_R − t_S) / (0.5 × (w_R + w_S)) — **target ≥2.5**
4. **Record** detector trace (PDF export) and integrate peak areas
   - If area% S:R **>50:50,** proceed to Route A (crystallization is faster/cheaper)
   - If area% S:R **<50:50,** proceed to Route B prep (R-enantiomer collection deferred to Wave 2)

### Preparative HPLC (1g feed scale)

#### Pre-run checklist

- [ ] Column oven @ 25°C, stabilized ≥30 min
- [ ] Mobile phase degassed (helium bubble ≥5 min)
- [ ] Pump pressure baseline <50 bar (hexane/IPA 80:20 @ 4.5 mL/min)
- [ ] UV baseline flat (±0.05 mAU over 5 min idle)
- [ ] Fraction collector vials labeled (S: #1–15, R: #16–30, waste: #31–40)
- [ ] 1g racemic omeprazole dissolved in 20 mL mobile phase; filtered through 0.45 µm PTFE syringe filter

#### Injection & collection

1. **Inject 500–1000 µL** (≤10 mg per injection to avoid overloading); repeat until 1g total loaded (100 injections × 10 mg, or 50 injections × 20 mg)
2. **S-enantiomer fraction window:** Inject → peak apex @ ~18 min → collect for 4 min (18 ± 2 min = 16–20 min window)
3. **R-enantiomer fraction window:** ~25 ± 2 min (23–27 min, deferred or discarded per G1 OTC-only scope)
4. **Stop injection** when total column feed = 1g; flush column with 20 mL mobile phase @ 4.5 mL/min post-final injection

#### Fraction pooling & recovery

1. **Pool S-enantiomer fractions** (vials #1–15, typically 60–75 mL combined liquid)
2. **Evaporate pooled fractions** via rotary evaporator @ 40°C, 50 mbar; final dryness under vacuum
3. **Weigh collected S-enantiomer:** Expected 0.70–0.95 g (70–95% recovery from 1g feed)
4. **Dissolve in CHCl₃** (5 mL) → measure **optical rotation [α]₂₀ᴰ**
   - Expected: +50° to +54° (confirms S-identity)
5. **Submit 10 mg** to analytical HPLC (same method as diagnostic run)
   - Expected: Area% S ≥99.50% (ICH M7 Class 5)

### Alternative: SFC-Supercritical Carbon Dioxide (Orthogonal Method)

**At R1, use as confirmatory only; not primary route.**

- Column: Chiralpak IC-3, 250 mm × 4.6 mm I.D., 3 µm
- Mobile phase: 95% CO₂ + 5% EtOH (with 0.1% formic acid)
- Flow rate: 3.0 mL/min @ 40°C, 100 bar
- Expected runtime: 15 min; S-enantiomer ~7 min, R-enantiomer ~10 min
- Benefit: Faster analysis (prep-scale confirmation in 15 min vs 35 min HPLC)
- **Defer to R1.5 or R2** for prep-SFC scale-up (equipment: FluidAI SFE-2 or equivalent)

### Deliverable

Same `purificationAttestation` record as Route A:
```json
{
  "upstreamApiSynthesisUri": "at://...",
  "scheme": "prep-hplc-chiral",
  "target_enantiomer": "S",
  "prep_hplc_column": "Chiralcel OD-H",
  "operatorDid": "did:...",
  "witnessDid": "did:...",
  "enantiomeric_purity_bp": 9950,
  "recovery_yield_bp": 8500,
  "outcome": "ok"
}
```

---

## Route Selection Decision Tree

**Use Route A if:**
- Crystalline resolution literature data available for similar APIs (yes → omeprazole proven 1973–2010 Merck routes)
- Budget/time constraint: Route A faster (2–3 days vs 7–10 days for Route B full cycle)
- Equipment availability: only basic glassware + polarimeter (yes)

**Use Route B if:**
- Route A yield <65% (troubleshoot salt kinetics first)
- Need upscale to ≥100g (Route B column can run sequential 100 mg injections; Route A batch ≤1g per crystallization cycle)
- Preparative HPLC already available in facility

**Combined approach (recommended for PoC):**
1. Run Route A analytic salt trial (0.5g); measure optical rotation
2. If [α]₂₀ᴰ **≥+50°** → declare Route A success; submit one sample to Route B analytical HPLC for ICH M7 purity confirmation
3. If [α]₂₀ᴰ **<+45°** → run Route B prep on 1g feed; use Route B S-enantiomer for QC battery

---

## QC Battery (Both Routes Converge)

**Minimum assay set (PoC phase):**

1. **Chiral HPLC:** Chiralcel OD-H, 280 nm, enantiomeric purity (Area% S ≥99.50%)
2. **Optical rotation:** [α]₂₀ᴰ in CHCl₃, +50° to +54° (S-omeprazole confirmation)
3. **HPLC purity:** RP-HPLC (RP-18, 50 mM phosphate pH 3 : acetonitrile 60:40), UV 280 nm, total purity ≥98% (sum of isomers)
4. **Melting point:** Omeprazole S-enantiomer literature mp = 137–139°C (DSC or capillary); ±2°C tolerance
5. **NMR (¹H + ¹³C):** CDCl₃ solvent; chemical shift agreement vs reference (optional for R1 PoC; mandatory R2)
6. **IR:** KBr pellet; characteristic peaks (C=O 1713 cm⁻¹, aromatic C=C 1495 cm⁻¹); compare to omeprazole USP reference
7. **Mass spectrometry:** ESI-MS or MALDI; [M+H]⁺ m/z = 346.1 (omeprazole MW = 345.4)
8. **Solubility check:** Room-temperature acetonitrile solution @ 50 mg/mL; clear, colorless (rules out oxidation/degradation)
9. **Endotoxin (LAL):** USP <85> gel clot method; <0.05 EU/mL (for potential parenteral application in R2+)
10. **Water content (Karl Fischer):** ≤2% w/w (hygroscopic salt)

**Typical turnaround:** HPLC (1 day) + optical rotation (same day) + remaining assays (3–5 days for full QC battery).

---

## Success Criteria (PoC Gate)

All of the following must be met:

1. ✅ **Enantiomeric purity:** Area% S-enantiomer ≥99.50% (ICH M7 Class 5 allowable <0.5% R)
2. ✅ **Optical rotation:** [α]₂₀ᴰ in range +50° to +54° (±3° from literature +52°)
3. ✅ **Recovery yield:** ≥65% for Route A OR ≥70% for Route B (from stated starting material)
4. ✅ **HPLC total purity:** ≥98% sum of omeprazole enantiomers (related substances <0.5% each)
5. ✅ **Witness attestation:** N ≥2 (operator DID + QP-equivalent DID or independent sensor DID) sign `purificationAttestation` record

**Pass = proceed to R2 pilot (≤100g synthesis, Annex 1 facility).**

---

## References

- Merck 1980s omeprazole synthesis (Lindberg et al., *Acta Pharmaceutica Suecica*, patent routes de-escalated 1990s)
- Daicel Chiral Technologies Chiralcel OD-H product sheet (resolution data omeprazole enantiomers)
- ICH M7 Guideline: Assessment and Control of DNA Reactive (Genotoxic) Impurities
- Polarimeter SOP: Optical rotation measurement (Bellingham+Stanley ADP220 user manual)
- USP <61> Microbiological Examination of Nonsterile Products
- Sigma-Aldrich safety data sheet: omeprazole (H0891), L-mandelic acid (M4256), ethyl acetate (E195)

---

**Document owner:** yakushi QA lead
**Executed upon:** Council Lv6+ attestation gate unlock (ADR-2605250630)
**Last reviewed:** 2026-05-25
