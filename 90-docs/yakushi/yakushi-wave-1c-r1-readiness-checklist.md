---
id: yakushi-wave-1c-r1-readiness
title: yakushi Wave 1c R1 — Pre-manufacturing readiness checklist
status: reference
doc_type: how-to
topic: yakushi/pharmaceutical/manufacturing
authoritative: false
last_verified: 2026-05-25T00:00:00Z
depends_on:
  - ADR-2605250630
  - ADR-2605250645
---

# yakushi Wave 1c R1 — Pre-manufacturing readiness checklist

**Phase:** R1 (benchtop PoC scale, ≤1g omeprazole per synthesis run)
**Scope:** Gate unlock verification → equipment readiness → material sourcing → protocol review → witness coordination → first synthesis authorization.

## Section A: Gate Unlock Verification (T-7 days before synthesis)

- [ ] **A1.** Confirm Council Lv6+ ≥3 vote approved ADR-2605250630
  - Council Chair signed-off: _____ (DID / name)
  - Vote date: _____
  - Approval margin: ___/5

- [ ] **A2.** Verify COUNCIL_ATTESTATION_TX_HASH set in cell.py (non-None)
  - `pharma_chiral_resolution/cell.py` line verified: _____
  - TxHash: 0x_____... (first 16 chars)
  - On-chain confirmation: ✅ (check etherscan / block explorer)

- [ ] **A3.** Verify SILEN_PHARMA_BASELINE_REVIEW_CID set in cell.py (non-None)
  - `pharma_chiral_resolution/cell.py` line verified: _____
  - IPFS CID: bafy_____... (first 16 chars)
  - IPFS resolution test: ✅ (curl ipfs.io/ipfs/bafy...)

- [ ] **A4.** Import test passed (no RuntimeError on cell module load)
  - Command: `python -c "from kotodama.cells.pharma_chiral_resolution import cell"`
  - Result: ✅ No error
  - Timestamp: _____

- [ ] **A5.** CI validation passed (GitHub Actions / lefthook)
  - e7m-verify: ✅
  - TxHash format check: ✅
  - CID format check: ✅
  - On-chain TxHash existence: ✅
  - IPFS CID resolution: ✅

---

## Section B: Equipment Readiness (T-14 days before synthesis)

### Route A: Crystalline Resolution (L-Mandelic Acid Salt)

- [ ] **B1.** Glassware inventory & condition
  - [ ] 100 mL round-bottom flask (clean, no residue)
  - [ ] 8 mm egg-shaped magnetic stir bar (magnetic test: ✅)
  - [ ] Reflux condenser + thermometer adapter (water flow test: ✅)
  - [ ] Digital thermometer -20 to +110°C (calibration check: _____ °C @ known reference)
  - [ ] Büchner funnel + vacuum flask (vacuum test: holds >0.8 bar for 30 sec)
  - [ ] Whatman GF/A filter paper stock (opened <6 months ago)

- [ ] **B2.** Hot plate / heating source
  - Equipment model: _____
  - Max temp setting: _____ °C
  - Stability test @ 65°C for 10 min: ±2°C margin ✅

- [ ] **B3.** Vacuum pump (if using rotary evaporator)
  - Model: _____
  - Pressure achieved: _____ mbar (target <10 mbar)
  - Oil check: ✅ (not discolored, not emulsified)

### Route B: Prep-HPLC Chiral

- [ ] **B4.** Agilent 1260 Infinity II (or equivalent) status
  - System model: _____
  - Last maintenance: _____ (date)
  - Pump baseline pressure @ 4.5 mL/min with mobile phase: _____ bar (target <50 bar)
  - Injector leakage test (idle 5 min): _____ µL leak (target <5 µL)
  - UV detector lamp hours: _____ (target <10k hours; replacement due >15k)
  - UV baseline stability (5 min idle, 280 nm): ±_____ mAU (target ±0.05 mAU)

- [ ] **B5.** Chiralcel OD-H column (250 mm × 10 mm I.D., 5 µm)
  - Column S/N: _____
  - Installation date: _____ (if new, <1 month; if used, <3 months intensive use)
  - Back pressure @ 4.5 mL/min hexane/IPA 80:20: _____ bar (target 120–150 bar)
  - Peak symmetry test (prior analytical run): Tailing factor _____ (target 0.8–1.2)
  - Column conditioning: _____ (last run date; pre-conditioned ≥4 h hexane/IPA flush if idle >1 week)

- [ ] **B6.** Solvent degassing & storage
  - [ ] Helium bubble degasser functional (bubble rate ≥10 mL/min)
  - [ ] Mobile phase prepared fresh <24 h ago (hexane + IPA 80:20)
  - [ ] Mobile phase storage: closed, inert atmosphere (N₂ or dry ice overlay)
  - [ ] Injection solvent (hexane/IPA 80:20): filtered 0.45 µm PTFE

- [ ] **B7.** Fraction collector (if using prep-HPLC)
  - Model: _____
  - Peak detection sensitivity: _____ mV (range 5–50 mV recommended)
  - Vial compatibility: 2 mL crimp-cap vials (pre-labeled, pre-weighed for recovery)
  - Dry run test (no sample): collection delay <5 sec ✅

### Both Routes

- [ ] **B8.** Polarimeter (optical rotation)
  - Instrument: _____ (e.g., Bellingham+Stanley ADP220)
  - Last calibration date: _____ (yearly recommended)
  - Calibration standard (sucrose / tartaric acid) test: _____ ± 0.5° (literature value _____)
  - Sample cell (1 dm): clean, no scratches, glass condition ✅

- [ ] **B9.** Safety equipment in synthesis area
  - [ ] Fire extinguisher (ABC type, pressure gauge in green zone)
  - [ ] Ethyl acetate spill kit (absorbent, waste container)
  - [ ] First aid kit (eye wash, burn ointment, bandages)
  - [ ] Lab coat + nitrile gloves available
  - [ ] No ignition sources within 3 m of synthesis bench (no hot plates, Bunsen burners)

---

## Section C: Material Sourcing & Verification (T-10 days before synthesis)

- [ ] **C1.** Racemic omeprazole (Sigma-Aldrich H0891-5G)
  - Lot #: _____
  - Purchase date: _____ (use <1 year from date of receipt)
  - Storage: RT, desiccant packet, sealed container
  - Visual inspection: white/off-white powder, no discoloration ✅
  - Endotoxin specification on cert: ≤0.02 EU/mL ✅ (if available; LAL test if unknown)

- [ ] **C2.** L(-)-Mandelic acid (Sigma-Aldrich M4256-25G)
  - Lot #: _____
  - Optical purity on cert: ≥99% L-enantiomer ✅
  - Storage: RT, desiccant, sealed
  - Visual inspection: white crystals, no discoloration ✅

- [ ] **C3.** Ethyl acetate (Fisher Scientific E195-1, HPLC grade)
  - Lot #: _____
  - Purity spec: ≥99.5% ✅
  - Water content (Karl Fischer) on cert: <0.05% ✅ (if available)
  - Storage: sealed, original bottle (opened <6 months ago)
  - Visual: clear, colorless, no suspended solids ✅

- [ ] **C4.** Diethyl ether (ACS grade, peroxide-free)
  - Peroxide test strip result: _____ ppm (target 0 ppm; replace if >25 ppm)
  - Storage: sealed, original can, <1 year from opening date

- [ ] **C5.** Chiralcel OD-H prep-HPLC mobile phase
  - n-Hexane HPLC grade (≥99%): opened <3 months
  - Isopropanol HPLC grade (≥99.9%): opened <3 months
  - TFA (≥99%, if using): opened <1 year, sealed
  - Mobile phase prepared fresh (T-2 hours before first injection)

---

## Section D: Protocol & Procedure Review (T-7 days before synthesis)

- [ ] **D1.** Omeprazole benchtop PoC protocol document signed-off
  - Document version: omeprazole-chiral-benchtop-poc-protocol.md (dated 2026-05-25)
  - Operator printed & annotated: _____ (name, date)
  - QA lead reviewed for clarity: _____ (name, date)
  - Any deviations from protocol approved by QP-equivalent: ☐ Yes ☐ No (if Yes, document reason: _______)

- [ ] **D2.** Route A procedure dry-run (without sample)
  - Glassware setup simulated ✅
  - Heating profile rehearsed @ 65°C target ✅
  - Cooling timeline understood (4 h cool-down) ✅
  - Filtration procedure practiced (vacuum applied, not over-applied) ✅

- [ ] **D3.** Route B procedure dry-run (without sample)
  - HPLC system primed with mobile phase (10 min flush, 4.5 mL/min) ✅
  - Injector tested (water injection, peak retention time recorded) ✅
  - Fraction collector settings configured for 4-min windows ✅
  - Rotary evaporator tested (vacuum, temperature control @ 40°C) ✅

- [ ] **D4.** Waste disposal plan documented
  - Ethyl acetate waste container labeled, capacity _____ L, disposal vendor: _____ (frequency: _____)
  - Chloroform (for optical rotation) waste container: ☐ Available
  - Spent solvent HAZMAT sign-off: _____ (operator name / facility contact)

---

## Section E: Witness Coordination & Attestation Setup (T-5 days before synthesis)

- [ ] **E1.** Primary operator DID confirmed
  - Operator name: _____
  - DID: did:web:etzhayyim.com:yakushi:_____
  - Passkey / hardware token access verified: ✅ (sign dummy record test)

- [ ] **E2.** QP-equivalent (Qualified Person or sensor witness) DID confirmed
  - QP-equivalent name / sensor type: _____
  - DID: did:web:etzhayyim.com:yakushi:_____
  - Passkey / automation signature capability verified: ✅

- [ ] **E3.** MST listener subscription confirmed
  - Murakumo levi node listening for `purificationAttestation` events: ✅
  - Cell subscription status (`pharma_chiral_resolution` on_event): ✅ SUBSCRIBED (check logs)
  - Fallback witness escalation (N=1 auto-escalates to Council): ✅ Understood

- [ ] **E4.** Attestation record template prepared (JSON draft)
  - Template file: purificationAttestation-omeprazole-Route-A.json (or Route B variant)
  - Required fields populated: apiInn, scheme, target_enantiomer, operatorDid, witnessDid, _____ (fill as applicable)
  - Optional fields (notes, timestamps): _____

- [ ] **E5.** Post-synthesis data capture plan
  - Optical rotation result → JSON field: optical_rotation_bp (manually entered after measurement)
  - HPLC enantiomeric purity result → JSON field: enantiomeric_purity_bp (HPLC report attached or linked)
  - Recovery yield calculation → JSON field: recovery_yield_bp (calculated from weights)
  - QC outcome: pass/rework-required/scrapped (determination rule: _____)

---

## Section F: Safety & Compliance Clearance (T-3 days before synthesis)

- [ ] **F1.** Charter Rider §2 compliance briefing completed
  - Operator reviewed §2(a): Transparent Force (omeprazole synthesis is open-sourced, routes from Fisons 1965 literature) ✅
  - Operator reviewed §2(c): No resale to advertisers / insurers (QC data is internal MST record only) ✅
  - Operator reviewed §2(h): Wellbecoming enforcement (labeling warning for long-term PPI use hypermagnesemia risk) ✅
  - Operator signed off: _____ (name, date)

- [ ] **F2.** G1 scope verification (OTC-only, off-patent perpetually in all-3 jurisdictions)
  - Omeprazole off-patent status: PMDA ✅ (expired ____), FDA ✅ (expired ____), EMA ✅ (expired ____)
  - No patent fence risk: ✅ (no active IPs covering omeprazole S-enantiomer separation via mandelic acid or prep-HPLC routes)

- [ ] **F3.** G7 CWC precursor check (no OPCW Schedule 3 reagents)
  - Route A (crystalline-resolution): only ethyl acetate, L-mandelic acid, acetic acid — ✅ No OPCW Schedule 3 items
  - Route B (prep-HPLC): only hexane, IPA, TFA — ✅ No OPCW Schedule 3 items
  - Safety review: ✅ Omeprazole synthesis omits acetic anhydride (contrast Wave 1b analgesics)

- [ ] **F4.** Facility documentation review
  - Benchtop synthesis performed in authorized lab space: ✅ (location: _____; facility contact: _____)
  - Chemical inventory log updated: ✅ (supervisor name: _____)
  - Environmental health & safety (EHS) contact on file: _____ (phone: _____)

- [ ] **F5.** Operator training sign-off
  - Operator has completed yakushi Wave 1c R1 training module (video, 15 min): ✅
  - Operator passed post-training quiz (≥80% score): _____ / 100
  - Operator name / signature: _____ (date: _____)

---

## Section G: Go/No-Go Decision (T-1 day before synthesis)

- [ ] **G1.** All equipment tests PASSED (Sections B1–B9)
  - Glassware ✅ | Heating ✅ | Vacuum ✅ | HPLC ✅ | Column ✅ | Polarimeter ✅ | Safety ✅

- [ ] **G2.** All materials verified (Sections C1–C5)
  - Racemic omeprazole ✅ | L-mandelic acid ✅ | Ethyl acetate ✅ | Solvents ✅

- [ ] **G3.** All protocols reviewed & dry-run (Sections D1–D4)
  - Route A procedure ✅ | Route B procedure ✅ | Waste plan ✅

- [ ] **G4.** Witness coordination confirmed (Sections E1–E5)
  - Operator DID ✅ | QP-equivalent DID ✅ | MST listener ✅ | Attestation template ✅

- [ ] **G5.** Safety & compliance cleared (Sections F1–F5)
  - Charter Rider ✅ | G1 scope ✅ | G7 precursor ✅ | Facility ✅ | Training ✅

**Final Authorization:**

- **QA Lead signature:** _____ (name, date, time) — **authorization to proceed with Route A and/or Route B**
- **Operator acknowledgment:** _____ (name, date, time) — **understood protocol, safety, attestation process**
- **Council liaison (if on-site):** _____ (name, date, time) — **optional presence for inaugural synthesis observation**

---

## Section H: Post-Synthesis Sign-Off (T+24 hours after synthesis completion)

- [ ] **H1.** Enantiomeric purity achieved: _____ bp (target ≥9950, i.e., ≥99.50%)
  - Route used: ☐ A (crystalline-resolution) ☐ B (prep-HPLC) ☐ Both parallel
  - Outcome: ☐ PASS (≥99.50%) ☐ REWORK-REQUIRED (97–99%) ☐ SCRAPPED (<97%)

- [ ] **H2.** Optical rotation confirmed: _____ ° [α]₂₀ᴰ (target +50° to +54°)
  - Measurement date/time: _____
  - Polarimeter condition: ✅

- [ ] **H3.** Recovery yield achieved: _____ bp (target Route A ≥6500 [65%], Route B ≥7000 [70%])
  - Mass isolated: _____ g
  - Calculation verified: _____ (name)

- [ ] **H4.** Attestation record published to MST
  - `purificationAttestation` record CID: bafy_____
  - Timestamp: _____
  - Witness signatures (N≥2): ✅ (operator + QP-equivalent)

- [ ] **H5.** QC battery initiated (full 10-point assay)
  - ☐ Chiral HPLC scheduled (lab name, date)
  - ☐ RP-HPLC scheduled
  - ☐ Melting point scheduled
  - ☐ NMR scheduled
  - ☐ IR scheduled
  - ☐ MS scheduled
  - ☐ Solubility test scheduled
  - ☐ LAL test scheduled
  - ☐ Karl Fischer test scheduled
  - Expected completion: _____ (date, ±5 days)

- [ ] **H6.** Synthesis report filed
  - Report date: _____
  - Route(s) used & justification: _____
  - Any deviations from protocol: ☐ Yes ☐ No (if Yes, explain: _______)
  - Operator lessons learned: _____
  - QA lead approval: _____ (signature, date)

---

## Notes

- **Printed checklist:** Print this document; mark completed items with pen/pencil (signature-ready for audits)
- **Digital record:** Maintain parallel digital copy in yakushi QA shared drive with timestamps
- **Escalation:** If ANY item is ❌, escalate to QA lead immediately (do not proceed)
- **Template customization:** Facility-specific details (contact names, phone numbers, disposal vendors) should be pre-filled before T-7 days

---

**Document owner:** yakushi QA lead
**Last reviewed:** 2026-05-25
**Readiness approval authority:** Council Lv6+ (via ADR-2605250630 attestation)
**Synthesis authority:** QA lead (upon completion of all 7 checklist sections A–G)
