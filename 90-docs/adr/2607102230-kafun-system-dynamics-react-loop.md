---
id: adr-2607102230-kafun-system-dynamics-react-loop
title: "ADR-2607102230: kafun 花粉 — a system-dynamics ReAct loop over remediation readiness"
status: accepted
doc_type: adr
topic: kafun-system-dynamics-react-loop
authoritative: true
last_verified: 2026-07-10
authoritative_for:
  - "kafun's forecasting/reasoning layer over `remediate/remediation-bottlenecks` is `methods/dynamics.cljc` (kafun's OWN readiness stock-flow) + `methods/react_loop.cljc` (the ReAct beat) — not a reuse of `etzhayyim.ie-flow.dynamics` (a differently-shaped SaaS stock) nor of tsuchifumi's `sysdyn.cljc` (a separate risk-domain E/A/I/B model)"
  - "the readiness stock-flow NEVER duplicates or relaxes the verdict gate — every forecasted stand is re-scored through the UNCHANGED `remediate/verdict`, so G1 (撲滅=restoration) / G4 (carbon) hold through a forecast exactly as they hold live"
  - "ACT is a PRE-REGISTERED forecast + a proposal ROUTED to the relevant downstream actor (sanae for sapling-supply / musubi for consent) — G5 (never-acts) is unchanged: kafun still supplies no sapling and grants no consent itself, forecast or not"
related:
  - 90-docs/adr/2606211712-kafun-pollen-remediation-actor.md
  - 90-docs/adr/2606201200-ibuki-coscientist-entropy-react-loop.md
  - 90-docs/adr/2606212030-kafun-ie-flow-energy-visualization.md
  - 90-docs/adr/2607072630-etzhayyim-com-etzhayyim-yosoku-system-dynamics-actor.md
supersedes: []
superseded_by: []
---

# ADR-2607102230: kafun 花粉 — a system-dynamics ReAct loop over remediation readiness

**Status**: accepted
**Date**: 2026-07-10
**Deciders**: Jun Kawasaki (owner instruction: design + implement a "system dynamics react
loop" for the kafun 花粉撲滅 actor, following up on ADR-2606211712 R0)

## Context

- kafun's R0 gate (`remediate.cljc`) is a pure, on-read verdict function: a stand's
  `pollen-burden`/`reforest-viability`/consent/protection/sapling-supply state maps
  deterministically to one of `{:refuse :await-consent :protected-selective
  :await-sapling-supply :reforest-priority :monitor}`. `remediation-bottlenecks` (landed in a
  follow-up commit, `32a8adc593`) already names WHICH blocking stage (the L1-1 無花粉苗木
  bottleneck or the consent bottleneck) jams the most stands and the counterfactual value of
  resolving it — but that view is STATIC: it answers "what if this blocker were fully resolved
  right now," not "how does the pipeline evolve as readiness accumulates over time."
- Two established patterns in this monorepo compose naturally to answer the "over time"
  question: **system dynamics** (a Forrester/Meadows-style stock-flow model — `tsuchifumi/
  methods/sysdyn.cljc`, the shared `etzhayyim.ie-flow.dynamics` `step-system`/`simulate`/
  `counterfactual` shape) and the **ReAct loop** (`ibuki/methods/react_loop.cljc`, ADR-2606201200:
  SENSE→ORIENT→HYPOTHESIZE→REVIEW→RANK→EVOLVE→ACT→OBSERVE→LEARN→PERSIST, a leak-free
  pre-registered-forecast-then-score cycle). kafun's OWN ADR-2606212030 already lists the ibuki
  react-loop ADR as `related`, so this ADR is closing a gap the design already anticipated.
- **The obvious pitfall**: naively copying ibuki's ACT step (which pre-registers a real dry-run
  EXPERIMENT the organism itself enacts) would put an ACT phase inside kafun — but kafun's G5
  invariant is stronger than ibuki's: kafun **never acts at all**, not even a dry-run of its
  own actuation. The design below keeps ACT strictly as "pre-register a FORECAST + route a
  PROPOSAL," never an experiment kafun itself carries out.
- **The obvious wrong reuse**: `etzhayyim.ie-flow.dynamics/step-system` has a stock shape
  (`:customers :trust :data-asset :model-quality :reserves`) and formulas (churn/spam/failures/
  revenue/cost) for a SaaS-shaped negentropy source — the wrong domain for forest stands.
  tsuchifumi's `sysdyn.cljc` is a separate risk-domain (E/A/I/B) model. Neither is kafun's
  domain. A new, actor-owned `dynamics.cljc` with kafun's OWN stock is the correct fit — the
  same reason `ie_flow.cljc` EMBEDS the shared ie-flow METRICS (order calculus) but each actor
  still supplies its own domain `config`/value model.

## Decision

Two new files in `20-actors/kafun/methods/`:

### `dynamics.cljc` — the readiness stock-flow (kafun's OWN domain, not a shared/generic stock)

- **Stock**: `{:supply-level :consent-level :cumulative-unblocked}` — `:supply-level` and
  `:consent-level` ∈ [0,1] accumulate toward a `ready-threshold` (1.0) exactly like a bathtub
  filling before it overflows (a legitimate SD pattern: continuous accumulation crossing a
  discrete gate). `:cumulative-unblocked` is a DERIVED count, not an independent stock.
- **Flow / inputs**: `{:supply-rate :consent-rate}` — a HYPOTHETICAL external readiness rate.
  kafun MODELS this; it never supplies sapling or grants consent itself (G5) — exactly the same
  epistemic status as `remediate/blocker-relax`'s existing hypothetical unblock.
- **`step-system`/`simulate`/`counterfactual`** mirror `etzhayyim.ie-flow.dynamics`'s shape
  (`(reductions step-system …)`) but over kafun's OWN stock — a parallel implementation, not an
  extension of the shared one (their stock shapes are incompatible; forcing a shared function
  over two unrelated domains would require either genericizing away all domain meaning or
  smuggling forest-stand fields into a SaaS-shaped record).
  - **`readiness-snapshot`** is the load-bearing correctness primitive: it re-scores the FIXED
    `stands` (never mutated, G5) with `:sapling-supply`/`:consent` flipped wherever readiness
    has crossed the threshold, then `step-system` counts `:reforest-priority` verdicts THROUGH
    THE UNCHANGED `remediate/verdict`. **There is no duplicate or relaxed gate** — a forecast
    can never make a `replant=false` or carbon-positive stand advance, because it runs through
    literally the same gate function a live assessment does (test-enforced,
    `hard-refusals-hold-through-the-forecast-g1-g4`).

### `react_loop.cljc` — the ReAct beat (mirrors ibuki's shape; ACT is propose-only)

```
SENSE      fold this loop's OWN ledger for the last readiness stock + prior forecast, advance
           by one step of a REALIZED (R0-representative) readiness rate
ORIENT     surprise = |prior forecast − now-realized cumulative-unblocked| (leak-free)
HYPOTHESIZE  candidate readiness-rate scenarios restricted to the CURRENT binding constraint
           (a fixed charter-clean catalog — supply-slow/fast, consent-slow/fast — never a
           free-form intervention; nil binding ⇒ no candidates, monitor-only beat)
REVIEW     a scenario may never REGRESS the pipeline (gain<0 filtered; structurally near-
           unreachable, defended rather than assumed)
RANK       kaizen-weighted efficiency (Δunblocked ÷ assumed rate), deterministic tie-break
EVOLVE     recombine the top-2 scenarios (both bottlenecks at once) when that beats the winner
ACT        the top scenario becomes a PRE-REGISTERED FORECAST (one more stock-flow step),
           persisted BEFORE the outcome is known — a PROPOSAL routed to sanae (supply) /
           musubi (consent), mirroring `ie_flow.cljc`'s downstream map. NEVER an experiment
           kafun itself carries out — G5 unchanged end-to-end.
OBSERVE    next beat: compare the prior forecast against the ledger's now-realized stock
LEARN      proper-score (normalized abs-error) → update the per-scenario kaizen weight
PERSIST    append one content-addressed tx to this loop's OWN ledger (kotoba.cljc) —
           idempotent-by-content, verify-chain tamper-evident, resume-safe, no-server-key
```

- **A SEPARATE ledger** (`data/persisted/kafun.react-loop.kotoba.edn`) from the remediation
  ledger autorun.cljc writes — the same separation ibuki keeps between its life-beat log and
  its coscientist log, so the two concerns (verdict history vs. bottleneck-forecast reasoning)
  don't collide on idempotency-by-content.
- **The realized readiness rate (`representative-progress`) is a function of the beat index
  ONLY — never of kafun's own chosen scenario.** This is a deliberate epistemic boundary: if the
  "realized" world moved faster whenever kafun proposed a fast scenario, kafun's PROPOSAL would
  be silently conflated with the outside world's ACTUAL pace — a subtle way G5 could be violated
  in spirit even while holding in letter. Mirrors ibuki's `representative-reading`, which is
  likewise a function of `(beatn, colony-size)` only, "never fabricates a windfall."
- **Datom vocabulary is fully namespaced under `:kafun.react/*` and `:react-beat/*`** — disjoint
  from `:kafun.rem/*` (the verdict ledger) and from any `:kafun/actuate`-shaped attribute (which
  remains unrepresentable repo-wide, G5). Test-enforced
  (`no-actuation-vocabulary-ever-appears-in-the-ledger-g5`).

## Consequences

- `run_tests.sh` grows to 9 suites (was 6): `test_bottleneck.cljc` (existing but not previously
  wired into the runner — a pre-existing gap closed opportunistically since this ADR's tests
  depend on the SAME `remediation-bottlenecks` lens) + `test_dynamics.cljc` + `test_react_loop.cljc`.
  63 tests / 164 assertions all green (was 38/111).
- `manifest.edn` `:actor/methods` and `:actor/tests` gain the two new files/suites.
- **Fleet registration is explicitly OUT OF SCOPE for this ADR** (no new Murakumo cell / cron /
  healthz port). The existing `KafunRemediationHeartbeatCell` continues to run only
  `autorun/beat`. Wiring `react-loop/beat` into the fleet — and deciding its own cron cadence
  and healthz port — is a follow-up, matching this actor's own established R0→R1 phased-rollout
  pattern (MATURITY.md).
- **No inochi-grounding, no real cadastral/telemetry feed** — `representative-progress` remains
  the R0 stand-in exactly like `remediate/blocker-relax`'s counterfactual and
  `autorun.cljc`'s synthetic seed; a live sapling-nursery/consent-registry feed is R1+, G7-gated,
  matching kafun's existing roadmap language verbatim.
- This ADR does NOT touch `etzhayyim.ie-flow.dynamics`, tsuchifumi's `sysdyn.cljc`, or the
  `etzhayyim/com-etzhayyim-yosoku` actor (ADR-2607072630) — all three remain independent; kafun's
  stock-flow model is self-contained within `20-actors/kafun/`.

## Alternatives Considered

- **Reuse `etzhayyim.ie-flow.dynamics/step-system` directly.** Rejected: its stock shape
  (customers/trust/data-asset/model-quality/reserves) and formulas (churn/spam/revenue/cost) are
  a SaaS negentropy-source domain with no meaningful mapping onto forest-stand readiness;
  forcing the reuse would require either a meaningless generic stock or smuggling kafun fields
  into a shared record other actors don't share.
- **Route the forecast through `etzhayyim/com-etzhayyim-yosoku`'s ScenarioGovernor (XMILE).**
  Rejected for this iteration: yosoku is a general-purpose, LLM-advisor-fronted governed
  simulation actor for POLICY/intervention scenarios across etzhayyim broadly — a much heavier
  dependency (separate repo, separate governor, mock-LLM advisor) than kafun's narrow need (a
  deterministic two-variable readiness forecast). Depending on yosoku here would also couple
  kafun's R0 tests to a second actor's release cadence. Not precluded as a LATER swap-in if
  yosoku's ScenarioGovernor proves a better fit once it matures past v1 — left as a documented
  option, not pursued now.
- **Give react_loop.cljc a real ACT (kafun enacts the top scenario as a dry-run, ibuki-style).**
  Rejected: ibuki's dry-run ACT is legitimate for ibuki because ibuki's own G8 boundary is
  "outward legs are member-principal," not "kafun never acts" — kafun's G5 is strictly stronger
  (assessment + R0 DESIGN ONLY, no actuation method of any kind, not even a self-directed
  dry-run). ACT here is therefore scoped to "forecast + propose a route," never an experiment
  kafun carries out on its own initiative.

## References

- ADR-2606211712 (kafun 花粉撲滅 remediation gate, R0)
- ADR-2606201200 (ibuki-coscientist entropy react-loop)
- ADR-2606212030 (kafun ie-flow + energy-flow SoS embedding)
- ADR-2607072630 (etzhayyim/com-etzhayyim-yosoku — System Dynamics XMILE governed actor)
- `20-actors/kafun/methods/remediate.cljc`, `methods/dynamics.cljc`, `methods/react_loop.cljc`
- `20-actors/ibuki/methods/react_loop.cljc` (the ReAct beat shape this ADR follows)
- `70-tools/src/etzhayyim/ie_flow/dynamics.cljc` (a DIFFERENT, SaaS-shaped stock — not reused)
