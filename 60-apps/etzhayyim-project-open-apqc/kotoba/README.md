# open-apqc — kotoba reference implementation (Phase 3 step 1)

kotoba port of the APQC PCF (Process Classification Framework) under the substrate rules of [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md). Promotes the project from the Phase 2 scaffold (README + CLAUDE.md only) to Phase 3 with a working taxonomy publisher.

Fourth kotoba actor after [`open-isco`](../../etzhayyim-project-open-isco/kotoba/) (occupations), [`open-isic`](../../etzhayyim-project-open-isic/kotoba/) (industry classes), and [`open-unispsc`](../../etzhayyim-project-open-unispsc/kotoba/) (procurement segments). The Phase 2 vendor-port plan (PCF catalog + BPMN task catalog + projector spec from `etzhayyim/etzhayyim-root`) is deferred — this PR delivers the substrate-publication surface using the public v7.4 cross-industry framework data directly.

## Phase 1 scope: the 13 L1 process categories

APQC PCF has five hierarchy layers:

| Layer | Cardinality | rkey |
|---|---:|---|
| L1 (process category) | 13 (v7.4 cross-industry) | this PR — `literal:{code}` (e.g. "7.0") |
| L2 (process group) | ~80 | future PR (`com.etzhayyim.apqc.processGroup`) |
| L3 (process) | ~250 | future PR |
| L4 (activity) | ~700 | future PR |
| L5 (task) | ~1,000 | future PR (segmented) |

Starting with L1 (13 entries) locks down the substrate-publication pattern at trivial cardinality. The seed data is **inline** in `src/seed.ts` because L1 is a well-known public list — future L2+ layers will load from a CSV / JSON catalog under `data/` once that catalog is checked in.

## Layout

```
kotoba/
├── README.md            # this file
├── package.json         # depends on @etzhayyim/sdk
├── tsconfig.json
└── src/
    ├── types.ts         # ProcessCategory + isValidL1Code + l1Ordinal + APQC_PCF_VERSION
    ├── types.test.ts    # vitest — 28 cases covering L1 code format (incl. all 13 valid + 11 rejected)
    ├── seed.ts          # one-shot seeder — inline 13-entry catalog → SDK.write() per category
    ├── seed.test.ts     # vitest — catalog completeness (cardinality, gap-free codes, anchor names) + converter shape
    ├── query.ts         # read API — SDK.read() with rkey or prefix MST traversal
    ├── verify.ts        # verification example — SDK.verify() returns Merkle proof
    └── index.ts         # public exports (queryAll, getByCode, helpers)
```

## Lexicon

`com.etzhayyim.apqc.processCategory` (record), at [`orgs/etzhayyim/com-etzhayyim-apqc/lex/processCategory.json`](../../../orgs/etzhayyim/com-etzhayyim-apqc/lex/processCategory.json). Naming convention follows the existing `com.etzhayyim.apqc.*` namespace (where sibling `getProcess` / `materializeSubprocesses` / `coverageSnapshot` / `emitEvent` are procedures) — record-vs-procedure split.

`rkey` policy: `literal:{code}` — the L1 identifier (e.g. "7.0", "13.0") is the MST key verbatim. Idempotent re-seeds produce no new records. AT-Protocol literal-rkey alphabet allows `.` so the dotted-code format is preserved on disk.

## v7.4 L1 catalog (anchor list)

```
 1.0  Develop Vision and Strategy
 2.0  Develop and Manage Products and Services
 3.0  Market and Sell Products and Services
 4.0  Deliver Physical Products
 5.0  Deliver Services
 6.0  Manage Customer Service
 7.0  Develop and Manage Human Capital
 8.0  Manage Information Technology (IT)
 9.0  Manage Financial Resources
10.0  Acquire, Construct, and Manage Assets
11.0  Manage Enterprise Risk, Compliance, Remediation, and Resiliency
12.0  Manage External Relationships
13.0  Develop and Manage Business Capabilities
```

Source: APQC's published PCF v7.4 cross-industry framework (public taxonomy, freely usable under APQC's open-license terms). When v7.5 ships with renamings, the seed catalog + anchor tests get updated in the same PR; the lexicon's `version` field locks records to the revision they were published under.

## Seed

```bash
# Full seed (13 L1 categories)
pnpm tsx src/seed.ts

# Subset
pnpm tsx src/seed.ts --only=7.0
```

Required env: `ETZ_PDS_URL` (default `https://pds.etzhayyim.com`) + either an authenticated SDK session OR an SDK builder that resolves credentials from the host (deploy-time concern; not in scope here).

## Query

```bash
pnpm tsx src/query.ts --code=7.0           # one L1 category
pnpm tsx src/query.ts --prefix=1           # 1.0 + 10.0..13.0 (prefix match)
pnpm tsx src/query.ts                       # full list
```

## Verify

```bash
pnpm tsx src/verify.ts at://did:web:etzhayyim.com/com.etzhayyim.apqc.processCategory/7.0
```

Returns the Merkle path from the record to the MST root that was anchored to Base L2 via the substrate pipeline. Any client (no credentials) can re-check the proof.

## Tests

```bash
pnpm test
# 36/36 (vitest):
#   - 28 type cases: all 13 valid L1 codes + 11 rejected variants (0.0 / 14.0 / 1.1 / "1" / etc.)
#                    + l1Ordinal numeric extraction + NaN-safe rejection
#   - 8 seed cases: catalog cardinality, gap-free 1.0–13.0, anchor names verbatim,
#                   toProcessCategory shape + level/version/publishedAt defaults + invalid-code throw + empty-name throw
```

## Status

| Surface | State |
|---|---|
| Record lexicon `com.etzhayyim.apqc.processCategory` | ✅ |
| Seeder + helpers + inline v7.4 catalog | ✅ |
| Pure-helper tests | ✅ 36/36 |
| Live PDS seed run | ⏳ pending PDS auth credentials (Gate 4 of [`OPERATIONAL-DEPLOY.md`](../../../50-infra/OPERATIONAL-DEPLOY.md)) |
| Anchor verify against deployed contract | ⏳ pending Gate 3 EtzhayyimAnchor deploy |
| L2 (`processGroup`) record lexicon + seed | ⏳ future PR (~80 entries, requires CSV/JSON catalog) |
| L3 / L4 / L5 layers | ⏳ future PRs |
| Vendor PCF catalog port (etzhayyim/etzhayyim-root) | ⏳ deferred (Phase 2 plan in project CLAUDE.md) |

## See also

- [`60-apps/etzhayyim-project-open-isco/kotoba/`](../../etzhayyim-project-open-isco/kotoba/) — 1st kotoba actor (525 ISCO-08 occupations)
- [`60-apps/etzhayyim-project-open-isic/kotoba/`](../../etzhayyim-project-open-isic/kotoba/) — 2nd kotoba actor (428 ISIC Rev.4 classes)
- [`60-apps/etzhayyim-project-open-unispsc/kotoba/`](../../etzhayyim-project-open-unispsc/kotoba/) — 3rd kotoba actor (50 UNSPSC segments)
- [`20-actors/etzhayyim-sdk/`](../../../20-actors/etzhayyim-sdk/) — substrate-purity SDK
- [`50-infra/OPERATIONAL-DEPLOY.md`](../../../50-infra/OPERATIONAL-DEPLOY.md) — production runbook
- [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — substrate rules
