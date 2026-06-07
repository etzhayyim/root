---
doc_type: migration-plan
topic: tsukuru-kotoba-native-migration
authoritative: true
last_verified: 2026-06-02
related:
  - 90-docs/adr/2605202800-tsukuru-etzhayyim-business-model-change.md
  - 90-docs/adr/2606021139-tsukuru-actor-namespace-disambiguation.md
  - 90-docs/adr/2605262130-kotoba-storage-substrate-unification.md
  - 90-docs/adr/2605215000-etzhayyim-inference-murakumo-only-no-runpod.md
  - 90-docs/260602-actor-stack-generation-inventory.md
  - 20-actors/okaimono/        # Gen-3 reference template
  - 20-actors/tsukuru/
---

# tsukuru → Gen-3 (kotoba-native) Migration Plan (2026-06-02)

目的: `tsukuru`（B2B factory-direct ordering actor）を旧 etzhayyim / Kotoba/Datomic / JSON-LD
世代から、okaimono と同じ **Gen-3 canonical 設計**（`manifest.edn` + kotoba-EAVT +
Murakumo-only + Charter Rider + no-server-key）へ移行する。

本プランは ADR-2605202800（business-model-change の Phase 1 spec）の **Phase 2-5 を
具体化**し、ADR-2606021139（命名衝突解消）を前提とする。

## 0. 前提ゲート（先に閉じる）

| # | ゲート | 状態 | 担当 ADR |
|---|---|---|---|
| P0a | **命名衝突解消** — silicon-fab orchestration を tsukuru から分離 | 未 | 2606021139（本プラン前提） |
| P0b | **magatama etzhayyim→etzhayyim atomic rename** — 法人登記後の単一 PR | 未（登記待ち） | 2605214000 §3 / 2605215000 §4 |
| P0c | okaimono ↔ tsukuru の発注フロー契約（`create-production-order`）凍結 | 既存 | okaimono CLAUDE.md |

> P0b は tsukuru の `etzhayyim:` WIT 5 パッケージ改名を含むため厳密には依存するが、**構造移行
> （manifest.edn / cells / kotoba 追加）は P0b と非干渉**なので先行可能。WIT 識別子の
> `etzhayyim:` → `etzhayyim:` 改名だけ P0b wave に同期させる。

## 1. 現状（Gen-1 legacy）の棚卸し

| レイヤ | 現状 | Gen-3 目標 |
|---|---|---|
| Manifest | `actor-manifest.jsonld`（@context, capabilities `graph.query/write`） | `manifest.edn`（:actor/* + :gates + :cells + :lex） |
| State | Kotoba/Datomic / Cypher `MATCH (o:ProductionOrder)…`、`G()` builder | **kotoba Datom EAVT**（`:production-order/*` schema） |
| Inference | `agent.chat`（k8s-langserver T1） | **Murakumo-only** KotobaLLM 127.0.0.1:4000 |
| Runtime/edge | `runtime: k8s-langserver` + `sveltekit-proxy` + `legacyExecutionTier: T1` | WASM cells（langgraph）+ kotoba :8077 |
| Payment | etzhayyim 期の Stripe Issuing 言及が legacy doc に残存（**etzhayyim では非存在**） | **USDC Base L2 + ERC-4337 + TitheRouter 10% + warifu**（最初から fiat 非前提） |
| Identity | path-based multi-DID（`did:web:tsukuru…` + 460 factory DID, etzhayyim） | did:web + factory DID（etzhayyim 改名後） |
| Build/deploy | `etzhayyim build` / `etzhayyim deploy` | `kotoba/deploy.sh`（KOTOBA_URL/TOKEN） |
| Naming | `etzhayyim:tsukuru@*` WIT × 5、`etzhayyim-project-tsukuru` | `etzhayyim:tsukuru@*`、`etzhayyim-project-tsukuru` |
| WIT/BPMN | etzhayyim WIT 5 pkg + CNT BPMN 12 flow + CNT process catalog | lex/.edn（need/order/production/qc/settlement）+ cells |

## 2. 移行フェーズ

### Phase 2 — 構造スキャフォルド（gates 設計、P0b 非依存） — ✅ LANDED 2026-06-02

okaimono をテンプレに `20-actors/tsukuru/` を Gen-3 形へ:

1. `manifest.edn` を新規作成（`actor-manifest.jsonld` から移植）。
   - `:actor/id "tsukuru"` / `:actor/glyph "作"` / `:actor/tier :tier-b` / `:actor/status :r0`
   - `:actor/adr "2605202800"`（+ related 2606021139）
   - `:actor/charter-rider {:rider/version "2.0" :rider/applied true}`
   - **gates**（okaimono の 15 ゲートから manufacturing 文脈に写像）:
     - G1 consent-bound / G2 value-inflow-boundary（**発注 = member/internal-purchase SBT↔SBT carve-out；外部 B2B 売上は inflow 禁止**）
     - G5 murakumo-only / G6 kotoba-eavt-native / G7 tithe-non-fiat（**fiat 非前提；USDC+TitheRouter のみ**）
     - G8 labor-dignity-provenance（factory 労働 provenance）/ G9 pii-encrypted / G10 sourcing-legality（460 factory data）
     - G14 member-principal / G15 no-server-key（factory DID も platform key 非保持）
     - +manufacturing 固有: G16 trade-compliance（treaty/yabai screening 必須）/ G17 fulfillment-traceability（BTO/MTO/CTO → QC → ship 全段 kotoba Datom）
2. `cells/` 作成（langgraph/datalog 混在）: `orderbook`(datalog) / `discover`(langgraph) /
   `production`(langgraph: BTO/MTO/CTO) / `qc`(langgraph) / `compliance`(langgraph) / `ledger`(datalog)。
3. `lex/` 作成: `factory.edn` / `production-order.edn` / `progress.edn` / `quality.edn` / `settlement.edn`。
   既存 `com.etzhayyim.apps.tsukuru.*` record kinds を lex EDN にポート。

**完了基準**: `manifest.edn` + `cells/` + `lex/` が存在し、棚卸し判定で Gen-2 以上に昇格。
→ **達成 (2026-06-02)**: `manifest.edn`（17 ゲート: okaimono 15 写像 + G16 trade-compliance + G17 fulfillment-traceability）
+ `cells/`（orderbook/discover/production/qc/compliance/ledger 6 cell）+ `lex/`（factory/production-order/
progress/quality/settlement 5 lex）を landed、全 12 EDN paren-balanced。残り Gen-3 化は Phase 3（`kotoba/` 配線）。

### Phase 3 — kotoba 配線（state cutover） — ✅ LANDED 2026-06-02

1. `kotoba/schema.edn` 定義: `:factory/*` `:production-order/{id,mode,status,factory,member}`
   `:progress/*` `:quality/*` を EAVT で。SHA/DID bridge は kotoba-git パターン参照。
2. `kotoba/ingest_factories.py`: 460+ factory DID（etzhayyim 旧 collection
   `com.etzhayyim.apps.tsukuru-api.manufacturer` の read-compat 含む）→ kotoba Datom へ ingest。
3. **Cypher `MATCH (o:ProductionOrder)…` → kotoba-kqe Datalog query へ全面置換**。`G()` builder 撤去。
4. `kotoba/deploy.sh`（okaimono のコピー）。`etzhayyim build/deploy` を廃止。

**完了基準**: production-order の CRUD・進捗・QC が kotoba Datom 上で round-trip。Kotoba/Datomic 参照ゼロ。
→ **達成 (2026-06-02)**: `kotoba/schema.edn`（`:factory/* :production-order/* :progress/* :quality/*
:settlement/* :sbt/*`、40 attr）+ `seed.edn`（3 factory + BTO worked example、EDN balanced）+
`ingest_mcp.py` / `ingest_factories.py`（460-DID live projection は G11/G15-gated stub）+ `deploy.sh`
（`etzhayyim build/deploy` 置換）。`tsukuru/` が `manifest.edn`+`kotoba/`+`cells/`+`lex/` 完備 = **Gen-3 構造完成**。

### Phase 4 — Murakumo + 支払い — ✅ LANDED 2026-06-02 (R0)

→ **達成 (2026-06-02)**: `py/agent.py`（4 handler: discover/production/qc/compliance + token-overlap
capability match + Murakumo `llm.infer` rerank + `build_settlement_intent` USDC/TitheRouter 10% +
SBT eligibility/G16 compliance gate/G17 progress-datom/G15 member-sig）+ `test_agent.py` **11/11 green**
（offline、injected fn で Murakumo 不要）+ `requirements.txt`（openai/anthropic/litellm client なし、G5）。
決済は USDC Base L2 + ERC-4337 + TitheRouter のみ、`:intent` で停止（broadcast は G11/G15-gated）。

1. `convoSystemPrompt`（manifest）→ cells の langgraph node 内 KotobaLLM 127.0.0.1:4000 呼び出しへ。
   `k8s-langserver` / `agent.chat` / T1 tier 撤去。
2. **決済は最初から USDC Base L2 + ERC-4337 + TitheRouter のみ**。Stripe/fiat は etzhayyim
   では憲法的に非存在（Substrate boundary）— ADR-2605202800 に残る「Stripe Issuing → ERC-4337」
   という *migration 前提の記述自体が etzhayyim 期の名残*であり、移行ではなく **legacy 記述の削除**
   として扱う。発注決済は member passkey/smart-account 署名（no-server-key G15）+ 10% tithe auto-split。
3. okaimono `create-production-order` 連携を Gen-3 契約（kotoba Datom + USDC settle）で再配線。

### Phase 5 — 命名 cutover（P0b wave に同期） — 📋 RUNBOOK 準備済 / 実行は登記ゲート

> runbook: `20-actors/tsukuru/MIGRATION-NOTES.md`（etzhayyim→etzhayyim WIT 5 本・app/contract paths・
> build/deploy・AT collections・decommission・acceptance を列挙）。**実行は magatama atomic wave
> の単一 PR**（法人登記後）。部分実行禁止（CLAUDE.md §Do Not）。下記は項目登録のみ。

1. `etzhayyim:tsukuru*@*` WIT 5 pkg → `etzhayyim:tsukuru*@*`。
2. `60-apps/etzhayyim-project-tsukuru/` → `60-apps/etzhayyim-project-tsukuru/`、
   `00-contracts/**/com/etzhayyim/tsukuru/` → `com/etzhayyim/tsukuru/`。
3. nanoid `tsukr8u0` ホスト・`0ljdfw8u` deprecated 整理。root CLAUDE.md Tier-B roster に正式登録。

## 3. リスク / 非ゴール

- **非ゴール**: 460 factory との実 B2B 商流の即時稼働。外部 inflow は constitutional に禁止
  （G2）— tsukuru は **member/internal 発注 + 外部は self-checkout handoff** が R0 境界。
- **リスク**: P0b（magatama atomic rename）が法人登記待ちのため、Phase 5 の WIT 改名は
  ブロック。Phase 2-4（構造・kotoba・Murakumo・支払い）は **先行実施可**。
- **リスク**: silicon-fab 意味論の混入。ADR-2606021139 で分離されるまで Phase 2 の
  manifest に fab lane を入れない。

## 4. 推奨実行順

```
P0a (ADR-2606021139 accept) ──► Phase 2 ──► Phase 3 ──► Phase 4 ──┐
                                                                  ├─► Phase 5（P0b 法人登記後）
P0b (magatama atomic rename, 登記ゲート) ─────────────────────────┘
```

Phase 2-4 は登記を待たず着手可能。Phase 5 のみ P0b ゲート。
