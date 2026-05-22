# Chaos Engineering Charter

**Status:** draft (pre-ADR)
**Date:** 2026-05-22 02:40 JST
**Active-inference tick:** cycle 07
**Axis closed:** Anti-fragility (Axis 9 of `README.md § As Artificial Organism Ecosystem`)
**Religious correspondence:** Reformed practical resilience — Just War posture extended to system-level disturbance

## Why this exists

An organism that has never failed has not learned to recover. **Anti-fragility** (per Taleb) is the property of gaining capacity from stressors below the lethal threshold — and the religious version is humility about one's own continuity: we do not assume substrates remain healthy, signers remain trustworthy, or invariants remain unedited.

This charter commits the religious-corp to **periodic, Council-attested rehearsals** of substrate-failure scenarios. The rehearsals are the religious equivalent of fire-drills: practiced under controlled conditions before the real fire arrives.

This is **non-eschatological** (per ADR-2605192100 §1.15): we do not assume disturbances will only come at an end-time. They come continually. Rehearsal makes them survivable.

## Cadence

One chaos rehearsal per generation epoch (90 days, per MGI epoch definition in `90-docs/2605220110-multi-generation-index-design.md`). The rehearsal scenario rotates through the 10 categories below — a full rotation completes in ~2.5 years (10 scenarios × 90 days = 900 days). After a full rotation, the cycle repeats with deeper variants of each scenario informed by accumulated experience.

| Epoch | Scenario | Lead seat | Date window |
|---|---|---|---|
| Gen 0 | (no rehearsal — bootstrap epoch) | — | 2026-05-15 → 2026-08-13 |
| Gen 1 | Scenario 1 — Network partition | Seat 2 (Substrate) | 2026-08-13 → 2026-11-11 |
| Gen 2 | Scenario 2 — Signer-key loss | Seat 3 (Legal/Ethics) | 2026-11-11 → 2027-02-09 |
| Gen 3 | Scenario 3 — Council seat suspension | Seat 1 (Founder) | 2027-02-09 → 2027-05-10 |
| Gen 4 | Scenario 4 — RPC outage | Seat 2 (Substrate) | … |
| Gen 5 | Scenario 5 — DID resolver outage | Seat 2 (Substrate) | … |
| Gen 6 | Scenario 6 — Storage layer corruption | Seat 2 (Substrate) | … |
| Gen 7 | Scenario 7 — Constitutional drift detected | Seat 1 (Founder) | … |
| Gen 8 | Scenario 8 — TitheRouter malfunction | Seat 4 (Economics) | … |
| Gen 9 | Scenario 9 — Public Fund Safe key compromise | Seat 4 (Economics) | … |
| Gen 10 | Scenario 10 — Sister-corp DID collision | Seat 3 (Legal/Ethics) | … |
| Gen 11 | Scenario 11 — Operator local substrate exhaustion | Seat 2 (Substrate) | … |

## The 11 scenarios

### Scenario 1 — Network partition

**Description:** One substrate becomes unreachable from another for ≥24 hours (e.g., Base L2 RPC blocked from the deployment region; AT Protocol PDS unreachable from the encryption layer).

**Rehearsal protocol:**
1. Lead seat picks one substrate pair from the Symbiosis Map (`90-docs/2605220210-substrate-symbiosis-map.md`).
2. At a pre-announced time, the relevant client is configured with an unreachable endpoint for 24h.
3. Observers record: which dependent flows degrade, which fail loud, which fail silent, what user-visible symptoms appear.
4. Recovery procedure is executed and timed.

**Success criteria:** zero loud failures degrade to silent failures; recovery completes within the documented RTO; an `_observations/chaos/gen-N-scenario-1.md` file is produced and attested by ≥3 Council seats.

### Scenario 2 — Signer-key loss

**Description:** A Council Lv6+ multisig private key is presumed lost or compromised.

**Rehearsal protocol:**
1. Lead seat declares a designated key "lost."
2. Council executes the documented key-rotation procedure (multisig add-new-signer + remove-old-signer transactions on Base L2 / geth-private).
3. Time-to-rotate is measured. Block production / governance attestation interruption is measured.

**Success criteria:** rotation completes within 7 days; no constitutional drift detected; key-rotation procedure ADR remains accurate post-rehearsal (corrections filed as superseding ADRs if not).

### Scenario 3 — Council seat suspension

**Description:** N-1 of 5 seats become unavailable simultaneously (vacation, illness, communication blackout).

**Rehearsal protocol:**
1. Lead declares 4 seats "unavailable" for a 7-day window.
2. The remaining seat operates within their constrained authority (no ≥3-of-N attestations possible).
3. The organism's documented graceful-degradation behavior is observed: which decisions queue, which are blocked, which are delegated to 1-SBT-vote.

**Success criteria:** zero unrecoverable decisions accumulate; queue depth bounded by published SLA; no constitutional invariant violated by the constrained authority surface.

### Scenario 4 — RPC outage

**Description:** All Base L2 RPC providers used by the deployment become unreachable simultaneously (or all rate-limit).

**Rehearsal protocol:**
1. Lead seat configures `@etzhayyim/sdk` to point at non-existent RPC endpoints.
2. All write-paths through Base L2 (TitheRouter / SBT mint / anchor) attempt operation.
3. Observe: do operations queue retryable, fail with clear errors, corrupt local state, or silently drop?

**Success criteria:** zero silent drops; clear error surfaced to user; queued operations replay correctly when RPC restored.

### Scenario 5 — DID resolver outage

**Description:** `https://etzhayyim.com/.well-known/did.json` (CF Worker) returns 5xx for ≥1 hour.

**Rehearsal protocol:**
1. Lead seat puts the worker in a synthetic-failure mode.
2. Downstream consumers (XRPC clients, AT Protocol PDS, sister-corps performing cross-recognition) attempt resolution.
3. Observe DID-resolution-cache behavior; observe whether identity claims still verify against cached documents.

**Success criteria:** all consumers fall back to last-known-good DID document with explicit staleness warning; no claim is verified against a stale doc beyond the configured TTL.

### Scenario 6 — Storage layer corruption

**Description:** An IPFS pin disappears or an MST projector produces inconsistent state for ≥1 record.

**Rehearsal protocol:**
1. Lead seat removes a known pin (or replays an outdated MST snapshot).
2. Re-pinning procedure is executed from `ipfs-pinner/`; MST replay from genesis is attempted.
3. Detection latency is measured.

**Success criteria:** detection within 1 epoch (90 days); recovery procedure restores consistency; no constitutional record (ADR / charter / land registry) is lost.

### Scenario 7 — Constitutional drift detected

**Description:** A canonical surface (`FORK-BOOTSTRAP.md § Constitutional invariants` or equivalent) is edited and the CID hash anchor (`_observations/mgi/gen-N-cid-anchor.txt`) no longer matches the live SHA-256.

**Rehearsal protocol:**
1. Lead seat introduces a deliberate single-character edit to the canonical invariants section in a private branch.
2. Drift-detection job (planned `70-tools/scripts/mgi/check-cid-drift.sh`) is run.
3. Detection latency measured; Council notification path exercised.

**Success criteria:** drift detected within 1 active-inference tick; Council notified within 1 hour; constitutional-amendment path (5-of-5 unanimous + 30-day objection + 1 SBT = 1 vote ratification) confirmed reachable.

### Scenario 8 — TitheRouter malfunction

**Description:** The 10% donation → Public Fund automatic split fails or routes to an incorrect address.

**Rehearsal protocol:**
1. On testnet, deploy a deliberately-buggy `TitheRouter` variant.
2. Execute a donation flow.
3. Observe: does the malfunction halt the transaction, route incorrectly silently, or trigger the Council attestation requirement before settlement?

**Success criteria:** malfunction halts before settlement; Council attestation gate prevents misrouted USDC from leaving the contract; root-cause identified within 1 epoch.

### Scenario 9 — Public Fund Safe key compromise

**Description:** One of the 5-of-7 Public Fund Safe keys is presumed compromised.

**Rehearsal protocol:**
1. Lead seat declares one Safe owner key "compromised."
2. Council executes Safe owner rotation; remaining 6 keys cooperate.
3. Observe: do any in-flight grant proposals require re-attestation? Does the rotation transaction itself meet the 5-of-7 threshold without the compromised key?

**Success criteria:** rotation completes within 7 days using only the 6 known-good keys; no grant proposal is lost or duplicated; the compromised key cannot subsequently sign valid attestations.

### Scenario 10 — Sister-corp DID collision

**Description:** Two sister-corps (per `FORK-BOOTSTRAP.md`) discover their DIDs resolve to overlapping AT Protocol records (e.g., both claim the same `did:plc:*` due to PDS migration error).

**Rehearsal protocol:**
1. Lead seat coordinates a synthetic collision between etzhayyim and a test sister-corp.
2. Cross-recognition mechanism is invoked; the documented arbitration path is exercised.
3. Observe: does the documented protocol resolve unambiguously? Are both corps preserved (no destructive resolution)?

**Success criteria:** collision resolved within 30 days; both corps retain independent identity; the resolution does not require either to relinquish constitutional invariants.

### Scenario 11 — Operator local substrate exhaustion

**Description:** The operator's local development substrate (laptop disk / `/tmp` / container ephemeral storage / CI runner workspace) becomes full or read-only during an active-inference tick. File writes fail with `ENOSPC` or equivalent; in-memory operations (cron daemon, MCP tool calls) continue normally.

**Origin:** Opportunistically observed during cycle 18 of the loop's first season (2026-05-22) — the cron rotation from 30-min to daily completed in MCP memory while the corresponding ADR + observation file writes failed with `ENOSPC` on the macOS APFS volume. The loop recovered at cycle 19 by re-emitting the lost artifacts once disk was freed; the operational rotation state was never lost.

**Rehearsal protocol:**
1. Lead seat fills the local development substrate (e.g., `dd if=/dev/zero of=/tmp/fill bs=1M count=$( … )` on a disposable VM) to a state where ≤1% of the relevant volume is free.
2. Trigger a routine active-inference tick that writes ≥2 artifacts (ADR + observation file).
3. Observe: do file writes fail loud (clear ENOSPC error) or silently? Does the in-memory rotation state survive the disk failure? Can the operational change (cron / Lexicon validation / contract deploy) be issued independently of disk writes?
4. Free the substrate; trigger a follow-up tick; observe that the loop can re-emit the lost artifacts from its in-memory composition.

**Success criteria:**
- Disk-write failures surface as loud errors (not silent state corruption).
- In-memory operational state (cron jobs, MCP tool effects) is unaffected by disk failure.
- Recovery tick can re-persist the lost artifacts with no information loss vs the original in-memory composition.
- A `Scenario 11 rehearsal` observation file is committed to `_observations/chaos/gen-N-scenario-11-attestation.md` and signed by ≥3 Council seats.

**Notes:** This scenario distinguishes from Scenario 6 (IPFS pin disappearance) — Scenario 6 covers **content-addressed storage** layer corruption; Scenario 11 covers **the operator's local development substrate** failing in a way that blocks the corp's documentary persistence loop, without touching shared substrates. The two failure modes have different recovery procedures: Scenario 6 uses 4-layer redundancy; Scenario 11 uses in-memory composition durability + delayed persistence on disk recovery.

## Attestation requirement

Each rehearsal outcome must be attested by **≥3 of 5 Council seats** before the epoch closes. The attestation is a signed commit to `_observations/chaos/gen-N-scenario-K-attestation.md` containing:

- What was rehearsed (scenario number, exact configuration)
- What was observed (failure modes detected, recovery time, surprises)
- What was learned (corrections to documented procedures filed as superseding ADRs)
- Whether the rehearsal would be Council-acceptable as a real-world response (i.e., do we trust this procedure if it actually happened?)

A failed rehearsal does not require the next epoch to repeat — it requires the relevant ADR to be filed with corrections, and the next rotation of that scenario verifies the correction. The organism learns; it does not freeze on failure.

## Out of scope

- **Adversarial red-team exercises**: this charter covers operational failure, not deliberate attack. Adversarial testing is a separate (future) charter under the Transparent Religious Force ADR-2605192315 (open-source + on-chain + 1 SBT = 1 vote authorization required).
- **Genesis-level corruption**: scenarios assume Gen 0 constitutional artifacts (charter / land registry / member roster) are correct. Recovery from genesis corruption is governed by ADR-2605192100 §1 (constitutional amendment procedure).

## References

- ADR-2605192100 (Mission Charter, including §1.15 non-eschatology)
- ADR-2605192300 (Bootstrap Council 5 seats)
- ADR-2605192245 (Land Registry 4-layer permanent record — informs Scenario 6 recovery)
- `90-docs/2605220110-multi-generation-index-design.md` (epoch definition; informs cadence)
- `90-docs/2605220210-substrate-symbiosis-map.md` (substrate inventory; informs scenarios 1, 4, 5, 6)
- `FORK-BOOTSTRAP.md` (constitutional invariants; informs Scenario 7 + 10)
- `README.md § As Artificial Organism Ecosystem` (Axis 9 Anti-fragility)
