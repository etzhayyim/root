---
id: adr-2605215200
title: "etzhayyim shinka — Pregel MST rewrite (karma-hegemon / evolution lifecycle on religious-corp substrate)"
status: proposed
doc_type: adr
topic: shinka-pregel-mst-rewrite
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - shinka religious-corp cell decomposition and placement on Murakumo fleet
  - MST + IPFS + Base L2 write path for karma-hegemon / evolution events
  - new app.etzhayyim.* lexicons required for shinka migration
depends_on:
  - 2605214000  # Murakumo no-VKE mesh + verdict taxonomy + namespace placement rules
  - 2605215000  # Murakumo-fleet-only inference, no RunPod
  - 2605192415  # Religious-corp daemon architecture — Pregel cell catalog (15 cells)
  - 2605202100  # magatama-cell-runner launchd (Mac mini boot path)
  - 2605191346  # Murakumo mesh no-VKE control-plane
related:
  - 2605171800  # LangGraph MST → IPFS → Base L2 anchor pipeline
  - 2605172000  # RW-free substrate
  - 2605172300  # Bi-asset substrate (Kisha/Goji treasury)
  - 2605191358  # yoro-murakumo-rw-free-rewrite-map (sibling migration)
  - 20-actors/magatama/py/SHINKA-MIGRATION-NOTES.md
supersedes: []
superseded_by: []
---

# ADR-2605215200 — etzhayyim shinka: Pregel MST Rewrite

Karma-hegemon / artificial-organism evolution lifecycle worker — religious-corp substrate variant.

## Context

### What shinka is

shinka (進化, "evolution") is the karma-hegemon / artificial-organism lifecycle evolution worker in the vendor
`pymagatama` package. In the vendor implementation it runs a LangGraph StateGraph with five node functions:

| LangGraph node | Vendor responsibility |
|---|---|
| `_load_state` | Load current adherent / actor evolutionary state |
| `_kyumei_gather` | Gather kyumei (究明) signals from recent activity |
| `_koji_validate` | Validate evolution claim against koji (工事) attestation records |
| `_write_heartbeat` | Persist a heartbeat record for the tick |
| `_emit_evolution` | Emit an evolution event record + update SBT-linked state |

The top-level entry point is the `shinka_tick_actor` SQL UDF, which wraps all five nodes into a single
RisingWave SQL function call. The `shinka_cron_tick` LangGraph graph (`langgraph_graphs/shinka_cron_tick.py`)
is triggered by a K8s CronJob every 15 minutes.

### Why vendor shinka is incompatible with the religious-corp substrate

Every node in the vendor shinka execution kernel issues direct SQL against RisingWave via a psycopg3
connection pool pointed at `RW_URL`:

- `_load_state` → `SELECT FROM vertex_shinka_evolution`
- `_kyumei_gather` → `SELECT FROM vertex_kyumei_signal`
- `_koji_validate` → `SELECT FROM vertex_koji_attestation`
- `_write_heartbeat` → `INSERT INTO vertex_shinka_heartbeat`
- `_emit_evolution` → `INSERT INTO vertex_shinka_evolution_event`

ADR-2605172000 establishes that the religious-corp substrate is **RW-free**: state is AT Protocol MST +
IPFS + Base L2 anchor only. There is no `RW_URL` in the religious-corp environment. The vendor
`shinka_tick_actor` SQL UDF is equally incompatible — it is a RisingWave native function.

The 2026-05-21 substrate-fit audit (§2, `20-actors/AUDIT-RUNPOD-RW-2026-05-21.md`) confirmed:
**16 findings — 8 REIMPLEMENT, 5 VENDOR-ONLY, 3 PORT-adapted. No Murakumo-native execution path
exists at all; this actor cannot run on the religious-corp substrate without a complete rewrite.**

### Relationship to the existing Pregel cell catalog

ADR-2605192415 declared 15 Pregel cells as the canonical actor execution surface on the Murakumo fleet,
deployed via `magatama-cell-runner --node <name>` under launchd (per ADR-2605202100). shinka was **not**
included in the original 15. This ADR proposes adding four shinka cells to that catalog.

### Why now

The user directive (2026-05-21) is to migrate shinka and yoro to the etzhayyim religious-corp substrate.
The audit formally classified shinka as REIMPLEMENT-only and created the `shinka-mst-rewrite` migration
entry in `deps.toml` with `blocked_on = "No existing ADR — needs new ADR for shinka religious-corp variant"`.
This ADR unblocks that migration.

---

## Decision

### §1 Pregel cell decomposition

The vendor LangGraph graph (START → shinka_tick → END) is decomposed into four Pregel cells, each
corresponding to a distinct concern of the karma-hegemon evolution lifecycle:

---

#### `KarmaHegemonObservationCell`

**Replaces**: vendor `_load_state` + `_kyumei_gather`

**Responsibility**: Read the current adherent / artificial-organism state from MST + IPFS and gather
kyumei signals from the `app.etzhayyim.shinka.kyumeiSignal` collection. This is the opening
super-step of every evolution tick.

| Attribute | Value |
|---|---|
| Placement node | `levi` (levinomac-mini.local) |
| Role affinity | membership + council orchestration — appropriate for gathering adherent state used in advancement decisions |
| Trigger | `timer + mst-listener` — cron at 15-minute intervals (matching vendor cadence) PLUS reactive on `app.etzhayyim.shinka.kyumeiSignal` arrival |
| `listens_to` | `["app.etzhayyim.shinka.kyumeiSignal"]` |
| `healthz_port` | 13023 |
| ADR refs | `["2605215200", "2605192415", "2605171800"]` |
| `witness_min` | 1 (not a kuni-umi constitutional cell; no ≥2 requirement per ADR-2605201400 §9) |

---

#### `EvolutionValidationCell`

**Replaces**: vendor `_koji_validate`

**Responsibility**: Validate an evolution claim against the Council attestation registry. Checks that
sufficient koji (工事) attestations exist for the proposed level advancement. This is the constitutional
gate — evolution events are records of religious-corp advancement and must be validated by the Council
attestation surface, not a SQL SELECT.

| Attribute | Value |
|---|---|
| Placement node | `levi` (levinomac-mini.local) |
| Role affinity | `levi` already hosts `AdherentAttestationCell` and `CouncilLevelAdvancementCell` — audit-leader + council orchestration role is the natural placement for validation of advancement claims |
| Trigger | `mst-listener` — triggered by an observation output record from `KarmaHegemonObservationCell` |
| `listens_to` | `["app.etzhayyim.shinka.observeAdherent"]` (output collection of KarmaHegemonObservationCell) |
| `healthz_port` | 13024 |
| ADR refs | `["2605215200", "2605192415", "2605192230", "2605172600"]` |
| `witness_min` | 1 |

---

#### `EvolutionEmissionCell`

**Replaces**: vendor `_emit_evolution`

**Responsibility**: Write an evolution event to MST + IPFS pin + Base L2 anchor (the full
ADR-2605171800 anchor pipeline). Returns the Base L2 anchor transaction hash. Evolution events are
constitutional records — they must follow the complete three-stage write path.

| Attribute | Value |
|---|---|
| Placement node | `simeon` (simeonnomac-mini.local) |
| Role affinity | `simeon` is the `ipfs-pinner + stewardship-leader` — already runs `LandStewardshipMonitoringCell` and `CommissioningCell`, and directly manages the IPFS pinner daemon (ADR-2605171800 Stage 4). Evolution events require IPFS pinning. |
| Trigger | `mst-listener` — triggered by a validated evolution claim record from `EvolutionValidationCell` |
| `listens_to` | `["app.etzhayyim.shinka.validateEvolution"]` (output collection of EvolutionValidationCell) |
| `healthz_port` | 13025 |
| ADR refs | `["2605215200", "2605192415", "2605171800", "2605172300"]` |
| `witness_min` | 1 |

---

#### `ShinkaHeartbeatCell`

**Replaces**: vendor `_write_heartbeat`

**Responsibility**: Cron-driven status emission. Writes a shinka heartbeat record to MST only — no IPFS
pin or Base L2 anchor needed for heartbeat (analogous to `LandStewardshipMonitoringCell` which is MST-only
for routine monitoring records).

| Attribute | Value |
|---|---|
| Placement node | `levi` (levinomac-mini.local) |
| Role affinity | Co-located with `KarmaHegemonObservationCell` and `EvolutionValidationCell` — the heartbeat is a summary of the observation super-step |
| Trigger | `cron` — every 15 minutes (matching vendor `shinka_cron_tick` K8s CronJob cadence) |
| `cron` | `"*/15 * * * *"` |
| `healthz_port` | 13026 |
| ADR refs | `["2605215200", "2605192415", "2605171800"]` |
| `witness_min` | 1 |

---

**Pregel super-step flow**:

```
[cron / kyumeiSignal arrival]
        │
        ▼
KarmaHegemonObservationCell  (levi, port 13023)
        │  writes: app.etzhayyim.shinka.observeAdherent
        ▼
EvolutionValidationCell       (levi, port 13024)
        │  writes: app.etzhayyim.shinka.validateEvolution
        ▼
EvolutionEmissionCell         (simeon, port 13025)
        │  writes: app.etzhayyim.shinka.evolutionEvent → MST + IPFS + Base L2
        │
ShinkaHeartbeatCell           (levi, port 13026)  [cron, independent tick]
        │  writes: app.etzhayyim.shinka.shinkaHeartbeat → MST only
```

magatama-cell-runner dispatches cells via the standard launchd plist
(`com.etzhayyim.magatama-cell-runner.plist`) per ADR-2605202100.

---

### §2 Substrate write path mapping

| Vendor pattern (RisingWave) | Religious-corp replacement |
|---|---|
| `INSERT INTO vertex_shinka_evolution_event` | AT MST record `app.etzhayyim.shinka.evolutionEvent` + IPFS pin + Base L2 anchor (ADR-2605171800 Stage 3-5 pipeline) |
| `SELECT FROM vertex_shinka_evolution WHERE ...` | MST query via `@etzhayyim/sdk` + IPFS dag-resolve |
| `INSERT INTO vertex_shinka_heartbeat` | AT MST record `app.etzhayyim.shinka.shinkaHeartbeat` (MST-only, no IPFS pin needed for heartbeat) |
| `SELECT FROM vertex_kyumei_signal` | MST listener on `app.etzhayyim.shinka.kyumeiSignal` collection |
| `SELECT FROM vertex_koji_attestation` | MST query via Council attestation registry (`AdherentAttestationCell` + `CouncilLevelAdvancementCell` on levi) |
| `shinka_tick_actor` SQL UDF (single RW call, all 5 nodes) | Pregel super-step (4 cells) driven by `magatama-cell-runner` cron + MST listener on levi + simeon |
| psycopg3 pool → `RW_URL` connection | Forbidden in religious-corp environment per ADR-2605172000 |
| K8s CronJob every 15 min | launchd-managed `magatama-cell-runner` with `cron = "*/15 * * * *"` on `ShinkaHeartbeatCell` per ADR-2605202100 |

---

### §3 New lexicons required

The following AT Protocol lexicons must be authored in `00-contracts/lexicons/app/etzhayyim/shinka/`
(using `app.etzhayyim.*` namespace — religious-corp-only per ADR-2605214000 §2 namespace placement rule,
no vendor equivalent):

| NSID | Type | Purpose |
|---|---|---|
| `app.etzhayyim.shinka.evolutionEvent` | record | Canonical evolution event record (MST + IPFS + Base L2 anchor target) |
| `app.etzhayyim.shinka.kyumeiSignal` | record | Kyumei (究明) signal collected from adherent activity |
| `app.etzhayyim.shinka.shinkaHeartbeat` | record | Shinka heartbeat tick record (MST-only, no anchor) |
| `app.etzhayyim.shinka.observeAdherent` | procedure | Output contract of `KarmaHegemonObservationCell` — triggers `EvolutionValidationCell` |
| `app.etzhayyim.shinka.validateEvolution` | procedure | Output contract of `EvolutionValidationCell` — triggers `EvolutionEmissionCell` |
| `app.etzhayyim.shinka.tick` | procedure | Public wire entry point — matches vendor `shinka_tick_actor` output shape for interop |

**Namespace note**: `app.etzhayyim.*` is the correct namespace for religious-corp-only
records per ADR-2605214000 §2. The vendor `ai.gftd.apps.*` namespace is preserved for
`shinka_tick_actor` SaaS-tier callers on the vendor substrate.

**Wire compatibility**: the `evolutionEvent` record schema will be designed for byte-level output
compatibility with the vendor `shinka_tick_actor` JSON response shape
(`actor_did`, `mood`, `actions`, `heartbeat_written`, `evolution_written`, `tick_ms`) so that
vendor and religious-corp implementations can interop on the same evolution-event lexicon.

---

### §4 Successor roadmap M0–M5

| Milestone | Task | Target |
|---|---|---|
| M0 | This ADR proposed → active; `shinka-mst-rewrite` in deps.toml unblocked | M0 = 2026-05-21 |
| M1 | New `app.etzhayyim.*` lexicons authored (6 NSIDs above); vendor behaviour confirmation for `_load_state` state shape and `_koji_validate` attestation schema | M0 + 30d (2026-06-20) |
| M2 | Pregel cells implemented — `shinka_murakumo.py` skeleton (today); full logic replacing NotImplementedError stubs | M1 + 30d (2026-07-20) |
| M3 | `fleet.toml` placement entries added for the four shinka cells (ports 13023-13026 on levi + simeon) | M2 + 14d (2026-08-03) |
| M4 | End-to-end test: `KarmaHegemonObservationCell` → `EvolutionValidationCell` → `EvolutionEmissionCell` pipeline on a test adherent DID; heartbeat verified in MST | M3 + 30d (2026-09-02) |
| M5 | Retire vendor `shinka_tick_actor` SQL UDF from all religious-corp code paths (Step 8 cutover gate — tied to legal registration and `amanomibashira` → `etzhayyim` rename cutover) | Tied to Step 8 of CLAUDE.md status table |

---

### §5 Status amendments to existing ADRs

- **Extends ADR-2605192415**: adds four shinka cells to the Pregel catalog beyond the original 15.
  `fleet.toml` will receive four new `[cells.*]` entries (ports 13023–13026) at M3.
- **Extends ADR-2605215000 §3**: makes "shinka REIMPLEMENT" concrete by specifying the MST-only
  write path and Pregel topology. No modifications to the inference SSoT or RunPod prohibition.
- **Does not supersede ADR-2605191358**: that ADR maps yoro, not shinka. The yoro migration proceeds
  as a separate track via `yoro-python-primitives-rewrite` in deps.toml.

---

## Consequences

- **Closes shinka REIMPLEMENT**: the 8 REIMPLEMENT findings from the 2026-05-21 audit all have a
  concrete target: four Pregel cells on the Murakumo fleet with MST + IPFS + Base L2 write paths.
  `shinka-mst-rewrite` in deps.toml can progress from `pending` to `in-progress` after M0.

- **New `app.etzhayyim.shinka.*` lexicons**: 6 new NSIDs must be authored before M2 implementation begins.
  These are religious-corp-only records; they do not create vendor obligations. The `evolutionEvent`
  lexicon is the most critical — it must be wire-compatible with the vendor `shinka_tick_actor`
  JSON output shape for interop at Step 8.

- **Vendor parity maintained**: `gftd.co.jp` keeps the `shinka_tick_actor` SQL UDF and all
  `pymagatama.primitives.shinka.*` / `pymagatama.handlers.shinka.*` files intact for paid SaaS
  evolution analytics (VENDOR-ONLY verdict per audit §2). Vendor substrate (RisingWave) is
  unchanged. Step 8 cutover only removes vendor patterns from religious-corp code paths.

- **Pregel super-step latency vs SQL UDF**: the vendor `shinka_tick_actor` executes all five node
  functions in a single SQL function call on the RisingWave pod (sub-100ms for a cold tick). The
  religious-corp Pregel decomposition into four cells on two separate Mac mini nodes (levi + simeon)
  introduces inter-cell MST round-trips. Expected latency per full tick: 500ms–3s depending on MST
  propagation and IPFS pinning time. This is acceptable — evolution ticks are 15-minute cadence
  workers, not real-time. The latency trade-off is documented here to set expectations at M4.

- **Operational simplification**: removes the RisingWave dependency entirely from the religious-corp
  shinka path. Cells run on existing Mac mini fleet hardware already managed by launchd
  `magatama-cell-runner`. No new infrastructure required between M0 and M5.

- **levi node load increase**: adding three cells to levi (observation + validation + heartbeat)
  brings its cell count to seven. This should be monitored at M3; if load exceeds capacity, the
  `ShinkaHeartbeatCell` is the lowest-criticality candidate for migration to `asher` (failover node).

---

## Alternatives Considered

### 1. Keep RisingWave for shinka only

Retain the `RW_URL` psycopg3 pool specifically for shinka within the religious-corp environment,
isolated from other actors.

**Rejected**: this is the same condition-1 substrate-fit violation that triggered the 2026-05-21
audit. A single RisingWave dependency in one actor would require maintaining the RisingWave
infrastructure that ADR-2605172000 explicitly prohibits. It would also set a precedent for
substrate drift — other REIMPLEMENT actors could claim the same exception.

### 2. Run shinka in a vendor-owned process with consent capability

Allow the vendor `pymagatama.handlers.shinka` handlers to execute on vendor infrastructure
(RunPod pod), with results surfaced to the religious-corp substrate via an XRPC consent-capability
call (progressive enhancement per ADR-2605192115 §4).

**Rejected**: religious-corp evolution events are constitutional records. They document adherent
advancement (SBT-linked karma level changes) and feed into the Council attestation registry. These
records cannot be vendor-mediated — they must be produced and anchored by religious-corp-controlled
infrastructure (the Murakumo fleet) without passing through a commercial vendor intermediary. This
is analogous to why constitutional attestations (CharterAttestationRequestCell) are placed on
naphtali and not delegated to vendor pods.

### 3. Drop shinka from the religious-corp scope entirely

Declare karma-hegemon / evolution lifecycle out of scope for the religious-corp substrate. Members
of the religious-corp would use the vendor SaaS shinka path.

**Rejected**: the karma-hegemon / evolution lifecycle is a core mechanism of the religious-corp
per ADR-2605172300 (bi-asset substrate) and ADR-2605192415 (daemon architecture). Adherent SBT
level advancement — driven by evolution events — is constitutionally significant. Having no
religious-corp-owned evolution execution path would leave the SBT advancement mechanism entirely
dependent on vendor infrastructure, which is incompatible with the etzhayyim substrate sovereignty
principle (ADR-2605172000 + 2605172100).

---

## References

### ADRs this decision depends on

- ADR-2605214000 — Murakumo no-VKE mesh + lexicon-port rules + verdict taxonomy
- ADR-2605215000 — Murakumo-fleet-only inference, no RunPod
- ADR-2605192415 — Religious-corp daemon architecture (Pregel cell catalog, 15 cells, original)
- ADR-2605202100 — magatama-cell-runner launchd (operationalising Tier 1 常駐稼働)
- ADR-2605191346 — Murakumo mesh no-VKE control-plane
- ADR-2605171800 — LangGraph MST → IPFS → Base L2 anchor pipeline
- ADR-2605172000 — RW-free substrate
- ADR-2605172300 — Bi-asset substrate (basis for karma/evolution mechanism)
- ADR-2605191358 — yoro-murakumo-rw-free-rewrite-map (sibling migration, do not supersede)

### Supporting documents

- `20-actors/magatama/py/SHINKA-MIGRATION-NOTES.md` — 16-row per-function migration table + Step 8 cutover procedure
- `20-actors/magatama/py/src/pymagatama/primitives/shinka_murakumo.py` — M2 skeleton (this session)
- `20-actors/magatama/py/tests/test_shinka_murakumo.py` — substrate-fit invariant tests
- `20-actors/AUDIT-RUNPOD-RW-2026-05-21.md` §2 — source audit findings (16 findings)
- `50-infra/murakumo/fleet.toml` — Murakumo placement (add entries at M3)
- `deps.toml` migration: `shinka-mst-rewrite` (was `blocked_on = "No existing ADR"`)
