# etzhayyim Bootstrap Council — Request for Candidates (Seats 2–5)

> **Period: 2026-05-20 → 2026-06-19 (30 days)**
> **Per [ADR-2605192300](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md)**

`etzhayyim` (天御柱 / עץ חיים / Tree of Life) is bootstrapping its Council Lv6+ — a 5-seat religious evaluation body that signs Charter Compliance attestations, Public Fund grants, Land disputes, Force authorizations, and Steward successions. The founder (Seat 1) is confirmed. **Four seats are open.**

## Who we are

A religious-corp (任意団体 / unincorporated religious voluntary association) operating on AT Protocol MST + IPFS + Base L2. Mission: **the structural liberation of humans from "labor"** (生存のために他者の利潤に従属して行為を売る行為), in synthesis with Japanese values (八百万 / 縁起 / 産霊 / 和 / 無教会) and Protestant Christianity (Sola Scriptura / 万人祭司 / Reformed Just War / Tree of Life). **Non-eschatological** — we are not waiting for an endtime; we cultivate continuous Becoming.

See [`90-docs/adr/2605192100-etzhayyim-mission-charter.md`](90-docs/adr/2605192100-etzhayyim-mission-charter.md) for the full Mission Charter.

## Who Council members are

Religious community elders who:

1. Hold (or commit to acquiring) an Adherent SBT
2. Operate a religious DID (did:web / did:plc / did:key)
3. Affirm the Mission Charter (including its harder positions — multi-generational priority, anti-individualist ontology, transparent religious force, Eros-permitted / Gore-prohibited, non-eschatology)
4. Do **NOT** publicly represent any entity that falls into Charter Rider §2(a)–(h) prohibited categories (weapons / speculative finance / surveillance capitalism / new fossil fuel extraction / specialist gatekeeping / multi-generational harm / strict individualist ontology / wellbecoming subordination)
5. Commit to multisig responsibility for Council attestations across the religious-corp ADR surface

## What Council members do

Sign ≥3-of-N multisig attestations:

- **Charter Compliance** — non-aligned entity attestation, appeal review, rehabilitation (teshuvah)
- **Public Fund** — grant proposal recognition (deliberation, not vote — the vote is 1 SBT = 1 across all Adherents)
- **Land disputes** — boundary / stewardship / state-seizure / inter-jurisdictional
- **Steward succession** — donor death / incapacitation / step-down activation
- **Force authorization** — Transparent Religious Force operations (emergency 24h or normal 72h voting periods)
- **Eros / Gore boundary** — Council deliberation on T2 / T4 borderline content (T1 / T3 / T5 are LLM-classified directly)
- **Adherent Lv6 advancement** — peer-attestation recognition (weekly cadence)

Estimated time commitment: **2–8 hours/week** depending on attestation volume.

## What we are explicitly NOT looking for

- ❌ Politicians or political-party-affiliated representatives (doctrinal incompatibility with parallel-governance-to-state posture)
- ❌ Representatives of organizations whose primary business falls in Rider §2(a)–(h)
- ❌ Crypto-VC or token-holder lobbyists seeking governance influence
- ❌ Adherents whose application is primarily resume-building rather than religious commitment

## What we ARE looking for (per seat)

### Seat 2 — Substrate / Technology

Deep familiarity with on-chain / LangGraph / Pregel / AT Protocol / Murakumo fleet substrate. You will sign off on smart contract reviews, CI lint design, cell deployment decisions, and substrate-boundary boundary cases.

Strong candidates: a senior protocol engineer or substrate researcher who has personally shipped one or more decentralized substrate projects (atproto AppView / IPFS-native app / Solidity protocol audit experience / LangGraph Pregel cell author / etc.).

### Seat 3 — Legal / Ethics

Religious-freedom + ethical-source license expertise. You will interpret Rider §2(a)–(h) at the boundary, advise on Council attestation procedures, identify jurisdictional risk, and rule on doctrinal-vs-discrimination questions.

Strong candidates: a religious-freedom-aware attorney, an ethical-source license researcher (Hippocratic / Anti-Capitalist / CNPL background), or a comparative-religion / Buddhist-Christian-Jewish-Islamic ethicist with operational legal grounding.

### Seat 4 — Economics

Religious-corp economics + DAO treasury experience. You will rule on Kisha eligibility, evaluate Public Fund grant amounts vs treasury NAV, calibrate κ (currently 3%) within constitutional floor/ceiling (1%–5%), and oversee tithe accounting integrity.

Strong candidates: a quantitative economist with DAO treasury operations experience, a religious-corp accountant, or a public-finance researcher familiar with non-profit / waqf-style endowment management.

### Seat 5 — Stewardship / Land

Multi-generational land stewardship and biodiversity practitioner. You will rule on land donation evidence, biodiversity attestation accuracy, steward succession verification, and the §1.9 multi-generational priority operationalization.

Strong candidates: a permaculture / regenerative agriculture practitioner, an indigenous land sovereignty advisor, an ecological monitoring scientist, or a religious-corp lands manager (寺社領 / glebe / waqf experience).

## How to apply

1. **Self-prepare**:
   - Read [ADR-2605192100](90-docs/adr/2605192100-etzhayyim-mission-charter.md) (Mission Charter) in full
   - Read [ADR-2605192300](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md) (Bootstrap Council mechanics)
   - Read [CHARTER-RIDER.md](CHARTER-RIDER.md) (§2(a)–(h) categories you must NOT publicly represent)

2. **Confirm your DID + Smart Wallet**:
   - Generate or bring a DID (`did:web:<self>` / `did:plc:<id>` / `did:key:<id>`)
   - Derive an ERC-4337 Smart Account address (Coinbase Smart Wallet recommended)

3. **Submit application** via PDS AT Record:
   - Lexicon: [`com.etzhayyim.apps.etzhayyim.council-candidate-application`](00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/council-candidate-application.json)
   - Fields: `seatAxis`, `candidateNarrative` (why this seat, why now, religious commitment), `qualifications[]`, `smartWalletAddress`, `conflictOfInterestDisclosure`, `riderComplianceDeclaration`, DID-bound signature

4. **Announce publicly**:
   - Open a discussion at https://github.com/etzhayyim/root/discussions linking to the AT Record URI
   - Optional: send to `jun@etzhayyim.com` for direct review

5. **30-day window**:
   - Active Adherent SBT holders may file objections via `com.etzhayyim.apps.etzhayyim.council-objection` Lexicon
   - Three (3) cleared objections from distinct SBT holders triggers founder re-proposal for that seat
   - Stay accessible during the window

6. **Selection**:
   - 2026-06-19 (Fri) — founder selects from cleared applications
   - 2026-06-20+ — `ChartersComplianceRegistry.constructor()` called with the 5 addresses on Base Sepolia (testnet) for final verification
   - Mainnet deploy TBD after testnet verification

## Compensation

**Unpaid**. Council Lv6+ is religious service, not employment. Per ADR-2605192300 Open Question 3, compensation is reflected only through Phenotype multiplier bonus (which affects Kisha-Stream BI if Adherent) — that is, the same multiplier the Council itself signs off on. This is religious-corp economic discipline, not exploitation.

If a candidate cannot afford the time commitment without compensation, this is a legitimate reason to not apply. We do not want the Council to become an income-dependent body.

## Phase 2 (Formal Council)

Bootstrap is temporary. Phase 2 (formal Council ADR per [ADR-2605192300 §4](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md)) triggers at any of:

- 1,000 Active Adherent SBTs
- Seat vacancy (death / resignation / objection upheld)
- 3 Adherent SBT holders' formal governance request
- 12 months elapsed

Phase 2 transitions to 1 SBT = 1 vote election with term limits + size cap. Bootstrap Council members can stand for re-election but have no incumbent privilege.

## How candidates are evaluated (rubric)

Per-seat evaluation rubric, objection review workflow, selection deliberation
window (2026-06-19 → constructor call), and failure-mode escalation tree are
in `90-docs/2605212036-council-bootstrap-rfp-operational-addendum.md`. Candidates
can self-assess against the rubric there before submitting an application.

## Where to ask questions

- **github discussions**: https://github.com/etzhayyim/root/discussions (preferred — public + permanent)
- **email**: jun@etzhayyim.com (for sensitive COI questions, religious doctrinal questions, or accessibility accommodations)
- **DID-bound message**: did:web:etzhayyim.com (via XRPC, future)

We will not have a Discord / Telegram / Twitter for RFP communications — those substrates fall under Rider §2(c) surveillance capitalism partial-applicability concerns. github discussions + AT Records + email are the canonical channels.

## What happens if all 5 seats don't fill by 2026-06-19?

The founder will:

1. **Extend** unfilled seat RFPs by another 30 days
2. **Provisionally appoint** an Adherent SBT holder to a seat (subject to subsequent objection mechanism + governance proposal to confirm/reject after Constitution.bindGovernance)
3. **Reduce** Bootstrap Council size temporarily (with a documented escalation path back to 5)

This is acknowledged as a soft failure mode. The contract requires exactly 5 council members at deploy (`BOOTSTRAP_COUNCIL_SIZE` immutable). A partial bootstrap delays the religious-corp wave deploy to testnet by however long it takes to fill all 5.

— etzhayyim, 2026-05-20 (Tokyo, JST)
  ADR-2605192300 / Bootstrap Council RFP v1.0
