---
id: adr-2606131600-shirabe-live-research-concierge-agent
title: "ADR-2606131600: shirabe 調べ — live research-concierge agent (kotoba-clj + gemma4) Tier-B actor R1"
status: accepted
doc_type: adr
topic: shirabe-live-research-concierge-agent
authoritative: true
last_verified: 2026-06-13
priority: 3.0
axis: architecture
weight: 0.3
priority_note: "First live web-research + LLM-answer membrane; the gemma4/answer layer over kotoba web search that lets the etzhayyim stack answer a person's natural-language question the way a frontier assistant would, on kotoba-clj + Murakumo gemma4."
authoritative_for:
  - shirabe-research-session
  - live-research-concierge-pattern
depends_on:
  - 2605215000
  - 2605262130
  - 2605312345
  - 2606012300
  - 2606039200
  - 2606061000
  - 2606122400
  - 2606131300
related:
  - 2606061900
  - 2606072802
  - 2606064500
supersedes: []
superseded_by: []
---

# ADR-2606131600: shirabe 調べ — live research-concierge agent (Tier-B actor R1)

**Status**: accepted (founder direction 2026-06-13; Council attestation = PR review per the
bootstrap operational premise, root CLAUDE.md 2026-06-11)
**Date**: 2026-06-13
**Deciders**: Jun Kawasaki

## Context

The founder asked (2026-06-13), motivated by a concrete case — *"is 青山の島田 open today?"* —
whether asking an agent at etzhayyim.com would produce the **same** answer the way a frontier
assistant does, but on **kotoba wasm + gemma4**. An audit of the live site + codebase found the
pieces but no wiring:

- **kotoba web search** (ADR-2606012300) indexes Common Crawl — a stale snapshot, operator-gated,
  not a live look-up and with no LLM/answer layer;
- **gemma4** inference is Murakumo-fleet-only (ADR-2605215000); the default weight **Maxwell**
  (ADR-2606061000) is R0 (no weights);
- the observatory/mirror actors ingest disclosed corpora; none **answers a natural-language
  question** by reading the **live** public web and grounding a cited gemma4 answer.

A freshness question ("…今日やっている?") cannot be answered from a Datom-log or Common-Crawl
snapshot: it needs (a) a **live** read of the public web and (b) a model that reasons from the
retrieved facts **plus the current date**. That capability was absent.

The nearest neighbours establish the precedent and the boundary: **kawaraban** 瓦版 mirrors live
news media (link-out, never the verdict); **tsubasa** 翼 does live fare meta-search (member
self-books, no inflow); **watari** 渡り ingests live AIS — i.e. **read-only external fetch** is an
established, charter-clean posture. **karakuri** 絡繰 (ADR-2606039200) defines own-account
automation tiers; **meisai** (ADR-2606122400) established that a **local Ollama gemma 4 QAT** call
conforms to the Murakumo-only invariant. What was missing is the membrane that composes a live
read-only web read with a Murakumo gemma4 answer.

## Decision

Create Tier-B actor **shirabe 調べ** (`20-actors/shirabe/`,
`did:web:etzhayyim.com:actor:shirabe`), written in **kotoba-clj** (`.cljc`, the clj-port-first
direction of ADR-2606131300) — a **live research-concierge membrane** that answers a
natural-language question via a bounded ReAct loop:

```
question ─▶ analyze (plan) ─▶ retrieve (read-only public web) ─▶ synthesize (Murakumo gemma4) ─▶ kotoba (Datom log)
```

- **analyze.cljc** — pure planner: freshness/qtype classification, entity extraction, bounded
  sub-query decomposition (≤4).
- **retrieve.cljc** — runs sub-queries through an **injected** read-only web fetcher; dedups by
  URL, ranks by token overlap, caps at `top-k`, content-addresses each snippet.
- **synthesize.cljc** — builds a citation-grounded prompt (plus the resolved **本日** date as a
  fact) and calls an **injected** Murakumo-fleet gemma4; parses `[n]` citations; surfaces
  `INSUFFICIENT` honestly. `allowed-infer-hosts` + `validate-host!` make a commercial LLM API
  structurally unrepresentable.
- **session.cljc** — the bounded ReAct orchestrator (`max-rounds` 2, loop-until-confident).
- **kotoba.cljc** — the **kotoba Datomic** write path: `[:db/add e a v]` tx-data + a
  content-addressed commit-DAG (`tx-cid`/`make-tx`/`append-tx`/`verify-chain`), the danjo/ibuki/
  meisai local-log pattern. The live `com.etzhayyim.apps.kotoba.datomic.transact` leg lives in the
  driver (operator-gated).
- **live.clj** — the G7-gated LIVE driver wiring a DuckDuckGo fetcher (G1) + a Murakumo Ollama
  infer (G2) into `session/research`, then persisting + verifying the chain.

The two live legs (`fetcher`, `infer`) are **injected**, so the pure methods do no ambient I/O —
the loop is a pure function of `(question, fetcher, infer, as-of)`, which keeps G7 structural and
makes the actor a content-addressed WASM component (One-Worker-many-WASM, ADR-2606014500).

### Gates (structural where possible)

- **G1 read-only public web, look-up never act** — the fetcher is read-only public web; shirabe
  never authenticates, books, buys, or submits a form. Purchasing/booking is a different
  member-principal actor (okaimono/shukubo/tsubasa).
- **G2 Murakumo-only inference** (ADR-2605215000) — `allowed-infer-hosts` allowlists LiteLLM
  127.0.0.1:4000 / EVO-X2 192.168.1.70:4000 / per-node Ollama 127.0.0.1:11434; `validate-host!`
  raises on any other host (test-enforced), and `kotoba/session-datoms` re-rejects a non-fleet
  model host at persist time.
- **G3 no personalization / no surveillance** — the loop takes only the question; no profile,
  cookies, history, or behavioural ranking.
- **G4 citation-grounded, non-fabricating** — the prompt forbids unsourced claims and answers
  `INSUFFICIENT` when sources do not suffice; the injected 本日 date is a fact, not a fabrication.
- **G5 bounded + sourced + transparent** — sub-queries ≤4, evidence ≤ top-k, ReAct ≤ max-rounds;
  the whole session is appended to the kotoba Datom log (相互監視, reciprocal not asymmetric).
- **G6 privacy** — `:shirabe.session/member` bound ONLY when a member signed; anonymous sessions
  bind no identity; the persisted log is local by default (`data/` gitignored).
- **G7 loop does no implicit network I/O** — both live legs injected; `live.clj` and the live
  `datomic.transact` are explicit operator/member steps, never a cron (test-enforced via the
  injected-fetcher/infer requirement).

### Non-goals

N1 not a purchasing/booking agent (look-up only; never acts outward) · N2 not a public ad index or
SEO engine (no ranking-for-money, no personalization) · N3 not a frontier-API client (Murakumo-only,
gemma4) · N4 not a surveillance/profiling tool (no user model) · N5 not an arbiter of truth — it
reports cited sources and says `INSUFFICIENT` rather than fabricate.

## Consequences

- The etzhayyim stack can now answer a person's freshness question the way the founder asked for:
  **verified live 2026-06-13** — `live.clj "青山の島田は今日やっている?"` ran a real DuckDuckGo
  search (6 real sources: soba-aqua / navitime / ぐるなび / hotpepper / retrip) → a real local
  **gemma 4 E4B QAT** (Murakumo-conformant) answer『…本日（2026-06-13）は第2土曜日であり、定休日
  であるため営業していない [2,4]』→ a content-addressed kotoba Datomic tx (verify-chain ok). The
  same loop with the committed EDN fixture is deterministic and test-covered.
- R1 lands: 6 `.cljc` methods (kotoba-clj, run under babashka + the kotoba engine) + `live.clj`
  driver + EDN fixture + lexicon (`com.etzhayyim.shirabe.researchSession`) + manifest/CLAUDE/wasm
  README + **21 tests / 53 assertions green**.
- The remaining legs are the usual operator/Council-gated ones (no-server-key): the
  etzhayyim.com worker `/ask` route, the live `datomic.transact` to a running kotoba node, the
  componentize-py WASM build, and the LiteLLM-gateway path when the fleet is up.

## Alternatives Considered

- **Surface kotoba web search (ADR-2606012300) publicly + add an LLM layer** — kept as a parallel
  track for the *index* side, but it answers from a Common-Crawl snapshot and cannot answer a
  freshness ("today") question; shirabe is the *live* look-up + answer membrane. The two compose.
- **Extend an existing concierge (toritsugi/…)** — rejected: those are 行政手続き-specialised with a
  UPL boundary; a general live-web research membrane does not fit their semantics.
- **Python pure-stdlib (the meisai/inochi R0 shape)** — written first, then dropped per founder
  direction in favour of **kotoba-clj** (`.cljc`), aligning with the clj-port-first invariant
  (ADR-2606131300); babashka runs the reference oracle today, the kotoba engine runs it as WASM.

# References

- ADR-2605215000 — Murakumo-only inference (no commercial GPU/API)
- ADR-2606012300 — kotoba hybrid web search (Common Crawl; the index sibling)
- ADR-2605312345 — kotoba Datom = first-class canonical state
- ADR-2606122400 — meisai (local Ollama gemma 4 QAT = Murakumo-conformant)
- ADR-2606131300 — Clojure-port determinism + golden-file first-class
- ADR-2606061000 — Maxwell default LLM weight
