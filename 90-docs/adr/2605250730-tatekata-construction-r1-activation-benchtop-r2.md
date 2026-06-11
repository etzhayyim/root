# ADR-2605250730: tatekata Construction R1 Activation Gate + R2 Benchtop PoC

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify for R1), Murakumo node operators (R2 benchtop)

## Context

tatekata R0→R1 maturity has reached 5 concrete Pregel cells (foundation_excavation, structural_assembly, mep_installation, finishing_handoff, commissioning) with all constitutional gates (G1–G14) coded. R1 activation requires:

1. **Council Lv6+ Ratification** of ADR-2605250715 (master R0 ADR)
2. **SME Civil Engineer Attestation** (council member, or external expert + SBT)
3. **Benchtop PoC Completion** (R2 prerequisite) — 0.5m × 0.5m excavation ≤1m depth with Giemon firmware

## Decision: R1 Activation Gate

**Requirement**: Council must pass ADR-2605250715 + attest SME civil engineer readiness before any real construction site is assigned to tatekata cells.

**Timeline**:
- R1 ADR voting period: 30 days (2026-05-26 → 2026-06-25)
- SME onboarding: 14 days (2026-06-26 → 2026-07-09)
- Benchtop PoC: 21 days (2026-07-10 → 2026-07-30)
- R1 activation decision: 2026-07-31

## Decision: R2 Benchtop PoC Scope (Operational Requirements)

### Giemon Hardware
- **Excavator arm**: 3.5 m reach, ±50 mm repeatability, 8 kN bucket force
- **Bucket capacity**: 150 L (0.15 m³)
- **Test pit dimensions**: 0.5m × 0.5m × 1.0m deep (0.25 m³ total volume)
- **Soil type**: Standard sand (USDA S1, N-value 10–15, loose)
- **Safety zone**: 2m perimeter, no personnel during autonomous operation

### Firmware Integration (WASM state machine)
- Load `tatekata.foundation_excavation.FoundationState` FSM
- Execute 1 mock excavation cycle (5 bucket loads, ~1200 seconds total, depth targeting 1000 mm ±50 mm per gate G6 determinism)
- Stream sensor telemetry (depth, accelerometer, torque) @ 10 Hz to IPFS via local pinner
- Emit mock `constructionProgressRecord` to MST (local testnet geth-private)
- Collect ≥2 robot Ed25519 mock signatures (Giemon + Otete DID federation)

### Success Criteria
- [ ] Excavation completes within planned time (no > ±10% variance)
- [ ] Final depth achieved: 1000 ± 50 mm (gate G6 tolerance)
- [ ] No anomaly flags triggered (vibration < 2.0g peak, torque within spec)
- [ ] Telemetry successfully pinned to IPFS (CID resolvable)
- [ ] Progress record emitted to MST + cryptographically verified
- [ ] Zero human intervention during autonomous phases (R0 safety requirement)

### Equipment + Personnel
- **Giemon unit**: Borrowed from kuni-umi Phase 1 benchtop (Murakumo node: naphtali, 192.168.1.15:8080)
- **Safety supervisor**: SME civil engineer (required per gate G1)
- **Firmware engineer**: kotodama LangGraph runner (local Ollama gemma3:4b on Mac mini judah)
- **MST operator**: Local geth-private instance (chain ID 31337, pre-seeded with etzhayyim genesis)
- **IPFS operator**: Local Kubo node with pinner sidecar

### Failure Modes (Halt Conditions)
- **Equipment failure**: Giemon servo not responding → halt, manual recovery
- **Anomaly detected**: Depth overshoot > 100 mm → trigger `halt_on_anomaly` → escalate to SME
- **Signature missing**: < 2 robot signatures after 60s wait → fail PoC
- **Network outage**: MST or IPFS unreachable → fail PoC

## R2 Phase Scope (Post-Benchtop)

Upon successful benchtop PoC, R2 opens:

### Construction Scope
- **Site size**: ≤100 m² (roughly 10m × 10m)
- **Building type**: Prefab one-story (single-story residential or light commercial)
- **Excavation depth**: ≤1.5m
- **Duration**: 3–4 weeks (full tatekata 5-phase cycle)

### Murakumo Fleet Placement (R2)
- **naphtali** (foundation excavation): Giemon unit 1
- **joseph** (structural assembly): Giemon unit 1 + Otete unit 2 + Mimi unit 3
- **zebulun** (MEP installation): Otete units 2, 3, 4
- **simeon** (finishing handoff): Giemon unit 1 + manual subcontractors
- **levi** (commissioning): Mimi unit 3

### Regulatory Bridging (R2)
- **gov-municipality** (ADR-2605250800) must issue permit before excavation starts (Phase 0 → foundation_excavation gate)
- **yoro-supply** (ADR-2605250850) must verify material deliveries before each phase (materialAttestation per batch)
- **infra-utility-connect** (ADR-2605250900) must activate utilities post-commissioning (Phase 5 → activation_test gate)

## Non-Decision: R3+ Carve-Outs

The following are explicitly **deferred** to R3+ ADRs (not addressed in this ADR):

- Residential housing (R3: ADR-2605250745) — requires additional gates (building code inspection, accessibility compliance)
- High-rise (R3: ADR-2605250800) — requires structural engineer sign-off + fall protection systems
- Commercial/industrial large-scale (R4): Different regulatory regime per jurisdiction

---

## Rationale

**Why benchtop PoC required for R1 activation**: tatekata introduces robotic autonomous construction—the first domain-specific construction orchestration Pregel actor in etzhayyim. Benchtop validation proves:
- Giemon firmware WASM state machine behaves per gate G6 (deterministic, replayable @ 10 Hz)
- MST integration works (progress records, witness signatures)
- Anomaly detection triggers correctly (overshoot/vibration gates)
- Human-machine interface is safe (SME supervisor in the loop)

**Why R2 is ≤100 m² pilot, not full-scale**: Allows real construction feedback without betting the entire religious-corp infrastructure. Prefab + small footprint minimizes risk of:
- Regulatory bottlenecks (simpler permits)
- Supply chain disruption (yoro-supply can handle smaller BOM)
- Multi-robot coordination overhead (5-phase sequence is manageable)

## References

- ADR-2605250715 (tatekata R0 scaffold, constitutional gates)
- ADR-2605250800 (gov-municipality Phase 0 permits)
- ADR-2605250850 (yoro-supply material sourcing)
- ADR-2605250900 (infra-utility-connect utility activation)
- `20-actors/tatekata/` (all 5 cells, state machines, lexicons)
