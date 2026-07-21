# com.etzhayyim.sonae.* — sonae (備え) Lexicons

**Owner actor**: `did:web:sonae.etzhayyim.com` (`orgs/etzhayyim/com-etzhayyim-sonae`)
**ADR**: ADR-2606091200 (R0 scaffold)
**Status**: R0 schema skeletons. Full schemas at R1+.
**Phase**: pre-disaster (before). Response Lexicons are `com.etzhayyim.kazaori.*`.

## 6 Lexicons

| # | Lexicon | Consumer cell | Purpose |
|---|---|---|---|
| L1 | `hazardSignalRecord` | hazard_watch | Open-feed hazard signal; `sourceFeed` enum (G4 open gov feeds); `openDataOnlyAttested` const true (G6) |
| L2 | `siteRiskProfile` | risk_assessment | Per-site exposure + vulnerability; community-scale (G3); aggregate-only, no individual data (G6) |
| L3 | `earlyWarningRelay` | early_warning_relay | Relay of OFFICIAL warning; `relayOnly` const true + `authoritativeSource` required (G8 — defining gate) |
| L4 | `preparednessPlan` | preparedness_plan | Stockpile / safe-site / route / opt-in registry targets; cross-actor mizuho/mitsuho/tatekata/hagukumi via $ref |
| L5 | `drillAttestation` | drill_attestation | Opt-in drill record; can satisfy kazaori R1 drill activation gate |
| L6 | `sonaeReadinessReview` | (Council attestation scope) | Periodic Sendai + Sphere alignment + forecast-accuracy + false-authority audit (G9) |

> The `handoff_trigger` cell emits a `disasterImminenceSignal` payload to
> `kazaori.emergency_declaration` (recommend-only). This is a cross-actor
> signal, not a sonae-owned record — the emergency state is owned by
> kazaori's `emergencyDeclarationAttestation` (G10).

## Schema Discipline (R1+)

- `additionalProperties: false` at top-level;
- L1 `sourceFeed` enum restricted to open gov feeds (G4) + `openDataOnlyAttested` const true (G6);
- L2 `communityScaleAttested` const true (G3) + NO individual-level fields (G6; aggregate opt-in counts only);
- L3 `relayOnly` const true + `authoritativeSource` REQUIRED (G8 — sonae never originates official warnings);
- L4 registries opt-in + member-signed encrypted per ADR-2605181100 (G6);
- L5 `participantsOptIn` const true (G6);
- L6 `falseAuthorityIncidents` audit counter (G8; target 0);
- Cross-actor coupling via $ref (siteRiskProfileRef / tatekataAssessmentRef / stockpileTarget.crossActor etc.).

## R0 Status

Schemas at R0 are skeleton-level; full structural enforcement at R1.

## Related Files

- [canonical `manifest.edn`](https://github.com/etzhayyim/com-etzhayyim-sonae/blob/8048df4675b8f504c3bd7b460280dfb270fb137b/manifest.edn)
- [standalone actor repository](https://github.com/etzhayyim/com-etzhayyim-sonae)
- `/90-docs/adr/2606091200-sonae-pre-disaster-foresight-tier-b-actor-r0.md`
- `/90-docs/adr/2605263200-kazaori-disaster-response-tier-b-actor-r0.md` (downstream response)
