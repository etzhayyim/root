# hakoniwa 箱庭 — forward-simulation observatory (synthetic-persona swarm)

**ADR**: 2606111500 · **depends**: 2606111400 (synthetic-persona / forward-simulation
charter carve-in) + 2606051800 (mitooshi 見通し — distribution-only forecasting it feeds) +
2606042330 (entity-as-actor — public-entity mirrors) + 2606091200 (sonae 備え — resilience
consumer) + 2605242600 / 2605241900 (baien-edge swarm) + 2605215000 (Murakumo-only) +
2605312345 (Datom = canonical state) + 2605231525 (no-server-key) + 2605181100 (PII envelope
discipline). **Status**: 🟡 R0 — design + deterministic engine + tests (live swarm gated).

hakoniwa ("箱庭" = a contained miniature garden / sandtray world) is the **charter-clean
inversion of a swarm-intelligence prediction engine** — the shape of `666ghj/MiroFish`. Where
that class of system models **real people** to predict (and implicitly steer) public opinion,
hakoniwa runs a **contained miniature world** populated **only by FICTIONAL latent personas**
and reads out a **DISTRIBUTION over possible futures**, routed to **resilience & preparedness**.
It is the generative front-end that **feeds mitooshi 見通し**: mitooshi already had the
leak-free proper-scoring backtest loop but **no generative simulation engine**; hakoniwa
produces the distributions mitooshi scores.

It answers the question "is there a MiroFish-equivalent agent-based social-simulation
forecaster?" — there was not; entity-as-actor mirrors are static and mitooshi only scores.
hakoniwa is the missing generative layer between them, built so the core inversion holds:
**simulating fictional agents is categorically distinct from surveilling real people**
(ADR-2606111400).

## Hard gates (constitutional — read before any change)

- **G1 — FICTIONAL latent personas only, NEVER a real-person model.** Every `:persona` is
  `:persona/synthetic true` — a cohort archetype, not a real individual. **No PII, no
  real-person profile, no re-identifiable trait, no mapping to a natural person.**
  `world.assert_synthetic` **refuses at load** any persona missing the synthetic marker or
  carrying a PII-class field (`:email`, `:person/name`, `:geo/point`, …). Real **already-
  public** entities (an entity-as-actor `org.*` mirror, a public topic) may appear as their
  existing public mirror — **never a natural person**. This is the same move sukashi makes
  (synthesized fictional fraud entities) and tsumugi makes (latent influence nodes).
- **G2 — DISTRIBUTION-ONLY** (inherits mitooshi G1). The output is a **distribution** over the
  outcome (quantiles + histogram), **never a point**. `:forecast/point-asserted` is
  structurally `false` and **no `:forecast/point` field exists**. 非終末論 (no single foretold
  future) made structural — the p50 is reported as a *quantile*, never as "the prediction".
- **G3 — NON-STEERING** (inherits mitooshi G2). Routed to **resilience / preparedness /
  robustness**. `:forecast/use` and `:outcome/use` are a **resilience-only enum**; `:trade`,
  `:wager`, `:position`, `:target`, `:manipulate`, `:campaign` are **not members** and are
  unrepresentable (a breach raises). hakoniwa never trades, never targets a person, never runs
  an influence/persuasion campaign. It is *not* a persuasion optimiser — there is no objective
  that maximises influence, and no real people to influence.
- **G4 — TRANSPARENT & RECIPROCAL** (相互監視; ADR-2606082400 + 2606111400). The whole box —
  world graph, persona parameters, every step, the run config — is **plaintext-public** on
  kotoba; open-source + on-chain + 1 SBT = 1 vote. No covert/asymmetric modelling, because
  there are **no real people in the box** to watch unwatched.
- **G5 — Murakumo-only inference** (ADR-2605215000) for the LLM-persona variant; the swarm
  rides **baien-edge** (ADR-2605242600 / 2605241900). R0 ships the **deterministic kernel
  only** (no LLM in the test path).
- **G6 — sourcing honesty.** Personas `:synthetic`; real public facts `:authoritative |
  :representative`. A box is **illustrative**, never an exhaustive model of a real population.
- **G7 — leak-free as-of** (inherits mitooshi G5). The forecast record carries
  `:forecast/as-of`; no future information leaks into the persona priors; mitooshi scores it
  leak-free with proper scoring.
- **G8 — outward-gated & no-server-key** (ADR-2605231525). R0 = engine + seed scenario +
  tests. **Live large-swarm runs, ingest of real public-entity structure, and ANY social
  emission of a distribution require Council + operator DID**; no platform-held key signs a
  hakoniwa artifact.

## Layout

```
20-actors/hakoniwa/
├── CLAUDE.md                              # this file
├── README.md                             # short orientation
├── manifest.jsonld                        # actor manifest (4 cells, 8 gates)
├── deps.toml                             # per-actor manifest (pure-stdlib, no third-party)
├── data/
│   └── seed-scenario.kotoba.edn           # FICTIONAL town scenario (18 synthetic personas)
├── methods/                               # pure-stdlib (no numpy) → kotoba pywasm-runnable
│   ├── world.py                          # EDN loader + G1 assert_synthetic (refuses real persons)
│   ├── simulate.py                       # Friedkin-Johnsen forward kernel + K-replica ensemble
│   ├── distribution.py                   # ensemble → quantiles/histogram → mitooshi forecast record
│   └── datom_emit.py                     # kotoba Datom-log (EAVT) emitter — canonical state
├── tests/                                 # 13 tests, pure stdlib (network-free, deterministic)
│   ├── test_simulate.py
│   └── test_distribution.py
├── wasm/
│   └── README.md                          # kotoba pywasm actor (componentize-py) design
└── out/                                   # GENERATED — do not hand-edit
    ├── distribution-report.md            # the outcome distribution (quantiles + histogram)
    ├── forecast-record.kotoba.edn        # mitooshi-shaped :forecast/kind :distribution record
    └── scenario-datoms.kotoba.edn        # EAVT projection (ground world + transient distribution)
```

## Run

```bash
cd 20-actors/hakoniwa
python3 methods/simulate.py                       # ensemble summary (mean only — distribution via next)
python3 methods/distribution.py                   # → out/distribution-report.md + forecast-record.kotoba.edn
python3 methods/datom_emit.py                     # → out/scenario-datoms.kotoba.edn (EAVT)
python3 methods/distribution.py --steps 20 --replicas 256 --seed 11   # larger box (still deterministic)

python3 tests/test_simulate.py && python3 tests/test_distribution.py   # 13 green
```

## Simulation kernel (Friedkin-Johnsen opinion dynamics)

For each synthetic persona `i`, with susceptibility `λ_i ∈ [0,1]`, row-normalised incoming
`:influences` weights `w_ij`, and anchor `a_i` (= `:persona/initial-stance` + any active
`:signal/push` it is `:exposed-to`):

```
x_i(t+1) = λ_i · Σ_j w_ij · x_j(t) + (1 − λ_i) · a_i
```

This converges to a fixed point. **The ensemble** comes from running `K` replicas, each
perturbing anchors by a **deterministic seeded jitter** (`sha256(seed:replica:persona)` →
`[−amp, amp]`, **no `Math.random`**, pywasm-portable). The spread of the per-replica town-wide
weighted-mean stance **is** the forecast distribution — that is the only thing hakoniwa
asserts, and it asserts it as a distribution (G2). The LLM-persona variant (G5, gated) replaces
the scalar update with a Murakumo-routed persona step; the *interface* (synthetic agents →
ensemble → distribution → mitooshi) is identical.

## Ontology (hakoniwa-scenario-ontology, `00-contracts/schemas/`)

- **nodes** `:sim/kind` ∈ `{:persona, :entity, :signal, :outcome}` — persona
  (`:persona/synthetic :persona/cohort :persona/susceptibility :persona/initial-stance
  :persona/weight`), entity (`:entity/public-ref` — an already-public mirror), signal
  (`:signal/push :signal/at-step`), outcome (`:outcome/measures :outcome/statistic
  :outcome/use`).
- **edges** `:en/kind` ∈ `{:influences, :exposed-to, :holds-stance, :measures}` carrying
  `:en/weight`.
- **derived** `:bond/replica-outcome` · `:bond/distribution` — transient, computed on read,
  never persisted (N1/G2).

## Cross-links

`:entity/public-ref` can name an **entity-as-actor** public mirror (`org.*`) or a public
topic — never a natural person. The output `:forecast/kind :distribution` record is handed to
**mitooshi 見通し** (ADR-2606051800) for leak-free proper-scoring; the resilience readout is
consumed by **sonae 備え** / **kazaori 風折**. hakoniwa simulates a fictional box; it does not
surveil, predict-as-fact, or steer.
