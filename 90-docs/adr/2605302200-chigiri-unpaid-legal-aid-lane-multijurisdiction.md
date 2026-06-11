---
id: adr-2605302200-chigiri-unpaid-legal-aid-lane-multijurisdiction
title: "ADR-2605302200: chigiri — 無償徹底 (zero-compensation) lawyer-supervised legal-aid lane + multi-jurisdiction UPL analysis (amends ADR-2605262700)"
status: proposed
doc_type: adr
topic: chigiri-unpaid-legal-aid-lane
authoritative: true
last_verified: 2026-05-30
priority: 6.6
axis: governance
weight: 0.62
priority_note: "Corrects a premise error ('非営利 ⇒ 弁護業務可') and adds a CONSTITUTIONAL legal-aid lane to chigiri. The operative axis is NOT for-profit/non-profit; it is (a) compensation and (b) qualified-lawyer involvement, and which of these binds varies by jurisdiction. Universal safe harbor adopted: zero compensation (incl. indirect benefit) + delivery by/under supervision of a jurisdiction-licensed lawyer. Adds cell `chigiri_legal_aid_clinic` + 2 constitutional gates (G15 zero-compensation, G16 lawyer-supervision) + per-jurisdiction routing table (JP/DE/FR/UK/US). Does NOT weaken UPL gate G14: chigiri itself still emits no legal advice; the new lane is a SUPERVISED human-lawyer delivery channel funded by Public Fund, with chigiri as intake/attestation substrate only. Litigation/court representation remains lawyer-monopoly everywhere and is OUT of scope. 認証ADR (Japan ADR法) flagged as a SEPARATE future lane, not adopted here."
authoritative_for:
  - chigiri zero-compensation legal-aid lane
  - multi-jurisdiction UPL / 非弁 analysis for religious-corp legal assistance (9 jurisdictions)
  - G15 zero-compensation invariant (incl. indirect benefit)
  - G16 jurisdiction-licensed-lawyer supervision invariant
  - per-jurisdiction legal-service routing table (JP/DE/FR/UK/US/KR/AU/CA-ON/AT-CH)
  - regulatory-family taxonomy (compensation / licensure / activity-gated)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605301020-basic-high-income-imputed-and-commons-asset-doctrine
related:
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605263400-musubi-covenant-ceremony-tier-b-actor-r0
  - adr-2605302330-chigiri-japan-certified-adr-mediation-lane
supersedes: []
superseded_by: []
---

# ADR-2605302200: chigiri — 無償徹底 (zero-compensation) lawyer-supervised legal-aid lane + multi-jurisdiction UPL analysis

**Status**: proposed
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki

# Context

A premise was raised in design discussion: *"非営利であれば弁護業務を行なって良いはず"* — that a
non-profit may provide legal-representation/advice services by virtue of being non-profit.

This premise is **incorrect as stated** in every jurisdiction surveyed. The legal-monopoly statutes
that protect the practice of law are **not gated on for-profit/non-profit status**. They are gated on
some combination of **(a) compensation** and **(b) the involvement of a qualified/licensed lawyer**,
and *which* of those two binds varies by jurisdiction. A non-profit (任意団体 / 公益社団 / NPO / Verein /
association / 501(c)(3)) that takes compensation for legal work is just as exposed as a for-profit one;
conversely a for-profit body acting truly gratis may escape the bar in some jurisdictions.

chigiri (ADR-2605262700) already encodes this correctly via **G14 (UPL prohibition)**: chigiri renders
**no legal advice**; human counsel is contracted from the Public Fund (Council Lv6+) when advice is
required. This ADR does **not** weaken G14. It instead opens a **bounded, constitutionally-gated lane**
through which the religious-corp may lawfully deliver *free* legal assistance to adherents — and pins
the exact conditions that keep it lawful across the five surveyed jurisdictions.

## Multi-jurisdiction analysis (verified 2026-05-30)

| Jurisdiction | Restricting statute | Operative axis | Does "free" (無償) suffice for **advice/consultation**? | Residual hard monopoly |
|---|---|---|---|---|
| **Japan** | 弁護士法 §72 (非弁護士の法律事務の取扱い等の禁止) | **Compensation** — requires 「報酬を得る目的」 **and** 「業として」 | **Yes** — gratis consultation lacks the 報酬 element (the "大学法律サークル" rationale). NB: 報酬 includes non-money benefit (物品・接待), so it must be *truly* free. | Court representation = 弁護士 only. 非弁提携 (§27) forbids fee-sharing with a non-lawyer body. |
| **Germany** | RDG (Rechtsdienstleistungsgesetz) §6 | **Compensation gate is satisfied by being free, BUT a supervision condition attaches** | **No, not alone** — §6 permits *unentgeltliche* Rechtsdienstleistung, but outside family/neighbour/close-personal ties it must be performed **by, or under the Anleitung (guidance) of, a person with Befähigung zum Richteramt** (a qualified jurist/lawyer). gemeinnützige Vereine qualify only when this supervision is met. | Court representation reserved; supervision is mandatory for organised free advice. |
| **France** | Loi n°71-1130 du 31 déc. 1971, art. 54 | **Compensation + habituality** — monopoly bites only «à titre habituel et **rémunéré**» | **Yes** for consultation juridique rendered *gratuitement*. (Cass. 7 May 2025 tightened the perimeter for *paid* personalised advice — reinforces that the line is rémunéré.) | Postulation / représentation en justice (litigation) reserved to avocats regardless of fee. |
| **England & Wales** | Legal Services Act 2007, Part 3 | **Activity-type, not compensation** — only the 6 *reserved legal activities* are restricted | **Yes — and broader**: giving legal advice is **unreserved**, lawful free *or* paid, by anyone incl. charities. Sch. 3 adds tailored exemptions for non-commercial bodies. | The 6 reserved activities (rights of audience, conduct of litigation, reserved instruments, probate, notarial acts, administration of oaths) require authorisation. |
| **United States** | State UPL rules / ABA Model Rule 5.5 (adopted state-by-state) | **Split by state** — some states gate on fee, others on licensure | **No (assume not)** — definitions vary *within* the US. California: «only attorneys can give legal advice», UPL **even for free** (licensure-gated). Other states define UPL as «doing a lawyer's work … for money» (compensation-gated). The protective assumption is licensure-gated. Non-profit/legal-aid (501(c)(3), LSC) operate **through bar-admitted attorneys**, with pro-bono/inactive-status supervision rules (e.g. D.C.). | Both advice and representation licensure-gated in the strict states; supervision by an admitted attorney is the enabling mechanism. **State-level granularity mandatory before any US matter.** |
| **South Korea** | 변호사법 (Attorney-at-Law Act) §109 | **Compensation** — «보수를 받거나 받을 것을 약속하고» (receiving or promising to receive remuneration) | **Yes (likely)** — free service lacks the remuneration element; §34 separately forbids fee-sharing with non-lawyers (cf. Japan §27). Five 士業-equivalents (변호사/노무사/변리사/법무사/행정사) each have a statutory scope. | Court appearance reserved to 변호사. |
| **Australia** | Legal Profession Uniform Law (state-adopted; e.g. NSW/Vic 2014), s.10 | **Compensation in several jurisdictions** — defence available if not for «fee, gain or reward» | **Yes (in those jurisdictions)** — pro bono practice with impunity where the «fee, gain or reward» defence exists. Max penalty otherwise 2 yrs / 250 penalty units. | Court practice reserved to qualified entities. |
| **Canada (Ontario)** | Law Society Act + LSO By-Law 4 | **Licensure** — lawyers **and licensed paralegals** may provide legal services | **No, generally** — providing legal services requires an LSO licence; By-Law 4 carves out specific not-for-fee / non-commercial exemptions. Ontario uniquely licenses **paralegals** for small-claims, POA, summary criminal, tribunals. | Reserved to lawyers/paralegals per LSO scope; UPL actively prosecuted. |
| **Switzerland** | BGFA (Anwaltsgesetz) | **Activity-type (court representation only)** — *verified 2026-05-30* | **Yes** — the Anwaltsmonopol is confined to professional party-representation before civil courts (and not even mediation/rental/labour courts or summary proceedings). **Out-of-court legal advice / Rechtsberatung is NOT monopolised** — unregistered advisers may give it. | Party-representation before civil courts reserved. `enabled` for out-of-court advice (G16 over-compliant). |
| **Austria** | RAO (Rechtsanwaltsordnung) §8 + Winkelschreiberei prohibition | **Broad** — paid business legal advice also restricted | **Not relied on** — Austrian Winkelschreiberei doctrine reaches beyond court representation. ⚠️ `verify-required` — AT matters NOT enabled at R0 until the unentgeltlich scope is confirmed against RAO + case law. | Broad reservation. ⚠️ R0 does NOT enable AT matters. |

### Key asymmetry (9 jurisdictions surveyed)

Two regulatory families emerge:

- **Compensation-gated** (free advice lawful on its own): **Japan** (§72), **France** (art. 54 «rémunéré»), **South Korea** (§109 «보수»), **Australia** (s.10 «fee, gain or reward» defence). "無償徹底" alone opens at least free advice here.
- **Licensure / activity-gated** (free is *not* sufficient): **Germany** (RDG §6 — free OK *but* qualified-jurist supervision mandatory), **United States** (split; assume licensure-gated — bar-admitted attorney must deliver/supervise; California explicitly so), **Canada/Ontario** (LSO licence required; narrow not-for-fee carve-outs), **Austria** (broad Anwaltsmonopol — verify).
- **Activity-type, advice unreserved** (most permissive): **England & Wales** (LSA 2007 — legal advice is unreserved, lawful free or paid; only the reserved-6 need authorisation), **Switzerland** (BGFA monopoly is court representation only; out-of-court advice not monopolised — *verified 2026-05-30*).
- **Everywhere**: actual **litigation / court representation** stays a lawyer (or, in Ontario, lawyer/paralegal) monopoly. Out of scope for this lane.

This confirms the universal safe harbor below holds across **all nine**: it is over-compliant in the compensation-gated and advice-unreserved families, and exactly-compliant in the licensure-gated family.

### Universal safe harbor

The single condition-set that is lawful in **all five** jurisdictions simultaneously:

> **Zero compensation (including indirect economic benefit) + delivery by, or under the supervision of, a lawyer licensed in the relevant jurisdiction.**

This is *over-compliant* in JP/FR/UK (which would permit free advice without the supervision overlay) and
*exactly-compliant* in DE/US (which require it). Adopting the strictest common denominator lets one design
serve all five without per-jurisdiction divergence in the trust-critical path — divergence is pushed to a
declarative routing table, not to the gate logic.

This also dovetails with existing doctrine: the religious-corp is already **non-profit, donation-only,
cash≡0 in-kind** (ADR-2605192115 + ADR-2605301020). "無償徹底" is therefore not a new constraint but a
restatement of the Charter's economic invariant applied to the legal-assistance surface.

# Decision

Amend chigiri (ADR-2605262700) — **G14 is preserved unchanged** — by adding:

## D1. New cell `chigiri_legal_aid_clinic` (R0 path-reserved)

A **delivery channel**, not an advice engine. chigiri provides: adherent intake, conflict-of-interest
check, matter attestation on MST (`com.etzhayyim.chigiri.legalAid.*`), and Public-Fund-funded routing to
a licensed lawyer. The legal advice itself is produced by the **human lawyer**, never by chigiri code or
by any LLM cell. Placed under the `gad` (external-interface) lane alongside `employment_compliance` /
`tax_receipt`.

## D2. G15 — Zero-compensation invariant (CONSTITUTIONAL, IMMUTABLE)

The legal-aid lane MUST charge the adherent **nothing** — no fee, no nominal processing fee, no tithe
attribution, no SBT-priced internal-purchase, and **no indirect economic benefit** (物品 / 接待 / quid-pro-quo
service credit). Donations are accepted **only** into the general Public Fund and MUST NOT be solicited as,
recorded as, or temporally coupled to consideration for a specific legal matter. Enforced by a lint hook
`70-tools/scripts/lint/no-legal-aid-consideration.mjs` (W1) that CI-blocks any code path linking a
`legalAid.matter` record to a payment/tithe/SBT-purchase record.

## D3. G16 — Jurisdiction-licensed-lawyer supervision invariant (CONSTITUTIONAL, IMMUTABLE)

Every `legalAid.matter` MUST carry a `supervisingCounsel` attestation: a DID-bound reference to a lawyer
**licensed in the adherent's jurisdiction** (or, for Germany, a person with Befähigung zum Richteramt;
for the US, a bar-admitted attorney in good standing), retained via Public Fund (Council Lv6+ per
ADR-2605192145). A matter without a resolvable, in-jurisdiction `supervisingCounsel` MUST NOT leave the
intake state. This satisfies DE/US strictly and JP/FR/UK over-compliantly.

## D4. Per-jurisdiction routing table (declarative, versioned)

`com.etzhayyim.chigiri.legalAid.jurisdictionPolicy` records encode, per ISO-3166 jurisdiction: the
restricting statute, whether unsupervised free advice is permissible (informational only — the gate still
requires G16 supervision), and the **hard-monopoly carve-out** (always: no litigation/court representation
without a duly-authorised advocate). The **nine rows** above seed the table (JP/DE/FR/UK/US/KR/AU/CA-ON/AT-CH),
each tagged `regulatoryFamily ∈ {compensation, licensure, activity}` and
`enableState ∈ {enabled, verify-required}`. AT/CH and US-state granularity ship as `verify-required`
(not enabled) at R0. Method is open per Charter Rider (published, auditable), mirroring danjo G6.

## D5. Hard scope ceiling (non-goals, IMMUTABLE)

The lane delivers **advice/consultation and document explanation only**. It MUST NOT perform: court
representation, litigation conduct, reserved instruments, probate, notarial acts, oath administration
(the UK reserved-6 set is the global ceiling proxy), or anything a jurisdiction reserves to advocates.
Those are routed to the adherent's retained counsel as an EXTERNAL act, never performed by the religious-corp.

## D6. Premise correction recorded

The Status index and chigiri CLAUDE.md are annotated: **"非営利 ≠ UPL exemption. The axis is
compensation + lawyer involvement; see ADR-2605302200."** This prevents the same premise error recurring.

# Consequences

**Positive**

- The religious-corp can lawfully extend *free* legal assistance to adherents in JP/DE/FR/UK/US under one
  uniform gate, funded by the existing Public Fund mechanism — no new financial rail.
- No conflict with the cash≡0 / donation-only / ad-free invariants; "無償徹底" *is* those invariants.
- G14 (chigiri renders no advice) is untouched; liability for advice sits with licensed human counsel,
  where it legally belongs. §27 非弁提携 risk is contained because chigiri takes **no fee** to share.

**Negative / costs**

- Throughput is bounded by retained-counsel availability and Public Fund budget; the lane cannot scale on
  software alone (by design — that boundary is the legal safe harbor, not a defect).
- Per-jurisdiction onboarding of supervising counsel is operational overhead; the routing table must be
  maintained as law changes (e.g. the Cass. 7 May 2025 line in France).
- Litigation needs are explicitly *not* served by this lane — adherents in dispute still need their own
  advocate; chigiri only attests and routes.

**Risks**

- "Indirect benefit" is a fuzzy boundary; G15's lint hook addresses code-path coupling but cannot catch
  social quid-pro-quo. Mitigation: explicit adherent-facing notice that legal aid is gratuitous and not
  conditioned on any donation.
- US state variance is wide; the table must record state-level, not just country-level, carve-outs before
  any US matter is enabled. R0 seeds 9 jurisdictions (JP/DE/FR/UK/US/KR/AU/CA-ON/AT-CH); of these only the
  compensation-gated + advice-unreserved set (JP/DE/FR/UK/KR/AU/CA-ON-with-supervision) is `enabled`. US
  state-level granularity and AT/CH out-of-court scope ship as `verify-required` (W1 gate), not enabled.

# Alternatives Considered

1. **"Non-profit ⇒ allowed" (the raised premise)** — rejected: false in all five jurisdictions; would
   expose the corp to 非弁 (JP §72), RDG, art. 54, UPL, and Model Rule 5.5 liability.
2. **Charge a nominal fee into the Public Fund** — rejected: introduces 報酬 (JP), rémunération (FR),
   and entgeltlich character (DE), collapsing the safe harbor and risking §27 非弁提携.
3. **Software/LLM-delivered advice (drop the human lawyer)** — rejected: UPL in US even if free; also
   violates chigiri G14 and Murakumo discipline. The lawyer is constitutive, not optional.
4. **認証ADR (Japan ADR法) certified-mediation lane** — *split out into **ADR-2605302330** (2026-05-30).*
   A genuinely distinct lawful channel (express §72 carve-out for 和解仲介 by certified providers, and
   lawful 報酬 — so it does not even require gratuitousness) mapping onto chigiri's `dispute_mediation`
   cell. Kept as a separate ADR because its legal basis is certification, not gratuitousness; it reuses
   this ADR's G16 supervising-counsel mechanism for the §6-(5) 弁護士助言措置.
5. **Per-jurisdiction divergent gates** — rejected for the trust-critical path: strictest-common-denominator
   (G15+G16) keeps the gate logic single-sourced; divergence lives only in the declarative routing table.

# References

- ADR-2605262700 (chigiri legal-procedure substrate Tier-B actor R0 — G14 UPL prohibition; this ADR amends it)
- ADR-2605192115 (non-profit / donation-only / no-ads) · ADR-2605192145 (Public Fund) · ADR-2605301020 (cash≡0 in-kind doctrine)
- ADR-2605262800 (public-data legal corpus ingestion) · ADR-2605263400 (musubi covenant ceremony — chigiri pair)
- Japan — 弁護士法 §72 / §27: e-Gov 法令検索 https://laws.e-gov.go.jp/law/324AC1000000205 ; 非弁行為要件解説 https://houritsushoku.com/archives/prohibition-of-non-lawyers-from-handling-legal-services-regarding-general-legal-cases.html ; 日弁連 業際・非弁対策 https://www.nichibenren.or.jp/activity/improvement/gyosai.html
- Germany — RDG §6 (unentgeltliche Rechtsdienstleistungen): https://www.gesetze-im-internet.de/rdg/__6.html ; https://dejure.org/gesetze/RDG/6.html
- France — Loi n°71-1130 art. 54 et s.: https://www.legifrance.gouv.fr/codes/section_lc/JORFTEXT000000508793/LEGISCTA000006112891/
- England & Wales — Legal Services Act 2007 (reserved legal activities, Sch. 3): https://www.legislation.gov.uk/ukpga/2007/29 ; Legal Services Board FAQ https://legalservicesboard.org.uk/enquiries/frequently-asked-questions/reserved-legal-activities
- United States — ABA Model Rule 5.5 (UPL / MJP): https://www.americanbar.org/groups/professional_responsibility/publications/model_rules_of_professional_conduct/rule_5_5_unauthorized_practice_of_law_multijurisdictional_practice_of_law/ ; California State Bar UPL https://www.calbar.ca.gov/Public/Free-Legal-Information/Unauthorized-Practice-of-Law
- South Korea — 변호사법 §109/§34: APEC Legal Services (ROK) https://www.legalservices.apec.org/inventory/rok.html ; PILnet legal-aid memo https://www.pilnet.org/wp-content/uploads/2022/11/Legal-Aid-Memo-SOUTH-KOREA.pdf
- Australia — Legal Profession Uniform Law s.10 («fee, gain or reward» defence): https://classic.austlii.edu.au/au/legis/nsw/consol_act/lpul333/ ; Knowler & Spencer, *Unqualified Persons and the Practice of Law* https://www.austlii.edu.au/au/journals/FlinLawJl/2014/7.pdf
- Canada (Ontario) — Law Society Act + By-Law 4 (lawyer/paralegal licensing): IAALS https://iaals.du.edu/news/paralegal-regulation-ontario-canada-northern-experience
- Austria / Switzerland — Anwaltsmonopol (⚠️ out-of-court free-advice scope requires further verification before AT/CH enablement): https://de.wikipedia.org/wiki/Anwaltsmonopol
