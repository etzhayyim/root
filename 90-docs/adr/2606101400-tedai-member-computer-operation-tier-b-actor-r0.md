---
id: adr-2606101400-tedai-member-computer-operation
title: "ADR-2606101400: tedai (手代) — member-computer-operation Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: tedai-member-computer-operation
authoritative: true
last_verified: 2026-06-10
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/tedai
  - com.etzhayyim.tedai.*
depends_on:
  - "2606039200"
  - "2605231525"
  - "2605215000"
  - "2605241900"
  - "2605181100"
  - "2605192200"
related:
  - "2606034800"
  - "2606042100"
  - "2606033600"
  - "2605302130"
  - "2606013800"
supersedes: []
superseded_by: []
---

# ADR-2606101400: tedai (手代) — member-computer-operation Tier-B actor (R0)

**Status**: proposed
**Date**: 2026-06-10
**Deciders**: Jun Kawasaki

# Context

The roster has a **browser-operation** actor — karakuri 絡繰 (ADR-2606039200) drives a GUI-only
*web service* on the member's own account through T1 official-API > T2 ToS-permitted browser-use >
T3 export — but **no computer-operation actor**: nothing that drives the member's own *computer*
(desktop apps, files, OS surfaces) the way frontier "computer-use" agents do (screenshot → plan →
click/type). The adjacent actors each stop short: ameno is the browser-local WASM *runtime* (it runs
actors, it does not operate the desktop), tazuna teleoperates *robot bodies* not computers
(ADR-2606042100), manimani *reads* PC files but never actuates, kotoba-os is a unikernel OS not a
desktop driver. The triggering request: *「kotoba の actor が browser, computer 操作ができるような
actor は設計している?」→「do it」.*

Desktop GUI toil is the same labor-liberation reservoir as web GUI toil (CLAUDE.md §Mission,
ADR-2605192100): re-keying between two desktop apps, hand-filing attachments, clicking through the
same wizard weekly. karakuri proved the charter-clean shape for automating it; tedai lifts exactly
that gate system from the web-service layer to the **OS layer**. The name **手代 (tedai)** is the
Edo merchant-house clerk who operates the house's affairs *on the master's instruction and under the
master's seal* — member-principal by etymology.

A literal computer-use clone would import a worse violation set than the web case, because the
desktop is where the person *lives*:

1. **Surveillance shape (bossware).** A generic "watch the screen and act" agent is one config flag
   away from employee monitoring, parental stalkerware, or partner surveillance. The screen also
   shows *other people* (video calls, shared screens) who never consented.
2. **Screenshot exfiltration.** Commercial computer-use agents ship every screenshot to a cloud
   model. The member's screen is the most PII-dense surface they own; frames must never leave the
   device (this is also exactly the baien edge-target invariant's home turf, ADR-2605241900, and
   manako's on-device-only precedent, ADR-2606034800).
3. **Detection-evasion.** Synthetic input that defeats anti-cheat, DRM, or bot-detection is the
   desktop analogue of karakuri's N2 — and a RAT/botnet is the desktop analogue of the scraper.
4. **Server-held device control.** A vendor that can inject input into your machine holds a
   platform key over your life. Pairing keys must be member-held (ADR-2605231525) and every
   mutating actuation member-signed.

**Why a new actor instead of a karakuri "T2.5 desktop adapter" (the considered alternative):**
karakuri's identity, registry axis, and gate G2 are all *service-ToS*-shaped (a vendor's published
API + its automation stance). The desktop has no vendor ToS axis; its gating axes are **device
consent, surveillance boundaries, and input-injection risk** — different registry, different
forbidden-verb sets, different evidence rules. Folding both into one actor would blur the two
threat models; keeping them siblings with the same vocabulary pattern (`ServiceOp` ↔ `DesktopOp`)
keeps each gate sharp. The browser surface stays karakuri's: tedai's registry routes browser apps
to karakuri by construction.

# Decision

Create **tedai (手代)**, a Tier-B R0 actor at `did:web:etzhayyim.com:actor:tedai` — the
**member-computer-operation** actor: karakuri's OS-layer sibling (web-service : karakuri =
computer : tedai = robot body : tazuna).

**Mission.** Give a member a uniform, auditable command vocabulary over their **own computer** —
desktop apps, files, OS surfaces — driving the safest available automation surface, with all vision
inference **on-device/LAN only**, every operation a kotoba Datom, and actuation gated behind member
signature + Council.

**The uniform vocabulary — `DesktopOp`** (the sumitsubo `ModelOp` / karakuri `ServiceOp` pattern,
one vocab across runtimes): `app` · `noun` · `verb` · classified **safety**
(`:read` / `:create` / `:update` / `:delete` / **`:outward`**) + a `destructive` flag + the selected
adapter `tier`. The fifth safety class `:outward` is new at the OS layer: a verb whose effect
**leaves the device** (send / post / pay / purchase / share / upload) is gated harder than a local
mutation, because the desktop is where local edits and world-facing acts share one keyboard.
A CLI string `tedai <app> <noun>.<verb> [--flags]` parses into exactly one `DesktopOp`.

**Three adapter tiers (safest-first, per app):**

- **T1 scripting / accessibility-API adapter** *(preferred)* — the OS's official automation
  surface: macOS AppleScript/JXA + AXUIElement, Windows UI Automation, Linux AT-SPI2/D-Bus, or the
  app's own CLI. Deterministic, semantic (no pixel guessing), OS-sanctioned, permission-dialog
  mediated.
- **T2 vision-pointer adapter (computer-use)** — screenshot → locate → click/type, **only when the
  app exposes no usable T1 surface AND its automation stance permits synthetic input** (G2). The
  vision model runs **on-device or LAN-Murakumo only** (G4); frames never leave the device.
- **T3 file-level adapter** — operate on the app's documents/files directly (the data-portability
  leg; many "GUI tasks" are really file transforms).

**Per-app capability + stance registry** (`data/app-registry.kotoba.edn`, `:representative`): each
app records its T1 automation surface, its **synthetic-input stance**
(`:permitted` / `:restricted` / `:prohibited` — anti-cheat games, DRM players, and apps whose terms
forbid synthetic input are `:prohibited` and refuse T2 by construction, even where T2 would work),
and a `:route` field — **browser apps route to karakuri** (the web surface is karakuri's; tedai
refuses to re-implement it). Missing stance defaults to `:prohibited` (default-deny input
injection).

**Cells (5; langgraph → WASM; Murakumo-only; `.solve()` raises at R0):**
`app_resolve` (dan) · `intent_plan` (naphtali) · **`pairing_broker`** (gad — member-keyless device
pairing) · `actuate_invoke` (asher) · `evidence_audit` (joseph).

**Gates (immutable R0→R3):**

- **G1 member-principal / own-device-only** *(defining)* — tedai operates **only** a device the
  member owns and has **physically paired** (consent ceremony, member-held pairing key); **no**
  third-party device control, no remote-admin-of-others, no fleet-of-other-people's-machines.
  Structurally not a RAT.
- **G2 T1-preferred / stance-honest** *(defining)* — prefer the OS's official automation surface;
  T2 vision-pointer only where the app's synthetic-input stance permits; **no detection-evasion**
  (no anti-cheat bypass, no DRM circumvention, no input-spoofing to defeat bot-detection, no
  driver-level input forgery). A `:prohibited` stance refuses T2 by construction.
- **G3 no-server-key** — pairing keys and device sessions are member-held, encrypted
  (`com.etzhayyim.encrypted.*`, ADR-2605181100), never platform-held; every mutating actuation is
  authorized by a **member signature**; a server signature is refused (ADR-2605231525).
- **G4 murakumo-only / on-device-vision** — NL → plan via LiteLLM `127.0.0.1:4000` only
  (ADR-2605215000); T2 vision inference **on-device (baien edge, ADR-2605241900) or LAN Murakumo**;
  **a screenshot never leaves the device** — cloud computer-use APIs are structurally
  unrepresentable.
- **G5 read-default / mutate-gated** — `:read` ops ship at R0 (plan only); `:create` / `:update` /
  destructive `:delete` require member-sig + explicit dry-run confirm; **`:outward`** ops (send /
  pay / post / upload) additionally require the outward gate.
- **G6 actuation-gated** — **any** live input injection (click, keystroke, file mutation) is
  Council Lv6+ + operator gated; R0 = offline parse / plan / dry-run only.
- **G7 kotoba-EAVT audit** — every planned and executed `DesktopOp` is a Datom (`as-of`,
  replayable); the member can audit exactly what touched their machine.
- **G8 no-surveillance** — screen observation is consent-scoped to the member's **own** session for
  the **duration of an op**; no ambient watching, no idle/presence monitoring, no keylogging, no
  camera/microphone capture, no observation of other persons (a frame containing a video call is
  not retained); **never** an employee-monitoring / parental-stalkerware / partner-surveillance
  product. Extends manako's on-device no-biometric precedent (ADR-2606034800).
- **G9 evidence-minimization** — the audit trail stores **hashes and structured summaries of
  evidence, never raw frames**; raw screenshots live on-device under the member's key and expire;
  flag keys (never values) are serialized into the Datom log.

**Non-goals:** N1 not bossware / employee-monitoring / parental-stalkerware / partner-surveillance
· N2 no anti-cheat / DRM / bot-detection evasion or driver-level input forgery · N3 not a RAT /
botnet — no control of any unpaired or third-party device · N4 no keylogging or credential
harvesting (of anyone, including the member — credentials are typed by the member, never by tedai)
· N5 not a click-farm / ad-fraud / fake-engagement / mass-automation engine · N6 no driving of
prohibited-content systems (Charter-Rider §2, ADR-2605192200) · N7 not a browser-automation tool —
browser surfaces route to karakuri.

**Empirical artifact (R0, all stdlib, no network, tests green):** `methods/desktop.py` — the
`DesktopOp` parser/planner: parses `tedai <app> <noun>.<verb> [--flags]`, resolves the app against
the `:representative` registry, classifies safety incl. `:outward`, selects the tier (T1-first),
enforces the **stance gate** (T2 on a `:prohibited` app refused by construction, G2), the **mutate
gate** (G5), the **outward gate** (G5), and the **karakuri route** (N7); emits a dry-run plan only
(G6). `methods/t2_vision.py` — the T2 computer-use plan builder where **surveillance verbs**
(keylog / capture-camera / watch-user / exfiltrate-screen, G8) and **evasion verbs** (anti-cheat /
DRM / detection bypass, G2) are **structurally unrepresentable** (constructing a step raises);
every plan begins by attaching the member's own pairing grant (G1/G3) and screenshots are
hash-evidenced only (G9). `methods/actuate_live.py` — the single live-actuation membrane: refuses
unless env flag + operator + Council Lv6+ + member-sig are all present, and at R0 raises
`NotImplementedError` even then. `methods/datom.py` — the G7/G9 kotoba audit projector
(deterministic, no clock reads, live ingest operator-gated). All five cells' state machines are
pure and unit-tested; `.solve()` raises until a Council activation ADR.

# Consequences

**Positive.** Closes the computer-operation gap in the roster with the same charter-clean inversion
karakuri proved for the web: members get an auditable, scriptable, member-signed handle over their
own desktop toil, and the surveillance / exfiltration / RAT failure modes of commercial computer-use
are excluded *by construction*, not by policy. The on-device-vision rule composes with the baien
edge invariant (a ≤2GB edge model is exactly the T2 vision engine this design wants) and with
manako (browser-local detection) as the perception substrate. The karakuri route keeps one owner
per surface.

**Negative / risk.** R0 ships no live actuation (plan/dry-run only) — real desktop automation needs
operator + Council action (G6) plus an R1 driver layer (OS accessibility permissions, input APIs)
that is genuinely hard to build well. The app registry is a bounded `:representative` subset; T2 on
GUI churn is fragile (same as karakuri's T2). The stance registry must be operator-maintained; a
stale `:permitted` could mis-route. G8's "no other persons in retained frames" needs a real
on-device redaction pass at R1 — at R0 it is enforced by not retaining frames at all. The
member-principal + no-server-key stance means tedai can never "just do it" unattended from a server;
that friction is intentional.

# Alternatives Considered

1. **Extend karakuri with a "T2.5 desktop adapter".** Rejected — different threat model (vendor-ToS
   vs device-consent/surveillance/input-injection), different registry axis, different forbidden
   verbs. Siblings with a shared vocabulary pattern beat one blurred actor. (This was the live
   design question; resolved here.)
2. **Clone commercial computer-use (cloud screenshots, generic remote control).** Rejected — imports
   the four violations in Context (bossware shape, frame exfiltration, evasion, server-held device
   control). tedai is the inversion.
3. **Vision-first (always T2).** Rejected — the OS ships official, deterministic automation surfaces
   (AppleScript/AX, UIA, AT-SPI) that are safer, faster, and permission-mediated; pixels are the
   last resort, exactly as browser T2 is in karakuri.
4. **Fold into tazuna (teleoperation).** Rejected — tazuna's domain is robot bodies under
   Transparent-Force constraints; a member's laptop is not a force surface and needs the
   surveillance gate set instead. The LfD/teleop substrate may later be *reused* for R1 input
   drivers.
5. **Server-held device agent for unattended convenience.** Rejected — violates G3 /
   ADR-2605231525; the member holds the pairing key and signs each mutation.

# References

- ADR-2606039200 — karakuri web-service-to-CLI (the gate system this ADR lifts to the OS layer)
- ADR-2605231525 — no platform-held signing key (G3)
- ADR-2605215000 — Murakumo-only inference (G4)
- ADR-2605241900 — baien edge-target invariant (G4 on-device vision engine)
- ADR-2605181100 — `com.etzhayyim.encrypted.*` envelope (G3 pairing grants, G9 evidence)
- ADR-2605192200 — Apache-2.0 + Charter-Rider §2 (N6 prohibited-use scan)
- ADR-2606034800 — manako browser-local vision (on-device-only / no-biometric precedent for G8)
- ADR-2606042100 — tazuna remote-robotics teleoperation (the sibling boundary in Alternative 4)
- ADR-2606033600 — sumitsubo `ModelOp` (the one-vocab pattern, mirrored as `DesktopOp`)
- ADR-2605302130 — himotoki own-data-only (G1 member-principal prior art)
- ADR-2606013800 — actor profile + dynamic did.json (apex Worker issues `did:web:…:tedai`)
