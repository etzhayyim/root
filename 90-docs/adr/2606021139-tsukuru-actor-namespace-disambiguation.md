---
id: adr-2606021139-tsukuru-actor-namespace-disambiguation
title: "ADR-2606021139: tsukuru actor namespace disambiguation — B2B factory-ordering vs silicon-fab orchestration"
status: proposed
doc_type: adr
topic: tsukuru-namespace-disambiguation
authoritative: true
last_verified: 2026-06-02
priority: 6.0
axis: organization
weight: 0.60
priority_note: "Resolves a name collision where one actor identity (tsukuru.etzhayyim.com) carries two unrelated domains; blocks clean Gen-3 migration of either."
authoritative_for:
  - tsukuru.etzhayyim.com actor identity scope
  - silicon-fab orchestration namespace placement
depends_on:
  - adr-2605202800-tsukuru-etzhayyim-business-model-change
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605242545-tsukuru-fab-equipment-pregel-charter
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - 20-actors/tsukuru/
  - 20-actors/silicon/
  - 90-docs/260602-actor-stack-generation-inventory.md
  - 90-docs/260602-tsukuru-kotoba-native-migration-plan.md
supersedes: []
superseded_by: []
---

# ADR-2606021139: tsukuru actor namespace disambiguation

**Status**: proposed
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki (Council Bootstrap Seat 1) — naming-only change, no constitutional impact

# Context

`tsukuru` という識別子が、互いに無関係な **2 つのドメイン**を同時に背負っており、
root `CLAUDE.md` 上でも別物として参照されている。

| 何の tsukuru | 実体 | スタック | ADR | root CLAUDE.md |
|---|---|---|---|---|
| **(A) B2B factory-direct ordering** | `20-actors/tsukuru/`（460+ factory DID, BTO/OEM, CNT process） | 旧 etzhayyim / RisingWave / JSON-LD | 0061, 2605202800, 2605202900 | 未掲載 |
| **(B) silicon-fab orchestration** | `20-actors/silicon/cells/`（litho/etch/CMP… 8 工程）+ baien ternary ASIC | Pregel cells | 2605242500, 2605242545 | line 77 "tsukuru (fab)" ✅ |

衝突の経緯: ADR-2605242500 が **「tsukuru.etzhayyim.com を一気通貫 orchestration の
SSoT に確定」** と宣言し、既存の B2B 発注 actor (A) と同じドメイン・同じ actor 名に
半導体 fab 装置 orchestration (B) を載せた。結果:

1. root CLAUDE.md line 77 の "tsukuru (fab)" ✅ は (B) を指すが、`20-actors/tsukuru/`
   の実体は (A)。読者は (A) を ✅ shipped と誤読しうる（実際は legacy R0）。
2. silicon cells は `20-actors/tsukuru/` ではなく **別ツリー `20-actors/silicon/cells/`**
   に置かれており、actor 名とディレクトリが一致しない。
3. 片方を Gen-3（kotoba-native）化しようとすると、もう片方の意味論が同じ manifest に
   混入し、clean migration ができない（→ 移行プランの前提障害）。

# Decision

**actor 名 `tsukuru` は (A) B2B factory-direct ordering 専用に確定する。** (B) silicon-fab
orchestration は別 actor 名 **`fuigo`/`silicon` レーン**として分離し、tsukuru ドメインから降ろす。

1. **(A) tsukuru = manufacturing orderbook actor**:
   - 識別子 `tsukuru` / `did:web:tsukuru.etzhayyim.com` / nanoid `tsukr8u0` は (A) が保持。
   - Gen-3 移行対象（→ `260602-tsukuru-kotoba-native-migration-plan.md`）。
2. **(B) silicon-fab orchestration を `silicon` actor に正式昇格**:
   - 既存 `20-actors/silicon/cells/`（litho/wafer/packaging/chiptest…）を canonical な home とする。
   - DID は `did:web:silicon.etzhayyim.com`（新規）。tsukuru ドメイン上の fab lane 参照は撤回。
   - root CLAUDE.md line 77 を `iwakura + fuigo + **silicon** (fab)` に訂正（"tsukuru (fab)" → "silicon (fab)"）。
3. **ADR-2605242500 / 2605242545 の "tsukuru.etzhayyim.com を fab SSoT" 条項を本 ADR で
   superseded** とし、両 ADR にポインタ注記を追加（id 再利用はしない）。
4. tsukuru が fab 装置を **発注対象**として扱うのは引き続き可（ISIC C26 lane）。それは
   orderbook (A) の 1 カテゴリであり、fab orchestration (B) の所有とは別レイヤ。

# Consequences

- **正**: actor 名とディレクトリ・DID・root CLAUDE.md 表記が 1:1 に揃う。tsukuru の Gen-3
  移行が silicon 意味論に汚染されずに進む。"tsukuru (fab) ✅" の誤読が解消。
- **正**: silicon が独立 actor として Tier-B roster に正式登録でき、baien ASIC 所有
  （inalienability 原則）と素直に結びつく。
- **負/コスト**: ADR-2605242500/545 の本文・`related` 参照・既存 silicon cell の DID 参照を
  `tsukuru.*` → `silicon.*` に書き換える小規模 sweep が必要。
- **非影響**: 憲法・Charter Rider・支払い境界には触れない（命名のみ）。Council 多数決不要。

# Alternatives Considered

1. **現状維持（1 actor が両方を持つ）**: ✗ 誤読と移行汚染が恒久化。
2. **(A) を改名し tsukuru を fab 専用にする**: ✗ tsukuru = 作る = manufacturing/ordering の
   語義に (A) の方が合致。460+ factory DID と nanoid 資産も (A) 側。改名コストが大きい。
3. **silicon を tsukuru のサブ actor (path-based) として残す**: ✗ cells が既に別ツリーにあり、
   ASIC 所有・inalienability の文脈で独立 actor の方が自然。

# References

- ADR-2605202800 (tsukuru full move to etzhayyim — business model change)
- ADR-2605242500 (baien ternary silicon + tsukuru fab charter) — fab-SSoT 条項 superseded by this ADR
- ADR-2605242545 (tsukuru fab equipment Pregel charter) — namespace 条項 superseded by this ADR
- ADR-2605262130 (kotoba storage substrate unification)
- `90-docs/260602-actor-stack-generation-inventory.md`
- `90-docs/260602-tsukuru-kotoba-native-migration-plan.md`
