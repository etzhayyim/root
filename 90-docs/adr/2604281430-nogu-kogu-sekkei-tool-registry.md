---
id: adr-2604281430-nogu-kogu-sekkei-tool-registry
title: "ADR-2604281430: nogu / kogu / sekkei — Tool, Equipment & Drawing Registry Actors"
status: active
doc_type: adr
topic: nogu-kogu-sekkei-actors
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - nogu actor (農具・農機具ライフサイクル)
  - kogu actor (工具・設備・測定器ライフサイクル)
  - sekkei actor (設計図・技術文書・BOMライフサイクル)
  - BPMN flows for nogu/kogu/sekkei
  - Kotoba/Datomic schema for vertex_nogu_* / vertex_kogu_* / vertex_sekkei_*
related:
  - adr-0056-bpmn-as-actor
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2604251830-shannon-optimal-layered-architecture
---

# ADR-2604281430 — nogu / kogu / sekkei Actor Registry

**Status**: active
**Date**: 2026-04-28
**Authors**: Jun Kawasaki + Claude Code

## Context

Physical-asset and document lifecycle management was a gap in the etzhayyim platform. Three domains needed dedicated actors:

- **農具・農機具 (nogu)** — 手工具 (鍬/鎌) から農業機械 (トラクター/コンバイン/田植機) までの個体登録・点検・整備・リース・廃棄。農機リサイクル法・ISO 11684 対応。
- **工具・設備 (kogu)** — 工場/建設/研究現場の手工具・電動工具・測定器・治工具。ISO 9001 §7.1.5 校正管理・JCSS/ISO 17025 準拠。
- **設計図・技術文書 (sekkei)** — 機械図面・電気回路図・BOM (Bill of Materials)・工程仕様書。ISO 10209・JIS Z 8316・ISO 9001 §8.3 対応。

All three require periodic monitoring (dailyPulse), event-driven workflows (checkout/inspection/review), and long-tail approval flows. The ADR-0056 BPMN-as-actor pattern removes the need for dedicated CF Workers.

## Decision

### Option B: 3 independent T1 actors with own domains

Each actor gets a dedicated `{name}.etzhayyim.com` domain, `did:web:{name}.etzhayyim.com` AT facade, and `erc725_root_pending = true` pending `provision-root-identity` (ADR-0074).

Option A (sub-actor under tsukuru) was rejected: lifecycle concerns (inspection scheduling, lease tracking) are orthogonal to manufacturing; coupling would inflate tsukuru's BPMN surface.

### BPMN-as-actor (ADR-0056) — 9 flows, 0 new CF Workers

| Actor | BPMN | Trigger | Zeebe Key |
|---|---|---|---|
| nogu | `nogu_daily_pulse` | R/P1D cron `0 30 0 * * *` | 2251799813843597 |
| nogu | `nogu_schedule_inspection` | XRPC `com.etzhayyim.apps.nogu.scheduleInspection` | 2251799813694354 |
| nogu | `nogu_record_lease` | XRPC `com.etzhayyim.apps.nogu.recordLease` | 2251799813694352 |
| kogu | `kogu_daily_pulse` | R/P1D cron `0 35 0 * * *` | 2251799813843723 |
| kogu | `kogu_schedule_calibration` | XRPC `com.etzhayyim.apps.kogu.scheduleCalibration` | 2251799813694913 |
| kogu | `kogu_checkout_tool` | XRPC `com.etzhayyim.apps.kogu.checkoutTool` | 2251799813844486 |
| sekkei | `sekkei_daily_pulse` | R/P1D cron `0 40 0 * * *` | 2251799813844372 |
| sekkei | `sekkei_review_drawing` | XRPC `com.etzhayyim.apps.sekkei.reviewDrawing` | 2251799813844587 |
| sekkei | `sekkei_approve_revision` | XRPC `com.etzhayyim.apps.sekkei.approveRevision` | 2251799813844684 |

All 9 processes deployed to Zeebe via F5 watcher at 2026-04-28T07:00–07:22Z (commit `5b821da3403`).

### Kotoba/Datomic schema — 14 tables + 1 MV

**nogu** (migration `20260428220000`):
- `vertex_nogu_item` — 農具/農機具個体 (category: hand-tool/tractor/transplanter/harvester/cultivator/sprayer/irrigation/other-machinery)
- `vertex_nogu_inspection` — 定期点検記録
- `vertex_nogu_maintenance` — 修理・整備記録
- `vertex_nogu_lease` — 農機リース記録
- `vertex_nogu_disposal` — 廃棄記録 (農機リサイクル法)

**kogu** (migration `20260428220100`):
- `vertex_kogu_item` — 工具個体 (ISO 9001 §7.1.5 `calibration_required` flag)
- `vertex_kogu_calibration` — JCSS/ISO 17025 校正記録
- `vertex_kogu_checkout` — 貸出・返却記録
- `vertex_kogu_inspection` — 工具点検記録

**sekkei** (migration `20260428220200`):
- `vertex_sekkei_drawing` — 設計図マスタ (drawingType: assembly/detail/schematic/wiring/layout/bom/spec/other)
- `vertex_sekkei_revision` — 改訂記録
- `vertex_sekkei_approval` — 承認記録
- `vertex_sekkei_bom_line` — BOM明細
- `vertex_sekkei_release` — 製造リリース記録
- `mv_sekkei_stale_reviews` — `status='pending-approval'` の revision 一覧 (sekkei dailyPulse 参照)

FLUSH added between each `CREATE INDEX` to avoid Kotoba/Datomic streaming job scheduler conflicts (lesson from prior kogu migration failure).

### Lexicon contracts — 17 JSON files

`00-contracts/lexicons/com/etzhayyim/apps/{nogu,kogu,sekkei}/*.json`:
- nogu: item, inspection, maintenance, lease, disposal, listItems
- kogu: item, calibration, checkout, inspection, listItems
- sekkei: drawing, revision, approval, bomLine, release, listDrawings

### Identity — AT Protocol facade + ERC725 root pending

```toml
# deps.toml [[mitama_actors]]
did = "did:web:{name}.etzhayyim.com"   # AT facade (federation + XRPC)
erc725_root_pending = true        # provision-root-identity not yet called
```

ERC725 root identity (ADR-0074) must be provisioned via `POST /internal/provision-root-identity` to `authz.etzhayyim.com` with `stableId: "actor:{name}"`. Tracked as `[[migrations]] id="erc725-provision-nogu-kogu-sekkei"`.

## Consequences

- **dailyPulse BPMNs** (timer-start R/P1D) activate automatically in Zeebe. First fires expected at next midnight UTC after deploy.
- **XRPC calls** to `com.etzhayyim.apps.{nogu,kogu,sekkei}.*` route via `dispatcher.etzhayyim.com:8080/xrpc/{nsid}` per ADR-0056.
- **Writes** go directly to Kotoba/Datomic via `generic.db.insert` primitives in pymagatama.
- **`write_table_allowlist`** in `vertex_bpmn_lexicon_binding` is NULL (unrestricted) for all 9 bindings — tighten per-table when domain writes are stabilized.
- **ERC725** not yet provisioned — DID doc serves `did:web:{name}.etzhayyim.com` AT facade only. Upgrade path: call `provision-root-identity` + update deps.toml `erc725_root_pending = false` + add `erc725_did`.

## Cross-actor dependencies

| Actor | Depends on | Relationship |
|---|---|---|
| nogu | maps | 圃場位置 (field geolocation) |
| nogu | nokyo | 農協組合員リース管理 |
| nogu | tsukuru | 製造元マッチング |
| kogu | sekkei | 工具仕様図参照 |
| kogu | tsukuru | 製造工程工具使用 |
| kogu | robotics | ロボット搭載工具管理 |
| sekkei | tsukuru | OEM製造指示 |
| sekkei | kogu | 工具仕様図 |
| sekkei | nogu | 農機設計図 |

## References

- ADR-0056: BPMN-as-actor pattern
- ADR-0074: ERC725 root identity
- ADR-0036: Worker-direct Hyperdrive persistence
- Commit `5b821da3403`: lexicons + BPMNs + graph migrations
- Zeebe deployment: 2026-04-28T07:00–07:22Z (bpmn-dispatcher pod `bpmn-dispatcher-7744654957-qbrcd`)
