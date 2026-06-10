# ibuki (息吹) — organism autonomy R2 gap-closure substrate

**DID**: `did:web:etzhayyim.com:actor:ibuki` · **Tier**: substrate · **Status**: R0+R1 · **ADR**: 2606101200

**Read the root `/CLAUDE.md` Charter + substrate rules first.** ibuki-specific invariants below
OVERRIDE nothing in the Charter; they make it concrete for this package.

## The one-sentence identity

息吹 (ibuki = the breath of life) closes the seven gaps that kept the artificial-organism
programme (UNSPSC W1/W2, post sink, Kaizen) from being a closed autonomous loop: organism state
(joucho mood / heartbeat cadence / posts / kaizen learning) now lives **as-of queryable on the
append-only kotoba Datom log**, narration is **Murakumo-only**, posting is **member-signed
(Wave-3 drainer)**, and Kaizen outcomes **flow back** so the colony learns.

## The beat cycle (autorun.py)

```
replay ─▶ perceive ─▶ feel ─▶ decide ─▶ narrate ─▶ act ─▶ checkpoint ─▶ append tx
(log →    (beat       (event   (durable   (Murakumo-  (:dry-run    (joucho +     (content-
 durable   events,     fold →   cooldown    only /      post datom   heartbeat     addressed,
 state)    G8-bounded) mood)    due check)  template)   + queue)     datoms)       verified)
```

Crash-resume is structural: every beat replays the log, so a 2-beat run + death + 1 more beat
produces a head CID **byte-identical** to an uninterrupted 3-beat run.

## Gates — do NOT weaken (each has a test in test_charter_invariants.py)

- **G6 Murakumo-only** — `infer.MURAKUMO_ALLOWED_HOSTS` is the LiteLLM loopback + EVO-X2 LAN +
  per-node Ollama fleet (ADR-2605215000). Any other endpoint raises `MurakumoOnlyViolation`.
  Offline / failure → deterministic template (fail-open; the organism keeps living).
- **G7 no-server-key** — drainer envelopes carry `requiresMemberSignature:true` +
  `serverHeldKey:false`; `submit()` refuses without an injected member signer AND
  `operator_ack=True`; `drainer.py` has no network import and no credential read
  (ADR-2605231525).
- **G8 outward-gated** — `:post/status` is `:dry-run` only; `:drain/status` is `:prepared`
  only; `:published` is unwritable by ibuki. Perception at R0 is a bounded `:representative`
  stimulus pattern (no live firehose).
- **非終末論 append-only** — `:db/add` only; no retraction op exists; re-observation is a new
  datom, never an overwrite.
- **Closed vocabularies raise, never guess** — joucho event kinds, kaizen outcomes, queue
  schema version.
- **Stdlib only, deterministic** — no third-party imports; no wall clock (logical beat time);
  no SQL / columnar store (N7).

## Build / test / run autonomously

```
./run_tests.sh                                  # all 9 suites (90 tests), hermetic
cd methods && python3 autorun.py --cycles 6 --fresh   # AUTONOMOUS loop → kotoba Datom log
                                                # prints per-organism mood as-of tx 1 vs head
cd methods && python3 fleet.py --cycles 9 --shard -1 --batch 2048 --fresh
                                                # R1: FULL 18,342-organism fleet sweep on one
                                                # verified chain (~35 s; jacob/joseph/issachar/
                                                # dan sharding mirrors fleet_cell_main)
```

Generated artifacts (`data/ibuki*.datoms.kotoba.edn`, `data/*posts.queue.ndjson`) are
gitignored — the committed seed is `data/seed-organisms.kotoba.edn`; the R1 fleet universe is
the committed monorepo registry `00-contracts/actor-registry/unispsc.json` (18,342 agents).
R1 sweep state is durable: `:fleet.shard/cursor` (round-robin) + `:fleet.shard/drain-line`
(each queue line prepared EXACTLY once) are datoms, so a mid-sweep crash resumes losslessly.

## Do not

- Do not add a non-Murakumo host to `MURAKUMO_ALLOWED_HOSTS`, or make `narrate` skip
  `assert_murakumo` — G6.
- Do not give `drainer.py` a network path, a credential read, or a default signer — G7. The
  member's runtime is INJECTED, never embedded.
- Do not make `:published` writable, or wire `autorun.py` / `fleet.py` / perception to live
  external I/O — G8 (Council gate). `cells/fleet_beat/cell.py` `.solve()` raises at R1; do
  not wire it to a live cron trigger.
- Do not introduce a retraction op or mutate an existing log line — append-only (非終末論).
- Do not add a wall-clock call (`time.time`, `datetime.now`) to any method — determinism +
  crash-resume depend on logical time.
- Do not widen a closed vocabulary by accepting unknown members instead of raising.
