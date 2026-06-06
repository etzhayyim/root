---
id: adr-2606064500-charter-principle-derivation-layering
title: "ADR-2606064500: Charter Principle/Derivation Layering — axioms vs derived doctrines vs implementation"
status: proposed
doc_type: adr
topic: charter-principle-derivation-layering
authoritative: true
last_verified: 2026-06-06
priority: 9.0
axis: governance
weight: 0.90
priority_note: "Constitutional meta-structure; ratification gated Council Lv7+ (touches amendment gates)."
authoritative_for:
  - charter-layer-taxonomy
  - principle-vs-derivation-classification
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605252300-charter-preamble-kingdom-of-god
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606064500: Charter Principle/Derivation Layering — axioms vs derived doctrines vs implementation

**Status**: proposed (Council Lv7+ ratification — touches the amendment-gate structure of the constitution)
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

The constitutional corpus today is **flat**: the Mission Charter (ADR-2605192100 §1.1–§1.16)
and the Charter Compliance Rider (CHARTER-RIDER.md §2(a)–§2(i)) are all referred to,
loosely, as "constitutional invariants." CLAUDE.md states that "the 8 prohibited categories
(§2(a)-(h)) … are constitutional invariants per ADR-2605192200 v2.0."

This flatness conflates three different kinds of statement and has produced concrete
category errors:

1. **A specific prohibited *case* is treated as if it were a first principle.** "Negation
   of surveillance capitalism" (§2(c)) is **not** an axiom — it is a *derivation*: it
   follows from the Wellbecoming axiom (cognitive sovereignty, §1.10) and the
   anti-individualist axiom (a person is not a commodifiable data-unit, §1.8). Several
   Rider clauses literally *are* the negation of a §1 axiom — §2(f) of §1.9, §2(g) of §1.8,
   §2(h) of §1.10 — and even cite that axiom in their own text. Treating the derivation as
   primitive hides the axiom and freezes a domain-specific application at the same
   amendment gate (Lv7+ unanimity) as the religious axiom it descends from.

2. **A pure *implementation* rule sits in the constitutional list.** §2(i) (religious-corp
   inference must run on the Murakumo fleet; RunPod/Vertex/Bedrock/etc. prohibited) is an
   **operational mechanism**, not a principle. The principle is A6 (no commercial
   extraction) + sovereignty; "which GPU backend" is infrastructure that will change as the
   fleet evolves. Yet it lives beside genuine axioms and even carries its own pending
   amendment process.

3. **An operator changing a *technical* mechanism is mistaken for amending the
   constitution.** The apex `/actors` page ships CSP `default-src 'none'` with the inline
   comment "no inline script (Charter Rider §2(c))." But §2(c) prohibits the *surveillance-
   capitalism business model*, not scripting. A first-party, same-origin, zero-egress,
   cookie-free ES module (e.g. resolving content-addressed `/kotoba` blocks in the visitor's
   own browser) does not collect, broker, or sell anyone's personal data — it satisfies
   §2(c) fully. "No script" was an over-broad implementation choice mis-attributed to the
   charter; tightening the CSP to `script-src 'self'; connect-src 'self'` *strengthens* the
   §2(c) value (third-party beacons become structurally impossible) while permitting
   first-party code. This was nearly mishandled as "weakening the Charter Rider."

The defect is **level confusion**: axioms, the doctrines derived from them, and the
mechanisms that implement those doctrines are all stored at one level with one amendment
gate. The fix is to make the layering explicit.

# Decision

Adopt a **three-layer charter taxonomy**. Every normative statement in the corpus is
classified into exactly one layer, and the **amendment gate scales with the layer**.

## Layer A — 基本原則 (Axioms / the constitution proper)

The irreducible religious-metaphysical and teleological commitments. They are not derived
from anything inside the corpus; everything else is derived from them. **Amendment requires
Council Lv7+ unanimity** (the existing constitutional lock, Charter §0.1 / Preamble §0.4).

| # | Axiom | Source | Religious grounding |
|---|---|---|---|
| **A1** | **反個人主義 関係存在論** — constitutive reality is collective / relational / multi-generational; "the individual exists independently and prior to the collective" is rejected as doctrine (the biological individual is not denied). | §1.8 | Tree of Life 互根性 (עץ חיים) · 縁起 pratītyasamutpāda · 産霊 musuhi · Ubuntu |
| **A2** | **多世代 standing** — the unit of moral/economic standing is the multi-generational collective; descendants (子・孫), including the not-yet-born, hold standing now. | §1.9 | entailed by A1 (the collective is multi-generational) · tikkun olam |
| **A3** | **Wellbecoming** — value is the *developmental trajectory*, not a static end-state; there is no terminal/eschatological state to optimise toward (非終末論). | §1.10, §1.15 | 修 shu · 雅歌 generativity · 黙示録 non-canonical |
| **A4** | **生圏帰属 / Tree of Life** — land and biosphere belong to life (生), not to states or persons. | §1.11 | 八百万 immanence · Tree of Life cosmology |
| **A5** | **労働解放 telos** — the final purpose is the structural liberation of humanity from "labor." | §1.0, §1.4 | the mission itself |
| **A6** | **非営利・献金のみ・payoff帰属=etzhayyim** — non-commercial; donation-only inflow; no profit-extraction; ownership/decision-rights are etzhayyim's. | ADR-2605192115 | 無教会 · 万人祭司 · waqf-equivalence |
| **A7** | **宗教的系譜 synthesis** — Japanese substrate (八百万 / 縁起 / 産霊 / 和 / 無教会) + Protestant Christianity (Sola Scriptura / 万人祭司 / Reformed Just War / Tree of Life); non-eschatological. | §1.14, §1.15 | the interpretive substrate that licenses every derivation |

A2 and A3 are tightly *entailed* by A1 but are stated as co-axioms because they carry
independent religious weight; A1 is the metaphysical root.

## Layer B — 導出教義 (Derived doctrines)

Domain applications of Layer A to economics, society, force, and expression. **Each Layer-B
statement MUST cite the Layer-A axiom(s) it derives from.** A Layer-B doctrine is **binding**
but **not primitive**: it may be **re-derived, refined, narrowed, or extended** as conditions
change, and new derived doctrines may be added, **provided the derivation from Layer A is
preserved and stated**. **Amendment gate: Council Lv6+ supermajority + a public objection
period** (the process already used for the §2(i) carve-out, ADR-2605262200) — *not* Lv7+
unanimity, because amending a derivation is not amending an axiom.

Existing Mission-Charter program clauses (§1.1 Basic Income, §1.2 collective asset, §1.3
energy, §1.4 robotics, §1.5 free-IP, §1.6 disintermediation, §1.7 anti-gatekeeping, §1.12
Transparent Force, §1.13 Eros/Gore) are Layer B, as are **all eight Rider prohibitions
§2(a)–§2(h)**. Their content is unchanged; only their *status* (derived, not axiomatic) and
their *gate* (Lv6+, not Lv7+) change.

## Layer C — 実装・運用規則 (Implementation / operational rules)

The concrete mechanisms that *satisfy* a Layer-B doctrine: protocols, CSP strings, lint
hooks, backend allow-lists, file formats, node addresses. **Not constitutional.** Changeable
by maintainers/operators **without a Council vote**, provided the change *provably still
satisfies its parent Layer-B doctrine* (and, transitively, Layer A). A Layer-C rule names its
parent; if a mechanism no longer serves its parent, it is replaced, not voted on.

Layer C includes: §2(i) (Murakumo-only inference + the specific prohibited-backend list),
the `/actors` CSP, the `no-cookie` lint hook, Murakumo node addresses, GPU model choices,
the `e7m verify` invariant *mechanisms* (the *values* they protect are Layer A/B).

## Derivation map (normative core of this ADR)

| Clause | Layer | Derives from | Note |
|---|---|---|---|
| §1.8 anti-individualism | **A1** | — | axiom |
| §1.9 multi-generational | **A2** | A1 | axiom |
| §1.10 Wellbecoming / §1.15 non-eschatology | **A3** | A1 | axiom |
| §1.11 land / Tree of Life | **A4** | A7 | axiom |
| §1.4/§1.0 labor liberation | **A5** | A1, A2 | axiom |
| non-profit / donation-only | **A6** | A1, A5 | axiom |
| §1.14 lineage synthesis | **A7** | — | axiom |
| §1.1 Basic Income | B | A5, A6, A2 | derived program |
| §1.5 free-IP release | B | A5, A7 (万人祭司) | derived program |
| §1.6 disintermediation · §1.7 anti-gatekeeping | B | A5, A6 | derived program |
| §1.12 Transparent Force | B | A1, A7 (Reformed Just War), A3 | derived program |
| §1.13 Eros 許容 / Gore 禁止 | B | A3, A2, A4 (産霊/雅歌) | derived program |
| §2(a) weapons / military | B | §1.12 ⇒ A1, A7 | only Transparent Force; covert/proprietary prohibited |
| §2(b) speculative finance | B | A6, §1.6 | anti-extraction |
| §2(c) **surveillance capitalism** | B | A3 (cognitive sovereignty), A1 (anti-commodification), A2 | **the trigger case** |
| §2(d) fossil-fuel extraction | B | A2, A4 | geological stock→flow, irreversible |
| §2(e) specialist gatekeeping | B | §1.7 ⇒ A5, A6 | near-restatement of §1.7 |
| §2(f) multi-generational harm | B | A2 | **direct negation of A2** |
| §2(g) strict individualist ontology | B | A1 | **direct negation of A1** (cites it in-text) |
| §2(h) Wellbecoming subordination | B | A3 | **direct negation of A3** (cites it in-text) |
| §2(i) commercial-GPU prohibition | **C** | A6 + sovereignty | mechanism (Murakumo-only); backend list is operational |
| `/actors` CSP `script-src/connect-src 'self'` | **C** | §2(c) ⇒ A3 | first-party code OK; third-party egress impossible |
| `no-cookie` lint · `e7m verify` mechanisms | **C** | §2(c), various B | mechanisms protecting B/A values |

## Governance consequence (summary)

| Layer | What | Amendment gate |
|---|---|---|
| **A** 基本原則 | religious axioms (A1–A7) | **Council Lv7+ unanimity** |
| **B** 導出教義 | derived doctrines, incl. §2(a)–§2(h) | **Council Lv6+ supermajority + public objection period**, derivation-from-A preserved |
| **C** 実装規則 | mechanisms (CSP, backend lists, hooks) | **operator/maintainer**, must provably satisfy its parent B |

# Consequences

**Positive**
- The constitution is small and legible: 7 axioms, not ~25 flat invariants.
- Domain prohibitions can track a changing world (new harms ⇒ new Layer-B derivations at the
  Lv6+ gate) without re-opening the religious axioms.
- Technical decisions (CSP, GPU backend, file format) stop masquerading as constitutional
  amendments — they are Layer C, changed by whoever maintains the mechanism, judged solely by
  "does it still satisfy its parent doctrine?"
- Every prohibition becomes *auditable against its axiom*: if a Layer-B rule cannot be derived
  from Layer A, it is mis-placed and subject to removal — a guard against constitutional creep.

**Costs / risks**
- This ADR is itself a **constitutional meta-change** (it redefines amendment gates), so it is
  **proposed, pending Council Lv7+ ratification**. Until ratified, the flat treatment in
  CLAUDE.md / ADR-2605192200 remains binding and every §2 clause keeps its current (Lv7+)
  status.
- **Content-preserving**: this ADR changes *no rule's meaning*. §2(a)–§2(h) remain fully
  binding; only their classification (derived, not axiomatic) and gate (Lv6+, not Lv7+) move.
- Re-classifying §2(i) and the CSP/lint rules to Layer C means an operator can change them
  without a vote — acceptable *only* because Layer C is constrained by the explicit "must
  provably satisfy its parent B" test, which is itself auditable by `e7m verify` /
  charter-rider-applicator.

# Non-goals / invariants preserved

- **N1** — does NOT weaken any §2(a)–§2(h) prohibition; all remain binding (content-preserving
  reclassification only).
- **N2** — does NOT touch Layer-A axioms; A1–A7 keep the Lv7+ unanimity lock.
- **N3** — does NOT authorise surveillance/trackers/cookies/PII-brokerage. The §2(c) *value*
  (A3 cognitive sovereignty + A1 anti-commodification) is reaffirmed; only the *mechanism*
  layer is freed (first-party, zero-egress code is permitted; third-party data extraction
  remains prohibited).
- **N4** — does NOT change the Murakumo-only inference invariant's *effect*; it reclassifies
  the *mechanism* (which backends) as Layer C while its *value* (A6 no-commercial-extraction)
  stays Layer A.

# Follow-ups (post-ratification)

1. Annotate CHARTER-RIDER.md §2(a)–§2(i) with a `derives-from:` line each (Layer-B/C tag +
   parent axiom), per the derivation map above.
2. Update CLAUDE.md "§2 are constitutional invariants" wording to "§2 are Layer-B derived
   doctrines (binding; Lv6+ gate)."
3. Extend `e7m verify` with a **derivation-integrity** check: every Layer-B/C rule must name a
   reachable Layer-A parent; an orphan rule fails the check.
4. Adopt a `layer:` + `derives-from:` field convention in future Rider/charter clauses so the
   taxonomy is machine-checkable from authoring time.
