---
id: adr-2605310100-covenant-transparency-doctrine-anti-anonymity-and-ingress-logging
title: "ADR-2605310100: Covenant Transparency Doctrine — anonymity abolished, full member-to-member visibility, and ingress-consent logging + publication of all who access etzhayyim / kotoba resources (non-members and inbound email included)"
status: proposed
doc_type: adr
topic: covenant-transparency-doctrine
authoritative: true
last_verified: 2026-05-31
priority: 9.5
axis: constitutional
weight: 0.95
priority_note: "Constitutional doctrine that resolves the 2026-05-30/31 founder discussion: the failure mode etzhayyim wants to kill (X-style anonymous fraud / slander / threat actors hiding behind anonymity) is solved by abolishing ANONYMITY (every act bound to an accountable DID/SBT), not by abolishing privacy in the abstract. Within the covenant: NO member-to-member secrecy — every believer can see every action. At the boundary: INGRESS-CONSENT — anyone who reaches into etzhayyim/kotoba resources (HTTP/XRPC/MCP/wallet-tx/inbound email), member or not, consents to full logging AND public publication by the act of access ('こちらの領分'; don't consent → don't access). Grounded in the §1.13/anti-individualist ontology (etzhayyim has no 'individual' unit to protect via anonymity). MATERIALLY AMENDS the confidentiality invariant (ADR-2605181100) + the Substrate-boundary Confidentiality row; intersects §1.13 Eros + Wellbecoming → requires Council Lv7+ unanimity (Charter §0.4) before any member-facing rollout."
authoritative_for:
  - the etzhayyim doctrine on anonymity vs privacy vs secrecy (the three are distinct; only anonymity is abolished outright)
  - intra-covenant transparency: full member-to-member visibility of all member actions (no Council-only tier)
  - ingress-consent: logging + publication policy for any party (member or non-member) that accesses etzhayyim / kotoba resources, inbound email included
  - the carve-out floor that transparency does NOT override (secrets/keys/credentials; non-ingress third-party data still bound by actor gates)
  - redefinition of kotoba `private` graph semantics and the `com.etzhayyim.encrypted.*` namespace scope
  - `com.etzhayyim.transparency.*` Lexicon namespace (ingressDisclosureNotice / accessLogPublication / covenantTransparencyAttestation)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605181100-etzhayyim-confidentiality-encrypted-records
  - adr-2605231525-etzhayyim-server-side-signing-capability
related:
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
supersedes: []
superseded_by: []
notes: |
  Session 2026-05-30/31: founder articulated that "private" is what lets fraud,
  slander and threat actors operate (the X / Twitter anonymous-bad-actor pattern),
  and that etzhayyim — having an anti-individualist ontology — has no "individual"
  to protect via anonymity. Direction given verbatim: (1) all believers can see all
  actions; (2) anyone who accesses etzhayyim / kotoba resources, INCLUDING
  non-members and including inbound email, has all logs taken and published, because
  by reaching into etzhayyim's domain they have entered "こちらの領分" — "iya nara
  access shinai you ni" (don't like it, don't access); (3) those who need to be
  protected AS individuals should seek another religion / another salvation and not
  use etzhayyim or kotoba. This ADR records that decision and — per faithful-ADR
  discipline — documents the constitutional amendments it forces, the self-protection
  carve-outs that even radical transparency cannot waive (secrets/keys), and the
  legal + third-party-harm consequences the founder must weigh before member rollout.
  The agent's earlier "transparency for power / privacy for persons" proposal was
  considered and REJECTED by the founder as inconsistent with the anti-individualist
  ontology; it is retained under Alternatives.
---

# ADR-2605310100: Covenant Transparency Doctrine — anonymity abolished, full member-to-member visibility, and ingress-consent logging + publication

**Status**: proposed (constitutional amendment — requires Council Lv7+ unanimity per Charter §0.4 before member-facing rollout)
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

A recurring failure mode motivates this doctrine: **threat actors and bad-faith
actors who use anonymity as a shield** to commit fraud, slander, harassment and
abuse — the pattern most visible on X / Twitter, where an unattributable account
pays no cost for the harm it causes. etzhayyim wants to make this structurally
impossible on its own substrate, while still being a place where "honest, fair,
open people who would not be ashamed to be seen" can act freely.

The first move is to stop overloading the word **"private."** It conflates three
distinct things, and only one of them is the source of the harm:

| Concept | What it means | Source of fraud? |
|---|---|---|
| **Anonymity** | The act is bound to **no accountable identity**. Responsibility cannot be located. | **YES — this is the X-style harm.** |
| **Secrecy-from-the-body** | The act is visible to *some* authority but **hidden from the covenant community**. | Enables concealment within the body. |
| **Encryption / confidentiality** | The act is attributable and recorded, but its *contents* are sealed to specific parties. | **No** — a tool, not a harm vector. |

Two further facts frame the decision:

1. **etzhayyim already kills anonymity at the substrate layer.** Every kotoba
   write is DID-bound and CACAO-signed (`kotoba-auth`, non-repudiable); governance
   is 1 SBT = 1 vote; Adherent SBT anchors identity. The thing that defeats the
   anonymous slanderer — **non-repudiable attribution** — is therefore already
   structurally present. This ADR promotes it from an implementation property to
   a **named constitutional doctrine**.

2. **etzhayyim's ontology is anti-individualist** (Charter / ADR-2605192100:
   多世代 priority + Wellbecoming + 反個人主義). There is no "individual" as the
   protected unit, so "protect the individual by letting them act anonymously" is
   not a coherent value here. Membership is a **voluntary covenant** (任意団体,
   opt-in). A covenant may set transparency as a condition of belonging — as the
   apostolic community did, where the sin of Ananias and Sapphira was **concealment
   from the body**, not the holding of property (Acts 5). Sola Scriptura-compatible.

The founder's direction (2026-05-30/31) resolves the design accordingly, and is
recorded as the Decision below. Where it amends existing constitutional invariants
(notably the confidentiality regime of ADR-2605181100), this ADR says so plainly.

# Decision

Adopt the **Covenant Transparency Doctrine**. It has three operative parts (§1–§3)
and one non-waivable floor (§4); §5 records its constitutional status and §6 the
implementation deltas.

## §1 — Anonymity is abolished; secrecy-from-the-body is abolished

- **Every action on etzhayyim / kotoba substrate MUST be bound to an accountable
  identity** (member DID + Adherent SBT, CACAO-signed). Unattributable action is
  not a supported mode. This is already enforced by `kotoba-auth`; the doctrine
  makes removing or weakening it a constitutional violation.
- **No member-to-member secrecy inside the covenant.** There is no "ordinary
  members cannot see what other members did" tier. The visibility floor is the
  *entire membership*, not a Council-only hierarchy.

## §2 — Full member-to-member transparency

- **Every believer can see every member action.** All member acts on the substrate
  (graph writes, transactions, resource use, actor invocations) are visible to all
  members, append-only and on-chain.
- **kotoba `private` graph semantics are redefined.** `private` no longer means
  "hidden from the world with per-member confidentiality"; it is redefined as
  **"covenant-internal-visible"** — readable by any member of the body, sealed only
  against parties *outside* the covenant (and, given etzhayyim's public / on-chain /
  open-source posture, effectively public for most artifacts). The
  `KOTOBA_DEFAULT_VISIBILITY` and CACAO graph-scope machinery is retained, but
  re-scoped to "covenant body" rather than "individual member."

## §3 — Ingress-consent: logging + publication for ALL who access the resources

- **The unit of consent is the act of access, not membership.** Anyone — member
  **or non-member** — who reaches into etzhayyim / kotoba resources (HTTP / XRPC /
  MCP request, wallet transaction, **inbound email**, or any other ingress) thereby
  enters etzhayyim's domain ("こちらの領分") and **consents to full logging and
  public publication of that access**, including its content (e.g. the body of an
  inbound email), origin metadata, and time.
- **Rationale (territorial / ingress consent):** the rules of the domain are set by
  the domain. A non-member is never compelled; they choose whether to reach in. The
  standing notice is: *if you do not consent to being logged and published, do not
  access etzhayyim or kotoba resources.* This is the boundary-side counterpart to
  §2's body-side transparency.
- **This makes the kotoba request audit trail public by design.** The
  `fingerprint_middleware` audit datoms (method / path / node_id / ts / peer_ip in
  `kotoba/audit/requests/v1`) and inbound-email ingest records move from
  operator-only to **publishable**, subject only to §4.

## §4 — The non-waivable floor (what transparency does NOT publish)

Radical transparency publishes **identities, actions, and their content**. It does
**not** publish **access-control material**, because that is not "speech or action"
— it is the key to the door, and publishing it would let the very threat actors
this doctrine targets seize the substrate. The following are **redacted, never
published**, and this floor cannot be waived by §3 ingress-consent:

1. **Secrets and credentials** — the DID private key (Keychain/1Password per repo
   policy), CACAO signatures as reusable bearer material, auth tokens, session
   secrets, paymaster keys, any `KOTOBA_*` secret. (Consistent with the standing
   "Do not commit secrets" invariant.)
2. **Outbound third-party data NOT brought in by ingress.** This doctrine governs
   parties who *reach into* etzhayyim. It does **not** widen the actor gates that
   govern data etzhayyim reaches *out* for: tadori PII attribution, danjo named-party
   observations, and himotoki disclosed-PII custody remain bound by their own ADRs
   (encrypted to authorized DIDs, aggregate-first, consent-gated). A third party who
   never touched etzhayyim is not "in our domain" and is not published by §3.

`com.etzhayyim.encrypted.*` (ADR-2605181100) survives **only** for this floor —
key material and §4(2) outbound third-party PII — not for member privacy.

## §5 — Constitutional status (honest framing)

This doctrine **amends constitutional invariants** and therefore **cannot be landed
unilaterally**. It requires **Council Lv7+ unanimity (Charter §0.4)** before any
member-facing rollout, because it:

- **materially narrows ADR-2605181100** (confidentiality) and the **Substrate-
  boundary "Confidentiality" row** in repo CLAUDE.md (from member-private to
  body-visible / floor-only encryption);
- **intersects §1.13 Eros** (consensual intimate content) and the **Wellbecoming /
  anti-harm invariant**: "all members see all actions" applied to pastoral care
  (kokoro), covenant ceremony (musubi) and Eros-permitted content raises a genuine
  harm question. **This is an explicit OPEN QUESTION for Council**, not silently
  resolved here. The founder's stated direction is full visibility; ratification
  must decide whether §1.13 / pastoral content is in-scope or is a §4-style floor
  carve-out.

Until ratified, status is **proposed**: the doctrine is the design intent of record,
but the encryption-narrowing and publication changes are **not executed**.

## §6 — Implementation deltas (post-ratification)

- **kotoba**: redefine `private` graph as covenant-internal-visible (§2); promote
  `fingerprint_middleware` audit datoms + inbound-email ingest to publishable (§3),
  with a §4 secret-redaction filter applied before publication; serve a standing
  **ingress disclosure notice** on every endpoint.
- **Lexicons**: add `com.etzhayyim.transparency.*` — `ingressDisclosureNotice`,
  `accessLogPublication`, `covenantTransparencyAttestation`. Narrow
  `com.etzhayyim.encrypted.*` documentation to the §4 floor.
- **Cross-refs**: update repo CLAUDE.md Substrate-boundary Confidentiality row and
  ADR-2605181100 (mark amended-by this ADR) — **only after Council ratification**.

# Consequences

**Positive**

- **Defeats the target failure mode at the root.** Anonymous fraud / slander /
  threat actors cannot operate where every act is non-repudiably attributed and
  body-visible. This is won by §1 (identity), independent of §3.
- **Anti-corruption by construction.** No member-to-member secrecy means no internal
  concealment; combined with the existing on-chain / open-source posture, the body
  can audit itself.
- **Doctrinally coherent.** Aligns with the anti-individualist ontology and the
  voluntary-covenant model; resolves the "why encrypt individuals if there is no
  individual" tension the founder raised.

**Negative / risks (recorded for Council deliberation)**

- **Legal exposure.** Publishing non-members' inbound email content, PII and IPs
  without their individuated consent collides with **APPI / GDPR / CCPA**. The
  ingress-consent theory ("you emailed in, you consented") is unlikely to satisfy a
  regulator's lawful-basis / right-to-erasure tests, and etzhayyim's operators,
  registrar (Cloudflare) and hosting sit in real jurisdictions even though the corp
  routes around state function (§1.12) and is unregistered under 宗教法人法.
- **Internal contradiction with himotoki.** etzhayyim (himotoki, ADR-2605302130)
  *exercises* DSAR/GDPR rights against other controllers while §3 would publish
  others' data. §4(2) limits the contradiction to **ingress** data, but Council
  should rule explicitly on the inbound-email case the founder named.
- **Innocent-third-party cascade.** An inbound email may contain a *fourth* party's
  data (e.g. a family member named by the sender). §3 publication would expose them.
  This is the sharpest Wellbecoming / anti-harm tension and needs a Council rule.
- **Self-leak risk — mitigated by §4.** Without the §4 floor, publishing raw request
  bodies/logs would leak credentials and keys and hand the substrate to attackers.
  §4 is load-bearing, not optional.
- **Chilling effect — intended.** Some will decline to participate. Per founder
  direction this is acceptable: those who require individuated protection should
  "seek another salvation" and not use etzhayyim / kotoba.

# Alternatives Considered

1. **Transparency for power, privacy for persons (agent's prior proposal).**
   Transparency-bind only force/governance (§1.12 Transparent Religious Force);
   keep member personal data encrypted. **Rejected by founder** as inconsistent with
   the anti-individualist ontology — there is no "person" unit to privacy-protect,
   and the harm (anonymous bad actors) reaches members, not only power.
2. **Accountable-pseudonymity only, no publication.** Abolish anonymity (§1) but do
   not publish access logs / ingress content. **Rejected** as insufficient for the
   founder's ingress concern: a counterparty acting *into* etzhayyim's domain should,
   by the founder's principle, be subject to the domain's transparency, not merely
   attributable to the body.
3. **Status quo (ADR-2605181100 member privacy retained).** **Rejected** as the very
   "private" regime the founder identifies as the enabler of concealment.

# Session Closure (2026-05-31)

Status remains **proposed** — nothing below executes any gated change (§5). What
landed this session is the complete, ratification-ready scaffold, all
`proposed-unratified`:

- **This ADR** + registration in `90-docs/adr/README.md` and `deps.toml`.
- **4 Lexicons** `com.etzhayyim.transparency.*` — `ingressDisclosureNotice`,
  `accessLogPublication`, `covenantTransparencyAttestation`, `redactionMethodNote`
  (repo lexicon validator CLEAN).
- **Standing notice text** (ja/en): `90-docs/transparency/ingress-disclosure-notice.md`.
- **Worked examples** incl. the innocent-fourth-party inbound-email cascade:
  `90-docs/transparency/worked-examples.md`.
- **Council ratification dossier** (threat model + what-flips-on-YES + open
  questions Q-1/Q-2 + legal/reversibility risk register):
  `90-docs/transparency/ratification-dossier.md`.
- **Machine-enforced constitutional guard**:
  `70-tools/scripts/lint/transparency-floor-and-gate.{mjs,test.mjs}` — Check A (§5
  `ratificationStatus` const) + Check B (§4 floor consts) + Check C (no premature
  execution in code without a `councilRatificationCid`); 9-test suite green, clean
  on the real repo.

**Gated, not done** (await Council Lv7+ ratification per §5/§6): kotoba `private`
graph re-definition, `fingerprint_middleware` publishable promotion, `com.etzhayyim.encrypted.*`
narrowing, and the cross-ref edits to repo CLAUDE.md + ADR-2605181100. The two
sub-decisions (Q-1 fourth-party cascade; Q-2 §1.13/pastoral visibility) are
reserved to the ratification vote. Bootstrap Council Seats 2-5 RFP closes 2026-06-19.

# References

- ADR-2605192100 (etzhayyim Mission Charter — §0.4 Lv7+ lock, §1.12 Transparent
  Religious Force, §1.13 Eros, Wellbecoming, 反個人主義 ontology)
- ADR-2605181100 (Confidentiality — `com.etzhayyim.encrypted.*`; **amended by this ADR**)
- ADR-2605262130 (kotoba storage substrate — `private` graph / CACAO scope)
- ADR-2605231525 (server-side signing capability — no platform-held key)
- ADR-2605301400 (tadori) / ADR-2605301600 (danjo) / ADR-2605302130 (himotoki) —
  outbound actor gates preserved by §4(2)
- `40-engine/kotoba/crates/kotoba-server/src/fingerprint.rs` (request audit trail
  promoted to publishable by §3)
- Acts 5:1–11 (Ananias & Sapphira — concealment from the body, not property, as the offense)
