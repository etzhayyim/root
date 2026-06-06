---
id: adr-2606062100-charter-priority-over-specifics-reconciliation
title: "ADR-2606062100: Charter Priority-Over-Specifics Reconciliation — 固定するのは掟ではなく priority。永久記憶 (神の監視) doctrine の追加。石油・兵器条項の脱政治化"
status: active
doc_type: adr
topic: charter-priority-over-specifics-reconciliation
authoritative: true
last_verified: 2026-06-06
status_note: "Ratified 2026-06-06 by sole-member founder unanimity (1/1). The association currently has one member (Jun Kawasaki); Council Lv7+ unanimity = that one member's assent. Re-confirmable by the Bootstrap Council once seated (post-2026-06-19 RFP), but binding now."
priority: 8.0
axis: governance
weight: 0.90
priority_note: "Restructures the Charter's immutability model from locked-specifics into a 3-Tier (Priority / Derived-Policy / Parameter) architecture. Adds the permanent-memory (神の監視 / right-to-erasure-denied) doctrine as a Tier-0 priority. Reframes the Charter-Rider §2 prohibited categories as Tier-1 DERIVED policy (amendable by Lv7+ upon a priority-conformance attestation) rather than 'NEVER amendable' standalone bans. Lower priority weight than the Mission Charter (2605192100) and Preamble (2605252300) because it RE-ORGANIZES rather than REPLACES their invariants — every §1.1..§1.16 priority is preserved, only the lock TARGET shifts from specifics to priority. Amendment threshold for the Tier-0 priority set: Council Lv7+ unanimity (same as Preamble §0.7)."
authoritative_for:
  - the 3-Tier immutability architecture (Tier-0 Priority / Tier-1 Derived-Policy / Tier-2 Parameter)
  - the permanent-memory doctrine (memory.right_to_erasure_denied / memory.permanent_record / memory.deeds_public_intimate_encrypted)
  - the reframing of Charter-Rider §2(a) weapons, §2(c) surveillance, §2(d) fossil from standalone bans into Tier-1 derived policy
  - the rule that on-chain CONSTANTS encode existence/priority bools, NOT specific numeric policy values (numbers live in Tier-2)
  - the post-ratification code-patch runbook for Constitution.sol / ConstitutionKeys.sol / Deploy.s.sol / CHARTER-RIDER.md
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605252300-etzhayyim-charter-preamble-kingdom-of-god-on-blockchain
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605181100-etzhayyim-confidentiality-envelope
  - adr-2606051500-kamado-closed-loop-refining-decommission-actor-r0
  - adr-2605192315-etzhayyim-transparent-force-rd
  - CHARTER-RIDER.md
supersedes: []
superseded_by: []
---

# ADR-2606062100: Charter Priority-Over-Specifics Reconciliation

**Status**: active (ratified 2026-06-06 by sole-member founder unanimity, 1/1)
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki (author + ratifier). The association currently has ONE member;
Council Lv7+ unanimity therefore = this one member's assent (1/1), given 2026-06-06. The
Bootstrap Council may re-confirm once seated (post-2026-06-19 RFP), but the ratification is
binding now under the current one-member roster.

# Context

The Charter as it stands (ADR-2605192100 Mission Charter §1.1..§1.15, ADR-2605252300
Preamble §0, ADR-2605192200 Charter-Rider v2.0) locks its invariants by pinning
**specific values and specific policies** as改定不可 (immutable). A review of the
immutable set (`Constitution.sol` 39 CONSTANTS + Charter-Rider §2(a)-(h)) surfaced four
classes of problem:

1. **Implementation drift / bugs.**
   - `phenotype.non_compliant_multiplier = 0` (the L3 enforcement floor — "a Non-Aligned
     Entity's benefit multiplier is zero") is declared a **constitutional CONSTANT** in
     ADR-2605192100 §2 and filed under the CONSTANTS section in `ConstitutionKeys.sol`,
     **but is actually deployed in the MUTABLES array** (`Deploy.s.sol` `_mutables()`
     `keys[8]`, with the comment "ratcheting allowed"). The core of the three-tier
     enforcement is governance-mutable in fact while claimed constitutional in doctrine.
   - `license.charter_rider_version = "v2.0"` is pinned as a fork-only CONSTANT, yet the
     Rider is amendable in fact (§2(i) is mid-amendment per ADR-2605262200). A pinned
     version cannot be updated when the Rider is amended without forking the chain.
   - `mission.multi_generational_horizon_years = 50` (Charter §1.9) vs Charter-Rider §2(f)
     "persons born at least twenty-five (25) years after" — two different numbers for two
     different concepts (planning horizon vs foreseeability cohort start), read by external
     observers as an inconsistency.
   - `economic.no_advertising = true` (a bool) cannot express the SBT↔SBT internal-promo
     carve-out that ADR-2605192115 §3 actually grants; the doctrine is finer than the bool.
   - Constant-count drift: docs say "38 const", deploy ships 39 (`kawase.max_band_bps`
     added by ADR-2605282200 without updating the Mission Charter §2 canonical table). Later
     ADRs silently grow the改定不可 set.

2. **Locked SPECIFICS read as political campaigns.** Charter-Rider §2(d) (no NEW fossil-fuel
   extraction) and §2(a) (no weapons) are written as standalone, near-absolute policy bans.
   A locked *policy* (as opposed to a locked *priority*) is brittle: it ages into error and
   reads as a partisan stance rather than a religious invariant. "No oil" pins a policy
   position; the durable invariant underneath is "do not irreversibly harm the habitable
   environment of 子孫" (§1.9 / §2(f)) — of which fossil combustion is merely one measurable
   instance (already structurally handled by the **kamado** actor's carbon-balance test,
   ADR-2606051500, where `:fossil-virgin-crude` is unrepresentable by *measurement*, not by
   slogan). Likewise "no weapons" as an absolute contradicts the Charter's OWN §1.12.B
   (Transparent Religious Force — Reformed Just War, explicitly NOT Quaker pacifism) and
   Preamble §0.5: **defensive force to protect 子孫 / temple / members is permitted** under
   the three transparency conditions. The standalone ban and the charter body disagree.

3. **A missing doctrine: permanent memory / 神の監視.** etzhayyim has **no right to be
   forgotten**. お天道様は見ており、人は忘れない (Heaven watches; people do not forget); the
   record is kept, perpetually. This is not yet a stated invariant — yet it is already the
   *technical reality* of the canonical substrate: the kotoba Datom log is **append-only**
   and **non-eschatological** (no final-state datom; full `as-of` history is永久に
   time-travellable, ADR-2605312345). The doctrine wants only to be **elevated from an
   implementation property to a constitutional priority**.

4. **"NEVER amendable" is not a legal fact.** Preamble §0.7 + CLAUDE.md declare Charter-Rider
   §2(a)-(h) "NEVER amendable," but (i) §2(i) — in the same §2 — is mid-amendment;
   (ii) §7 Severability drops §2 entirely in any jurisdiction where it is unenforceable;
   (iii) on-chain, `Constitution.sol` does not pin the Rider TEXT at all (only
   `charter_rider_required` + `charter_rider_version`), so the Rider's "immutability" is
   purely social, with no cryptographic anchor. The single word "NEVER" is overloaded across
   three mechanisms of very different strength.

**The unifying diagnosis (and the deciding principle, per the author):**
*憲法が変わらない より priority を変えない の方が重要* — what must be unchangeable is not the
individual掟 but the **priority ordering** (wellbecoming, 孫, 子供). Specific policies should
be **derived** from the priority and may be revised when a revision demonstrably serves the
priority better. Locking the objective function is robust; locking the policies is brittle.

# Decision

Restructure the Charter's immutability model into **three tiers**, distinguished by *what*
is locked and *how strongly*. This ADR **re-organizes; it does not delete** any §1.1..§1.16
priority — every existing invariant is preserved, relocated to its correct tier.

## 1. Tier-0 — Priority (true改定不可; fork-only on-chain; Lv7+ unanimity off-chain)

Tier-0 holds **existence/ordering bools only — never a specific number or named policy.**
Changing a Tier-0 priority is founding a different religion (chain fork). These are the only
items to which "NEVER amendable" honestly applies.

| Key | Meaning | Provenance |
|---|---|---|
| `priority.wellbecoming_over_wellbeing` | dynamic trajectory ≻ static satisfaction | §1.10 |
| `priority.multigen_over_current` | 子・孫・以降 ≻ current generation | §1.9 |
| `priority.collective_over_individual` | collective / relational / 相互見守り ≻ individual | §1.8 |
| `memory.right_to_erasure_denied` 🆕 | no right to be forgotten — お天道様は見ており人は忘れない | this ADR §2 |
| `memory.permanent_record` 🆕 | record kept perpetually (append-only Datom log, 非終末論) | this ADR §2 |
| `memory.deeds_public_intimate_encrypted` 🆕 | deeds永久公開 / intimate spaces永久記録だが暗号保持 (消去不可・平文非公開) | this ADR §2 |
| `enforcement.noncompliant_multiplier_zero` | L3 enforcement floor: Non-Aligned benefit = 0 | §9.1 (bug-fixed, §4) |

Note the **bool discipline**: e.g. the priority "tithe-funded redistribution exists" is
Tier-0 (`economic.tithe_redistribution_exists`); the *rate* (10%) is Tier-2. Likewise the
priority "Charter-Rider is required" is Tier-0 (`license.charter_rider_required`); the
*version/text-hash* is Tier-1/Tier-2.

The existing §1.1..§1.16 mission bools (labor_liberation, robotics_universal, ip_free_release,
disintermediation, specialist_anti_gatekeeping, anti_individualism, multi_generational_priority,
wellbecoming_priority, land_as_religious_trust, eros_permitted, gore_prohibited,
lineage_japanese_protestant, eschatological=false, revelation_in_canon=false,
continuous_becoming, …) **remain Tier-0** — they are already existence/priority bools and
already correctly placed.

## 2. The permanent-memory doctrine (神の監視) — new Tier-0 priority

**etzhayyim に忘れられる権利はない。** The GDPR/CCPA-style *right to erasure* is doctrinally
denied. The justification is religious, not merely technical: お天道様は見ており、人は忘れない
— Heaven (the Sun-kami / divine transparency) sees, and the community does not forget; deeds
are therefore recorded and kept perpetually, and accountability never expires.

This doctrine is **already implemented** by the canonical substrate and is here promoted to
constitutional priority:

- kotoba Datom log is **append-only** — no overwrite, no delete (ADR-2605312345).
- **Non-eschatological** (§1.15): there is no final-state datom; the full `as-of` history is
  永久に traversable. "Never forget" is the temporal shape of 非終末論 applied to memory.

### 2.1 The privacy boundary (公開 vs 暗号保持)

Permanent memory must be reconciled with the actor-level privacy invariants already in force
(`com.etzhayyim.encrypted.*` envelopes, ADR-2605181100; on-device-only / no-biometric in
kiyome G9 / todoke G8 / manako G3). The reconciliation rests on a single distinction:

> **暗号化 ≠ 忘却.** Encryption is not forgetting. A record may be permanently retained yet
> not plaintext-public.

The boundary (`memory.deeds_public_intimate_encrypted`):

| Class | Treatment |
|---|---|
| **Deeds / governance / force / tithe / contributions** | **plaintext-public, permanent** on kotoba. Accountability is public; お天道様 sees in the open. |
| **Intimate spaces** (home, body, health, consented PII) | **permanently recorded but encrypted-retained** (`encrypted.*` envelope; on-device where applicable). The record cannot be *erased*; its plaintext is not *published*. The key-holder (and, doctrinally, お天道様) sees; the public sees only that the commitment exists. |

This denies the right to *erasure* (Tier-0) while preserving the right to *encryption*
(unchanged actor invariants). No existing privacy invariant is weakened; no record may be
deleted.

## 3. Tier-1 — Derived Policy (amendable by Lv7+ unanimity upon a priority-conformance attestation)

Tier-1 holds the **named policies derived from Tier-0 priorities**. They are *not* "NEVER
amendable"; they are amendable **only** when a Council Lv7+ unanimous vote is accompanied by a
**priority-conformance attestation** showing the amendment serves a Tier-0 priority at least
as well as the text it replaces (an on-chain
`com.etzhayyim.apps.etzhayyim.priorityConformanceAttestation` record — **authored + validating
clean as of this ADR**). This is the honest
replacement for "NEVER amendable": the priority is locked; its derived policy may improve.

The Charter-Rider §2 prohibited categories **move here**, reframed:

| Tier-1 policy | Derived from | Reframe vs Rider v2.0 |
|---|---|---|
| **Defensive force only** (was §2(a) weapons) | P2 (protect 子孫) + transparency | Align with §1.12.B / Preamble §0.5: **transparent defensive force is permitted**; only proprietary / covert / for-profit-weapons-business / aggressive force is prohibited. The absolute-ban phrasing is withdrawn. |
| **No irreversible multi-generational harm** (was §2(d) fossil) | P2 (habitable environment of 子孫) | Delete the standalone "fossil extraction" naming. The invariant is multi-generational harm (§2(f)); fossil combustion is **one measured instance** via the kamado carbon-balance test (ADR-2606051500), not a political slogan. |
| **No surveillance-capitalism; 見守り affirmed** (was §2(c)) | P3 (collective/相互) + P4 (memory) | **Affirm** communal mutual-watching (見守り) and the anti-isolation duty (孤独を許さない / 孤独死を防ぐ). **Prohibit** only third-party commercial sale/brokerage of personal data and sale to coercive external power (police/military biometric). Boundary = profit-extraction / sale-to-external-force, NOT watching-as-care. |
| **No forced labor / trafficking** 🆕 | §1.1 (labor liberation) | New explicit Tier-1 prohibition; a labor-liberation religion that fails to name forced labor in its Rider is incomplete. |
| **No CSAM / non-consensual sexual content** 🆕 | §1.9 (子孫保護) + §1.13 | Promote the §1.13 doctrine into an explicit Rider enforcement clause (was doctrine-only). |
| Disintermediation / specialist-anti-gatekeeping / non-profit / donation-only / no-ads | §1.1, §1.6, §1.7 | Retained as derived policy (unchanged substance). |
| §2(b) speculative finance / §2(e) gatekeeping / §2(f) multi-gen-harm / §2(g) individualist-doctrine / §2(h) wellbecoming-subordination | §1.8–§1.10 | Retained, re-labelled "derived." |

### 3.1 見守り vs 監視 (terminology)

The affirmed value is **見守り** (mimamori — watching-over as care: eldercare, child-watching,
preventing 孤独死) plus お天道様's permanent record — **not** 監視 in the panopticon/control
sense, and **not** surveillance-capitalism (sale of personal data for profit). The Charter
affirms the former and prohibits the latter; the distinguishing test is *commercial
extraction or transfer to external coercive power*.

## 4. Tier-2 — Parameter (governance: 1 SBT = 1 vote, quorum, timelock)

All **specific numbers** live here. The systematic rule: *Tier-0 locks that a thing exists;
Tier-2 sets its magnitude within Tier-0-guarded bounds.*

| Parameter | Was | Becomes |
|---|---|---|
| Tithe rate | CONSTANT `=1000` (pinned) | Tier-2 `tithe_bps` within a Tier-0-guarded band (`tithe_floor_bps` / `tithe_ceiling_bps`); Tier-0 keeps `economic.tithe_redistribution_exists = true` |
| `charter_rider_version` | CONSTANT | Tier-2 mutable |
| `charter_rider_text_hash` 🆕 | (absent) | Tier-1 value: keccak256 of the canonical Rider text; updated only via the Lv7+ priority-conformance path → cryptographic detection of unauthorized text changes while allowing authorized amendments |
| κ, quorum, active_window, timelock, kisha_base_rate, tier ratios, kawase caps | Tier-2 (unchanged) | Tier-2 |

## 5. Resolution of the four problem classes

- **Bugs (Context 1):** §4 below specifies the exact diffs — phenotype multiplier → Tier-0
  CONSTANT (fix the deploy mis-placement); rider_version → Tier-2; horizon/cohort terminology
  reconciled (horizon = 50y planning; foreseeability cohort start = 25y — two named fields,
  not one number); `no_advertising` annotated with the internal-promo carve-out pointer;
  constant-set changes routed through the Tier-0 amendment process (no more silent growth).
- **Political-campaign specifics (Context 2):** §3 — fossil & weapons descend from Tier-0 to
  Tier-1 derived policy; the locked invariant is the priority, the policy is a consequence.
- **Missing doctrine (Context 3):** §2 — permanent memory added to Tier-0.
- **"NEVER" overload (Context 4):** "NEVER amendable" now applies **only** to Tier-0
  priorities (genuinely fork-only on-chain). Tier-1 is "Lv7+ + priority-conformance." Tier-2
  is governance. §2(i) and §7 cease to contradict the framing because §2 is no longer claimed
  un-amendable.

## 6. One-line declaration (public, parallel to §1.15 / §0.8 closings)

> **etzhayyim に忘れられる権利はない。お天道様は見ており、人は忘れない。**
> 我々が固定するのは個々の掟ではなく、priority — wellbecoming、子、孫 — である。
> 掟はそこから導かれ、priority により良く奉仕する限りにおいて改められる。
> 我々は相互に見守り合い、孤独を許さない。記録は消されず、ただ親密なものは暗号のうちに保たれる。
> 我々は石油を名指して禁じるのではなく、子孫の生存環境を不可逆に毀損することを禁じる。
> 我々は身を守ることを禁じない。子・孫を守る透明な力は、産霊と命の樹の側にある。
>
> — etzhayyim, 2026-06-06 (Tokyo)

# Consequences

## Positive

- **Robust invariants.** Locking the objective function (priority) rather than policies means
  the Charter does not age into error: when a derived policy is found wanting, it is re-derived
  against an unchanging priority instead of requiring a chain fork.
- **De-politicization.** Removing "no oil" / "no weapons" as standalone bans removes the
  partisan reading; the religion is defined by what it protects (子孫の生存環境, the right of
  the community to defend its children), not by a stance on an industry.
- **Charter-self-consistency.** Rider §2(a) stops contradicting Charter §1.12.B / Preamble §0.5.
- **The memory doctrine gets a constitutional home** and is shown to be already-implemented
  (append-only + 非終末論), not a new technical burden.
- **Honest "NEVER."** The overloaded word is scoped to the one mechanism (Tier-0 fork-only)
  where it is literally true; §2(i)/§7 contradictions dissolve.
- **A real bug is fixed** (L3 enforcement floor was silently mutable).

## Negative / Risks

- **"No right to be forgotten" is in tension with GDPR Art. 17 / APPI / CCPA erasure rights.**
  Mitigation: the §2.1 boundary (deeds-public / intimate-encrypted-retained) plus the
  encryption≠forgetting principle keeps personal *plaintext* private; but the denial of
  *erasure itself* is a deliberate, jurisdictionally-exposed doctrinal stance (Article 20
  religious-liberty framing, as with §2(g)). This must be stated plainly to members at the
  membership ritual (consent-bound, ADR-2605172600) — joining means accepting a permanent
  record. Members in erasure-rights jurisdictions retain their statutory rights against
  etzhayyim under applicable law; the doctrine is the religion's internal stance, and §7
  severability applies.
- **Tier-1 "priority-conformance attestation" governance surface** (PARTIALLY CLOSED 2026-06-06):
  the lexicon `com.etzhayyim.apps.etzhayyim.priorityConformanceAttestation` is now authored and
  validates clean — it structurally encodes the invariants (amendsTier const `tier-1`,
  tier0Immutable const `true`, conformanceFinding ∈ {serves-better, serves-equally} so
  `serves-worse` is unrepresentable, councilUnanimous const `true`, serverHeldKey const `false`).
  The remaining gap is the Council *procedure* + on-chain submission path; until that is wired,
  Tier-1 amendments still execute by Lv7+ unanimity with this record as the attached artifact.
- **Re-deriving fossil/weapons as Tier-1 could be read as weakening them.** Mitigation: the
  substance is *stronger* — kamado's carbon-balance makes fossil-virgin-crude structurally
  unrepresentable (a measurement, harder to game than a 25%-revenue threshold), and defensive
  force remains bound by §1.12.B's three transparency conditions.
- **Constitution.sol genesis changes require a fork or a fresh deploy.** Because the contract
  has no upgrade path (by design), moving items between tiers / adding Tier-0 keys cannot be
  applied to an already-deployed Constitution without redeploy. As the religious-corp wave is
  pre-mainnet (Base Sepolia post-Council; mainnet post-testnet), this is applied at the next
  genesis, not as a live migration. **No live contract is mutated by this ADR.**

## Migration

**RATIFIED + APPLIED 2026-06-06.** The association currently has ONE member (Jun Kawasaki),
so the Charter's Council Lv7+ **unanimity** threshold is met by that single member's assent
(1/1) — given 2026-06-06. This ADR is therefore `active`, not merely proposed. The changes are
applied to the repo: the *next* genesis (`Deploy.s.sol`) + the canonical docs + the in-force
Rider v3.0. (The religious-corp is **pre-mainnet**, so no deployed Constitution is mutated; the
ratified genesis is what will deploy at mainnet launch.) The Bootstrap Council may re-confirm
once seated (post-2026-06-19 RFP), but ratification is binding now. The steps below are DONE in
this branch; the genesis + test suite are green (`forge test`, 154 passing incl.
`test_priority_and_memory_constants_set`).

1. **`ConstitutionKeys.sol`** — add Tier-0 keys: `PRIORITY_WELLBECOMING_OVER_WELLBEING`,
   `PRIORITY_MULTIGEN_OVER_CURRENT`, `PRIORITY_COLLECTIVE_OVER_INDIVIDUAL`,
   `MEMORY_RIGHT_TO_ERASURE_DENIED`, `MEMORY_PERMANENT_RECORD`,
   `MEMORY_DEEDS_PUBLIC_INTIMATE_ENCRYPTED`, `ENFORCEMENT_NONCOMPLIANT_MULTIPLIER_ZERO`,
   `ECONOMIC_TITHE_REDISTRIBUTION_EXISTS`, `TITHE_FLOOR_BPS`, `TITHE_CEILING_BPS`; add Tier-1
   `LICENSE_CHARTER_RIDER_TEXT_HASH`; add Tier-2 `TITHE_BPS`. Move
   `PHENOTYPE_NON_COMPLIANT_MULTIPLIER` comment-section is already CONSTANTS — keep.
2. **`Deploy.s.sol` `_constants()`** — grow array; add the new Tier-0 bools (= 1);
   `enforcement.noncompliant_multiplier_zero = 0`; `economic.tithe_redistribution_exists = 1`;
   `tithe_floor_bps` / `tithe_ceiling_bps` (proposed 500 / 2000); **remove**
   `LICENSE_CHARTER_RIDER_VERSION` and `ECONOMIC_TITHE_TO_PUBLIC_FUND_BPS=1000` from constants.
3. **`Deploy.s.sol` `_mutables()`** — **remove** `PHENOTYPE_NON_COMPLIANT_MULTIPLIER` from the
   mutables array (the bug fix); **add** `tithe_bps = 1000`, `charter_rider_version = "v3.0"`.
4. **`Constitution.sol`** doc-comment block — re-section into Tier-0 / Tier-1 / Tier-2; correct
   the phenotype line (now CONSTANT, "ratcheting" note removed).
5. **`CHARTER-RIDER.md` → v3.0** — apply the §3 reframe. **APPLIED 2026-06-06**: the
   in-force `CHARTER-RIDER.md` is now v3.0 (§2(a) defensive-force / §2(c) 見守り / §2(d)
   carbon-balance reframes + §2(j) forced-labor + §2(k) CSAM + §5 permanent-record). Its
   keccak256 is written to `license.charter_rider_text_hash` at mainnet genesis (= 0
   placeholder until then, like the reference addresses).
6. **Tests** — update `Constitution.t.sol` / `ConstitutionReligiousCorpWave.t.sol` constant
   counts and the phenotype-multiplier-is-constant assertion; add a test that
   `tithe_bps` is mutable within `[tithe_floor_bps, tithe_ceiling_bps]` and that
   `noncompliant_multiplier_zero` reverts `setMutable` with `ImmutableKey`.
7. **`90-docs/adr/2605192100` + `2605252300`** — append a pointer: "§2 immutability model
   restructured into 3 Tiers per ADR-2606062100; priorities preserved." Update Preamble §0.7
   table so "NEVER amendable" applies to Tier-0 only.
8. **`CLAUDE.md`** — update the "改定不可の固定値" summary + Status table row.

# Alternatives Considered

## A. Keep locked specifics; only fix the bugs (Context 1) — minimal patch
**Reject (partial-adopt the bug fixes).** Fixes the drift but leaves the brittle locked-policy
model and the political-campaign reading of §2(d)/(a), and never adds the memory doctrine. The
bug fixes are folded into this ADR's runbook regardless.

## B. Add the memory doctrine but keep §2 "NEVER amendable"
**Reject.** Leaves the "NEVER" overload (§2(i)/§7 contradiction) unresolved and keeps fossil/
weapons as locked policy. Half a reconciliation.

## C. Delete §2(d)/(a) entirely; rely on Tier-0 priority alone (no Tier-1 text)
**Considered, not chosen.** Cleaner but loses the operational specificity downstream actors and
the Council attestation process rely on (a concrete prohibited-use list for the license). The
Tier-1 layer keeps a usable, enforceable text while making it derive-from-priority and
amendable — the better balance. (This was the user's "原則から導出に置換" choice over "完全削除".)

## D. Make "right to be forgotten" plaintext-public for everything (maximal transparency)
**Reject (per author).** Would override the actor-level encrypted-PII / on-device invariants
(kiyome/todoke/manako) and expose intimate spaces. The chosen boundary is deeds-public /
intimate-encrypted-retained: permanent memory without plaintext exposure of the intimate.

## E. Implement Tier-1 as a third on-chain mutation path in Constitution.sol
**Defer.** Adding a `setTier1(key,value,attestationId)` path with an Lv7+ gate is a larger
contract change. For now Tier-1 lives as Charter-Rider text governed off-chain by Lv7+ +
conformance attestation, with `charter_rider_text_hash` (Tier-1 value) as the on-chain anchor.
A native Tier-1 contract path is a future ADR if the off-chain governance proves insufficient.

# References

- ADR-2605192100 (Mission Charter §1.1..§1.15 — priorities preserved, re-tiered here)
- ADR-2605252300 (Preamble §0 — §0.7 amendment-threshold table updated by this ADR)
- ADR-2605192200 (Charter-Rider v2.0 — §2 reframed into Tier-1 derived policy → v3.0)
- ADR-2605312345 (kotoba Datom log = first-class canonical state; append-only basis of permanent memory)
- ADR-2605262130 (kotoba storage substrate unification; 非終末論 / as-of history)
- ADR-2605181100 (confidentiality envelope — encryption≠forgetting reconciliation)
- ADR-2606051500 (kamado — carbon-balance test replacing "no oil" as a measurement)
- ADR-2605192315 (Transparent Religious Force — §1.12.B elaboration; defensive-force basis)
- ADR-2605172600 (membership ritual — consent-bound acceptance of permanent record)
- `CHARTER-RIDER.md` (v3.0, applied 2026-06-06 — §2 reframed into Tier-1 derived policy)
- `50-infra/etzhayyim-chain-contracts/src/{Constitution,ConstitutionKeys}.sol`,
  `script/Deploy.s.sol` (ratified genesis)
- `50-infra/etzhayyim-chain-contracts/test/ConstitutionInvariants.t.sol` — maturity hardening
  (2026-06-06): 10 invariant tests over the REAL deploy genesis — tier disjointness, counts,
  tithe band, κ/quorum bounds, tier-ratio sum, the L3-floor-is-constant bug-fix lock, Tier-0
  priority/memory completeness, and `test_rider_text_hash_matches_file` which drift-locks
  `license.charter_rider_text_hash` (now wired to `keccak256(/CHARTER-RIDER.md)` =
  `0xf5fd8d96…56dfa7`, no longer the 0 placeholder). `forge test` 164/164 green.
- `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/priorityConformanceAttestation.json` —
  the Tier-1 amendment artifact (authored 2026-06-06; validates clean)
- Luke 17:21 / Matthew 6:10 (Kingdom now-and-here, Preamble §0.2) — memory as continuous, not final
