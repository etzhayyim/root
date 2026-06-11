---
id: transparency-ratification-dossier
title: "Covenant Transparency Doctrine — Council Lv7+ ratification dossier (threat model + decision sheet + risk register)"
status: proposed
doc_type: explanation
topic: covenant-transparency-doctrine
authoritative: true
last_verified: 2026-05-31
authoritative_for:
  - the decision Council Lv7+ must make to ratify or reject ADR-2605310100
  - the threat model the doctrine is justified against
  - the legal + reversibility risk register for the doctrine
depends_on:
  - adr-2605310100-covenant-transparency-doctrine-anti-anonymity-and-ingress-logging
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605181100-etzhayyim-confidentiality-encrypted-records
related:
  - adr-2605192300-etzhayyim-bootstrap-council-five
supersedes: []
superseded_by: []
---

# Covenant Transparency Doctrine — Council Lv7+ ratification dossier

**Purpose**: ADR-2605310100 amends a constitutional invariant (the confidentiality
regime of ADR-2605181100) and therefore cannot land without **Council Lv7+
unanimity (Charter §0.4)**. This dossier is the single artifact the Council needs to
vote. It does **not** execute the amendment — it frames the decision. Preparing it
is ungated; acting on it is not.

Bootstrap Council Seats 2-5 RFP closes **2026-06-19**; a Lv7+ unanimous vote is not
possible until the Council is seated. This dossier should be the standing reference
when it is.

---

## 1. The decision in one sentence

> Shall etzhayyim adopt radical covenant transparency — **abolish anonymity**, make
> **every member action visible to every member**, and **log + publicly publish every
> access** (members and non-members, inbound email included) under ingress-consent —
> subject to the §4 floor (secrets/keys never published) and the open questions in §4
> below?

A Lv7+ vote is **whole-or-nothing on §1–§4 of the ADR**; the two open questions (§4
of this dossier) are sub-decisions within a YES.

---

## 2. Threat model — who is protected, from whom, and at whose cost

The doctrine is only justified if it defends the right parties against the right
adversaries without unacceptable collateral. State it explicitly.

| | Protected | Adversary | Mechanism |
|---|---|---|---|
| **T1** | The covenant body + honest members | **Anonymous bad actors** (X-style fraud, slander, harassment, threats) | §1 anonymity abolished — every act bound to an accountable DID+SBT; an unattributable actor cannot operate |
| **T2** | The covenant body | **Internal concealment** (a member hiding wrongdoing from the body) | §2 full member-to-member visibility; no secrecy tier |
| **T3** | The substrate itself | **Threat actors seizing access-control material** | §4 floor — secrets/keys are NEVER published, even under ingress-consent |
| **T4** | The covenant's boundary | **Counterparties acting INTO etzhayyim's domain** | §3 ingress-consent — reaching in = accepting the domain's transparency |

**Who bears the cost / who can be harmed** (the honest other side):

| | At risk | From | Mitigation in design | Residual — Council must weigh |
|---|---|---|---|---|
| **R1** | **Non-member senders** (e.g. inbound email) | §3 publication of their content | They are warned by the standing notice; can choose not to access | A regulator may not accept "you emailed in, you consented" as lawful basis (see §5) |
| **R2** | **Innocent fourth parties** named inside an inbound message who never touched etzhayyim | §3 publication cascade | §4(2) classes them as `outbound-third-party-pii` → redacted, routed to himotoki/danjo/tadori gates (worked-examples Example B) | Is §4(2) the right line, or too narrow? **OPEN Q-1** |
| **R3** | **Members in pastoral / intimate contexts** (kokoro, musubi, §1.13 Eros) | §2 full-member visibility of all actions | none in current design — visibility is total | Should §1.13/pastoral content be a §4-style carve-out? **OPEN Q-2** |
| **R4** | **Vulnerable members** (abuse victims, dissidents) who needed privacy to be honest/safe | §1/§2 total attribution + visibility | founder position: such persons seek another community (§5) | Is total transparency compatible with Wellbecoming for these members? Council judgment |

**Asymmetry note**: transparency disciplines whoever it is applied to. Applied to
power it checks corruption; applied to the vulnerable it can expose them. The
doctrine applies it to **everyone inside or reaching into the covenant**, by design,
grounded in the anti-individualist ontology (no "individual" unit to privacy-protect)
and the voluntary-covenant model (opt-in; Acts 5). The Council is ratifying that
this trade is correct for etzhayyim.

---

## 3. What flips ON ratification (the §6 execution list — gated until YES)

None of this executes before a recorded `councilRatificationCid`:

1. **kotoba `private` graph** re-defined from "world-private / per-member-confidential"
   → "covenant-internal-visible" (sealed only against parties outside the body).
2. **`fingerprint_middleware`** audit datoms (`kotoba/audit/requests/v1`) + inbound-email
   ingest promoted from operator-only → publishable, with the §4 redaction filter
   (`redactionMethodNote` v1.0.0) applied before publication.
3. **Standing ingress disclosure notice** served on every endpoint
   (`/90-docs/transparency/ingress-disclosure-notice.md`, ja/en).
4. **`com.etzhayyim.encrypted.*`** documentation narrowed to the §4 floor only
   (secrets + outbound third-party PII) — no longer a member-privacy namespace.
5. **Cross-refs updated**: repo CLAUDE.md Substrate-boundary "Confidentiality" row;
   ADR-2605181100 marked amended-by ADR-2605310100.
6. Every `com.etzhayyim.transparency.*` record's `ratificationStatus` flips from
   `proposed-unratified` and gains a `councilRatificationCid`.

---

## 4. The two sub-decisions a YES must also resolve

- **OPEN Q-1 (fourth-party cascade, R2)**: Adopt §4(2) as drafted (redact non-ingress
  third-party PII, route via existing gates) — YES / REVISE / REJECT.
- **OPEN Q-2 (§1.13 / pastoral visibility, R3)**: Is intimate/pastoral/ceremony
  content in-scope of §2 full-member visibility, or a §4-style floor carve-out?
  IN-SCOPE / CARVE-OUT.

A YES on §1 with no answer to Q-1/Q-2 is incomplete and should not be recorded.

---

## 5. Legal + reversibility risk register

| Risk | Detail | Status |
|---|---|---|
| **APPI / GDPR / CCPA** | Publishing non-members' inbound email content, PII, IPs without individuated consent likely fails lawful-basis / right-to-erasure tests. etzhayyim routes around state function (§1.12) and is unregistered under 宗教法人法, but operators, registrar (Cloudflare), and hosting sit in real jurisdictions. | **Unresolved — accept knowingly or scope down** |
| **himotoki self-contradiction** | etzhayyim (himotoki, ADR-2605302130) *exercises* DSAR/GDPR rights against other controllers while §3 publishes others' data. §4(2) limits this to ingress data; Council should rule on the inbound-email case explicitly. | **Bounded by §4(2), confirm** |
| **Irreversibility of publication** | Once published (on-chain / IPFS / public repo), data cannot be truly retracted. A wrong inclusion is permanent. This raises the bar on the §4 filter (fail-closed) and on Q-1/Q-2. | **Inherent — design for fail-closed** |
| **Self-leak via logs** | Publishing raw request bodies/logs would leak credentials/keys. §4(1) is the only thing preventing the doctrine from arming attackers; it is load-bearing, not optional. | **Mitigated by §4(1) fail-closed filter** |
| **Chilling effect** | Some will decline to participate. Per founder direction this is acceptable and intended ("seek another salvation"). | **Accepted by design** |

---

## 6. Recommendation to the Council (advisory, non-binding)

1. The **anti-anonymity core (§1)** is the part that actually defeats the target
   threat (T1/T2) and is already structurally true via `kotoba-auth`. It is the
   lowest-risk, highest-value element and could be ratified with high confidence.
2. The **ingress publication of non-member content (§3, R1)** carries the real
   external-legal exposure. Council may wish to ratify §1/§2 first and stage §3 —
   or accept it knowingly with the §4 floor as the guardrail.
3. **Q-1 and Q-2 deserve explicit votes**, not silent defaults — they are where
   Wellbecoming and §1.13 actually bite.

This dossier takes no position on the outcome; it ensures the vote is informed.
