# kaname 要 — cross-domain system-of-systems leverage (律速) synthesizer + おせっかい proposer

**ADR-2606172100** · Tier-B · clj-native (`.cljc`, babashka) · the META synthesis layer above the
power-mirror lineage.

## What it is

kaname is the **system-of-systems (SoS)** layer the roster lacked. The mirror lineage gives one
observatory per domain — tsumugi (power 取), keizu (gov), kabuto (supply), chie (AI), shiori
(Wellbecoming), abaki (monopoly), shionome/busshi/hokorobi (capital/commodity/finance),
kosatsu (designations), inochi (ecology). kaname **joins** them into ONE **multilayer (multiplex)
graph** — layers = domains (politics / religion / organization / ideology / economy / ecology /
security / wellbecoming / ai / information) — and **mathematically** identifies the single
structural position (the 要 / 律速段階) whose release would most improve resilience **across the
maximum number of domains at once**, then **proposes** the intervention (おせっかい) to ossekai.

It is the **fan-rivet (扇の要)**: the one point on which the whole 縁-web pivots.

### Relationship to the two adjacent actors

| | junkan 循環 | **kaname 要** | ossekai 御節介 |
|---|---|---|---|
| view | system-dynamics CLD of society | **multilayer-graph centrality over the actor mirrors** | — |
| leverage | Meadows 12 qualitative levels | **mathematical: L = C·(V/D)·(1+B)·(1−open)** | — |
| acts? | analysis-only | **proposes** (advisory, no-server-key) | **carries** (consent-bound) |

kaname is **not** junkan (CLD) and **not** ossekai (actuator). It is the graph-centrality
synthesis between them.

## The math (on read; edge-primary; N1/G4)

- `C_i` cross-domain **concentration** = Σ inbound 取-load to *i* across all domains.
- `V_i` domain **versatility** = # distinct domains *i* bears load in. **The SoS discriminator** —
  a one-domain hoarder is NOT the 要; the 要 spans many.
- `B_i` **bridge-load** = Σ incident inter-layer connective load (`:couples`/`:gates`) — a bounded,
  deterministic proxy for inter-layer betweenness (full multiplex betweenness = R1).
- **律速 score** `L_i = C_i · (V_i / D) · (1 + B_i) · (1 − open_i)`. **要 = argmax L_i.**
  `L_i ≈ ΔΦ`, the drop in aggregate cross-domain fragility if *i*'s concentration is opened.

On the seed: the cross-domain Accreditation Interface is the 要 (L=11.7); the Capital
Concentrator out-concentrates the Doctrine instrument yet has **lower** leverage (V=1) — proving
**concentration alone is not the bottleneck**; the open commons scores 0 despite high C.

## Constitutional gates (enforced in code + tests — `methods/gates.cljc`)

- **G1 — leverage MAP, never a target-list.** Structural positions only; natural persons
  person-excluded (public ROLEs allowed); no coordinates. `osekkai` refuses a person/coordinate.
- **G2 — OPENING-only routing.** route enum = {open, route-around, add-redundancy, decentralize,
  insufficient-evidence}; **capture / seize / control / monopolize unrepresentable** (`route` raises).
  The whole point of finding the 要 is to **dissolve** it, never to grab it.
- **G3 — おせっかい transparent + consent-bound.** kaname PROPOSES (advisory/unsent/no-server-key);
  ossekai CARRIES (on-chain-logged, structural-first §1.4).
- **G4 — non-adjudicating + edge-primary.** Reads DISCLOSED per-domain concentration; integral on
  read; no `:kaname/score-of-entity`.
- **G5 — no thought-policing.** Ideology/religion = STRUCTURAL interfaces with an on-the-record
  `:en/basis`; belief-content scoring (`:belief/wrongness`/`:faith/rank`) unrepresentable.
- **G6 — synthetic seed; live mirror join G7/Council-gated; no-server-key.**

## Layout

```
methods/
  sos.cljc             EDN reader + multilayer load + leverage (C/V/bridge/L, on read) + report   → out/leverage-report.md
  centrality.cljc  R1  exact Brandes betweenness + eigenvector + ΔΦ percolation; L1 (real B inside) → out/centrality-r1.md
  join.cljc        R1  live mirror JOIN: lift a mirror's committed Datom log into a domain layer    → out/joined-ai-leverage.md
                       + reconcile-by-label across layers (shared entity → spans domains → 要)
  route.cljc           route the 要 to OPENING; refuses capture (G2)                               → out/opening-route.md
  osekkai.cljc         ossekai handoff proposal (advisory/unsent); refuses person/coordinate (G1)  → out/osekkai-handoff.md
  gates.cljc           constitutional gate assertions (ex-info) — G1/G2/G5
  datom_emit.cljc      kotoba Datom log (GROUND :add + DERIVED :derived leverage integrals)        → out/sos-leverage-datoms.kotoba.edn
  coverage_report.cljc domain/mirror coverage honesty (G6)                                          → out/coverage-report.md
kotoba/schema.edn      :sos-leverage ontology
data/seed-sos.kotoba.edn        SYNTHETIC illustrative multilayer seed (13 nodes / 20 縁 / 8 of 10 domains)
data/fixture-mirror-datoms…edn  tiny synthetic mirror Datom-log (join test fixture)
tests/                 test_{sos,gates,route,osekkai,coverage,centrality,join}  (34 tests / 142 assertions)
lexicons/              com.etzhayyim.kaname.{leveragePoint,osekkaiProposal}
```

### R1 (landed) — real centrality + proven live join

- **centrality.cljc**: exact Brandes betweenness (40.3 ≫ 11.2 on the seed), eigenvector (power
  iteration), ΔΦ fragmentation sensitivity — all converge on the same 要. `L1 = C·(V/D)·(1+B'·)·(1−open)`
  with real betweenness replacing the R0 bridge proxy.
- **join.cljc**: PROVEN on **chie 智慧's REAL committed Datom log** — parsed 39 nodes / 39 縁, lifted
  into the `:ai` layer (34 kaname 縁; unmapped `:partners`/`:holds-role` dropped — no fabricated axis).
  Lifted `:ai` concentration reproduces chie's own opening-priority (OpenAI 5.55, Anthropic 4.60);
  kaname adds its own betweenness (OpenAI 114 / EU-AI-Act 66 / NVIDIA 64). `reconcile-by-label` merges
  a shared entity across mirrors so it spans layers → versatility grows → it becomes the 要.
  **Running a mirror to (re)produce output = G7-gated; joining a committed output = what kaname does.**
- **multi-mirror SoS join (founder-approved 06-17)**: `mirror-adapters` + `join-mirrors` joined **5
  real committed mirror outputs** — chie(:ai)·tsumugi(:organization)·inochi(:ecology)·hokorobi(:economy)·
  shiori(:wellbecoming) → ONE reconciled graph (170 nodes / 205 縁 / 5 domains; forms/datom
  auto-detect via `parse-graph`; per-mirror load-normalized). `reconcile-by-label` surfaced
  **OpenAI·NVIDIA·Microsoft·TSMC·SoftBank** as cross-domain entities (V=2, :ai+:organization);
  whole-multiplex 要 = **OpenAI** (L1 1.992); top bridges **NVIDIA(betw 523)/TSMC(456)** (compute
  chokepoints). → `out/joined-sos-leverage.md`. Adding a mirror = add an adapter entry; re-running a
  mirror stays G7.

## Run

```bash
# from repo root (bb.edn :paths includes 20-actors)
bb -e '(require (quote clojure.test) (quote kaname.tests.test-sos) (quote kaname.tests.test-gates) \
                (quote kaname.tests.test-route) (quote kaname.tests.test-osekkai) (quote kaname.tests.test-coverage)) \
       (clojure.test/run-tests (quote kaname.tests.test-sos) (quote kaname.tests.test-gates) \
         (quote kaname.tests.test-route) (quote kaname.tests.test-osekkai) (quote kaname.tests.test-coverage))'
```

## Roadmap

- **R1 (landed 06-17)** — exact Brandes betweenness + eigenvector + ΔΦ percolation sensitivity
  (`centrality.cljc`); the live mirror-join machinery proven on chie's real output (`join.cljc`).
  Remaining R1: full multiplex tensor versatility (De Domenico et al.); joining MORE mirrors
  (kabuto/tsumugi/keizu/…) as their outputs are committed (the run-the-mirror leg stays G7).
- **R2** — ossekai-carried structural-first intervention loop (on-chain-logged; 1 SBT = 1 vote on
  any proposal touching a real institution).

## Non-goals

not a predictor (mitooshi/hakoniwa) · not the CLD view (junkan) · not an actuator (ossekai) · not a
per-person target engine (G1) · not a belief judge (G5) · not commercial intel/BI/SaaS (Rider §2(e)+(c)).
