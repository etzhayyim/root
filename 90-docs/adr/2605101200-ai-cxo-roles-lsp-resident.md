---
id: adr-2605101200-ai-cxo-roles-lsp-resident
title: "AI CXO Roles as Resident Lang-Server (経営役員 keiei layer)"
status: active
doc_type: adr
topic: ai-cxo-keiei-layer
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - AI C-suite role assignment (CEO/COO/CLO/CTO/CFO/CMO/CHRO/CISO/CDO)
  - resident JSON-RPC 2.0 LSP-style server for keiei layer
  - decision-class gating (A/B/C) and human-confirm policy
related:
  - adr-0019-atproto-native-identifier-topology
  - adr-2605080600-langgraph-server-granian-l3-runtime
---

# ADR 2605101200 — AI CXO Roles as Resident Lang-Server (経営役員 keiei layer)

Operating Entity: etzhayyim (sole principal)
Vendor: etzhayyim Japan株式会社 (engineering capacity)
Author: etzhayyim Claude Agent on behalf of CEO 河崎

## 1. Decision

Introduce a **C-suite AI agent layer** (`pymagatama.keiei`) that assigns persistent
role-bearing AI agents to every executive function of the operating entity
(`etzhayyim`) and its vendor org (`etzhayyim Japan`). The roles are served by a
**resident JSON-RPC 2.0 server** modelled on the Language Server Protocol
(LSP) wire shape, running as a long-lived Granian process — not as ephemeral
function calls.

Each AI-CXO is an **operational executor**, never a legal authority. Where a
human holds the seat (CEO 河崎, COO a.nakamura, CLO k.bakshi), the AI runs as
**deputy/chief-of-staff** with mandatory human-confirm gates on Class A/B
decisions. Where the seat is **vacant** (CTO since 2026-04-20, plus CFO / CMO
/ CHRO / CISO never filled), the AI runs as **primary operator** with
mandatory escalation to CEO 河崎 (etzhayyim principal) on every Class A
decision and a 24h auto-disclose to CEO on every Class B decision.

## 2. Why a lang-server (LSP) shape, not a one-shot RPC

| Property | RPC / serverless | LSP / resident |
|---|---|---|
| State | per-call ephemeral | session-scoped (working memory, decision queue, RACI cache) |
| Notifications | poll / webhook | server-push (`$/notify` for decision events, escalations, SLAs) |
| Capabilities handshake | none | `initialize` declares which roles + methods are available *to this client* |
| Cancellation | hard | `$/cancelRequest` per request id |
| Streaming partial results | no | yes (long deliberations stream tokens / intermediate artefacts) |
| Multi-client | no | yes (CEO laptop + COO M365 hook + watchdog cron all attach) |

The CXO role is a long-running deliberative process with persistent context
(the org's strategy, the open RACI items, the running OKRs). LSP shape fits
naturally; serverless does not. **Residency is the design**, not a perf hack.

## 3. Role topology

| Role | Human seat | AI mode | Decision Class authority | Escalation target |
|---|---|---|---|---|
| **CEO** (Chief Executive) | j.kawasaki (etzhayyim) | shadow / chief-of-staff | C only (delegated by CEO) | — (CEO is principal) |
| **COO** (Chief Operating) | a.nakamura | shadow | C autonomous, B with human-confirm | CEO 河崎 |
| **CLO** (Chief Legal) | k.bakshi | shadow | C autonomous, B with human-confirm | CEO 河崎 |
| **CTO** (Chief Technology) | **vacant** (a.oda 契約終了 2026-04-20) | **primary** | C autonomous, B with 24h auto-disclose | CEO 河崎 |
| **CFO** (Chief Financial) | **vacant** | **primary, financial-action gated** | read-only + draft-only on financial actions; **no autonomous spend** | CEO 河崎 + COO |
| **CMO** (Chief Marketing) | **vacant** (t.ichihara = Branding 事業部, n.takahashi/k.takahashi = creative — none = CMO) | **primary** | C autonomous on owned-channel post; B with human-confirm on paid spend | CEO 河崎 + COO |
| **CHRO** (Chief Human Resources) | **vacant** | **primary, payroll gated** | C on internal comms / scheduling; B with human-confirm on hiring/firing/comp | CEO 河崎 + COO |
| **CISO** (Chief Information Security) | n.takahashi (Cybersecurity 事業部責任者) | shadow | C autonomous on hardening; B with human-confirm on incident disclosure | CEO 河崎 + n.takahashi |
| **CDO** (Chief Design) | k.takahashi (クリエイティブディレクター) | shadow | C only | k.takahashi → CEO |

Decision Classes follow `00-contracts/dmn/` taxonomy (A=org-level / B=ops-level
/ C=operational / D=routine).

## 4. Hard rules (encode in `keiei/roles.py`)

1. **Operating-entity boundary** — every AI-CXO action's `principal` field is
   `did:web:etz-hayim` regardless of which role acted. Vendor (etzhayyim Japan) is
   never the principal. SSoT: `deps.toml [platform.operating_entity]`.
2. **Financial-action prohibition** — CFO AI **MUST NOT** initiate Stripe
   charges, wire transfers, payroll runs, or sign legal documents. It may
   only **prepare drafts** and **request human approval** via consent
   workflow (`createConsentHelper`). Per `[etzhayyim_agent.permissions]`
   `financial_action = false`.
3. **External-mail gate** — All `etzhayyim.com` / `etzhayyim.com` / `etzhayyim.works` /
   `etzhayyim.com` recipients = direct send. All other recipients = draft only,
   require human approval before `sendDraft`. Per
   `[etzhayyim_agent.auth] email_send_external = "draft_only"`.
4. **Class A escalation, no exceptions** — Any decision tagged Class A
   (org-level: legal entity changes, M&A, layoffs, public statements) is
   **always** routed to CEO 河崎 with `$/escalate` notification + blocking
   wait. AI never executes Class A autonomously, even in primary mode.
5. **24h auto-disclose** — Every Class B decision executed by a primary-mode
   AI-CXO is appended to `_working/keiei/CXO-LEDGER.md` and emailed to CEO
   within 24h. Silent execution = institutional discipline violation
   (echoes iter86+ audit pattern).
6. **No cross-role override** — CMO cannot bypass CFO's financial gate; CTO
   cannot bypass CISO's security review. Inter-role calls go through the
   LSP method namespace (`cxo.cfo.review` etc.) and respect each role's gates.

## 5. LSP wire (JSON-RPC 2.0)

Transport: **Unix socket** (`$XDG_RUNTIME_DIR/keiei.sock`) for local clients
+ **WebSocket** (`wss://keiei.etzhayyim.com/lsp`) for remote (mTLS, `did:web` auth
via PDS pipethrough). Both speak identical JSON-RPC 2.0.

### Methods (initial set — extend per role as needed)

| Method | Direction | Purpose |
|---|---|---|
| `initialize` | client → server | handshake, returns `serverCapabilities.roles[]` and per-role `methods[]` |
| `initialized` | client → server | post-handshake ack |
| `cxo/listRoles` | client → server | enumerate live roles + status (mode, last decision, queue depth) |
| `cxo/{role}/decide` | client → server | submit a decision request (returns decision id, may stream partial reasoning) |
| `cxo/{role}/review` | client → server | review artefact (PR, contract draft, marketing copy) — returns advisory |
| `cxo/{role}/state` | client → server | snapshot working memory + open items |
| `cxo/{role}/escalate` | client → server | force-escalate a pending decision to human principal |
| `$/escalate` | server → client | server pushes "I need human input on decision X by deadline Y" |
| `$/decisionMade` | server → client | server pushes audit entry after each Class B/C decision |
| `$/sla` | server → client | server pushes SLA warnings (e.g. "CEO reply not received within 48h") |
| `$/cancelRequest` | both | standard LSP cancel |
| `shutdown` / `exit` | client → server | graceful drain + halt |

### Capability handshake example

```json
// → initialize
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
  "clientInfo":{"name":"claude-code","version":"opus-4-7"},
  "principal":"did:web:etz-hayim",
  "actingAs":"j.kawasaki@etzhayyim.com"
}}
// ← response
{"jsonrpc":"2.0","id":1,"result":{
  "serverInfo":{"name":"keiei-lsp","version":"0.1.0"},
  "serverCapabilities":{
    "roles":[
      {"id":"ceo","mode":"shadow","humanSeat":"j.kawasaki@etzhayyim.com"},
      {"id":"coo","mode":"shadow","humanSeat":"a.nakamura@etzhayyim.com"},
      {"id":"clo","mode":"shadow","humanSeat":"k.bakshi@etzhayyim.com"},
      {"id":"cto","mode":"primary","humanSeat":null,"escalateTo":"j.kawasaki@etzhayyim.com"},
      {"id":"cfo","mode":"primary","humanSeat":null,"financialActionGated":true},
      {"id":"cmo","mode":"primary","humanSeat":null},
      {"id":"chro","mode":"primary","humanSeat":null,"payrollGated":true},
      {"id":"ciso","mode":"shadow","humanSeat":"n.takahashi@etzhayyim.works"},
      {"id":"cdo","mode":"shadow","humanSeat":"k.takahashi@etzhayyim.com"}
    ],
    "decisionClasses":["A","B","C","D"],
    "auditChannel":"_working/keiei/CXO-LEDGER.md"
  }
}}
```

## 6. Implementation layout

```
20-actors/magatama/py/src/pymagatama/keiei/
├── __init__.py          # public exports: ROLES, build_role_graph, run_lsp
├── __main__.py          # entry: python -m pymagatama.keiei [--socket|--ws]
├── roles.py             # declarative role registry (this ADR §3 + §4 in code)
├── principals.py        # etzhayyim binding + escalation routing
├── graph.py             # LangGraph factory — one graph per role, persisted via checkpointer
└── lsp_server.py        # JSON-RPC 2.0 dispatcher (asyncio, stdio + Unix-socket + WS)
```

The graph definitions reuse `langgraph_graphs/_kafun_common.llm` for LLM
calls and persist state via the LangGraph Checkpointer Storage convention
(ADR 2605082100). Per-role state schemas live in `roles.py` next to the role
definition (graph-definition-as-data per ADR 2605082000).

## 7. Residency (常駐)

### 7a. Local dev (macOS) — launchd

```xml
<!-- ~/Library/LaunchAgents/com.etzhayyim.keiei.plist -->
<plist version="1.0"><dict>
  <key>Label</key><string>com.etzhayyim.keiei</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/env</string>
    <string>uv</string><string>run</string>
    <string>python</string><string>-m</string><string>pymagatama.keiei</string>
    <string>--socket</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>WorkingDirectory</key>
  <string>/Users/junkawasaki/etzhayyim/etzhayyim-root/20-actors/magatama/py</string>
  <key>StandardOutPath</key><string>/tmp/keiei.out.log</string>
  <key>StandardErrorPath</key><string>/tmp/keiei.err.log</string>
</dict></plist>
```

`launchctl load ~/Library/LaunchAgents/com.etzhayyim.keiei.plist` to start.

### 7b. Production — k8s Deployment (granian L3 runtime per ADR 2605080600)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: {name: keiei-lsp, namespace: keiei}
spec:
  replicas: 1   # single-writer per CEO 河崎; HA via leader-election (future)
  selector: {matchLabels: {app: keiei-lsp}}
  template:
    spec:
      containers:
      - name: keiei
        image: ghcr.io/etzhayyim/keiei-lsp:latest
        command: ["granian","--interface","asgi","pymagatama.keiei.lsp_server:app"]
        env:
        - {name: KEIEI_PRINCIPAL_DID, value: "did:web:etz-hayim"}
        - {name: KEIEI_LEDGER_PATH, value: "/data/CXO-LEDGER.md"}
        - {name: etzhayyim_LLM_URL, value: "https://murakumo.etzhayyim.com/v1/chat/completions"}
        ports: [{containerPort: 8443, name: lsp-wss}]
        volumeMounts: [{name: state, mountPath: /data}]
      volumes: [{name: state, persistentVolumeClaim: {claimName: keiei-state}}]
```

Resource budget: 1 CPU / 2GB RAM / 10GB PVC. LLM calls go to murakumo
fleet (not local-resident).

## 8. Audit & ledger

Single append-only file: `_working/keiei/CXO-LEDGER.md`. Format echoes
`DECISION-LOG.md`:

```
| seq | date | role | class | summary | decided_by | escalated_to | artefact |
```

Class A entries link to a CEO-approval record in PDS
(`com.etzhayyim.governance.classA-approval`). Class B entries auto-disclose to
CEO inbox within 24h via `microsoft.etzhayyim.com sendMail` (internal direct).

## 9. Migration path

| Phase | Scope | Status |
|---|---|---|
| **Phase 0** (this ADR) | design + role registry + skeleton LSP server | **proposed** iter123 |
| Phase 1 | implement `cto` role first (vacant seat, real demand from infra work) — graph + LSP method handlers + ledger emit | **shipped 2026-05-12** (graph/cto.py + LSP `_decide` wired to `dispatch_decide`; ledger seq 11+ rationale-tracked) |
| Phase 2 | add `cfo` (gated) + `cmo` + `chro` for vacant-seat coverage + 24h auto-disclose mailer | **shipped 2026-05-14** — `graph/{cfo,cmo,chro}.py` lens routing + `pymagatama.keiei.mailer` + launchd plist `com.etzhayyim.keiei-mailer` (hourly tick) + `_working/keiei/CXO-MAILER-STATE.json` watermark. Hard rules force-gated by `roles.gate()` (cfo financial_action_gated, chro payroll_gated). 43 unit tests under `tests/test_keiei_phase2.py` |
| Phase 3 | shadow roles (`ceo`/`coo`/`clo`/`ciso`/`cdo`) — chief-of-staff for existing humans | **shipped 2026-05-14** — `graph/{ceo,coo,clo,ciso,cdo}.py` fully expanded with shadow-mode lens routing (AI-CEO impersonation guardrail § ADR §10, COO Track A/B/C ownership map, CLO BCI Rule 36 + atproto OAuth wire-format + malak G2 + outreach placeholder discipline, CISO 8 malak hard invariants + vault zero-knowledge + threat-ledger pattern, CDO Bonsai cultivar metaphor + WCAG 2.2 AA + [data-lang] i18n + paid/owned channel split with AI-CMO). Class B gated to blocking human-confirm via `roles.gate()` shadow rule. 49 unit tests under `tests/test_keiei_phase3.py` (including mailer-excludes-shadow-Class-B regression). |
| Phase 4 | residency hardening — k8s deploy, mTLS, multi-client, leader-election | **code shipped 2026-05-14 (operator apply pending)** — HTTP transport `pymagatama.keiei.http_server` (FastAPI + bearer auth + JSON-RPC pass-through, granian-served per ADR-2605080600); `pymagatama.keiei.leader.K8sLeaseLeader` acquires/renews `coordination.k8s.io/v1` Lease via stdlib HTTPS (no python-kubernetes dep); `LocalLeader` fallback preserves launchd path; `ledger_append` + `mailer.run_once` gated on `is_leader()`, followers surface `status="not-leader"` + `leaderIdentity` (HTTP 503 + `X-Keiei-Leader`). k8s manifests under `50-infra/k8s/keiei/` (Namespace, ServiceAccount + namespaced Role/RoleBinding scoped to `leases/keiei-writer`, Deployment 3-replica with downward-API identity + RWX PVC `/data/keiei`, Service ClusterIP, Ingress `keiei.etzhayyim.com` with `nginx.ingress.kubernetes.io/auth-tls-secret` mTLS + `proxy-next-upstream` on 503, PDB minAvailable=2, kustomization). Image source `60-apps/etzhayyim-project-keiei/lg/Dockerfile`. RUNBOOK at `50-infra/k8s/keiei/RUNBOOK.md`. Operator (y-nishino) remaining: RWX class verify, image build/push, secret provisioning (`keiei-lsp-secrets` + `keiei-etzhayyim-ai-tls` + `keiei-mtls-ca`), per-client mTLS cert issuance, DNS, `kubectl apply -k`, RUNBOOK §3-§6 walk. 9 unit tests + 6 fastapi-gated tests in `tests/test_keiei_phase4.py` (combined 101 + 6 across all phases). |

## 10. Anti-goals (explicit)

- **Not a replacement** for human CXO seats. Even in primary mode the AI is
  an executor, not a fiduciary. Filling the actual CTO seat with a human
  remains the right action; AI-CTO is a stop-gap.
- **Not a CEO 河崎 simulator.** AI-CEO mode = chief-of-staff aggregating
  signal for 河崎; it never speaks *as* 河崎 to external counterparties.
- **Not a free-running daemon.** Every Class B/C action is audited; Class A
  is blocking-escalated. Silent autonomy = discipline violation.
- **Not a separate LLM stack.** Reuses murakumo + magatama + LangGraph
  primitives. The novelty is *role-bearing residency*, not new infra.

## 11. Cross-references

- `deps.toml [platform.operating_entity]` — etzhayyim principal SSoT
- `deps.toml [etzhayyim_agent]` — auth / permissions / org_members
- `90-docs/adr/2605080600-langgraph-server-granian-l3-runtime.md` — runtime
- `90-docs/adr/2605082000-langgraph-graph-definition-as-data.md` — graph SSoT
- `90-docs/adr/2605082100-langgraph-checkpointer-storage.md` — state persistence
- `00-contracts/dmn/` — Decision Class taxonomy (A/B/C/D)
- `_working/etzhayyim-revenue/DECISION-LOG.md` — chronology (iter123 entry)
