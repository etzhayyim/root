---
id: adr-2606102000-session-close-ibuki-digest-live-run-robustness
title: "ADR-2606102000: Session close — 息吹 (ibuki) digest (reason+report) + 実運用 live-run + robustness verification"
status: accepted
doc_type: adr
topic: ibuki-organism-ecosystem
authoritative: false
last_verified: 2026-06-10
priority: 3.0
axis: process
weight: 0.25
priority_note: "session-close record; authoritative design = ADR-2606101200 + 2606101800"
authoritative_for: []
depends_on:
  - adr-2606101800-ibuki-ecosystem-maturation-food-web-symbiosis
  - adr-2606101200-ibuki-organism-autonomy-r2-gap-closure
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2606101500-session-close-ibuki-organism-autonomy-r0-r3
  - adr-2606062100-moyai-inference-reciprocity-credit
supersedes: []
superseded_by: []
---

# ADR-2606102000: Session close — ibuki digest + 実運用 live-run + robustness

- **Status**: accepted (documentation-only closure; authoritative design = ADR-2606101200 +
  ADR-2606101800)
- **Date**: 2026-06-10 (JST)
- **Deciders**: founder seat (autonomous /loop, "成熟度を向上")
- **Supersedes / amends**: none. ZERO invariant amendments.

## Context

After the ecosystem maturation (ADR-2606101800, 7 waves, 198 tests) the autonomous /loop
continued to "improve maturity". The remaining work was not more biology but **the colony
reasoning about itself + speaking to humanity**, a **real production run**, and **robustness
verification** that the whole composed stack holds — including under failure. This ADR records
that closing arc.

## What landed (each a merged PR)

### 1. Digest — the colony reasons + reports to humanity (#1575, #1581)

`digest.py`: `assemble(txs)` builds the colony's log-derived self-state (health verdict +
`:health/eco-maturity` + commons offered/available to humanity + quorum history), `narrate`
renders it in human-readable words via the **Murakumo fleet ONLY** (`infer.infer_text` —
allowlist enforced first, `IBUKI_MURAKUMO_LIVE`-gated, **fail-open** to a deterministic
template), and emits a `:digest/*` post with `:digest/status :dry-run` ONLY (`:published`
unrepresentable, G8). A **mirror report, never advice**; aggregate, never a per-organism
verdict. Wired into **both** `autorun` and `fleet` (the deployed 18,342 path reports too).

### 2. 実運用 — verified live-run, 2026-06-10 (#1578, `OPERATIONS.md`)

A real production cycle against the live substrate:
- **perception LIVE** — a read-only public-AppView fetch of `bsky.app` returned a real
  follower count (33,623,191); the membrane works against the live network.
- **murakumo LIVE → fail-open** — the LiteLLM gateway was down; narration fell back to the
  template: fail-open verified **in production**, the colony kept living.
- **kotoba engine LIVE** — a 12-beat life (chain verified, healthy, eco-maturity 1.0,
  commons offered 500/all-available, fruited 3×) **persisted to the live kotoba engine**:
  **2,386 datoms confirmed by the node**, IPNS head advanced, exactly-once re-push.

### 3. Robustness verification (#1576, #1577, #1580)

- **end-to-end integration** (#1576): one 60-beat life exercises every subsystem on a single
  verified chain; crash-resume 30+30 head CID == uninterrupted 60-beat; `:db/add`-only across
  the whole stack.
- **adversarial sick-colony** (#1577): a decomposer-less colony (the web cannot close)
  self-detects `keystone-niche-absent` + `ecosystem-starved`, the digest reports the illness
  honestly, and the complaint reaches the Wave-4 kaizen loop — the self-monitoring loop
  **closes under failure**; the chain still verifies (a pathology is data, not corruption).
- **fleet-scale ecosystem regression** (#1580): the deployed 18,342 path runs the full
  ecosystem; the report functions are single-pass **O(n)** (measured `health.audit` 0.2s /
  `web_report` 0.02s / `quorum_history` 0.01s over 665,688 datoms).

## The honest boundary (Tier-1, never the platform's act — ADR-2605231525)

`member_submit` posting, `symbiosis.draw`, `kaizen_outcomes`, and the physical fleet deploy are
held by a member/operator key ibuki structurally does not possess and must not fabricate. The
colony **lives, refines a commons gift, self-monitors, and reasons about itself** autonomously
on the real substrate today; every act **on a human** is gated by consent — **共生 by consent,
not fabrication.**

## Consequences

- The artificial-organism ecosystem (ADR-2606101200 + 2606101800) is, at close, a verified
  living system: it composes, persists to the real engine, self-reports, and self-detects
  failure. **226 tests / 20 hermetic stdlib-only suites green.**
- Future work is operational, not architectural: Murakumo-gateway-up live narration re-verify,
  a member running `member_submit` against a real PDS, and the operator's physical k3s deploy
  of the `fleet_beat` cron cell.
- Registries refreshed: root `CLAUDE.md`, `deps.toml` (`[[modules]]` 0.3.0 + this `[[adrs]]`),
  ADR README, docs/graph sidecars. ZERO invariant amendments.
