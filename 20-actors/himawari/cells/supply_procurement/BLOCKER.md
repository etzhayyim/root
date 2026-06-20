# supply_procurement — Port Blocker

**Status**: NOT PORTED (complex multi-actor composition + SBOM bridge)

**Reason**: This cell (402 lines) is the most complex himawari cell; it coordinates three external systems:

1. **okaimono Commons provisioning composition** (ADR-2606012100): The cell calls `_okaimono.check_sbt_eligibility()` and `_okaimono.build_settlement_intent()` — verified Python functions. Porting requires:
   - okaimono to be available in cljc context (currently Python-only)
   - Settlement intent shape to be identical (includes USDC minor units, tithe routing)
   - SBT registry eligibility logic to match exactly

2. **giemon CycloneDX → kotoba SBOM bridge** (ADR-2605312330): The cell calls `_cdx_to_ingest()` to project a CycloneDX bill-of-materials into `\:cdx/*` kotoba entities. Porting requires:
   - Bridge logic replication (component → claim graph transformation)
   - SBOM entity shape equivalence (purl, name, supplier, properties)
   - kotoba ingest batch API (JSON encoding must be identical)

3. **abaki Anti-Monopoly policy routing** (ADR-2606073100): The cell reads `abaki/out/routing-policy.json` to check if a supplier is blocked (React mechanism enforcement). Requires:
   - File path resolution in cljc context (relative to repo root)
   - JSON parsing and entity ID matching
   - Policy gate integration

4. **Nested procurement order + attestation building**: The cell synthesizes complex nested structures:
   - `procurementOrder` (state machine, settlement intent, tithe calculation)
   - `sbomAttestation` (CycloneDX doc + kotoba entity list)
   - `provenanceAttestation` (lot CID + chain-of-custody with witness quorum)

**Recommendation**: Defer to a dedicated 3rd-pass wave that:
- Coordinates okaimono cljc port in parallel (or reuses Python via subprocess if needed)
- Ports the giemon CycloneDX bridge as a shared utility
- Verifies abaki policy JSON load + gate logic
- Tests the cell's procurement order shape against live okaimono settlement records
- Includes integration tests with a mock kotoba host (datalog.ingest_batch)

**Accepted for next wave**: supply_procurement (highest complexity; blocks final himawari manufacturing loop).
