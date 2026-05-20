# hanrei rw-free

Phase E wave 3 Option B reference implementation of hanrei on the etzhayyim substrate.

Per [ADR-2605203000](../../../90-docs/adr/2605203000-rw-free-write-target-options.md), hanrei was deferred during today's wave 1+2 because vendor src/app.ts uses `createKyselyDb()` (forbidden on etzhayyim per ADR-2605172000). Option B (PDS XRPC) is the per-actor decision.

Initial slice: **3 of 31** hanrei XRPC commands ported.

- `ai.gftd.hanrei.registerJurisdictions` → `registerJurisdiction` (singular, idempotent rkey)
- `ai.gftd.hanrei.getJurisdiction`
- `ai.gftd.hanrei.listJurisdictions`

Remaining 28 commands (`registerCourtProfiles / collectCases / collectCaseDetail / collectEgovLaws / collectGazette / collectLegislation / searchCases / searchDecisions / extractCasePersons / createInformationHunt / coverageStats / ...`) follow same Option B pattern; wave 3+ follow-up.

## Pattern translation (Option B)

| Vendor | etzhayyim |
|---|---|
| `const db = createKyselyDb(env.HYPERDRIVE);` | `import type { Etzhayyim }` |
| `db.insertInto("vertex_hanrei_jurisdiction").values({...})` | `e.write({ collection: "ai.gftd.hanrei.jurisdiction", record, rkey })` |
| Read via SELECT … WHERE iso3 = ? | `e.read({ collection, rkey: \`jurisdiction-${iso3}\` })` |

Same idempotency pattern as ipaddress / tsukuru (rkey derived from natural key).

## Note on vendor stubs

Vendor's cmdGetJurisdiction / cmdListJurisdictions were already returning `[]` (TODO: vertex_jurisdiction not in @gftd/graph-schema). The Option B rewrite is therefore behavior-preserving + finally functional — PDS XRPC writes work today without waiting for graph-schema additions.

## Authority chain (per hanrei CLAUDE.md)

```
did:web:hanrei.etzhayyim.com                       — controller
did:web:hanrei.etzhayyim.com:jurisdiction:{iso3}   ← this slice
did:web:hanrei.etzhayyim.com:court:{jurisdiction}:{courtId}
did:web:hanrei.etzhayyim.com:case:{caseId}
did:web:hanrei.etzhayyim.com:law:{lawId}
```

## Usage

```ts
import { Etzhayyim } from "@etzhayyim/sdk";
import {
  registerJurisdiction,
  getJurisdiction,
  listJurisdictions,
} from "@etzhayyim/hanrei-rw-free";

const e = new Etzhayyim({
  did: "did:web:hanrei.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  // session or auth
});

const out = await registerJurisdiction(e, {
  iso3: "JPN",
  name: "Japan",
  nameLocal: "日本国",
  legalSystem: "civil-law",
  primaryLanguage: "ja",
  caseLawSource: "courts.go.jp",
});
// → { status: "registered", jurisdictionUri, did: "did:web:hanrei.etzhayyim.com:jurisdiction:jpn" }

const got = await getJurisdiction(e, { iso3: "JPN" });
// → { jurisdiction: { iso3: "jpn", name: "Japan", ... } }
```

## Related

- [ADR-2605203000](../../../90-docs/adr/2605203000-rw-free-write-target-options.md) — Phase E decision matrix
- [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — RW-free substrate
- [ipaddress rw-free](../../ai-gftd-project-ipaddress/rw-free/) — Option B sibling reference (2/37 commands)
- [tsukuru rw-free](../../ai-gftd-project-tsukuru/rw-free/) — Option B full app (13/46 commands)
