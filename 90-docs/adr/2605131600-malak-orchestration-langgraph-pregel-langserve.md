---
id: adr-2605131600-malak-orchestration-langgraph-pregel-langserve
title: "malak orchestration — BPMN replaced by LangGraph + Pregel + LangServe"
status: active
doc_type: adr
topic: malak-orchestration-langgraph-pivot
authoritative: true
last_verified: 2026-05-13
authoritative_for:
  - new malak orchestration model (LangGraph StateGraph + Pregel super-step + Send fan-out)
  - LangServe-style FastAPI HTTP route exposure
  - Replacement of new BPMN-as-actor flows under etzhayyim-root/00-contracts/bpmn/com/etzhayyim/malak/
priority: 8.6
axis: orchestration
weight: 0.86
priority_note: "New malak orchestrations use LangGraph. Legacy 18 malak BPMN files preserved for pyzeebe-direct path; no retroactive rewrite."
depends_on:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-2605082200-pyzeebe-handler-thin-dispatcher-contract
  - adr-2605131500-malak-surveillance-collapse-from-mehikari
related:
  - adr-0056-bpmn-as-actor
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
supersedes: []
superseded_by: []
notes: |
  Pivot decision on 2026-05-13 (user directive): "BPMN じゃなくて
  langgraph, pregel, langserver で設計、実装して". Two BPMN files
  scaffolded one hour earlier (CXO-LEDGER #39) were archived and replaced
  with LangGraph implementations. The 18 legacy malak BPMN files
  (createThreatOrg, draftAgencyReferral, etc., pre-2026-05-13) remain in
  place because they precede this pivot and continue to operate via the
  pyzeebe-direct path.
---

# Context

ADR-0056 (BPMN-as-actor) established BPMN 2.0 + Zeebe DSL as the
canonical orchestration model for multi-step actor flows. malak shipped
18 BPMN files (createThreatOrg, draftAgencyReferral, exportAgencyReferral
Package, etc.) under this model.

ADRs 2605080600 / 2605082000 / 2605082100 / 2605082200 then introduced
LangGraph as the canonical Phase-7 / Phase-8 orchestration layer with
pyzeebe relegated to a thin task dispatcher (ADR-2605082200). The
direction is clear in the platform: BPMN orchestration is dead path for
new flows; pyzeebe survives as a task pickup mechanism only.

When CXO-LEDGER #39 scaffolded two new BPMN files
(`exportSurveillanceEvidence.bpmn` + `agencyOutreachFullFlow.bpmn`) for
the new malak.surveillance capability cluster, the user reverted that
decision the same day with the directive quoted in the notes header
above: design and implement orchestration with LangGraph + Pregel +
LangServe instead.

# Decision

**New malak orchestrations use LangGraph StateGraph + Pregel super-step
parallelism + LangServe-style FastAPI HTTP routes.** The legacy 18 malak
BPMN files are retained (`status: legacy`) for the pyzeebe-direct path
but no new BPMN flows are written under `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/malak/`.

## 1. LangGraph chains

Three production chains, each a `langgraph.graph.StateGraph` compiled
to a Pregel runtime:

| Chain | Module | NSID | Pregel super-steps |
|---|---|---|---|
| `exportSurveillanceEvidence` | `kotodama/malak/langgraph/export_surveillance_evidence.py` | `com.etzhayyim.apps.malak.exportSurveillanceEvidence` | 4 (Send fan-out to render_doc × 4) |
| `agencyOutreachFullFlow` | `kotodama/malak/langgraph/agency_outreach_full_flow.py` | `com.etzhayyim.apps.malak.agencyOutreachFullFlow` (composite) | 6 (sequential + 5 conditional abort branches) |
| `draftAgencyBriefing` | `kotodama/malak/langgraph/briefing.py` | `com.etzhayyim.apps.malak.draftAgencyBriefing` | 8 (graph-native entity extraction + RW row staging) |

## 2. Pregel parallel fan-out via Send

`langgraph.constants.Send` is the canonical BSP fan-out primitive. Each
`Send(node_name, partial_state)` dispatches a parallel super-step, and
LangGraph applies an implicit barrier before the next sequential node:

```python
from langgraph.constants import Send

def fan_out_to_renderers(state):
    return [Send("render_doc", {**state, "_doc_type": dt})
            for dt in state["doc_types"]]
```

Parallel writes to a shared channel **require an `Annotated[Dict, reducer]`
type** on the state field, or LangGraph raises `InvalidUpdateError: Can
receive only one value per step`. The canonical reducer for our use case
is a shallow dict merge:

```python
def _merge_dict(a, b):
    if not a: return dict(b or {})
    if not b: return dict(a)
    out = dict(a); out.update(b); return out

class ExportEvidenceState(TypedDict, total=False):
    rendered_docs: Annotated[Dict[str, str], _merge_dict]
```

## 3. LangServe-style FastAPI server

`kotodama/malak/langgraph/server.py` exposes the three chains over HTTP:

```
GET  /health                            → {status, chains}
GET  /chains                            → registry (3 chains + pregel topology + gates)
GET  /chains/{name}/topology            → graph-definition-as-data introspection (ADR-2605082000)
POST /invoke/{name}                     → invoke(state_dict) → trimmed_final_state
```

The trim step removes PII channels (`rendered_docs`, `rendered_md`,
`graph_rows`, `draft_body`, `raw_url_citations`) before returning the
response — zero-knowledge invariant preservation. Markdown / DOCX / PDF
artefacts are persisted to filesystem (via `persist_node`) but never echoed
in the HTTP response.

Production deployment per ADR-2605080600:

```
granian --interface asgi kotodama.malak.langgraph.server:app
        --host 0.0.0.0 --port 8765
```

## 4. Three-layer hard gates (defense-in-depth)

Each surveillance/outreach gate is enforced at **three layers**:

| Layer | File / location |
|---|---|
| Edge | CF Worker `60-apps/etzhayyim-project-malak/.../src/app.ts:preflightGate` |
| pyzeebe (thin dispatch) | `kotodama/primitives/malak.py:task_malak_*` |
| LangGraph | Conditional edges in the three chains above |

Failing any layer returns 4xx / status="denied" / status="abort_*"
without reaching the next layer. This pattern is required for
`queryPerson` warrant gate, `exportSurveillanceEvidence` two-stage
approval, `registerAgencyProspect` opt-in source whitelist, and
`sendAgencyOutreach` business-hour gate.

## 5. Internationalisation in LangGraph chains

`draftAgencyBriefing` chain selects renderers by `state.language`:

```python
def _pick_renderers(language: str):
    if language.lower().startswith("en"):
        return DOC_RENDERERS_EN, SECTION_TITLE_EN
    return DOC_RENDERERS_JP, SECTION_TITLE_JP
```

JP renderers in `briefing_templates.py`, EN renderers in
`briefing_templates_en.py`. The same chain (8 super-steps, same entity
extractor) produces JP NPA briefings and EN INTERPOL IPSG briefings.

Similarly, `agencyOutreachFullFlow:draft_outreach_node` selects body
template by `state.template_key` (`v1_intro` JP / `v1_intro_en` /
`v1_intro_en_interpol` / `v1_intro_en_continental_eu`) — a single chain
runs JP fraud-network outreach and EU GDPR-compliant outreach.

# Legacy BPMN status

The 18 malak BPMN files in `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/malak/` are
retained `status: legacy`:

```
buildAgencyReferralEvidenceBundle.bpmn
createThreatOrg.bpmn
draftAgencyReferral.bpmn
exportAgencyReferralPackage.bpmn
exportStixBundle.bpmn
getDashboard.bpmn
getThreatGraph.bpmn
ingestTrapMessage.bpmn
linkWalletToActor.bpmn
listAgencyReferralDrafts.bpmn
listAgencyReferralExports.bpmn
listThreatActors.bpmn
listWallets.bpmn
queryRiskChain.bpmn
registerPhishingTrapInbox.bpmn
registerThreatActor.bpmn
reviewAgencyReferralDraft.bpmn
runInvestigationTick.bpmn
```

Each remains the canonical definition of its NSID flow under the
pyzeebe-direct path. No retroactive rewrite is mandated; **migration to
LangGraph happens opportunistically when a flow is touched substantively**.

The two scaffolded-and-replaced files
(`exportSurveillanceEvidence.bpmn` + `agencyOutreachFullFlow.bpmn`) are
in `_archive/2026-05-13-malak-bpmn-replaced-by-langgraph/` with a
README pointer to this ADR.

# Alternatives considered

## A. Keep BPMN for the 2 new surveillance flows

- Pros: ADR-0056 consistency, existing pyzeebe pickup works
- Cons: contradicts ADRs 2605080600 / 2605082000 / 2605082200 establishing
  LangGraph as canonical orchestration. **Rejected** — platform direction.

## B. Use SpiffWorkflow (per ADR-2605081200) inside LangGraph nodes

- Pros: BPMN authoring tools work
- Cons: extra layer with no benefit when the orchestration is best
  expressed in code; SpiffWorkflow is appropriate for human-authored
  approval flows but not for parallel doc-render fan-out. **Rejected**
  for these two chains specifically; future human-driven approval flows
  may revisit.

## C. Hand-write a fan-out loop without Pregel Send

- Pros: simpler mental model for new contributors
- Cons: loses the implicit barrier, no `langgraph_sdk` introspection,
  cannot stream partial results. **Rejected**.

# Operational implications

- Image rebuild: pyzeebe pod (`kotodama` image) rebuilt with new
  `primitives/malak.py:task_malak_draft_agency_briefing` etc. handlers
  + `zeebe_worker_main.py:malak.register(...)` call.
  Handoff: `_working/malak/surveillance/PYZEEBE-REDEPLOY-HANDOFF.md`.
- LangServer pod: NEW Mac-native or container deploy of
  `kotodama.malak.langgraph.server:app` via Granian.
  Reference manifest pattern: `50-infra/k8s/murakumo-kubelet/examples/malak-langserver-pod.yaml`.
- atproto Worker (PDS validator): already deployed
  (`Version 22ad3cd6-de51-4ed9-962c-2c8dd037a43e`, CXO #33). Re-deploy
  triggers when lexicon-bundled.ts changes.

# References

- CXO-LEDGER #39 — 2 BPMN scaffold (later archived)
- CXO-LEDGER #40 — pivot decision + 3 chains + FastAPI server
- CXO-LEDGER #41 — language-agnostic chain demonstrated (INTERPOL EN briefing)
- CXO-LEDGER #42 — outreach chain handles JP + EN variants
- ADR-2605131500 — companion ADR for the broader malak.surveillance design
- `_archive/2026-05-13-malak-bpmn-replaced-by-langgraph/README.md`
