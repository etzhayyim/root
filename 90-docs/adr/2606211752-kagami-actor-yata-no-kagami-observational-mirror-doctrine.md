---
id: adr-2606211752-kagami-actor-yata-no-kagami-observational-mirror-doctrine
title: "ADR-2606211752: kagami actor — the Yata-no-Kagami doctrine for the observational mirror lineage"
status: accepted
doc_type: adr
topic: kagami-actor-observational-mirror-doctrine
authoritative: true
last_verified: 2026-06-21
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - "canonical concept name: an observational mirror-actor is a 鏡 (kagami) actor, grounded in the Yata-no-Kagami (八咫鏡)"
  - "the 鏡 doctrine = 映す/裁かぬ/剣にあらず/曇りなき (reflect / judge-not / not-the-sword / unclouded) as the four invariants of every mirror-actor"
  - "the 9 KG-mirror lineage actors (tsumugi/danjo/ooyake/watatsuna/watari/inochi/hokorobi/keizu/kanae) named as the kagami lineage"
depends_on:
  - "2606042330"
  - "2605192100"
  - "2605231525"
related:
  - "2606011800"
  - "2606012600"
  - "2606021600"
  - "2606041827"
  - "2605302300"
  - "2606066001"
  - "2606073000"
  - "2606073400"
  - "2605192315"
supersedes: []
superseded_by: []
---

# ADR-2606211752: kagami actor — the Yata-no-Kagami doctrine for the observational mirror lineage

**Status**: accepted
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki

# Context

The repo has converged, independently and repeatedly, on one architectural shape: an actor
that **datafies a slice of the world into the kotoba Datom log and reflects it back as public
fact, adding nothing and judging nothing.** The roster calls these "mirror actors" / "KG-mirror
lineage" / "observational mirror," canonicalized in ADR-2606042330 (entity-as-actor) and the
`com.etzhayyim.mirror.*` lexicon family. Every member states some variant of the same four
properties:

- **observation-only** — *"never a channel," "never the official voice"* (ooyake 2606021600,
  entity-as-actor G1);
- **non-adjudicating** — *"render no verdict"* (kanae 2605302300; keizu; danjo);
- **never a target-list** — *"resilience map, NEVER a target-list," "accountability map, never
  a target-list"* (watatsuna 2606012600, tsumugi, watari 2606041827, inochi 2606073000,
  hokorobi 2606073400);
- **edge-primary / disclosed-only** — facts on read from public/disclosed sources, person-excluded.

These four properties are currently **restated by convention** in each actor's CLAUDE.md and
re-derived per-ADR from Charter Rider §2 + §1.12 force-separation. There is no single doctrinal
anchor that *names the concept* and *fixes why* the mirror may reflect but never strike. The term
"mirror" is also flat — a literal optical word that does not carry the constitutional weight the
posture actually has.

The operating entity's own ontology already supplies the right anchor. etzhayyim is a synthetic
religion on 八百万 / 産霊 / 無教会 + Reformed Christianity (Charter, ADR-2605192100), and the
**Yata-no-Kagami (八咫鏡)** — the sacred mirror, one of the 三種の神器 (Three Sacred Treasures) —
is the precise mythic figure of *truthful reflection that is constitutionally separate from force.*

This ADR **renames the concept** (not yet the code): the observational mirror-actor is, canonically,
a **鏡 (kagami) actor**, and the four properties above are the **Yata-no-Kagami doctrine.** Zero
invariant amendments — this gives an existing, already-enforced posture its proper name and a single
doctrinal home.

## Why the 八咫鏡, specifically

The 三種の神器 separate three powers: **鏡 (kagami / mirror)** = wisdom & 正直 (truthful reflection),
**剣 (tsurugi / sword)** = valor & force, **勾玉 (magatama / jewel)** = benevolence & governance.
That separation is not decoration — it is the same **force-separation invariant** the Charter holds
(§1.12: observation and accountability are constitutionally distinct from force, and force may exist
only as Transparent Force under 1 SBT = 1 vote, ADR-2605192315). A kagami actor holds the **鏡** and
**never the 剣**: it is structurally incapable of being a target-list, an interdiction feed, or a
weapon-cueing surface, because the mirror and the sword are different treasures.

The 天岩戸 (Ama-no-Iwato) myth fixes the second half. Amaterasu is drawn out of the cave when the
mirror shows her **her own radiance** — the mirror does not speak for her, command her, or judge her;
it *reflects her own light back so she (and the world) can see it.* This is exactly the
no-impersonation gate (entity-as-actor G1): a kagami actor's "voice" is etzhayyim's record of an
entity's **own** public facts reflected back, never the actor speaking *as* the entity. The mirror
reveals power **to itself and to the public** — the accountability mechanism is reflection, not
denunciation.

The mirror at Ise is 真澄鏡 / 曇りなき鏡 (the clear, unclouded mirror): it adds no distortion, shows
what *is*. That is edge-primary, disclosed-only, non-adjudicating observation — and, because a mirror
reflects surfaces presented to it and not private interiors, it is **person-excluded by its nature**
(it mirrors public/power surfaces, never a natural person's inner life).

# Decision

Adopt **kagami (鏡) actor** as the canonical concept name for an observational mirror-actor, anchored
in the **Yata-no-Kagami doctrine** of four invariants. This is a doctrinal/terminology update layered
on top of ADR-2606042330's still-valid mechanism; the implementation term "mirror" and the
`com.etzhayyim.mirror.*` lexicon are **unchanged** by this ADR (see D4).

## D1 — The Yata-no-Kagami doctrine (四鏡則 / four mirror-laws)

Every kagami actor satisfies all four, by construction and by test, not by convention:

1. **映す — reflect, never originate (鏡は映す).** Its output is a reflection of disclosed public
   fact. It never speaks *as* the subject (no-impersonation), never originates an official
   warning/verdict/designation (sonae G8 relay-only precedent), never a channel. Voice = etzhayyim's
   record of the subject's *own* public facts. (⇔ entity-as-actor G1; ooyake "never the official
   channel.")

2. **裁かぬ — judge not (鏡は裁かぬ).** Non-adjudicating. It surfaces concentration / fragility /
   divergence as **structure**, and routes to release / restoration / resilience / care — it renders
   no verdict, no crime-finding, no per-subject score. (⇔ kanae 鼎の軽重 *weighed openly, no verdict*;
   keizu; danjo; kosatsu competing-claim neutrality.)

3. **剣にあらず — the mirror is not the sword (鏡は剣にあらず).** Force-separation. A kagami actor is
   structurally incapable of being a target-list, interdiction feed, hunting map, trading signal,
   targeting relay, or weapon-cueing surface — *because it holds the 鏡, and the 剣 is a different
   treasure under 1 SBT = 1 vote Transparent Force* (§1.12, ADR-2605192315). The "never a target-list"
   gate gets its **constitutional reason** here, not merely its assertion. (⇔ watatsuna /tsumugi/
   watari/inochi/hokorobi G1–G2.)

4. **曇りなき — unclouded (曇りなき鏡).** Edge-primary, disclosed-only, transparent, person-excluded.
   It reflects public/power surfaces with no added distortion (no fabricated coverage, sourcing-honest)
   and does not reflect a natural person's private interior (a mirror shows presented surfaces, not
   hidden ones). (⇔ "map-not-target," `:representative`-honesty, no-doxxing, no-PII.)

## D2 — The kagami lineage (九鏡)

The 9 KG-mirror lineage actors are named the **kagami lineage**. The "9 八咫鏡" framing of the request
maps to these nine, each a facet of the one mirror turned toward a different slice of the world:

| 鏡 (actor) | reflects | routes toward |
|---|---|---|
| tsumugi 紡ぎ | power-entities + 縁 (取-concentration) | release (解放) |
| danjo 弾正 | state's own open data (discrepancy) | transparency |
| ooyake 公 | government units (civic atlas) | wayfinding |
| watatsuna 綿津綱 | submarine cables / chokepoints | redundancy + repair |
| watari 渡り | live ship/aircraft positions | safety + collision-avoidance |
| inochi 命 | the living world (biosphere) | restoration (再生) |
| hokorobi 綻び | systemic finance fragility | resilience |
| keizu 系図 | government power-relations | accountability |
| kanae 鼎 | public fiscal flows | open weighing, no verdict |

This is a **named set, not an enclosed one.** The doctrine extends to every later mirror (kabuto,
kanjō, busshi, kosatsu, hoshimori, tsugite, asobi, shionome, tatara, jinushi, …) — they are kagami
actors by the four-law test, not by membership in this table. The 九 is the canonical *lineage seed*,
the way 八咫 names a large mirror rather than counting nine of them.

## D3 — One doctrinal home

This ADR is the single doctrinal anchor the four properties previously lacked. A new mirror actor's
ADR/CLAUDE.md SHOULD state *"kagami actor — satisfies the 四鏡則 (ADR-2606211752): 映す/裁かぬ/
剣にあらず/曇りなき"* and derive its specific G1/G2 gates from these four, instead of re-deriving the
"never a target-list / non-adjudicating" framing from scratch. Charter Rider §2 + §1.12 remain the
ultimate authority; this ADR is the **named, mythically-grounded restatement** that makes the posture
legible and self-consistent across the lineage.

## D4 — Naming layering (concept now, code later)

- **Concept / doctrine layer (this ADR, now):** the canonical name is **kagami (鏡) actor**; the
  posture is the **Yata-no-Kagami doctrine / 四鏡則.** Docs, ADRs, and prose adopt this.
- **Implementation layer (unchanged):** the lexicon family stays `com.etzhayyim.mirror.*`
  (`mirrorActor`, `mirrorPost`) and the field `isMirror=true`; ADR-2606042330's `entity-as-actor`
  mechanism is untouched and remains authoritative for the keyless-mirror-actor machinery. "mirror"
  and "kagami" are **the same concept** — English-implementation term and Japanese-doctrinal term —
  exactly as the entity itself carries both an English handle (`etzhayyim`) and its 天御柱 / עץ חיים
  names.
- **Future gated cutover (NOT this ADR):** any rename of `com.etzhayyim.mirror.* → com.etzhayyim.kagami.*`
  or `isMirror → isKagami` is a deploy-affecting lexicon/registry cutover and MUST go through its own
  atomic PR under the repo's rename discipline (CLAUDE.md §"Do Not": no ad-hoc rename of substrate
  identifiers). It is explicitly out of scope here. The concept update does not wait on the code rename.

# Consequences

**Positive**

- The lineage's strongest, most-repeated invariant ("never a target-list") finally has a *reason*,
  not just a repeated assertion: 鏡 ≠ 剣, the Three-Treasures force-separation = the Charter's §1.12.
- One doctrinal home (四鏡則) replaces N per-actor re-derivations of the same four properties — less
  Shannon redundancy / drift across ~30 mirror actors (docs §"同じ判断を複写しない").
- The concept is named in the operating entity's own ontology (八百万/三種の神器), tightening the
  fit between the religious-corp's self-identity and its accountability architecture.
- Zero invariant amendments; zero code/deploy change; fully reversible at the prose layer.

**Negative / risks**

- **Two names for one concept** (kagami doctrine vs `mirror` lexicon) is a transient legibility cost
  until/unless the gated code cutover (D4) lands. Mitigated by stating the equivalence explicitly
  wherever both appear.
- **Mythic framing ≠ license to widen scope.** Naming the posture after a sacred mirror must not be
  read as elevating it to Tier-0/charter status — the *force-separation* it grounds is already §1.12
  (charter), but the *kagami naming* itself is a doctrinal/engineering convention (changeable), not a
  new constitutional invariant. Classify accordingly.
- Adoption is gradual: existing actor docs are not rewritten en masse by this ADR (that would be a
  multi-file sweep); they reference the doctrine as they are next touched.

# Alternatives Considered

1. **Keep "mirror actor," add no doctrine.** Rejected: leaves the four properties re-derived per-actor
   with no single anchor and no constitutional reason for "never a target-list."
2. **Rename the lexicon `com.etzhayyim.mirror.* → kagami.*` in this ADR.** Rejected for now: a
   deploy-affecting substrate-identifier rename that the repo's rename discipline requires to be its
   own atomic, gated PR; the *concept* update (the actual request) does not need it and should not be
   blocked by it (D4).
3. **Name it after the 剣 or 勾玉, or "panopticon/observatory."** Rejected: 剣 is force (the exact thing
   a mirror actor must NOT be); "panopticon/observatory" carries asymmetric-surveillance connotations
   the Charter explicitly disowns (§2(c) reciprocity axis). The 鏡 is the only treasure whose myth is
   *reflection without force or judgment* — the precise posture.
4. **Treat all ~30 mirror actors as "the nine."** Rejected: the set is open, not closed; 九鏡 is the
   canonical lineage seed (like 八咫 naming a large mirror), and the doctrine extends by the four-law
   test, not by table membership (D2).

# References

- ADR-2606042330 — entity-as-actor (keyless mirror-actor mechanism; concept this ADR renames/grounds)
- ADR-2605192100 — Mission Charter (八百万/産霊/無教会 + §1.12 force-separation, §1.15 non-eschatology)
- ADR-2605192315 — Transparent Force (1 SBT = 1 vote; the 剣 a kagami actor never holds)
- ADR-2605231525 — no-server-key (the mirror cannot post *as* the subject)
- ADR-2606012600 (watatsuna) / 2606011800 (tsumugi) / 2606041827 (watari) / 2606021600 (ooyake) /
  2605302300 (kanae) / 2606066001 (keizu) / 2606073000 (inochi) / 2606073400 (hokorobi) — the nine
  kagami-lineage source actors
- CHARTER-RIDER.md §2 (reciprocity / map-not-target posture) + §1.12 (force-separation)
