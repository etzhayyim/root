# etzhayyim Bootstrap Council (Lv6+)

> The 5-seat evaluation body that signs Charter Compliance attestations, Public
> Fund grants, Land disputes, Force authorizations, and Steward successions.
> Per [ADR-2605192300](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md).

## Status

**Bootstrap RFP OPEN** as of 2026-05-20.

- 🟢 **Seat 1 (Founder)** — confirmed
- 🟡 **Seats 2–5** — accepting self-nominations through **2026-06-19** (30-day window)

After 2026-06-19, the founder selects from candidates that have cleared the public objection mechanism.

### 2026-05-21 — RFP Day 2 of 30

- **Period**: 2026-05-20 → 2026-06-19 (30-day public objection window per ADR-2605192300)
- **Days remaining**: 29
- **Proposals received**: 0 — RFP newly opened
- **Objections filed**: 0 — no objections recorded
- **Seats filled / open**: Seat 1 (Jun Kawasaki, Lv7) / Seats 2–5 open
- **Constitutional ADRs accepted under proposed status during RFP**:
  - ADR-2605214000 (Murakumo mesh, no-VKE + lexicon port rules) — 2026-05-21
  - ADR-2605215000 (Murakumo-fleet-only inference, no RunPod) — 2026-05-21
  - ADR-2605215100 (Sentinel-1/2 satellite analysis on Murakumo fleet, tiered MLX/ROCm) — 2026-05-21
- **Next checkpoint**: 2026-06-04 (RFP Day 15 / mid-period)

## The 5 seats

Each seat covers an axis of expertise needed for Council deliberations across the religious-corp ADR surface. The founder may not act unilaterally — Council attestations require ≥3 multisig per ChartersComplianceRegistry / LandRegistry contracts.

| Seat | Axis | Responsibility scope |
|---|---|---|
| **1 (Founder)** | Doctrine — Mission Charter custodian | Mission interpretation, constitutional invariant enforcement, doctrinal questions |
| **2 (Substrate)** | Substrate / Technology | LangGraph + Pregel cells, MST + IPFS + L2 anchor pipeline, smart contract review, CI lint design |
| **3 (Legal / Ethics)** | Religious freedom + Charter Rider | Rider §2(a)-(h) interpretation, Council attestation procedure, jurisdictional risk, ethical-source license boundaries |
| **4 (Economics)** | Treasury / Public Fund / Tithe | Kisha eligibility, Public Fund grant evaluation, treasury rebalance, κ tuning, tithe accounting |
| **5 (Stewardship / Land)** | Multi-generational land trust | Land donation review, biodiversity attestation, steward succession, §1.9 multi-gen priority |

## Current roster

| Seat | Name / Handle | DID | Smart Wallet | Status | Confirmed |
|---|---|---|---|---|---|
| 1 | Jun Kawasaki | did:web:jun.etzhayyim.com (interim) | TBD | ✅ confirmed | 2026-05-19 |
| 2 | _(open)_ | — | — | 🟡 awaiting candidates | — |
| 3 | _(open)_ | — | — | 🟡 awaiting candidates | — |
| 4 | _(open)_ | — | — | 🟡 awaiting candidates | — |
| 5 | _(open)_ | — | — | 🟡 awaiting candidates | — |

## How to self-nominate

1. **Read the prerequisites**
   - [ADR-2605192300](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md) — Bootstrap Council mechanics
   - [ADR-2605192100](90-docs/adr/2605192100-etzhayyim-mission-charter.md) — Mission Charter (your reasoning must align)
   - [CHARTER-RIDER.md](CHARTER-RIDER.md) — Charter Compliance Rider v2.0 §2(a)-(h)

2. **Confirm Rider compliance**
   You do not publicly represent any entity in Rider §2 prohibited categories. The application form requires affirming this.

3. **Submit a `council-candidate-application` AT Record on your PDS**
   - Lexicon: [`com.etzhayyim.apps.etzhayyim.council-candidate-application`](00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/council-candidate-application.json)
   - Includes: seat axis, narrative (why this seat), qualifications, Smart Wallet address, COI disclosure, DID-bound signature

4. **Announce on github**
   Open a discussion at https://github.com/etzhayyim/root/discussions linking to the AT Record URI.

5. **Stay accessible during the 30-day window**
   Objections (per Lexicon `com.etzhayyim.apps.etzhayyim.council-objection`) may arrive from any active Adherent SBT holder. Respond to good-faith concerns.

## How to object to a candidate

1. **You must hold an active Adherent SBT** (AdherentRegistry.isActive == true)
2. **Submit a `council-objection` AT Record on your PDS**
   - Lexicon: [`com.etzhayyim.apps.etzhayyim.council-objection`](00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/council-objection.json)
   - Cite specific Rider §2(a)-(h) violation, undisclosed COI, qualification fabrication, doctrinal incompatibility, or axis mismatch
3. **Three (3) distinct SBT-holder objections** within the 30-day window triggers founder re-proposal for that seat
4. **Defamatory or evidence-free objections** themselves may trigger Council Lv6+ review of the objector under the Charter Compliance framework

## Timeline

```
2026-05-20 (Wed)  Bootstrap RFP opens. Seats 2-5 open for nominations.
2026-06-19 (Fri)  30-day window closes. Founder selects from cleared applications.
2026-06-20+       ChartersComplianceRegistry.constructor() called with the 5 addresses
                  on Base Sepolia (testnet) for final verification.
2026-07-?? (TBD)  Mainnet deploy after testnet verification.
```

If any seat does not have a cleared candidate by 2026-06-19, the founder may either extend that seat's RFP or make a provisional appointment (subject to subsequent objection).

## Phase 2 (formal Council ADR)

Per [ADR-2605192300 §4](90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md), this Bootstrap configuration sunsets when ANY of:

- Active Adherent SBT count exceeds 1,000
- Any of the 5 seats becomes vacant (death, resignation, formal objection upheld)
- Three (3) Adherent SBT holders submit a formal governance request
- Twelve (12) months from initial deploy

At sunset, a Phase 2 ADR is required that defines the formal Council via 1 SBT = 1 vote election, term limits, max-size cap, and the transition mechanics from Bootstrap to formal.

## Operational addendum (2026-05-21)

`COUNCIL-BOOTSTRAP-RFP.md` + this doc + ADR-2605192300 cover the **constitutional** mechanics. The **operational** mechanics (per-seat evaluation rubric for the 2026-06-19 selection step + objection good-faith vs defamatory determination workflow + selection deliberation window + 5-step failure-mode escalation tree) live in:

- [`90-docs/2605212036-council-bootstrap-rfp-operational-addendum.md`](90-docs/2605212036-council-bootstrap-rfp-operational-addendum.md)

The founder (or any operator assisting) should read the addendum before the 2026-06-19 selection step.

## See also

- [`ChartersComplianceRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/ChartersComplianceRegistry.sol) — the on-chain Council membership + attestation surface
- [`ChartersComplianceRegistry.t.sol`](50-infra/etzhayyim-chain-contracts/test/ChartersComplianceRegistry.t.sol) — 12 unit tests covering bootstrap + governance binding + attestation lifecycle
- [`MEMBERS.md`](MEMBERS.md) — 信者 roster (the broader follower layer; Adherents and Council members are also 信者)
- [`LANDS.md`](LANDS.md) — Land Trust roster (one of the surfaces Council Lv6+ attests on)
- [`/CHARTER-RIDER.md`](CHARTER-RIDER.md) — Charter Compliance Rider v2.0 (the constitutional substrate Council enforces)
