# open-unispsc — kotoba reference implementation

kotoba port of the UN UNSPSC (Standard Products and Services Code) taxonomy under the substrate rules of [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md): no RisingWave, no centralized DB, no fiat payment processor. Taxonomy state lives on AT Protocol MST + IPFS; the substrate pipeline (mst-projector → ipfs-pinner → anchor-cron) anchors the MST root to Base L2 so any third party can verify the taxonomy without trusting this operator.

Third kotoba actor after [`open-isco/kotoba/`](../../etzhayyim-project-open-isco/kotoba/) (occupations) and [`open-isic/kotoba/`](../../etzhayyim-project-open-isic/kotoba/) (industry classes). The classification runtime (active business logic for segments / families / classes / commodities) lives in this same project's sibling directories and uses different lexicons (the `*procedure*` lexicons under `com.etzhayyim.apps.openUnispsc.*`); this PR adds only the taxonomy publisher surface.

## Phase 1 scope: the 50 segments

UNSPSC has four hierarchical layers:

| Layer | Cardinality | rkey |
|---|---:|---|
| Segment | 50 (2-digit) | this PR — `literal:{code}` |
| Family | ~400 (4-digit) | future PR |
| Class | ~900 (6-digit) | future PR |
| Commodity | ~70,000 (8-digit) | future PR (likely segmented) |

Starting with the smallest layer locks down the substrate-publication pattern at minimal cardinality. The family/class/commodity layers reuse the exact same scaffolding — only the lexicon NSID + source data change.

## Layout

```
kotoba/
├── README.md            # this file
├── package.json         # depends on @etzhayyim/sdk
├── tsconfig.json
└── src/
    ├── types.ts         # SegmentDef + isValidCode / isValidSlug / cpcSectionFor
    ├── types.test.ts    # vitest — 56 cases covering code format, slug regex, CPC ranges
    ├── seed.ts          # one-shot seeder — reads ../segments.csv → SDK.write() per segment
    ├── seed.test.ts     # vitest — converter shape + CSV parsing (comma-in-name handling, sort, header)
    ├── query.ts         # read API — SDK.read() with key-prefix MST traversal
    ├── verify.ts        # verification example — SDK.verify() returns Merkle proof
    └── index.ts         # public exports (queryByPrefix, getByCode, helpers)
```

## Lexicon

`com.etzhayyim.apps.openUnispsc.segmentDef` (record), at [`00-contracts/lexicons/com/etzhayyim/apps/openUnispsc/segmentDef.json`](../../../00-contracts/lexicons/com/etzhayyim/apps/openUnispsc/segmentDef.json). Naming note: the sibling `segment.json` is a **procedure** that actively resolves a segment as a business-portfolio boundary; `segmentDef` is the **record** companion that persists the catalog on PDS. The two are complementary — the procedure does runtime work, the record gives the substrate pipeline a content-addressable target.

`rkey` policy: `literal:{code}` — the 2-digit UNSPSC code is the MST key verbatim. Idempotent re-seeds produce no new records.

## CPC concordance (optional field)

`cpcSectionFor(code)` implements the segment-range → CPC-section mapping documented in the project root CLAUDE.md:

| UNSPSC segments | Primary CPC section | Why |
|---|---|---|
| 10–15 | 0–1 | Agriculture, ores |
| 20–27 | 3–4 | Transportable goods, machinery |
| 30–31 | 5 | Construction |
| 39–48 | 3–4 | Goods, machinery |
| 50–53 | 2 | Food, textiles |
| 55–60 | 8 | Business services |
| 70–86 | 6–9 | Services |
| 90–95 | 9 | Community / public services |

Codes outside those ranges (16–19, 28–29, 32–38, 49, 54, 61–69, 87–89, 96–98) leave `cpcSection` absent rather than guessing.

## Seed

```bash
# Full seed (50 segments) from ../segments.csv
pnpm tsx src/seed.ts

# Subset
pnpm tsx src/seed.ts --only=43
pnpm tsx src/seed.ts --since=80
```

Required env: `ETZ_PDS_URL` (default `https://pds.etzhayyim.com`) + either an authenticated SDK session OR an SDK builder that resolves credentials from the host (deploy-time concern; not in scope here).

## Query

```bash
pnpm tsx src/query.ts --code=43           # one segment
pnpm tsx src/query.ts --prefix=1          # all 1x segments
pnpm tsx src/query.ts --prefix=8 --limit=20
pnpm tsx src/query.ts                      # full list
```

## Verify

```bash
pnpm tsx src/verify.ts at://did:web:etzhayyim.com/com.etzhayyim.apps.openUnispsc.segmentDef/43
```

Returns the Merkle path from the record to the MST root that was anchored to Base L2 via the substrate pipeline. Any client (no credentials) can re-check the proof.

## Tests

```bash
pnpm test
# 68/68 (vitest):
#   - 56 type cases: code format, slug regex (incl. boundary edges), CPC range mapping (all 16 boundaries + gap codes), invalid-code → undefined
#   - 12 seed cases: csvRowToSegmentDef (CPC enrichment, gap handling, whitespace trim, invalid-code throw, invalid-slug throw, empty-name throw); parseCsv (header parsing, sort by code, comma-in-name preservation, missing-header rejection, empty/blank-line input)
```

## Status

| Surface | State |
|---|---|
| Record lexicon `com.etzhayyim.apps.openUnispsc.segmentDef` | ✅ |
| Seeder + helpers + CPC enrichment | ✅ |
| Pure-helper tests | ✅ 68/68 |
| Live PDS seed run | ⏳ pending `ETZ_SEEDER_DID` + PDS auth credentials (Gate 4 of [`OPERATIONAL-DEPLOY.md`](../../../50-infra/OPERATIONAL-DEPLOY.md)) |
| Anchor verify against deployed contract | ⏳ pending Gate 3 EtzhayyimAnchor deploy |
| Family / class / commodity record lexicons | ⏳ future PR (~400 / ~900 / ~70k cardinality) |

## See also

- [`60-apps/etzhayyim-project-open-isco/kotoba/`](../../etzhayyim-project-open-isco/kotoba/) — first kotoba actor (525 ISCO-08 occupations)
- [`60-apps/etzhayyim-project-open-isic/kotoba/`](../../etzhayyim-project-open-isic/kotoba/) — second kotoba actor (428 ISIC Rev.4 4-digit classes)
- [`20-actors/etzhayyim-sdk/`](../../../20-actors/etzhayyim-sdk/) — the substrate-purity SDK
- [`50-infra/mst-projector/`](../../../50-infra/mst-projector/) — Stage 3 of the trust-less verification chain
- [`50-infra/OPERATIONAL-DEPLOY.md`](../../../50-infra/OPERATIONAL-DEPLOY.md) — production runbook
- [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — substrate rules
- [ADR-2605171300](../../../90-docs/adr/2605171300-open-unispsc-generative-agent-fleet.md) — UNSPSC generative agent fleet (the classification runtime that complements this taxonomy publisher)
