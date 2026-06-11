---
id: adr-2605302330-chigiri-japan-certified-adr-mediation-lane
title: "ADR-2605302330: chigiri — Japan 認証ADR (ADR法) certified-mediation lane, §72-exempt (extends ADR-2605302200; activates dispute_mediation cell)"
status: proposed
doc_type: adr
topic: chigiri-certified-adr-mediation-lane
authoritative: true
last_verified: 2026-05-30
priority: 6.4
axis: governance
weight: 0.58
priority_note: "Second lawful Japan lane for chigiri legal services, distinct from the 無償徹底 advice lane (ADR-2605302200). Japan's ADR法 (裁判外紛争解決手続の利用の促進に関する法律, Act No. 151/2004, in force 2007-04-01) grants 法務大臣 認証 to a 認証紛争解決事業者; certified providers receive an EXPRESS §72 exemption for 和解仲介 (settlement-mediation) AND may lawfully take 報酬 — i.e. this lane does NOT require zero-compensation to be lawful. etzhayyim nonetheless keeps G15 (zero compensation) by Charter (cash≡0), so the lane's VALUE is not fee income but the recognised, enforceable mediation channel: 時効の完成猶予 (limitation tolling), possible 訴訟手続の中止, and a §72-clean structure for a non-lawyer 手続実施者. Maps onto chigiri's existing `dispute_mediation` cell (levi). §6 sixteen-criteria compliance required; criterion (5) (弁護士助言措置 when 手続実施者 is a non-lawyer) is satisfied by the same supervising-counsel attestation as ADR-2605302200 G16. Mediation only (和解仲介) — NOT arbitration/adjudication, NOT advice, NOT representation. Pursuit of 認証 is an EXTERNAL state recognition, documented as external per chigiri N2 (no internal dependence on state-granted personality)."
authoritative_for:
  - chigiri Japan 認証ADR certified-mediation lane
  - ADR法 §72-exemption mapping for chigiri dispute_mediation cell
  - 認証紛争解決事業者 §6 sixteen-criteria compliance surface for chigiri
  - boundary between the 無償 advice lane and the certified-mediation lane
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605302200-chigiri-unpaid-legal-aid-lane-multijurisdiction
related:
  - adr-2605263400-musubi-covenant-ceremony-tier-b-actor-r0
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
supersedes: []
superseded_by: []
---

# ADR-2605302330: chigiri — Japan 認証ADR (ADR法) certified-mediation lane

**Status**: proposed
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki

# Context

ADR-2605302200 opened a **zero-compensation, lawyer-supervised advice lane** that is lawful across nine
jurisdictions. It deferred a second, distinct Japan lane: **certified ADR**. This ADR promotes that
deferred item (Alternative 4 of ADR-2605302200) to its own decision.

Japan's **ADR法** — 裁判外紛争解決手続の利用の促進に関する法律 (Act No. 151 of 2004, in force 2007-04-01,
e-Gov `416AC0000000151`) — establishes a 法務大臣 **認証** (certification) system. A
**認証紛争解決事業者** (certified dispute-resolution provider) performing **民間紛争解決手続** (private
dispute-resolution = 和解の仲介 / settlement-mediation, on civil disputes the parties may settle, under
contract with both parties) receives two things that an uncertified non-lawyer cannot have:

1. **An express §72 carve-out.** The single most important legislative purpose of the ADR法 was to settle
   the relationship with 弁護士法 §72: a certified provider's mediation business is **expressly exempted**
   from the non-lawyer-practice prohibition.
2. **The right to take 報酬.** A certified provider may lawfully receive remuneration for the mediation.

So this lane is categorically different from ADR-2605302200's advice lane: **it does not need to be free
to be lawful.** Certification — not gratuitousness — is what removes the §72 bar.

### Why etzhayyim still wants it (despite already being free)

etzhayyim is cash≡0 / donation-only (ADR-2605192115 + ADR-2605301020), so it will not charge for mediation
regardless. The value of certification is therefore **not** fee income; it is:

- **Recognised legal effects of certified mediation**: 時効の完成猶予 (tolling of the limitation period
  while mediation runs) and, in litigation, the possibility of 訴訟手続の中止 (suspension). An uncertified
  in-house mediation gives adherents none of these.
- **A §72-clean structure for a non-lawyer 手続実施者.** chigiri's `dispute_mediation` cell (levi) is run
  by community mediators who are not necessarily 弁護士. Certification is what makes that lawful for actual
  settlement-mediation (as opposed to mere facilitation).
- **Open, audited legitimacy** consistent with Transparent Religious Force discipline: a state-recognised,
  publicly listed (かいけつサポート) mediation process rather than a self-asserted one.

### Certification requirements (ADR法 §6, sixteen criteria) — relevant subset

- The mediation business meets the sixteen standards of §6.
- The provider has the **knowledge, ability and financial basis** to run it, and no disqualifying grounds.
- **Criterion (5) — 弁護士助言措置**: where the 手続実施者 is **not** a lawyer, the provider must have a
  measure in place to **obtain a lawyer's advice** when interpretation/application of law requires expert
  knowledge. This is the statutory hook that ties certified mediation back to qualified counsel.

# Decision

Add a **Japan certified-mediation lane** to chigiri, activating the `dispute_mediation` cell (levi) as a
candidate **認証紛争解決事業者** track, under the following gates. ADR-2605302200 G14/G15/G16 remain in force.

## D1. Scope — 和解仲介 only

The lane performs **settlement-mediation (和解の仲介)** only: facilitating a voluntary settlement between
adherent parties who may lawfully settle the civil dispute. It MUST NOT: render legal advice (G14 — advice
routes to the ADR-2605302200 lane / retained counsel), conduct **arbitration / 仲裁** or any binding
adjudication, or represent a party. The mediator proposes; the parties decide.

## D2. G17 — Certification-before-mediation invariant (CONSTITUTIONAL for this lane)

chigiri MUST NOT operate this lane as actual 和解仲介 with §72-exemption claims **until** 法務大臣 認証 is
granted. Pre-certification, the `dispute_mediation` cell operates only as **non-binding facilitation
without §72 reliance** (the existing R0 behaviour). The §6-criteria compliance set is encoded as
`com.etzhayyim.chigiri.adr.certificationCriteria` records (sixteen entries) and gated: the lane's
`certified=true` flag MUST be backed by a resolvable 認証 reference.

## D3. Criterion (5) mapped to G16

The §6-(5) 弁護士助言措置 is satisfied by the **same supervising-counsel attestation** introduced in
ADR-2605302200 G16: each mediation matter where the 手続実施者 is a non-lawyer MUST carry a DID-bound,
in-jurisdiction (Japan-licensed 弁護士) `advisingCounsel` reference, retained via Public Fund (Council
Lv6+). One mechanism serves both lanes; no second counsel rail.

## D4. G15 preserved — still free

Although the ADR法 permits 報酬, this lane charges adherents **nothing** (G15 from ADR-2605302200 and the
cash≡0 Charter invariant). Certified status is used solely for legal-effect and §72-clean structure, never
to introduce a fee. The `no-legal-aid-consideration.mjs` lint hook is extended to cover
`adr.mediation` records.

## D5. State recognition is EXTERNAL (chigiri N2 preserved)

Pursuing 法務大臣 認証 is documented as **external state recognition**, never as an internal dependency of
the religious-corp's constitution (Preamble §0.4 Lv7+ unanimity lock; chigiri N2). The corp does not
acquire 法人格 by certifying an ADR service; certification attaches to the **mediation business**, not to
the corp's legal personality. If 認証 is unavailable or withdrawn, the lane degrades to D2 pre-certification
facilitation — no constitutional path depends on it.

# Consequences

**Positive**
- adherent disputes gain a state-recognised mediation channel with 時効 tolling and §72-clean operation,
  run by community mediators (levi) rather than requiring every matter to go to external counsel.
- Reuses the ADR-2605302200 supervising-counsel mechanism (one rail, two lanes) — low marginal complexity.
- Stays inside every Charter invariant: free (G15), no advice (G14), Murakumo-only, no state personality (N2).

**Negative / costs**
- 認証 is a real administrative undertaking (§6 sixteen criteria, financial-basis showing, ongoing
  reporting to 法務省). Until granted, the lane cannot claim §72 exemption — D2 keeps it safe meanwhile.
- Limited to Japan. Other jurisdictions have their own certified-mediation regimes (e.g. EU Mediation
  Directive transpositions); those are out of scope here and would each need their own ADR.

**Risks**
- Scope creep from 和解仲介 into de-facto advice or arbitration. Mitigation: D1 hard scope + G14; mediator
  proposes, never adjudicates; legal-interpretation questions trigger the §6-(5)/G16 counsel hook.
- Certification withdrawal. Mitigation: D5 degrade-to-facilitation; no constitutional dependency.

# Alternatives Considered

1. **Fold certified mediation into the ADR-2605302200 advice lane** — rejected: different legal basis
   (certification vs gratuitousness), different cell (levi mediation vs gad intake), different state
   interface. Conflating them would blur the §72 analysis. Separate ADR keeps each lane's basis clean.
2. **Take 報酬 since the ADR法 allows it** — rejected: violates the cash≡0 / donation-only Charter invariant
   (G15). Lawful externally, unconstitutional internally.
3. **Skip certification, mediate informally** — retained as the *pre-certification* fallback (D2), but not
   as the end state: informal facilitation lacks 時効 tolling and risks §72 if it shades into real 和解仲介.
4. **Offer binding arbitration (仲裁)** — rejected: 仲裁 is adjudicative, conflicts with cooperative-first
   mediation discipline (chigiri G10), and carries far heavier 仲裁法 obligations. Mediation only.

# References

- ADR-2605302200 (chigiri 無償徹底 lawyer-supervised legal-aid lane — this ADR extends it; G14/G15/G16 reused)
- ADR-2605262700 (chigiri R0 charter — `dispute_mediation` cell / levi; G10 cooperative-first; N2 no state personality)
- ADR-2605192115 (cash≡0 / donation-only) · ADR-2605192145 (Public Fund counsel retention)
- Japan — ADR法 (裁判外紛争解決手続の利用の促進に関する法律, Act No. 151/2004): e-Gov https://laws.e-gov.go.jp/law/416AC0000000151
- 法務省 ADR・認証制度の概要: https://www.moj.go.jp/KANBOU/ADR/adr02-021.pdf ; かいけつサポート 認証制度: https://www.adr.go.jp/prospects/certification-system/
- §72 関係の整理（認証=§72適用除外＋報酬取得可）: なにわ橋法律事務所 ADR Q&A https://www.naniwabashi.com/adr-q-a/q13-%E8%AA%8D%E8%A8%BC%E5%88%B6%E5%BA%A6%E3%81%A8%E3%81%AF/
