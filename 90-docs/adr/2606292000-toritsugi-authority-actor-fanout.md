---
id: adr-2606292000-toritsugi-authority-actor-fanout
title: "ADR-2606292000: toritsugi authority-actor fanout — per-regime keyless mirror actors on apex did:web + i18n"
status: accepted
doc_type: adr
topic: toritsugi-authority-actor-fanout
authoritative: true
last_verified: 2026-06-29
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - toritsugi-authority-actor-fanout-pattern
  - per-regime-keyless-mirror-did-web
  - toritsugi-i18n-7lang
depends_on:
  - 2605312030
  - 2606272355
  - 2605231525
  - 2606013800
related:
  - 2605312400
  - 2605302130
  - 2606060900
supersedes: []
superseded_by: []
---

# ADR-2606292000: toritsugi authority-actor fanout — per-regime keyless mirror actors on apex did:web + i18n

**Status**: accepted
**Date**: 2026-06-29
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)
**Merged**: PR #2758 (root) + PR #1 (com-etzhayyim-toritsugi) — 2026-06-29

# Context

toritsugi (取次, ADR-2605312030) holds a **coded procedure registry** of 164
government procedures across 52 jurisdictions. The registry's `regime` field
encodes the **authority (所管)** — the specific ministry / municipality / agency
responsible for a procedure (e.g. `jp-jichitai` = 市区町村, `jp-national-tax` =
国税庁, `us-federal` = US federal agencies).

The parent toritsugi actor serves as a single concierge. However, the user
requirement is to **split toritsugi into per-authority actors**, each published
at `etzhayyim.com` with its own DID, lexicon, and multi-language support — so
that each authority's procedures are served by a dedicated, independently
resolvable actor.

Three infrastructure gaps were identified:

1. **did:web format分裂**: 3系統が混在 — GitHub Pages 静的
   (`did:web:etzhayyim.github.io:com-etzhayyim-<name>`), apex Worker 動的
   (`did:web:etzhayyim.com:actor:<h>`), actor-manifest 独自形式. CLAUDE.md は
   apex 形式を指示するが未実装だった。
2. **i18n 機構が実体ゼロ**: `com-etzhayyim-i18n` は Murakumo qwen3.5-4b 翻訳
   サービス設計のみで、`messages/<lang>.json` / locales / 共通 utility は1つもない。
3. **procedure kind が lexicon first-class ではない**: `COVERAGE.md` の kind 分類
   (passport/business/tax 等) は `procedureId` プレフィックスから推論される
   dashboard label であり、lexicon schema 上のフィールドではない。

# Decision

## 1. Authority (regime) 単位で actor を分割

toritsugi の `regime` フィールド（148 unique values）を authority 区分として、
**regime ごとに1つの keyless mirror actor** を生成する:

- actor name: `toritsugi-<regime>` (e.g. `toritsugi-jp-jichitai`, `toritsugi-us-federal`)
- DID: `did:web:etzhayyim.com:actor:toritsugi-<regime>` (apex path did)
- parent: `toritsugi` (ADR-2605312030)
- pattern: keyless R0 mirror (verificationMethod: [], same as tate case-actors
  ADR-2606122300 + gov-mirror constellation ADR-2606272355)

148 authority actors cover all 164 procedures in the seed registry. Each actor
holds only the procedures belonging to its regime, preserving the
jurisdiction-generic architecture while enabling per-authority resolution.

**Why regime (authority) and not procedure-kind**: authority が違えば法体系・管轄・
言語・窓口が完全に異なるため、actor を分ける意義が明確。同一 authority 内の
手続き（例: jp-jichitai 内の住民票/転入届/出生届/児童手当）は1 actor に集約。

## 2. apex did:web 形式を SSoT に統一

`did:web:etzhayyim.com:actor:<h>` を canonical 形式とする:

- apex Worker (`50-infra/etzhayyim-did-web`, ADR-2606013800) が各 actor の
  `did.json` / `profile.json` を動的発行（既に `public/actor/<h>/` で実装済み）
- 各 `com-etzhayyim-*` repo の `.well-known/did.json` を **alias** に格下げ
  (`alsoKnownAs` で apex を指す)
- RAD identity 台帳 (`80-data/kotoba-rad/<name>.identity.journal.edn`) の
  `:rad/did-web` を全件 apex 形式に更新（append-only journal なので追記エントリ）

## 3. i18n: 国連公用6言語 + ja (7言語) を R1 で対応

各 authority actor に `messages/<lang>.json` を生成:

- **ja** (SSoT) + **ar / zh / en / fr / ru / es** (国連公用6言語)
- ICU MessageFormat 準拠の key-value JSON
- `com-etzhayyim-i18n` の Murakumo qwen3.5-4b batch 翻訳パイプラインが
  ja SSoT → 6言語に自動翻訳（人手校閲 gate, G8 非捏造）
- 3層 i18n: README 層 (README.\<lang\>.md) + Lexicon/出力文書層 (messages/) +
  公開サイト層 (Accept-Language routing)

## 4. Lexicon を authority ごとに定義

各 authority actor に `com.etzhayyim.toritsugi.<regime>.procedure` lexicon を生成:
親 `com.etzhayyim.toritsugi.procedure` と同 schema だが `regime` を
first-class knownValue として固定。`00-contracts/lexicons/com/etzhayyim/toritsugi/<regime>/procedure.json`
に配置。

## 5. Generator script

`orgs/etzhayyim/com-etzhayyim-toritsugi/scripts/gen_authority_actors.clj` (bb):
`procedures.seed.json` を読み → regime で group by → 148 actor の
`did.json` / `profile.json` / RAD journal / `messages/<lang>.json` × 7言語
を生成。`--dry-run` / `--regime <list>` / `--check` オプション対応。

# Consequences

- **148 新規 keyless mirror actor** が apex Worker 配下に生成される
  (`public/actor/toritsugi-<regime>/`)
- **148 RAD identity journal** が `80-data/kotoba-rad/` に追加される
- **148 × 7 = 1,036 i18n message files** が生成される
- **148 lexicon** が `00-contracts/lexicons/com/etzhayyim/toritsugi/<regime>/`
  に生成される
- 既存 164 actor の did:web を GitHub Pages 形式から apex 形式に統一
  (RAD 台帳 + .well-known/did.json の更新)
- toritsugi parent actor は registry 全体を保持したまま、各 authority actor が
  その regime の procedures への解決点となる
- G5 (行政書士法/UPL) / G8 (非捏造) / G14 (verified-procedure-only) / G15
  (self-submit default) は全て不変 — authority actor も同じ constitutional gates に縛られる

# Alternatives Considered

## A. procedure kind (10種) で分割

passport / business / national-id / driving / marriage / civic / social-security /
tax / other / civil-vital の 10 actor に分割する案。**不採用**: kind は
`procedureId` プレフィックスから推論される後方互換ラベルであり、lexicon 上の
first-class フィールドではない。また同一 kind でも authority が違えば法体系・
言語・窓口が完全に異なるため、authority 区分の方が分割の意義が明確。

## B. jurisdiction (52法域) で分割

国毎に1 actor を作る案。**不採用**: 同一国内でも authority が違えば
(例: JP で jichitai/national/national-tax/business-registry/civil-registry/
driving-licence の6系統) 手続き体系が完全に異なるため、authority の方が
正しい粒度。

## C. toritsugi を1つのまま、kind を lexicon first-class 化

actor を増やさず `procedure.kind` フィールドを新設する案。**不採用**: ユーザー
要件が「それぞれの手続きごとに actor として etzhayyim.com で公開」であるため、
actor を分ける必要がある。

# References

- ADR-2605312030 (toritsugi — citizen government-procedure concierge)
- ADR-2606272355 (actor self-publication seed on kotoba mesh)
- ADR-2605231525 (no-server-key)
- ADR-2606013800 (actor profile + dynamic did.json)
- ADR-2606122300 (tate case-actors — keyless mirror pattern)
- `orgs/etzhayyim/com-etzhayyim-toritsugi/scripts/gen_authority_actors.clj`
- `orgs/etzhayyim/com-etzhayyim-toritsugi/registry/procedures.seed.json`
- `orgs/etzhayyim/com-etzhayyim-toritsugi/COVERAGE.md`
