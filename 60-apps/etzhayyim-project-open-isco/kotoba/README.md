# open-isco — kotoba reference implementation

This directory is the **reference implementation** of an etzhayyim/root open app under the substrate rules of [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md): no RisingWave, no centralized DB, no fiat payment processor. All state lives on AT Protocol MST + IPFS; all anchoring lands on Base L2; all reads go through [@etzhayyim/sdk](../../../20-actors/etzhayyim-sdk/).

The sibling [`../appview/`](../appview) directory is the **legacy** RW-backed implementation, kept for reference until this kotoba version reaches parity.

## What this proves

ISCO-08 is a small, slow-moving, public dataset (525 occupations across 4 hierarchy levels). It's the ideal "smallest open-* app" cohort to demonstrate the substrate replacement end-to-end:

| Property | Why it makes this a good first proof |
|---|---|
| Cardinality ≈ 525 | Browser MST traversal works comfortably in-memory |
| Write rate ≈ 0 | Seed once per ISCO revision (~10 year cadence); no real-time concerns |
| No auth required | Read-only public data; SDK auth surface not exercised |
| Public source (ILO) | No PII, no consent flow needed |
| Hierarchy = MST-natural | major / sub-major / minor / unit-group key prefixes map directly to MST prefix traversal |

If the SDK pattern works here cleanly, it generalizes to the other 21 open-* apps.

## Layout

```
kotoba/
├── README.md            # this file
├── package.json         # depends on @etzhayyim/sdk
├── tsconfig.json
├── src/
│   ├── types.ts         # Occupation type (matches com.etzhayyim.apps.openIsco.occupation lexicon)
│   ├── seed.ts          # one-shot seeder — reads ISCO CSV → SDK.write() per row
│   ├── query.ts         # read API — SDK.read() with key-prefix MST traversal
│   ├── verify.ts        # verification example — SDK.verify() returns Merkle proof
│   └── index.ts         # public exports
└── data/
    └── isco08.sample.json   # 5-occupation sample for smoke tests
```

## SDK usage map (ADR-2605172000 § "Per-app-pattern migration guide")

Old (RW-backed `appview/`):

```typescript
// pseudocode of the old appview
const rows = await kysely
  .selectFrom('vertex_open_isco_occupation')
  .where('major', '=', '2')
  .selectAll()
  .execute();
```

New (this kotoba reference impl):

```typescript
import { Etzhayyim } from "@etzhayyim/sdk";

const e = new Etzhayyim({
  did: "did:web:etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  ipfsGateway: "https://ipfs.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
});

// Read — replaces SELECT
const { records } = await e.read<Occupation>({
  collection: "com.etzhayyim.apps.openIsco.occupation",
  prefix: "2",       // major code prefix
  limit: 100,
});
```

## Seed → query → verify cycle

1. **Seed once** (operator action, after ISCO release):
   ```bash
   pnpm tsx src/seed.ts data/isco08.full.csv
   # → 525 records, ~525 PDS writes, ~1 L2 anchor batch
   # → idempotent (re-running skips existing rkey)
   ```

2. **Query anytime** (any client, no SDK token):
   ```bash
   pnpm tsx src/query.ts --prefix=2          # 'Professionals' major group
   pnpm tsx src/query.ts --code=2511         # specific occupation
   ```

3. **Verify anytime** (any third party):
   ```bash
   pnpm tsx src/verify.ts at://did:web:etzhayyim.com/com.etzhayyim.apps.openIsco.occupation/3a7b6806
   # → { included: true, anchoredAt: { txHash, blockNumber, rootCid }, merklePath: [...] }
   ```

## What's NOT here (intentional)

- No SQL migration files. `appview/` has those for the RW path; kotoba is kotoba by construction.
- No Postgres connection string. No env var for `DATABASE_URL`.
- No Stripe / billing. Read access is free; rate limiting belongs in PDS, not in app code.
- No JWT issuer. The user (read) doesn't authenticate; the seeder (write) authenticates via DID + WebAuthn signature.

## Status

**Scaffold v0.0.0**. The SDK methods themselves still throw "not yet implemented" (see [@etzhayyim/sdk](../../../20-actors/etzhayyim-sdk/README.md)). This reference impl demonstrates the *call shape* — once the SDK lands its v0.1, this app becomes the first concrete test of the substrate end-to-end.

## See also

- [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — substrate hard rule
- [@etzhayyim/sdk](../../../20-actors/etzhayyim-sdk/README.md) — SDK API surface
- [`../appview/`](../appview/) — the RW-backed legacy implementation
- ILO ISCO-08 — https://www.ilo.org/public/english/bureau/stat/isco/isco08/
