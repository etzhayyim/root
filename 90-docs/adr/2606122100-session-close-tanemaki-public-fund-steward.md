---
id: adr-2606122100-session-close-tanemaki-public-fund-steward
title: "ADR-2606122100: Session close — Public-Fund 投資判断/DD survey → tanemaki 種蒔き grant-steward R0 design+implementation (PR #1697)"
status: active
doc_type: adr
topic: session-close-tanemaki-public-fund-steward
authoritative: false
last_verified: 2026-06-12
priority: 5.0
axis: governance
weight: 0.50
priority_note: "Documentation-only session-close record for the 2026-06-12 tanemaki session: the founder's 投資先判断/DD actor survey answered (none exists; structurally cannot as an INVESTMENT; the outflow-judgment lane existed only as the un-actor-ized PublicFundGrantCell sketch), followed by the directed design+implementation of tanemaki 種蒔き (ADR-2606122000) — the fund-manager inversion — landed as PR #1697."
authoritative_for:
  - session-close record for the 2026-06-12 tanemaki public-fund-steward session
depends_on:
  - adr-2606122000-tanemaki-public-fund-grant-steward
related:
  - adr-2606121225-session-close-worktree-cleanup-pr-merge-ruleset-bypass
supersedes: []
superseded_by: []
---

# ADR-2606122100: Session close — Public-Fund 投資判断/DD survey → tanemaki 種蒔き R0 (PR #1697)

**Status**: active (documentation-only session-close record)
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki

# Context

Founder の問い (2026-06-12): 「etzhayyim として企業や投資先の判断、public fund としての資金の
投資先の判断を行う actor はある? DD なども含めて」。

# The session arc

1. **Survey (read-only)** — answer: **存在せず、構造的に存在できない**。
   - 投資 (equity / ROI / return waterfall) は Tier-0 priority (非営利のみ / Donation 流入のみ,
     ADR-2605192100 §1.6) から導出される禁止で、fuchi 扶持 (ADR-2606052300 G1) が inflow 側で
     その inversion パターンを確立済み (investment-instrument vocabulary unrepresentable)。
   - Public Fund の **outflow 判断** (grant 評議) は ADR-2605192145 に GrantGovernor
     (1 SBT = 1 vote + timelock) + `PublicFundGrantCell` 評価 cell sketch として設計済みだが、
     status proposed のまま actor 化されておらず、DD の実体 (criteria / screens / evidence
     supply / public scorecard) が無かった。
   - DD の素材になる observatory 群 (kanjō 勘定 / kabuto 兜 / tsumugi 紡ぎ / kosatsu 高札 /
     ooyake 公 / shiori 栞) は成熟済み — 全て non-adjudicating / public。
2. **Direction** — 「public fund の fund manager を org として設計、既存の組織への資金使途を
   public に判断、評価基準なども含めて」。
3. **Design + implementation** — **tanemaki 種蒔き** (ADR-2606122000, Tier-B actor R0,
   **PR #1697**): the charter-clean **fund-manager inversion** — hard screens S1..S6 (適格性,
   charter anchors disclosed, screens fire BEFORE weighting) → public rubric C1..C8 (weights
   Σ=1.0 enforced; evidence mapped to the observatory lineage) → route ∈ {excluded,
   insufficient-evidence, propose} → UNSENT advisory proposal → **1 SBT = 1 vote 決定**。
   G1 steward-not-sovereign (no `:fund` route; refusals raise; `advisory:true / bindsFund:false`)
   + G2 give-only instruments (equity/ROI unrepresentable, fuchi G1 reuse) + G6 synthetic seed
   (実在組織の scoring は committed seed では test-enforced で不可; real-org DD = G7-gated live
   leg, kanjō primary-disclosure pattern)。31 tests green; pre-commit 全ゲート通過 (docs
   registry + graph.jsonld regen, deps.edn `:adrs` structural append, yirah declaration)。

# Honest state at close

- **PR #1697 OPEN** (branch `worktree-tanemaki-public-fund-steward`) — Council attestation =
  PR review (founder operational premise, 2026-06-11); merge が ratification に相当。
- R0 は **offline + synthetic**: observatory live fusion / on-chain GrantGovernor 提出 /
  実在組織評価は全て G7 / Council gate の先。G9 (COI declaration) は schema + gate のみで
  signed-record flow は未実装。Contracts は Base testnet (post-Council, RFP closes 06-19) 待ち。
- Worktree は PR merge まで保持 (CLAUDE.md worktree-cleanup rule: merge 後に削除)。

# Consequences

- The roster now brackets the Public Fund with the same give-only algebra on both sides:
  fuchi 扶持 (inflow: internal maintainer sustenance) ↔ tanemaki 種蒔き (outflow: external-org
  grants), with the decision held at 1 SBT = 1 vote in both lanes.
- Follow-ups (gated): observatory evidence fusion (kanjō/kabuto/tsumugi live edges), real-org
  DD G7 flow, GrantGovernor on-chain submission lane, G9 signed COI records, and backing the
  ADR-2605192145 `PublicFundGrantCell` runtime with tanemaki's methods when the cell lands.

# References

- ADR-2606122000 (tanemaki 種蒔き — the actor; PR #1697)
- ADR-2605192145 (Public Fund architecture) · ADR-2605192130 (10% tithe)
- ADR-2606052300 (fuchi 扶持 — the inversion pattern) · ADR-2606032000 (kanjō — live-leg pattern)
