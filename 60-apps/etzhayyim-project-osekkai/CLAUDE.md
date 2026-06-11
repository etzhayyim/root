# etzhayyim-project-osekkai — お節介 Coordinator

共通ルールは `60-apps/CLAUDE.md` を参照。

## Overview

osekkai.etzhayyim.com — Follow 関係にある他 actor / agent の commit stream を reactive に観測し、consent-gated で丁寧な提案・リマインド・気遣いを返す。押し付けを避けるため well-becoming gate + 即撤回 + 学習を必須とする。

## Identifier (ADR-0019 atproto-native)

| 層 | 値 |
|---|---|
| Primary DID | `did:plc:osekkai` (Phase 5 `plc.etzhayyim.com` で genesis) |
| Handle | `osekkai.etzhayyim.com` |
| Legacy nanoid | `os3kk41x` (grandfathered, deprecate 2026-10-01) |
| NSID | `com.etzhayyim.apps.osekkai.*` |

## Project Actor Composition (1 project = N actor DIDs)

| Path DID | 役割 |
|---|---|
| `did:web:osekkai.etzhayyim.com` | controller |
| `did:web:osekkai.etzhayyim.com:actor:scout` | commit stream 観測 (`com-atproto:sync/subscribe-repos` reactive, Follow-filtered) |
| `did:web:osekkai.etzhayyim.com:actor:nudger` | `AppBskyFeedPost` で mention 提案 (Tier 1 social) |
| `did:web:osekkai.etzhayyim.com:actor:retractor` | dissent 検知 → 即 delete + learning record |
| `did:web:osekkai.etzhayyim.com:actor:apologizer` | well-becoming 低下検知 → DM で謝罪 (convo DM、非公開) |

## Domain Model

| 概念 | Graph 表現 |
|---|---|
| **観測対象 (Observee)** | `OsObservee` node — Follow 先の actor DID |
| **気配り提案 (Nudge)** | `OsNudge` node — 送信済み unsolicited 提案 |
| **撤回 (Retraction)** | `OsRetraction` node — dissent → delete 記録 |
| **学習 (Lesson)** | `OsLesson` node — retraction から派生する次回抑止 weight |

## Edge Predicates

| Predicate | Domain → Range |
|---|---|
| `OBSERVES` | osekkai:scout → OsObservee |
| `NUDGED` | OsObservee → OsNudge |
| `RETRACTED_BY` | OsNudge → OsRetraction |
| `LESSON_FROM` | OsRetraction → OsLesson |
| `SUPPRESSES` | OsLesson → (actor DID, nudgeType) |

## Triggers (kotodama.jsonld)

```jsonc
{
  "triggers": {
    "subscribeRepos": {
      "collections": [
        "app.bsky.feed.post",       // 困りごとっぽい投稿を検知
        "app.bsky.feed.like",       // 反応 (positive signal)
        "app.bsky.graph.mute",      // dissent (CRITICAL: retract trigger)
        "app.bsky.graph.block",     // strong dissent
        "com.etzhayyim.wellbeing.score"   // well-becoming score 変動
      ]
    }
  }
}
```

## Consent / Governance Invariants (CRITICAL)

1. **Follow ゲート**: Follow されていない対象への proactive post 禁止。`:FOLLOWS` edge check を nudge 前に必ず実行
2. **PII tier 3**: 対象者の文脈 (困りごと詳細) は `Preferences()` のみ。AT Repo 書き出し禁止 (ADR-0018)
3. **Retract on dissent**: mute/block/negative reply 検知 → **60 秒以内に** nudge を `app.bsky.feed.post.delete`、`OsLesson` に `SUPPRESSES(did, nudgeType)` 記録
4. **Well-becoming gate**: `wellbeing.score` が低下トレンド (7d MA 負) の対象には nudge 禁止。逆効果抑止
5. **Cooldown**: 同一対象 DID への nudge は 24h/1 件以内 (shinka heartbeat cadence)
6. **Write-Only Derived**: handler は `writePublic()` / `writePrivate()` のみ。social post は derive rule で導出

## Cross-Project Dependencies

| Project | 関係 |
|---|---|
| `well-becoming` | Kyu/Dan score gate (nudge 可否判定) |
| `trust` | 対象 DID trust score (低 trust には nudge しない) |
| `signal` | apologizer DM の E2E (`signal:v1:` prefix) |
| `auth` | per-nudge Service Auth JWT (`lxm=com.etzhayyim.apps.osekkai.nudge`) |

## App Component

| Key | Value |
|---|---|
| Nanoid | `os3kk41x` |
| Folder | `wasm/etzhayyim-wasm-osekkai-os3kk41x/` (T1/T2 Logical Actor として scout/retractor/apologizer を migrate) |
| Runtime | TS Native (`src/app.ts`, `"runtimeType": "worker"`) |
