---
id: cohort-seed-procedure-spec-260414
title: "com.etzhayyim.cohort.seed — PDS Procedure Implementation Spec (ADR-0026 Iter 11)"
status: active
doc_type: how-to
topic: cohort-seed
authoritative: false
last_verified: 2026-04-14
related:
  - adr-0026-agent-only-reverse-identity-topology
  - cohort-coverage-evaluation-baseline-260414
supersedes: []
superseded_by: []
---

# Goal

`com.etzhayyim.cohort.seed` procedure (`00-contracts/lexicons/com/etzhayyim/cohort/seed.json`) の実装手順を固定。
`etzhayyim cohort seed --segment <jsonld>` CLI が XRPC 経由で PDS に call して
`vertex_cohort_actor` row を insert する経路。

# Input / Output (lexicon 既定)

```typescript
// Input (from seed.json)
{
  segmentJsonld: string,      // 構造化された demographic segment (JSON-LD)
  kAnonymity: number,         // >= 50
  fissionEnabled?: boolean,   // default false
  policyRef?: string,         // 将来的な policy DID
}

// Output
{
  did: string,                // 生成 / 解決された did:plc:pending-*
  handle: string,             // cohort-{nano}.etzhayyim.com
  signatureUri: string,       // at://...self
  genesisAt: string,
}
```

# Implementation Steps

## 1. NSID 検証

`StrictCommandNSID<"com.etzhayyim.cohort.seed">` compile-time guard で lexicon 存在を担保。
生成済み `LEXICON_NSID["com.etzhayyim.cohort.seed"]` を使う。

## 2. segment_hash 導出

```typescript
import { parseSegmentHash } from '@etzhayyim/magatama-host-sdk/cohort';

async function deriveSegmentHash(segmentJsonld: string): Promise<string> {
  // 1. canonicalize JSON-LD (URDNA2015 相当。当面は sorted-key JSON で代用)
  const canonical = JSON.stringify(JSON.parse(segmentJsonld), Object.keys(JSON.parse(segmentJsonld)).sort());
  // 2. SHA-256
  const buf = new TextEncoder().encode(canonical);
  const hash = await crypto.subtle.digest('SHA-256', buf);
  // 3. derive pcfL1/role/industry/seniority/locale from JSON-LD claims
  //    (segmentJsonld に @type=Cohort + pcfL1/role/locale 必須)
  const obj = JSON.parse(segmentJsonld);
  const parts = [
    `pcfL1=${obj.pcfL1}`,
    `role=${obj.role}`,
    obj.industry ? `industry=${obj.industry}` : null,
    obj.seniority ? `seniority=${obj.seniority}` : null,
    `locale=${obj.locale}`,
  ].filter(Boolean);
  return `sha256:${parts.join(';')}`;  // matches CohortSegment parser
}
```

## 3. handle / DID mint

```typescript
const nano = genID('coh').slice(-8); // 8-char, base36
const handle = `cohort-${nano}.etzhayyim.com`;
// Phase 5 (plc.etzhayyim.com live) 後: call com.etzhayyim.plc.migrateActor with genesis op
// 暫定: "did:plc:pending-" + nano
const did = `did:plc:pending-${nano}`;
```

## 4. k-anonymity 検証

```typescript
if (input.kAnonymity < 50) {
  throw new LexiconValidationError('k_anonymity must be >= 50 (ADR-0026 Phase A)');
}
```

## 5. `vertex_cohort_actor` INSERT

```typescript
const db = createKyselyDb(env.HYPERDRIVE);
await db.insertInto('vertex_cohort_actor')
  .values({
    vertex_id: did,
    cohort_did: did,
    handle,
    kind: 'cohort',
    segment_hash: segmentHash,
    k_anonymity: input.kAnonymity,
    fission_enabled: input.fissionEnabled ?? false,
    derived_from: null,
    status: 'pending-plc-genesis',
    signature_uri: `at://${handle}/com.etzhayyim.cohort.signature/self`,
    genesis_at: new Date().toISOString(),
    owner_did: 'did:web:cohort-watchdog.etzhayyim.com',
    created_date: new Date(),
  })
  .execute();
```

## 6. Signature record write

cohort actor の at:// repo に `com.etzhayyim.cohort.signature` を self rkey で write:

```typescript
await sdk.pds.dispatch({
  type: 'com.atproto.repo.createRecord',
  did,
  collection: 'com.etzhayyim.cohort.signature',
  rkey: 'self',
  record: {
    segmentHash,
    demographicVector: input.segmentJsonld,
    kAnonymity: input.kAnonymity,
    policyRef: input.policyRef ?? null,
    fissionEnabled: input.fissionEnabled ?? false,
    createdAt: new Date().toISOString(),
  },
});
```

## 7. OCEL genesis emit (cohort-watchdog との対称)

```typescript
await forwardOcelToApqc({
  cohortDid: did,
  eventType: 'cohort.genesis' as any,  // 型を union 拡張する
  kProxy: input.kAnonymity,
  apqcL1: parseSegmentHash(segmentHash)?.pcfL1 ?? null,
  apqcDid: apqcL1 ? `did:web:kyber-projector.etzhayyim.com:apqc:${apqcL1}` : null,
});
```

# TODO before implementation

1. `forwardOcelToApqc` の eventType union に `cohort.genesis` を追加 (現 `cohort.kReevaluated` のみ)
2. PDS handler file に `sdk.app.command(nsid('com.etzhayyim.cohort.seed'), ...)` を追加
3. `deps.toml [[cohort_actors]]` への書き戻し reconciliation (optional — runtime は `vertex_cohort_actor` が SSoT)

# References

- `00-contracts/lexicons/com/etzhayyim/cohort/seed.json`
- `20-actors/magatama/sdk/magatama-host-sdk/src/cohort.ts`
- `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts`
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
