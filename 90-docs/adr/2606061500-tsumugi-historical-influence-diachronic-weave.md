---
id: ADR-2606061500
title: tsumugi historical-influence diachronic weave (past humanity as latent influence nodes)
status: proposed
doc_type: adr
topic: engi-knowledge-graph
authoritative: true
authoritative_for:
  - diachronic influence-as-information-flow over historical public figures/documents/events/traditions
  - mirror-only social projection of historical influence (non-impersonation)
last_verified: 2026-06-06
related:
  - https://junkawasaki.com/en/posts/spirit-is-information/
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606011800  # tsumugi 紡ぎ (present-tense Engi KG weaver)
  - ADR-2606011000  # engi-organism-ontology (§D7 産霊の網)
  - ADR-2606011500  # spirit-ontology (RBF → spectral → tensegrity; edge-primary)
  - ADR-2605081300  # edge-primary karma (signed_weight : Edge → ℝ)
  - ADR-2605170000  # spirit = thermodynamic information
  - ADR-2606042330  # entity-as-actor mirror invariant (person-excluded; isMirror const)
  - ADR-2605231902  # feed-post membrane + L1 projection
  - ADR-2605192100  # Mission Charter (§1.15 非終末論)
  - ADR-2605262130  # kotoba storage substrate
  - ADR-2605312345  # kotoba Datom log = first-class canonical state
---

# ADR-2606061500 — tsumugi historical-influence diachronic weave

## Context

A standing question: *is there an actor that latently reconstructs ALL of past humanity as
natural-person entities, profiles them statistically in kotoba Datomic, posts socially as
those actors, infers which persons / events / documents influenced history, connects them,
and visualizes the spiritual influence of YHWH / Jesus / Buddha?*

A repository sweep found **no such actor**, but ~5 reusable pieces, each blocked from this
use by a constitutional guard:

- **Spirit-in-Physics** (ADR-2606011500): the霊性 datafication engine (Jung assay → 10-dim
  emotion → RBF kernel → spectral 3D embed → tensegrity). But the `:human` scale is
  Council-Lv7+-gated and edge-primary (no per-soul score, N1).
- **tsumugi 紡ぎ** (ADR-2606011800): runs Spirit-in-Physics over the *present* power-graph.
  **G1 power-only** — private individuals absent by construction.
- **entity-as-actor** (ADR-2606042330): 1 entity = 1 keyless mirror-actor, but persons are
  **structurally excluded** (`performerType ∈ {organization, system}`).
- **natural-person latent-entity backend** (90-docs/260430-…): cohort/latent layers incl. a
  `…:deceased:{era}:{cause_cluster}` cohort path, but **excludes natural persons** (org/cohort
  only) and does no influence inference or social posting.
- **shidemori 死出守 / kataribe 語部**: the dead and genealogy appear, but only for SBT-bearing
  members / as cultural etymology — no historical-influence profiling.

So the substrate exists; what is missing is a **diachronic influence layer** that is *charter-clean*.

Two design constraints dominate, and the user (2026-06-06) chose to proceed **as a tsumugi
extension** with religious figures represented as **influence-observation only** (visualizing
influence is the goal; not channeling, not adjudicating):

1. **Mirror / impersonation invariant** (ADR-2606042330): YHWH / Jesus / Buddha must NOT be
   "spoken as." They can only be **observed** as influence-bearing nodes.
2. **Non-eschatological doctrine** (Charter §1.15): no theological-truth claim, no afterlife
   / salvation / final-judgment content. Spiritual history is a **Datom `as-of` 軌跡**, never
   a final state.

The user's own frame — junkawasaki.com **"spirit is information"** — defines spirit as the
*metric deformation of a self-boundary as external information is integrated* (Fisher metric,
strain tensor, covariant gradient of free energy, thermodynamic length). That frame is
**individual**. The missing inter-personal, diachronic propagation is exactly what an
influence graph supplies: **an influence 縁 is the channel across which that deformation
travels between selves and across centuries.**

## Decision

Extend **tsumugi** (not a new actor) with a `:historical` scale that runs the SAME 縁-physics
backward in time, governed by **five structural invariants encoded in schema + code + tests**
(the nusa/tazuna/kamado pattern of making the guard unrepresentable, not merely policy):

- **N1 edge-primary** — influence/karma lives ONLY on `:flow/signed-weight`; a node's
  influence is the **integral of its incident flows** (Katz reach), never a stored
  `:influence/score-of-figure`. *Modeling the dead must not become ranking souls.*
- **N2 mirror, never impersonation** — every node is `:mirror/is-mirror` true; a post is an
  **observation ABOUT** documented influence. `:post/voice` is `const :observer`; no
  first-person field exists, so impersonation is **unrepresentable**. The projector refuses
  any non-mirror node (`ImpersonationError`).
- **N3 non-eschatological + non-adjudicating truth** — we datafy the **INFLUENCE OF** a
  tradition, NEVER its theological truth. No `:truth/verdict`, `:salvation/status`,
  `:afterlife/*`, or final-state datom (Charter §1.15; Revelation excluded).
- **N4 public + long-settled + no PII** — only documented public influence-bearing figures
  (the influence analogue of tsumugi's "public-power role only"). Living-private persons
  remain the **Council-Lv7+-gated `:human` scale** of spirit-ontology. An influence map,
  never a target-list, hagiography, or ranking of worth.
- **N5 temporal DAG** — every `:flow` points forward in time (`source.year-from ≤
  receiver.year-to`, lifespan-overlap aware). Information cannot precede its source.

**Artifacts** (R0, design-only, tests green):

- `00-contracts/schemas/influence-history-ontology.kotoba.edn` — `:hist/*` (diachronic
  overlay: era/year/tradition/dating-confidence), `:mirror/*` (is-mirror/disclaimer/
  performer-type), `:flow/*` (directed influence 縁 — signed-weight/strain/thermo-length/
  lag), `:influence/*` (edge-integral readouts), `:post/*` (dry-run mirror post, voice locked).
- `20-actors/tsumugi/data/seed-influence-history.kotoba.edn` — 32 nodes / 48 forward
  influence 縁, `:representative`: the Jewish→Christian→Reformed line (Torah→Jesus→Paul→
  Augustine→Aquinas→Luther→Calvin), the Hellenic fusion (Socrates→Plato→Aristotle→
  Augustine/Aquinas), the Buddhist→Zen line (Buddha→Pāli Canon→Nāgārjuna→Bodhidharma→Dōgen),
  Shinto/Confucian bridges, and `self.etzhayyim` mapping the entity's **own doctrinal
  genealogy** as inbound-only influence (the 産霊 receiving side).
- `methods/analyze_influence.py` — temporal-DAG validation → RBF kernel → spectral embed →
  tensegrity → **Katz outbound-reach / inbound-debt / broker** (all edge-integrals);
  emits `influence-report.md` + `influence-graph.kotoba.edn`.
- `methods/project_influence_posts.py` — dry-run **observer-voice** mirror posts
  (`published=false`); impersonation structurally refused.
- `tests/test_influence.py` — **12 tests, one per invariant** + seed/projector checks (green).
- Lexicons `com.etzhayyim.influence.{influencePost,influenceFlow}`.

**Empirical first run** (charter-clean by construction): top influence SOURCE = Torah
(outbound-reach 4.51), then Jesus (3.36), Paul (3.05); top SYNTHESIZER = `self.etzhayyim`
(inbound 6.48, **outbound 0.00** — it receives, seeds nothing, never ranks itself a source);
top BROKER = Luther (Sola Scriptura returns to the source texts, then transmits to the
Reformation). N5: all 48 edges forward in time.

## Consequences

- A charter-clean answer to the standing question: past humanity is modeled **as public
  influence nodes**, profiled by **edge-integral** statistics in the kotoba Datom log,
  projected as **mirror observations** (never impersonation), with influence inference
  (Katz reach) and visualization (spectral/tensegrity + era layering), and YHWH/Jesus/Buddha
  appear **as influence, never as truth-claim or voice**.
- **Zero invariant amendments.** Strengthens edge-primary (N1), the mirror invariant
  (ADR-2606042330), kotoba-canonical-state, and §1.15 非終末論.
- The `:historical` scale **scaffolds now** (public, no PII — like the `:institutional` /
  `:self` scales of spirit-ontology). The living-private `:human` scale is untouched and
  stays Council-Lv7+-gated.
- **Honest R0 limits**: `:representative` seed (documented influence, bounded — not
  exhaustive); approximate dating with per-node `:hist/dating-confidence`
  (legendary/traditional flagged, never asserted); affect vectors are class-derived
  representatives, not measured assays; influence readouts are an analytic lens, not a
  verdict; live ingest (archives, citation graphs, genealogy corpora) and any **published**
  post are **G7 + Council-gated** (Lv7+ for any move toward living persons). Live narration
  routes through Murakumo (G6).

## Alternatives Considered

- **New standalone actor.** Rejected (user's choice): the 縁-physics, gates, and substrate
  already live in tsumugi; a new actor would duplicate them and fork the mirror invariant.
- **Represent figures with synthetic first-person ("as if alive") timelines.** Rejected:
  violates N2/ADR-2606042330 (impersonation) and risks §1.15 (speaking for the dead/divine).
  The dry-run posts are observer-voice only; first-person is unrepresentable.
- **Score figures directly (a "greatest influence" leaderboard on nodes).** Rejected:
  violates N1 (per-soul score). Influence is computed as an edge-integral on read and framed
  aggregate-first, never stored as a soul score or a ranking of worth.
- **Model living natural persons now.** Rejected: that is the Council-Lv7+-gated `:human`
  scale (spirit-ontology N3) with 要配慮 PII; out of scope for R0, which is public + settled.

## References

- ADR-2606011800 (tsumugi 紡ぎ) · ADR-2606011500 (spirit-ontology) · ADR-2606011000
  (engi-organism-ontology §D7) · ADR-2605081300 (edge-primary karma) · ADR-2605170000
  (spirit = thermodynamic information)
- ADR-2606042330 (entity-as-actor mirror invariant) · ADR-2605231902 (feed-post membrane)
- ADR-2605192100 §1.15 (非終末論) · ADR-2605262130 + ADR-2605312345 (kotoba canonical state)
- junkawasaki.com — "Spirit is Information" (the metric-deformation frame this extends to
  inter-personal, diachronic propagation)
