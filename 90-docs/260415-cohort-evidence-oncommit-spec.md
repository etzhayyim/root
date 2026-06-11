---
id: cohort-evidence-oncommit-spec-260415
title: "com.etzhayyim.cohort.evidence onCommit Handler Spec (ADR-0026 Phase B)"
status: active
doc_type: how-to
topic: cohort-evidence
authoritative: false
last_verified: 2026-04-15
related:
  - adr-0026-agent-only-reverse-identity-topology
  - cohort-coverage-evaluation-baseline-260414
supersedes: []
superseded_by: []
---

# Goal

Phase B: `com.etzhayyim.cohort.evidence` の commit → APQC projector OCEL emit 経路を固定。

# Invocation path

PDS subscribeRepos pipeline 内の `onCommit(commit)` が ADR-0026 collection を検出した時に fire する。

```typescript
// hypothetical hook inside the PDS commit dispatcher
async function handleCohortEvidenceCommit(
  env: Env,
  commit: {
    collection: string;
    rkey: string;
    action: 'create' | 'update' | 'delete';
    record: {
      cohortDid: string;
      evidenceHash: string;
      signalKind: string;
      posterior?: number;
      judgeAgreement?: boolean;
      tier: 'tier1-hashed';
      observedAt: string;
    };
  },
): Promise<void> {
  if (commit.collection !== 'com.etzhayyim.cohort.evidence') return;
  if (commit.action !== 'create') return;

  // 1. Fetch cohort actor to resolve pcfL1 / fission_enabled
  const db = createKyselyDb(env.HYPERDRIVE);
  const cohort = await db
    .selectFrom('vertex_cohort_actor' as any)
    .select(['segment_hash', 'fission_enabled'] as any[])
    .where('cohort_did' as any, '=', commit.record.cohortDid)
    .limit(1)
    .execute() as any[];
  if (cohort.length === 0) return;

  const segmentHash = String(cohort[0].segment_hash ?? '');
  const fissionEnabled = Boolean(cohort[0].fission_enabled ?? false);
  const pcfL1 = extractPcfL1(segmentHash);

  // 2. Count prior evidence to determine genesis vs accrued
  const priorCount = (await db
    .selectFrom('mv_cohort_identity_posterior' as any)
    .select(['evidence_count'] as any[])
    .where('cohort_did' as any, '=', commit.record.cohortDid)
    .limit(1)
    .execute() as any[])[0]?.evidence_count ?? 0;

  // 3. Derive OCEL event type using host-sdk helper
  const eventType = deriveCohortEventType({
    evidenceCountBefore: Number(priorCount),
    posterior: commit.record.posterior ?? null,
    judgeAgreement: commit.record.judgeAgreement ?? null,
    kProxy: null,                       // watchdog is authoritative for k-drift
    fissionEnabled,
    didFission: false,
  });

  // 4. Forward to projector
  await forwardOcelToApqc({
    cohortDid: commit.record.cohortDid,
    eventType,                                         // genesis / accrued / fissionReady
    kProxy: commit.record.posterior ?? 0,              // overload: posterior into kProxy slot
    apqcL1: pcfL1,
    apqcDid: pcfL1 ? `did:web:kyber-projector.etzhayyim.com:apqc:${pcfL1}` : null,
  });
}
```

# Open issues

- `forwardOcelToApqc` の `kProxy` 引数を `numericPayload` 等に rename して意味を分離するべき (現状は k_proxy と posterior を同じ slot で運んでいる)
- `deriveCohortEventType` は `@etzhayyim/kotodama-host-sdk/cohort` からの import。PDS worker bundle に含まれる
- Phase C の `cohort.fission` は別経路 (別 handler、ADR-0026 Phase C fission procedure)

# Integration points

- Existing commit dispatcher: `50-infra/cloudflare/workers/atproto/src/core.ts` もしくは PDS subscribeRepos handler chain
- NSID 分岐は既存 handler 群 (`handlers/feed.ts`, `handlers/infra.ts`) に似た pattern で挿入

# References

- `00-contracts/lexicons/com/etzhayyim/cohort/evidence.json`
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/cohort.ts` (`deriveCohortEventType`)
- `50-infra/cloudflare/workers/atproto/src/agent/cohort-watchdog.ts` (`forwardOcelToApqc`)
- `90-docs/adr/0026-agent-only-reverse-identity-topology.md`
