---
id: adr-2605242100-baien-server-xl-carve-out
title: "Baien-server / baien-XL carve-out from edge invariant — 4-tier ladder (edge / bonsai / server / XL)"
status: accepted
doc_type: adr
topic: baien-server-xl-carve-out
authoritative: true
last_verified: 2026-05-24
authoritative_for:
  - non-edge baien variant naming + scope
  - 4-tier ladder (edge / bonsai / server / XL)
  - which invariants stay vs. drop per tier
  - Charter Rider + Murakumo applicability across tiers
depends_on:
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605231300-baien-distill-react-loop
  - adr-2605241930-baien-mx-move4-audio-graft
related:
  - 70-tools/baien-mx-train/
  - runbook-bitnet-cpp-evo-x2-build
supersedes: []
superseded_by: []
---

# Context

ADR-2605241900 codifies the **baien edge-target invariant**: 8 hard
ceilings (trunk ≤ 4 B, weights ≤ 1.6 GB, RAM @ 4 k ≤ 2.0 GB, RAM @ 16 k
≤ 2.5 GB, ctx ≤ 16 384, frozen encoders, cumulative encoder ≤ 600 MB,
iPhone-14 first-token ≤ 3 s). These are **constitutional** — a Council
Lv6+ supermajority is needed to amend.

The invariant is correct for the edge promise, but it leaves three
legitimate non-edge research use cases out in the cold:

1. **Frontier comparison runs** — apples-to-apples bench against
   Opus / GPT-5 / Gemini / Qwen-Max at the tier where they actually
   live (frontier-bench-snapshot-260523 §A) requires running a much
   larger BitNet-shape variant, not the 2 B edge artifact.
2. **Distillation teacher generation** — ADR-2605231300's
   `select_teacher` fallback (when HF dataset path fails) needs a
   trustworthy teacher whose outputs we own; running an >4B BitNet
   variant on EVO-X2 to generate teacher signals does not threaten
   the edge invariant if the artifact is named clearly.
3. **Internal benchmark runs on EVO-X2-class hardware** — single 80 GB
   GPU / 128 GB unified Apple Silicon / Ryzen AI Max+ class machines
   can comfortably host 16 B-class BitNet models for research even if
   they will never be shipped to phones.

Without a carve-out, every experimental > 4 B run violates the
invariant and (in spirit) requires a Council vote. That is too high a
bar for routine R&D and would gate ordinary experiments behind
constitutional process.

ADR-2605241900 §"Carve-out" already names `baien-server-*` and
`baien-XL-*` as out-of-scope. **This ADR fleshes that carve-out into a
4-tier ladder** with explicit rules for what stays in-scope of the
constitutional layer and what does not, while keeping Charter Rider
§2(a)-(h) and the Murakumo-only inference invariant (ADR-2605215000)
applicable to all four tiers.

# Decision

## 4-tier ladder

| Tier | Namespace | Trunk ceiling | Weights | Target hardware | Edge invariant applies? |
|---|---|---|---|---|---|
| **edge** | `baien-edge-*` (default `baien-*`) | ≤ 4 B | ≤ 1.6 GB | WASM-32 / iPhone 12+ / Android 4 GB | **YES** (ADR-2605241900) |
| **bonsai** | `roso-*` | ≤ 2 B (1-bit packing, Bonsai density) | ≤ 0.8 GB | sub-iPhone-12 / Android 2 GB | **YES** (tighter than edge) |
| **server** | `baien-server-*` | ≤ 16 B | ≤ 32 GB bf16 | EVO-X2 / single 80 GB GPU | **NO** |
| **XL** | `baien-XL-*` | unlimited | unlimited | multi-GPU datacenter | **NO** |

## Naming rules

- `baien` (no prefix) is the canonical alias for `baien-edge`. Any
  artifact published bare under the `baien` name MUST satisfy the
  edge ceiling. There is no "small / medium / large" within `baien-*`
  that escapes the ceiling.
- `roso-{name}` for 1-bit Bonsai-density edge sub-variants
  targeting sub-iPhone-12 / Android 2 GB. The tighter ceiling is not
  formally codified in this ADR; a follow-up ADR pins exact numbers
  once a Bonsai checkpoint exists.
- `baien-server-{name}` MUST appear in the model id in the registry,
  in HuggingFace publication, in training config, and in bench logs.
  The `-server-` infix is mandatory, not decorative.
- `baien-XL-{name}` likewise — the `-XL-` infix is mandatory.

## Shared vs divergent

| Concern | Shared across all tiers | Divergent |
|---|---|---|
| Training pipeline | Move 1–7 graft pattern (frozen encoder + 1.58-bit projector + frozen trunk) | trunk size; per-modality token count for server/XL |
| Distill loop | ADR-2605231300 ReAct loop (analyze → fetch/teacher → SFT → eval → commit) | teacher selection (server/XL may use larger teachers) |
| Charter Rider scanner | Required at every commit_node | None |
| lefthook hooks | Required (no-advertising / no-purchase-purpose / charter-rider-notice) | None |
| Trunk backbone | BitNet 1.58 family | server tier may swap to a > 4 B BitNet successor when Microsoft publishes one; XL may use a full-precision teacher fork |
| Encoder budget | ADR-2605241900 §7 (600 MB cumulative) | server ≤ 4 GB cumulative; XL unlimited |
| Context window | ADR-2605241900 §5 (≤ 16 384 edge) | server ≤ 64 k; XL ≤ 128 k via ADR-2605231600 Stage 3 |

## Guarantees

- Server/XL outputs MUST NOT be distributed under the bare `baien`
  name without the `-server-` / `-XL-` infix. Mis-tagging is a release
  blocker.
- Server/XL weights MUST NOT be packaged into a `baien-edge` release
  artifact. The lefthook `baien-edge-fit-attestation` hook (Phase 2
  of ADR-2605241900 enforcement) already blocks any edge-tagged
  artifact that exceeds the ceiling.
- Server/XL remain subject to **Charter Rider §2(a)-(h)** — no
  weapons design, no surveillance capitalism, no fossil-fuel
  optimization, etc. The carve-out is from the edge size ceiling,
  not from the substantive Charter constraints.
- Server/XL inference remains subject to the **Murakumo-only invariant**
  (ADR-2605215000) — EVO-X2 LAN, LiteLLM gateway, per-node Ollama,
  and Council-approved on-prem expansions only. No RunPod, no
  Vertex direct, no Anthropic-from-vendor-key, no commercial GPU
  rental, regardless of tier.

## Non-goals

- **Frontier-beating remains an explicit non-goal even for XL.**
  Charter Rider §2(h) (Wellbecoming) plus ADR-2605241900 framing
  treat the structural gap to frontier (3 orders of magnitude in
  parameters; 2-3 orders in pretrain compute) as out of scope. XL
  exists for (a) distillation teaching of edge variants and (b)
  apples-to-apples benchmark fairness, not capability supremacy. Any
  proposal that re-frames XL as a frontier competitor requires its
  own ADR with explicit Charter alignment review.
- **No Charter Rider carve-out.** The 8 prohibited categories apply
  identically across tiers.
- **No Murakumo-only carve-out.** Bigger model ≠ permission to rent
  H100s. Server/XL train and infer on Murakumo fleet hardware only.

# Consequences

- **Move 5 (video) C/D configs** become legal — server/XL configs
  exceed the 600 MB cumulative encoder ceiling but ship under
  `baien-server-*` / `baien-XL-*` naming (see ADR-2605242110).
- **Move 6 (robotics) server tier** action head ships under
  `baien-server-*` post-Council ratification of action-policy safety
  review (see ADR-2605242120 §Safety rationale).
- **bitnet.cpp build runbook** (`90-docs/runbooks/bitnet-cpp-evo-x2-build.md`)
  can target server-tier benchmarking on EVO-X2 when wired into
  `e7m bench` — no edge invariant tripwire.
- **Distill loop** can fall back to a `baien-server-*` teacher when
  `select_teacher` path triggers, with `commit_node` recording the
  teacher tier explicitly so reviewers can sanity-check before
  flipping `available: true`.
- **frontier-bench-snapshot** can grow a "baien-server" column
  alongside the existing baien edge column for apples-to-apples
  honesty (clearly labeled as not the edge target).

# Alternatives Considered

1. **Drop the edge ceiling and unify under one `baien` name.**
   Rejected — sacrifices the entire edge promise (the founding
   reason baien exists per ADR-2605092350). The ceiling is a feature.
2. **Make all > 4 B work require Council vote.** Rejected — too high
   a bar for routine R&D; bottlenecks Council on operational decisions
   that aren't constitutional.
3. **Carve out only `baien-XL`, leave `baien-server` ambiguous.**
   Rejected — the EVO-X2 / single-80-GB-GPU tier is a real and common
   inflection point; without a name it would default to `baien-XL`
   and lose nuance.
4. **Drop the Murakumo-only invariant for server/XL.** Rejected —
   Murakumo-only is ADR-2605215000 (a different constitutional layer
   that has its own Council mechanism). Bigger models are not a
   justification for commercial GPU rental.

# References

- ADR-2605241900 — baien edge-target invariant (the constitution this
  ADR carves out from)
- ADR-2605215000 — etzhayyim inference Murakumo-only (no RunPod)
- ADR-2605192200 — etzhayyim Charter Rider v2.0 (§2(a)-(h) constraints
  that apply across all tiers)
- ADR-2605231300 — baien-distill ReAct loop (teacher fallback path)
- ADR-2605241930 — Move 4 audio graft (the Move 4-7 series this ADR
  unblocks server/XL configs for)
- ADR-2605092350 — baien design (founding edge / browser / CPU promise)
