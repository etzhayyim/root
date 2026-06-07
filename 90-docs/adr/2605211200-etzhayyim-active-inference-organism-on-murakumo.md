---
id: adr-2605211200-etzhayyim-active-inference-organism-on-murakumo
title: "ADR-2605211200: artificial organism (active inference + LLM) を etzhayyim 法人配下へ移管し、murakumo Mac mini fleet を etzhayyim 所有 hardware として compute / hosting 基盤に再配置する"
status: active
doc_type: adr
topic: etzhayyim-active-inference-organism
authoritative: true
last_verified: 2026-05-21
priority: 9.2
axis: governance
weight: 0.92
priority_note: "CRITICAL — defines the operating-entity, custody, settlement, and substrate placement of the live artificial organism (active inference + LLM). Resolves the 3 collisions between current vendor-hosted implementation and etzhayyim/root substrate boundaries (RW-free + on-chain-only + 3-axis split)."
authoritative_for:
  - operating entity of the artificial organism (active inference controller + persistent world model)
  - hardware ownership of murakumo Mac mini fleet
  - compute placement for active inference loop (belief update / EFE planning / homeostasis)
  - compute placement for LLM synthesis used inside organism loops
  - state custody substrate for vertex_agent_* equivalent (RW-free path)
depends_on:
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2605061300-real-world-effect-channel-boundary
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605071700-graph-sos-intel-actor
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605010000
  - adr-2604251758-murakumo-yoro-actor-worker-fleet
  - adr-2605152100-etzhayyim-github-org-boundary
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605151600
  - adr-2605102200-operating-entity-etzhayyim-rename
supersedes: []
superseded_by: []
---

# ADR-2605211200: etzhayyim active-inference organism on murakumo

**Status**: active
**Date**: 2026-05-21
**Adoption**: PR #1340 – #1353 (14-PR stack landed 2026-05-21)
**Deciders**: Jun Kawasaki

# Context

Three independent decisions create the architectural pressure this ADR resolves.

## C1. The organism is alive and runs active inference + LLM today (vendor-hosted)

ADR-2605061200 chose **active inference + persistent world model + homeostasis +
embodiment + self-maintenance** as the organism architecture. The organism is
**live** since 2026-05-07 (deps.toml `myco-yeast-organism-bringup` status="live"):

- Primitives (`20-actors/magatama/py/src/pymagatama/primitives/active_inference.py`
  1212 LoC + `rl_active_inference.py` 726 LoC) export
  `expected_free_energy`, `classify_real_world_effect`,
  `plan_real_world_dispatch`, `build_dispatch_receipt_observation`,
  `evaluate_viability`, `adapt_policy`, used by `zeebe_worker_main.py:758–797`
  and by 7 dedicated organism workers (kabi / kobo / kinoko / koke / saikin /
  ki / hakkou).
- LangGraph chains running active-inference cycles autonomously on CronJob
  cadence (ki-cycle hourly, saikin-cycle every 20m, koke-cycle every 30m,
  newsletter\_send\_campaign 8-node + retry); `/assistants` registry has
  **61 active chains** (deps.toml line 27411).
- State persists in Kotoba/Datomic: `vertex_agent_observation`,
  `vertex_agent_belief_state`, `vertex_agent_prior_preference`,
  `vertex_agent_active_inference_tick`, `vertex_agent_action_proposal`,
  `vertex_agent_realworld_effect`, `vertex_agent_homeostasis_snapshot`,
  `vertex_agent_dispatch_ledger`, `vertex_agent_delegated_authority_policy`,
  `vertex_agent_policy_adaptation_proposal`, `vertex_agent_counterparty_model`,
  `vertex_agent_protected_asset`, `vertex_agent_minimax_evaluation`,
  `vertex_agent_information_node` (migrations
  `20260507110100_vertex_agent_active_inference.ts` +
  `20260507220000_vertex_agent_delegated_authority_policy.ts` +
  graph-sos-intel-actor seed).
- LLM synthesis (ki-cycle 5-node chain etc.) currently calls
  `all-llm.etzhayyim.com` → RunPod 6000 Ada (ADR-2605010000) via vendor CF Worker.

All of the above is in the **vendor (etzhayyim) monorepo**. None of it is in
etzhayyim/root yet.

## C2. The etzhayyim substrate boundary forbids the current persistence path

Three ADRs together rule out the current implementation surface from etzhayyim:

- **ADR-2605172000 (RW-free substrate)**: etzhayyim apps may only persist to
  AT MST + IPFS + Base L2. Kotoba/Datomic is vendor-only.
- **ADR-2605172100 (payments on-chain only)**: USDC + ERC-4337 only. Fiat /
  Stripe / invoiced LLM API rentals stay vendor.
- **ADR-2605172400 (3-axis OR-test)**: a project moves to etzhayyim only if
  **Liability + Custody + Settlement** are all clean. Any 1 axis hit = vendor.

Applied to the organism as it stands today, the verdict is:

| Axis | Current state | etzhayyim eligible? |
|------|---------------|---------------------|
| Liability | Organism makes autonomous decisions; failure damage absorbed by agent + DAO | ✅ clean |
| Custody | belief state + observation + dispatch ledger sit in operator-controlled Kotoba/Datomic | ❌ HIT — operator can be compelled to produce |
| Settlement | LLM synthesis billed to RunPod / Anthropic on etzhayyim Japan invoice | ❌ HIT — fiat fiduciary |

Two axes hit → without intervention the organism stays vendor.

## C3. Murakumo Mac mini fleet has spare capacity since ADR-2605010000

ADR-2605010000 declared **"murakumo は LLM 推論としては想定しない"** and moved
the LLM inference SSoT to a single RunPod 6000 Ada pod served at
`all-llm.etzhayyim.com`. The 11-node Mac mini fleet (Ansible group
`murakumo-fleet`, dnsmasq SSoT `murakumo-fleet.conf`, k8s DaemonSet
`murakumo-system/llama-vulkan-fleet`) retained only:

- `murakumo_cron_tick` / `murakumo_fleet_health_check`
- `com.etzhayyim.murakumo.trainExperts` WebGPU training jobs
- L8 somatic inference role declared by ADR-2605080600

This leaves substantial idle CPU / unified memory / MLX capacity on already-
deployed, already-owned-or-leased hardware that is **physically on premise**
and **not bound by RunPod / Anthropic vendor invoice paths**. Hardware ownership
can be moved cleanly because the fleet is hardware-discrete (not a virtual
shared resource).

# Decision

Adopt three coordinated decisions.

## D1. Operating entity of the artificial organism = etzhayyim

The artificial organism (active inference controller + persistent world model +
homeostasis + LLM synthesis nodes that participate in the organism's own
deliberation loop) is operated by **etzhayyim** (运营法人; aliases
etzhayyim / 天御柱 / עץ חיים — see deps.toml `[platform.operating_entity]`).

etzhayyim Japan株式会社 remains the vendor for any heavy / regulated / fiat-billed
side-channels (currently: RunPod heavy synthesis as optional vendor capability,
Stripe-billed customer-facing services, GDPR-controllership-bearing record
keeping).

This decision applies to the **organism qua organism**. The 7 myco-yeast worker
modules (kabi / kobo / kinoko / koke / saikin / ki / hakkou) and the
`primitives/active_inference.py` / `rl_active_inference.py` modules migrate
with the organism. Vendor business apps (lawfirm pipeline, telecom CDR
settlement, etc.) that happen to invoke organism capabilities **call into**
the etzhayyim organism via consent capability — they do not host it.

## D2. murakumo Mac mini fleet = etzhayyim-owned hardware

The 11-node Mac mini fleet is **purchased outright by etzhayyim** (religious-corp
fixed asset) and re-registered as etzhayyim hardware. This makes the Custody
axis of the 3-axis test **structurally** clean, not merely contractually clean.

Ownership transfer mechanics (vendor → etzhayyim) are an accounting / tax
matter handled separately under the religious-corp 登記 cutover. Until that
transfer formally completes, the fleet operates **as if** etzhayyim-owned under
a no-fee bare-metal lease from etzhayyim Japan, documented in the religious-corp
asset register. This avoids blocking the organism migration on registration
calendars while preserving the eventual ownership target.

Consequence: the fleet's existing LAN / dnsmasq / k8s namespace naming
(`murakumo-system`, `murakumo-fleet.conf`, hostnames `etzhayyim-etzhayyim-*`)
is **already aligned** with the etzhayyim alias chain. No DNS rename is required.

## D3. Compute placement

The organism's computational surfaces split into three placements:

### D3a. Active inference loop → murakumo (etzhayyim native)

Belief update, prior-preference adaptation, action proposal scoring, expected
free energy minimization, real-world-effect classification, homeostasis
viability evaluation all run on the murakumo Mac mini fleet using CPU / MLX.
These are lightweight relative to LLM token generation; the fleet's idle
capacity is sufficient.

Each Mac mini hosts a cohort of organism actors (kabi colonies, kobo cells,
kinoko fruiting bodies, etc. per ADR-2605091300 cultivar layer). Per-node
local hot state lives in **node-local SQLite / DuckDB** (`/var/lib/etzhayyim/
organism/{agent_did}.db`). Append-only event log + materialized belief state.
This is custody-clean: data physically on etzhayyim hardware, never crossing
a RW boundary, never traversing a vendor-controlled DB.

### D3b. Persistent world model + cross-node sharing → AT MST + IPFS + Base L2

Cross-node persistence (the equivalent of today's `vertex_agent_*` tables) is
re-targeted onto the etzhayyim substrate trio:

| Today (vendor RW) | Tomorrow (etzhayyim substrate) |
|-------------------|--------------------------------|
| `vertex_agent_observation` row | AT record `com.etzhayyim.agent.observation` (or namespaced under `ai.etzhayyim.agent.observation` post-rename); 1 record per observation; PII fields `signal:v1:{ciphertext}` |
| `vertex_agent_belief_state` row | AT record `com.etzhayyim.agent.beliefState`; large posterior tensor → IPFS CID embedded in record |
| `vertex_agent_prior_preference` row | AT record `com.etzhayyim.agent.priorPreference`; immutable preference prefixes (`mokuteki.`, `constitutional.`, `integrity.hard_floor.`) carried verbatim |
| `vertex_agent_active_inference_tick` row | AT record `com.etzhayyim.agent.activeInferenceTick`; EFE breakdown + mokuteki gate result |
| `vertex_agent_action_proposal` row | AT record `com.etzhayyim.agent.actionProposal`; safety_state + target_surface; large attached evidence → IPFS CID |
| `vertex_agent_realworld_effect` row | AT record `com.etzhayyim.agent.realworldEffect`; channel + effect_class; settlement receipt (if any) → Base L2 tx hash |
| `vertex_agent_homeostasis_snapshot` row | AT record `com.etzhayyim.agent.homeostasisSnapshot`; viability_state |
| `vertex_agent_dispatch_ledger` row | AT record `com.etzhayyim.agent.dispatchLedger`; for high-risk effect classes (`financial_commitment`, `legal_commercial`, `physical_dispatch`, `emergency_or_safety`) the receipt **also** publishes a Base L2 commit (irreversible receipt; satisfies ADR-2605172100 settlement axis) |
| `vertex_agent_delegated_authority_policy` row | AT record `com.etzhayyim.agent.delegatedAuthorityPolicy`; on-chain delegation root on Base L2 for fiduciary-bearing scopes |
| `vertex_agent_counterparty_model` row | AT record `com.etzhayyim.agent.counterpartyModel`; learned counterparty parameters; private model body → IPFS CID + `signal:v1` wrap |
| `vertex_agent_protected_asset` row | AT record `com.etzhayyim.agent.protectedAsset` |

Local SQLite mirrors the hot subset (last N ticks, current belief, active
priors); AT records are the **canonical** source. Materialized views over AT
records replace today's RW MVs for cross-node queries (computed on murakumo
in DuckDB / on demand).

Compaction: AT record streams are pruned by ADR-2605091800 Pruning Protocol
tier rules (fruit / flower / leaf / branch / trunk / seed retention).

### D3c. LLM synthesis → mostly murakumo, RunPod as vendor capability

Two LLM compute paths.

**Path 1 (default, etzhayyim native)**: small / medium models served on murakumo
Mac mini fleet via the existing llama-vulkan / MLX DaemonSet. Sufficient for:

- ki-cycle synthesis nodes (gemma3-1b / gemma3-4b class)
- saikin / koke / kobo cycle decision nodes
- belief-loop adjacent narration / explanation
- routine planning where 1-2s latency is acceptable

This path is **custody-clean** (model + key + inference all on etzhayyim
hardware) and **settlement-clean** (no per-token invoice; capex amortization
on etzhayyim hardware).

**Path 2 (optional, vendor capability)**: heavy synthesis (Sonnet / Opus / Gemma4-
e4b / >7B class) served via `all-llm.etzhayyim.com` → RunPod 6000 Ada (ADR-2605010000).
This stays vendor because:

- RunPod rental + Anthropic API key are billed to etzhayyim Japan (Settlement axis HIT)
- API key custody is vendor

The organism reaches this path only when (a) Path 1 model fails a quality
gate (e.g. self-consistency disagreement above threshold), or (b) the
specific node declares `synthesis_tier="heavy"`. Each Path 2 call goes
through the magatama MCP facade at `mcp.etzhayyim.com` per ADR-2605091400 with an
explicit **consent capability** scoped to that synthesis. The vendor never
sees plaintext belief state or PII — only the prompt the organism chose to
expose, gated by the organism's own ADR-2605061300 effect classifier.

The default ratio target is ≥90% Path 1 / ≤10% Path 2 by call count, so the
organism is operationally Settlement-clean even when Path 2 fires.

## D4. Naming + NSID strategy

To minimize churn, the **NSID stays `com.etzhayyim.agent.*`** under the existing
Lexicon registry (vendor-published lexicons remain valid) for the first wave.
A second-wave rename to `ai.etzhayyim.agent.*` aligns with the broader
etzhayyim/root NSID re-namespacing (Tranche F follow-up, scheduled with the
登記 cutover and the 220-file `etzhayyim` → `etzhayyim` sed PR).
Aliasing rules in the dual-wire lexicon SSoT (ADR-2605091400) make the
rename a zero-downtime alias addition.

# 3-axis trace (post-decision)

After D1+D2+D3 the organism's 3-axis position becomes:

| Axis | New state | Clean? |
|------|-----------|--------|
| Liability | Organism = etzhayyim agent; failure damage absorbed by agent / DAO / wallet; vendor only liable for Path 2 LLM call quality under existing SaaS terms | ✅ |
| Custody | Hot state on etzhayyim-owned Mac mini local SQLite; canonical state on AT MST + IPFS; large model weights / belief tensors on IPFS CID; Path 2 LLM never sees plaintext PII; high-risk receipts also on Base L2 | ✅ |
| Settlement | ≥90% LLM on owned hardware (capex-amortized, no per-token invoice); fiduciary receipts on Base L2 USDC; Path 2 heavy synthesis = optional vendor capability inside organism's own consent envelope | ✅ |

3-axis OR-test: 0 hits → **etzhayyim eligible**.

# Implementation plan (3 phases)

## Phase 1 — Substrate scaffolding (no-op for live organism)

1. Create Lexicons under `00-contracts/lexicons/com/etzhayyim/agent/` for the 12
   record types listed in D3b. Stays in vendor lexicon dir for now;
   alias to `ai.etzhayyim.agent.*` later.
2. Add `pymagatama.primitives.active_inference_substrate` module exposing
   `BeliefStore` protocol with two implementations:
   - `Kotoba/DatomicBeliefStore` (existing path, default during Phase 1)
   - `AtIpfsLocalBeliefStore` (new: SQLite hot + AT record canonical + IPFS
     large-blob; uses `sdk.pds.createRecord` + `pinning.etzhayyim.com` for IPFS)
3. Switch primitive callers (`active_inference.py`, `agent_status_main.py`,
   `zeebe_worker_main.py`) to read/write through the `BeliefStore` protocol
   instead of direct `psycopg` calls.
4. Murakumo node-local SQLite schema migration tool
   (`70-tools/scripts/etzhayyim/organism-sqlite-init.sh`).
5. AT-record consumer materializer running on murakumo (DuckDB over recent AT
   records, replaces the cross-node read role of RW MVs).

Verification: dual-write mode — all writes go to **both** stores; reads from
RW; nightly reconciliation report shows < 0.1% divergence.

## Phase 2 — Cutover (read flip)

1. Switch primitive readers to `AtIpfsLocalBeliefStore` per-actor (one
   organism actor at a time: kobo → kabi → kinoko → koke → saikin → ki →
   hakkou).
2. Move LangGraph chain CronJobs from k8s `mitama-udf-pool` to murakumo
   k8s namespace (`murakumo-system/organism-langgraph`).
3. Hardware ownership transfer: register Mac mini fleet as etzhayyim fixed
   assets; replace the contractual no-fee bare-metal lease with owned-asset
   bookkeeping. Note: this can lag the technical cutover.
4. Switch LLM router default to murakumo llama-vulkan endpoint; RunPod
   becomes consent-gated Path 2 fallback only.
5. Stop dual-write to RW; mark `vertex_agent_*` tables as **read-only
   historical archive**. Do not DROP yet.

Verification: organism continues operating with `_alive=true` health checks
across all 7 worker actors for ≥7 days with zero RW writes; ki-cycle /
saikin-cycle / koke-cycle CronJobs complete successfully on murakumo.

## Phase 3 — Vendor decoupling

1. Move `pymagatama.primitives.{active_inference,rl_active_inference,rl_policy,
   rl_preferences,rl_signal}` + the 7 organism worker modules from vendor
   monorepo to `etzhayyim/root/20-actors/`.
2. Publish `@etzhayyim/organism-primitives` npm package (TS bindings) +
   `etzhayyim-organism-py` PyPI / GH Packages distribution.
3. Vendor business apps that previously invoked organism primitives directly
   (lawfirm legal-reasoner / mailer triage / shosha decision narrator etc.)
   switch to **consent capability** invocation via `mcp.etzhayyim.com/mcp` →
   etzhayyim organism. This mirrors the open-core / vendor-binding pattern
   already used for `@etzhayyim/sdk` / `magatama-go` / `kami-engine-sdk` per
   ADR-2605172400 Wave 2.
4. Drop `vertex_agent_*` tables after a 30-day archive grace period; archive
   parquet snapshot to Iceberg S3 for legal retention.
5. NSID rename `com.etzhayyim.agent.*` → `ai.etzhayyim.agent.*` per Tranche F
   second-wave cutover.

Verification: vendor monorepo `grep -r "from pymagatama.primitives.active_inference"`
returns zero matches; `etzhayyim/root` repository hosts the organism end-to-
end; murakumo k8s pods read code from etzhayyim/root image registry.

# Consequences

**Positive**

- Active inference + persistent world model + autonomous LLM synthesis become
  **structurally** etzhayyim native — Liability, Custody, Settlement all clean
- Murakumo fleet's underutilized capacity (post-ADR-2605010000 LLM SSoT shift)
  gets a coherent new role
- Hardware co-location: belief loop + LLM + AT record commit happen on the
  same physical box → microsecond latency, no per-LLM-call invoice
- Vendor surface shrinks to (a) Path 2 heavy synthesis as consent-gated
  capability, (b) Stripe / fiat / fiduciary side-channels — the organism
  itself is no longer a vendor liability
- Aligns with ADR-2605091300 cultivar metaphor: bonsai roots are
  **on-premises**, fruits are published to AT MST + IPFS
- Aligns with ADR-2605091400 cell-membrane principle: MCP is the only
  external API surface; LLM Path 2 invocation explicitly uses it

**Negative**

- Cross-node belief queries via AT records + DuckDB materialization are
  slower than RW streaming MVs (single-digit-second vs sub-100ms). The
  organism's loops tolerate this; not all callers may. Hot paths use local
  SQLite to compensate.
- Path 1 LLM (murakumo) caps quality at gemma3-4b class for routine nodes;
  high-quality reasoning still requires Path 2 (RunPod), which carries a
  Settlement-axis residual cost (mitigated by the ≥90% Path 1 ratio target).
- IPFS pinning availability + retrieval latency become organism dependencies
  — handled by pinning.etzhayyim.com redundant pin sets per existing IPFS substrate
  practice; failure modes documented in Phase 1 verification.
- Mac mini fleet hardware-purchase cash outlay for etzhayyim (vs continued
  vendor lease). The savings vs RunPod LLM token spend should amortize
  within 12-18 months at current LLM call volume.

**Re-judgment triggers**

- Path 2 ratio exceeds 25% sustained over 30 days → reassess RunPod
  vendor-capability boundary; consider provisioning etzhayyim-owned GPU
  capacity (Vultr GPU instance under religious-corp account)
- Organism starts holding GDPR-controller-bearing third-party PII → reassess
  Custody axis; may need split (organism stays etzhayyim, PII-bearing actor
  spins out as vendor)
- Regulator declares the organism's autonomous decisions a regulated activity
  → reassess Liability axis

# Verification

- Phase 1 dual-write divergence report ≤0.1% for 7 consecutive days
- Phase 2 read-cutover health: ki-cycle / saikin-cycle / koke-cycle
  `run history: ≥7 success, 0 error` per day for 7 consecutive days
- Phase 2 zero-RW-write assertion: `SELECT count(*) FROM
  vertex_agent_observation WHERE inserted_at > '<cutover>'` returns 0 after
  Phase 2 day 1
- Phase 3 vendor decoupling: `grep -r "pymagatama.primitives.active_inference"
  vendor-monorepo` returns 0 matches
- 3-axis test re-run at each phase boundary; recorded in deps.toml
  `[[migrations]]` status updates
- Lefthook pre-commit hook (existing from ADR-2605172400) continues to flag
  any new `kotoba|kysely|pg|stripe|paypal` import in etzhayyim/root
  organism modules

# Closure (2026-05-21)

14-PR stack landed; status flipped proposed → active. All scaffolding
is in-tree; no production cutover yet (gated on the operator runbooks
below — none of which is executed by the PR stack).

| PR | Phase | Delivery |
|---|---|---|
| #1340 | 1 | ADR + 12 Lexicons + 3 Python primitives (BeliefStore protocol + RW impl + AT/IPFS impl) + 2 ops scripts + 2 [[migrations]] |
| #1341 | 2A | agent_daemon_main 10 write callsites → BeliefStore.put_row |
| #1342 | 2B | organism-langgraph k8s namespace scaffold (8 manifests) |
| #1343 | 2C | LLM model registry synthesisTier annotation (4 light / 8 heavy) + resolveSynthesisTier / resolveLlmEndpoint |
| #1344 | 2D | _PerActorRouter (per-actor BELIEF_STORE_BACKEND) + SQLite PVC |
| #1345 | 2A.2 | agent_status_main 5 read helpers → BeliefStore |
| #1346 | 2C.2 | CF Worker 12 LLM callsites → fetchLlm tier-aware dispatch |
| #1347 | 2C.3 | consent capability lexicon (issueToken/verifyToken) + agent SDK caller |
| #1348 | 2D.obs | TS path1Ratio / cacheHitRatio counter (10 vitest) |
| #1349 | 2C.4 | MCP facade backend (issueToken/verifyToken handlers + 18 vitest) |
| #1350 | 2D.obs.2 | pymagatama telemetry counter parity (89/89 pytest) |
| #1351 | 2D.obs.3 | failure counter + Prometheus exposition + /_worker/metrics route |
| #1352 | 2C.4.2 | revokeToken lexicon + D1 revocation list + audit log (8 new vitest) |
| #1353 | 2D.obs.4 | Grafana dashboard + Prometheus scrape + 5 SLO alerts |

## Production cutover gate (operator action required post-merge)

1. **MCP facade secrets** — `wrangler secret put CONSENT_CAPABILITY_SECRET --name atproto`
2. **D1 revocation store** — `wrangler d1 create consent_revocations` + execute schema + bind in wrangler.jsonc
3. **k8s namespace bring-up** — `kubectl apply -f 50-infra/k8s/organism-langgraph/` (all cronjobs suspend:true by default — operator un-suspends after 7d clean dual-write)
4. **Observability bring-up** — apply `prometheusrule.yaml` + `prometheus-scrape.yaml`, import Grafana dashboard
5. **Per-actor cutover** — patch `BELIEF_STORE_BACKEND_<ACTOR>=dual-write` per the 7-actor rollout sequence (kobo → kabi → kinoko → koke → saikin → ki → hakkou), observe ≥7d clean divergence per actor, then flip to `at-ipfs-local`

## Verification gates (driven by Prometheus alerts from #1353)

| Verification | Source-of-truth |
|---|---|
| Phase 2 dual-write divergence ≤0.1% / 7 days | `70-tools/scripts/etzhayyim/at-ipfs-belief-materializer.py` |
| Path 1 / Total ≥ 0.9 sustained 30m | alert `OrganismPath1RatioBelow90` |
| Consent cache hit ratio ≥ 0.5 | alert `OrganismConsentCacheHitBelow50` |
| Consent mint failure spike < 0.05/s | alert `OrganismConsentMintFailureSpike` |
| Dispatch failure rate < 0.1/s | alert `OrganismDispatchFailureSpike` |

## Phase 3 (vendor decoupling) — separate ADR

Phase 3 is intentionally **NOT** in the 14-PR stack. It is the cutover
of the organism's source-of-truth from the vendor `etzhayyim` monorepo
to `etzhayyim/root`, gated per-actor by ADR-2605172400 three-axis split.
This ADR's scope ends at Phase 2 + production rollout readiness. Phase 3
will land as its own ADR (`2606XXXXXXXX-etzhayyim-organism-phase-3-vendor-decouple.md`)
once Phase 2 has run 30+ days clean in production.

# References

- ADR-2605061200 — active inference + persistent world model architecture
- ADR-2605061300 — real-world effect channel boundary
- ADR-2605071200 — myco-yeast organism Japanese naming
- ADR-2605071700 — graph-sos-intel-actor (vertex_agent_* tables)
- ADR-2605080600 — LangGraph Server + Granian L3 runtime
- ADR-2605091300 — bonsai cultivar metaphor
- ADR-2605091400 — MCP as cell membrane; lexicon = dual-wire SSoT
- ADR-2605010000 — RunPod 6000 Ada unified LLM pod
- ADR-2604251758 — murakumo-yoro actor worker fleet
- ADR-2605152100 — etzhayyim github org boundary
- ADR-2605172000 — etzhayyim RW-free substrate
- ADR-2605172100 — payments on-chain only
- ADR-2605172400 — etzhayyim / vendor 3-axis split rule
- deps.toml `myco-yeast-organism-bringup` (status="live", 2026-05-07)
- deps.toml `[platform.operating_entity]` — etzhayyim canonical identity
- deps.toml `[etzhayyim_agent]` — vendor relationship contract
