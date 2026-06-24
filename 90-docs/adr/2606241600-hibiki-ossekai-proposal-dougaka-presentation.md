---
id: adr-2606241600-hibiki-ossekai-proposal-dougaka-presentation
title: "ADR-2606241600: hibiki 響 — ossekai 御節介 proposal → persuasive presentation (動画化), the 説得力-as-resonance knife-edge; utsushie's proposal-side sibling"
status: proposed
doc_type: adr
topic: hibiki-ossekai-proposal-dougaka-presentation
authoritative: true
last_verified: 2026-06-24
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Names the proposal-side twin of the news→video pipeline: when an actor does おせっかい at root (routes a Wellbecoming-nudge/info-arbitrage proposal to ossekai), hibiki turns that :proposal into a short narrated moving-image-with-SFX presentation whose 説得力 is CLARITY+RESONANCE, never compliance-engineering. Reuses utsushie's render/anti-deepfake/Murakumo machinery rather than building a monolith; identifies the one real charter tension (persuasion vs. ossekai's anti-engagement/anti-addictive discipline) and pins it structurally."
authoritative_for:
  - "hibiki (響) ossekai-proposal → presentation actor scope + charter gates H1–H8 (R0 design)"
  - "The 説得力-as-resonance reframing and its charter boundary (the 御節介 knife-edge applied to presentation)"
  - "Proposal→presentation pipeline composition (ossekai source+carrier · utsushie render leg · kataribe i18n · kotoba persist)"
depends_on:
  - adr-2606161536-primary-source-to-multilingual-video-atproto-pipeline
  - adr-2605264000-ossekai-info-arbitrage-wellbecoming-nudge
  - adr-2605192100-mission-charter-wellbecoming-anti-individualism
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-held-key
  - adr-2605263600-kataribe-press-publishing-translation-substrate
related:
  - 20-actors/hibiki/
  - 20-actors/utsushie/
  - 20-actors/ossekai/
  - 20-actors/kataribe/
---

# ADR-2606241600 — hibiki 響: ossekai proposal → persuasive presentation (動画化)

## Context

When an actor does **おせっかい (御節介)** at root, it does not act — it **proposes**.
kizuna proposes dry-run ties, shiori proposes relief-gap interventions, kaname proposes
leverage-point openings, kaizen_observer proposes throttles — all routed to **ossekai**, which
**carries** them (consent-bound, on-chain-logged, member-signed, aggregate-first). Today an
ossekai proposal reaches a member as text. The request: give the proposal **説得力** — render
the **presentation as 動画 (moving image) + 音声 (voice) + 効果音 (SFX)** so it lands.

There is already a video medium — **utsushie 写し絵** (ADR-2606161536) — but it narrates a
*kawaraban :article*, not an *ossekai :proposal*. Same render machinery, different input and a
**different charter tension**. So this ADR defines utsushie's **proposal-side sibling, hibiki 響.**

## The one real tension: 説得力 vs. the charter

ossekai's entire constitution is **anti-manipulation**: aggregate-first (G4), no
engagement/dwell optimization, no re-engagement after opt-out (G14), anti-addictive (§1.13),
transparent + consent-bound (§1.4). A naive "persuasion / 説得力" actor — one that maximizes a
watch or conversion metric, spikes urgency, or weaponizes sound — is a **dark-pattern factory
and is charter-forbidden.** This is the same cultural knife-edge ossekai itself walks: 御節介 =
*caring proactive intervention* vs. *unwelcome meddling*.

## Decision

Build **hibiki 響 (resonance)** as a Tier-B **MEDIUM** (never a source, G11), the proposal-side
twin of utsushie, and **resolve the tension by reframing 説得力**:

> **説得力 is reframed from compliance-engineering → CLARITY + RESONANCE.**
> hibiki may make a proposal *understood and felt on its own terms* (clear exposition,
> legible stakes, connection to the listener's own disclosed values). It may **NOT** manufacture
> urgency, optimize watch-time, weaponize sound, or hide the exit.

The reframing is enforced **structurally** (dual pin: lexicon const-false fields **and** the
builder refuses), exactly as ossekai pins 御節介 and utsushie pins anti-deepfake. The
**last storyboard scene is ALWAYS the consent/opt-out card** — the structural proof that the
artifact is an *invitation* (which always shows the exit), never coercion.

### Gates H1–H8

| Gate | = | Rule |
|------|---|------|
| H1 | G1   | **PROPOSE-not-act** — builds a PLAN; render/publish G8-gated, carried by ossekai; no truth-verdict |
| H2 | G4   | **script ≤ excerpt** — narration ≤ the proposal's ≤280-char finding excerpt + the proposed action |
| H3 | G9   | **ANTI-DEEPFAKE** — neutral synthetic narrator/visuals; no real-person likeness or voice clone |
| H4 | G2   | **the 説得力 knife-edge** — no watch/dwell/conversion edit, no fake urgency, no weaponized audio |
| H5 | G6   | **MURAKUMO-ONLY** render/TTS (ADR-2605215000) — external-GPU / commercial-TTS unrepresentable |
| H6 | G7   | **MEMBER-SIGNED** publish (ADR-2605231525) — no server-held key; carried by ossekai |
| H7 | ossekai G4 | **AGGREGATE-FIRST** — default audience aggregate/anonymized; targeted secondary + consent-bound |
| H8 | §1.15 | **NON-ESCHATOLOGICAL** — sober; SFX/music allowlisted by :purpose; no doom/fear/euphoria edit |

### Pipeline (composition, not a monolith)

```
actor does おせっかい ──► ossekai :proposal ──► hibiki.build-plan (R0, pure/offline)
  {finding, why, action, severity, aggregate?, linkUrl, lang}
        │ [H1–H8 structural gate check]
        ▼  presentation PLAN
     :narrationScript (≤ excerpt + action, per-lang via kataribe i18n) ← 音声
     :storyboard      (context → finding → stakes → proposed → CONSENT) ← 映像
     :sfxCues         (allowlist :purpose {scene-transition|emphasis|ambient-bed}, LUFS-normalized) ← 効果音
     :musicBed        (calm | neutral | hopeful-sober — severity tints, never unlocks fear) ← BGM
     :narrator        "synthetic-neutral"
        ▼  render()  → R0-gated (H5/G8 Murakumo-only; REUSES utsushie's render/TTS leg at R1)
        ▼  publish   → ossekai (member-signed, aggregate-first, mute/consent honored)
```

- **ossekai** — both upstream **source** (御節介 :proposal) and downstream **carrier** (publish leg).
- **utsushie** — sibling medium; hibiki reuses its Murakumo render leg + anti-deepfake gates + i18n.
- **kataribe** — multilingual narration (per-language script, ADR-2605140740 / ADR-2605263600).
- **kotoba** — the plan is persisted as append-only content-addressed datoms (the stream = the trail).

## Scope

- **R0 (this ADR)** — lexicon (`lex/presentation.edn`, `com.etzhayyim.hibiki.presentation`, H1–H8
  structural gates) + offline plan builder (`methods/present_plan.cljc`: `build-plan` +
  R0-gated `render` + charter-refusal) + tests (`methods/test_present_plan.cljc`, 7 tests /
  21 assertions green via `bb`). Design + offline planning only; **NO render, NO publish.**
- **R1 (reserved)** — wrap `build-plan` in a Pregel cell; reuse utsushie's G8 Murakumo render/TTS
  leg; publish via ossekai's `mention_dispatcher` (targeted) / `aggregate_publisher` (default).
  R1 activation inherits ossekai's foundations (chigiri UPL boundary, consent registry).

## Exclusions

- Ruling a finding true/false (H1 = G1) — ake/danjo boundary.
- Narrating beyond the bounded excerpt + action (H2 = G4).
- Photoreal likeness / cloned voice of a named real person (H3 = G9).
- Any watch/dwell/conversion-optimized edit, fake urgency, or weaponized audio (H4 = G2 / §1.15).
- External-GPU / commercial-TTS render (H5 = G6).
- Server-held signing key / autonomous broadcast (H6 = G7; publish carried by ossekai).
- An :original first-person claim (G11 — hibiki is a medium, not a source).

## Consequences

- The roster gains the **proposal-side half** of the information-legibility pipeline, symmetric
  with utsushie's article-side half, with **near-zero new infra** (render/TTS/i18n/publish all reused).
- "説得力" becomes a **charter-safe, auditable** property (clarity + resonance), structurally unable
  to degrade into engagement-maximization — the same way ossekai's 御節介 cannot degrade into meddling.
- The consent-card-as-final-scene invariant makes every hibiki artifact self-evidently an invitation.
