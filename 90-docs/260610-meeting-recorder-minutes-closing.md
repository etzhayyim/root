---
id: 260610-meeting-recorder-minutes-closing
title: meeting-recorder 議事録 generation — 2026-06-10 closing summary
status: active
doc_type: explanation
topic: meeting-recorder minutes generation closing
authoritative: false
last_verified: 2026-06-10
related:
  - 90-docs/adr/2606101920-meeting-recorder-minutes-generation.md
  - 90-docs/260422-meeting-recorder-session-summary.md
---

# meeting-recorder 議事録 generation — 2026-06-10 closing summary

2026-04-22 R0 セッションで「設計意図のみ・未実装」だった **minutes 議事録生成**を、
両リポジトリ (etzhayyim/root + vendor gftdcojp/ai-gftd-apps-gftdcojp) にわたって
設計 → 実装 → 検証 → 文書化まで完了したセッションのクロージング記録。設計の正本は
ADR-2606101920 (etzhayyim 側) + ADR-0089 D6 amendment (vendor 側)。

## Landed

| # | 成果物 | PR | 状態 |
|---|---|---|---|
| 1 | kotoba (kotoba-E2E) 議事録生成層 — `minutes.ts` (extractive + Murakumo 膜) + lexicon 3 本 + ADR-2606101920 | etzhayyim/root#1585 | ✅ **MERGED** (16/16 tests, tsc clean) |
| 2 | vendor container minutes-pipeline — leave 時自動生成 + `$type` guardrail 修正 + Meet adapter Phase 1.5 + `vertex_meetingrecorder_minutes` migration + lexicon 2 本 (ai.gftd) + ADR-0089 D6 | gftdcojp/ai-gftd-apps-gftdcojp#1440 | 🟡 open (mock-path E2E 検証済) |
| 3 | appview `getMinutes` XRPC (Worker 正本、read path) | etzhayyim/root#1590 | 🟡 open |

## Verification evidence

- **kotoba**: vitest 16/16 (抽出・再生成・バリデーション・G4 ゲート拒否・Murakumo 成功/失敗/非 loopback 拒否・read-cap・coverage)
- **vendor container**: mock-path E2E ×3 — murakumo 経路 / extractive 経路 / meet 経路。
  fake PDS に 6 recordingChunk + 3 transcriptSegment + 1 meetingMinutes、
  cipher 4 field (summary/decisions/actionItems/topics) を AES-256-GCM 復号して平文一致、
  3 record 種すべて `$type` あり

## Key decisions (正本は各 ADR)

- **生成場所の二重化は役割分担**: etzhayyim kotoba 側は「復号権限を持つ caller がオンデマンド生成」(G4 Murakumo-only + refused-by-default 膜、サイレントフォールバック禁止)。vendor container 側は「leave 時の自動生成」(平文が存在する唯一の場所、LLM 失敗時は抽出フォールバックを `generator` field で正直に記録)。lexicon/暗号化方針は両者で同型。
- **鍵共有**: minutes cipher は transcriptSegment.textCipher と同一 per-session 鍵 — 1 grant で transcript + minutes を覆う。

## NOT done (次セッション以降)

1. **Provider SDK sidecars** — Teams .NET 8 / Zoom C++ (SDK 再配布不可) / Meet WebRTC media bridge。tenant credentials + 実会議検証が必須
2. **Operator 手順** — vendor: PDS lexicon bundle 3-step + alembic apply。etzhayyim: appview deploy
3. AT record → vertex table projection 配線 (transcript と同状況)
4. vendor 既存不整合: transcriptSegment lexicon `confidence integer 0..1` vs pipeline float

## Session ops note

セッション中にホストのディスクが完全枯渇 (残 0MB、全ツール ENOSPC 停止)。
npm/Homebrew/pip キャッシュ削除で 3.7GB 復旧して続行した。並行エージェントが
同居するマシンではディスク残量も共有資源 — 大型 clone 前に `df` を見ること。
