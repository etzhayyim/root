---
id: adr-2606292130-google-ads-charter-clean-outreach-performance-marketing-actor-r0
title: "ADR-2606292130: com-google-ads — charter-clean outreach & performance-marketing actor (R0)"
status: proposed
doc_type: adr
topic: google-ads-charter-clean-outreach-actor
authoritative: true
last_verified: 2026-06-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/com-google-ads
depends_on:
  - 2606022300   # akashi — public ad-disclosure transparency (the disclose/verify sibling)
  - 2606072600   # talent — self-sovereign cohort-first registry (audience consent source)
  - 2605215000   # Murakumo-only inference
  - 2605262130   # kotoba storage substrate unification (EAVT canonical)
  - 2605301600   # danjo — public accountability oversight (spend transparency downstream)
related:
  - 260607        # clean-room actors / 600-generation (googleads-compat is the REST shell)
  - 2605181100   # Signal-E2E PII ciphertext
supersedes: []
superseded_by: []
---

# ADR-2606292130: com-google-ads — charter-clean outreach & performance-marketing actor (R0)

**Status**: proposed
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki

# Context

The organization needs to do **outreach** — surface its mission (events,
publications, mutual-aid drives, land-sovereignty campaigns, donation
appeals) to people who would opt into hearing about it. In the prevailing
ad-tech stack ("Google Ads" standing in for the whole performance-marketing
ad-platform category), outreach is purchased through a system whose telos is
**surveillance-based conversion optimization**: individual behavioral
targeting, cross-site tracking pixels, opaque auctions, retargeting,
microtargeting of protected categories, and third-party purchased/scraped
audiences — with spend actuated by auto-optimizers that answer to no human
sign-off.

A religious-corp / commons actor cannot adopt that stack as-is. The harms are
not incidental features to disable; they are the substrate's business model.
But the org also cannot pretend outreach does not exist — mission
amplification is a legitimate function, and ceding it to commercial ad-tech
(or doing it opaquely) is itself a governance failure.

There is already a sibling actor that defines the **disclose/verify** side of
advertising for this org: **akashi (証)**, ADR-2606022300 — a kotoba-native
actor that passively ingests *already-public* platform ad-disclosure evidence
into source-cited EAVT and emits non-adjudicating transparency links.
akashi is read-only and third-party-facing. What is missing is the
**buy/create side**: an actor that plans, proposes, and (only after human
sign-off) publishes the org's *own* outreach campaigns — under constitutional
invariants that make it structurally incapable of the surveillance/ad-tech
harms akashi exists to surface in others.

A REST clean-room shell already exists as `googleads-compat` (ADR-260607,
L4, 30 endpoints over Campaign/Audience/Event/Profile/Message/Funnel,
kotoba-wasm). That is an API-compatible external surface. This ADR does NOT
extend the compat shell; it defines the **kotoba-native semantic actor**
`com-google-ads` (actor id `com-google-ads`, glyph 広) whose data model,
governance, and cross-actor boundaries are the org's own — not a clone of
Google's.

# Decision

## 1. com-google-ads is the charter-clean inversion of the ad-platform telos

| Ad platform (harm to invert) | com-google-ads (charter-clean) |
|---|---|
| individual behavioral targeting / profiling / retargeting | **cohort-scale only**; no `:person/*` individual profile exists (G2) |
| cross-site tracking pixel / ad SDK / third-party identity | **no ad SDK, no tracking pixel**; first-party aggregate only (G8) |
| auto-optimized spend, no human accountability | **propose → human sign-off → publish**; finance DID approves via interrupt-before (G1) |
| opaque spend | **append-only, finance-signed spend ledger** as durable EAVT (G4) |
| purchased / scraped / third-party PII audiences | **self-sovereign opt-in cohorts only**; prohibited sources refused, license notwithstanding (G3) |
| microtargeting protected categories, dark patterns | **anti-manipulation gate** on creatives + targeting (G5) |
| vendor LLM narration | **Murakumo-only** (G6, ADR-2605215000) |
| disclosures are the platform's, not the advertiser's | **every published creative + spend range mirrored to akashi 証** as the org's own disclosure (G7) |

The single invariant, analogous to robotaxi's "AR1 never actuates a rejected
trajectory":

> **com-google-ads never publishes a campaign, bid, budget, or creative that
> a human (finance/Council) has not approved, and never targets an
> identifiable individual.**

## 2. Topology: propose ⊣ govern ⊣ approve, observe-only performance

```
cohort (from talent / self-sovereign opt-in, G3)
        │
        ▼
   ┌──────────────┐   proposal    ┌──────────────────┐
   │ ProposeCell  │ ────────────▶ │  PolicyGovernor  │  (independent: G2/G3/G5 gates)
   │ (LLM advisor,│  campaign +   │  cohort-only? •  │
   │   sealed)    │  bid/budget/  │  consent-proven? │
   │              │  creative     │  anti-manip?     │
   └──────────────┘               └────────┬─────────┘
                              accept ◀─────┴────▶ reject/hold
                                │                     │
                          [interrupt-before           │
                           :request-approval]         │ (MRC analog = zero-spend pause)
                                │                     │
                          finance DID signs off       │
                                ▼                     
   ┌──────────────┐   publish      ┌──────────────────┐
   │  SpendCell   │ ─────────────▶ │  DiscloseCell    │ ──▶ akashi 証 (G7 mirror)
   │ (append-only,│  campaign +    │  creative + spend│     + danjo (public accountability)
   │  finance-    │  spend datoms  │  range disclosure│
   │  signed, G4) │                └──────────────────┘
   └──────────────┘
        ▲
        │ aggregate performance (impressions/clicks/conv by cohort — no individual, G2)
   ┌──────────────┐
   │ PerformCell  │  (read-time aggregates flagged :bond/is-transient — never durable verdicts)
   └──────────────┘
```

The ProposeCell is a sealed intelligence node (Murakumo LLM advisor) returning
**proposals only**. The PolicyGovernor is an independent system (rules, not
LLM) that checks the cohort/consent/anti-manipulation invariants and can
**reject** a proposal (the MRC analog is a *zero-spend pause* — the safe
fallback when governance fails or confidence is low). `interrupt-before
#{:request-approval}` is the human-in-the-loop: a real finance/Council
sign-off, not a rubber stamp. Performance is **observe-only and
aggregate-first**; there is no per-individual journey.

## 3. Data model: kotoba EAVT, governance-annotated

Canonical state is the kotoba Datom log (ADR-2605262130). Schema in
`kotoba/schema.edn`. Six entity families:

- `:campaign/*` — cohort-bound, budget-capped, approval-gated, status
- `:audience/*` — self-sovereign opt-in cohort, k-anonymous, **hard-retractable** (GDPR Art 17; no `:_alive` soft-delete flag, mirroring talent G4)
- `:creative/*` — content hash + review verdict + akashi disclosure ref
- `:performance/*` — aggregate impressions/clicks/conversions by cohort; flagged `:bond/is-transient` (computed on read, like itonami G3 — never a durable verdict)
- `:spend/*` — append-only ledger, finance DID-signed
- `:proposal/*` — actor proposals + human disposition (commit/hold/reject), the audit trail

Identifying fields in audience consent records (if any contact PII is needed
for outreach) MUST be `signal:v1:` ciphertext (ADR-2605181100, G3); plaintext
is refused at the gate.

## 4. Constitutional gates (G1–G9)

| Gate | Name | Rule |
|---|---|---|
| G1 | propose-not-actuate | campaign/bid/budget/creative PUBLISH requires human (finance/Council) sign-off via `interrupt-before`; the actor only proposes. |
| G2 | cohort-scale-only | no `:person/*` individual targeting, profiling, retargeting, or cross-site identity; audiences are aggregate cohorts; anti-surveillance. |
| G3 | consent-gated-audience | audiences from self-sovereign opt-in + public-credential enrichment ONLY; purchased/scraped/third-party PII refused; identifying fields are Signal-E2E ciphertext; GDPR Art 17 hard delete. |
| G4 | spend-append-only-finance-signed | every spend/bid/impression is a durable EAVT datom, finance DID-signed; no silent/off-book spend. |
| G5 | anti-manipulation | no microtargeting of protected categories (religion/ethnicity/health/politics/sexual-orientation/age-inferred-minor); no dark patterns; no deceptive creatives; creative review gate. |
| G6 | murakumo-only-narration | ADR-2605215000; no vendor/external LLM. |
| G7 | akashi-transparency-mirror | every published creative + spend range mirrored to akashi 証 as the org's own disclosure; buy/create side and disclose/verify side are one loop. |
| G8 | no-ad-sdk-no-tracking-pixel | no Meta Pixel / GA4 ads / third-party ad SDK / affiliate tracking code in org properties; first-party aggregate only. |
| G9 | no-commercial-resale | no audience/lead resale, no competitor-intel SaaS; outreach is mission-bound. |

## 5. Cells

| Cell | Kind | Runtime | Doc |
|---|---|---|---|
| `googleads.audience` | datalog | kotoba | self-sovereign opt-in cohort registry, k-anon, hard-delete |
| `googleads.propose` | langgraph | wasm | proposal-only campaign planner; `interrupt-before` finance sign-off |
| `googleads.performance` | datalog | kotoba | aggregate-first performance read (transient, G2) |
| `googleads.spend` | datalog | kotoba | append-only spend ledger, finance-signed (G4) |
| `googleads.disclose` | langgraph | wasm | mirrors creative + spend range to akashi (G7) |

## 6. Cross-actor boundaries

- **upstream**: `talent` (self-sovereign cohort supply — opt-in cohorts flow from talent's consented registry), `isco` (occupation taxonomy for cohort keys)
- **peer**: `akashi` 証 (disclosure mirror target, G7 — the one-loop buy/disclose pair), `moushibumi` (political-neutral citizen participation — com-google-ads MUST NOT become voter persuasion; shared no-political-profiling boundary with akashi G4)
- **downstream**: `toritate` (ledger — spend records), `danjo` (public accountability — spend transparency)

com-google-ads is bounded AWAY from `malak`: no CTI, no ad-fraud case
creation. If a published creative's landing evidence intersects known
phishing/malware (from akashi's `malakEvidenceCandidate`), the path is
akashi→malak, not com-google-ads→malak.

## 7. Phased rollout

- **R0** (this ADR) — scaffold: manifest + EAVT schema + lexicons + gates + did + DESIGN. All cells raise at import until configured (mirrors akashi R0).
- **R1** — benchtop: single cohort, propose→approve→publish loop with mock performance, finance sign-off via interrupt, akashi mirror stub.
- **R2** — pilot: first real outreach campaign (e.g. a donation drive) under G1–G9, aggregate performance read, full akashi mirror.
- **R3** — multi-cohort fleet, cohort-level spend caps, Council promotion gates computed as Datalog queries over the spend+proposal audit log.

# Consequences

- **Real (designed, tested at R1)**: the propose-not-actuate invariant, cohort-only anti-surveillance, consent-gated audience, append-only finance-signed spend, akashi transparency mirror, creative anti-manipulation gate, Murakumo-only narration, the buy/disclose one-loop with akashi.
- **Mocked (R1 swap points)**: ProposeCell LLM (→ Murakumo LiteLLM loopback), the live ads-API publish adapter (→ the real first-party/consented channel), performance ingestion (→ platform aggregate reports, never individual).
- **Structurally impossible by design**: individual targeting, tracking pixels, purchased audiences, off-book spend, voter microtargeting.
- **Outward registration (owner-authorized 2026-06-29, standing-auth per CLAUDE.md «Actors»)**: split repo `etzhayyim/com-google-ads` → west entry → RAD identity journal (`:rad/repo "github.com/etzhayyim/com-google-ads"`, `:rad/did-web "did:web:etzhayyim.github.io:com-google-ads"`, `:rad/name "com-google-ads"`, `:rad/aozora-collection "com.etzhayyim.apps.googleads"`), per CLAUDE.md Actors section. Owner directive authorizes the outward flow as standard (not per-step-confirmed); landing in an isolated root worktree + PR per root CLAUDE.md (the shared root checkout is raced).

# Alternatives Considered

1. **Extend `googleads-compat`** (the REST clean-room shell) with gates. Rejected: the compat shell is an API-compatible external surface (L4, Google's entity shapes); bolting governance onto a clone leaves the telos intact. The native actor must own its data model and boundaries.
2. **No outreach actor at all** (abandon amplification). Rejected: ceding outreach to commercial ad-tech or doing it opaquely is a governance failure; the org needs a charter-clean way to amplify.
3. **A single "ads" actor that both buys and discloses** (merge with akashi). Rejected: akashi is read-only / third-party-facing / non-adjudicating transparency; com-google-ads is the org's own buy/create side with human-actuated publish. Separating them keeps the disclose/verify side independent of the buy side (the same reason akashi is bounded from malak).

# References

- akashi — `20-actors/akashi/manifest.edn`, ADR-2606022300
- talent — `20-actors/talent/manifest.edn`, ADR-2606072600
- itonami — `20-actors/itonami/` (observe→recommend, transient datoms), ADR-2606082300
- robotaxi-actor — sealed intelligence ⊣ independent governor pattern, ADR-0001
- googleads-compat — REST clean-room shell, ADR-260607
- Murakumo-only inference — ADR-2605215000
- Signal-E2E PII — ADR-2605181100
- kotoba storage substrate — ADR-2605262130
