# etzhayyim — Terms of Use

> **DRAFT — not legal advice; counsel review required.**

**Project:** etzhayyim (アマノミハシラ / 天御柱 / עץ חיים, "Tree of Life") — a **non-profit** artificial-organism platform maintaining RAD cryptographic identity, an on-chain constitution and member roster, governor-mediated actor contracts, and append-only public-good ledgers.
**Operator / Entity form:** a **religious corporation established in the State of Delaware, United States** (Etzhayyim), operated as a non-profit religious organization.
**Domain / DID:** https://etzhayyim.com · `did:web:etzhayyim.com` (per-repo RAD identities under `did:web:etzhayyim.github.io:<repo>`).
**Last updated:** 2026-07-02
**Governing law:** the State of Delaware, United States.

etzhayyim is operated **only on donation** — there is no advertising, nothing is for sale, there is no subscription, and there is no member cash stipend (README; DONATE.md). **These Terms contain no commercial, payment, or paid-service provisions**, because none exist.

By using etzhayyim surfaces (the website, open apps, `e7m` CLI / MCP tools, and the public repositories/ledgers) you agree to these Terms.

---

## 0. Nature of the project

etzhayyim is a public-benefit, donation-funded religious corporation established in the State of Delaware, United States (Etzhayyim). Its constitution forbids profit distribution, advertising, and selling anything (DONATE.md). Its work — RAD identity records, the artificial-organism ecosystem, and its ledgers — is maintained and published as a **public good** under an open license (Apache 2.0; README).

## 1. No fees, no sale, no commercial relationship

- Access is free. We do not sell goods, services, memberships, data, or advertising.
- **Donations earn you nothing.** A donation is a pure gift — no perks, tiers, priority, governance weight, or recognition (anti-class invariant, ADR-2606012100 §G4; DONATE.md). Giving is never required to use anything.
- We use **no custodial fiat processor** (no Stripe / GitHub Sponsors / Patreon / Open Collective / Ko-fi / Liberapay) and retain **no donor PII**; value may flow only via non-custodial rails (USDC on Base L2 via `TitheRouter`, a curated crypto allowlist held as-is, a non-custodial fiat on-ramp, or in-kind compute/bills) (DONATE.md; ADR-2605172100, ADR-2606111800).

## 2. Membership (信者) — voluntary, permanent, and public

Membership is a voluntary religious commitment recorded as a **dual-permanent public record**: an on-chain `EtzhayyimMembership.join(...)` transaction on Base L2 **and** a row in this repository's git history, plus a signed oath AT Record on the member's own PDS (MEMBERS.md; ADR-2605172600).

By joining you understand and accept that:
- **The roster is open, admin-less, and permanent.** Anyone can read and verify any row against Base L2 and the linked AT Record.
- **Revocation is additive, not erasure.** Calling `EtzhayyimMembership.revoke()` and adding a "Revoked" entry records the change as new history; **the original join record remains** (MEMBERS.md §Revocation). This is intentional and is a core tension with statutory erasure/deletion rights (US state privacy laws such as CCPA/CPRA; and, for any covered users, GDPR/APPI) — see the Privacy Policy §4 and `[CONFIRM]` below.
- Membership confers **no economic benefit** and imposes no monetary obligation.

`[CONFIRM: reconciliation of the permanent on-chain + git membership record with data-subject deletion rights (CCPA/CPRA deletion as the primary regime; and, for covered users, GDPR Art. 17 / APPI cessation-of-use); whether members are told, before joining, that erasure is technically impossible and consent to that; and minimum age for the membership ritual.]`

## 3. RAD identity and organism data as a public good

Each actor/repository carries a **RAD identity**: `repo`, `did:web:etzhayyim.github.io:<repo>`, and an **append-only identity journal ledger** (`80-data/kotoba-rad/<name>.identity.journal.edn`). Governor-mediated actor contracts, the artificial-organism ecosystem state (CNS observations, aliveness metrics, members/lands registries), and these ledgers are maintained as durable, open, verifiable public records.

- The ledgers and constitution are **append-only / on-chain by design**; entries are not silently mutated or deleted.
- These records may include identifiers (e.g. GitHub handles, DIDs, wallet/Smart-Account addresses) that relate to identifiable people. See the Privacy Policy.

## 4. Governance

etzhayyim is governed by an on-chain constitution and a Council with a level ladder (Lv1 誓 → Lv7 老) and SBT-based voting (1 SBT = 1 vote) (README; MEMBERS.md; COUNCIL.md). Governance decisions (e.g. adding a crypto asset, ratifying amendments) follow the documented Council tiers/levels. Governance participation is a matter of the constitution, **not** these Terms of Use, and is not purchasable.

## 5. Acceptable use

When using etzhayyim surfaces you must not:
- attempt to corrupt, forge, or improperly mutate the ledgers, RAD identities, constitution, or roster;
- use the organism/atlas data as an attack surface or target list, or otherwise contrary to the constitutional invariants (e.g. observational-mirror / never-a-target-list postures, ADR-2605192100);
- use the read-only `e7m` / MCP tools to attempt privileged mutation (operator-only actions such as prune-approval are intentionally not exposed); or
- act unlawfully or infringe others' rights.

`[CONFIRM: full acceptable-use policy for public surfaces and the compute mesh, and enforcement/exclusion process for an admin-less US religious corporation.]`

## 6. Donated compute (in-kind)

If you donate compute (an `ameno` browser tab, an `e7m node join` laptop, or a `kotoba` pod), participation is **consent-gated, uncompensated, non-titheable, best-effort, and SLA-free**, and you may leave at any time (`e7m node leave`) (DONATE.md). You keep your own keys; etzhayyim holds none. `[CONFIRM: compute-donor terms — resource/battery/thermal budget, data processed on donor nodes, liability, and the R0→live external mesh-enrollment consent flow (ADR-2606012100 §G9).]`

## 7. Open license; no warranty

Software and records are provided under the repository's open license (Apache 2.0) and **"AS IS", without warranty of any kind**, to the maximum extent permitted by law. etzhayyim, being donation-funded and non-commercial, disclaims liability for use of the platform, ledgers, or organism outputs to the fullest extent the law allows. `[CONFIRM: liability posture appropriate for a US religious corporation (and its governing state) and any mandatory carve-outs.]`

## 8. Not government / not professional advice

Certain actors mirror public bodies or produce domain assessments (e.g. `ooyake` gov-atlas, `sng` attestations); these are **observational mirrors and member support only — never official channels, never the government, never a substitute for licensed professional or legal advice**, and they never actuate real-world systems without the documented consent + governor + Council controls (README; ADR-2606021600; ADR-2605265900).

## 9. Changes; governing law

We may update these Terms (see "Last updated"). These Terms are governed by the laws of the **State of Delaware, United States**, without regard to conflict-of-laws rules. The parties submit to the state and federal courts located in the State of Delaware as the venue for disputes. `[CONFIRM: dispute-resolution mechanism (e.g. arbitration) appropriate to a US religious corporation.]`

## 10. Contact

Legal and privacy inquiries: hello@etzhayyim.com. Mailing address: 1000 North West Street, Suite 1200, Wilmington, DE 19801, United States. No EU/UK GDPR Art. 27 representative or DPO is designated at this time.

---

*Draft template grounded in the repository README, DONATE.md, MEMBERS.md, COUNCIL.md, the `80-data/kotoba-rad/*` RAD ledgers, and the cited ADRs. No commercial/payment clauses are included because the project is non-profit and donation-only. All `[CONFIRM]` items require counsel confirmation before publication.*
