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
  only; `:published` is not writable by ibuki — what actually went out is recorded as a
  member-attributed `:receipt/*` (see §R2). Default perception is the bounded
  `:representative` stimulus pattern; the live membrane (§R2) is read-only + allowlisted
  and enabled by explicit operator env.
- **N7 / 非終末論**: kotoba Datom log only; `:db/add` only — no retraction op exists.
- Closed vocabularies raise, never guess (joucho events, kaizen outcomes, queue schema v).

## R1 — the 18,342-organism fleet on durable checkpoints (same wave)

`methods/fleet.py` binds the FULL UNSPSC fleet (the committed monorepo registry
`00-contracts/actor-registry/unispsc.json`, 18,342 agents) to the durable substrate,
replacing the kotodama fleet cell's RAM-fragility (4,096-organism LRU whose state dies with
the pod) with log-native state:

- **No LRU needed for correctness** — an organism's state is never "evicted"; it is replayed
  from the log when its slice comes around.
- **Bounded beats at any fleet size** — each beat ticks the next `batch_size` organisms,
  round-robin over the shard via a DURABLE `:fleet.shard/cursor` datom; an incremental
  `:fleet.shard/drain-line` cursor guarantees each queue line is prepared EXACTLY once.
- **Single-pass log index** (`index_log`) — per-entity folds are O(log) each (quadratic
  poison at 18k organisms); the index recovers identical facts in one scan
  (`test_index_log_matches_per_entity_folds`).
- **Sharding mirrors fleet_cell_main** — jacob -1 (all) / joseph 0 (segments 10-29) /
  issachar 1 (30-44) / dan 2 (45-60); same env resolution
  (`UNISPSC_ORGANISM_SHARD_ALL` / `UNISPSC_ORGANISM_SHARD_INDEX` / `ETZHAYYIM_NODE`);
  the partition is asserted complete + disjoint against the real registry.
- **Crash-resume at fleet scale** — kill the runner mid-sweep, resume: head CID
  byte-identical to an uninterrupted sweep (`test_crash_resume_equals_uninterrupted_sweep`).
- **Verified at full scale** — `python3 fleet.py --cycles 9 --shard -1 --batch 2048 --fresh`
  brings all **18,342/18,342 organisms alive on one verified chain in ~35 s** (46 MB log,
  gitignored).
- `cells/fleet_beat/cell.py` `.solve()` raises — live cron deployment of continuous fleet
  operation stays Council Lv6+ + operator gated (G8), the same gate the kotodama fleet cell
  awaits.

## R2 — code-complete outward paths (Council gate exercised as PR merge)

Per founder direction 2026-06-10 (*「council ゲート = PR request の merge として、コード段階では
最後まで実装を進めてください」*), the Council gate for CODE-level completion is exercised as PR
review+merge (founder = sole Lv7+ member, 1/1 unanimity, consistent with the Charter §0.1
ratification precedent). Every outward path is therefore implemented to the end. What
distinguishes a *gate-flip* (merge-authorizable) from an *invariant* (structural, NOT
merge-flippable) is made explicit:

| path | implementation | what stays structural |
|---|---|---|
| live perception | `methods/perception.py` — READ-ONLY public XRPC membrane (`app.bsky.actor.getProfile` on the allowlisted public AppView; follower delta → capped closed-vocab joucho events; durable `:perception/*` snapshot datoms); wired into the fleet beat; enabled by `IBUKI_PERCEPTION_LIVE=1` | https GET + host allowlist (violation raises before I/O); reads NO credential; failure fails open to the representative pattern; offline beats emit no perception datoms (R1 head CIDs unchanged) |
| live posting | `methods/member_submit.py` — the MEMBER-principal runtime: `createSession` with the member's OWN env credentials (`IBUKI_MEMBER_*`) → `createRecord` on the member's OWN PDS, via `drainer.submit`'s injected-signer + operator-ack gate; CLI requires `--yes` | no env → refusal; **cron context (`IBUKI_CRON=1`) → refusal even WITH credentials** (a platform job may never hold a member key, ADR-2605231525); https only; nothing committed/cached/platform-held |
| receipt return edge | `methods/receipts.py` — member-submission receipts fold back onto the Datom log as `:receipt/*` (`:receipt/status :submitted-by-member`, `:receipt/submitted-by <member did>`) | ibuki still NEVER asserts `:published` — the receipt attributes the act to the member; organism posts stay `:dry-run` (two events, two attributions, one log) |
| cron cell | `cells/fleet_beat/cell.py` `.solve()` RUNS the durable fleet beat (env-resolved shard, bounded batch, local log); registered on joseph/issachar/dan in `50-infra/murakumo/fleet.toml` (cron 3/33/43 \* \* \* \*) | the cell prepares envelopes but can never post (member_submit refuses cron); Murakumo-only narration; local-log-only persistence |

End-to-end verified: 2 fleet beats (64 organisms, real registry) → 64 member-sign-ready
envelopes → member-signed submission (injected transport) → 64 `:receipt/*` datoms ingested
onto the SAME verified chain (`{'ok': True, 'length': 3}`).

## R3 — the local log lands on the LIVE kotoba engine (same wave)

The local EDN tx log was kotoba-native by design; R3 closes the final hop with
`methods/kotoba_bridge.py` + `methods/kaizen_outcomes.py`:

- **transact bridge** — each local tx becomes one
  `com.etzhayyim.apps.kotoba.datomic.transact` call against a running kotoba node
  (allowlist: loopback + EVO-X2 `:8077` only — anything else raises before I/O). The
  `graph` id is `KotobaCid::from_bytes(name)` recomputed in Python and **pinned against the
  CID the live engine accepted**; `expected_parent` chains remote commits (optimistic
  concurrency — a forked remote head fails loudly); every pushed tx carries `:ibuki.tx/*`
  provenance meta (local tx id / CID / prev) so the distributed graph maps back to the
  local commit-DAG; the push cursor is a `:bridge/*` checkpoint ON the local log
  (exactly-once: a re-run never resends). Default = no-I/O dry-run export;
  `IBUKI_KOTOBA_LIVE=1` to push. Operator auth = an explicitly **unsigned** bearer whose
  `sub` is the node's PUBLIC operator DID (`IBUKI_KOTOBA_OPERATOR_DID`) — the kotoba
  server documents loopback/edge as the signature trust boundary; **no key material is
  held or read** (engine reads on private graphs require the owner's CACAO and stay out
  of scope by design).
- **VERIFIED LIVE 2026-06-10** against the running local node (`kotoba-server`,
  `KOTOBA_STORE_PATH=~/.local/kotoba-etzhayyim/sled`): 2 fleet beats (16 organisms, real
  registry) pushed as 2 transacts → engine returned `status:ok`, per-tx `tx_cid` +
  `commit_cid`, **780 datoms confirmed**, IPNS head advanced; re-push sent only the bridge
  checkpoint (exactly-once observed live).
- **kaizen outcome collector** — `kaizen_outcomes.py` fills the Wave-4 outcomes file from
  the real source of truth (`gh pr view --json state`, operator-principal: operator's own
  `gh` auth, cron contexts refused, READ-ONLY — merge/close/comment unrepresentable);
  MERGED→merged / CLOSED→rejected / OPEN→pending feed `kaizen_feedback` end-to-end
  (collector → fold → suppression verified in one test).

### R0 scope honesty

- 3 `:representative` seed organisms in `autorun.py` demonstrate the single-organism loop;
  `fleet.py` (R1) runs the real 18,342-code registry offline.
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
- 134 tests across 13 standalone suites (`./run_tests.sh`), stdlib-only, hermetic; the
  engine hop additionally verified against the LIVE local kotoba node.
- Future: operator turn-up of the live flags on fleet nodes (IBUKI_PERCEPTION_LIVE /
  IBUKI_MURAKUMO_LIVE / IBUKI_KOTOBA_LIVE) + a member running member_submit against a
  real PDS + ameno passkey-session signer as an alternative member runtime + owner-CACAO
  read path for private-graph queries (kept out of scope: it would require wielding the
  node key).
