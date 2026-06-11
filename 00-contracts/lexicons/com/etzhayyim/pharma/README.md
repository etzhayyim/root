# com.etzhayyim.pharma.* — yakushi pharmaceutical R&D lexicons

Per yakushi master charter [ADR-2605250500](../../../../../90-docs/adr/2605250500-yakushi-pharmaceutical-rd-charter.md).

8 lexicons covering the full pharmaceutical R&D substrate from raw-material intake
through patient adverse-event reporting:

| Lexicon | Purpose | Encryption |
|---|---|---|
| `rawMaterialAttestation` | API precursor + excipient intake (G7 CWC + safety) | public; CWC schedule / safety class visible |
| `apiSynthesisAttestation` | per-step API synthesis attestation | public |
| `purificationAttestation` | API purification (recryst + activated charcoal + (chlorpheniramine) prep-HPLC) | public |
| `qcAttestation` | per-lot QC suite (HPLC / IR / NMR / KF / ICP-MS / GC / PGI / endotoxin / microbial) | public |
| `fillFinishAttestation` | aseptic processing + BFS fill-finish (Annex 1 2023) | public |
| `lotAttestation` | final per-lot release with full upstream attestation chain CIDs | public |
| `silenPharmaReview` | Council Lv6+ ≥ 3 multisig review verdict (G3) | public |
| `adverseEventReport` | patient AE intake (G5 + G10) | XChaCha20-Poly1305 envelope for patient identity; aggregated narrative public |

All lexicons enforce witness invariant N ≥ 2 (G9) and substrate boundary
(`@etzhayyim/sdk` only, per G14).

## Wave 1b extension (ADR-2605250600)

`apiInn` knownValues extended from 3 → 12 (Wave 1 triplet + Wave 1b 9 additions:
acetaminophen / aspirin / ibuprofen / diphenhydramine-hydrochloride /
cetirizine-dihydrochloride / loratadine / famotidine / clotrimazole / diclofenac-sodium).

`fillFinishAttestation` + `lotAttestation` added `dosageForm` field with 10 knownValues
(sterile eye drop multi-dose + unit-dose, tablet uncoated/film-coated/enteric,
capsule, topical cream/gel/ointment/spray).

`qcAttestation` added non-sterile dosage form fields: `dissolutionPct30min` /
`dissolutionPct60min` / `contentUniformityRsdPct` / `friabilityPctMassLoss` /
`disintegrationTimeMin` (tablet — USP <701>/<711>/<905>/<1216>); `viscosityCp` /
`pHValue` (topical).

`silenPharmaReview` `scope` knownValues extended with `wave-1b-*` triggers
(api-addition, dosage-form-tablet-attestation, dosage-form-topical-attestation,
tablet-press-equipment-qualification, topical-mixer-equipment-qualification,
non-sterile-microbial-limit-baseline, wave-1b-launch-{pmda,fda,ema}).

Sterile dosage form requirements (sterileFilter / CCIT / sterility / endotoxin /
bfsRunParams) are now optional in `fillFinishAttestation` — required by dosageForm
business rule rather than schema-level required[]. Non-sterile dosage forms
(tablet / topical) use unitsProduced + dosage-specific equipment DID +
microbial limit only.
