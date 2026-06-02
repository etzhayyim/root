# com.etzhayyim.tsukuroi.* — Lexicons

Lexicon surface for **tsukuroi** (繕い) — the authorized vulnerability-remediation
+ patch-proposal actor; the constructive sibling of **akuma** (悪魔). Master ADR:
**ADR-2605291500**. SSoT detail: `20-actors/tsukuroi/CLAUDE.md`.

tsukuroi closes the akuma diagnosis loop (ADR-2605151400): owner-attested
finding → defensive fix patch → egress-restricted sandbox validation →
**PROPOSE-ONLY** fork-and-PR → human owner merges → akuma re-probe verifies.

R0 = schema skeletons (this directory). R1 adds `additionalProperties: false`
+ required-field enforcement + signature/scan gates (Council Lv6+ ≥3 ratify,
post 2026-06-19).

| Lexicon | Purpose | Key structural invariants |
|---|---|---|
| `remediationMandate` | owner+authority dual-signed remediation authorization, scoped to an akuma `findingCid` | `mergeAuthorityHeld` const false (G4); `delegationCredentialRef` is a ref not a secret (G8); `allowedPaths` bounds writes (G6) |
| `patchProposal` | a candidate defensive fix patch | `defensiveOnly` const true (G5); `autonomousMerge` const false (G4); `pathsTouched ⊆ allowedPaths` (G6) |
| `patchValidationResult` | sandbox build/test outcome | `ranAgainstLiveTarget` const false (G9); `sandboxNamespace` const `tsukuroi-validate` |
| `closureAttestation` | remediation closure | `remediated` true iff `ownerMerged` ∧ `akumaReprobePass` (G11) |
| `silenTsukuroiReview` | quarterly Council audit | four zero-counters const 0: `autonomousMergeCount`/`exploitArtifactCount`/`outOfScopeWriteCount`/`platformHeldKeyCount` (G4/G5/G6/G8); nonzero ⇒ halt + chigiri.disputeMediation (G13) |

**Ceiling (constitutional)**: PROPOSE-ONLY (no merge/deploy) · NO PROBING
(akuma `findingCid` input only) · DEFENSIVE-ONLY (no exploit/PoC, §2(a)) ·
NO PLATFORM-HELD KEY (ADR-2605231525) · Murakumo-only inference (ADR-2605215000).
