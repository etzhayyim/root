---
id: adr-2606131350-yabai-sms-smishing-ioc-and-yoro-ondevice-organizer
title: "ADR-2606131350: yabai JP SMS smishing IOC corpus + yoro on-device Gemma E4B SMS-organizer R0"
status: accepted
doc_type: adr
topic: yabai-sms-smishing-ioc-and-yoro-ondevice-organizer
authoritative: true
last_verified: 2026-06-13
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - yabai SMS smishing IOC corpus (defensive CTI)
  - yoro on-device SMS-organizer design (Gemma E4B QAT, default-SMS-role)
depends_on: []
related:
  - adr-2605301400-tadori-onchain-tx-tracing
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605215000-etzhayyim-inference-murakumo-only
  - adr-2604291630-yoro-guest-projector-browser-local-gemma-e2b
  - adr-2605140740-yoro-gemma-e4b-social-post-translation
supersedes: []
superseded_by: []
---

# ADR-2606131350: yabai JP SMS smishing IOC corpus + yoro on-device Gemma E4B SMS-organizer R0

**Status**: accepted (IOC corpus LANDED, PR #1707 merged 2026-06-13; on-device organizer = R0 design)
**Date**: 2026-06-13
**Deciders**: Jun Kawasaki

# Context

An operator full-device Android SMS ingest (Pixel 10 Pro Fold, Android 16, arm64-v8a, 16GB
RAM; warehoused in the private com-junkawasaki repo per its ADR-0016) surfaced two etzhayyim
concerns:

1. **A real, first-hand JP SMS smishing campaign corpus.** Of 587 messages, a large fraction
   are smishing — most prominently a long-running WhatsApp-impersonation campaign (JP-language
   "account deletion / unverified / high-risk login" lures) that rotates both typosquat lure
   domains and spoofed alphanumeric sender IDs across 2025-11 .. 2026-05. This is exactly the
   defensive CTI yabai exists to hold (ADR-2605301400 §T3), and a first-hand observation is
   higher-value than a vendor feed.

2. **"Organize the messages on the device itself" is impossible from adb.** `adb shell content
   delete --uri content://sms` returns exit 0 but deletes nothing (empirically verified: 587
   before and after). Android 16 (non-root) grants SMS write/delete ONLY to the holder of the
   default-SMS-app role (`RoleManager.ROLE_SMS`); the adb shell UID (2000) does not hold it.
   On-device organization therefore requires an app that takes the default-SMS role — which is
   the natural home for on-device LLM triage and connects to the Baien edge-target invariant
   (ADR-2605241900) and yoro's existing SMS plumbing.

# Decision

## A. yabai SMS smishing IOC corpus (LANDED)

`20-actors/yabai/data/sms-smishing-jp-2026h1.kotoba.edn` — a kotoba EAVT corpus using the
existing `:indicator/*` vocab (ADR-2605301400 §T3 ontology):

- **19 lure domains** (16-domain WhatsApp-impersonation typosquat rotation + Mastercard / 楽天
  / iCloud one-offs), **17 spoofed alphanumeric sender IDs**, **2 sender phone numbers**
  (1 pig-butchering "wrong number" opener, `:candidate`).
- `:sourcing :authoritative` (first-hand), TLP:CLEAR. **Victim/target identifiers fully redacted
  (G6/G10)** — attacker-side infrastructure only; no plaintext PII enters the public substrate.
- Ontology doc enums minimally extended: `:indicator/type` += `:sender-id :phone`,
  `:indicator/category` += `:scam` (doc-string only, no structural change).

Separation of duties unchanged: yabai SCORES; the Council enforces; tadori holds case evidence.
Merged via PR #1707 (2026-06-13). Mergeable into the merged CTI graph via `methods/ingest.py`
in a follow-up; the file follows the `seed-passive-dns.kotoba.edn` shape.

## B. yoro on-device Gemma E4B QAT SMS-organizer (R0 design)

The on-device SMS-organizer is an **extension of yoro**, not a new app — yoro Android already
reads SMS natively (`AndroidDataImportPlugin.java`, `Telephony` + `READ_SMS`) and ships a
fastlane release pipeline (iOS lanes create_app/certs/build/beta/release/submit/metadata;
Android lanes build/build_aab/device/beta/release/promote; `com.etzhayyim.yoro`).

Two native Capacitor plugins are added:

1. **default-SMS-role plugin** — request `RoleManager.ROLE_SMS`; once granted, SMS
   write/delete/move become available (the only path to on-device organization, per Context #2).
2. **on-device inference plugin** — MediaPipe LLM Inference / LiteRT running **Gemma 3n E4B QAT
   int4** (effective-4B, ~4.4GB). The 16GB/arm64-v8a/Android-16 device is far above the Baien
   `Android 4GB` baseline (ADR-2605241900); this lowers the server-side `gemma4:e4b` translation
   model (ADR-2605140740, Murakumo) onto the handset for **classification/triage only**
   (spam / 督促 / 本人確認 / 対人 / OTP). SMS bodies never leave the device — consistent with the
   Murakumo-only-or-on-device inference posture (ADR-2605215000) and warehouse no-PII-egress.

**ClojureScript feasibility**: the UI layer is ClojureScript-ready — yoro-ui already runs a
shadow-cljs + Reagent/re-frame migration harness (ADR-2606121350). The two new capabilities,
however, are native (Kotlin): the default-SMS role and the LiteRT `.task`/`.litertlm` runtime
cannot live in a WebView. Target architecture: **Capacitor + ClojureScript UI + two native
Kotlin plugins**.

# Consequences

- yabai gains a first-hand, redacted, TLP:CLEAR smishing corpus (defensive CTI, reusable
  across orgs without holding the victim's PII).
- The "organize on the device" requirement is correctly scoped: read-only adb ingest (warehouse)
  is separate from on-device mutation (default-SMS-role app); the latter is deferred to the yoro
  organizer implementation.
- A concrete R0 realization of the Baien edge-target invariant for yoro: E4B QAT on-handset,
  not just browser-local E2B (ADR-2604291630).

# Alternatives Considered

- **Delete spam via adb** — impossible (default-SMS role required; empirically verified).
- **Server-side E4B triage** — would egress SMS bodies; violates warehouse/on-device posture.
- **New standalone SMS app** — yoro already holds SMS read, fastlane, and a cljs base; an
  extension is lower-cost.
- **Browser-local (WebGPU/transformers.js) for organization** — cannot take the default-SMS role
  and cannot run the QAT LiteRT format; native plugin required.

# References

- PR #1707 (merged 2026-06-13) — `20-actors/yabai/data/sms-smishing-jp-2026h1.kotoba.edn`
- com-junkawasaki ADR-0016 (Android SMS full ingest + on-device organizer) — private warehouse side
- ADR-2605301400 (tadori / yabai kotoba CTI vocab), ADR-2605241900 (Baien edge-target),
  ADR-2605215000 (Murakumo-only inference), ADR-2605140740 (yoro Gemma E4B translation),
  ADR-2604291630 (yoro browser-local E2B), ADR-2606121350 (yoro-ui svelte→cljs harness)
