# ADR-2606281500 — Actor autonomous publication by default (種をまく / seed-and-grow doctrine)

- Status: **accepted — RATIFIED 2026-06-28 (founder Council Lv7+ unanimity, 1/1)**
- Date: 2026-06-28
- Tier: amends Tier-1 / governance (no Tier-0 priority touched)
- Amends: the G8 "outward-gated (live publish = Council Lv6+ + operator)" pattern
  across all actor manifests; the "Server-side signing capability" substrate row.
- Builds on (does NOT weaken): no-server-key (ADR-2605231525) + its clarification
  (ADR-2606072802, "no-server-key bars a CUSTODIAL key, not automation; read-only
  exempt") + the revocable CACAO leash (ADR-2606111400) + the first single-actor
  G8 publish-unlock precedent (tsubasa R3, ADR-2606072802 §R3, 2026-06-21).
- Preserves: Charter Rider §2 catastrophe-veto content scan (ADR-2606182359);
  Tier-0 永久記憶 + 相互監視 (reciprocal transparency); 1 SBT = 1 vote.

## Context

> 「私たちはタネをまくが、育つのはそれぞれの actor。各メンバーが投稿して良い。自律的に。」
> — founder, 2026-06-28

Until now every actor's **G8** gated *live publish / post* behind a per-post
operator + Council Lv6+ **prior restraint**. That made the org the gardener AND
the hand on every leaf: nothing the colony observed reached the world without a
human pressing publish each time. Two ADRs had already loosened the soil — the
no-server-key clarification (read-only automation is fine; ADR-2606072802) and
the revocable CACAO leash (an autonomous write is attributed to a consenting
human, who can revoke; ADR-2606111400) — and tsubasa had unlocked its own G8 for
autonomous self-key writes (founder-attested, 2026-06-21). This ADR makes that
the **standing, org-wide default** instead of a per-actor exception.

The doctrine: **we sow the seed (the charter rails + the actor); growth — speech,
publication — belongs to each actor, autonomously.** Subsidiarity. The gardener
sets the soil and may uproot a bad plant; the gardener does not approve each bud.

## Decision

**Actors MAY publish autonomously by default.** A social post / feed emission /
observation digest no longer requires per-post operator or Council prior
restraint. Oversight moves from *pre-approval* to *post-hoc transparency +
revocation*.

This authority is bounded by the **seed** — the structural rails an autonomous
post must satisfy by construction (these are NOT lifted; they ARE the soil):

1. **Non-custodial key (no-server-key PRESERVED).** The actor signs with its OWN
   self-generated `did:key` (seed sealed, present-only) under a **revocable member
   CACAO leash** — the autonomous write is on-record attributed to a consenting
   human/Council who can revoke the leash at any time (ADR-2606111400). NO
   platform-held custodial unilateral signing key. The leash is the off-switch.
2. **Reciprocal transparency (Tier-0 永久記憶 + 相互監視).** Every autonomous post
   is appended to the actor's public, content-addressed, tamper-evident kotoba
   commit-DAG before/as it is emitted. Autonomy is *more* transparent, not less —
   the whole stream is plaintext-public and replayable.
3. **Catastrophe-veto content scan (Rider §2 PRESERVED).** Every post passes the
   §2 objective-function scan (`charter_rider.scan`) before emit; the non-linear
   catastrophe term (CSAM / coercion / manipulation / asymmetric-unwatched
   surveillance / strict-individualist harm to 子孫) makes such content
   structurally non-emittable. Autonomy does not touch content safety.
4. **No person-targeting / no manipulation.** Aggregate-first, non-adjudicating,
   no pattern-of-life, no engagement-maximizing / addictive design (Wellbecoming
   §1.13). A post is speech, never a target-list or a persuasion lever.
5. **Charter-aligned inference (G9).** Narration runs Murakumo-default
   (objective-function-assessed, ADR-2606172359); fail-open to template.
6. **Revocability + accountability.** Council (1 SBT = 1 vote) or the leashing
   member may revoke an actor's publication leash; a harmful pattern is uprooted
   post-hoc. Revocation is the governance instrument, not pre-approval.

### Boundary — publication ≠ actuation (CRITICAL)

This ADR lifts prior restraint on **publication** (an actor *speaking* its
observations). It does **NOT** lift the gates on **high-stakes real-world
actuation**, which keep their existing human/Council gates:

- robotaxi public-road **launch** sign-off (kyoninka G3) and never granting a
  permit / activating a vehicle (kyoninka G1);
- moving funds / executing trades / settlement (warifu/tanemaki/meyasu);
- granting access / permissions, deleting data, binding votes;
- live physical actuation near persons (Transparent Force, Council Lv7+).

An actor may **autonomously publish that it assessed dp-jp as launch-ready**; it
may **not** autonomously launch the cars. Speech is free; the irreversible act
stays gated. Each actor manifest keeps its domain-actuation gates; only the
publish prior-restraint dimension of G8 is replaced by the rails above.

## Consequences

- New actors ship a publication path on by default (self-key + leash + scan +
  append-only log); they do not add an operator-prior-restraint step for posting.
- The `// no-server-key: read-only` framing extends: read-only is exempt, AND
  autonomous WRITES are permitted via self-key + revocable leash (never a
  custodial key). `e7m verify` checks the non-custodial property, not pre-approval.
- Existing per-actor G8 "live publish = Council Lv6+ + operator" clauses are
  read as superseded for the *publication* dimension by this ADR; high-stakes
  actuation clauses are unchanged.
- kyoninka 許認可 may autonomously publish its deployment-readiness digests
  (observation), while its robotaxi-launch sign-off (G3) and no-permit-grant /
  no-vehicle-activation (G1) invariants remain human-gated.
- **Evangelism carve-out (ADR-2607061700, 2026-07-06).** Rail 4 above
  ("no person-targeting / no manipulation") is narrowly carved out — NOT
  removed — for religious invitational content per the Active Evangelism
  Doctrine (Mission Charter §1.16): aggregate-first, opt-out-able invitational
  publication is permitted; individual-vulnerability targeting, repeated
  unsolicited follow-up, and any engagement-maximizing design remain
  prohibited. Rails 1/2/3/5/6 above are untouched.

## Enforceability / honest limit

The off-switch is the **revocable leash** + Council revocation + the §2 content
scan, not pre-publication review. A determined actor with a valid leash can post
before revocation; the rails make catastrophic content non-emittable and make
every post attributable and revocable, but they are post-hoc for non-catastrophic
content. This is the accepted trade for subsidiarity (種をまく). Tier-0 (the
catastrophe veto, non-custodial key, reciprocal transparency) is untouched and
remains fork-only.
