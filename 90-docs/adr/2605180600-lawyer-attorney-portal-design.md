---
id: adr-2605180600-lawyer-attorney-portal-design
title: "ADR-2605180600: lawyer.etzhayyim.com — Attorney Portal Design (Pregel + LangServer + Svelte)"
status: active
doc_type: adr
topic: lawyer-portal
authoritative: true
last_verified: 2026-05-18
authoritative_for:
  - lawyer.etzhayyim.com service design and UI view structure
  - lawfirm↔lawyer connection protocol (externalCounselGrant flow)
  - ISCO-2611 document approval gate design
  - LangGraph attorney workspace graph definitions
  - com.etzhayyim.apps.lawyer.* lexicon namespace ownership
related:
  - adr-0016-legal-cluster-topology
  - adr-0018-pii-tier3-cohort-first
  - adr-0079-lawfirm-india-intake-auto-route
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605080600-langgraph-server-granian-l3-runtime
supersedes: []
superseded_by: []
---

# Context

`lawfirm.etzhayyim.com` serves clients with intake, matter management, and billing. The platform lacked an attorney-facing workspace. Attorneys (bengoshi) — starting with k.bakshi (`did:etzhayyim:{h_lawyer}:{h_bakshi}`) as Lead CLO — need a dedicated portal to:

- Accept or decline external counsel grant invitations from lawfirm.etzhayyim.com
- View and work on assigned matters (as lead advocate or co-counsel)
- Log work notes and time entries against matters
- Submit AI-assisted document drafts that pass the ISCO-2611 lawyer-review compliance gate before finalization
- Prepare for upcoming hearings

The existing CLAUDE.md stated "独自 `com.etzhayyim.apps.lawyer.*` は作らない" as an early MVP constraint. This ADR supersedes that constraint: as the attorney portal matures into a standalone appview at `lawyer.etzhayyim.com`, a dedicated lexicon namespace is required to model attorney-specific operations that have no natural home in the client-facing `com.etzhayyim.apps.lawfirm.*` namespace.

# Decision

## 1. Lexicon Namespace

Create `com.etzhayyim.apps.lawyer.*` as the authoritative namespace for attorney-facing operations. The `com.etzhayyim.apps.lawfirm.*` namespace remains the SSoT for shared matter/grant/hearing/time-entry records. Lawyer lexicons are read/write facades that operate on those shared records, scoped by `firmDid=did:web:lawyer.etzhayyim.com`.

### 6 XRPC Commands

| NSID | Type | Description |
|---|---|---|
| `com.etzhayyim.apps.lawyer.getDashboard` | query | Snapshot: active matters + pending grants + upcoming hearings + unbilled minutes |
| `com.etzhayyim.apps.lawyer.listAssignedMatters` | query | Matters where lawyerDid is `lead_advocate_did` OR in `co_counsel_dids` |
| `com.etzhayyim.apps.lawyer.listPendingGrants` | query | `externalCounselGrant` records with `status=invited` targeting this lawyerDid |
| `com.etzhayyim.apps.lawyer.acceptGrant` | procedure | Flip grant `status=accepted`, open matter workspace access |
| `com.etzhayyim.apps.lawyer.logWorkNote` | procedure | Write encrypted work note + optional billable time to matter |
| `com.etzhayyim.apps.lawyer.submitDocumentDraft` | procedure | Trigger AI draft generation → ISCO-2611 approval gate → store in `vertex_lawyer_document_draft` |

Time entries flow back through the shared lexicon: `com.etzhayyim.apps.lawfirm.recordTimeEntry` with `firmDid=did:web:lawyer.etzhayyim.com`.

## 2. lawfirm → lawyer Connection Protocol

```
lawfirm.createCase (India / external-counsel marker detected)
  → auto-mint externalCounselGrant (granteeDid=k.bakshi, status=invited)
  → lawyer subscribeRepos trigger fires on grant collection
  → lawyer portal shows grant in /grants view
  → attorney calls com.etzhayyim.apps.lawyer.acceptGrant
  → grant status=accepted, acceptedAt=now()
  → attorney can now call listAssignedMatters, logWorkNote, submitDocumentDraft
  → time entries loop back via com.etzhayyim.apps.lawfirm.recordTimeEntry (firmDid=did:web:lawyer.etzhayyim.com)
```

The grant record (`com.etzhayyim.apps.lawfirm.externalCounselGrant`) is the canonical authority object. Its `capabilities[]` array (`read`, `comment`, `uploadDocument`, `propose`, `sign`, `scheduleHearing`) governs what the attorney may do in the matter workspace.

Auto-routing: when `lawfirm.createCase` detects an India jurisdiction marker (`jurisdiction="IND"` or intake language classifier `lang=hi|bn|ta|te|mr`), the dispatcher mints the grant automatically without manual invite. This is the ADR-0036 India intake auto-route pattern extended to the lawyer portal.

## 3. ISCO-2611 Document Approval Gate

ISCO-2611 (Legal Professionals — Lawyers) requires that AI-generated legal documents are reviewed and approved by a licensed attorney before use. The gate is implemented as a LangGraph HITL (Human-In-The-Loop) checkpoint node.

State machine:

```
draft
  → (LangServer: generate_draft node)
under_review
  → (HITL interrupt: reviewerDid notified via logWorkNote + app.bsky.feed.post)
approved  (reviewer calls approveDocumentDraft — future lexicon)
  OR
rejected  (reviewer calls rejectDocumentDraft — future lexicon)
```

The `vertex_lawyer_document_draft` table records the full lifecycle. `generatedContent` is stored field-encrypted (`signal:v1:` envelope) at rest. The `langserverRunId` links to the LangServer thread for audit.

## 4. LangGraph Graphs

### `lawyer_matter_workspace` (Supervisor pattern)

```
Supervisor
  ├── matters_list     — query vertex_lawfirm_matter WHERE lead_advocate_did|co_counsel_dids
  ├── grants_list      — query vertex_lawfirm_grant WHERE granteeDid AND status=invited
  ├── hearings_list    — query vertex_lawfirm_hearing WHERE matterId IN assigned_matters
  └── document_draft   — invoke lawyer_document_drafting subgraph
```

### `lawyer_document_drafting` (Sequential + HITL)

```
load_matter_context
  → generate_draft        (LLM call: resolveModelId() — RunPod 6000 Ada SSoT)
  → compliance_check      (jurisdiction-aware rules: vakalatnama form / court format)
  → approval_gate         (HITL interrupt → reviewerDid)
  → finalize              (status=approved, write to vertex_lawyer_document_draft)
```

LangGraph checkpointer: PostgreSQL (Kotoba/Datomic 4566) via `AsyncPostgresSaver`. Thread ID = `draft:{draftId}`.

## 5. UI Views (Svelte, 5 routes)

| Route | View | Primary Data |
|---|---|---|
| `/` | Dashboard | `getDashboard` — stats cards + recent matters + pending grants + hearings |
| `/matters` | Matter List | `listAssignedMatters` — filterable by status/role |
| `/matters/[id]` | Matter Workspace | Timeline sidebar + documents tab + time entries tab + AI draft panel |
| `/grants` | Grants | `listPendingGrants` — accept / decline cards |
| `/drafts` | Drafts | `submitDocumentDraft` form + draft status tracker |

All routes are protected by AT Protocol session JWT. The Svelte app calls `/xrpc/com.etzhayyim.apps.lawyer.*` against the lawyer Worker BFF at `lawyer.etzhayyim.com`.

## 6. Data Tables (Kotoba/Datomic)

### New tables (lawyer-specific)

| Table | Key columns | Description |
|---|---|---|
| `vertex_lawyer_work_note` | `note_id`, `matter_id`, `lawyer_did`, `firm_did`, `note_type`, `content` (signal:v1:), `billable_minutes`, `tags`, `created_at` | Encrypted attorney work notes |
| `vertex_lawyer_document_draft` | `draft_id`, `matter_id`, `lawyer_did`, `firm_did`, `document_type`, `status`, `generated_content` (signal:v1:), `reviewer_did`, `langserver_run_id`, `created_at`, `approved_at` | AI-assisted draft lifecycle |

### Shared tables (read from lawfirm namespace)

- `vertex_lawfirm_matter` — matter records (firmDid-scoped)
- `vertex_lawfirm_grant` — externalCounselGrant records
- `vertex_lawfirm_hearing` — scheduled hearings
- `vertex_lawfirm_time_entry` — billable time entries

All tables follow ADR-0095 canonical columns: `actor_did`, `org_did`, `at_did`, `created_at`.

## 7. Identity

| Layer | Value |
|---|---|
| Handle | `lawyer.etzhayyim.com` |
| did:web | `did:web:lawyer.etzhayyim.com` |
| FIRM_DID | `did:web:lawyer.etzhayyim.com` |
| nanoid | `334bbd5f` |
| Runtime tier | T2 TS Native (CF Worker + Hono) |
| Worker path | `60-apps/etzhayyim-project-lawyer/appview/etzhayyim-wasm-lawyer-334bbd5f/` |
| Lead bengoshi | k.bakshi — `did:etzhayyim:{h_lawyer}:{h_bakshi}` |

## 8. GitHub Repository & Engineer Workflow (2026-05-18)

| Repo | URL | Visibility |
|---|---|---|
| `etzhayyim/lawfirm` | https://github.com/etzhayyim/lawfirm | private |
| `etzhayyim/lawyer` | https://github.com/etzhayyim/lawyer | private |

**Engineer access** (push permission): `gw-cKd` (chikada) / `tanaka4B2` (tanaka) / `dir445` (nishino)

### lawfirm repo layout

```
worker/          ← CF Worker: src/app.ts + svelte/ (all pages)
python/
  primitives/    ← lawfirm_billing / intake / translate / tenant / ... (12 files)
lexicons/lawfirm/ ← 65 AT Protocol lexicon JSON (NSID contract SSoT)
.github/workflows/deploy.yml  ← push to main → wrangler deploy
```

### lawyer repo layout

```
worker/          ← CF Worker: src/app.ts + svelte/ (5 views)
python/
  primitives/lawyer_workspace.py    ← 6 pyzeebe task handlers
  langgraph/
    lawyer_matter_workspace.py      ← Supervisor graph (assistant_id: lawyer-matter-workspace)
    lawyer_document_drafting.py     ← ISCO-2611 HITL graph (assistant_id: lawyer-document-drafting)
lexicons/lawyer/  ← 6 AT Protocol lexicon JSON
.github/workflows/deploy.yml
```

### CI/CD

- `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` secrets set in both repos
- PR → `build-svelte` only (no deploy); push to `main` → `build-svelte` → `deploy`
- Python changes trigger K8s rolling update (bpmn-dispatcher pod restart)

### Sync policy

These repos are standalone copies of the relevant monorepo subtrees. Changes merged to `main` in each repo must be manually backported to `etzhayyim-root` (monorepo stays as the authoritative source for shared infra). A `git subtree` automation is tracked in `deps.toml [[migrations]] lawfirm-lawyer-repo-monorepo-sync`.

## 9. PII Handling

Attorney notes and generated document content are Tier 3 PII (attorney-client privileged). All `content` and `generatedContent` fields are stored with `signal:v1:` field encryption. The reviewer's DID and approval decisions are Tier 2 (firmDid-scoped, not federated). Matter party identities follow ADR-0018 cohort-first principles.

# Consequences

## Positive

- Attorneys get a dedicated workspace with grant acceptance, matter browsing, AI drafting, and time logging in one portal
- ISCO-2611 gate is enforced at the LangGraph level — no approved document bypasses human review
- `externalCounselGrant` remains the canonical authority object (no duplication of grant logic)
- Time entries flow back to lawfirm via shared lexicon, enabling unified billing view

## Negative / Trade-offs

- Two lexicon namespaces (`lawfirm.*` + `lawyer.*`) must stay in sync as matter/grant schemas evolve
- HITL approval gate adds latency to document finalization (acceptable for legal domain)
- `lawyer_document_drafting` graph requires LangServer pod availability (RunPod 6000 Ada SSoT per ADR-2605010000)

## Future Work

- `approveDocumentDraft` / `rejectDocumentDraft` lexicons (reviewer-side procedures)
- Hearing prep assistant graph (`lawyer_hearing_prep`) — case law retrieval via hanrei.etzhayyim.com
- Multi-firm support (k.bakshi handling grants from multiple lawfirm tenants)
- E-signature integration via `com.etzhayyim.apps.lawfirm.eSignRequest` (shared lexicon)

# References

- Lexicons: `00-contracts/lexicons/com/etzhayyim/apps/lawyer/`
- Shared lawfirm lexicons: `00-contracts/lexicons/com/etzhayyim/apps/lawfirm/`
- ADR-0016: Legal Cluster Topology → `90-docs/adr/0016-legal-cluster-topology.md`
- ADR-0018: PII Tier 3 + Cohort-First → `90-docs/adr/0018-pii-tier3-cohort-first.md`
- ADR-0036: Lawfirm India Intake Auto-Route → `90-docs/adr/0036-lawfirm-india-intake-auto-route.md`
- ADR-2605010000: RunPod 6000 Ada Unified Pod (LLM SSoT) → `90-docs/adr/2605010000-runpod-6000ada-unified-pod.md`
- ADR-2605080600: LangGraph Server + Granian L3 Runtime → `90-docs/adr/2605080600-langgraph-server-granian-l3-runtime.md`
- ADR-2605111200: CF Worker Edge-Only (no RW connection) → `90-docs/adr/2605111200-cf-worker-edge-only-no-rw-connection.md`
- Worker path: `60-apps/etzhayyim-project-lawyer/appview/etzhayyim-wasm-lawyer-334bbd5f/`
- Project CLAUDE.md: `60-apps/etzhayyim-project-lawyer/CLAUDE.md`
