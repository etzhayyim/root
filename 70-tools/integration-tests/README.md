# Phase H Cross-Actor Integration Tests

End-to-end test suite demonstrating that the 25-actor etzhayyim mesh composes correctly via the `@etzhayyim/sdk-mock` in-memory PDS substrate.

## Purpose

Phase H validates that:
1. Multi-actor flows complete without cross-contamination
2. Actor DIDs and collection namespaces remain isolated
3. Reference integrity is preserved across actor boundaries
4. Core platform metaphors (bonsai vascular, authority chain, blast radius) work end-to-end

## Test Scenarios

### 1. `bonsai-vascular.test.ts` — Photosynthesis → Fermentation → Sap Flow

**Actors**: koke → hakkou → ki

**Flow**:
- `koke.fixSignal()` captures raw external signal (CO₂ → glucose)
- `hakkou.startFerment()` + `updateFermentStatus()` transforms glucose → ethanol
- `ki.absorb()` + `synthesize()` + `bloom()` + `ring()` completes vascular pipeline

**Validates**: End-to-end traceability from fixation → fermentation → synthesis → bloom → dendrochronology snapshot.

### 2. `authority-chain.test.ts` — Jurisdiction + Statute + Cases

**Actors**: hanrei + houbun

**Flow**:
- `hanrei.registerJurisdiction()` establishes civil-law context
- `hanrei.seedCases()` populates case corpus
- `houbun.registerStatute()` + `registerArticle()` anchors statutory text

**Validates**: Separate collections, DID prefixes, and cross-actor reference integrity.

### 3. `sbom-blast-radius.test.ts` — CVE Pipeline with Host Attribution

**Actors**: ipaddress + sbom

**Flow**:
- `ipaddress.registerAsn()` + `registerPrefix()` + `registerIp()` maps network topology
- `sbom.registerArtifact()` + `registerComponent()` defines app dependencies
- `sbom.cveIngestOsv()` + `registerVulnMatch()` identifies blast radius

**Validates**: Cross-actor querying and CVE severity propagation across mesh.

### 4. `otakiage-lifecycle.test.ts` — State Machine Transitions

**Actors**: otakiage (single-actor state machine patterns)

**Flow**:
- Test 1: `reuse_then_ritual` → `handover` path
- Test 2: `reuse_then_ritual` → `expire` → `ritualize` cascade
- Test 3: `ritual_only` → `ritual_pending` immediate transition

**Validates**: State machine correctness and terminal state enforcement.

### 5. `mst-projector-end-to-end.test.ts` — Materialized Views

**Actors**: kiyo + mst-projector

**Flow**:
- Submit 3 papers via `kiyo.submitPaper()`
- Direct projector commit processing (no firehose)
- Query by text search, attribute, and aggregate

**Validates**: Indexing, pagination, and multi-mode query correctness.

## Running Tests

```bash
npm test
```

Tests use `vitest` with globals enabled. Each test runs independently with a fresh `MockEtzhayyim` instance.

## Architecture

- **MockEtzhayyim**: In-memory PDS substrate with collection isolation and URI generation
- **Workspace references**: All actor packages use `workspace:*` resolution
- **Collection namespace**: Auto-prefixed by each actor's barrel exports
- **No dependencies**: Tests don't require PDS, IPFS, L2, or network

## Notes

- Sequences preserve insertion order (TID-like semantics)
- Pagination cursors are rkey-based
- Soft-delete and conflict resolution are actor-specific (not mocked)
- Phase 3 features (firehose streaming, distributed projectors) mock to no-op
