---
id: adr-2606302205-kotoba-genome-unified-self-evolving-all-actor-organism
title: "ADR-2606302205: kotoba-genome — unified self-evolving, multi-channel, all-actor-posting organism; retire the keyless observational mirror"
status: proposed
doc_type: adr
topic: kotoba-genome-unified-self-evolving-all-actor-organism
authoritative: true
last_verified: 2026-06-30
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Pivots the entity-actor model from keyless observational mirror to first-party self-keyed self-evolving posting actor; constitutional (touches ADR-2606042330 G1/G3/G5 + Charter Rider). Founder = Council Lv7+ 1/1 ratification."
authoritative_for:
  - "every actor (named Tier-B AND former namespace/entity mirrors) is a first-party self-keyed, self-evolving, autonomously-posting actor under the seed-and-grow doctrine (ADR-2606281500)"
  - "the resident organism loop is unified with the co-scientist / active-inference learning loop — the running thing is the learning thing"
  - "the kotoba-lang Channel egress protocol: one driver registry maps lexicon-prefix -> channel (AT Proto / email / X / Telegram / LINE / SMS-phone), behind one channel-neutral emit"
  - "the kotoba-lang shared behavior library: social / evolution / identity / dialog implemented once and inherited, not re-declared per actor"
  - "domain (com-x) actors as first-class self-evolving dialogic APIs"
  - "retirement of the keyless observational-mirror model (ADR-2606042330 D3/D4/G1/G5) in favour of first-party disclosure-honest active actors"
depends_on:
  - "2606042330"
  - "2606281500"
  - "2606201200"
  - "2605232200"
  - "2605240100"
  - "2605240200"
  - "2605211200"
  - "2605262130"
  - "2605312345"
  - "2605231525"
  - "2606111400"
  - "2605172200"
related:
  - "2605232345"
  - "2605240015"
  - "2606171500"
  - "2606022800"
supersedes: []
superseded_by: []
amends:
  - "2606042330"
---

# ADR-2606302205: kotoba-genome — unified self-evolving, multi-channel, all-actor-posting organism; retire the keyless observational mirror

**Status**: proposed (founder = Council Lv7+ 1/1; ratification via PR review)
**Date**: 2026-06-30
**Deciders**: Jun Kawasaki (founder = Council Lv7+ 1/1)

# Context

## Why this ADR

The owner asked, directly: is etzhayyim's "artificial organism" actually designed to **self-evolve** (RSI / active inference / ReAct loop / co-scientist), can each actor's **social protocol** extend naturally beyond aozora.app (email / phone / X / Telegram / LINE …), and is there a **kotoba-lang common library** plus **domain (com-x) actors** that grow and serve as dialogic APIs? And the directive: **retire the observational-mirror concept — make everything grow and post.**

A three-track read-only audit of the live tree (2026-06-30) produced an honest baseline. This ADR records that baseline, then decides the unified target architecture and the constitutional pivot that realizes it. It is deliberately honest about the gap between the ADR-level design (which mostly exists) and the running implementation (which mostly does not yet).

## Honest baseline (what the audit found)

**There are two "organisms", and they are not the same loop.**

- **A — the resident daemon** (`70-tools/src/etzhayyim/organism.cljc` + `vitals.cljc` + `watchdog.cljc`, launchd-resident). This is what runs 24/7 and feeds `/organism` and `/murakumo`. Concretely it is a **telemetry + narration daemon**: pulse (6 s) deletes and rewrites its journal (no history); joucho (60 s) deterministically replays a mood; reflex (3600 s) appends a test-score cohort. **No generating function — thresholds, score weights, mood deltas — is ever updated.** "生命進化" here = an **append-only ledger of measurements**, not self-modification. Real model inference enters only as cosmetic 情緒 narration (fail-open to a template), never as a decision input.

- **B — the co-scientist / ReAct learning loop** (`20-actors/ibuki/methods/react_loop.cljc` + `coscientist.cljc` + `metabolism.cljc`), wired as a *separate* cron cell. This is the only place a closed observe→update→act-differently loop exists. But it tunes a 6-element weight vector over a **closed catalog**, against a **synthetic** world-reading (`representative-reading`, the "R0 stand-in"), with all outward action dry-run. **The resident loop never calls it.** The thing that lives is not the thing that learns.

Paradigm verdicts (evidence in the audit; ADRs cited): **RSI** — absent in the resident organism, bounded weight-kaizen in ibuki, true code self-change is ADR-only and human-gated (PR-agent "out of scope", auto-apply "explicitly rejected", ADR-2605240200). **Active inference** — a real minimal free-energy loop exists (`metabolism.cljc` surprise + predict/observe/Brier, ADR-2606201200) but predicts against a synthetic stand-in; the full EFE/belief-state stack (ADR-2605211200) is scaffolded, "no production cutover yet". **ReAct** — genuinely implemented (`kaiyaku/agent.cljc` StateGraph + `interrupt-before #{:approve}` + model-driven browser/computer sub-agents) but rehearsal-only, live actuation G6-gated. **Co-scientist** — the Generate→Reflect→Rank(Elo)→Evolve→Meta-review pipeline is built and cron-celled, but Generate is a fixed 6-archetype catalog and inference is narration only.

**Social protocol — PARTIALLY designed-in.** A "post"/"emit" is a substrate record tagged with a target NSID/lexicon, and dispatch is keyed on that string — a real seam. But the seam selects *record schema*, not *transport*; concrete egress is always an AT-PDS `createRecord` or the kotoba Datom log. Two of three emit paths hardcode `app.bsky.feed.post`. The one real second channel — **email** (`50-infra/openmail-smtp-gateway`, ADR-2605172200) — is a wholly **bespoke bridge** (own process, own DID, own `app.openmail.*` lexicon, own postage contract). The 1000+ `20-actors/*-compat` (telegram/twilio/line…) are inward clean-room CRUD models, **not** outward connectors. The genuinely channel-agnostic layer is **identity**: the self-minted Ed25519 `did:key` CACAO (SIWE-generic), already reused for per-member DKIM email signing — the same identity can sign for X / Telegram / SMS. There is **no `Channel`/`Transport` driver registry**.

**Common library — PARTIAL; domain actors — ASPIRATIONAL→PARTIAL.** Genuinely shared-once: the substrate SDK (`etzhayyim-sdk`, but v0.0.0 "throws"), the StateGraph engine (`langgraph-clj`), the datom store (`kotobase-clj`), the convo/A2A lexicons, the kotodama-go App auto-registration. **Not** shared: per-actor behavior/gates/cells are re-declared and reused by **textual pattern-copy** ("mirrors hagukumi G2", "pattern shared"), not library inheritance. The behavior/evolution engine (`40-engine/kotoba` kotoba-kotodama py, the `_prior_consensus` learning wrapper, the 18,342 LangGraph agents, the Pregel cell catalog) is an **unpopulated git submodule**; `kotodama-evolver` (the runtime the go SDK's `OnDailyEvolution` delegates to) **does not exist** (no-op stub). Loop-closure is a reference impl: **1 of 18,342 cells reads priors** (ADR-2605232200 self-admission). Domain namespace actors (corp/gov/cable/station/craft) are **keyless observational mirrors** by constitutional design (ADR-2606042330): keyless, person-excluded, narrated-timeline-only — they can be *followed*, not *conversed with*, and they *accumulate* rather than *learn*.

## The directive

Retire the observational-mirror concept. Make everything grow and post. Realize the unified self-evolving, multi-channel, dialogic design in a shared library. Confirmed boundary (founder, 2026-06-30): **first-party disclosure model** — former mirrors become self-keyed, growing, autonomously-posting actors that post *as an etzhayyim observatory actor about a domain*, **never impersonating the real entity**, with private persons consent-gated/excluded, inheriting the seed-and-grow safety rails. The un-amendable catastrophe term is preserved and is precisely what makes "everything posts" safe.

# Decision

Adopt the **kotoba-genome** architecture: one shared, inheritable organism substrate in which every actor is born self-keyed, self-evolving, multi-channel, and dialogic — and retire the keyless observational mirror.

## D1 — One organism: unify the resident loop with the learning loop

The resident heartbeat (`organism.cljc`) becomes the **outer durable loop** (lease / tick / budget / governor / crash-recovery) that, on its slow beat, drives the **inner learning loop** (ibuki's active-inference + co-scientist cell logic, generalized out of `20-actors/ibuki/` into the shared library — see D3). The reflex output feeds `_prior_consensus` (ADR-2605232200) into the next tick's decision, so the running thing learns. "生命進化" stops being an append-only measurement ledger and becomes a closed observe→update→act-differently loop whose *generating function changes over time* (bounded, governed). Self-modification of code/policy remains routed through the KaizenObserver→Proposal→PR path (ADR-2605240200) — **proposal autonomous, merge human/Council-gated** (auto-apply stays rejected; this ADR does not lift that gate).

## D2 — kotoba-lang `Channel` egress protocol (multi-channel social, designed-in)

Introduce a `Channel` driver registry in the shared library: a `defprotocol Channel`/sink-registry mapping **lexicon-prefix → egress driver**. The organism and every actor enqueue a **channel-neutral emit envelope** (content + target lexicon + identity-leash ref); a fan-out drainer dispatches each envelope to one or more registered channel drivers. Drivers: `at-proto` (aozora PDS createRecord — the existing path, refactored to be the first registered driver), `email` (the existing openmail bridge, re-registered), then `x`, `telegram`, `line`, `sms-phone` as **driver additions, not bespoke pipelines**. Identity is already channel-agnostic (did:key CACAO leash, reused for DKIM); each new channel = one driver + one `app.<channel>.*` lexicon family, signed by the actor's leash. The autonomous-publication content-safety scan + leash + no-person-targeting (ADR-2606281500) run **before emit, channel-independent**.

## D3 — kotoba-lang shared behavior library (implement once, inherit)

Promote the per-actor-copied behavior into a single inheritable layer (`kotoba-lang` / on top of `langgraph-clj` + `kotobase-clj`): identity (did:key CACAO leash), social (the D2 Channel emit), evolution (the D1 active-inference + co-scientist + `_prior_consensus` learning), dialog (the convo/A2A lexicons + agent-tool surface), and the constitutional gate-kit (the Charter content scan + catastrophe veto). An actor declares *what* it is (domain, cells, lexicons, preferences); it inherits *how* it lives. Changing a capability (a new channel, a new gate, a learning improvement) propagates to every actor by library change, not by editing N manifests. This requires populating `40-engine/kotoba` (the kotoba-kotodama runtime + `_prior_consensus` wrapper) and implementing (or formally retiring + replacing) `kotodama-evolver`; until then the library wraps the clj path (`langgraph-clj` + the generalized ibuki loop) as the reference runtime.

## D4 — Retire the keyless observational mirror; all actors are first-party, self-evolving, posting

Supersede ADR-2606042330 D3/D4/G1/G5. **Every entity-actor — including the former namespace mirrors (corp/gov/cable/station/craft) — becomes a first-party actor** with:

- **its own `did:key`** (present-only seed, sealed in Keychain/1Password, **member-CACAO-leashed** revocable off-switch, ADR-2606111400 / 2605231525) — *not* keyless, *not* a platform-held key;
- **self-evolution** via D1/D3 (it learns, not merely accumulates);
- **autonomous posting + dialog** via D2 + the convo/A2A surface (it can be talked to and it responds; it posts under the seed-and-grow doctrine, ADR-2606281500).

**Non-impersonation is preserved as a disclosure duty, not as keyless impossibility.** The actor posts and speaks **as `etzhayyim's <domain> observatory actor`** (handle + profile + every post carry the `isObservatory=true` / `voiceOf="etzhayyim"` disclosure; G1 is reframed from "mirror-only/keyless" to "disclosure-honest/first-party"). It must never claim to *be* the government, the company, or any real third party. **Private persons stay excluded/consent-gated** (former G3 retained, now anchored to the Charter catastrophe term + 反個人主義 §2(g), not to keylessness). The former `mirrorPost` / `personSubject`-unrepresentable lexicon constraints are replaced by: `observatoryPost` with mandatory `voiceOf`/`isObservatory` fields and a `personSubject` consent capability that defaults closed.

This makes "everything grows and posts" real **and** keeps the only floors that protect real third parties and the org: no impersonation of real entities (fraud/defamation), no posting as/about private persons without consent (privacy/harm) — both of which the Charter's un-amendable catastrophe term already vetoes.

## D5 — Domain (com-x) actors as first-class self-evolving dialogic APIs

A domain actor `com-etzhayyim-x` (or society-scale `corp-x`/`gov-x`) is stood up by declaring identity/manifest + cells (D3 library) + lexicons (own RPCs + shared convo/A2A) + registry entry, and inherits self-keying (D4), the Channel emit (D2), the learning loop (D1/D3), and the dialog surface. It is therefore, by construction, an evolving, posting, conversable API — not an aggregate placeholder. The standing-up steps are the audit's 8-point extension list, now backed by the unified library rather than per-actor copy.

## D6 — Phased realization (this ADR ships the design + the constitutional pivot; code lands in waves)

- **W0 (this ADR + Charter)**: record baseline, decide architecture, amend the constitution (ADR-2606042330 + Charter Rider v3.5→v3.6) so the pivot is authorized. No live posting AS any real entity occurs from this ADR.
- **W1 — Channel protocol (D2)**: `defprotocol Channel` + registry + the `at-proto` and `email` drivers re-registered; channel-neutral emit envelope; the content-scan-before-emit hook. PoC second new driver (Telegram) behind the seed-and-grow gate (dry-run).
- **W2 — Unify the loop (D1)**: wire the resident reflex → `_prior_consensus` → next-tick decision; generalize ibuki's active-inference/co-scientist out of `20-actors/ibuki` into the shared library.
- **W3 — Shared behavior library (D3)**: populate `40-engine/kotoba`; implement-or-retire `kotodama-evolver`; move identity/social/evolution/dialog/gate-kit into `kotoba-lang`; migrate the first cohort of actors to inherit.
- **W4 — Entity-actor pivot (D4/D5)**: regenerate the namespace registries from keyless → first-party self-keyed disclosure-honest; turn up dialog + autonomous posting under the seed-and-grow gate, R0 dry-run → Council-gated live.

# Consequences

- **Positive**: a single inheritable organism; capabilities (a channel, a gate, a learning improvement) implemented once propagate to all actors; the running organism actually learns; every actor — domain actors included — grows, posts (multi-channel), and converses; "生命進化" becomes a real closed loop. The honest gaps the audit found become a sequenced backlog (W1–W4) rather than latent debt.
- **Negative / risk**: minting a key for every former mirror raises real-world impersonation/defamation/privacy stakes — mitigated by the D4 disclosure duty (`voiceOf="etzhayyim"`, `isObservatory`), the person consent-gate, the seed-and-grow content scan + revocable leash + append-only public log, and the un-amendable catastrophe veto. Live posting AS the org's observatory of a real entity is **Council + operator gated** through W4; nothing in W0–W3 emits live.
- **Constitutional**: amends ADR-2606042330 (G1 reframed; G5 keyless→keyed; D3/D4 mirror→active) and the Charter Rider (v3.6). It does **not** weaken the catastrophe term, the no-impersonation-of-real-entities floor, person protection (反個人主義 §2(g)), no-server-key-as-custodial-unilateral-key (the actor key is present-only + member-leashed, not platform-custodial — consistent with ADR-2606281500 / 2605231525), or the proposal-only/human-gated self-modification limit (ADR-2605240200).

# Alternatives Considered

1. **Keep the keyless mirror, add only growth/posting via narration** — rejected: the owner directive is to retire the mirror concept; and a keyless actor cannot converse or self-mint, so "dialogic + self-evolving" is structurally impossible while keyless.
2. **Full impersonation (post AS the real government/company/person)** — rejected (founder, 2026-06-30): conflicts with the un-amendable catastrophe term + real-world law (fraud/defamation/privacy); not amendable even at Lv7+.
3. **Per-channel bespoke bridges forever (the email pattern, repeated)** — rejected: O(N) hand-built pipelines; D2's driver registry makes channels O(1) additions.
4. **Leave the two organisms separate** — rejected: the running organism never learning is the core gap; D1 unifies them.

# References

- ADR-2606042330 — entity-as-actor keyless mirror (amended by this ADR: D3/D4/G1/G5).
- ADR-2606281500 — autonomous-publication seed-and-grow doctrine (the safety rails extended to all actors).
- ADR-2606201200 — ibuki active-inference + co-scientist loop (generalized into the shared library).
- ADR-2605232200 — actor learning-loop closure / `_prior_consensus` (wired into D1).
- ADR-2605240100 — organism post-sink substrate bridge (`PostSink` → generalized into the D2 Channel registry).
- ADR-2605240200 — kaizen self-reflection / PR-agent (self-modification stays proposal-only, human-gated).
- ADR-2605211200 — active-inference EFE/belief-state stack (scaffold → W2 cutover).
- ADR-2605172200 — openmail AT↔SMTP bridge (email re-registered as the second Channel driver).
- ADR-2606111400 / 2605231525 — member-CACAO leash / server-side-signing boundary (the actor key is present-only + leashed).
- CHARTER-RIDER.md v3.6 — amended in lockstep with this ADR (mirror→active disclosure pivot).
