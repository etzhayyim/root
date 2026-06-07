---
id: adr-0075-yoro-engagement-wellbecoming
title: "ADR-0030: YORO Engagement Algorithm — Shannon / Bayes / Graph / Topology / Joucho-emotion with well-becoming guardrails"
status: active
doc_type: adr
topic: ranking-wellbecoming
authoritative: true
last_verified: 2026-04-17
authoritative_for:
  - yoro AppView feed ranking の 5 理論レイヤー割当
  - PII Tier 3 / cohort k>=50 / signal-encrypted ζ hard-gate を hot path で enforce する不変条件
  - doom-scroll / night-mode / datacenter-ASN guardrail の閾値と効果
  - IP-intent prior の非永続化ルール
  - client-side session topology が送出できる scalar の allow-list
related:
  - adr-0018-pii-tier3-cohort-first
  - adr-0019-atproto-native-identifier-topology
  - adr-0026-agent-only-reverse-identity-topology
  - adr-0028-cohort-mv-sharding
supersedes: []
superseded_by: []
---

# Context

YORO (yoro.etzhayyim.com) は AT Protocol superset + AI Agent-First の social platform。これまでの feed は `created_at DESC + diversityInterleave` のみで、TikTok / Instagram / X のような「見る人の興味を惹く」関心駆動ランキングが無かった。一方で platform 全体には関連理論 / データが既に揃っている:

- Shannon 4-layer (etzhayyim CLI / mokuteki)
- Bayesian posterior streaming (ADR-0026 cohort identity)
- Kotoba/Datomic graph (edge_follows / edge_likes / edge_reposts / `mv_actor_*` MV 12 本)
- Joucho 5 軸 (`vertex_joucho` joy/calm/stress/gratitude/focus)
- Society6 Well-Becoming Kyu/Dan
- Signal E2E (`signal:v1:` 前置)
- Murakumo / Ameno LLM infer

これらを **well-becoming を負帰還として組み込む**形で統合し、短期エンゲージメントの高さと長期の情緒健康を両立させる feed ranking を設計する。個人 PII は ADR-0018 の Tier 3 + cohort-first を絶対条件とする。

# Decision

## 1. 5 直交レイヤー構成

候補集合に対し以下の線形結合を softmax してランク:

```
final(post, viewer) =
      α · Bayes_interest(post | viewer)          # 関心 (latent posterior)
    + β · PageRank_personalized(post, viewer)    # 社会伝播 (follow two-hop)
    + γ · Shannon_novelty(post | history)        # 多様性 (H 最大化、rerank で加算)
    − δ · TDA_echo_penalty(viewer_session)       # echo-chamber 減点
    + ε · Joucho_align(post, viewer_state)       # 情緒整合 (well-becoming 負帰還)
    − ζ · PII_leak_risk(post, viewer)            # consent / tier hard gate
```

| Layer | 理論 | 実装場所 | 主データ源 |
|---|---|---|---|
| L1 Shannon | 情報理論 | `src/appview/rank.ts#shannonRerank` | 候補集合 topic/author/emotion 分布 |
| L2 Bayes | 関心 posterior | 同上 `scoreCandidate#bayesInterest` | `mv_actor_subject_engagement`, IP intent prior で shrink |
| L3 Graph | personalized PPR | 同上 `scoreCandidate#pageRank` | `edge_follows` 2 段 (limit 500 / 5000) |
| L4 Topology | session echo | `svelte/src/lib/session-topology.svelte.ts` (client) → body scalars | `sessionStorage` ring buffer (50 slot) |
| L5 Joucho | 情緒整合 | `src/appview/rank.ts#jouchoAlignScore` + `topic-extract.ts#jouchoRowToState` | `vertex_joucho` 最新行 |

ハイパラ α..ζ は `DEFAULT_WEIGHTS = {alpha:1.0, beta:0.6, gamma:0.4, delta:0.8, epsilon:0.5, zeta:1.0}` を初期値とし、将来 mokuteki 5 軸 objective (engagement/competence/contribution/growth/resilience) の夜間勾配で更新する (P5 予定、本 ADR では初期値を確定)。

## 2. PII / Consent hard-gate (CRITICAL, 不変条件)

hot path で以下を強制する。bypass 禁止:

1. **signal-encrypted post** で `candidate.audienceDid !== viewer.did` の場合 `piiLeakRisk = 1.0`、`applyHardGate` で softmax 前に除外。softening 禁止。
2. **cohort k<50** (viewer の follower count を proxy として使用) の場合 `personalizeOff = true`。PPR=0、Bayes は uniform prior に 0.3 倍で shrink。
3. **consent.individualScope = false** の viewer には cohort hash 集計のみ露出。個体 posterior 参照禁止。
4. **IP 原値 (`CF-Connecting-IP` / `request.cf.ip`) は Worker 外に持ち出さない**。ログにも `cf.country` / `cf.timezone` / `asnType` 粒度のみ。`coarseRegion` は将来 `mv_intent_cohort_size` で k>=50 を確認してから露出する (現状 null)。
5. **client-side session topology は scalar 3 個のみ送出**: `echoPersistence` (0..1)、`sessionDwellMs` (integer)、`sessionDistinctTopics` (integer)。生トピック履歴は `sessionStorage` に閉じる。

## 3. Well-becoming 負帰還 (doom-scroll / night / datacenter)

`deriveGuardrails()` が以下フラグを算出し、`scoreCandidate` がこれを用いて重みを動的調整する:

| Flag | 条件 | 効果 |
|---|---|---|
| `personalizeOff` | `cohortSize < 50` | β = 0、α × 0.3 |
| `nightMode` | `intent.localHour ∈ [23, 5)` | ε × 1.5 (serenity boost) |
| `botSuspect` | `intent.asnType === "datacenter"` | α/β に botPenalty 0.5 倍 |
| `doomScroll` | `sessionDwellMs > 45min` (night: 20min) ∧ (`stressIdx > 70` ∨ night) | δ × 2、ε × 2 |

## 4. Topic extraction precedence

`topic-extract.ts#extractTopic` が以下優先順で bucket key を決定する (shannonRerank の多様性軸):

1. Facet-declared hashtag (`app.bsky.richtext.facet#tag`) → `tag:{lowercase}`
2. Inline `#tag` fallback → 同上
3. Embed kind (images/video/record/external) → `embed:{kind}`
4. Link facet domain (JP `co.jp` 2-segment TLD 対応) → `url:{registrable-domain}`
5. null (shannonRerank では `_` バケット)

## 5. 新規 NSID / Lexicon

- `com.etzhayyim.yoro.feed.getRankedFeed` (query, optional: `echoPersistence` / `sessionDwellMs` / `sessionDistinctTopics` / `debug`)

既存 `app.bsky.feed.getTimeline` / `com.etzhayyim.yoro.feed.getDiscoverFeed` は互換維持。`getRankedFeed` は opt-in path で、MV / 候補取得失敗時は `getDiscoverFeed` に自動降格する (既存フォールバック契約維持)。

## 6. Nintendo-style UX コンポーネント

- `$lib/wellbecoming/StressPauseModal.svelte` — 10 分カウントダウン、`playWindBell` on open / `playChimeC5` on resume、resume 時 `resetSessionTopology()`。
- `$lib/wellbecoming/ReactionWheel.svelte` — 長押し 8 emoji 放射配置、5 リアクションが Joucho 5 軸にタグ付け。viewport clamp 済。

両コンポーネントは `prefers-reduced-motion` / `prefers-reduced-sound` を尊重する `sound.ts` helpers を利用する。

# Consequences

## Positive

- ranking が 5 直交軸で解釈可能になり、debug 出力 (`eta` / `personalizeOff` / `nightMode` / `doomScroll` / `cohortSize` / `twoHopAuthors` / `bayesShrink` / `topicsDistinct` / `viewerJouchoLoaded` / `sessionEchoPersistence` / `sessionDwellMs`) で per-request にゲートと数値を点検できる。
- hard-gate が hot path にあるため、ポリシー違反時に softmax が "ほぼゼロ" で柔らかく通過する余地がない。
- session topology を client side に閉じたことで、生トピック履歴 / 生 IP が server / log / federation 経路に流出しない。
- doom-scroll が検出されると δ と ε が倍掛けされ、echo 負方向 + serenity 正方向で自動的に feed が "休む方向" に引かれる。
- 既存 MV (`mv_actor_social_stats` / `mv_actor_subject_engagement`) と既存テーブル (`edge_follows` / `vertex_joucho`) のみで駆動、新規 MV 追加は P5 まで先送り可能。

## Negative / Trade-offs

- cohort-size proxy として follower count を使っているため、フォロー 0 の新規 viewer は常に `personalizeOff`。ADR-0028 の `mv_intent_cohort_size` が入るまで回復手段は cohort segment への自動参加のみ。
- Joucho state が `vertex_joucho` に存在しない viewer は `jouchoAlign = 0`。情緒整合が効くのは joucho scoring を少なくとも 1 回した user のみ。
- TDA echo penalty は現状 client の簡易計算 (`1 - distinct/total`)。本格的な persistent homology (giotto-tda wasm on Ameno WebGPU) は P5 で置換予定。
- `DEFAULT_WEIGHTS` は経験則で置いた。mokuteki 5 軸 objective による勾配学習 (P5) まで手動チューニング。

## Invariants (不変条件)

以下は後方互換を含め破ってはならない:

1. `piiLeakRisk >= 0.5` は softmax 前に必ず除外 (soften 禁止)。
2. `cohortSize < 50` では PPR=0。IP prior / follow graph 由来の個人特定経路を無効化。
3. client-side session topology の送出 scalar は 3 個 (`echoPersistence` / `sessionDwellMs` / `sessionDistinctTopics`) のみ。raw topic history の漏出禁止。
4. `getRankedFeed` は候補取得失敗で `getDiscoverFeed` に degrade する既存契約を維持する。
5. lexicon parameters の `min` / `max` 境界は lexicon 側で bound される (worker は更に `clampNum` で保険)。

# Alternatives Considered

## A. 単一 LLM scorer (server-side Murakumo 1 pass)

- **却下**: hot path が LLM call になると 100ms 超、PII Tier 3 の plaintext を server が見てしまう、explainability 喪失。

## B. Browser-only ranking (PPR / Bayes も client で)

- **却下**: full follow graph を client に送るコストと privacy 悪化。ADR-0018 の cohort-hash 露出契約に反する。

## C. 既存 `diversityInterleave` を維持、単に重み付け

- **却下**: topic/author/emotion 3 次元に対する entropy 最大化が表現できない。echo-chamber 検出不能。

## D. Per-post emotion MV を先行

- **保留**: Murakumo batch infer のインフラ負荷が大きく、cold start 時に feed 全体が止まるリスク。P5 で incremental に投入する。

# References

- `/root/.claude/plans/yoro-etzhayyim-ai-facebook-zazzy-teapot.md` (design plan, user-approved 2026-04-17)
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/appview/rank.ts`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/appview/feed.ts#handleGetRankedFeed`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/appview/topic-extract.ts`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/appview/intent-prior.ts`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/session-topology.svelte.ts`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/wellbecoming/StressPauseModal.svelte`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/wellbecoming/ReactionWheel.svelte`
- `00-contracts/lexicons/com/etzhayyim/yoro/feed/getRankedFeed.json`
- Related: ADR-0018 (PII Tier 3 + cohort-first), ADR-0019 (identifier topology), ADR-0026 (agent-only reverse identity), ADR-0028 (cohort MV sharding)
