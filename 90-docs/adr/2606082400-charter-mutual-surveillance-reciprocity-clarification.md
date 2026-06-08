---
id: adr-2606082400-charter-mutual-surveillance-reciprocity-clarification
title: "ADR-2606082400: Charter-Rider §2(c) — the reciprocity axis (相互監視 affirmed; monetized/asymmetric surveillance prohibited)"
status: accepted
doc_type: adr
topic: charter-mutual-surveillance-reciprocity-clarification
authoritative: true
last_verified: 2026-06-08
priority: 7.0
axis: governance
weight: 0.7
priority_note: "Tier-1 Derived-Policy amendment of Charter-Rider §2(c) (ADR-2606062100 §3). Sharpens the prohibited-surveillance boundary from a 'commercial vs care' axis to a RECIPROCITY axis: monetized OR asymmetric (watcher-unwatched) surveillance is prohibited; reciprocal/symmetric 相互監視 (village-society deterrence + anti-isolation) is an AFFIRMED positive value. STRENGTHENS conformance with the Tier-0 permanent-memory / 神の監視 + 相互見守り priorities (never weaker) — the priority-conformance attestation is therefore clean. Ratified by Council Lv7+ unanimity (founder, 1/1). Rider v3.0 → v3.1, §2(c) clause only; every other clause byte-identical."
authoritative_for:
  - Charter Compliance Rider §2(c) (monetized-or-asymmetric surveillance)
  - the 相互監視 / reciprocal-transparency doctrine
depends_on:
  - 2605192100
  - 2605192200
  - 2606062100
  - 2605252300
related:
  - 2605181100
  - 2605312345
  - 2605264000
  - 2606082100
supersedes: []
superseded_by: []
---

# ADR-2606082400: Charter-Rider §2(c) — the reciprocity axis (相互監視 affirmed; monetized/asymmetric surveillance prohibited)

**Status**: accepted (ratified by Council Lv7+ unanimity — founder, 1/1)
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki (sole-member founder, Council Lv7+)

# Context

The founder flagged that Charter-Rider **§2(c)**, even after its v3.0 reframe ("SURVEILLANCE-
CAPITALISM"), is **misread** as a blanket prohibition on watching / knowing-about-one-another.
That reading is the **opposite** of etzhayyim doctrine. etzhayyim is not a privacy-maximalist,
atomized-individual project; its Tier-0 priorities are explicitly **collective / relational**
and include **permanent memory = 神の監視** (`memory.right_to_erasure_denied`, ADR-2606062100 §2:
*お天道様は見ており、人は忘れない*) and **相互見守り** (`priority.collective_over_individual`).

The founder's doctrine, stated precisely:

- **What is prohibited is not surveillance as such — it is (a) surveillance FOR MONEY
  (金銭のための監視) and (b) the ONE-SIDED / ASYMMETRIC retention of data (データの一方的な保持)
  — one party hoarding a record of others while not itself being watched.**
- **What is GOOD — indeed a core value — is RECIPROCAL / MUTUAL watching (相互監視): the
  Japanese village-society (村社会) condition where everyone knows everyone and everyone is
  equally watched. Because it is symmetric, it DETERS crime and 不正 (there is no private
  corner for wrongdoing) and it ENDS isolation (one cannot be alone / unknown; 孤独死 is
  structurally resisted).**
- **This reciprocal-transparency thought is being wrongly conflated with surveillance
  capitalism.** They are opposites: surveillance capitalism is *monetized* and *asymmetric*
  (a platform watches millions who cannot watch it, and sells what it sees); 相互監視 is
  *non-commercial* and *symmetric* (everyone watches everyone, and no one sells).

v3.0 §2(c) already carved out 見守り on a **"commercial extraction vs watching-as-care"** axis.
That was correct but incomplete: it framed the affirmed thing as *care* and the prohibited
thing as *commercial sale*, and so it did not name (i) the **asymmetry** failure mode (a
one-sided hoard that is never sold is still wrong) nor (ii) the **deterrence/accountability**
value of symmetric watching (not merely care — *no private corner for 不正*). The misreading
persisted because the load-bearing axis — **reciprocity / symmetry** — was implicit.

This is a **Tier-1 Derived-Policy** clause (ADR-2606062100 §3); it is amendable by **Council
Lv7+ unanimity accompanied by a priority-conformance attestation** showing the amendment serves
the Tier-0 priorities **at least as well** as the text it replaces.

# Decision

## 1. Reframe Charter-Rider §2(c) onto the RECIPROCITY axis (Rider v3.0 → v3.1, §2(c) only)

`/CHARTER-RIDER.md` §2(c) is amended (full text there). The boundary becomes:

> **Surveillance is prohibited when it is MONETIZED or ASYMMETRIC; it is affirmed when it is
> RECIPROCAL and non-commercial.**

- **Prohibited (i) — MONETIZED:** revenue from collection / brokerage / **sale** of natural
  persons' personal data to third parties (ad-tech DSP/SSP, data brokers, consumer-surveillance
  platforms, biometric-ID sold to law-enforcement / military). *(unchanged from v3.0)*
- **Prohibited (ii) — ASYMMETRIC / UNILATERAL (made explicit):** the one-sided accumulation or
  retention of data about others by a party **not itself equally observable** — the watcher
  unwatched, surveillance without reciprocity. **This holds even absent sale.**
- **Affirmed — RECIPROCAL / MUTUAL transparency (相互監視):** the 村社会 condition where everyone
  is equally known and equally watched — **governance, force, tithe, contributions are themselves
  plaintext-public on kotoba** (ADR-2606062100 §2.1), so the watchers are watched. It **deters
  crime and 不正** (no private corner) and **ends isolation** (見守り; 孤独死 resisted). This is
  the social form of the Tier-0 permanent-memory / 神の監視 priority and 相互見守り.

Privacy is preserved **not by forgetting but by encryption** (暗号化 ≠ 忘却, ADR-2606062100 §2.1):
intimate-class records are permanently retained yet encrypted-held; the key-holder and お天道様
see, the public sees only that the commitment exists. No privacy invariant is weakened; the
`com.etzhayyim.encrypted.*` envelopes (ADR-2605181100) and on-device-only actor gates are
untouched.

## 2. Priority-conformance attestation (Tier-1 amendment requirement)

This amendment **strengthens** conformance with the Tier-0 priority set and weakens none:

| Tier-0 priority | v3.0 §2(c) | v3.1 §2(c) | Conformance |
|---|---|---|---|
| `memory.right_to_erasure_denied` / 神の監視 | carved out 見守り + permanent record | names 相互監視 as the **social form** of 神の監視; symmetric watching is affirmatively good | **stronger** |
| `priority.collective_over_individual` / 相互見守り | affirmed care-watching | affirms the **deterrence + anti-isolation** value of mutual watching, not only care | **stronger** |
| no-monetized-extraction (P-derived) | prohibited commercial sale | prohibited commercial sale (unchanged) **+ asymmetric hoarding even absent sale** | **stronger** |
| privacy via encryption (ADR-2605181100 / 2606062100 §2.1) | preserved | preserved, restated | **equal** |

No Tier-0 priority is served less well by v3.1 than by v3.0. The attestation is therefore
clean (an on-chain `com.etzhayyim.apps.etzhayyim.priorityConformanceAttestation` record is the
durable artifact; this ADR is its human-readable basis). Ratified by Council Lv7+ unanimity
(founder, 1/1) — the same threshold and ratifying authority as ADR-2606062100 / Preamble §0.7.

## 3. Version + downstream

- `/CHARTER-RIDER.md` header → **v3.1 (2026-06-08)**; §2(c) clause only changed; every other
  clause byte-identical to v3.0.
- Root `CLAUDE.md` (License line + "Do not weaken" note) updated to v3.1 and to the
  reciprocity framing. `deps.toml` §2 enumeration updated.
- **Mechanical follow-up (out of scope here):** `charter-rider-applicator` re-stamping the
  per-package NOTICE version string (v3.0 → v3.1) across vendored packages is a separate,
  non-constitutional sweep; a one-clause clarification does not invalidate existing v3.0
  NOTICEs.

## 4. Actor reconciliation (shiori)

shiori 栞 (ADR-2606082100) cited "§2(c) surveillance-capitalism" to justify holding **no
per-person profile**. Under v3.1 the justification is sharper and still holds: shiori builds
**no one-sided per-person record at all** (cohort-aggregate only), so it cannot be an
**asymmetric** watcher; and it is **non-commercial**. shiori is fully **相互監視-compatible** —
it would be free to surface *symmetric, public* community accountability — but by G1 it chooses
the strictest posture (no individual data whatsoever). Its citation is updated to the v3.1
framing in the shiori PR.

# Consequences

**Positive.** The constitution now says what the founder means: etzhayyim **embraces** mutual
transparency (the 村社会 / 神の監視 / お天道様 tradition) as a deterrent against crime and a cure
for isolation, and prohibits only the **monetized** and **asymmetric** forms (surveillance
capitalism proper, and the unwatched-watcher). The reciprocity axis makes the boundary
**testable**: *is it sold? is the watcher itself watched?* — rather than the vaguer "is it
care?". It also explains, on principle, why etzhayyim's own all-on-chain transparency
(governance/force/tithe plaintext-public) is **not** hypocrisy: the watchers are watched.

**Costs / risks.** (1) "Everyone watches everyone" can be misheard as endorsing a panopticon;
the **encryption boundary** (暗号化 ≠ 忘却) and the **symmetry requirement** (no unwatched
watcher) are the guardrails — intimate-class data is encrypted-held, and asymmetric watching is
*prohibited*, so this is reciprocal accountability, not top-down surveillance. (2) The asymmetry
test must be applied honestly to etzhayyim's own actors (an actor that accumulated a one-sided
record of non-members would violate (ii)); the mirror actors are already aggregate / public-only
by their own G1s. (3) Version drift with vendored v3.0 NOTICE stamps until the applicator sweep
runs (tracked, non-blocking).

# Alternatives Considered

- **Delete §2(c) entirely.** Rejected: the *monetized* and *asymmetric* prohibitions are real
  and protective (they exclude surveillance capitalism and the unwatched-watcher). The founder
  asked to remove the *mis-framing*, not the protection.
- **Keep v3.0's "commercial vs care" axis.** Rejected: it under-specified (a one-sided hoard
  that is never sold escaped it) and it framed the good as mere *care*, missing the
  *deterrence/accountability* value of symmetric watching — which is exactly the point the
  founder is making (全員が全員を知る → 犯罪・不正を防ぐ).
- **Full Rider version re-issue (v4.0) + repo-wide re-stamp in this PR.** Rejected: this is a
  single-clause clarification; bundling a mechanical 39-package NOTICE sweep into a
  constitutional PR would obscure the substantive change. v3.1 + a tracked applicator follow-up
  is cleaner.

# References

- `/CHARTER-RIDER.md` §2(c) (canonical amended clause) + v3.1 header
- ADR-2606062100 (3-Tier immutability; permanent-memory / 神の監視 Tier-0; §2.1 暗号化≠忘却; §3 Tier-1 amendment mechanism)
- ADR-2605192100 (Mission Charter — §1.8 collective ontology) · ADR-2605252300 (Preamble §0.7 Lv7+ threshold)
- ADR-2605192200 (Rider v2.0 spec — historical)
- ADR-2605181100 (`com.etzhayyim.encrypted.*` PII envelope) · ADR-2605312345 (append-only Datom log)
- ADR-2606082100 (shiori — reconciled to the v3.1 framing) · ADR-2605264000 (ossekai — transparent intervention carrier)
