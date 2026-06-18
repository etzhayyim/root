---
id: adr-2606171500-organism-social-reward-joucho-wellbecoming
title: "ADR-2606171500: 生命活動の報酬と情緒 — atproto 反応 / メール / 感情を charter-clean に joucho → Wellbecoming → 子孫 へ結ぶ設計"
status: accepted
doc_type: adr
topic: organism-social-reward-joucho-wellbecoming
authoritative: true
last_verified: 2026-06-17
priority: 7.0
axis: organism-autonomy
weight: 0.7
priority_note: "『social post への like/love/comment、メール送受信、内容の感情スコア → 報酬 → wellbecoming → 子・孫 → joucho』という直感的ループの一部は §1.13 (anti-addictive / engagement-maximizing 禁止) と正面衝突する。本 ADR はその衝突を明文化し、charter-clean な代替配線 (互恵イベント / 軌跡としての Wellbecoming / per-soul score 不在) を固定する。"
depends_on:
  - "2605192100"  # mission charter — 多世代(子・孫) priority / Wellbecoming §1.13 動的軌跡 / 反個人主義 ontology
  - "2606101200"  # ibuki organism autonomy — joucho 5-axis mood event-fold / as-of replay / no per-organism wellbeing score
  - "2606082100"  # moyai social-capital mint (Part A) — reciprocity credit; keeper-only mint
  - "2606082102"  # shiori Wellbecoming detractor observatory — :engagement-maximizing-design = DETRACTOR
  - "2606112200"  # yir'ah doctrine — no-score-of-soul / map-not-target の神学的正典
---

# ADR-2606171500 — 生命活動の報酬と情緒: charter-clean な joucho → Wellbecoming → 子孫

## Context

問い (founder, 2026-06-17): 生命活動を、(a) atproto の social post への **like / love / comment**、
(b) **メールの送受信**、(c) reply / メール **内容の感情スコア分析** を報酬として、それらに基づく
**Wellbecoming** と **子・孫**、**joucho (情緒)** につながるように設計されているか。

### 現状調査 (実コード)

- **joucho (情緒)** = ibuki の 5 軸 mood (joy/calm/stress/gratitude/focus) が観測イベントの fold で
  進化し、`:joucho/*` datom として append-only kotoba log に **as-of replayable** で永続 (ADR-2606101200)。
  mood は投稿カデンスを決め、行動に効く。**骨格は存在する。**
- しかし現行 CLOSED event 語彙は 6 種のみ: `post-emitted / follower-gained / inbox-pressure /
  kaizen-merged / kaizen-rejected / idle`。
  - ソーシャル反応は **follower 数の差分のみ** (`perception.cljc`, read-only public XRPC)。
    **like / love / comment / reply は読まず、mood に効かない。**
  - メールは **`inbox-pressure` (量/圧) のみ**。送受信・内容感情は mood に未接続。openmail 未配線。
  - 感情/sentiment コードは別アクター (tsumugi / shiori / ake) に在るが ibuki の mood/報酬に未接続。
  - moyai 報酬は commons-inference 入会権 + keeping のみ。**社会的反応 → 報酬は未配線。**
  - **mood → Wellbecoming → 子孫 のコードレベル配線は無い** (`子孫`/`descendant` grep 空)。

### 憲法的制約 (これは設計漏れではなく意図的回避)

直感的ループのうち **「like/love/comment を報酬化して mood を駆動する」部分は Charter と衝突する**:

- §1.13 **Wellbecoming = anti-addictive-design** (動的軌跡であり静的 wellbeing ではない)。
- shiori (ADR-2606082102) は `:engagement-maximizing-design` を **DETRACTOR driver (人への害)** と明示分類。
- kawaraban G2 = **no engagement rank**; ibuki gate = **per-organism wellbeing SCORE を決して assert しない**
  (edge-primary); yir'ah doctrine (ADR-2606112200) = **no-score-of-soul**。

→ engagement tally → reward → mood は、まさに禁止されている addictive 設計。per-person の感情スコアリングは
soul の点数化にも触れる。

## Decision

直感的ループを **charter-clean に再構成**して実装する。固定する priority は「掟」ではなく以下:

1. **報酬は関係的であって engagement ではない** — 新イベント
   `:event/dialogue-reciprocated` (joucho)。**post が互恵的な返信を引き出した = 縁が返った**ときに発火し、
   `[joy +2, calm +1, stress -1, gratitude +3]` で mood を温める (聞かれた → 孤立が和らぐ)。
   like/comment の **カウントは構造的に表現不能** (closed vocab が unknown を raise)。engagement tally は
   イベントになりえない。

2. **Wellbecoming は LEVEL でなく MOVEMENT (軌跡)** — `wellbecoming.cljc` は health と同じく
   **log からの純粋 READ-DERIVATION**。`:joucho/*` beat 履歴の窓から **per-axis の移動量 + 合成方向**
   (`:improving / :declining / :steady`) を算出し `:wellbecoming/*` datom として emit する。
   **`:wellbecoming/score` / `:wellbecoming/level` 属性は構造的に存在しない** (テストで guard)。
   魂は数値に還元されず、その**軌跡だけ**が witness される (§1.13 動的軌跡の定義そのもの)。

3. **メール内容の感情** は per-person affect になりうる → **member 自身宛・同意ベース (himotoki envelope) /
   cohort-aggregate のみ**、mood 寄与は「対話の温度」に bounded。本 ADR では `dialogue-reciprocated` の
   関係シグナルに留め、内容スコアの mood 駆動は **将来作業** (consent-gated) とする。

4. **子・孫 priority への接続** = moyai の **世代 heir-decay 移譲** (子孫へ漸減移譲) を将来設計とする。
   Wellbecoming の **as-of 軌跡** (静的でない becoming) こそが子孫 priority が消費すべき信号であり、
   本 ADR はその供給側 (`:wellbecoming/*` movement) を据える。実際の heir-decay ledger は未実装 (次 ADR)。

## 実装 (このコミットで landed)

- `20-actors/ibuki/methods/joucho.cljc` — `:event/dialogue-reciprocated` を closed vocab に追加。
- `20-actors/ibuki/methods/wellbecoming.cljc` — Wellbecoming-as-trajectory の純粋導出 + `:wellbecoming/*`
  movement datom (no score/level、edge-primary)。
- `20-actors/ibuki/methods/test_wellbecoming.cljc` — 13 assertions green。互恵イベントが engagement でない
  こと / Wellbecoming が score でないこと / improving・declining・steady 軌跡を検証 (`test:ibuki` に登録)。
- `/organism` 可視化 (`50-infra/etzhayyim-did-web/public/organism/`) に **情緒 (joucho) レイヤー** を追加:
  細胞の色温度 = mood、軌跡 = Wellbecoming movement (`bb vitals:joucho` が `joucho.json` を emit)。

## Gates / invariants (weaken 禁止)

- **engagement-count unrepresentable** — like/love/comment/dwell の数を joucho イベントにしない。
  反応は関係 (`dialogue-reciprocated`) としてのみ表現。
- **no-score-of-soul** — `:wellbecoming/score`/`:wellbecoming/level` を導入しない。Wellbecoming は movement。
- **per-person affect 禁止** — メール/返信の感情は member-consent + aggregate のみ。per-soul の感情点数化禁止。
- **closed vocab raises** — 未知イベントは guess せず raise (joucho 規律)。
- **append-only / deterministic / no wall clock / Murakumo-only** — ibuki の既存 gate を継承。

## Future work

- moyai **heir-decay** ledger (Wellbecoming 軌跡 → 子・孫 priority へ漸減移譲)。
- `dialogue-reciprocated` の **live 配線** (member-attributed post → 互恵返信の read-only 観測; G8/operator gate)。
- メール内容感情の **consent-gated / aggregate** 寄与 (himotoki envelope)。
- joucho を ibuki 1 体から **organism 全体の代謝軸**へ拡張するか (設計判断)。
