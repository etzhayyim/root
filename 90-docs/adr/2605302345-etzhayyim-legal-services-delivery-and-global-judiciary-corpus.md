---
id: adr-2605302345-etzhayyim-legal-services-delivery-and-global-judiciary-corpus
title: "ADR-2605302345: etzhayyim.com legal-services delivery (counsel-operated, UPL-safe) + global judiciary corpus ingestion (courts/judges/case-history)"
status: proposed
doc_type: adr
topic: etzhayyim-legal-services-delivery-and-judiciary-corpus
authoritative: true
last_verified: 2026-05-30
priority: 6.7
axis: governance
weight: 0.64
priority_note: "Operationalizes real legal consultation AS etzhayyim.com and a global courts/judges/case-history ingestion corpus, while structurally preventing UPL and judge-profiling crimes. Directive: 'etzhayyim.com として実際に法的相談ができるように / fax 等と接続して全法律業務 / 全世界の裁判所・裁判官・裁判履歴を ingest'. Three hard boundaries are enforced as constitutional gates, NOT waived: (1) etzhayyim software/legal-person renders NO legal advice and performs NO reserved activity (litigation, court filing, representation, notarial) — those are a lawyer monopoly in every surveyed jurisdiction; the corp is substrate + orchestration only, all advice/representation delivered BY jurisdiction-licensed counsel (G14 + ADR-2605302200 G16). (2) The fax/email/e-filing comms gateway is COUNSEL-OPERATED: every outbound legal-act artifact is actuated by a human licensed lawyer with their own credential/signature; etzhayyim holds no signing key for any legal act (extends no-server-key ADR-2605231525) — G18. (3) Judge data: France loi 2019-222 art.33 CRIMINALLY prohibits evaluating/analyzing/comparing/predicting magistrates by identity (penalties art.226-18, up to 5y); globally, judge identity is ingested for factual reference only, NEVER profiling — G19. Ingestion is passive-only (pre-published public records, sealed/juvenile/non-public excluded — danjo G3), GDPR-pseudonymized, kotoba-EAVT-native, Murakumo-only. 'All legal work' is reframed as full-spectrum support ORCHESTRATED THROUGH counsel-of-record; the corp never becomes a law firm. Extends chigiri ADR-2605302200 / 2605302330, hanrei, and global legal corpus ADR-2605262800."
authoritative_for:
  - etzhayyim.com legal-consultation delivery architecture (counsel-operated, UPL-safe)
  - G18 counsel-operated comms gateway invariant (fax/email/e-filing; no corp signing key for legal acts)
  - G19 judge-analytics prohibition (France art.33 + global no-profiling)
  - global judiciary corpus ingestion (courts / judges / case-history) scope + gates
  - reframing of "all legal work" as counsel-orchestrated full-spectrum support
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605302200-chigiri-unpaid-legal-aid-lane-multijurisdiction
  - adr-2605302330-chigiri-japan-certified-adr-mediation-lane
related:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
supersedes: []
superseded_by: []
---

# ADR-2605302345: etzhayyim.com legal-services delivery + global judiciary corpus ingestion

**Status**: proposed
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki

# Context

Directive: make **etzhayyim.com actually provide legal consultation**; **connect fax etc. so all legal
work can be performed**; and **ingest the world's courts, judges, and case-history**.

The first and third are largely achievable. The second contains one element that **cannot** be granted as
literally stated, because it would be a crime in every surveyed jurisdiction. This ADR delivers the
achievable maximum and converts the impossible literal demand into the lawful adjacent capability, with the
boundaries written as constitutional gates rather than waived.

## What is bounded, and why (honest framing)

1. **etzhayyim software / legal-person may not practise law.** Across all jurisdictions surveyed in
   ADR-2605302200 (JP/DE/FR/UK/US/KR/AU/CA-ON/AT/CH), giving legal advice and performing *reserved
   activities* (litigation, court representation, court filing, notarial acts) is restricted to licensed
   lawyers (chigiri G14). "etzhayyim.com performs all legal work itself" = UPL. **Not grantable.**
   Achievable instead: etzhayyim.com is the **substrate + orchestration + free clinic front-end**, and a
   **jurisdiction-licensed lawyer** is the actor-of-record for every advice or reserved act. To the
   adherent this *is* "consult and get full legal help at etzhayyim.com" — the lawfulness comes from *who*
   performs the regulated act, not from hiding it.

2. **A fax / e-filing pipe is fine as transport; autonomous use of it is UPL.** Courts (incl. Japan) still
   rely on fax. A gateway is useful. But an artifact that *is* a legal act — a court filing, a 準備書面, a
   内容証明, a demand letter on the corp's behalf — drafted and transmitted *by the software without a
   lawyer* is UPL and, where it asserts representation, also a false-authority offence. **Gate:** the
   gateway is **counsel-operated** — a human licensed lawyer actuates and signs each legal-act artifact
   with their own credential. etzhayyim holds **no signing key for any legal act** (this is the existing
   no-server-key invariant, ADR-2605231525, applied to the legal surface).

3. **Judge data carries a criminal landmine.** France loi n°2019-222 du 23 mars 2019, **art. 33**, makes
   it a **crime** (penalties of Code pénal art. 226-18, up to 5 years) to reuse magistrates'/court-staff
   *identity data* in order to **evaluate, analyse, compare or predict** their professional practices —
   i.e. "judge analytics" is illegal in France. Several other systems restrict judge profiling under data
   protection law. **Gate:** judge identity is ingested for *factual reference only* (who presides where,
   role, public biography), **never** for profiling/scoring/prediction; France magistrates carry a hard
   no-analytics flag.

# Decision

Two coordinated capabilities, each fenced by constitutional gates. chigiri G14 and ADR-2605302200
G15/G16 remain in force throughout.

## Part 1 — etzhayyim.com legal-consultation delivery (counsel-operated)

### D1. The corp is substrate; counsel is the practitioner

etzhayyim.com provides: adherent intake, conflict check, matter records on MST
(`com.etzhayyim.chigiri.legalAid.*`), secure consultation channel, scheduling, document custody, and
Public-Fund-funded **routing to a jurisdiction-licensed lawyer** (ADR-2605302200 G16). The **legal advice
itself is produced by the human lawyer**, never by chigiri code or any LLM cell (G14; Murakumo discipline
applies only to non-advice assistance such as template retrieval). This realises "real consultation at
etzhayyim.com" lawfully.

### D2. G18 — Counsel-operated comms gateway invariant (CONSTITUTIONAL, IMMUTABLE)

A comms gateway (`50-infra/etzhayyim-legal-comms/`) MAY bridge fax, email, secure messaging, and
jurisdiction e-filing endpoints. But:

- Any outbound artifact that constitutes a **legal act** (court filing/postulation, 準備書面/pleadings,
  内容証明/formal notice, demand or representation letter, anything asserting authority to act for a party)
  MUST be **actuated and signed by a human lawyer licensed in the destination jurisdiction**, using *their
  own* credential. The gateway records a `counselActuation` attestation (DID-bound, per artifact).
- etzhayyim operates **no signing key, seal, or credential for any legal act** (extends no-server-key
  ADR-2605231525; the `// no-server-key: read-only` marker does NOT cover legal-act signing — there is no
  exemption here). The corp may transmit *non-legal-act* material (appointment confirmations, document
  delivery the adherent authored, scheduling) without counsel actuation.
- A lint hook `70-tools/scripts/lint/no-autonomous-legal-act.mjs` (W1) CI-blocks any code path that emits
  a legal-act artifact class without a resolvable `counselActuation`.

### D3. "All legal work" = counsel-orchestrated full-spectrum support (scope, IMMUTABLE)

The platform may *orchestrate* the full lifecycle (intake → advice → drafting → filing → representation →
resolution), but every **reserved activity** in that lifecycle is performed by the **counsel-of-record**,
not by the corp. etzhayyim never becomes a law firm, never holds itself out as entitled to practise, and
never takes a fee (G15). Non-goal, hard: autonomous (lawyer-absent) drafting/filing/representation.

## Part 2 — Global judiciary corpus ingestion (extends hanrei + ADR-2605262800)

### D4. Scope — courts, decisions, case-history (passive-only)

Ingest into kotoba-EAVT (`com.etzhayyim.judiciary.*`): (a) **court directory** — jurisdiction, instance,
competence, procedure, public contact/e-filing endpoints; (b) **judicial decisions / case-history** —
published judgments, dockets where public; (c) **judge reference** — name, court, role, official public
biography. Ingestion is **passive-only** (danjo G3): only **pre-published public records**; NO scraping
behind authentication, NO sealed / juvenile / in-camera / non-public records, NO whistleblower or private
sources. Source-provenance ≥1 public CID per record (cf. danjo G5).

### D5. G19 — Judge-analytics prohibition (CONSTITUTIONAL, IMMUTABLE)

Judge identity data is stored and served for **factual reference only** (who presides where; role; public
bio). The system MUST NOT evaluate, analyse, compare, score, rank, or predict a named judge's
practices/decisions. France magistrates carry a hard `noAnalytics=true` flag enforcing loi 2019-222 art.33
(criminal); the flag is the **global default** and may only be relaxed per-jurisdiction after explicit
legality review — never for France. A lint/query hook `lint-no-judge-profiling` blocks any aggregation
keyed on judge identity. (This mirrors danjo's non-adjudicating discipline: the corpus reports facts, it
does not profile the judiciary.)

### D6. Litigant-PII pseudonymization

Before any L1 projection / public surface, litigant and third-party PII is pseudonymized per the
source-jurisdiction rule (e.g. France art. 33 pseudonymization; GDPR; Japan 個人情報保護法). Raw records
stay in the encrypted envelope (`com.etzhayyim.encrypted.*`, ADR-2605181100) until pseudonymized.

### D7. Substrate discipline

kotoba-EAVT-native (ADR-2605262130; no Kotoba/Datomic/projection layer); Murakumo-only inference
(ADR-2605215000) for any classification/summarization of corpus text; Apache-2.0 + Charter Rider; ingestion
runs as an organism sensor (`kotodama.organism.sensors.judiciary.*`) on heartbeat cadence.

# Consequences

**Positive**
- Adherents get a real, free, full-lifecycle legal clinic *at etzhayyim.com*, lawful in every surveyed
  jurisdiction because regulated acts are performed by licensed counsel.
- A genuine fax/e-filing bridge exists for counsel to use — the practical capability the directive wanted —
  without the corp committing UPL.
- A world judiciary corpus (courts/decisions/judge-reference) powers chigiri/hanrei lookups, with the two
  criminal/data-protection landmines (UPL, judge-analytics) structurally defused.

**Negative / costs**
- Throughput bounded by counsel availability + Public Fund (by design); the platform cannot scale
  representation on software alone.
- Per-jurisdiction onboarding of licensed counsel and per-jurisdiction ingestion-legality review are real
  operational load. AT and US-state remain `verify-required` (ADR-2605302200); France judge data is
  permanently `noAnalytics`.
- Some "case-history" data is non-public in many systems and is simply excluded — the corpus is bounded by
  what is lawfully public.

**Risks**
- Drift from orchestration into autonomous practice. Mitigation: G18 + G14 + the `no-autonomous-legal-act`
  hook; counsel actuation is required at the artifact layer, not merely by policy.
- Accidental judge-profiling feature creep (e.g. "win-rate by judge"). Mitigation: G19 global default flag
  + query-layer block; France hard-locked.
- e-filing endpoints differ wildly and some prohibit third-party transmission. Mitigation: the gateway is a
  transport for *counsel's own* authenticated submission, not a corp identity at the court.

# Alternatives Considered

1. **Grant the literal request — etzhayyim.com performs all legal work, autonomous fax filing** — rejected:
   UPL in every jurisdiction; autonomous court filing also risks false-authority offences. Non-grantable.
2. **LLM-delivered legal advice (skip the lawyer)** — rejected: UPL (even free, e.g. US/California) and
   violates G14 + Murakumo discipline. The licensed human is constitutive.
3. **Full judge analytics ("which judge rules how")** — rejected: criminal in France (art.33), data-protection
   exposure elsewhere. Replaced by factual judge-reference under G19.
4. **Scrape courts live for completeness** — rejected: violates passive-ingestion (danjo G3) and many
   portals' terms; the corpus is limited to pre-published public records.
5. **Hold a corp signing credential at the court for speed** — rejected: breaks no-server-key
   (ADR-2605231525) and asserts corp authority to act = UPL. Counsel signs with their own credential.

# References

- ADR-2605302200 (chigiri 無償徹底 legal-aid lane + 10-jurisdiction matrix; G14/G15/G16) · ADR-2605302330 (Japan 認証ADR mediation lane)
- ADR-2605262700 (chigiri R0 — G14 UPL prohibition) · ADR-2605262800 (global legal corpus ingestion — extended here) · hanrei actor (case-law/judicial intelligence)
- ADR-2605231525 (no-server-key — extended to legal-act signing, G18) · ADR-2605181100 (encrypted records) · ADR-2605262130 (kotoba EAVT) · ADR-2605215000 (Murakumo-only)
- ADR-2605301600 (danjo — passive-ingestion G3 + non-adjudication, the pattern G19 mirrors)
- France — loi n°2019-222 du 23 mars 2019, art. 33 (judge-analytics criminal prohibition): Légifrance https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000038261761 ; Code pénal art. 226-18 https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037289662/2021-07-04
- UPL / reserved-activity bases per ADR-2605302200 References (JP §72 / US Model Rule 5.5 / UK LSA 2007 / etc.)
