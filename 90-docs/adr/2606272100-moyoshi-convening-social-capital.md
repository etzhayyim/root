---
id: adr-2606272100-moyoshi-convening-social-capital
title: "ADR-2606272100: moyoshi 催し — event design / convening actor that MINTS validated social capital (not turnout)"
status: proposed
doc_type: adr
topic: moyoshi-actor-convening-social-capital
authoritative: true
last_verified: 2026-06-27
priority: 4.0
axis: architecture
weight: 0.50
priority_note: "Plan/design/host gatherings whose telos is validated tie-formation → mints the convening sub-ledger of social capital, never attendance/engagement"
authoritative_for:
  - 20-actors/moyoshi
depends_on:
  - adr-2606232200-kizuna-actor-social-self-evolution-sos
  - adr-2606073200-asobi-play-cultural-kg-mirror
  - adr-2605264000-ossekai-information-arbitrage-wellbecoming
related:
  - SOCIAL-CAPITAL-LEDGER (kotoba/docs)
  - adr-2606062100-moyai-credit
  - adr-2605263400-musubi-covenant-ceremony
supersedes: []
superseded_by: []
---

# ADR-2606272100: moyoshi 催し — convening actor that mints validated social capital

**Status**: proposed
**Date**: 2026-06-27
**Deciders**: Jun Kawasaki

## Context

The substrate already ships every *piece* of "raise social capital by holding
events" — but no actor whose **telos** is the act of convening itself:

- **social capital ledger** (`kotoba/docs/SOCIAL-CAPITAL-LEDGER.md`) — mints/decays
  a non-transferable, non-yield, decaying capital. But its only mint sources today
  are **情報開示 (disclosure)** and **wellbecoming 介入**. *Holding a gathering that
  forms human bonds is not a mint source.*
- **kizuna 絆** (ADR-2606232200) — reads the actor society's social graph and
  identifies fragility (isolated actors, the 律速 bridge, low-reciprocity pairs),
  but is `PROPOSE-not-act` and only proposes *ties*. It cannot convene the gathering
  that would actually heal the fragility it finds.
- **asobi 遊び** (ADR-2606073200) — maps cultural works / **events** / venues as a
  participation-*access* surface (OPENING vs enclosure), but is explicitly a *map*,
  non-adjudicating, with **no event-hosting side**.
- **musubi 結** — performs *ceremonies* (婚礼/命名/葬送), a narrow ritual subset.
- **bizzabo-compat** — a clean-room of an event-SaaS API; an integration shim, not a
  governed actor.

What is missing is the **convening loop**: take kizuna's fragility signal, *design*
a gathering that would repair it, run it past an independent governor, hand it to a
human to actually host (consent-bound), then **mint social capital only from the ties
that actually formed and survived** — never from headcount.

Doing this naïvely is dangerous, which is why it needs an actor layer (the same
argument as robotaxi/kenchi/talent): an event-designer LLM has **no notion of
turnout-vs-bond, openness, consent, accessibility, or sybil-resistance**. Left
unsealed it optimizes attendance and reach — i.e. it rebuilds the
engagement-industrial complex the Charter forbids (§1.13 / Rider §2(h)).

## Decision

Add **`moyoshi 催し`** (`20-actors/moyoshi/`, clj/bb over the kotoba Datom log) — an
event **design / convening** actor on the langgraph-clj supervised-superstep pattern,
sealing an **EventDesigner-LLM** behind an independent **ConveningGovernor**, with a
human host in the actuation loop (ossekai + member CACAO, no-server-key).

> **催し (moyoshi)** — a thing one *holds*; 催す = to host/convene. The name is the
> means; the telos is **絆 (validated ties)**, denominated in social capital.

### The core contract (sealed advisor + independent governor)

```
kizuna fragility signal  +  injected openness/consent/accessibility context
        │   (isolated actor · 律速 bridge · low-reciprocity pair)
        ▼
  ┌──────────────────┐  event design   ┌────────────────────┐
  │ EventDesigner-LLM │ ──────────────▶ │ ConveningGovernor  │  (independent)
  │ (sealed node)     │  who/what/where │ openness · consent │
  │                   │  /openness/coc  │ a11y · anti-engmt  │
  └──────────────────┘                 └─────────┬──────────┘
                                   propose ◀──────┴──────▶ refuse
                                      │                      │
                            :event/proposed (:dry-run)    widen/return
                            → ossekai + member CACAO       ("not an opening")
                                      │
                              human hosts (member-signed go)
                                      ▼
                        settle: observe ties that FORMED and SURVIVED
                        a decay window → mint social/mint/convening/<epoch>
```

**moyoshi never books, charges, invites, or posts on its own, and never mints from
attendance.** It mints only from *ties that formed because of the gathering and
survived* — attributed to the convener DID, anti-sybil via moyai's
proof-of-contribution.

### The loop (one beat — `moyoshi.methods.moyoshi/beat`)

```
perceive  kizuna fragility (isolated/律速/low-reciprocity) + asobi openness gaps
  → design   EventDesigner-LLM proposes a gathering concept (purpose, audience set
             as DIDs, format, venue-openness, Code-of-Conduct, accessibility plan)
  → govern   ConveningGovernor checks G2..G6; refuses or returns-to-widen
  → propose  :event/proposed (:status :dry-run, :route :ossekai); member CACAO leash
  → settle   after the event + a decay window: count reciprocal ties that FORMED and
             SURVIVED (Δ vs pre-event baseline from kizuna) → emit the mint signal
  → persist  content-addressed append-only kotoba commit-DAG; idempotent heartbeat
```

Pure + deterministic where it can be (sorted DID order, ties broken by id; no wall
clock / randomness in the graph + settlement math — the LLM design step is the only
non-deterministic node and it is sealed + advisory).

### New mint source — the convening sub-ledger

Extend the social capital ledger (reusing moyai verbatim, per its §"do not fork")
with **one** new mint predicate. It changes *only the mint source*; decay /
conservation / non-transfer / earn-rate-cap / burn machinery is inherited unchanged.

| predicate (`A`) | `V` | written by | meaning |
|---|---|---|---|
| `social/mint/convening/<epoch>` | smic | settle job | convening points minted to the **convener** DID this epoch |
| `social/burn/<epoch>` | smic | burn job | (existing) extractive/coerced convening burns here |

```
mint_convening_smic(convener, e)
  = SCALE · w_convening · n_validated_ties(convener, e)
```

where `n_validated_ties` counts ties (reciprocal follow / sustained reciprocal
interaction, observed via kizuna) that (a) did **not** exist in the pre-event
baseline, (b) **survived ≥ S epochs** after the gathering, and (c) **passed the
anti-sybil membrane** (moyai proof-of-contribution — distinct, non-colluding DIDs).
RSVPs, headcount, reach, and same-epoch likes mint **nothing**.

```
burn_convening_smic(convener, e)
  = SCALE · burn_extractive_mult · w_convening · n_manipulative(convener, e)
```

`n_manipulative` = gatherings found (Council-attested) to be engagement-farming,
coerced, pay-to-enter, or exclusionary. `burn_extractive_mult > 1` keeps the
"嘘で損 / 囲い込みで損" asymmetry: faking community costs more than it earns. Params
(`w_convening`, survival window `S`, `burn_extractive_mult`) live in the existing
`social/capital/params/active` Council-attested blob — no new param surface.

### Constitutional gates (in code + tests)

- **G1 PROPOSE-not-act.** moyoshi emits `:event/proposed` (`:status :dry-run`,
  `:route :ossekai`). No book/charge/invite/post path. Actuation is a human host
  via ossekai + member CACAO (no-server-key, ADR-2606072802). moyoshi never hosts,
  pays, or messages on its own.
- **G2 BONDS-not-turnout (anti-engagement).** The objective is reciprocal
  tie-formation + connectivity repair + wellbecoming-Δ — **never** attendance /
  reach / RSVP / virality / retention. No turnout-maximization field is
  representable (mirrors kizuna G2 / asobi G1; Charter §1.13 / Rider §2(h)).
- **G3 OPENING-not-enclosure.** Every proposed gathering must *increase*
  participation-openness (asobi's OPENING route). Pay-to-enter, exclusionary, or
  attention-platform-locked convening is refused at the governor.
- **G4 MINT-on-validated-ties-only.** Convening capital mints ONLY from ties
  that formed AND survived ≥ S epochs AND passed the anti-sybil membrane. Headcount /
  RSVP / same-epoch engagement mint nothing. Coerced/faked ties burn asymmetrically.
- **G5 CONSENT-bound, person-protective.** No person is invited, profiled, or matched
  without consent; person-level data is purpose-limited (talent-actor PolicyGovernor
  pattern). **No per-person engagement score is representable** — the audience is a
  set of DIDs to *open access to*, never individuals to *rank* (person-excluded
  scoring, cf. kizuna G3, but participation is allowed).
- **G6 no-server-key.** moyoshi READS kizuna/asobi public signals + PROPOSES; it
  holds no key.

### Tight pairs

- **kizuna 絆** — supplies the fragility signal in (the design target) and the
  baseline graph for settlement (the mint signal out). moyoshi is the *act* that
  realizes kizuna's *proposals*.
- **social capital ledger / moyai 舫い** — the denomination; moyoshi adds exactly one
  mint predicate and reuses everything else.
- **ossekai 御節介** — the consent-bound actuator + wellbecoming-Δ source.
- **asobi 遊び** — the openness/enclosure map G3 checks against; a held gathering is
  an asobi *event* node, surfaced on the OPENING route.
- **musubi 結** — covenant ceremonies are a *special, ritual category* of moyoshi
  (explicit cross-actor hand-off at R2).

## Status / scope

**R3 — code-complete on a verified commit-DAG + LIVE-engine bridge + fleet residence** (this
ADR + `manifest.edn` + `README.md` + `methods/moyoshi.cljc` core + `kotoba.app.edn` + tests, R1;
plus the R2 + R3 legs below). 23 tests / 58→76 assertions green (`bb run_tests.clj`).

- **R1** — the pure convening core: `design-gathering` / `govern` (ConveningGovernor,
  G1..G6) / `validated-ties` + `settle` (G4 mint) / `beat`.
- **R2** — the three named legs, the kaname/ibuki pattern:
  - *live kizuna ingest* (`methods/ingest`) — lifts a COMMITTED kizuna 絆 readout into
    moyoshi's fragility input (running kizuna = G7; joining its committed output = the
    actor's job, the kaname join pattern). no-server-key.
  - *settlement decay-window job* (`methods/settle`) — a pending-gathering ledger +
    `settle-at = epoch + S` scheduler around the pure mint core; mints only at the
    window's end, only from survived + new + anti-sybil ties (G4).
  - *commit-DAG persistence* (`methods/kotoba`) — each beat is one content-addressed,
    idempotent-by-content tx of EAVT datoms (verify-chain tamper-evident, resume-safe),
    via the shared `kotoba.datom` binding. no-server-key (local append).
  - *on-kse mesh wrapper* (`methods/mesh.clj`) — the KOTOBA Mesh entry the
    `kotoba.app.edn` component points at; *autonomous heartbeat* (`autorun`) wires
    ingest → design → govern → record → settle → persist. **Verified live**: beat #0
    proposes (host=kaname) + records the pending gathering + persists (verify-chain :ok);
    beat #1 at the same epoch is idempotent (`:no-change`).
- **R3** — code-complete, the kaname/ibuki residence pattern:
  - *kotoba live-engine bridge* (`methods/kotoba_bridge`) — each local tx becomes one
    `com.etzhayyim.apps.kotoba.datomic.transact` against a running node (host allowlist
    refuses off-fleet endpoints BEFORE any I/O; exactly-once `:bridge/*` cursor keyed by
    local CID; `:moyoshi.tx/*` provenance; `expected_parent` chaining; DRY-RUN by default,
    live = `MOYOSHI_KOTOBA_LIVE=1`; unsigned public-DID operator bearer on the loopback
    trust boundary — no-server-key).
  - *autorun `--bridge`* — pushes the commit-DAG after persist, **FAIL-OPEN** (engine down /
    operator DID absent → the beat still completes locally). *epoch-from-clock* (the 1-day
    ledger clock, isolated in the clj `-main` so `beat` stays deterministic). *settlement
    now-graph* `ingest/observe-from-kizuna` (settle due gatherings against kizuna's CURRENT
    reciprocal ties). **Verified**: a `--bridge` beat with no live engine fail-opens
    (`bridge: fail-open (ConnectException)`) and still persists + verify-chain :ok.
  - *fleet cell* (`cell.cljc` → `MoyoshiHeartbeatCell`, registered in cell-runner
    `cells.edn`: node reuben, cron `39 * * * *`, healthz 13092 — LOCAL-only, no bridge).
  - *LaunchAgent* (`deploy/`, bb-native per ADR-2606072802: `install.clj` + plist template +
    `run-heartbeat.clj`) — hourly `--bridge` residence; reads the operator DID dynamically
    from the running node's env. Live install + live-engine push = the operator step.

No mint predicate effect is realized on the LIVE engine until the anti-sybil membrane (moyai
PoC) is wired and Council-attested; the local commit-DAG is a content-addressed append-only log.

## Consequences

- **+** Closes the "convening" coverage gap: the substrate can now *grow* social
  capital through designed gatherings, not only disclosure + wellbecoming.
- **+** Sybil/engagement-farming is structurally unrewardable: minting on
  *survived, anti-sybil-validated* ties (not headcount) makes a fake event a net
  **burn**, not a profit.
- **−** Tie-survival settlement adds latency (capital mints S epochs *after* the
  event) and depends on kizuna's live ingest leg landing first.
- **−** One new mint predicate touches the social capital MV — needs the kotoba-query
  `mv.rs` per-commit-Δ step extended (small, additive; same shape as disclosure).
