# 50-infra/hanami-robot — path reservation (R0)

**Status**: R0 path reservation — no code, no CAD, no firmware yet.

Per [ADR-2605260230](../../90-docs/adr/2605260230-hanami-robot-mechanical-design-mitate-r2-critical-path.md) §Decision 7 (Open-source release / G13): this directory is reserved for the Hanami (鼻見) robot's mechanical CAD, firmware source, network whitelist config, and classifier training corpus metadata. **R1 ADR creates the actual artifacts here** — R0 commits the path reservation only (analogous to the mmsheaf module path reservation pattern in ADR-2605250700).

Hanami is a **mitate-native** robotics class (8th class by count; sibling pattern to silicon Wave 2's Funamori introduction). Owned by mitate (`orgs/etzhayyim/com-etzhayyim-mitate`), not kuni-umi.

## Scope (what lands here at R1 prototype)

| Subdirectory | Content | Status |
|---|---|---|
| `cad/` | Mechanical CAD (4mm 軟性スコープ + 6-DOF arm + force-cutoff motor driver + autoclave-compatible scope tip) | R1 |
| `firmware/` | Embedded firmware source (force-feedback loop + network whitelist + emergency-stop logic) | R1 |
| `network-whitelist/` | Murakumo gateway IP allowlist config (G12 enforcement — no commercial vendor inference endpoint reachable) | R1 |
| `classifier-training-corpus/` | Metadata only (consent provenance, IRB-equivalent attestation CIDs); image data itself lives encrypted in MST per G2 | R1 |
| `validation/` | Phase A bench / Phase B phantom + cadaveric / Phase C clinical validation result attestations | R1 → R2 |
| `manufacturing-partner-attestation/` | DID registry of charter-aligned manufacturers per Decision 7 | R2 |

## Activation gate

This path stays scaffold-only until **mitate R1** has shipped (per ADR-2605260200) **AND** the Hanami R1 prototype ADR (TBD) lands with:

- ≥ 1 ENT specialist on Council medical advisory
- Manufacturing partner DID registered (kuni-umi class-A sterile sibling reuse is the proposed candidate per ADR-2605260230 §Decision 5 R1)
- Council Lv6+ ≥ 3 attestation of the Decision 2 safety validation matrix (5×4 hazard × mitigation grid)

Until then this directory contains **only this README** — the path reservation marker.

## Cross-corp manufacturing

Cross-religious-corp manufacturing per ADR-2605260230 §Decision 7 requires `silenMitateReview` scope `hanami-cross-corp-manufacture-attestation`. Apache 2.0 + Charter Compliance Rider v2.0 governs all artifacts that eventually land here.

## See also

- [ADR-2605260230](../../90-docs/adr/2605260230-hanami-robot-mechanical-design-mitate-r2-critical-path.md) — Hanami master design ADR
- [ADR-2605260100](../../90-docs/adr/2605260100-mitate-diagnostic-routing-charter.md) — mitate master charter
- [ADR-2605260200](../../90-docs/adr/2605260200-mitate-r1-advisory-self-care-pwa.md) — mitate R1 (Hanami mech design listed as R1→R2 transition prerequisite)
- [com-etzhayyim-mitate](https://github.com/etzhayyim/com-etzhayyim-mitate) — owning actor
- [`40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_nasal_endoscopy_acquire/`](../../40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_nasal_endoscopy_acquire/) — the Pregel cell that drives Hanami at runtime
