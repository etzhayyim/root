---
id: doc-2605212036-council-bootstrap-rfp-operational-addendum
title: "Council Bootstrap RFP — operational addendum (selection rubric + objection workflow + deliberation window + failure modes)"
status: active
doc_type: how-to
topic: council-bootstrap-rfp-operational-addendum
authoritative: true
last_verified: 2026-05-21
priority: 7.5
axis: governance
weight: 0.60
priority_note: "Fills the operational gaps in COUNCIL-BOOTSTRAP-RFP.md + COUNCIL.md + ADR-2605192300: (1) per-seat candidate evaluation rubric for the founder's 2026-06-19 selection step, (2) objection review workflow (good-faith vs defamatory), (3) selection deliberation window (2026-06-19 → constructor call), (4) failure modes (0 candidates / blanket objections / deadlock). Operational only — does not change the constitutional decisions in ADR-2605192300, just makes them executable."
authoritative_for:
  - per-seat candidate evaluation rubric (Seat 2/3/4/5)
  - objection good-faith vs defamatory determination procedure
  - selection deliberation window (2026-06-19 → 2026-06-20+ constructor call)
  - failure modes + escalation paths
depends_on:
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - COUNCIL.md
  - COUNCIL-BOOTSTRAP-RFP.md
  - CHARTER-RIDER.md
supersedes: []
superseded_by: []
---

# Council Bootstrap RFP — operational addendum

**Date**: 2026-05-21
**Tracking**: COUNCIL-BOOTSTRAP-RFP.md (30-day window 2026-05-20 → 2026-06-19)
**Scope**: Operational mechanics. Does NOT change constitutional decisions in
ADR-2605192300; just makes the 2026-06-19 selection step executable.

## Why this addendum exists

The RFP doc says "founder selects from cleared applications" on 2026-06-19. The
COUNCIL.md doc says "respond to good-faith concerns" during the window. Neither
specifies HOW. This addendum fills 4 specific gaps that the founder (or any
operator reviewing candidates) needs answered before the deadline:

1. **Per-seat evaluation rubric** — what does "strong candidate" actually mean
   for Seat 2 vs Seat 3 vs Seat 4 vs Seat 5?
2. **Objection review workflow** — how is "good-faith" vs "defamatory or
   evidence-free" determined?
3. **Selection deliberation window** — what happens between 2026-06-19
   (window closes) and 2026-06-20+ (constructor call)?
4. **Failure modes** — what concrete action does the founder take if 0
   candidates clear, or all candidates get 3+ objections, or seats deadlock?

## §1 Per-seat evaluation rubric

The founder scores each candidate on a 0-3 scale across 4 dimensions. A score
of ≥9/12 is the de facto "strong candidate" threshold. Tie-breakers go to
diversity-of-background + multi-jurisdictional reach + religious commitment
visibility.

### Common dimensions (all 4 seats)

| Dimension | 0 (absent) | 1 (claimed) | 2 (demonstrable) | 3 (peer-validated) |
|-----------|-----------|-------------|-------------------|---------------------|
| **Religious commitment** | No religious affiliation, treats this as a tech/legal/economics role | Self-identifies as religious but no public practice | Public religious practice (community membership, regular ritual, study) for ≥2 years | Recognized in their tradition (ordained / commissioned / cited by peers as a religious-corp-equivalent figure) |
| **Charter Rider §2 compatibility** | Currently a primary employee / officer of an entity in §2(a)-(h) | Past §2 involvement, current clean | No §2 involvement in past 24 months | Public record of declining §2-adjacent work on stated religious / ethical grounds |
| **Multi-jurisdictional reach** | Single jurisdiction, no cross-border experience | Bilingual or has lived in 2+ jurisdictions | Operationally active across 2+ jurisdictions (current consulting / projects / publications) | Recognized in 3+ jurisdictions, including at least one non-OECD |
| **Time commitment realism** | Time budget unrealistic given other obligations (likely to ghost) | Has time but no risk-mitigation if circumstances change | Has time + identified a backup / co-reviewer arrangement | Time + backup + explicit "I will not run for re-election in Phase 2" commitment (reduces incumbent-power risk) |

### Seat 2 — Substrate / Technology (axis-specific)

| Dimension | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| **Shipped decentralized substrate** | Only ships SaaS / centralized infrastructure | Has experimented with decentralized projects but not shipped | Has shipped 1 non-trivial decentralized substrate (AT Protocol AppView / IPFS-native app / Solidity protocol audit / LangGraph Pregel cell author / etc.) | Multiple shipped substrate projects + maintains active relationships with at least one core protocol team |
| **CI lint / quality discipline** | No public artifact | Public repos have some CI | Public repos have lint hooks + security scan + smoke tests | Has authored / maintained CI tooling that other projects adopted |

**Seat 2 minimum**: ≥2 on "Shipped decentralized substrate". A candidate scoring
1 here is not yet ready; recommend re-application in Phase 2 after they have
shipped.

### Seat 3 — Legal / Ethics

| Dimension | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| **Religious-freedom legal grounding** | No legal background | Law degree, no religious-freedom specialty | Religious-freedom-adjacent practice (constitutional / first amendment / international religious freedom / 信教の自由) for ≥5 years | Recognized published work + has counseled at least one religious organization through a substantive religious-freedom dispute |
| **Ethical-source license fluency** | Never read CNPL / Hippocratic / Anti-Capitalist licenses | Read them, doesn't recommend them | Has counseled clients toward ethical-source license adoption | Has authored / maintained an ethical-source license OR cited as expert in license design |

**Seat 3 minimum**: ≥2 on either "Religious-freedom legal grounding" OR
"Ethical-source license fluency" (not both — finding both in one candidate
is rare). The other dimension can be ≥1.

### Seat 4 — Economics

| Dimension | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| **DAO treasury operations** | No DAO / treasury experience | Holds tokens, no operational role | Has served as treasury committee / multisig signer for ≥1 DAO ≥6 months | Has designed treasury policy / κ-tuning equivalents OR is the explicit treasury lead of a recognized DAO |
| **Non-profit / waqf / endowment fluency** | None | Familiar with non-profit accounting basics | Has audited or run a non-profit endowment | Recognized practitioner in non-profit / religious-corp / waqf finance |

**Seat 4 minimum**: ≥2 on either "DAO treasury operations" OR "Non-profit /
waqf / endowment fluency". The other ≥1.

### Seat 5 — Stewardship / Land

| Dimension | 0 | 1 | 2 | 3 |
|-----------|---|---|---|---|
| **Hands-on land practice** | No land work | Hobbyist / home garden | Active permaculture / regenerative agriculture / indigenous-land-sovereignty / ecological monitoring practitioner ≥3 years | Recognized practitioner with peer / institutional acknowledgment |
| **Religious-land synthesis** | No religious lens on land | Personal religious framing of land work | Public writing / teaching that connects religious tradition + land stewardship | Has shaped a religious-corp / 寺社領 / glebe / waqf land program |

**Seat 5 minimum**: ≥2 on "Hands-on land practice". "Religious-land synthesis"
can be ≥1.

### Aggregate scoring

```
Score = common_dimensions_sum + seat_specific_dimensions_sum

Common max: 4 × 3 = 12
Seat 2 specific max: 2 × 3 = 6  → Seat 2 aggregate max = 18
Seat 3 specific max: 2 × 3 = 6  → Seat 3 aggregate max = 18
Seat 4 specific max: 2 × 3 = 6  → Seat 4 aggregate max = 18
Seat 5 specific max: 2 × 3 = 6  → Seat 5 aggregate max = 18

Strong-candidate threshold: ≥13/18 (≈72%)
```

The threshold is **not** automatic — it's a discussion anchor. The founder
documents the score + rationale in the selection AT Record per §3 below.

## §2 Objection review workflow

The COUNCIL.md says "3 cleared objections triggers re-proposal" but doesn't
specify how an objection is judged cleared (good-faith) vs uncleared
(defamatory / evidence-free). This is the procedure:

### Step 2.1 — Receive

An objection arrives as `com.etzhayyim.apps.etzhayyim.council-objection` AT Record
during the 30-day window. The objector MUST hold an active Adherent SBT
(checked via `AdherentRegistry.isActive(did) == true`). Objections from
non-Adherents are filed but not counted.

### Step 2.2 — Categorize

Each objection cites one of 5 grounds (per the Lexicon):

| Ground | Burden of evidence |
|--------|---------------------|
| **A. Rider §2(a)–(h) violation** | A specific entity name + role + date range + public-record citation (LinkedIn / press release / company website snapshot). Hearsay does not clear |
| **B. Undisclosed COI** | A specific overlap between the candidate's stated qualifications and an undisclosed financial / employment / familial tie to a party that would benefit from the candidate's Council attestation |
| **C. Qualification fabrication** | A specific claim in the application + counter-evidence that the claim is materially false (not just exaggerated) |
| **D. Doctrinal incompatibility** | A specific Mission Charter clause + a specific candidate public statement contradicting it |
| **E. Axis mismatch** | The candidate's expertise does not match the seat (e.g. Seat 5 candidate with no land practice). Note: this is a soft objection — the founder may still select with the score < threshold |

### Step 2.3 — Judge

The founder reviews each objection within 7 days of receipt:

- **Cleared** (counts toward the 3-objection threshold) if: cites a specific
  ground + provides at least 1 evidence link + the evidence is verifiable
  by a third party.
- **Uncleared** if: vague, repeats prior cleared objections (the same fact
  asserted by multiple objectors counts as 1 unless the new objector
  contributes new evidence), purely opinion-based, or invokes a ground the
  Lexicon does not enumerate.
- **Defamatory** if: includes factually false statements about the candidate,
  or invokes characteristics protected from religious-corp adverse action
  (race, sexuality, etc.) without an evidence link to actual §2 conduct.

### Step 2.4 — Record

For each judged objection, the founder writes a public reply AT Record
(`com.etzhayyim.apps.etzhayyim.council-objection-disposition`) within 7 days:

- Cleared objections list cited evidence
- Uncleared objections explain why (1-2 sentences, no need to defame the
  objector)
- Defamatory objections trigger Council Lv6+ review of the objector
  (per existing CHARTER-RIDER.md / current draft Council attestation flow)

The candidate may submit a reply AT Record within 7 days of the
disposition, which the founder reads but does not act on unless it reveals
new information.

### Step 2.5 — Threshold

3 cleared objections (from 3 distinct Adherent SBT holders, with distinct
evidence — same objector can't trigger threshold by themselves) → founder
re-proposes the seat with a different candidate. Counter starts fresh for
the new candidate.

## §3 Selection deliberation window (2026-06-19 → 2026-06-20+)

The RFP doc says window closes 2026-06-19 (Fri) and constructor is called
2026-06-20+. In practice the founder may need more than 1 day to:

1. Finalize per-seat scoring spreadsheet (~2 hours per seat × 4 seats = 8 hours)
2. Write public selection rationale per seat (~1 hour per seat = 4 hours)
3. Coordinate Smart Wallet address handoff with selected candidates (varies
   per candidate's wallet readiness — could be hours or days)
4. Final §2 / COI re-audit on selected candidates the day before constructor
   call (~1 hour per seat = 4 hours)

**Realistic timeline**:

```
2026-06-19 (Fri)    18:00 JST    RFP window closes; no new applications accepted
2026-06-19 (Fri)    18:00–23:00  Founder reviews all cleared applications + scores
2026-06-20 (Sat)    morning       Founder writes per-seat rationale AT Records
2026-06-20 (Sat)    afternoon     Notify selected candidates; collect Smart Wallet addrs
2026-06-21 (Sun)    daytime       Selected candidates confirm by signed AT Record
2026-06-22 (Mon)    morning       Final §2/COI re-audit
2026-06-22 (Mon)    daytime       ChartersComplianceRegistry.constructor() on Base Sepolia
2026-06-22 (Mon)    evening       Public announcement (AT Record + GitHub discussion)
```

If any selected candidate fails the final re-audit (Step 6), the founder may
substitute the next-highest-scoring cleared applicant for that seat OR
escalate to a failure mode (§4).

## §4 Failure modes

### §4.1 — 0 candidates apply (or 0 clear objections)

The founder publishes a 30-day extension AT Record per seat. The constitutional
requirement of `BOOTSTRAP_COUNCIL_SIZE = 5` immutable means **the contract
cannot deploy until all 5 seats are filled**. Acceptable to extend up to 3×
30-day windows (total 120 days from initial 2026-05-20) before escalating to
§4.4.

### §4.2 — All candidates for a seat get 3+ cleared objections

This signals either:
- The candidate pool for that axis is too narrow (e.g. Seat 5 in a tech-heavy
  community), OR
- The objection threshold is being used as a veto by a faction.

The founder publishes a public diagnosis AT Record explaining which case it
is, then takes the corresponding action:

- **Pool too narrow**: 30-day extension + active outreach to specific
  communities (permaculture organizations / religious legal aid bar / DAO
  treasury committees / atproto-developer Slack equivalents).
- **Faction veto**: founder consults with a non-Council third party (e.g. the
  Charter Rider author OR a senior religious figure unaffiliated with
  etzhayyim) for a non-binding review, then either escalates (§4.3) OR
  exercises provisional appointment (§4.3).

### §4.3 — Provisional appointment

Per RFP §"What happens if all 5 seats don't fill by 2026-06-19?":

> The founder will: [...] **Provisionally appoint** an Adherent SBT holder
> to a seat (subject to subsequent objection mechanism + governance proposal
> to confirm/reject after Constitution.bindGovernance)

Operational rules for provisional appointment:

- Must be an active Adherent SBT holder
- Must score ≥9/18 on the per-seat rubric (lower than the 13/18 strong
  threshold but not arbitrarily low)
- The appointee's AT Record explicitly says "provisional, subject to
  governance proposal confirmation"
- A `Constitution.bindGovernance`-triggered confirmation vote is scheduled
  within 90 days of contract deploy

### §4.4 — Bootstrap reduction (temporary)

If no path through §4.1–§4.3 fills all 5 seats within 120 days, the founder
may petition for an ADR amendment (NOT a direct constitutional change) to
temporarily reduce `BOOTSTRAP_COUNCIL_SIZE` from 5 → 3 (founder + 2 of the
most strongly-supported axis seats). The amendment ADR must:

- Identify which 2 seats are filled (typically Seats 2 + 3, or 2 + 4)
- Specify the 12-month re-evaluation point at which the Council MUST return
  to size 5
- Pass a 1 SBT = 1 vote among all Adherents (NOT just the Council itself)

This is acknowledged as a last-resort failure mode. The founder commits to
publishing a public post-mortem if §4.4 is invoked.

### §4.5 — Deadlock signals

If multiple §4 paths are tried with no progress, the founder MUST publish a
"Phase 1 (Bootstrap) failed; pivoting to Phase 2 election approach" public
notice and trigger an early Phase 2 ADR draft. This is failure-resilient
behavior — the religious-corp doesn't die because Bootstrap was hard; it
moves to a different governance model.

## §5 Operator checklist (for the 2026-06-19 deadline)

The founder (or any operator assisting) should have the following ready by
the deadline:

- [ ] Per-seat scoring spreadsheet template (rubric scaffolded per §1)
- [ ] All cleared `council-candidate-application` AT Records in a single
      reading list
- [ ] All cleared + uncleared + defamatory objection AT Records indexed by
      candidate
- [ ] Smart Wallet address collection template (1 row per selected candidate,
      to be filled 2026-06-20)
- [ ] Foundry script: `forge script script/DeployReligiousCorp.s.sol
      --rpc-url base-sepolia --broadcast` with `BOOTSTRAP_COUNCIL_ADDRESSES`
      env var set to the 5 confirmed addresses
- [ ] Public announcement AT Record draft (5 paragraphs, one per seat)
- [ ] Failure-mode escalation tree pre-printed (this doc §4) so the founder
      doesn't need to re-design under deadline pressure

## §6 What this addendum is NOT

- Not a constitutional change. ADR-2605192300 + the 5-seat size + the 30-day
  objection window remain authoritative.
- Not a guarantee of selection. The founder retains discretionary judgment;
  the rubric is a discussion anchor, not a contract.
- Not binding on Phase 2. When Phase 2 (formal Council) replaces Bootstrap,
  this addendum is automatically superseded.

## §7 References

- COUNCIL-BOOTSTRAP-RFP.md — public RFP, 30-day window 2026-05-20 → 2026-06-19
- COUNCIL.md — roster + mechanics overview
- ADR-2605192300 — Bootstrap Council 5-seat constitutional ADR
- ADR-2605192100 — Mission Charter
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2(a)–(h) prohibited categories)
- CHARTER-RIDER.md — Rider canonical text
- `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/council-candidate-application.json`
- `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/council-objection.json`
- `50-infra/etzhayyim-chain-contracts/src/ChartersComplianceRegistry.sol`
- `50-infra/etzhayyim-chain-contracts/script/DeployReligiousCorp.s.sol`
