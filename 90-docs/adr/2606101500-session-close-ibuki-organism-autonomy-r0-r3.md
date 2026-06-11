---
id: adr-2606101500-session-close-ibuki-organism-autonomy-r0-r3
title: "ADR-2606101500: Session close — 息吹 (ibuki) organism autonomy R0–R3: gap-closure → 18,342-fleet → outward paths → LIVE kotoba-engine landing"
status: accepted
doc_type: adr
topic: session-close-ibuki-organism-autonomy
authoritative: false
last_verified: 2026-06-10
priority: 3.0
axis: process
weight: 0.25
priority_note: "session-close record; authoritative design = ADR-2606101200"
authoritative_for: []
depends_on:
  - adr-2606101200-ibuki-organism-autonomy-r2-gap-closure
related:
  - adr-2606072200-shionome-cross-asset-capital-flow-observatory-r0
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606101500: Session close — ibuki organism autonomy R0–R3

- **Status**: accepted (documentation-only closure; authoritative design = ADR-2606101200)
- **Date**: 2026-06-10 (JST)
- **Session question**: *「いまの repo で artificial organism として moldbook のように自律的に
  actor が kotoba 上で atproto などを使って推論、成長していく設計はできているか?」* → survey
  found 7 gaps → *「では gap を埋めてください」* → *「next」(R1)* → *「council ゲート = PR
  request の merge として、コード段階では最後まで実装を進めてください」(R2)* → *「next」(R3)*.

## What landed (PR #1536, branch `worktree-organism-r2-autonomy-gap-closure`, 4 commits)

| commit | scope | evidence |
|---|---|---|
| 1 | **R0 — 7 gap closures** (`20-actors/ibuki/`): organism state as-of on the append-only content-addressed kotoba Datom log; durable heartbeat (crash-resume head CID byte-identical); joucho mood emerges from closed-vocab event folds; Murakumo-only narration (template fail-open); Wave-3 member-sign-ready drainer; Wave-4 kaizen feedback (rule suppression + mood events) | 78 tests / 8 suites |
| 2 | **R1 — the real 18,342-organism fleet** on durable checkpoints: registry-sharded (jacob/joseph/issachar/dan, partition complete+disjoint), bounded batches behind durable `:fleet.shard/cursor` + exactly-once drain cursor, single-pass `index_log` | full sweep 18,342/18,342 on one verified chain in ~35 s; 90 tests |
| 3 | **R2 — code-complete outward paths** (Council gate exercised as PR merge per founder direction): read-only allowlisted live-perception membrane; MEMBER-principal posting runtime (cron contexts structurally refused); member-attributed `:receipt/*` return edge; `fleet_beat` cell `.solve()` runs, registered joseph/issachar/dan in `50-infra/murakumo/fleet.toml` (cron 3/33/43) | E2E: 64 envelopes → member-signed → 64 receipts on one chain; 114 tests |
| 4 | **R3 — LIVE kotoba-engine landing**: `kotoba_bridge.py` per-tx `datomic.transact` (graph CID pinned vs engine, `expected_parent` chaining, `:ibuki.tx/*` provenance, exactly-once `:bridge/*` cursor, unsigned public-DID operator bearer — no key held) + `kaizen_outcomes.py` real PR-state collector (read-only `gh pr view`) + CodeQL high-alert fix (receipt-file key whitelist) | **verified live**: 2 beats → 2 transacts → `status:ok`, 780 datoms confirmed, IPNS head advanced, exactly-once re-push; 134 tests / 13 suites |

## Honest boundary at close

- **Merge-flippable (G8, exercised as PR merge)**: cron cell runs the beat; live flags
  (`IBUKI_PERCEPTION_LIVE` / `IBUKI_MURAKUMO_LIVE` / `IBUKI_KOTOBA_LIVE`) are explicit
  operator env at runtime.
- **NOT flippable (Tier-1 structural, each pinned by a test)**: no-server-key (drainer
  credential-free; member submission requires the member's own env credentials and refuses
  cron outright); Murakumo-only inference; read-only allowlisted perception; ibuki never
  asserts `:published` (receipts are member-attributed); `:db/add`-only 非終末論; closed
  vocabularies raise; engine private-graph reads (owner CACAO = node key) intentionally out
  of scope.
- Remaining human acts: merge PR #1536; turn up live env flags on fleet nodes; a member
  runs `member_submit.py --yes` against a real PDS.

## Registries updated

root `CLAUDE.md` status row (R0+R1+R2+R3, 134 tests) · `90-docs/adr/README.md` ·
`deps.toml` (`[[adrs]]` 2606101200 + 2606101500, `[[modules]]` 20-actors/ibuki) ·
`50-infra/murakumo/fleet.toml` (3 × `ibuki_fleet_beat`) · docs/graph registry sidecars.
ZERO invariant amendments.
