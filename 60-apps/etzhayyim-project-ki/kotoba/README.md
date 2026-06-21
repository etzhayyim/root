# ki kotoba

Phase E Option B reference implementation of ki (樹液 / sap) on the etzhayyim substrate.

Per [ADR-2605203000](../../../90-docs/adr/2605203000-kotoba-write-target-options.md), ki migrates from vendor's `createKyselyDb` pattern (RW direct write via dispatcher proxy) to **Option B** — PDS XRPC writes via `@etzhayyim/sdk e.write()`.

Coverage: **4 of 4 (100%)** canonical ki lexicons ported.

| Tier | Commands | Slice |
|---|---|---|
| Vascular | absorb, synthesize, bloom, ring | **1** |

## Bonsai biology mapping

```
koke/hakkou   →  absorb     →  AbsorbRecord     (xylem entry)
absorb        →  synthesize →  SynthesisRecord  (LLM photosynthesis)
synthesize    →  bloom      →  BloomRecord      (phloem publication)
periodically  →  ring       →  RingRecord       (dendrochronology snapshot)
```

## Architectural note (different from sibling kotoba packages)

Vendor's ki is a thin-edge dispatcher — its Worker proxies XRPC calls to
`dispatcher.etzhayyim.com`, which writes the underlying record into RisingWave.
On the etzhayyim substrate per ADR-2605111200:

- The CF Worker stays a **pure thin XRPC facade** (no RW write, no createKyselyDb).
- The LangServer pod owns the LLM call (`synthesize` stage) and writes the SynthesisRecord directly via `e.write()`.
- This `kotoba` package supplies the persistence layer used by **both** pod and Worker — `absorb` and `bloom` are simple records the Worker can write directly (no LLM); `synthesize` is pod-side because it needs LLM compute.

Same Option B `e.write()` API for all 4 procedures — the call site differs.

## Authority-chain DIDs

```
did:web:ki.etzhayyim.com                              — controller
did:web:ki.etzhayyim.com:absorb:{absorbId-slug}       — AbsorbRecord
did:web:ki.etzhayyim.com:synthesis:{artifactId-slug}  — SynthesisRecord
did:web:ki.etzhayyim.com:bloom:{bloomId-slug}         — BloomRecord
did:web:ki.etzhayyim.com:ring:{ringId-slug}           — RingRecord
```

## Usage

```ts
import { Etzhayyim } from "@etzhayyim/sdk";
import { absorb, synthesize, bloom, ring } from "@etzhayyim/ki-kotoba";

const e = new Etzhayyim({
  did: "did:web:ki.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
});

// 4-stage flow
const a = await absorb(e, {
  absorbId: "abs-2026-001",
  sourceVertexId: "vertex_koke_fixation:fix-2026-001",
  inputKind: "fixation",
  content: "Raw signal text or content reference",
});

const s = await synthesize(e, {
  artifactId: "art-2026-001",
  absorbId: a.absorbId!,
  synthesis: "LLM-synthesized structured knowledge",
  confidencePermille: 870,   // 0.87 (no-float per AT Lexicon)
  model: "claude-opus-4-7",
});

const b = await bloom(e, {
  bloomId: "bloom-2026-001",
  artifactId: s.artifactId!,
});

const r = await ring(e, {
  ringId: "ring-2026-q2",
  period: "P1W",   // 1-week snapshot window
});
// → snapshotCount = number of BloomRecord rows published within the past week
```

## Why Option B for ki

Per ADR-2605203000 Phase E decision matrix:
- **Catalog**: knowledge graph signals + LLM artifacts (private state, not federated)
- **Write cadence**: per-signal burst (absorb/synthesize/bloom triggered by LangGraph runs)
- **Query pattern**: timeline walks (ring scans bloom records) + LLM call result lookups

Option A (vendor RW mirror) rejected — ADR-2605172000 mandates kotoba.

## What this package IS / ISN'T

**IS**:
- Reference impl of all 4 canonical ki lexicons on Option B (PDS XRPC).
- Documentation of the dispatcher-proxy → pod+worker translation.
- ISO-8601 duration parsing for ring.period.

**ISN'T**:
- A deployed Worker (scaffold-only).
- The LLM `synthesize` engine itself — this is the persistence side; the LangServer pod owns the model call.
- mst-projector views — Phase 3 dependency for ring snapshot O(1).

## Related

- [ADR-2605203000](../../../90-docs/adr/2605203000-kotoba-write-target-options.md) — Phase E write-target options
- [ADR-2605111200](../../../90-docs/adr/2605111200-cf-worker-edge-only-no-rw-connection.md) — CF Worker edge-only
- [hanrei kotoba](../../etzhayyim-project-hanrei/kotoba/) — Option B reference (31/31 ✓)
- [ipaddress kotoba](../../etzhayyim-project-ipaddress/kotoba/) — Option B reference (37/37 ✓)
- [sbom kotoba](../../etzhayyim-project-sbom/kotoba/) — Option B reference (17/N, canonical ✓)
- [kiyo kotoba](../../etzhayyim-project-kiyo/kotoba/) — Option B reference (12/12 ✓)
