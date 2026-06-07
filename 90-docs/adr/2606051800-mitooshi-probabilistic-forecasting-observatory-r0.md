---
id: adr-2606051800-mitooshi-probabilistic-forecasting-observatory-r0
title: "mitooshi 見通し — probabilistic forecasting observatory (Tier-B actor R0; the charter-clean inverse of a quant trading bot + the leak-free fact→error→weight→learn architecture)"
status: proposed-pending-council-ratification
doc_type: adr
topic: mitooshi-probabilistic-forecasting-observatory
authoritative: true
last_verified: 2026-06-05
priority: 6.2
axis: actor
weight: 0.62
priority_note: "Answers 「kotoba で quant market や Google-Trends の model での未来予測 actor は設計しているか? 実際の予測と、事実からモデル誤差・weight を修正・学習する architecture は?」 (was: no forecasting actor; only scattered fragments — kakaku price-history, kotodama opportunity.forecast, ameno predict-next; kanjo/yobel explicitly PROHIBIT forecasting/speculation). A naive quant predictor is a trading bot = profit speculation (Charter §1.3 + yobel prohibition), so mitooshi is its INVERSE: a probabilistic OBSERVATORY (watari/kanjo-style non-adjudicating mirror) that forecasts distributions over public series routed to resilience and NEVER trades. The fact→error→weight→learn loop is made structural on the append-only Datom log (leak-free proper-scoring). Charter-clean by construction (nusa/tazuna pattern): distribution-only (G1) + non-speculative (G2) + primary-public-source (G4) + leak-free-skill-honest scoring (G5). ZERO invariant amendments."
authoritative_for:
  - "mitooshi actor scope (probabilistic forecasting over public time-series + leak-free proper-scoring backtest + residual-driven recalibration; design-only)"
  - "the distribution-only / no-point-assertion invariant (:forecast/point-asserted false — 非終末論 made structural)"
  - "the non-speculative / no-trading invariant (:forecast/use enum excludes trade/wager/position)"
  - "the leak-free proper-scoring rule (info-as-of boundary; CRPS/pinball/Brier/log-score; skill vs documented baseline)"
  - "the baien-edge residual→weight online-update boundary (G8) + no-server-key model promotion (G9)"
depends_on:
  - adr-2606041827-watari-live-ship-aircraft-position-kg-r0
  - adr-2606012600-watatsuna-submarine-cable-resilience
  - adr-2605242600-baien-federated-r0
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2606032000-kanjo-corporate-financial-disclosure-kg-r0
  - adr-2605302300-kanae-government-fiscal-flow-visualization-r0
  - adr-2605301600-danjo-public-accountability-oversight-r0
supersedes: []
superseded_by: []
---

# ADR-2606051800: mitooshi 見通し — probabilistic forecasting observatory (R0)

**Status**: proposed-pending-council-ratification
**Date**: 2026-06-05
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council ratification

# Context

The question: *「いまの kotoba で quant market や Google Trends の model での未来予測 actor
は設計しているか? また実際の予測と、事実からモデル誤差・weight を修正・学習する
architecture は?」*

**The honest pre-state (verified by full-roster search):** there is **no forecasting
actor**. Across 146 actor directories the only prediction-adjacent fragments are
`kakaku` (price *history* storage, no model), `kotodama` (`opportunity.forecast` CRM
heuristic), `recruit` (`DemandForecast` cohort), `maps` (`forecast_get` sensor sim), and
`ameno` (active-inference `predict-next` for chat UX, ADR-2605191113). There is **no**
quant-market actor, **no** prediction-market actor, **no** time-series model, **no**
backtesting framework, **no** online-learning / model-error-correction loop, and **no**
Google-Trends ingestion. Two actors explicitly *prohibit* the naive shape: `kanjo` ("No
forecasting — reported actuals only … not 投資助言業") and `yobel` (bars "predictive
market / derivative speculation").

That prohibition is the key. A naive *"quant-market prediction"* actor is a **trading
bot**, and a trading bot is profit speculation — which collides head-on with the Charter:
non-profit-only (§1.3), the yobel speculation bar, and the kanjo no-advice boundary.
**The reason it was never built is that the素直 form is unconstitutional, not that it was
overlooked.**

So the design problem is not "build a predictor" but "build the *charter-clean* shape of
one" — the same inversion by which okaimono inverts Amazon, yadori inverts GoDaddy, and
kamado makes a fossil-feedstock refinery unrepresentable. The forecasting analogue of
watari/kanjo/kabuto: a **non-adjudicating observatory** that emits **probability
distributions** routed to **resilience/planning**, and never trades.

The second half of the question — *"事実からモデル誤差・weight を修正・学習する
architecture"* — turns out to already have all its load-bearing parts in the substrate:
the kotoba append-only Datom log (`as-of` = leak-free ground truth), baien federated edge
(weight updates, ADR-2605242600/2630), and the watari/watatsuna public series. What was
missing was the **wiring**: a forecast lexicon, a proper-scoring residual engine, a
residual→weight online-update step, and a calibration-gated promotion. mitooshi is that
wiring.

# Decision

Introduce **mitooshi 見通し**, a Tier-B probabilistic forecasting observatory.
`did:web:etzhayyim.com:actor:mitooshi`. 見通し = *visibility into a distribution of
possible futures*, never a prophecy of one (deliberately non-occult per G12, deliberately
probabilistic per 非終末論).

## What it does

Emits **probability distributions** (`:forecast/dist-kind` ∈ gaussian / quantile /
categorical / ensemble) over **public time-series** (chokepoint transit-load, congestion,
availability, flow-rate, price-index, search-interest) into the kotoba Datom log, routed
to **resilience / planning / nowcast / early-warning / research**, and scores them
leak-free against the facts that later realize them. It **never** places a trade, holds a
position, settles money, advises, rates, or values.

## The four structural invariants (enforced in schema `:db/allowed`/enum + lexicon
`const`/`enum` + Python `ValueError`/refusal — the nusa/tazuna/kamado pattern)

1. **G1 distribution-only / no-point-assertion** — `:forecast/point-asserted` is
   `:db/allowed [false]`. A deterministic single-future is **unrepresentable**. This is
   非終末論 made structural: there is no final-state datom; a forecast is always a
   distribution carrying its own uncertainty.
2. **G2 non-speculative / no-trading** — `:forecast/use` enum is `{resilience planning
   nowcast early-warning research}`; `trade`/`speculation`/`wager`/`position` are not enum
   members. A forecast made to place a bet cannot be expressed.
3. **G4 primary-public-source-only** — `:series/source-class` enum excludes proprietary
   terminals (Bloomberg/CapIQ/Refinitiv/四季報) and scraped Google-Trends (the kanjo
   §2(c)/(e) anti-gatekeeping precedent). Trends, if ever, only via the karakuri
   member-principal ToS-honest path, recorded `:member-principal` and G10-gated.
4. **G5 leak-free / skill-honest scoring** — every forecast carries `:info-as-of` (the
   latest observation the forecaster could see); `score_pair` **raises** unless the
   scored observation's `:observed-at` is strictly after it. On an append-only Datom log
   a backtest physically cannot see the future — this asserts it. Scoring uses proper
   scoring rules only; skill is measured against a documented baseline.

## The architecture you asked about (事実 → 誤差 → weight 修正 → 学習)

```
   kotoba Datom log (as-of = ground truth, append-only)
   (1) forecast_issue → distribution datom, stamped :info-as-of   [G1, G2]
   (2) series_ingest  → realizing observation, append-only :observed-at   [G4]
   (3) backtest_score → join forecast×obs across as-of → CRPS/pinball/Brier/log-score
                        + PIT + skill-vs-baseline   [G5: leak-checked, G12: skill-honest]
   (4) online_update  → residuals drive EWMA bias-corr + variance-inflation
                        → proposed new model version   [G8: baien federated edge only]
   (5) calibration_gate → promote ONLY if skill>0 (G12) AND calibrated (G7)
                          AND member/operator-signed (G9 no-server-key)
```

The append-only log is what makes the loop honest: the forecast records *what was knowable*
(`:info-as-of`), the observation records *when the fact arrived* (`:observed-at`), so
look-ahead leakage — the failure that makes most backtests lie — is impossible by
construction. The residual `y − mean` is exactly the training signal; the EWMA
bias-correction and variance-inflation are the design-only reference recalibrator standing
in for the real baien federated backward pass (Murakumo-only, edge envelope).

## Artifacts (this ADR)

- Ontology `00-contracts/schemas/forecasting-ontology.kotoba.edn` (`:series :obs :forecast
  :fc.score :baseline :fc.model :fc.calib :fc.update`) with the four invariants encoded.
- `methods/score.py` — the empirical heart: CRPS (Gaussian closed form + degenerate-MAE
  limit), pinball/quantile loss, multi-class Brier, log-score, PIT, **ensemble energy-form
  CRPS + ensemble PIT**, climatology / persistence baselines, skill score, leak-checked
  `score_pair` (gaussian/quantile/categorical/ensemble), set-level scorecard + calibration.
  **26 tests** (closed-form CRPS value, ensemble energy-form value, leak/point/speculation
  refusals, calibration deviation, set-level skill).
- `methods/analyze.py` — leak-free metric-aware backtest over the seed (all 4 distribution
  kinds, each with a metric-appropriate baseline) → scorecard + derived score datoms.
  **7 tests.** Seed: gaussian **CRPS 0.089 / skill +0.81 (clim) +0.31 (persist)** · quantile
  **pinball 0.024 / skill +0.71** · categorical **Brier 0.338 / skill +0.44** · ensemble
  **CRPS 0.027 / skill +0.78** — all skilled.
- `methods/ingest.py` — offline public-series normalizer; the file-ingest mirror of the
  series_ingest cell's G4 source membrane (refuses Bloomberg/CapIQ/scraped-Trends), G10
  `--live` gated. **7 tests.**
- `methods/bridge.py` — **cross-actor composition**: maps watari (`:movement/chokepoint`,
  vessel-transit) + watatsuna (`:resilience/chokepoint`, cable-load Tbps) derived chokepoint
  aggregates into mitooshi `:series`/`:obs` over the SHARED chokepoint keyword space, so
  mitooshi forecasts the very chokepoints they observe. **Verified on the real watari +
  watatsuna analyzer outputs** (9 chokepoint series; `:malacca` → both a 3-vessel transit
  series and a 940 Tbps cable series; 54 non-chokepoint records ignored). The `:derived`
  sibling outputs are ingested as `:representative` public observations tagged
  `:obs/source-actor`, never as authoritative fact (G11). **6 tests.**
- 5 cells — ALL coded state machines (`series_ingest` G4 source membrane, `forecast_issue`
  G1/G2 gate, `backtest_score` `score_batch` leak-checked scoring, `online_update` residual→
  weight, `calibration_gate` G7/G9/G12 promotion gate); `.solve()` `RuntimeError` at R0.
  **24 tests.**
- `methods/analyze.py` also emits a **PIT reliability diagram** (`out/reliability.md`) + the
  `:fc.calib/*` datoms (`out/reliability.kotoba.edn`, kami-engine-viz-ready) — the G7
  calibration-honesty artifact, with an explicit small-sample caveat.
- `test_learning_loop.py` — **end-to-end learning-loop integration test**: a biased +
  mis-dispersed model corrected by its own residuals (`score_pair` → `online_update` →
  `apply_correction` → re-score → `calibration_gate`) drives **CRPS 1.503 → 0.403 (−73%),
  PIT mean 0.95 → 0.50, learned bias +2.02**, promotion CLEARED (member-signed) / REFUSED
  (unsigned, no-server-key). **6 tests** — the proof the loop closes and improves.
- `test_continual_learning.py` — **multi-round continual-learning / drift test**: the EWMA
  correction converges to the true systematic bias over many rounds, rejects per-round noise,
  and **re-converges on a regime drift** (true bias `2.0 → 4.0` tracked: `c → 1.996` then
  `c → 3.996`) — the model keeps following reality, doesn't get stuck. **5 tests.**
- `methods/horizon.py` — **multi-horizon skill-decay analysis**: on a mean-reverting AR(1)
  process (φ=0.9), a leak-free h-step forecaster scored against climatology shows skill
  **+0.30 @h=1 → +0.006 @h=3 → ≈0 @h=6** while CRPS rises — the honest useful-foresight range
  (a long-range forecast eventually does no better than the climatological mean; never a
  flat-skill crystal ball, 非終末論). **6 tests.** Plus `run_tests.sh` (one-command suite).
- 6 lexicons `com.etzhayyim.mitooshi.*`; manifest (edn + jsonld); README; CLAUDE.md;
  `:representative` seed; registered in `INFRA_ACTORS` (`did:web:etzhayyim.com:actor:mitooshi`).
- **89 tests green** total (one-command `run_tests.sh`).

# Gates (12) and Non-goals (7)

G1 distribution-only · G2 non-speculative · G3 non-adjudicating · G4
primary-public-source-only · G5 leak-free proper-scoring · G6 Murakumo-only · G7
calibration-honest · G8 baien-edge online-update · G9 no-server-key · G10 outward-gated ·
G11 sourcing-honesty · G12 anti-pseudoscience. (Full text: `manifest.edn`.)

N1 not a trading/quant bot · N2 no investment advice/rating/valuation/業績予想 · N3 no
proprietary-terminal or scraped-Trends ingest · N4 no person-level prediction /
pattern-of-life · N5 no point-prophecy / deterministic final-state · N6 no commercial-GPU
training · N7 no server-signed promotion.

# Consequences

**Positive.** The substrate gains its missing forecasting limb in a form that cannot drift
into speculation. The "correct the model from fact" architecture the question asks for
exists and is *tested*, with leak-freeness guaranteed by the storage model rather than by
discipline. It composes immediately with watari/watatsuna (which supply the series) and
danjo/kanae (which consume the forecasts). Zero invariant amendments.

**Negative / honest R0.** Design + datafication + **offline** scoring/recalibration only.
No live ingest, publish, model promotion, or federated backward pass (all G10 — Council
Lv6+ + operator). Seed is `:representative` (illustrative values, not live capture).
All four distribution kinds (gaussian/quantile/categorical/ensemble) are wired end-to-end in
`analyze.py`. The recalibrator is the reference EWMA design — the closed loop is proven on
synthetic data in `test_learning_loop.py` (CRPS −73%) and shown stable + drift-tracking over
many rounds in `test_continual_learning.py`, but it is not yet the live baien federated
trainer. `ingest.py` is offline-only (no network code; `--live` is gate-refused). Calibration
deviation on a small per-series seed is necessarily lumpy (small-sample) — reported honestly.

# Alternatives considered

- **A quant trading actor.** Rejected — profit speculation, Charter §1.3 + yobel.
- **Point forecasts.** Rejected — a deterministic asserted future violates 非終末論 and
  hides uncertainty; made structurally unrepresentable (G1).
- **A separate projection DB / vector store for backtests.** Rejected — the append-only
  Datom log already gives leak-free `as-of` joins (ADR-2605312345); a side store would
  reintroduce the look-ahead-leak risk the log eliminates.
- **Ingest Google Trends / Bloomberg directly.** Rejected — proprietary-terminal
  gatekeeping (kanjo §2(c)/(e)); only primary-public or karakuri member-principal paths.

# Roadmap

R0 (this ADR) → R1 live-but-gated primary-public ingest + quantile/categorical forecasters
+ baien-edge recalibration wired to the federated PoC → R2 standing forecasting service for
danjo/kanae/watari resilience views + member-principal Trends via karakuri + continual
recalibration with drift monitoring. No phase ever trades.
