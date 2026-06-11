---
id: doc-2605111400-phase2-app-actor-dispatcher-migration-guide
title: "Phase 2 — App actor: Worker DB callsite → bpmn-dispatcher 経由 XRPC 移行ガイド"
status: active
doc_type: how-to
topic: cf-worker-db-callsite-migration
authoritative: true
last_verified: 2026-05-11
authoritative_for:
  - per-file-migration-pattern
  - nsid-naming-convention-for-domain-writes
  - server-side-handler-placement
  - yatabase-migration-tracking
related:
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605111300-pds-to-pod-bun-container
  - adr-2605080600-langgraph-server-granian-l3-runtime
---

# Phase 2 migration guide — App actor DB callsite

ADR-2605111200 / -2605111300 が完了したあと、`60-apps/` 配下の **99 ファイル** の Worker handler はまだ `createKyselyDb(env.HYPERDRIVE)` を呼び続けており、runtime で `WorkerDBProhibitedError` を投げる。本ガイドはこれを `sdk.pds.xrpc(...)` 経由の server-side dispatch に書き換える per-actor 手順を示す。

## 移行 pattern

### Before (Phase 1 throws)

```ts
import { createKyselyDb } from "@etzhayyim/kotodama-host-sdk";

// Write
const db = createKyselyDb(sdk.env.HYPERDRIVE);
await db.insertInto("vertex_<actor>_<kind>" as any).values({
  vertex_id, sensitivity_ord, owner_did, /* typed fields */
}).execute();

// Read
const row = await db.selectFrom("vertex_<actor>_<kind>" as any)
  .selectAll()
  .where("rkey" as never, "=", rkey)
  .executeTakeFirst();
```

### After (Phase 2 dispatcher)

```ts
// Worker side: 純粋に dispatch だけ。env.HYPERDRIVE は触らない。
await sdk.pds.xrpc("com.etzhayyim.apps.<actor>.<methodName>", {
  /* same payload — server がそのまま vertex_<actor>_<kind> に INSERT */
});

const result = await sdk.pds.xrpc("com.etzhayyim.apps.<actor>.get<Kind>", { rkey });
const row = (result as { row?: unknown })?.row;
```

### NSID 命名規約

| 操作 | NSID パターン | 例 |
|---|---|---|
| 単一 row write | `com.etzhayyim.apps.<actor>.put<Kind>` | `com.etzhayyim.dns.putTransferStep` |
| 単一 row upsert | `com.etzhayyim.apps.<actor>.upsert<Kind>` | `com.etzhayyim.apps.yatabase.upsertLead` |
| 単一 row read by rkey/key | `com.etzhayyim.apps.<actor>.get<Kind>` | `com.etzhayyim.apps.yatabase.getLead` |
| List/query | `com.etzhayyim.apps.<actor>.list<Kind>` | `com.etzhayyim.apps.yatabase.listLeads` |
| Delete | `com.etzhayyim.apps.<actor>.delete<Kind>` | `com.etzhayyim.apps.yatabase.deleteLead` |
| Event emit (audit / metering) | `com.etzhayyim.apps.<actor>.emit<Event>` | `com.etzhayyim.apps.yatabase.emitBillingEvent` |
| Custom domain op (multi-row / transactional) | `com.etzhayyim.apps.<actor>.<verb>` | `com.etzhayyim.apps.yatabase.signupOrg` |

NSID は 3〜4 セグメント。短縮禁止 (root CLAUDE.md §LLM Coding Guardrails)。

## Server-side handler 配置

dispatcher は `vertex_bpmn_lexicon_binding[nsid]` で route 先を決める (ADR-2605080600 §dispatcher routing)。

| Handler 種別 | 配置 | 適合用途 |
|---|---|---|
| **LangGraph node** (`kotodama` graph) | `kotodama.<actor>.graph.py` の `@graph.node` | LLM / tool 呼び出し / multi-step / interrupt |
| **SpiffWorkflow BPMN worker** (`kotodama.spiff_worker`) | `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/<actor>/*.bpmn` + worker task | BPMN-native (timer / boundary / audit-friendly) |
| **pyzeebe / generic primitive** | `kotodama/zeebe_worker_main.py` の `generic.db.insert/select` で汎用 INSERT/SELECT | 単純 CRUD のみ |
| **Direct C-path** | `kotodama/yoro_social.py` の `insert_social_post_record` 等 | `vertex_repo_record` への social write |

新規 NSID 追加手順:

1. `00-contracts/lexicons/com/etzhayyim/apps/<actor>/<method>.json` を作成 (input/output schema)
2. `node 70-tools/scripts/contract/gen-lexicon-nsid-types.mjs` で TS 型再生成
3. server-side handler を上表のどこかに実装
4. `vertex_bpmn_lexicon_binding` row を追加 (どの routing target に流すか宣言)
5. Worker handler を本ガイドの "After" pattern に置換

## yorishiro squarespace pilot (reference)

`60-apps/etzhayyim-project-yorishiro/appview/etzhayyim-wasm-yorishiro-squarespace-sqddf3sp/src/app.ts`

3 DB callsite を以下の NSID に置換 (server-side handler は別 PR):

| 旧 callsite | 新 NSID | payload shape |
|---|---|---|
| `db.insertInto("vertex_dns_transfer_step")...values(stepRow)` (line 50) | `com.etzhayyim.dns.putTransferStep` | `{vertex_id, transferRequestUri, step, status, actorDid, occurredAt, errorMessage?, bindZoneFileUri?, cfTransferId?}` |
| `db.selectFrom("vertex_ai_etzhayyim_apps_dns_transferRequest")...where("rkey","=",rkey)` (line 73) | `com.etzhayyim.dns.getTransferRequest` | `{rkey}` → `{request?: {domain, status, ...}}` |
| `db.insertInto("vertex_dns_transfer_outcome")...values(outcomeRow)` (line 137) | `com.etzhayyim.dns.putTransferOutcome` | `{vertex_id, transferRequestUri, domain, result, zoneDid?, cloudflareZoneId?, failureReason?, completedAt}` |

### Diff (mechanical)

```diff
- import { createKyselyDb, createWorkerExport, nowISO, type HostSDK } from "@etzhayyim/kotodama-host-sdk";
+ import { createWorkerExport, nowISO, type HostSDK } from "@etzhayyim/kotodama-host-sdk";

  async function emitStep(sdk: HostSDK, transferRequestUri: string, step: StepName, status: ..., extra: ... = {}) {
    const rkey = `${step}-${Date.now().toString(36)}`;
-   await createKyselyDb().insertInto("vertex_dns_transfer_step" as any).values({
-     vertex_id: `at://${SQ_EXPORTER_DID}/com.etzhayyim.dns.transferStep/${rkey}`,
-     sensitivity_ord: 2, owner_did: SQ_EXPORTER_DID,
-     transfer_request_uri: transferRequestUri,
-     step, status, actor_did: SQ_EXPORTER_DID, occurred_at: nowISO(),
-     ...(extra.errorMessage !== undefined ? { error_message: extra.errorMessage } : {}),
-     ...(extra.bindZoneFileUri !== undefined ? { bind_zone_file_uri: extra.bindZoneFileUri } : {}),
-     ...(extra.cfTransferId !== undefined ? { cf_transfer_id: extra.cfTransferId } : {}),
-   }).execute();
+   await sdk.pds.xrpc("com.etzhayyim.dns.putTransferStep", {
+     rkey,
+     transferRequestUri,
+     step,
+     status,
+     actorDid: SQ_EXPORTER_DID,
+     occurredAt: nowISO(),
+     errorMessage: extra.errorMessage,
+     bindZoneFileUri: extra.bindZoneFileUri,
+     cfTransferId: extra.cfTransferId,
+   });
  }
```

完全な diff は per-actor migration PR で commit する (本 doc では割愛)。

## yatabase audit (21 files, biggest single actor)

`60-apps/etzhayyim-project-yatabase/src/`. このディレクトリだけで Phase 2 の **22%** を占めるため、actor 単独で 1 PR を立てるのが妥当。各ファイルの table 触り表:

| File | refs | lines | tables touched | 推奨 NSID prefix |
|---|---:|---:|---|---|
| `agents/chikada.ts` | 3 | 173 | vertex_audit_log | `com.etzhayyim.apps.yatabase.chikada.*` |
| `agents/nishino.ts` | 3 | 312 | vertex_api_key, vertex_billing_event, vertex_email_outbox, vertex_lead | `com.etzhayyim.apps.yatabase.nishino.*` |
| `agents/registry.ts` | 2 | 311 | vertex_lead, vertex_yata_agent_run, vertex_yata_qa_run | `com.etzhayyim.apps.yatabase.registry.*` |
| `agents/sakamoto.ts` | 3 | 212 | vertex_email_outbox | `com.etzhayyim.apps.yatabase.sakamoto.*` |
| `agents/tanaka.ts` | 3 | 241 | vertex_audit_log, vertex_billing_event, vertex_email_outbox, vertex_yata_qa_run | `com.etzhayyim.apps.yatabase.tanaka.*` |
| `audit-log.ts` | 4 | 178 | vertex_audit_log | `com.etzhayyim.apps.yatabase.emitAuditLog`, `listAuditLog` |
| `auth-signup.ts` | 7 | 262 | vertex_api_key, vertex_demo | `com.etzhayyim.apps.yatabase.signup`, `issueApiKey` |
| `billing-stripe.ts` | 4 | 406 | vertex_billing_event, vertex_org_plan | `com.etzhayyim.apps.yatabase.emitBillingEvent`, `getOrgPlan` |
| `data-rights.ts` | 4 | 307 | vertex_api_key, vertex_billing_event, vertex_org_plan, vertex_yata_blob | `com.etzhayyim.apps.yatabase.exportUserData`, `purgeUserData` |
| `email-outbox.ts` | 3 | 619 | vertex_email_outbox | `com.etzhayyim.apps.yatabase.queueEmail`, `markEmailDelivered` |
| `hyperdrive-reads.ts` | 3 | 258 | vertex_yata_blob, vertex_yata_bucket | `com.etzhayyim.apps.yatabase.list<*>` (read helpers) |
| `invoice.ts` | 3 | 399 | vertex_billing_event | `com.etzhayyim.apps.yatabase.generateInvoice`, `listInvoices` |
| `leads.ts` | 4 | 704 | vertex_lead | `com.etzhayyim.apps.yatabase.upsertLead`, `listLeads`, `getLead`, `deleteLead` |
| `metering.ts` | 4 | 197 | vertex_billing_event | `com.etzhayyim.apps.yatabase.recordUsage`, `getUsage` |
| `org-members.ts` | 4 | 309 | vertex_api_key | `com.etzhayyim.apps.yatabase.addMember`, `removeMember`, `listMembers` |
| `plan-quota.ts` | 3 | 262 | vertex_billing_event, vertex_org_plan | `com.etzhayyim.apps.yatabase.getQuota`, `enforceQuota` |
| `public-acl.ts` | 2 | 157 | vertex_yata_bucket | `com.etzhayyim.apps.yatabase.setBucketAcl`, `getBucketAcl` |
| `s3-sigv4.ts` | 3 | 442 | vertex_api_key | `com.etzhayyim.apps.yatabase.signS3Request` |
| `schema-describe.ts` | 4 | 134 | (introspection) | `com.etzhayyim.apps.yatabase.describeSchema` |
| `status.ts` | 4 | 287 | vertex_yata_agent_run, vertex_yata_qa_run | `com.etzhayyim.apps.yatabase.status` |
| `team.ts` | 4 | 225 | vertex_yata_agent_run | `com.etzhayyim.apps.yatabase.team` |

**Estimated work**: ~70 call sites total, ~21 new NSID lexicons, ~21 server-side handlers (kotodama primitives or LangGraph nodes). 推定 2-3 day-PR per a small team of 1-2 developers.

## 全 actor 一覧 (99 files)

| Actor | files | Phase 2 priority |
|---|---:|---|
| yatabase | 21 | high (newest, well-defined) |
| yorishiro | 4 | medium (good pilot, 1-handler-per-file) |
| tsukuru, shinkansen, os-messaging, open-kyber, kyber-qzzg06nh, insatsu | 2 each | medium |
| yukkuri, yoro, xlsx, webya, watashi, toshi-kozan, tenso, society6, smishing, site, shinshi, shinka, shigotoba, seibutsu, sanctions, saiban, repository, pptx, playwright, pachinko, open-water, open-swift, open-rail, open-power, open-ports, open-ossekai, open-network, open-jpn-gov, … (~36 actors total) | 1 each | low (trivial migrations, batch in one PR) |

Total app-side files in scope: **99**. SDK glue: 3. Total: 102.

## Tracking

`deps.toml [[migrations]] phase-2-app-actor-dispatcher-migration` で per-actor 進捗を tracking。`done_actors` / `in_progress_actors` / `blocked_actors` を更新する。

各 actor PR の DoD:

- [ ] 全 `createKyselyDb` callsite が `sdk.pds.xrpc(...)` に置換済
- [ ] 対応 NSID lexicon JSON が `00-contracts/lexicons/com/etzhayyim/apps/<actor>/` に追加
- [ ] `gen-lexicon-nsid-types.mjs` を実行して型再生成
- [ ] server-side handler が一カ所 (kotodama primitive / LangGraph node / Spiff BPMN) に存在
- [ ] `vertex_bpmn_lexicon_binding` row 追加 (どこに route するか宣言)
- [ ] Smoke test: actor の代表的 XRPC が live で動く

## See also

- ADR-2605111200 (CF Worker edge-only)
- ADR-2605111300 (PDS pod migration — infra Worker 系も最終的に同じ運命)
- ADR-2605080600 (LangGraph Server + Granian L3) — main routing target
- ADR-2605081200 (SpiffWorkflow BPMN replacement) — BPMN-native route
- `90-docs/adr/2604282300-cf-worker-edge-layer-zeebe-rw-udf-business-logic.md` §Addendum 2026-04-30 — dispatcher 3-way routing reference
