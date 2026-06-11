# `com.etzhayyim.creative.*` — Lexicon Namespace

**ADR**: ADR-2605265000 (R0 scaffold; creative-pd substrate for baien training)
**Bucket family**: `creative-pd/{films,video,music,audio}/` IPFS-pinned via DataLad
**Parent framework**: ADR-2605262400 (public-data ingestion)

## Records (7)

| Lexicon | Purpose |
|---|---|
| `publicDomainStatusAttestation` | Core per-work PD status × 7-jurisdiction matrix (G1+G2+G3 STRUCTURAL); music modality requires composition + recording dual-attestation |
| `tierBNhkLicenseAttestation` | NHK Creative Library (CC-BY 2.1 JP) per-clip tracker; G13 STRUCTURAL fleet-internal carve-out per ADR-2605262100 R1.4 precedent (NOT externally published) |
| `tierBCcByAttestation` | Wikimedia Commons + Mutopia CC-BY 3.0/4.0 + CC-BY-SA 3.0/4.0 attribution-chain tracker; share-alike propagation flag for downstream artifacts |
| `orphanWorkResearchAttestation` | R3+ orphan-works research-only carve-out (Council Lv6+ ≥3; diligent-search per US Copyright Office Best Practices 2015; work ≥95 yr old; researchOnlyNotTrainingAttested const true STRUCTURAL) |
| `wellbecomingFramingScan` | G7 Charter Rider §2(d) per-work review (R1 manual; R2+ rule-encoded auto-flag → Council Lv6+ ≥3 queue; verdict ∈ {admit, admit-with-context, exclude}) |
| `creativeMemorizationEvalReport` | G6 3-pronged memorization-guardrail eval at every baien-distill commit_node (verbatim regurgitation ≤1% + DP-SGD ε≤8.0 R3+ + Chromaprint distance ≥0.2 for audio); G10 evidence emission to `90-docs/baien/creative-memorization-eval-{R-step}.jsonl` |
| `jurisdictionConflictResolution` | URAA §104A + cross-juris conflicts (CA CUSMA / JP TPP / US pre-1978); pessimistic REJECT default + futureEligibilityYear for re-evaluation queue |

## Structural enforcement summary

Per the chigiri / toritate / iyashi / mizuho / kazaori / ossekai
pattern — gates enforced at schema layer via `const` fields and
`minLength` constraints so malformed records reject at the projection
layer.

| Gate | Lexicon-layer structural enforcement |
|---|---|
| G1 per-work PD attestation | publicDomainStatusAttestation `pdStatusByJurisdiction minLength 7` + `pessimisticThresholdYearsPostMortem minimum 70` |
| G2 multi-juris pessimistic | publicDomainStatusAttestation per-jurisdiction `status` enum knownValues exclude 'copyright-active' / 'uraa-restored' / 'uncertain-rejected' / 'conflict-rejected' from admission |
| G3 music dual-copyright | publicDomainStatusAttestation `compositionPdStatus` AND `recordingPdStatus` required for music-recording modality; `performerRightPdStatus` for audio/video with performers |
| G6 memorization guardrail | creativeMemorizationEvalReport `verbatimRegurgitationPass`/`chromaprintPass`/`dpSgdPass` (R3+)/`clipFeaturePass` const-check; `overallVerdict` enum admits only 'pass' at commit_node |
| G7 Wellbecoming framing | wellbecomingFramingScan `verdict` enum {admit, admit-with-context, exclude}; admit-with-context requires `councilLv6PlusAttestations minLength 3` |
| G8 attribution chain | publicDomainStatusAttestation `attributionChainCid` required (every work); tierBCcByAttestation + tierBNhkLicenseAttestation `attributionText` required |
| G13 fleet-internal NHK | tierBNhkLicenseAttestation `fleetInternalCarveOutAttested: const true` + `downstreamArtifactNotExternallyPublishedAttested: const true` + `nonCommercialAffirmation: const true` |
| R3+ orphan research-only | orphanWorkResearchAttestation `researchOnlyNotTrainingAttested: const true` + `councilLv6PlusAttestations minLength 3` + `workMinAgeYears minimum 95` + `workEstimatedYear maximum 1931` (2026 baseline) |

## Cross-actor citations

- **e7m-dataset (ADR-2605262400)** — parent framework + PASSIVE-ONLY discipline + datasetPin pattern
- **baien-moemoekyun (ADR-2605262100)** — `commit_node` enforces G6 memorization-eval; G13 fleet-internal NC carve-out precedent for NHK Tier-B
- **manabi (ADR-2605261045)** — arts-literacy + civic-literacy primary-source citations (Tier-A only; no Tier-B NHK in public-facing curriculum)
- **ossekai (ADR-2605264000)** — Annual Public-Domain-Day Jan 1 feed-post advisory
- **chigiri (ADR-2605262700)** — multi-juris PD verification consultation at R2+; orphan-works procedural attestation
- **kotoba (ADR-2605262130)** — storage substrate; kotoba-kqe arrangements

## 4 modalities × bucket layout

```
e7m-dataset:creative-pd/
├── films/<source>/<work-id>/
├── video/<source>/<work-id>/
├── music/
│   ├── compositions/<source>/<work-id>/  (Mutopia, IMSLP symbolic — G3 sidesteps recording layer)
│   └── recordings/<source>/<work-id>/    (audio — dual-attestation: composition + recording)
└── audio/
    ├── speech/<source>/<work-id>/         (LibriVox audiobooks)
    ├── folklife/<source>/<work-id>/        (oral history, field recordings)
    └── radio-pd/<source>/<work-id>/        (pre-1972 US radio PD subset)
```

## Related files

- `/90-docs/adr/2605265000-creative-pd-substrate-for-baien-training-r0.md` — Master ADR
- `/70-tools/baien-moemoekyun-train/recipes/creative/` — Recipe templates (R1 writes)
- `/70-tools/baien-moemoekyun-train/scripts/assemble-creative-pd-corpus.py` — Cold-path corpus assembler (R1 writes)
- `/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/creative/` — Sensor scaffold (R1 writes)
- `/CHARTER-RIDER.md` §2(d) + §2(e) — G5 + G7 sources
