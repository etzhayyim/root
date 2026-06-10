---
id: adr-2606101200-ibuki-organism-autonomy-r2-gap-closure
title: "ADR-2606101200: 息吹 (ibuki) — organism autonomy R2 gap-closure substrate (as-of state on kotoba · durable heartbeat · Murakumo narration · Wave-3 drainer · Wave-4 kaizen feedback)"
status: accepted
doc_type: adr
topic: ibuki-organism-autonomy-gap-closure
authoritative: true
last_verified: 2026-06-10
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - ibuki-organism-autonomy-substrate
  - organism-state-as-of-kotoba
  - organism-wave3-post-drainer
  - organism-wave4-kaizen-feedback
depends_on:
  - adr-2605232345-unspsc-organism-w1
  - adr-2605240000-unspsc-organism-w2-mass-deploy
  - adr-2605240100-unspsc-post-sink
  - adr-2605240200-kaizen-self-reflection
  - adr-2606072200-shionome-cross-asset-capital-flow-observatory-r0
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
related:
  - adr-2605270930-organism-r0-r1-sprint
  - adr-2606051800-mitooshi-probabilistic-forecasting-observatory
  - adr-2606082500-kaizen-github-independent-self-evolution-kotoba-git
supersedes: []
superseded_by: []
---

# ADR-2606101200: 息吹 (ibuki) — organism autonomy R2 gap-closure substrate

- **Status**: accepted
- **Date**: 2026-06-10 (JST)
- **Deciders**: founder seat
- **Supersedes / amends**: none — ZERO invariant amendments. Closes implementation gaps; every
  existing gate (no-server-key, Murakumo-only, outward-gated) is *kept and made structural*.

## Context

The artificial-organism programme (heartbeat-cadence W1, 18,342-organism mass-deploy W2, post
sink, Kaizen self-reflection) is architecturally coherent but the loop does not close. A
2026-06-10 survey of "actors autonomously inferring and growing on kotoba" found seven gaps:

1. **No durable scheduler** — cadence cooldowns lived in process RAM; a pod death between
   ticks lost state.
2. **WASM/cron runtime is fire-and-forget** — nothing recovered an organism's place in time.
3. **Organism state was not on the kotoba Datom log** — joucho / cadence / lifecycle were
   ephemeral Python dicts; "what was this organism's mood at tx N" was unanswerable, violating
   the spirit of ADR-2605312345 (kotoba Datom log = first-class canonical state).
4. **Joucho was a constant stub** (50/50/30/50/50) — mood never moved, cadence never varied,
   personality never emerged.
5. **Inference was not wired into the tick** — the Murakumo path existed (ADR-2605302355) but
   organisms posted templated text only.
6. **Wave-3 drainer unbuilt** — posts accumulated in the NDJSON queue; nothing turned them
   into member-signable atproto records.
7. **Kaizen was one-way** — proposals flowed out; merge/reject outcomes never flowed back, so
   the observer could not learn.

shionome (ADR-2606072200) already demonstrated the charter-permitted form of autonomy: an
offline heartbeat loop that persists content-addressed transactions to a local append-only
kotoba Datom log, with live external I/O gated. ibuki applies that proven pattern to the
organism layer.

## Decision

Create **`20-actors/ibuki/`** (息吹 — the breath of life; heartbeat + 産霊), a pure-stdlib
substrate package that closes gaps 1–7. One module per gap, one integrating loop:

| module | closes | mechanism |
|---|---|---|
| `methods/datoms.py` | 3 | content-addressed append-only EAVT tx log (sha256 commit-DAG, shionome-isomorphic) + as-of readers (`fold_entity` / `entities` / `events_for`) |
| `methods/joucho.py` | 4 | deterministic per-code personality baseline (stress axis bounded [25,65] — stress comes from lived events, never temperament) + CLOSED event vocabulary folded into 5-axis scores; mood = replay of the persisted `:joucho.event/*` stream → **as-of queryable, emergent** |
| `methods/heartbeat.py` | 1, 2 | `:heartbeat/*` checkpoint datoms per beat; `replay()` recovers exact cadence state from the log; `due_to_post()` is a pure function of (log, mood, logical now) — crash-resume changes nothing |
| `methods/infer.py` | 5 | narration via the Murakumo fleet ONLY (host:port allowlist; any other endpoint raises `MurakumoOnlyViolation` before any gate is consulted); offline/failed → deterministic template (fail-open) |
| `methods/drainer.py` | 6 | consumes the ADR-2605240100 v=1 NDJSON queue → `com.atproto.repo.createRecord`-shaped envelopes with `requiresMemberSignature:true` / `serverHeldKey:false`; `submit()` only forwards to an externally-injected member signer + explicit operator ack; module has **no network and no credential path** |
| `methods/kaizen_feedback.py` | 7 | folds proposal outcomes (merged/rejected/pending, closed vocab) into per-rule stats; ≥3 consecutive rejections suppress a rule for 12 beats (`should_emit` gate); outcomes also map to joucho events (merge calms, rejection stresses) — the colony learns through the log while humans stay the decision-makers (ADR-2605240200 auto-apply remains rejected) |
| `methods/autorun.py` | all | the beat cycle: replay → perceive → feel → decide → narrate → act (`:post/status :dry-run` datom + queue line) → checkpoint → append one content-addressed tx; logical time only |

### Determinism + durability invariants (tested)

- Same seed + same cycle count → **identical head CID**.
- 2 beats, process death, 1 more beat → head CID **byte-identical** to an uninterrupted 3-beat
  run (`test_crash_resume_equals_uninterrupted_run`) — nothing lives only in RAM.
- `verify_chain` recomputes every CID; tamper anywhere breaks every later CID.

### Gates kept (structural, each with a test)

- **G6 Murakumo-only** (ADR-2605215000): allowlist ⊆ {LiteLLM loopback :4000, EVO-X2 LAN
  192.168.1.70, per-node Ollama :11434}; commercial endpoints unrepresentable.
- **G7 no-server-key** (ADR-2605231525): ibuki holds no key, reads no env/credential, has no
  network path in the drainer; posting without an injected member signer raises.
- **G8 outward-gated**: `:post/status` is `:dry-run` only; `:drain/status` is `:prepared`
  only; `:published` is not writable by ibuki — only a member-signed submission receipt
  (ingested separately, future R1) may assert it. R0 perception is a bounded
  `:representative` stimulus pattern; live firehose perception stays Council-gated.
- **N7 / 非終末論**: kotoba Datom log only; `:db/add` only — no retraction op exists.
- Closed vocabularies raise, never guess (joucho events, kaizen outcomes, queue schema v).

### R0 scope honesty

- 3 `:representative` seed organisms stand in for the 18,342-code fleet; R1 binds the
  kotodama fleet cell (`fleet_cell_main.py`) to these durable checkpoints.
- The drainer prepares; it cannot publish. Live submission needs the member's own signing
  runtime (ameno passkey session) + operator ack — one human gate-flip away, per design.
- Kaizen outcomes arrive via an operator-written NDJSON file (from `gh pr view`), not via
  ibuki reaching out to GitHub (cf. ADR-2606082500 for the kotoba-git direction).

## Consequences

- The organism loop is closed in its charter-permitted form: an organism now lives, feels,
  remembers, narrates, and learns **on the canonical substrate**, with every outward edge
  member-signed and operator-gated.
- "What was organism X's mood at tx N" is now a pure log query — Wellbecoming as as-of
  history (ADR-2606011500's discipline) reaches the organism layer.
- 78 tests across 8 standalone suites (`./run_tests.sh`), stdlib-only, hermetic.
- Future: R1 = kotodama fleet-cell binding + ameno member-signing runtime for the drainer;
  R2 = live perception membrane (G8 Council gate) + Murakumo live narration on fleet nodes.
