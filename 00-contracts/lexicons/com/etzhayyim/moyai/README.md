# com.etzhayyim.moyai.* — Lexicons (舫い inference reciprocity credit)

**moyai 舫い** is the **non-monetary, give-to-get reward** for participating in commons
inference (ADR-2606062100). Contributing verified inference/compute MINTS reciprocity
credit; drawing *discretionary surplus* inference BURNS it — *to obtain information you must
generate information* (情報を得るためには情報を生成する). It is the charter-clean **carve-out**
to `give.computeDonationAttestation`'s G4 (compute donation grants no benefit): moyai grants
no *benefit* — it grants a **commons-use-right** on the very resource you helped produce
(the 入会権 / iriai-ken model, ADR-2605192345). Reciprocity, not welfare.

| Lexicon | Purpose |
|---|---|
| `contributionAttestation` | **MINT** — a verified proof-of-contribution (honeypot + spot-check passed, non-duplicate) mints credit bound to the contributing DID. Carries the five const locks. |
| `drawReceipt` | **BURN** — a receipt for drawing inference: free within the subsistence floor (information-as-BHI) / free when the mesh is idle / burns credit only for discretionary surplus under contention. |

## The five const locks (why a *reward* stays charter-clean)

Each is `const` in-schema (and enforced again in code + tests, the nusa/kamado/fuchi pattern):

- `redeemableUsdMicros = 0` — **non-monetary**; cash≡0 (N1); cannot be income, so it **does
  not affect Basic High Income** (the explicit design constraint).
- `transferable = false` — **non-transferable**; no transfer/gift/merge/pool verb exists →
  sybils cannot recombine credit across identities.
- `affectsBasicHighIncome = false` — moyai **never** touches BHI; the subsistence inference
  floor is unconditional, credit only governs discretionary surplus under contention.
- `grantsGovernanceWeight = false` — 1 SBT = 1 vote untouched.
- `grantsBenefitOrStage = false` — never a Liberation-Ladder / welfare / priority-for-
  benefits path (anti-class N2/N3, ADR-2605261000).

Plus, on `drawReceipt`, `essentialGuaranteed = true` (const): essential information is served
on every draw regardless of credit.

## Relationship to `give.computeDonationAttestation`

| | `give.computeDonationAttestation` (ADR-2606012100) | `moyai.contributionAttestation` (ADR-2606062100) |
|---|---|---|
| medium | donating compute as a **pure gift** | donating **verified** compute that mints a reward |
| reward | none (`grantsBenefit=false`) | **moyai credit** (a commons-draw-right; still `grantsBenefitOrStage=false`) |
| verification | best-effort attestation | honeypot + spot-check proof-of-contribution |
| cash | `compensatedUsdMicros=0` | `redeemableUsdMicros=0` |
| BHI | untouched | untouched (`affectsBasicHighIncome=false`) |

Both are non-cash, non-benefit, BHI-neutral. moyai adds a *non-monetary reciprocity reward*
on top of verified contribution, scoped strictly to commons-draw-rights.

## Reference implementation

`50-infra/etzhayyim-moyai-credit/` — append-only ledger (decay + conservation +
non-transferable by construction), proof-of-contribution anti-fraud membrane, fair-share
BHI-firewall scheduler, end-to-end demo. 46 tests (`run_tests.sh`).

## Constitutional invariants

- No PII beyond the contributing/drawing DID; never a per-donor leaderboard (anti-class).
- `additionalProperties` omitted ⇒ no extra fields; integer-with-implied-units, no floats on
  the record (ADR-2605190900); decay computed at read time only.
- no-server-key: the node co-signs mints; the server cannot mint (ADR-2605231525).
- Supersedes the legacy RisingWave credits economy (`bpmn/com/etzhayyim/credits/*`,
  ameno `vertex_credits_af_event`).
