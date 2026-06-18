---
id: adr-2606161700-multigenerational-extraction-risk-gate
title: "ADR-2606161700: Multi-generational (子・孫) × Wellbecoming risk-assessment axis for resource extraction — reframing the blanket mining ban (Charter Rider §2(l)) as a multi-gen harm gate; Rider v3.2"
status: accepted
doc_type: adr
topic: multigenerational-extraction-risk-gate
authoritative: true
last_verified: 2026-06-16
priority: 9.0
axis: charter
weight: 0.90
priority_note: "Tier-1 derived-policy amendment (Charter Rider §2(l)); ratified by founder/Council Lv7+ unanimity (1/1) with priority-conformance attestation per Rider §0."
authoritative_for:
  - canonical framing of resource extraction / mining under the Charter (risk-gate, NOT blanket ban)
  - Charter Compliance Rider §2(l) reframe + version bump to v3.2
  - the multi-generational (子・孫) × wellbecoming risk-assessment axis as the test for extractive activity
  - kanayama N1 reframe (recycling-first by preference, not extraction-forbidden by constitution)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2606062100-charter-priority-over-specifics-3-tier
  - adr-2606082400-charter-rider-reciprocity-axis-v3-1
  - adr-2605252400-kanayama-circular-metallurgy-r0
  - adr-2606051500-kamado-closed-loop-carbon-refining
related:
  - adr-2606073100-abaki-anti-monopoly-intelligence-membrane-r0
supersedes: []
superseded_by: []
---

# ADR-2606161700: Multi-generational (子・孫) × Wellbecoming risk-assessment axis for resource extraction

**Status**: accepted (RATIFIED 2026-06-16, founder/Council Lv7+ unanimity 1/1)
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki (founder = Council Lv7+, 1/1)
**Charter layer**: Tier-1 Derived Policy amendment (Charter Compliance Rider §2(l)) + canonical-framing decision. Amends a Rider §2 category, which per Rider §0 + §6 requires Council Lv7+ unanimity plus a priority-conformance attestation. Both supplied below (§Decision.5).

# Context

The founder has repeatedly stated the constitutional intent, and it had drifted in the text:

> 採掘や採油を禁止しているのではなくて、多世代にわたって問題のある活動を禁止したいだけ。
> 単なる禁止ではなく、Wellbecoming・孫・子供への risk 評価を軸にしてほしい。

The Charter itself already encodes exactly this axis for most concerns:

- **Tier-0 priority** (ADR-2606062100 §1): dynamic *wellbecoming* over static wellbeing; **multi-generational descendants (子・孫 and beyond)** over the present generation. These are the constitution proper (fork-only).
- **「固定するのは掟ではなく priority」** (ADR-2606062100): the immutable thing is the *priority*, not a fixed list of forbidden industries.
- **Rider §2(d)** (IRREVERSIBLE MULTI-GENERATIONAL ENVIRONMENTAL HARM) was deliberately reframed in v3.0 away from the v2.0 "new fossil-fuel extraction" *blanket ban* into a **measured-instance** test: "Fossil-fuel combustion is ONE MEASURED INSTANCE, assessed by carbon balance … NOT by industry name or political slogan."
- **Rider §2(f)** carries the same "persons born at least 25 years hence / irreversible loss" multi-generational standard for knowledge/genetic/decision-making harm.

**The defect.** Rider §2(l) ("MONOPOLISTIC RESOURCE EXTRACTION / MINING", added in v3.0) is the one clause that *contradicts* this axis. Its text — "Operation of commercial mining or extraction of rare metals and other geologically restricted resources … This prohibition is structural" — is a **by-industry-name blanket ban**, the very framing v3.0 had already rejected for fossil fuels in §2(d). It over-prohibits (forbids reversible, well-stewarded, non-monopolistic recovery that descendants will actually need for renewable build-out, recycling feedstock, and substrate sovereignty) and under-reasons (bans by the word "mining" rather than by measured harm to 子孫).

This drift had also propagated into downstream actor text:
- `kanayama` (金山) frames primary mining as a **"constitutional N1 — recycling-only invariant"** in its ADR-2605252400 §5, CLAUDE.md, README, and both manifests.
- root `CLAUDE.md` records **"mining N1-excluded"** in the tazuna survey row.
- `rare-earth-coverage` (an *observation watcher*, not an extractor) lacked the explicit risk-axis framing for what it is actually for.

This ADR realigns the text with the standing constitutional intent: **extraction is gated by multi-generational risk, not banned by name.**

# Decision

## 1. Canonical framing (the rule)

Resource extraction — mining (incl. gold 金 / silver 銀 / rare metals レアメタル / rare earths レアアース / critical minerals), drilling, and the like — is **NOT prohibited as such** under the Charter. It is **gated by a multi-generational (子・孫 and beyond) × Wellbecoming risk assessment**, using the SAME standard already established in Rider §2(d)/§2(f):

> An extractive activity is prohibited when its foreseeable expected impact — assessed by the prudent **multi-generational steward**, not the present-quarter shareholder — includes (i) **irreversible** harm to the habitable environment / biosphere of persons born at least **twenty-five (25) years hence**, or (ii) the entrenchment of a **resource monopoly / chokepoint dependency** that subordinates descendants' wellbecoming to a present controller's rent.

Otherwise — when reversible, well-stewarded, remediated, and non-monopolistic — extraction is **permitted** (subject to its own actor ADR + the ordinary Rider §2(a)–(k) clearances). A by-industry-name ban is explicitly NOT the rule; the **harm-to-子孫 assessment is the rule**. This is symmetric with how §2(d) already treats fossil fuels (measured by carbon balance, not by slogan).

This framing is the canonical reading wherever Charter text, an actor, or a doc previously implied "mining is forbidden."

## 2. Charter Compliance Rider §2(l) reframe → **v3.2**

Rider §2(l) is rewritten from the v3.0 blanket "commercial mining" ban to the multi-generational risk-gate (full text applied in `/CHARTER-RIDER.md`). The Rider header is bumped **v3.1 → v3.2 (Last revised 2026-06-16)**; every other clause is byte-identical to v3.1. The reframe keeps the two genuinely-prohibited cores — (i) irreversible multi-gen environmental harm (already the §2(d) standard) and (ii) monopolistic/chokepoint entrenchment (the §1.12 anti-monopoly concern, the legitimate kernel of the old §2(l)) — and drops the over-broad "mining as such" prohibition.

## 3. kanayama (金山) N1 reframe

`kanayama` remains, **by design preference**, a recycling-first / urban-mining actor — because closed-loop Al recovery at ~5% of primary Hall-Héroult energy is the largest materials-layer wellbecoming win available, NOT because primary extraction is constitutionally forbidden. Its N1 is reframed from a constitutional **"recycling-only invariant / mining excluded (immutable)"** to a **scope boundary**:

> N1 — Primary mining is **out of kanayama's R0–R3 scope** (kanayama is the recovery/recycling actor). It is **not constitutionally forbidden**: any primary-extraction capability must be proposed as its OWN actor/ADR and must pass the multi-generational (子・孫) × wellbecoming risk gate (ADR-2606161700 §1) — preferring, where the assessment is close, the lower-risk recovery path kanayama already provides.

The "IMMUTABLE R0–R3" stamp on N1 is relaxed accordingly (the *gate* is the invariant, kanayama's recovery-first *scope* is a design choice). N2–N8 are unchanged (they are independent concerns: primary-smelting energy, war contamination, radiological, NDA secrecy, WEEE, deep-sea-habitat, conflict-mineral attestation — several of these are themselves multi-gen-harm or §2 instances and stand on their own).

## 4. rare-earth-coverage watcher — risk-axis as analytical core

`rare-earth-coverage` is an **observation watcher** (a supply-chain / dependency KG mirror, sibling of the kabuto / tsumugi / inochi observatory lineage), not an extractor. It carries the multi-generational × wellbecoming risk-assessment axis as its **analytical core**: it maps where rare-metal value chains create **chokepoint / monopoly dependency** and **multi-gen environmental risk**, routed to **resilience / de-monopolization / restoration** — never a target-list, never an extraction recipe. This intent is recorded in the actor (CLAUDE.md + a `riskAssessmentAxis` block on the manifest).

## 5. Priority-conformance attestation (Rider §0 / §6 requirement)

This amendment **serves the Tier-0 multi-generational priority at least as well as the text it replaces** — the §0 test for amending a §2 category:

- The blanket "mining as such" ban is a **crude proxy** for the real priority. It simultaneously **over-prohibits** (forbidding reversible, stewarded, non-monopolistic recovery that 子孫 need for renewables, batteries, and substrate sovereignty) and **under-reasons** (judging by an industry's *name* rather than by its *measured impact on descendants*).
- The risk-gate ties the prohibition **directly** to the Tier-0 priority (irreversible harm to persons ≥25 yr hence; monopoly that mortgages descendants' wellbecoming), exactly as §2(d) already does for carbon. It can prohibit *more* precisely (a genuinely catastrophic or monopolistic extraction is still caught) while permitting the stewarded paths the priority actually wants.
- It is therefore **never weaker** on the priority; it is strictly better-aimed.

**Ratification**: founder = Council Lv7+, unanimity 1/1, 2026-06-16. (Bootstrap-Council operational premise: Council attestation = PR review; this ADR's merge commit / PR is the attestation record.)

# Consequences

**Positive**
- The Charter text now matches the standing constitutional intent: 禁止リストではなく多世代リスク評価軸.
- §2(l) is consistent with §2(d)/§2(f) (one coherent "measured multi-gen harm, not slogan" doctrine across environment, knowledge/genetics, and resources).
- Future extraction actors (should any be proposed) have a clear, principled gate to pass rather than a flat wall — and the recovery-first preference (kanayama) is preserved as the lower-risk default.
- `rare-earth-coverage` gains an explicit analytical telos.

**Negative / risks**
- "Multi-generational risk assessment" is a judgment standard, not a bright line; it can be gamed by optimistic foreseeability claims. Mitigation: the standard is explicitly the *prudent multi-generational steward* (not present-quarter shareholder), assessments are Council-attested + plaintext-public on kotoba (相互監視), and the §2(d) carbon-balance instance shows the measured-test pattern.
- The kotoba submodule's vendored `40-engine/kotoba/CHARTER-RIDER.md` is still at v2.0 (predates §2(l) entirely) and is out of scope for this ADR (separate repo; tracked for a future submodule rider-sync).

**Non-changes (deliberately untouched)**
- `sarutahiko`'s "mining-haul trucks" non-goal stays: that is a *scope + Reformed-Just-War / no-unmanned-military* concern about building giant haul/▮military vehicles, not a statement that extraction is forbidden. Reframing it here would be scope creep.
- N2–N8 of kanayama, and §2(a)–(k) of the Rider, are unchanged.

# Alternatives Considered

1. **Leave §2(l) as a blanket ban, add a footnote.** Rejected: the contradiction with §2(d) and with the Tier-0 "priority not 掟" doctrine is in the *normative* text; a footnote would not fix the controlling clause or the downstream actor framing.
2. **Delete §2(l) entirely** (rely on §2(d) + §1.12). Rejected: §2(l) usefully *names* the resource-extraction case and the monopoly/chokepoint kernel that §2(d) (environmental) does not squarely cover. Reframing > deleting.
3. **Reframe only the watcher + kanayama, leave the Rider.** Rejected: the user chose "ADR + 全箇所修正"; the Rider is the source of truth — fixing only downstream leaves the controlling clause wrong.

# References

- ADR-2605192100 — etzhayyim Mission Charter (§1.9 multi-gen, §1.12 anti-monopoly)
- ADR-2605192200 — IP-Free-Release Charter Rider (Rider 正本)
- ADR-2606062100 — Charter priority-over-specifics 3-Tier (「固定するのは掟ではなく priority」; v3.0)
- ADR-2606082400 — Rider reciprocity-axis v3.1
- ADR-2605252400 — kanayama circular metallurgy R0 (N1 reframed by this ADR §3)
- ADR-2606051500 — kamado closed-loop carbon refining (the §2(d) measured-instance precedent for extraction-by-balance)
- ADR-2606073100 — abaki anti-monopoly intelligence membrane (route-around, not punishment)
- `/CHARTER-RIDER.md` — Rider v3.2 (this ADR applies §2(l))
