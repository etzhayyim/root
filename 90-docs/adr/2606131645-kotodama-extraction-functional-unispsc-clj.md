---
id: adr-2606131645-kotodama-extraction-functional-unispsc-clj
title: "ADR-2606131645: kotodama 抽出 + 18,343 UNSPSC actor の機能化 Clojure 移行 + kotoba submodule 撤去"
status: proposed
doc_type: adr
topic: kotodama-extraction-functional-unispsc-clj
authoritative: true
last_verified: 2026-06-16
priority: 6.0
axis: architecture
weight: 0.70
priority_note: "substrate/actor topology change; unlocks the kotodama portion of the Step 8 gate"
authoritative_for:
  - kotodama package location (root-side, extracted repo — not inside the kotoba submodule)
  - UNSPSC actor implementation language + runtime (Clojure / langgraph-clj / kotoba Datom)
  - kotoba engine consumption by root (external dependency, not in-tree submodule)
depends_on:
  - "2605262130"
  - "2605214000"
  - "2605215000"
  - "2605171300"
  - "2606011500"
related:
  - "2605240000"
  - "2605232345"
  - "2606101200"
supersedes: []
superseded_by:
  - 2606161200
amended_by:
  - 2606161200
---

# ADR-2606131645: kotodama 抽出 + 18,343 UNSPSC actor の機能化 Clojure 移行 + kotoba submodule 撤去

**Status**: proposed
**Date**: 2026-06-13
**Deciders**: Jun Kawasaki (founder = Council Lv7+ 1/1)

# Context

`etzhayyim/root` の意味ある Python 実コードは約 5,546 件で、その最大の塊が kotoba submodule
(`40-engine/kotoba/crates/kotoba-kotodama/py/`) 内の **18,343 個の UNSPSC LangGraph agent**
(`c<code>.py`、UNSPSC 商品コード 1 個 = 1 ファイル、ADR-2605171300 / 2605240000 / 2605232345) である。

監査により判明した内訳と問題点:

- **Tier 3 placeholder 11,448 (61%)** — `receive→process→emit` の空テンプレ stub。**実機能していない**。
- **Tier 2 defaults-wrapper 5,239 (29%)** — テンプレ + spec 検証 + デフォルト注入。
- **Tier 1 bespoke 1,655 (9%)** — Gemini 生成の商品別ドメインロジック。**唯一まともに機能**。
- ISCO 関連は約 4 ファイルのみ(実質 UNSPSC 問題)。

3 つの構造的問題:

1. **空テンプレ問題**: 90% が機能しない stub であり「18,343 actor で全 UNSPSC をカバー」という主張が実態を伴わない。
2. **submodule ロック**: これらは kotoba **submodule** 内にあり、root から編集・移行しづらく、Step 8 atomic-cutover
   gate (ADR-2605214000 §3、法人登記 + Council 承認待ち) でロックされている。
3. **生成方針の非効率**: 91% がテンプレ生成物。ファイル単位で Clojure へ翻訳するのは非効率。

移行先 Clojure スタックは既に成熟している:
- `langgraph-clj` v0.2.0 — StateGraph orchestration (graph/checkpoint/kotoba_checkpoint、全 `.cljc` 移植可)
- `langchain-clj` v0.1.0 — Datomic 風 EAV ストア + Murakumo model adapter + `kotoba_db.cljc`
  (kotoba-server XRPC `com.etzhayyim.apps.kotoba.datomic.*` backend)

founder 意図(2026-06-13): 空テンプレ stub は不可。だが **UNSPSC coverage 18,343 は全件維持**し、
18,343 を **有機的(生きて個体化)・機能的(商品ごとに実際に役立つ)** な actor として
**kotoba Datom + Clojure + langgraph-clj** で実装し**実 deploy** する。移行は効率的に。
あわせて kotodama を kotoba submodule から独立させ、root から kotoba submodule を撤去する。

# Decision

## D1. actor 数は維持、減らすのは手書きファイルのみ (data-driven 機能化)

**18,343 全 coverage を不変条件として維持する。** 削減するのは「手書き `.py` ファイル数」だけ。
**1 個の機能的 organism フレームワーク (Clojure) + コード別データ/能力 → 18,343 個の生きた機能的 actor**
を data-driven に生成・deploy する。各 actor は自分の DID・自分の Datom 状態・heartbeat を持ち、
商品ドメインに対して実際に機能する。

各 actor の「機能的・有機的」は次の 4 源泉で全 18,343 に効かせる:

1. **コード別データ** — taxonomy + spec + risk-tags + 能力プロファイル。現状 enrichment 2,836 件
   (`80-data/unspsc_v26_ucalypt.jsonl`) を **全 18,343 へ拡張** (Murakumo でデータを生成、コードは生成しない)。
2. **能力ライブラリ** — 1,655 bespoke のドメインロジックを segment/family 別の再利用可能能力 (clj) に一般化し、
   placeholder/defaults 由来の 16,687 code も実機能を獲得させる。
3. **Murakumo 推論** — 商品 grounding の実推論 (Murakumo-only, ADR-2605215000 不変)。
4. **organism 生命** — heartbeat / joucho (event fold から創発) / kaizen を kotoba Datom log 上で
   (ibuki ADR-2606101200 パターン)。共有コードでも各 instance の軌跡は個体化する。

runtime 契約は不変に保つ: `invoke(input) -> {result:{code,title,segment,did,ok,...}, log:[...]}`、
DID = `did:web:etzhayyim.com:actor:c<code>`、HTTP 応答 `{ok,code,shard,threadId,state,latencyMs}`。

## D2. kotodama を独立 repo に抽出、root は依存参照

kotodama (Pregel framework + cells + UNSPSC organism framework + taxonomy data + bespoke clj) を
独立 repo `etzhayyim/kototama` に抽出する。root はこれを依存として参照する
(clj は `deps.edn` coord、Rust/TS host SDK は path/published 依存)。ローカル dev は sibling checkout を用いる。

## D3. kotoba Rust エンジンは外部依存、root から submodule 撤去

kotoba Rust エンジン (17 crates) を root の **in-tree git submodule から外部 cargo/git 依存へ**変更する。
`.gitmodules` の `[submodule "40-engine/kotoba"]` を削除し、in-tree `40-engine/kotoba` を除去する。
これは ADR-2605262130 (kotoba = canonical substrate engine) の **substrate としての地位は維持**したまま、
**物理的同梱形態のみ submodule → 外部依存へ**変更するもの。kotoba が canonical state engine である不変条件は不変。

## D4. Step 8 gate からの分離

ADR-2605214000 §3 の Step 8 atomic-cutover のうち、**kotodama runtime 部分 (`kotoba-kotodama/py/`) を本 migration に吸収し
解除**する。murakumo runtime rename (`50-infra/cluster/murakumo/`, 220-file の env/DNS/launchd 等) は
**本 migration のスコープ外**として分離して残す (引き続き法人登記 + Council gate)。両者を同一 PR に混在させない。

## D5. 不変条件 (本 ADR が固定)

- 18,343 全 coverage 維持 (registry `00-contracts/actor-registry/unispsc.json` と一致)
- 各 actor は機能的 — 空 stub 禁止 (空応答 0 をテストで強制)
- DID 不変 (`did:web:etzhayyim.com:actor:c<code>`)
- Murakumo-only 推論 (ADR-2605215000、商用 GPU 不可)
- kotoba Datom が canonical state (ADR-2605262130 / 2605312345)
- Apache 2.0 + Charter Rider 継承

## D6. founder ratification

本 ADR は CLAUDE.md「Council attestation = PR review」運用に基づき、founder (Council Lv7+ 1/1) が
本 migration を内包する PR の review approval をもって ratify する。

# Consequences

- **正**: 全 18,343 が実機能を持つ生きた actor になる (空 stub 解消)。手書き `.py` 18,343 → framework + data へ集約。
  root が kotoba submodule を持たなくなり、clone/CI が軽くなる。actor 状態が kotoba Datom に as-of 永続し有機的軌跡を持つ。
- **負/リスク**: 18,343 体の Murakumo 推論付き heartbeat を 10 ノード Mac mini fleet で回す負荷
  (既存 Python organism fleet が同規模実績 → cadence 制御 + フォールバックで吸収)。
  Murakumo データ生成の品質が機能性を左右 (能力ライブラリ + spec 検証で下限担保、bespoke parity で回帰検出)。
- **更新が必要な箇所**: `CLAUDE.md` (substrate engine 宣言・cell catalog ポインタ・do-not 句 line 402)、
  `bb.edn` test task、`50-infra/murakumo/fleet.toml` + `placement-contract.yaml`、`CHARTER-RIDER.md` (nv_compat パス)、
  `70-tools/scripts/lint/substrate-boundary.mjs`、`deps.toml [[migrations]]`、
  `PYMAGATAMA-MIGRATION-NOTES.md` (新 repo へ移設)。

# 実装記録 — Delivered (2026-06-16 更新)

決定どおり機能版 Clojure UNSPSC actor を **etzhayyim/kototama**(local: `orgs/etzhayyim/kototama`)に抽出済み。
当初記録(11 tests / 78 assertions)から下記まで前進した(`clojure -X:test` 再現可能)。

- **framework + データ**: `kototama.unspsc.{taxonomy capability organism react life fleet}`、taxonomy 18,342 code
  (`80-data/unspsc_v26_ucalypt.jsonl` enrichment ⨝ `00-contracts/actor-registry/unispsc.json` SSoT)。
- **bespoke 能力ライブラリ**: segment 別 capability を **8 → 33/36 segments** に拡張(charter-clean **33/33** 完了;
  15 fuels / 20 mining / 46 defense-security は charter 設計除外)。各 entry に parity test、空入力は常に reject。
  **40 tests / 222 assertions green**。
- **kotoba-Datom backend 配線**: `fleet/sweep!` の `:kotoba` store が `langchain.kotoba-db`(`kotoba-conn` +
  `kotoba-api` を `:db-api`)経由で checkpoint を永続。operator Bearer JWT(`:kotoba-token`、ADR-2605231525)対応。
  **ライブノード(127.0.0.1:8077)へ write→read 実証**(actor thread `unspsc-10101500` を Datom log から読戻し)。
- **Stage-D 学習ループ移植**: Python `unispsc_capabilities/wrapper.py` の `_compute_prior_consensus` を
  `kototama.unspsc.life/{prior-consensus prior-shortcut?}` に純関数移植(parity test)、organism に opt-in shortcut。
- **移行先 libs publish**: `langchain-clj v0.1.1`(openai-model adapter)/ `langgraph-clj v0.2.1`(StateGraph
  checkpointer XRPC)。root 内 clj は kaiyaku 式 git 座標で参照可能。
- **ツール: kotoba-code**(`com-junkawasaki/kotoba-code`)— model-neutral・test-gated・kotoba-Datom 永続の
  agentic コーディングエージェント(langchain-clj / langgraph-clj 上)。Phase 2c の能力 authoring の大半を
  kimi-k2.7-code(OpenRouter)で駆動、各ユニット test-gated + 監督レビュー + PR(#1〜#10)。実運用で
  retry-on-API-error / rollback-on-throw / gate-feedback(KC_GATE_ROUNDS)と段階的に堅牢化。

未了は本 ADR の `:gated`(operator/production-infra 依存)のまま: submodule 撤去 cutover・py 削除・fleet rollout。

# Alternatives Considered

- **1 個のパラメトリック agent に集約して 16,687 を削除** — ファイル数は最小だが「空 stub を 1 個の共有 stub に
  畳む」だけで coverage の機能性が上がらない。founder により却下 (「テンプレは良くない、全件を有機的・機能的に」)。
- **kotoba 全体を root へ vendoring (in-tree copy)** — submodule は消えるが Rust+py 全体を抱え upstream 同期を失う。重い。却下。
- **bespoke 1,655 を全件個別 clj へ機械翻訳** — 忠実だが 1,655 件分の検証コストが残り、placeholder 16,687 の
  機能化に寄与しない。能力ライブラリ + データ昇華を採用 (bespoke はその種)。
- **submodule 維持のまま py を clj 化** — Step 8 ロックと canonical-substrate の物理同梱が温存され、
  「root から submodule を持たない」という founder 要求を満たさない。却下。

# References

- ADR-2605171300 (Open-UNSPSC generative agent fleet — 本 ADR が空テンプレ生成方針を撤回)
- ADR-2605240000 / 2605232345 (UNSPSC organism W2 mass-deploy / actor-as-organism)
- ADR-2605214000 §3 (Step 8 atomic cutover — kotodama 部分を分離・吸収)
- ADR-2605215000 §4 (Murakumo-only inference)
- ADR-2605262130 (kotoba storage substrate unification — substrate 地位維持、同梱形態のみ変更)
- ADR-2606011500 §4 (kami-engine submodule パターン — 参照)
- ADR-2606101200 (ibuki organism autonomy — 機能的 organism の参照実装)
- langgraph-clj / langchain-clj (移行先 clj スタック)
