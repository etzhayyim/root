# com.etzhayyim.manabi.* — Lexicons

Per ADR-2605261045. R0 stubs; full schemas R1+.

**PRIVACY INVARIANT G6**: `learningSessionAttestation` enforces `additionalProperties: false` + `learnerAgeBucket` discriminator. Under-18 sessions emit only aggregate fields (sessionDuration, moduleId, completionFraction); per-learner detail forbidden.

**ANTI-CREDENTIALISM INVARIANT G7**: manabi issues no degrees / transcripts / GPA. Only `skillAttestation` (subject-specific replayable demonstration) used by L5+ adherent productive contribution.

| Lexicon | Purpose |
|---|---|
| `curriculumAttestation` | Module declaration (open-source + Council Lv6+ ≥3 charter alignment + Charter Rider scan) |
| `learningSessionAttestation` | Per-session aggregate (minor) or encrypted-detail-optional (adult) |
| `charterUnderstandingAttestation` | Adherent SBT informed-consent baseline (self-paced demonstration, not test) |
| `silenEducationReview` | Council attestation scope |
| `certPrepSession` | cert_prep sub-cell per-session (CISA/CISSP knowledge-domain study; G15+G16 negative-space enforcement) — ADR-2605264400 |
| `personalMaterialImport` | cert_prep sub-cell user-imported study material (Tier-C `internalOnly:true` per ADR-2605262400) — ADR-2605264400 |
| `domainMasteryAttestation` | cert_prep subject-specific skillAttestation-family; `credentialClaimedAttested:false` structural — ADR-2605264400 |

## Related ADRs

- ADR-2605261045 — manabi master ADR
- ADR-2605261000 — Liberation Ladder L4 + L5 gates (charterUnderstandingAttestation = SBT issuance prerequisite §2.1)
- ADR-2605181200 — Rotating pseudonym DID (minor learner)
- ADR-2605192200 — Charter Rider (pedagogy + license)
- ADR-2605264400 — manabi cert_prep sub-cell (IT audit / infosec knowledge-domain study)
