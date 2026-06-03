# etzhayyim-project-lawyer

`lawyer.etzhayyim.com` — attorney-facing portal for bengoshi working on matters connected to `lawfirm.etzhayyim.com`. ADR-0029 recursive did:etzhayyim + ADR-0016 legal cluster + ADR-2605180600 attorney portal design.

## Identity

| Layer | Value |
|---|---|
| Handle | `lawyer.etzhayyim.com` |
| did:web | `did:web:lawyer.etzhayyim.com` |
| FIRM_DID | `did:web:lawyer.etzhayyim.com` |
| did:etzhayyim (root) | `did:etzhayyim:{h_lawyer}` ← `bootstrap.sh` で mint、`deps.toml` `[[mitama_actors]]` と対応 |
| nanoid | `334bbd5f` |
| Runtime tier | T2 TS Native (Cloudflare Worker + Hono) |
| Worker path | `60-apps/etzhayyim-project-lawyer/appview/etzhayyim-wasm-lawyer-334bbd5f/` |
| Lexicon SSoT (shared) | `00-contracts/lexicons/com/etzhayyim/apps/lawfirm/` (matters, grants, hearings, time entries) |
| Lexicon SSoT (lawyer) | `00-contracts/lexicons/com/etzhayyim/apps/lawyer/` (attorney-specific operations) |

## Lead Bengoshi

| Person | did:etzhayyim (depth 2) | Role | Status |
|---|---|---|---|
| k.bakshi (クナル) | `did:etzhayyim:{h_lawyer}:{h_bakshi}` | CLO / Lead Bengoshi | `bootstrap.sh` Phase 1 で mintChildDid (kind=pubkey) |

## Active Matters (MVP)

| Case | Matter DID | Status | Client |
|---|---|---|---|
| 鹿児島大学 | `did:etzhayyim:{h_lawyer}:{h_kagoshima_matter}` | engaged (pre-litigation) | etzhayyim Japan (`did:etzhayyim:{h_etzhayyim}`) |

詳細: [cases/kagoshima-univ.md](../etzhayyim-project-kaisya/cases/kagoshima-univ.md)

## Relationship to lawfirm.etzhayyim.com

`lawfirm.etzhayyim.com` は client-facing (intake, matter management, billing)。`lawyer.etzhayyim.com` は attorney-facing (workspace, grant acceptance, AI drafting, time logging, hearing prep)。両者は `com.etzhayyim.apps.lawfirm.*` 共有 lexicon を `firmDid` でスコープして協調する。

- Shared data: `vertex_lawfirm_matter`, `vertex_lawfirm_grant`, `vertex_lawfirm_hearing`, `vertex_lawfirm_time_entry`
- Lawyer-own data: `vertex_lawyer_work_note`, `vertex_lawyer_document_draft`
- Time entries は `com.etzhayyim.apps.lawfirm.recordTimeEntry` (firmDid=`did:web:lawyer.etzhayyim.com`) で lawfirm 側に記録

## Lawyer Portal Service Design

設計詳細の SSoT: `90-docs/adr/2605180600-lawyer-attorney-portal-design.md`

### 6 XRPC Commands (`com.etzhayyim.apps.lawyer.*`)

| NSID | Type | 説明 |
|---|---|---|
| `com.etzhayyim.apps.lawyer.getDashboard` | query | Dashboard snapshot: active matters + pending grants + upcoming hearings + unbilled minutes |
| `com.etzhayyim.apps.lawyer.listAssignedMatters` | query | lead_advocate_did または co_counsel_dids に含まれる matters 一覧 |
| `com.etzhayyim.apps.lawyer.listPendingGrants` | query | status=invited の externalCounselGrant 一覧 |
| `com.etzhayyim.apps.lawyer.acceptGrant` | procedure | Grant 承認 → status=accepted → matter workspace open |
| `com.etzhayyim.apps.lawyer.logWorkNote` | procedure | 暗号化 work note + 請求可能時間をマターに記録 |
| `com.etzhayyim.apps.lawyer.submitDocumentDraft` | procedure | AI 文書草案生成 → ISCO-2611 承認ゲート → draft 保存 |

### lawfirm → lawyer Connection Protocol (externalCounselGrant Flow)

```
lawfirm.createCase (India マーカー検知 または 手動 invite)
  → externalCounselGrant mint (granteeDid=k.bakshi, status=invited)
  → subscribeRepos trigger → lawyer portal に通知
  → /grants ビューに表示
  → 弁護士が com.etzhayyim.apps.lawyer.acceptGrant を呼出
  → grant status=accepted, acceptedAt=now()
  → listAssignedMatters / logWorkNote / submitDocumentDraft が使用可能に
  → 時間記録は com.etzhayyim.apps.lawfirm.recordTimeEntry (firmDid=did:web:lawyer.etzhayyim.com) で法律事務所側に還流
```

Grant record の `capabilities[]` (`read`, `comment`, `uploadDocument`, `propose`, `sign`, `scheduleHearing`) が matter workspace 内の権限を制御する。

### ISCO-2611 Document Approval Gate

ISCO-2611 (Legal Professionals) 準拠: AI 生成法的文書は認定弁護士によるレビュー・承認が必須。

```
draft
  → (LangServer: generate_draft)
under_review
  → (HITL interrupt: reviewerDid に通知)
approved  または  rejected
```

- `generatedContent` は `signal:v1:` フィールド暗号化で保存
- `langserverRunId` で LangServer スレッドと紐付け (監査証跡)
- 承認者 DID は `reviewerDid` パラメータで明示。未指定時は k.bakshi が fallback

### 5 Svelte Views

| Route | View | データソース |
|---|---|---|
| `/` | Dashboard | `getDashboard` — stats cards + 最近のマター + 保留中 grant + 予定 hearing |
| `/matters` | Matter List | `listAssignedMatters` — status/role でフィルタ可 |
| `/matters/[id]` | Matter Workspace | タイムライン sidebar + documents タブ + time entries タブ + AI draft パネル |
| `/grants` | Grants | `listPendingGrants` — 承認 / 辞退カード |
| `/drafts` | Drafts | `submitDocumentDraft` フォーム + draft ステータストラッカー |

全ルートは AT Protocol session JWT で保護。Svelte は `/xrpc/com.etzhayyim.apps.lawyer.*` を `lawyer.etzhayyim.com` Worker BFF に向けて呼出す。

### LangGraph Graphs (LangServer, Vultr k8s)

**`lawyer_matter_workspace`** (Supervisor pattern):
```
Supervisor
  ├── matters_list     — vertex_lawfirm_matter WHERE lead_advocate_did|co_counsel_dids
  ├── grants_list      — vertex_lawfirm_grant WHERE granteeDid AND status=invited
  ├── hearings_list    — vertex_lawfirm_hearing WHERE matterId IN assigned_matters
  └── document_draft   — lawyer_document_drafting サブグラフ呼出
```

**`lawyer_document_drafting`** (Sequential + HITL):
```
load_matter_context
  → generate_draft        (resolveModelId() — RunPod 6000 Ada SSoT)
  → compliance_check      (管轄ルール: vakalatnama 書式 / 裁判所フォーマット)
  → approval_gate         (HITL interrupt → reviewerDid)
  → finalize              (status=approved → vertex_lawyer_document_draft)
```

Checkpointer: PostgreSQL (RisingWave :4566) `AsyncPostgresSaver`。Thread ID = `draft:{draftId}`。

### Data Tables (RisingWave)

**Lawyer-specific tables:**

| Table | Key columns |
|---|---|
| `vertex_lawyer_work_note` | `note_id`, `matter_id`, `lawyer_did`, `firm_did`, `note_type`, `content` (signal:v1:), `billable_minutes`, `tags`, `actor_did`, `org_did`, `created_at` |
| `vertex_lawyer_document_draft` | `draft_id`, `matter_id`, `lawyer_did`, `firm_did`, `document_type`, `status`, `generated_content` (signal:v1:), `reviewer_did`, `langserver_run_id`, `approved_at`, `actor_did`, `org_did`, `created_at` |

全テーブルは ADR-0095 canonical columns (`actor_did`, `org_did`, `at_did`, `created_at`) 必須。

## Governance

- RACI: `responsible` (etzhayyim が owner)
- Classification: `confidential` (attorney-client privilege)
- Compliance: `attorney-client-privilege` / `appi` / `iso-2611`
- AI draft は ISCO-2611 lawyer 承認必須 (ADR-2605180600)
- PII: `content` / `generatedContent` は Tier 3 (`signal:v1:` 暗号化)

## Deploy

```bash
cd 60-apps/etzhayyim-project-lawyer/appview/etzhayyim-wasm-lawyer-334bbd5f
etzhayyim deploy
curl -sI https://lawyer.etzhayyim.com/_app/meta         # 200 確認
curl -s "https://lawyer.etzhayyim.com/xrpc/com.etzhayyim.apps.lawyer.getDashboard?lawyerDid=did:web:lawyer.etzhayyim.com"
```

## Bootstrap Runbook

[bootstrap.sh](bootstrap.sh) 参照。

1. `etzhayyim auth login` — browser OAuth (j.kawasaki)
2. Phase 1: createGuestAccount (lawyer root) + mintChildDid (k.bakshi)
3. Phase 3: registerLawfirm + createEngagement + createMatter

## Reference

- Lawyer lexicons: [`00-contracts/lexicons/com/etzhayyim/apps/lawyer/`](../../00-contracts/lexicons/com/etzhayyim/apps/lawyer/)
  - `listAssignedMatters.json`
  - `listPendingGrants.json`
  - `acceptGrant.json`
  - `getDashboard.json`
  - `logWorkNote.json`
  - `submitDocumentDraft.json`
- Shared lawfirm lexicons: [`00-contracts/lexicons/com/etzhayyim/apps/lawfirm/`](../../00-contracts/lexicons/com/etzhayyim/apps/lawfirm/)
- ADR-2605180600 (Attorney Portal Design): [`90-docs/adr/2605180600-lawyer-attorney-portal-design.md`](../../90-docs/adr/2605180600-lawyer-attorney-portal-design.md)
- ADR-0016 (Legal Cluster): [`90-docs/adr/0016-legal-cluster-topology.md`](../../90-docs/adr/0016-legal-cluster-topology.md)
- ADR-0018 (PII Tier 3): [`90-docs/adr/0018-pii-tier3-cohort-first.md`](../../90-docs/adr/0018-pii-tier3-cohort-first.md)
- ADR-0029 recursive did:etzhayyim: [`90-docs/adr/0029-did-etzhayyim-recursive-hash-merkle.md`](../../90-docs/adr/0029-did-etzhayyim-recursive-hash-merkle.md)
- lawfirm reference impl: [`60-apps/etzhayyim-project-lawfirm/`](../etzhayyim-project-lawfirm/)
