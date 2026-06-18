---
id: adr-2606181200-r2-autonomous-gate-removal-member-signed-capability-reconciliation
title: "ADR-2606181200: R2-Autonomous live-gate removal — member-signed-capability reconciliation (6 actors)"
status: proposed
doc_type: adr
topic: r2-autonomous-live-gate-removal
authoritative: true
last_verified: 2026-06-18
priority: 8.0
axis: charter-compliance
weight: 0.80
priority_note: "Tier-1 substrate invariant (no-server-key) was regressed across 6 actors; this ratifies the fix."
authoritative_for:
  - r2-autonomous-live-gate-removal-resolution
depends_on:
  - 2605231525  # no-server-key religious-corp architecture
  - 2605215000  # Murakumo-only inference
  - 2606111400  # ibuki/mimamori member-signed CACAO capability
related:
  - 90-docs/260617-r2-autonomous-live-gate-removal-charter-audit.md
  - 20-actors/ossekai/FINDING-G7-autonomy-conflict.md
  - 2606052300  # fuchi R2
  - 2606073100  # abaki R2
  - 2605264000  # ossekai R2
  - 2606071400  # omise
  - 2606071500  # ainori
  - 2606071600  # shukubo
supersedes: []
superseded_by: []
---

# ADR-2606181200: R2-Autonomous live-gate removal — member-signed-capability reconciliation (6 actors)

**Status**: proposed (Council attestation = PR review, per root CLAUDE.md bootstrap premise)
**Date**: 2026-06-18
**Deciders**: Jun Kawasaki

# Context

A recurring "R2 Autonomous" change pattern had, across **6 actors**, replaced an actor's live
outward-action gate with one that proceeds **without a member/operator/Council signoff** —
substituting a server-held synthetic credential or auto-marking an unsigned settlement as
executed. This regresses the Tier-1 substrate invariant **no-server-key** (ADR-2605231525) and
the per-actor outward-gating / no-auto-execute gates. Surfaced 2026-06-16/17 by failing tests
(`ossekai/py/test_agent.py`, `fuchi.methods.test-live-gate`) during the cljc port wave and
audited in `90-docs/260617-r2-autonomous-live-gate-removal-charter-audit.md`.

Two severities were found:

- **SEVERE (fuchi, abaki, ossekai)** — a `live_gate` / publisher turned always-admissible with a
  **synthetic server-held signature** (`autonomous_system_signature`) standing in for the
  member/operator/Council signoff; G7/G10/G2 refusals stripped. abaki was worst: a GREEN CI test
  (`test-r2-gate-always-admissible`) actively **ratified** the bypass.
- **MILD (ainori, omise, shukubo)** — `build_settlement_intent` unconditionally set
  `state="executed"` on an **unsigned** intent, bypassing the operator-gate and the member-signed
  `authorize_settlement`; G7-equivalent (no-server-key) settlement refusal otherwise held. omise
  also had a GREEN test ratifying the auto-execute; shukubo's regression was entirely unguarded.

# Decision

Adopt **Option 1 — member-signed-capability autonomy** (the ibuki/mimamori precedent,
ADR-2606111400) as the uniform resolution for the whole pattern, and reconcile each actor's code
**and its tests** accordingly. R2 autonomy is preserved **without a server-held key**: a member
pre-signs a scoped, revocable capability in their own runtime which the autonomous loop
**presents** (never holds); the write is attributed to the consenting member.

Concretely, as landed 2026-06-17/18:

1. **fuchi** — `methods/live_gate.cljc` rewritten: refuse-by-default, ordered checks (operator
   flag → attestation → Council Lv6/Lv7-couple → member signature), `server-or-blank-signer?`
   rejects blank/anon/server/`autonomous_system_signature`; the contradictory `live_gate.py` twin
   pruned. `test-live-gate` re-registered in `test:fuchi`.
2. **abaki** — `methods/live_gate.cljc` rewritten (one publish leg, Council Lv6); the GREEN
   ratifying test reconciled to assert refusal-by-default + the member-capability path; `publish-live`
   de-autonomized.
3. **ossekai** — `py/agent.py` gains a shared `_outward_authorized()` gate behind all 4 outward
   handlers (operator attestation OR a presented member capability; else `:draft`, no broadcast);
   `_attestation_ok` (G13 Council Lv6+ ≥3/≥4) restored.
4. **ainori / omise / shukubo** — `build_settlement_intent` →
   `state = "executed" if operator_ref else "intent"`; `authorize_settlement` transitions a
   member-signed intent → `executed`; omise's bypass-ratifying test reconciled, shukubo's missing
   guard added.

**Invariants reaffirmed (never to be relaxed by an "autonomous" change):** no platform-held
private key (ADR-2605231525); a synthetic/server signer is refused; live outward legs refuse by
default and require operator attestation OR a member-signed capability; no settlement executes
unsigned; Murakumo-only inference (ADR-2605215000).

# Consequences

- All 6 actors' suites are green with the restored gates; no CI test asserts an always-admissible
  gate or an unsigned auto-executed settlement (the two ratifying tests were corrected, not the
  code weakened).
- Autonomy is retained: an actor can still act without a human in the live loop **iff** a member
  has issued a scoped capability (or an operator attests) — accountability by consent.
- Future "autonomy" upgrades MUST route through this pattern; a synthetic server credential is a
  charter regression, not a feature. New live-gate code should ship a refusing-by-default test.

# Alternatives Considered

- **Option 2 — restore pure operator/Council gating** (no autonomy): makes the suites pass but
  abandons the R2 autonomy goal; rejected as unnecessarily restrictive given Option 1 preserves
  both autonomy and no-server-key.
- **Option 3 — document an explicit G7 exemption** (Council Lv7+ + `// no-server-key:` marker):
  rejected — a synthetic server-held signature is the exact thing no-server-key forbids; the bar
  is not available for a convenience autonomy path.

# References

- ADR-2605231525 (no-server-key religious-corp architecture)
- ADR-2606111400 (ibuki/mimamori member-signed CACAO capability — the charter-clean autonomy path)
- ADR-2605215000 (Murakumo-only inference)
- `90-docs/260617-r2-autonomous-live-gate-removal-charter-audit.md` (the cross-actor finding + per-actor resolution table)
- `20-actors/ossekai/FINDING-G7-autonomy-conflict.md` (the first instance)
