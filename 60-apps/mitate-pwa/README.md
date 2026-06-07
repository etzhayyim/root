# mitate-pwa — religious-corp self-care advisory PWA (見立て)

**Status**: R0 scaffold — Worker contract locked, runtime returns **503** until R1 baseline attestations land per [ADR-2605260200](../../90-docs/adr/2605260200-mitate-r1-advisory-self-care-pwa.md).

Per:
- [ADR-2605260100](../../90-docs/adr/2605260100-mitate-diagnostic-routing-charter.md) — mitate master charter
- [ADR-2605260200](../../90-docs/adr/2605260200-mitate-r1-advisory-self-care-pwa.md) — R1 self-care advisory PWA

Patient-facing PWA for chronic nasal congestion 5-condition triage advisory. Standalone app (separate from `ameno-pwa`) for medical disclaimer UX integrability + future R2 MD-dashboard divergence.

## Activation gate (R1 deploy)

Worker returns `503 MitateR1PhaseGateLocked` until `MITATE_R1_PHASE_GATE` env var is set to a non-`locked` value. Setting requires Council Lv6+ ≥ 3 multisig attestation of:

1. `charter-baseline` (silenMitateReview)
2. `g3-disclaimer-text-baseline` + 1 licensed MD co-sign
3. `g5-emergency-keyword-baseline` + 1 emergency medicine specialist
4. `g5-false-negative-adversarial-testing-baseline` + 1 emergency medicine specialist
5. `g6-escalation-protocol-baseline` + 1 licensed MD
6. `g11-intake-form-text-review`
7. `g11-notification-channel-baseline`
8. `condition-{1..5}-bayesian-prior-baseline` (5 separate, 1 licensed MD co-sign each)

Plus: ≥ 1 licensed MD on Council medical advisory + 1 emergency medicine specialist registered for G5 attestations.

## Constitutional invariants enforced at the routing layer

| Gate | Enforcement point | Test |
|---|---|---|
| **G3** disclaimer-first | `/triage` + `/medication-audit` 303 → `/disclaimer` until ack present | `tests/g3-disclaimer-flow.test.ts` |
| **G5** emergency_screen pass-through | POST `/xrpc/com.etzhayyim.mitate.triageVerdict` → 405 `G5InvariantBlocked` | `tests/g5-emergency-bypass-impossible.test.ts` |
| **G11** notification 3-channel only | `/notify/{channel}` checks `G11_ALLOWED_NOTIFICATION_CHANNELS` | `tests/g11-no-addictive-design.test.ts` |
| **G14** substrate boundary | all substrate writes via `proxyToSubstrate()` → `ETZHAYYIM_SDK_PROXY_URL`; no direct AT MST / IPFS / viem / noble-ciphers / libsignal imports | `tests/g14-substrate-boundary.test.ts` |

## R1 active vs R2 gated lexicon NSIDs

R1 active (4):
- `com.etzhayyim.mitate.rhinitisIntake`
- `com.etzhayyim.mitate.triageVerdict` (read-only — POST blocked per G5)
- `com.etzhayyim.mitate.emergencyEscalation`

R2 gated (return 503 `MitateR2GatedLexicon`):
- `com.etzhayyim.mitate.diagnosticOrder`
- `com.etzhayyim.mitate.diagnosticResult`
- `com.etzhayyim.mitate.treatmentPlan`
- `com.etzhayyim.mitate.outcomeFollowup`

## App layout

```
60-apps/mitate-pwa/
├── kotodama.jsonld           # app metadata + constitutional gates registry
├── wrangler.jsonc            # CF Worker config; routes mitate.etzhayyim.com/*
├── package.json              # typecheck + vitest
├── tsconfig.json
├── src/
│   └── app.ts                # Worker entry: phase gate + routing invariants + substrate proxy
├── public/                   # static patient-facing HTML
│   ├── index.html            # disclaimer-first landing
│   ├── disclaimer.html       # G3 + G1 + G6 triple-ack
│   └── emergency.html        # G5 ER routing display
├── tests/                    # G3 / G5 / G11 / G14 invariant assertions
│   ├── g3-disclaimer-flow.test.ts
│   ├── g5-emergency-bypass-impossible.test.ts
│   ├── g11-no-addictive-design.test.ts
│   └── g14-substrate-boundary.test.ts
└── README.md                 # this file
```

## What R1 implementation lands on top of this scaffold

- `verifyDisclaimerAck()` real implementation: session cookie + consent receipt CID resolution against MST
- 30-day rotating pseudonym DID derivation in browser (passkey ES256 + HKDF)
- Patient intake form HTML (per condition top-7 sign signature + medication history + trigger diary)
- Triage verdict display HTML (G3 disclaimer overlay before posterior probabilities reveal)
- Emergency overlay JS (intercepts patient input on red-flag signal, displays ER routing)
- Medication audit display HTML (condition 5 — 3-tier withdrawal protocol selection)
- Substrate proxy worker (intermediate `substrate-proxy.etzhayyim.com` worker that wraps @etzhayyim/sdk — keeps the patient-facing Worker network surface minimal)

## Phasing

| Phase | Worker behavior | Cells active |
|---|---|---|
| R0 (this commit) | 503 — phase gate locked | 0 (all import-time RuntimeError) |
| R1 (post-baseline attestations) | advisory tier — intake / triage / medication-audit / emergency-screen | 4 |
| R2 (post-Hanami + licensed MD ≥ 2 + community center) | + diagnostic ordering + treatment routing + QOL followup | 11 |
| R3 (post-60-day public review + 薬事/医療機器手続き) | + SLIT cohort + ESS surgery planner + Kafun-watch | 13 |

## License

Apache 2.0 + [Charter Compliance Rider v2.0](../../CHARTER-RIDER.md).
