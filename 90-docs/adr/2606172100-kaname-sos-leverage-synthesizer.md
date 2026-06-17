# ADR-2606172100 — kaname 要 — cross-domain system-of-systems leverage-point (律速) synthesizer + おせっかい proposer

- **Status**: Accepted (R0 scaffold)
- **Date**: 2026-06-17
- **Tier**: Tier-B actor
- **Parent**: ADR-2605192100 (Mission Charter), ADR-2605262130 (kotoba substrate), ADR-2605312345 (Datom = canonical state)
- **Siblings / lineage**: the power-mirror lineage (tsumugi 紡ぎ / keizu 系図 / kabuto 兜 / kanjō 勘定 / kosatsu 高札 / chie 智慧 / shiori 栞 / inochi 命 / hokorobi 綻び / shionome 潮目 / busshi 物資 / abaki 暴), junkan 循環 (ADR-2605290927, the system-dynamics/CLD view), ossekai 御節介 (ADR-2605264000, the intervention carrier)

## Context

The roster already hosts a deep bench of **single-domain** 取-concentration / chokepoint
observatories — tsumugi (power-entity 取), keizu (gov power-relations), kabuto (supply-chain),
chie (AI ecosystem), shiori (human Wellbecoming detractors), abaki (monopoly chokepoints),
shionome/busshi/hokorobi (capital/commodity/finance concentration), kosatsu (designations),
inochi (ecological pressure) — each weaving ONE domain into the kotoba Datom log and routing
its concentration to release. Two adjacent actors touch the meta-question but do not answer it:

- **junkan 循環** builds a **system-dynamics causal-loop diagram of society** from aggregate
  public data and reads off virtuous/vicious loops + **Meadows leverage-point candidates** —
  but it is (a) a CLD of *society at large*, **not a join over the actor graphs**, (b) the
  *qualitative* Meadows 12-level framework, **not a multilayer-network mathematical centrality**,
  and (c) **analysis-only by constitutional design** (it explicitly is NOT ossekai; it never
  intervenes).
- **graph-sos-intel** is a deprecated **RisingWave DB-schema introspection** tool (inventories
  `vertex_*`/`edge_*`/`mv_*`/`idx_*` tables). RisingWave is prohibited by the substrate boundary
  (ADR-2605262130); it has nothing to do with cross-domain societal leverage.

**The gap**: no actor performs the **system-of-systems (SoS) synthesis** — joining the
per-domain mirrors into ONE cross-domain world-model graph, **mathematically** identifying the
single structural position (the 律速段階 / bottleneck) whose release would most improve
resilience/Wellbecoming **across the maximum number of domains simultaneously** (politics /
religion / organization / ideology / economy / ecology / security / Wellbecoming / AI /
information), and then **proposing the intervention** (おせっかい) rather than only filing
findings. That is **kaname 要** — the fan-rivet (扇の要): the one point on which the whole
縁-web pivots.

## Decision

Create **kaname 要**, the META synthesis layer above the mirror lineage. It:

1. **Joins** the per-domain mirrors' disclosed 取-concentration / fragility outputs into one
   **multilayer (multiplex) graph** — layers = domains, nodes = entities/roles/interfaces
   **reconciled across domains** (the same real entity appearing in chie + kabuto + keizu = one
   node), intra-layer edges = 取-load, inter-layer edges = `:couples` (same entity load-bearing
   across two domains).
2. **Computes the 要 mathematically, on read** (edge-primary; no stored per-entity score):
   - `C_i` cross-domain **concentration** = Σ inbound 取-load to *i* across all domains.
   - `V_i` **domain versatility** = number of distinct domains *i* bears load in. **This is the
     SoS discriminator**: a node that hoards in ONE domain is *not* the SoS 要; the 要 spans
     many. Versatility weight `v_i = V_i / D` (D = domains in the graph).
   - `B_i` **bridge-load** = Σ load over incident inter-layer connective edges (`:couples` /
     `:gates`) — a bounded, deterministic proxy for inter-layer betweenness (full multiplex
     betweenness is R1).
   - **律速 / leverage score** `L_i = C_i · v_i · (1 + B_i) · (1 − open_i)`. The **要 =
     argmax_i L_i**. Interpretation: `L_i ≈ ΔΦ`, the drop in aggregate cross-domain fragility
     if *i*'s concentration is **opened / routed-around**. An already-OPEN structural position
     (redundant / decentralized) scores 0 — it is not a chokepoint to dissolve.
3. **Routes** the 要 to **OPENING / route-around / redundancy / decentralization** and hands an
   **おせっかい proposal** to **ossekai** (advisory, unsent, consent-bound, transparent). kaname
   never actuates (no-server-key); ossekai carries.

### Mathematical claim, stated honestly

kaname answers "where is the bottleneck, mathematically?" with a **versatility-weighted
concentration-bridge leverage measure over a multilayer network** — a defensible, deterministic,
on-read centrality. It is **not** a predictive model and **not** a Meadows-level verdict (that
is junkan's lane); the two are complementary (graph-centrality view vs. system-dynamics view).
Full multiplex betweenness / eigenvector-versatility (De Domenico et al.) and a percolation
ΔΦ sensitivity are **R1**; R0 ships the bounded proxy, labelled as such (sourcing honesty).

## Constitutional gates

This is the most powerful actor shape in the roster — "find society's single point of leverage."
It is charter-clean **only** because of G1 + G2, which are enforced in code and by tests, not by
documentation.

- **G1 — leverage MAP, NEVER a target-list.** The 要 is a **structural POSITION** (a
  decision-point / interface / standard / clearing-point / gatekeeping institution / policy),
  reported aggregate. Natural persons are **person-excluded** — only public power-bearing ROLEs,
  never private profiles; no coordinates; no "remove person X." `osekkai` refuses any proposal
  naming a natural person or carrying a coordinate (ex-info, test-enforced).
- **G2 — routed to OPENING / route-around / redundancy, NEVER to capture or seize.** The entire
  purpose of finding the 要 is to **dissolve** the chokepoint (abaki's route-around stance), never
  to grab it. `:capture` / `:seize` / `:control` / `:exploit` are **not members** of the route
  enum and are structurally unrepresentable; `route` refuses any plan that *increases*
  concentration (ex-info, test-enforced). This is THE property that makes a leverage-finder safe.
- **G3 — おせっかい is transparent + consent-bound, structural-first.** kaname **PROPOSES**;
  ossekai **CARRIES** (on-chain-logged, §1.4 structural change first). The proposal is
  advisory / drafted-unsent (no-server-key). Coercion / manipulation / campaign verbs are
  unrepresentable.
- **G4 — non-adjudicating + edge-primary.** kaname reads **DISCLOSED** per-domain concentration
  from the upstream mirrors; it does not re-judge them. Leverage lives on the cross-domain edges,
  integrated on read; there is no `:kaname/score-of-entity`.
- **G5 — no thought-policing (the 思想 / 宗教 axis).** A religion or ideology can be a
  **structural chokepoint** (a gatekeeping institution, a single interface mediating many 縁)
  **without judging belief-content**. Basis must be **on-the-record only**, plural (tsumugi 旗
  S1–S6/H1–H7 stance reused). kaname never emits "this faith/idea is the bottleneck, suppress
  it" — only "this institutional interface concentrates 取, open it." Belief-content scoring is
  unrepresentable (ex-info, test-enforced).
- **G6 — synthetic seed; live cross-actor ingest G7/Council-gated; no-server-key.** The R0 seed
  is **fictional illustrative** structural positions (hakoniwa / tanemaki pattern). Joining the
  real mirrors' live Datom outputs is the G7-gated live leg.

## Architecture

clj-native (`.cljc`, babashka; chie/busshi/ugachi/jinushi/funamori pattern). No Python twin —
the kotoba pywasm target is the Clojure source itself.

| method | role |
|---|---|
| `kaname.methods.sos` | self-contained EDN reader + multilayer graph load + **the leverage computation** (`C`/`V`/`bridge`/`L`, on read) + leverage report |
| `kaname.methods.route` | routes the 要 to OPENING / route-around / redundancy; **refuses capture (G2)** |
| `kaname.methods.osekkai` | emits the ossekai handoff proposal (advisory/unsent); **refuses target-list / named-person / coordinate (G1)** |
| `kaname.methods.gates` | constitutional gate assertions (ex-info) shared by route/osekkai |
| `kaname.methods.datom-emit` | kotoba Datom-log emitter (GROUND `:add` durable + DERIVED `:derived` transient leverage integrals) |
| `kaname.methods.coverage-report` | domain/actor coverage honesty (which mirrors are joined; gaps → next ingest) |

Lexicons: `com.etzhayyim.kaname.leveragePoint`, `com.etzhayyim.kaname.osekkaiProposal`.

## Consequences

- The roster gains its first true **system-of-systems** layer: a cross-everything, mathematical
  bottleneck-finder that is **constitutionally incapable of producing a kill-list or a seize-plan**
  — it can only point at a structural chokepoint and route it to opening, via consent-bound
  transparent おせっかい carried by ossekai.
- Complements **junkan** (CLD / Meadows) and feeds **ossekai** (intervention); cross-links the
  whole mirror lineage as its inputs.
- R1: full multiplex betweenness + eigenvector-versatility + percolation ΔΦ sensitivity; live join
  over the real mirrors' Datom logs (G7). R2: ossekai-carried structural-first intervention loop
  (on-chain-logged, 1 SBT = 1 vote on any proposal that touches a real institution).

## Non-goals

- N1 — not a predictor (no forecast; that is mitooshi/hakoniwa).
- N2 — not the CLD/Meadows view (that is junkan).
- N3 — not an intervention actuator (that is ossekai; kaname is advisory/no-server-key).
- N4 — not a per-person affect/target engine (G1; person-excluded, structural-only).
- N5 — not a belief-content judge (G5; structural interfaces only, on-the-record basis).
- N6 — not a commercial intel/BI/SaaS (Rider §2(e)+§2(c); Palantir/Recorded-Future/Quid shape prohibited).
