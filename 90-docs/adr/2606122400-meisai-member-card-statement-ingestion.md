---
id: adr-2606122400-meisai-member-card-statement-ingestion
title: "ADR-2606122400: meisai 明細 — member card-statement (利用明細) ingestion Tier-B actor R0"
status: accepted
doc_type: adr
topic: meisai-member-card-statement-ingestion
authoritative: true
last_verified: 2026-06-12
priority: 3.0
axis: architecture
weight: 0.3
priority_note: "First member-own personal-finance ingestion actor; the statement-table ground truth beneath organizer's mail patterns and kaiyaku's recurring-charge ties."
authoritative_for:
  - member-card-statement-ingestion
  - meisai-datom-shape
depends_on:
  - 2605262130
  - 2605312345
  - 2605215000
  - 2606039200
related:
  - 2606112201
  - 2605262900
  - 2605302000
supersedes: []
superseded_by: []
---

# ADR-2606122400: meisai 明細 — member card-statement ingestion (Tier-B actor R0)

**Status**: accepted (founder direction 2026-06-12; Council attestation = PR review per the
bootstrap operational premise, root CLAUDE.md 2026-06-11)
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki

## Context

The founder asked (2026-06-12) for an actor that ingests their card 利用明細 from
sumitclub.jp (SuMi TRUST CLUB), placed in etzhayyim root. The fetch capability already
exists outside this repo as a generic, reusable stack —
`com-junkawasaki/{langgraph-clj, langchain-clj, computer-use-clj}` — whose
`examples/sumitclub_meisai.clj` is a READ-ONLY computer-use agent the member runs on
their own machine against their own account: credentials are vault-injected
(`type_secret`, 1Password/Bitwarden — a secret never reaches the model, the message
history, or the action log), the system prompt forbids every state-changing control on
the card site, and inference defaults to **local Ollama gemma 4 QAT**, which conforms to
the Murakumo-only inference invariant (ADR-2605215000) — no vendor LLM API callout.

What was missing is the etzhayyim-side ingestion: statement rows as datoms on the
canonical substrate (kotoba Datom log, ADR-2605262130 + 2605312345), under this repo's
constitutional discipline for personal data.

The roster's nearest neighbors do adjacent but distinct things: **organizer** detects
ご利用明細 *mail* patterns; **kaiyaku** 解約 consumes recurring-charge ties; **karakuri**
絡繰 defines the own-account automation posture (T1 API > T2 ToS-permitted headless >
T3 export) that the fetch leg instantiates; **toritate** 執帳 is the corp's OWN books
(a member's personal card is not that); **warifu** 割符 is the corp's own card rail.
None holds the member's statement table itself.

## Decision

Create Tier-B actor **meisai 明細** (`20-actors/meisai/`,
`did:web:etzhayyim.com:actor:meisai`): member-own card-statement ingestion into a
local, append-only, content-addressed kotoba Datom log, family pattern
(danjo/shionome/kanjō `methods/` + `autorun.py` heartbeat).

Datom shape: `meisai-stmt:<source>:<YYYY-MM>` with
`:meisai.stmt/{source,month,total-jpy,row-count,intake-cid,source-url}`;
`meisai-row:<sha256[:16]>` with
`:meisai.row/{stmt,index,date,merchant,amount-jpy,note}`. `:db/add` only.

### Gates (structural where possible)

- **G1 member-own only** — the sole input is a local intake file the member produced
  about their own account.
- **G2 credential/PAN unrepresentable** — `ingest.guard` RAISES on credential-shaped
  keys (password/secret/otp/cvv/pin/token) and PAN-shaped values (13–19-digit runs)
  anywhere in an intake (test-enforced). meisai holds no credential; the vault stays at
  the member's host.
- **G3 local-only personal data** — `data/` (intake + persisted log) is gitignored; the
  loop persists locally and publishes/pins/posts nothing. This repo is public; a card
  statement in a commit is unrecoverable.
- **G4 read-only at source** — the fetch leg's HARD-RULES prompt forbids every
  state-changing control (支払い方法/リボ/分割/変更/登録/解約/申込); meisai itself never
  contacts the source.
- **G5 provenance + dedup** — every statement tx carries the intake content CID; row
  entities are deterministic hashes; re-ingest is a no-op; `verify_chain` detects tamper.
- **G6 Murakumo-only inference** — the fetch leg defaults to local Ollama gemma 4 QAT
  (`jvm_host.clj` `LLM=ollama`); vendor-LLM adapter paths are not used in the etzhayyim
  context (ADR-2605215000).
- **G7 live leg operator-gated** — the browser fetch is an explicit member/operator
  step, never a cron; meisai's own loop does no network I/O (test-enforced).

### Non-goals

N1 not a budgeting advisor (no advice/scoring) · N2 not a third-party scraper service ·
N3 not a payment instrument · N4 not a publication pipeline (aggregates would need a
future Council-gated ADR) · N5 not a credential store.

## Consequences

- The organizer → kaiyaku subscription pipeline gains row-level ground truth: recurring
  merchants in `:meisai.row/*` can feed kaiyaku's 縁-ledger worklist (R1 handoff).
- The karakuri T2 posture gets its first concrete financial-site instantiation, with the
  credential boundary held by the vault layer rather than policy text.
- R0 lands: methods (kotoba.py / ingest.py / autorun.py, pure stdlib, pywasm-ready) +
  21 green checks + manifest/README/CLAUDE/MATURITY. Lexicon
  (`com.etzhayyim.meisai.statement`), fleet heartbeat registration, kaiyaku handoff, and
  additional card sources are R1, gated as usual.
