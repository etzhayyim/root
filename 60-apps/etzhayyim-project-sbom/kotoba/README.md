# sbom kotoba

Phase E Option B reference implementation of sbom on the etzhayyim substrate.

Per [ADR-2605203000](../../../90-docs/adr/2605203000-kotoba-write-target-options.md), sbom migrates from vendor's `createKyselyDb` pattern (RW direct write) to **Option B** — PDS XRPC writes via `@etzhayyim/sdk e.write()`.

Coverage: **17** commands across 7 tiers (canonical vendor lexicon surface complete).

| Tier | Commands | Slice |
|---|---|---|
| Artifact | registerArtifact, getArtifact | 1 |
| Component | registerComponent, listComponents | 1 |
| CVE + VulnMatch | cveIngestOsv, registerVulnMatch, listVulnMatches | 2 |
| Patch | registerPatchPolicy, registerPatchAction, getBlastRadius | 3 |
| Analyze + SLA | getSlaTimer, listOverdueVulnMatches, getArtifactDependents, analyzeApp | 4 |
| Recall + Health | recall, updateComponentSupplier, health | **5** |

Vendor canonical lexicons (`registerArtifact / cveIngestOsv / recall /
health`) are all covered + the extended graph (Component / VulnMatch /
PatchPolicy / PatchAction / analytics).

## Authority-chain DIDs (per sbom CLAUDE.md)

```
did:web:sbom.etzhayyim.com                                — controller
did:web:sbom.etzhayyim.com:artifact:{sha256-short}        — this slice (SbomArtifact)
did:web:sbom.etzhayyim.com:component:{purl-slug}          — this slice (SbomComponent)
did:web:sbom.etzhayyim.com:cve:{cve-id}                   — this slice (CveEntry)
did:web:sbom.etzhayyim.com:vulnmatch:{cve-id}-{purl-slug} — this slice (VulnMatch)
did:web:sbom.etzhayyim.com:patchpolicy:{policy-id}        — this slice (PatchPolicy)
did:web:sbom.etzhayyim.com:patchaction:{action-id}        — this slice (PatchAction)
```

## Pattern translation (Option B)

| Vendor (`sbom.etzhayyim.com`) | etzhayyim (this PR) |
|---|---|
| `const db = createKyselyDb();` | `import type { Etzhayyim } from "@etzhayyim/sdk"` |
| `db.insertInto("vertex_sbom_artifact").values({...}).execute()` | `e.write({ collection: "com.etzhayyim.apps.sbom.artifact", record, rkey })` |
| `db.selectFrom("vertex_sbom_artifact").where("sha256","=",h).execute()` | `e.read({ collection, rkey: \`artifact-${sha256Short(h)}\` })` |

## Usage

```ts
import { Etzhayyim } from "@etzhayyim/sdk";
import { registerArtifact, registerComponent } from "@etzhayyim/sbom-kotoba";

const e = new Etzhayyim({
  did: "did:web:sbom.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
});

// Register an SBOM artifact
const art = await registerArtifact(e, {
  sha256: "a3f5e8b7c2d1a4f6e9b8d7c5a2f1e3b6d8c4a5f9e7b3d2c8a1f6e5b4d3c2a1f0",
  format: "cyclonedx-1.5",
  builtForAppDid: "did:web:yata.etzhayyim.com:app:ameno",
  componentCount: 247,
});
// → { status: "registered", artifactUri: "at://...", did: "did:web:sbom...artifact:a3f5e8b7c2d1" }

// Register a component
const c = await registerComponent(e, {
  purl: "pkg:npm/lodash@4.17.21",
  name: "lodash",
  version: "4.17.21",
  ecosystem: "npm",
  license: ["MIT"],
  artifactDid: art.did,
});
```

## Why Option B for sbom

Per ADR-2605203000 Phase E decision matrix:
- **Catalog: A-group open standards** — SBOM is CycloneDX/SPDX (open standards), CVE feeds from OSV (open data)
- **Data shape**: small structured records (artifact metadata + component refs + vuln matches), NOT bulk blobs
- **Write cadence**: per-build burst (every CI run) + per-vuln-feed-poll bursts (hourly via ct-monitor)
- **Query pattern**: blast-radius walks (purl → vulnmatch → artifact → app) + SLA timer scans

Option A (vendor RW mirror) rejected — ADR-2605172000 mandates kotoba for actor migration.
Option C (IPFS) rejected — SBOM records are small structured data, not blobs.

## What this package IS / ISN'T

**IS**:
- Reference impl of 4 sbom commands on Option B (PDS XRPC).
- Documentation of the createKyselyDb → e.write() translation.
- Type definitions for the SbomArtifact + SbomComponent tiers of the sbom authority chain.

**ISN'T**:
- A deployed Worker (scaffold-only, matches open-isco / hanrei / ipaddress kotoba state).
- A production replacement for `sbom.etzhayyim.com` — vendor `sbom` continues to serve builds during migration.
- Full command parity — VulnMatch/PatchPolicy/PatchAction tiers + CVE pipeline ship in follow-up slices.
- mst-projector views — Phase 3 dependency for graph walks (blast radius).

## Related

- [ADR-2605203000](../../../90-docs/adr/2605203000-kotoba-write-target-options.md) — Phase E write-target options
- [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — kotoba substrate
- [hanrei kotoba](../../etzhayyim-project-hanrei/kotoba/) — Option B reference (31/31 complete)
- [ipaddress kotoba](../../etzhayyim-project-ipaddress/kotoba/) — Option B reference (37/37 complete)
- [sbom CLAUDE.md](../CLAUDE.md) — actor design + graph relationships
