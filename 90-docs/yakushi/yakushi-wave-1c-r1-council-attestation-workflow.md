---
id: yakushi-wave-1c-r1-council-workflow
title: Wave 1c R1 Council Lv6+ attestation workflow (gate unlock procedure)
status: reference
doc_type: how-to
topic: yakushi/pharmaceutical/council-governance
authoritative: false
last_verified: 2026-05-25T00:00:00Z
depends_on:
  - ADR-2605250630
  - ADR-2605192300
---

# Wave 1c R1 Council Lv6+ attestation workflow

**Scope:** Procedural steps for Council Lv6+ ≥3 multisig attestation required to unlock `pharma_chiral_resolution` and `pharma_liquid_formulation` cell gates.
**Timeline:** Council motion 2026-05; gate unlock target 2026-06-30.

## Overview

Three constitutional gates must be set non-None in cell code before R1 manufacturing can begin:

1. **COUNCIL_ATTESTATION_TX_HASH** — Base L2 (Ethereum-compatible) Council Lv6+ ≥3 multisig transaction hash
2. **SILEN_PHARMA_BASELINE_REVIEW_CID** — IPFS CID of `com.etzhayyim.pharma.silenPharmaReview` Lexicon record (verdict = "approve")
3. **Additional for benzonatate (R1.5 only):** BENZONATATE_PMDA_OTC_APPROVAL_CID (contingent on PMDA decision)

## Phase 1: Pre-Ballot Documentation (T-2 weeks)

### Step 1a: yakushi team prepares summary memo

**Responsible:** yakushi QA lead + Chief Operating Operator (if applicable)

**Document to prepare:**
```
Title: yakushi Wave 1c R1 — Council Attestation Request Memo
Target: Council Lv6+ (≥3 approval required)
Date: [today]
Scope: Unlock omeprazole chiral synthesis + guaifenesin liquid formulation gates

Attachments:
  - ADR-2605250630 (full text)
  - Omeprazole benchtop PoC protocol (reference)
  - QC battery specifications (10-point assay set)
  - Equipment qualification checklist (Chiralcel OD-H column, Chiralcel OD-H 250×10)
  - Benzonatate PMDA monitoring assignment (3-month tracking plan)
  - Charter Rider §2(a)-(h) per-API clearance checklist
  - Risk matrix (equipment failure, route yield <65%, contamination, witness N<2)
  - Timeline: Council motion 2026-05 → gate unlock 2026-06-30 target
```

**Distribution:** Send to all 5 Council members (Seat 1-5) via encrypted email (AES-256-GCM, per ADR-2605181100 if sensitive discussion)

### Step 1b: Council async review period (1 week)

**Process:**
- Each Council member reads ADR + attachments
- Members post clarifying questions to a shared `yakushi-wave-1c-r1` Bluesky thread (public record, per ADR-2605192315 Transparent Force invariant)
- yakushi team responds to public questions within 24 h
- Private concerns: confidential email to full Council (encrypted)

**Expected questions:**
- "What is the failure mode if crystalline-resolution yield <65%?" → Answer: Switch to Route B prep-HPLC, yield target 70-95%
- "What witness requirements?" → Answer: N≥2 (operator DID + QP-equivalent DID or automated sensor DID), N=1 auto-escalates to Council
- "What is the Benzonatate PMDA deadline?" → Answer: R1 phase monitors until 2026-06-30; if approved → R1.5 amendment ADR within 8 days
- "Has omeprazole been synthesized before in religious-corp?" → Answer: No, this is Wave 1c inaugural; routes are Fisons 1965 (open literature) and Chiralcel OD-H prep (Daicel standard)

## Phase 2: Ballot & Multisig Signature (T-1 week)

### Step 2a: Council calls formal vote (Bluesky + async Slack)

**Responsible:** Council Chair (Seat 1)

**Ballot format:**

```
Title: yakushi Wave 1c R1 — Unlock chiral synthesis + liquid formulation gates
Votes required: ≥3 of 5 (supermajority per ADR-2605192300)
Motion: Approve ADR-2605250630, authorize deployment of COUNCIL_ATTESTATION_TX_HASH
        + SILEN_PHARMA_BASELINE_REVIEW_CID to cell.py gates

Option A: APPROVE (unlock gates; proceed to R1 manufacturing readiness)
Option B: DEFER (delay vote 2 weeks; require additional documentation)
Option C: REJECT (request protocol revision; sends back to yakushi team)

Voting window: [date] 09:00 JST → [date] 17:00 JST (24 h, async)
```

**Expected vote tally:** 3-5 APPROVE (if memo satisfied clarifying questions).

### Step 2b: Multisig transaction signing (post-vote)

**Responsible:** Council Lv6+ multisig Safe contract operators (typically Council Chair + 2 others)

**Process:**

1. **Proposal creation** (Safe.etzhayyim.eth on Base Sepolia testnet or Base mainnet — TBD per deployment phase):
   - Target: `ChartersComplianceRegistry.sol` (or `yakushi-wave-1c-registry.sol` if dedicated)
   - Function: `attest(apiScope="wave-1c-chiral-resolution-baseline", verdict="approve", cid=<IPFS_CID>)`
   - Parameters:
     ```solidity
     {
       scope: "wave-1c-chiral-resolution-baseline",
       verdict: "approve",
       silenPharmaReviewCid: "bafy...",
       attestationTime: <block.timestamp>,
       councilMultisigDid: "did:...",
       signers: [Council member 1 DID, Council member 2 DID, Council member 3 DID]
     }
     ```

2. **On-chain threshold** (≥3 of 5 multisig):
   - Chair signs (1/3)
   - Member 2 signs (2/3)
   - Member 3 signs (3/3 → threshold met, transaction executable)

3. **Execute transaction**:
   - Safe executes; emits `AttestationApproved(cid, scope, verdict)` event
   - Transaction hash recorded: `COUNCIL_ATTESTATION_TX_HASH = 0x[32-byte hex]`
   - Block confirmations: ≥12 before downstream use (testnet: ~3 min; mainnet: ~3 min @ 2-block avg)

**On-chain record:**
```
ChainID: Base Sepolia (84532) [testnet] or Base (8453) [mainnet — TBD]
TxHash: 0x[COUNCIL_ATTESTATION_TX_HASH]
Timestamp: [UTC timestamp]
Status: ✅ CONFIRMED (12 blocks)
Event: AttestationApproved(cid="bafy...", scope="wave-1c-chiral-resolution-baseline", verdict="approve")
Signers: council.etzhayyim.eth [3/5 multisig]
```

### Step 2c: IPFS publish `silenPharmaReview` record

**Responsible:** yakushi team (with Council chair delegated signature authority)

**Record structure:**

```json
{
  "type": "com.etzhayyim.pharma.silenPharmaReview",
  "createdAt": "2026-05-[date]T00:00:00Z",
  "scope": "wave-1c-chiral-resolution-baseline",
  "apiInn": ["omeprazole"],
  "verdict": "approve",
  "councilMultisigDid": "did:...",
  "councilAttestationTxHash": "0x...",
  "chainId": 8453,
  "attestationUri": "at://did:plc:[council-actor]/com.etzhayyim.pharma.silenPharmaReview/[rkey]",
  "gatekeepers": {
    "operatorDid": "did:web:etzhayyim.com:yakushi:operator",
    "qpEquivalentDid": "did:web:etzhayyim.com:yakushi:qp-equivalent"
  },
  "conditions": {
    "benchtopPoCRequired": true,
    "benchtopPoCProtocol": "omeprazole-chiral-benchtop-poc-protocol.md",
    "witnessMinimum": 2,
    "successCriteria": [
      "enantiomeric_purity_bp >= 9950",
      "recovery_yield_bp >= 6500",
      "optical_rotation_range: [50, 54]"
    ]
  },
  "benzonatateContingency": {
    "status": "monitoring",
    "pmda_decision_window_deadline": "2026-06-30T23:59:59Z",
    "r1_5_unlock_contingency": "ADR-2605250645"
  }
}
```

**Publishing path:**
1. Serialize to NDJSON + sign with Council chair DID (Cleartext JSON → JWS → wrap in IPFS structure)
2. Upload to Kubo IPFS node (`ipfs add -w silenPharmaReview.json`)
3. Record CID: `bafy...[32-byte hash]`
4. Publish to `council.etzhayyim.com` Bluesky PDS as `at://...` record (public attestation visibility)

**Result:** SILEN_PHARMA_BASELINE_REVIEW_CID = "bafy[...]" (immutable IPFS reference).

## Phase 3: Gate Unlock in Code (T-0)

### Step 3a: PR to unlock gates

**Responsible:** yakushi team

**Files to modify:**
- `40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_chiral_resolution/cell.py`
- `40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_liquid_formulation/cell.py`

**Changes (template):**

```python
# Before:
COUNCIL_ATTESTATION_TX_HASH: str | None = None
SILEN_PHARMA_BASELINE_REVIEW_CID: str | None = None

# After (set by Council vote):
COUNCIL_ATTESTATION_TX_HASH: str = "0x[32-byte Council multisig Tx hash from Step 2b]"
SILEN_PHARMA_BASELINE_REVIEW_CID: str = "bafy[...]"  # IPFS CID from Step 2c
```

**Verification:**
- Run `pytest 40-engine/kotoba/crates/kotoba-kotodama/cells/pharma_chiral_resolution/tests/test_gate_unlock.py` → ✅ PASS (no RuntimeError on import)
- Run `python -c "from kotodama.cells.pharma_chiral_resolution import cell; print(cell.COUNCIL_ATTESTATION_TX_HASH)"` → prints hash (not None)

**PR format:**
```
Title: chore(yakushi): unlock Wave 1c R1 gates — Council attestation ≥3 approval

- Set COUNCIL_ATTESTATION_TX_HASH in pharma_chiral_resolution/cell.py
- Set SILEN_PHARMA_BASELINE_REVIEW_CID in pharma_chiral_resolution/cell.py
- Set same gates in pharma_liquid_formulation/cell.py
- Verified: gate validation passes; no RuntimeError on module import
- Council motion: [date] ✅ APPROVED (≥3 votes)
- On-chain tx: 0x[hash] (12 confirmations, Base L2)
- IPFS CID: bafy[...] (published to council.etzhayyim.com)

See ADR-2605250630 for full context.
```

**Merge condition:** Code review + ≥1 approval from Council Chair (safety check).

### Step 3b: CI validation

**Automated checks (lefthook + GitHub Actions):**
- ✅ e7m-verify: Confirms COUNCIL_ATTESTATION_TX_HASH is a valid Ethereum address format
- ✅ Confirms SILEN_PHARMA_BASELINE_REVIEW_CID is a valid IPFS CID (CIDv1 format)
- ✅ Confirms gates match on-chain attestation (fetch from Base L2 JSON-RPC, verify TxHash exists)
- ✅ Confirms IPFS CID resolves to a valid silenPharmaReview record (deterministic hash check)

**If any check fails:** PR marked as blocked; yakushi team must reconcile (e.g., typo in Tx hash).

## Phase 4: Manufacturing Readiness Check (T+1 day)

### Step 4a: Final operational checklist

**Responsible:** yakushi team + QA lead

Before first benchtop PoC synthesis:

- [ ] Gates unlock verified (no RuntimeError on `from kotodama.cells.pharma_chiral_resolution import cell`)
- [ ] Equipment ready (Chiralcel OD-H column certified, Agilent 1260 HPLC functional, polarimeter calibrated)
- [ ] Materials sourced (racemic omeprazole H0891-5G, L-mandelic acid M4256, ethyl acetate HPLC)
- [ ] Protocol printed + reviewed by ≥2 witnesses (operator + QP-equivalent or sensor)
- [ ] MST listener subscribed to `purificationAttestation` events (Murakumo levi node listening for cell triggers)
- [ ] Safety review passed (omeprazole enantiomers: non-toxic @ benchtop scale; EtOAc: flammable — fire extinguisher nearby)
- [ ] Witness N≥2 roster confirmed (two DIDs pre-authorized to sign attestations)

**Sign-off:** yakushi team + Council chair counter-signature (attestation of readiness).

## Risk Mitigation Table

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Council vote fails to reach ≥3 approval | Low | Delay 2 weeks; revise ADR | Include detailed attachments in memo; pre-brief Council members individually |
| Multisig signing takes >5 days | Medium | Stretch timeline to 2026-06-15 | Use async signing; automated Safe signature notification system |
| Benchtop PoC yield <65% (Route A fails) | Medium | Switch to Route B prep-HPLC | Document Route B as fallback; stock Chiralcel OD-H column as spare |
| IPFS node unavailable during CID publish | Low | Publish to secondary node (e.g., Infura) | Dual-pin to Kubo + Infura; verify CID resolves before gate unlock PR |
| Witness N=1 (single operator only) | Low | Auto-escalate to Council; manufacturing blocked | Pre-assign QP-equivalent DID before synthesis; contract mandatory dual sign-off |
| Benzonatate PMDA decision delays past 2026-06-30 | Medium | R1.5 ADR deferred; manufacturing blocked until Wave 2 | Continuously monitor PMDA official journal; set calendar reminder at T-2 weeks |

## Timeline Summary

```
T-14d: yakushi memo to Council
T-7d:  Council async review + clarifying questions
T-3d:  Council formal vote (24 h voting window)
T-2d:  Multisig transaction signing (Safe 0x...) + IPFS publish (bafy...)
T-0d:  PR merge (gates unlock)
T+1d:  Manufacturing readiness checklist
T+2d:  First benchtop PoC synthesis begins
T+21d: PoC completion + attestation records published
```

**Hard deadline:** 2026-06-30 (Council gate unlock must be complete by this date for R1 phase to proceed on timeline).

## See Also

- ADR-2605250630: Wave 1c R1 charter (master, this gate framework)
- ADR-2605192300: etzhayyim Bootstrap Council 5名 roster + expertise matrix
- ADR-2605192230: Three-tier enforcement (L1 license / L2 gate / L3 Council attestation)
- ADR-2605231525: no-server-key invariant (G13, multisig-only for keys)
- `20-actors/yakushi/CLAUDE.md`: actor-level governance rules + cell pattern
- `omeprazole-chiral-benchtop-poc-protocol.md`: execution playbook (what happens after gates unlock)

---

**Owner:** yakushi QA lead (in coordination with Council Chair)
**Last reviewed:** 2026-05-25
**Next review:** Upon Council motion filing (target 2026-05)
