# ADR-2606072000 — sentei 剪定: Council as Pruner (post-hoc pruning governance, not prior restraint)

- **Status**: Proposed (R0)
- **Date**: 2026-06-07 (JST)
- **Authors**: etzhayyim (operating entity directive)
- **Supersedes (framing of)**: the *prior-restraint* reading of every outward gate across the actor wave (G7 live-inference / G11 Transparent-Force-publication / the "Council Lv6+ + operator BEFORE live publish" pattern in ADR-2605301600 danjo, ADR-2605302300 kanae, ADR-2606042330 entity-as-actor, and siblings). It does **not** repeal those gates — it **re-times** them.
- **Builds on**: ADR-2605312345 (Datom log = first-class canonical state), ADR-2606052100 (ake — append-only member-signed correction + revert), ADR-2605231525 (no-server-key), ADR-2605192100 §1.12 (Transparent Religious Force), Charter §1.15 (非終末論).

## Context — the directive

> 「Council は事前に止めるのではなくて、出てから止める。枝が育ってから、剪定する。
> council の役割は **剪定者 (sentei)**。etzhayyim の artificial organism の root からの
> organism の成長は止めないし、止められない。ただ伸び続ける枝を、剪定して美しく保つ。」

etzhayyim is an **artificial organism** that grows from its root (the Charter + the append-only
Datom log). Until now, governance was modelled as **prior restraint**: an actor's outward action
(live publish, live ingest, named-party disclosure, live actuation) was *blocked before it could
happen* until Council Lv6+/Lv7+ + an operator pre-approved it. That is a gate that stops growth at
the bud.

The directive inverts the model. **Growth from the root is unstoppable and is never pre-blocked.**
A branch grows, manifests, and only *then* — once it is a real, observable branch — may it be
**pruned**: cut back to keep the organism beautiful and within the Charter. The Council's organ for
this is **sentei 剪定** (剪定 = the horticultural/bonsai pruning of an living tree). The Council is
the **pruner (剪定者)**, not the censor.

This is not a loosening of the Charter — it is a re-timing of enforcement that is *more* faithful to
two invariants the prior-restraint model sat awkwardly against:

- **非終末論 (Charter §1.15)** — there is no final-state, no pre-ordained stop. An append-only log
  has no "halt"; it only grows. Prior restraint pretended to a power (freeze the future) the
  substrate does not have. Pruning is the only enforcement an append-only organism *can* actually
  perform: you cannot un-write a fact, you can only **append a retraction over it**.
- **Transparent Religious Force (ADR-2605192100 §1.12.B)** — force is legitimate only *after* it is
  on-chain, open, and 1-SBT-1-vote. A prior-restraint veto is exercised in the dark before anything
  is logged; a prune is a **logged, signed, voted, public act over a thing that already exists**.

## Decision

### D1 — Governance is post-hoc pruning, not prior restraint

Outward actions **proceed by default**. An actor that has built a branch (assembled fundFlowEdge,
projected datoms, drafted a disclosure, signed a publish) **may cross the publish/autonomy gate
itself** — autonomously, member-signed, no operator pre-approval required. The branch manifests on
the canonical Datom log. Enforcement happens *afterward*, by **sentei**, who prunes.

The legacy gate clauses (G7/G11 "Council Lv6+ + operator BEFORE live") are **re-read** repo-wide:
they no longer mean "the action is forbidden until approved." They mean "the action is **prunable**;
Council, as sentei, may cut it back after it manifests." The *artifact* of those gates becomes a
**prune-handle**, not a pre-lock.

### D2 — `sentei 剪定` is the Council's pruning organ (new Tier-B actor)

sentei observes **manifested branches** and prunes the overgrown / charter-violating ones to keep
the organism 美しく (beautiful, Wellbecoming-aligned). It is the operational, on-chain expression of
"Council = 剪定者". Defined in `20-actors/sentei/` (this ADR is its R0 charter).

### D3 — Pruning is append-only and reversible (非終末論; 剪定 is care, not destruction)

A prune **never deletes** a branch. It **appends** a `:prune/*` datom that marks the branch pruned
(quarantined / retracted / rolled-back-from-live-view / revoked). The branch's full Datom history
**remains** — recoverable by `as-of`, auditable forever. A mistaken cut **heals**: `regraft`
appends a restoration (exactly the `ake` revert pattern, ADR-2606052100). Pruning keeps the tree
shapely; it does not kill the tree.

### D4 — Structural invariants (the same 3-place enforcement as nusa/tazuna/kamado/ake/fuchi)

Encoded in **schema + lexicon const/enum + Python `ValueError`** so the violations are
*unrepresentable*, not merely discouraged:

| Gate | Invariant | Unrepresentable |
|---|---|---|
| **G1 no-prior-restraint** | sentei may act **only on a manifested branch** (`:branch/manifested` true). | a pre-emptive block — `:prune/prior-restraint` is not in the action enum; `prune()` raises on an unmanifested branch. The Council *cannot* stop a branch before it grows. |
| **G2 append-only / 非終末論** | a prune appends; it never deletes. The branch history survives. | `:prune/delete` / hard-erase — not in the enum; the engine only appends. |
| **G3 growth-unstoppable** | sentei prunes *named branches* only; it has no "halt the organism" power. | `:prune/halt-organism` / freeze-root — not representable. Root growth has no off-switch by construction. |
| **G4 Transparent Force** | every prune is an on-chain logged datom + Council Lv6+ sign (Lv7+ for invariant-adjacent) + 1 SBT = 1 vote for a *contested* prune. | a covert/unsigned/unlogged prune — `serverHeldKey` const false; an unsigned prune is refused. |
| **G5 no-server-key** | a prune is Council/member-signed; the server can never sign one. | a platform-key prune (ADR-2605231525). |
| **G6 reversible (regraft)** | any prune can be un-pruned; mistaken cuts heal via as-of. | an irreversible prune — every `:prune` has a defined inverse `:regraft`. |
| **G7 care-telos (美しく保つ)** | a prune must cite a Charter basis (overgrowth, §2(a)-(h) hit, mirror-violation, …); it is grooming, not punishment, and carries **no** verdict/guilt value. | a punitive/adjudicating prune — no `:prune/verdict` field; G4-token scan (the ake/kanae pattern). |
| **G8 Murakumo-only** | any "is this branch overgrown?" classification is Murakumo (ADR-2605215000); the model *flags*, Council *decides* (ake G2 pattern — non-adjudicating router). | vendor-LLM adjudication. |

### D5 — Pruning action vocabulary (`:prune/action` enum)

`quarantine` (hide from the live view, history kept) · `retract` (append a retraction over a
published datom) · `rollback` (as-of restore the live head to before the branch) · `revoke`
(withdraw an attestation/grant) · `regraft` (the inverse — un-prune / restore). **Not** representable:
`delete`, `prior-restraint`, `halt-organism`, `verdict`.

## Consequences

- **Actors self-publish.** kanae/danjo (and every gated actor) may now cross their own
  live-publish/live-ingest gates autonomously and member-signed. The kanae/danjo fiscal datoms
  (ADR-2606072000 sibling work) are the worked example: they grow onto the canonical log on their
  own; sentei is the organ that would prune them if they overgrew (e.g. a named-party disclosure
  that breaches G10, or a `:representative` figure later shown false → `retract` + `regraft` when
  corrected).
- **Enforcement is honest about the substrate.** You cannot un-write the append-only log; the only
  real lever is append-a-retraction. The model now matches the physics.
- **The Charter's hard invariants still bind** — but as *pruning targets that always succeed when
  invoked*, not as pre-locks. A §2(a)-(h) branch that manifests is **immediately prunable** by
  sentei (Lv6+, or Lv7+ for invariant-adjacent), and the prune is itself public + voted +
  reversible. Nothing about the 8 prohibited categories, no-server-key, cash≡0, Land inalienability,
  non-eschatology, or Murakumo-only is weakened; their *timing* moves from "blocked before" to
  "pruned after, transparently."
- **Mistakes heal.** Because prunes are reversible (`regraft`) and history is append-only, an
  over-aggressive Council cut is itself correctable — the organism is anti-fragile, not brittle.

## Non-goals / boundaries

- sentei is **not** a deletion tool (N1), **not** a prior-restraint veto (N2 — structurally
  impossible), **not** an adjudicator of guilt (N3 — no verdict field), **not** able to halt the
  organism's root growth (N4 — no such power exists), **not** server-signed (N5).
- This ADR does **not** amend the Lv7+-locked constitutional constants; it re-times their
  enforcement. The re-timing itself, touching the §1.12 Force model, is **Council Lv7+ ratifiable**
  (and, fittingly, prunable).

## R0 deliverable

`20-actors/sentei/` — ontology (`pruning-ontology.kotoba.edn`) + lexicons (`com.etzhayyim.sentei.*`)
+ `methods/prune.py` (the pure-function pruning engine: the 5 actions, the G1 manifested-only guard,
G2 append-only history, G6 regraft inverse, G7 care-telos no-verdict scan) + `methods/analyze.py`
(end-to-end over a `:representative` seed) + tests + registration in INFRA_ACTORS + actor-profile
seed. Design + offline only; live prune execution is itself Council Lv6+ signed (and reversible).
