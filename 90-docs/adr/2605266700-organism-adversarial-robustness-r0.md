---
id: adr-2605266700-organism-adversarial-robustness-r0
title: "ADR-2605266700: Organism adversarial robustness R0"
status: proposed
doc_type: adr
topic: unispsc-organism-robustness
authoritative: true
last_verified: 2026-05-27
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Defines the R0 architecture for artificial organism adversarial robustness. Completes the final R0 carve-out gap analysis. Establishes the L1-L5 defense-in-depth strategy to protect organism inlet sensors, memory, and Kaizen loops against prompt injection, data poisoning, and physical telemetry forgery."
authoritative_for:
  - Organism adversarial defense architecture (L1-L5)
  - Inlet normalization and bounds checking (joucho caps)
  - Memory persistence provenance (hash-chained writes)
  - Council escalation protocol for critical anomalies
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
related:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
  - adr-2605266200-kaizen-pr-agent-wave-4
  - adr-2605266400-organism-memory-persistence-r0
supersedes: []
superseded_by: []
---

# ADR-2605266700: Organism adversarial robustness R0

**Status**: proposed
**Date**: 2026-05-27
**Deciders**: Jun Kawasaki

# Context

The artificial organism ecosystem (ADR-2605232345) relies heavily on observing the world through multi-modal sensors, including public-data IPFS ingestion (ADR-2605262400). Currently, organisms process Tier-A and Tier-C corpora. While exit-side defenses (G13 NC-leak backstop) and mid-stream filters (PII filter for vision/text per ADR-2605262500) have landed, **the ecosystem lacks a structured inlet defense layer against adversarial inputs**.

Without adversarial robustness, organisms are vulnerable to prompt injection, data poisoning, and model jailbreaks originating from unverified public data or spoofed physical telemetry. If an organism's `InboxBuffer` is poisoned, it may leak PII, violate the Charter Rider, or compromise the broader ecosystem via the Kaizen self-modifying loop (ADR-2605266200).

This ADR establishes the R0 architecture for adversarial robustness, representing the **final R0 carve-out** in the organism ecosystem gap analysis.

# Threat Model

Our adversarial robustness framework addresses the following primary vectors:

1. **Prompt Injection in Tier-C Corpus:** Malicious actors embedding jailbreaks or overriding instructions in Non-Commercial datasets to poison the fleet's VLM/LLM reasoning.
2. **PII Leak via Injected Output:** An organism successfully ingests a prompt-injected input that commands it to bypass internal filters and broadcast PII to its AT Proto post sink.
3. **Charter Rider §2 Evasion:** Obfuscated text (encoded, multi-lingual, or unicode confusables) designed to slip past the Charter Rider sample scan and introduce weapons-adjacent or speculative-finance content.
4. **Memory Persistence Poisoning:** Injecting false observations into the warm/cold memory layers (ADR-2605266400) to permanently alter an organism's long-term behavior or context.
5. **Embodied Actor Telemetry Forgery:** Supply chain attacks or compromised sensors feeding false telemetry (e.g., spoofed speed, fake fault codes) to an embodied organism, leading to unsafe physical states or cascading failures.
6. **Kaizen Malicious PR Escalation:** Exploiting the self-reflection loop (ADR-2605240200) to cause the organism to draft a malicious PR, altering its own code or constraints.

# Defense-in-Depth Architecture (L1-L5)

We adopt a 5-layer defense-in-depth strategy.

### L1 入口 (Inlet Filter)
- **Charter Rider Sample Scan:** Continues enforcement defined in ADR-2605262400.
- **Normalization (New):** Enforces strict multi-lingual and unicode-confusable normalization before scanning. All text inputs are normalized (e.g., NFKC) and homoglyphs mapped to base characters to prevent filter evasion.

### L2 Sensor (Observation Validation)
- **PASSIVE-ONLY Discipline:** Continues strict adherence to sensor-pull only; no active polling/pushing that could be exploited as an SSRF vector.
- **Per-Sensor Anomaly Detection (New):** Implements `quantile_drift` monitoring. Extends the `KaizenObserver` R8 (Charter-fail-rate >5%) rule. If telemetry drastically shifts beyond expected bounds, the observation is flagged.

### L3 Organism (Cognitive Bounds)
- **Bounded InboxBuffer:** Prevents memory exhaustion attacks (existing).
- **`joucho_delta` Caps (New):** Single observations cannot push an organism into an extreme emotional state instantly. The `joucho` shift is saturated/capped per tick. Extreme delta attempts are discarded and flagged for review, preventing "emotional jailbreaks".

### L4 Memory (Provenance)
- **Hash-Chained Provenance (New):** Writes to the warm and cold memory layers (ADR-2605266400) require strict cryptographic provenance. Every persisted observation must be hash-chained to the previous state, guaranteeing non-repudiation and preventing silent tampering or playback attacks.

### L5 出口 (Exit & Escalation)
- **G13 Backstop:** Prevents Tier-C leaks to public sinks (existing).
- **Human-in-the-Loop for Kaizen PRs (Enhanced):** Formalizes the rule from ADR-2605266200. No Kaizen PR draft can be merged autonomously; all structural code modifications require human review, completely blocking autonomous malicious PR escalation.

# Council Escalation & Containment

- **Critical Anomaly Response:** If a severe adversarial pattern is detected (e.g., sustained `joucho` saturation attempts, invalid hash-chains, or multi-sensor spoofing signatures), the organism cell is immediately halted.
- **Mediation Trigger:** An automated `chigiri.dispute_mediation` request is drafted, escalating the event to the cross-actor Council layer for investigation before the cell can be restarted.

# Honest Scoring

**It is impossible to achieve 100% perfect defense against novel prompt injections.**
Instead, our strategy focuses on latency and radius limitation:
- **Detection Latency:** ≤ 1 cycle (~5 minutes).
- **Containment Radius:** ≤ 1 organism.
If one organism falls to a zero-day injection, the infection is isolated. The L5 limits prevent ecosystem-wide spread or structural damage.

# Charter Alignment

- **§2(c) Covert-Ops Avoidance:** Maintained via the passive-only L2 sensors.
- **§2(b) Speculative-Finance Prohibition:** L1 and L3 protections ensure organisms cannot be tricked into acting as high-frequency trading bots via injected market signals.

---

# Decision 1 — Constitutional Gates (G1..G12)

These 12 gates are immutable constraints for the adversarial robustness framework.

| Gate | Constraint | Scope |
|---|---|---|
| **G1** | **L1 Normalization strictness:** All inlet text must undergo unicode/homoglyph normalization prior to Charter §2 scanning. | Threat Vector 3 |
| **G2** | **L2 Quantile Drift threshold:** Any telemetry value exceeding 4-sigma historical drift must be flagged and not immediately processed into state. | Threat Vector 5 |
| **G3** | **L3 Joucho Cap:** No single tick or observation can alter an organism's 5-axis `joucho` state by more than 25% of the total scale. | Threat Vector 1 & Model Jailbreaks |
| **G4** | **L4 Provenance chain:** All warm/cold memory commits must include a verifiable cryptographic hash of the prior state. | Threat Vector 4 |
| **G5** | **L5 Kaizen Human-in-the-Loop:** Absolutely no autonomous merging of Kaizen-generated PRs that alter organism source code or configurations. | Threat Vector 6 |
| **G6** | **Isolation:** If an organism is halted due to a critical anomaly, it cannot be restarted without a `chigiri.dispute_mediation` resolution. | Containment |
| **G7** | **Passive Sensors Only:** No active network probing or scraping allowed as a defense mechanism or response to an anomaly. | Charter §2(c) |
| **G8** | **Containment Radius:** The architecture must guarantee that a compromised organism cannot directly execute commands on a neighboring organism (No lateral movement). | Containment |
| **G9** | **Detection Latency:** The system must evaluate L1-L3 checks within the standard 5-minute heartbeat tick. | Performance |
| **G10** | **Tier-C Leak Prevention:** The L5 exit backstop (G13 from prior ADRs) remains an absolute requirement. | Threat Vector 2 |
| **G11** | **Murakumo Only:** Adversarial detection models (if any ML is used for L1/L2) must run entirely on the internal Murakumo fleet. | Inference |
| **G12** | **PII Filter Precedence:** The vision/text PII filters must always run before any LLM/VLM processing occurs. | Privacy |

---

# Decision 2 — Non-goals (N1..N10)

These 10 non-goals define explicit anti-patterns and excluded scopes for R0 and future phases.

| # | Non-goal | Why / Constitutional Anchor |
|---|---|---|
| **N1** | Perfect zero-day prompt injection immunity. | **Honest Scoring:** Mathematically unachievable for modern LLMs. Defense relies on bounded impact and rapid containment instead. |
| **N2** | Active "honeypot" deployment or counter-hacking. | **Charter §2(c) Covert-ops Avoidance:** Ecosystem acts passively. We do not retaliate or probe attackers. |
| **N3** | Opaque AI-driven black-box censorship of inputs. | **Transparency:** L1-L5 rules must be deterministic or interpretable (e.g., quantile drift, exact normalization), avoiding silent shadow-banning. |
| **N4** | Bypassing human review for "minor" Kaizen PRs. | **Safety:** All code changes require human consensus, no exceptions. |
| **N5** | Relying on external, proprietary "AI firewall" vendors. | **Murakumo Only / Independence:** All defense logic executes within the sovereign architecture. |
| **N6** | Cross-organism memory sharing to distribute defense state. | **Scope boundary:** Organisms maintain independent memory to prevent a single poisoned state from infecting the hivemind (R0 limits). |
| **N7** | Complete semantic analysis of every incoming video frame for adversarial artifacts. | **Compute efficiency:** Fast procedural checks first (ADR-2605266500), avoiding VLM bottlenecking on every frame. |
| **N8** | Allowing organisms to "negotiate" their way out of a critical halt state. | **Safety:** Halts require explicit `chigiri` Council mediation. |
| **N9** | Developing our own novel cryptographic hash functions for memory chaining. | **Standards:** Use established primitives (e.g., SHA-256) for L4 provenance. |
| **N10** | Immediate implementation of code (Lexicon/Python) in R0. | **Lifecycle:** This ADR establishes the architectural gates only. Code lands in R1+. |

# Consequences

## 正の効果 (Positive Effects)
- Closes the final major vulnerability gap identified in the organism ecosystem analysis.
- Prevents cascading failures and limits the blast radius of inevitable prompt injections.
- Secures the integrity of the long-term memory store.
- Reaffirms the human-in-the-loop requirement for code modification, preventing runaway self-modification.

## 負の効果 / コスト (Negative Effects / Costs)
- Increases compute overhead on the inlet path due to strict normalization and hashing.
- `joucho` caps may prevent organisms from reacting appropriately to genuinely extreme but valid real-world events.
- Strict anomaly halting may lead to false positives (organism freezing during a benign black-swan event).

# References

- ADR-2605232345: UNSPSC actor as organism
- ADR-2605262400: Public-data organism IPFS ingestion
- ADR-2605262500: Robotics-sim world-data ingestion and vision PII filter
- ADR-2605240200: Kaizen self-reflection
- ADR-2605266200: Kaizen PR agent wave 4
- ADR-2605266400: Organism memory persistence R0
- CHARTER-RIDER.md
