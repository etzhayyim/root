# com.etzhayyim.kokoro.* — kokoro (心) Lexicons

**Owner actor**: `did:web:kokoro.etzhayyim.com` ([`com-etzhayyim-kokoro`](https://github.com/etzhayyim/com-etzhayyim-kokoro))
**ADR**: ADR-2605263700 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.

## 5 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `peerSupportCircleAttestation` | peer_support_circle | G4+G9+G10+G11 structural; encryptedPayloadCid REQUIRED + optInOnly const true + surveillanceBasedMonitoring const false + multi-gen cohort mix |
| L2 | `griefSupportAttestation` | grief_support | G4 STRUCTURAL: encryptedPayloadCid REQUIRED; musubi funeral cross-link |
| L3 | `counselorAttestation` | (all cells; counselor verification) | G3+G14 STRUCTURAL: counselorClass const "community-witnessed-competent" (clergy/ordained/state-licensed-psych/clinical-psychiatrist DELIBERATELY excluded); lLevel const L5 + employmentRelation const vocation-flow; witnessingCounselorAttestations minLength 3 |
| L4 | `acuteCrisisEscalationLog` | acute_crisis_escalation | G13 STRUCTURAL: mitateG5EmergencyKeywordTriggeredCid REQUIRED; severity enum |
| L5 | `silenKokoroReview` | (Council attestation scope) | G3/G4/G5/G6/G7/G8/G9/G10/G14 const-field structural enforcement (10+ const-field structurals) |

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- `required` list covering constitutionally-relevant fields;
- L1 STRUCTURAL: `encryptedPayloadCid` REQUIRED + `optInOnly` const true + `surveillanceBasedMonitoring` const false;
- L2 STRUCTURAL: `encryptedPayloadCid` REQUIRED;
- L3 STRUCTURAL: `counselorClass` const "community-witnessed-competent"; `lLevel` const "L5"; `employmentRelation` const "vocation-flow"; `witnessingCounselorAttestations` minLength 3;
- L4 STRUCTURAL: `mitateG5EmergencyKeywordTriggeredCid` REQUIRED;
- L5 STRUCTURAL multiple const-field enforcement:
  - `conversionTherapyEventsCount` const 0 (G5)
  - `commercialMentalHealthSoftwarePenetrationPct` const 0 (G7)
  - `commercialAiTherapyChatbotPenetrationPct` const 0 (G8)
  - `mandatoryScreeningEventsCount` const 0 (G9)
  - `surveillanceBasedMoodMonitoringEventsCount` const 0 (G10)
  - `aiOnlyTherapyEventsCount` const 0 (G6)
  - `videoRecordingEventsCount` const 0 (G4)
  - `clinicalPsychiatricEntityPenetrationPct` const 0 (G3)
  - `counselorVocationFlowCompliantRatioPctIntegerHundredths` const 10000 (G14)
  - `acuteCrisisEscalationsToMitateCount` (informational; not const)
  - `multiGenCohortRatioAvgPctIntegerHundredths` (G11 multi-gen invariant tracking)

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- `orgs/etzhayyim/com-etzhayyim-kokoro/manifest.edn` (canonical)
- `orgs/etzhayyim/com-etzhayyim-kokoro/README.md`
- `orgs/etzhayyim/com-etzhayyim-kokoro/CLAUDE.md`
- `/90-docs/adr/2605263700-kokoro-mental-health-tier-b-actor-r0.md`
