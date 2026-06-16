---
id: adr-2606161200-organism-runtime-3layer-kotodama-split
title: "ADR-2606161200: organism runtime 3層分割 — kotodama runtime / root unspsc actor / kotoba substrate (supersedes 2606131645)"
status: proposed
doc_type: adr
topic: organism-runtime-3layer-kotodama-split
authoritative: true
last_verified: 2026-06-16
priority: 6.0
axis: architecture
weight: 0.70
priority_note: "actor/runtime topology change; splits the kototama monolith into a reusable runtime + a concrete root actor"
authoritative_for:
  - "organism runtime location (com-junkawasaki/kotodama, generic, domain-injected)"
  - "UNSPSC concrete actor location (etzhayyim/root 20-actors/unspsc)"
  - "retirement of the standalone etzhayyim/kototama repo"
depends_on:
  - "2606131645"
  - "2605262130"
  - "2605215000"
related:
  - "2606101200"
supersedes: []
superseded_by: []
---

# ADR-2606161200: organism runtime 3層分割 — kotodama runtime / root unspsc actor / kotoba substrate

**Status**: proposed
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki (founder = Council Lv7+ 1/1; PR review = Council attestation)
**ADR hierarchy**: actor/runtime topology. **ADR-2606131645 を amend/supersede** する(同 ADR の D2「kotodama を単一の独立 repo に抽出」を、下記 3層分割に置き換える)。D1(機能版・空 stub 禁止)・D3(kotoba は外部依存)・D5(不変条件)・D6(founder ratification)は維持。

# Context

ADR-2606131645 は 18,343 個の Python `c<code>.py`(90% 空 stub)を撤去し、機能版 Clojure UNSPSC actor を **単一の独立 repo `etzhayyim/kototama`** に抽出した。実装は成熟した(bespoke capability 8→33/36、kotoba-Datom 配線、Stage-D 学習ループ、40 tests green)。

しかし運用してみると、kototama 1 repo に**性質の異なる 2 つ**が同居していることが違和感の源だった:

1. **汎用 organism runtime** — `life`(joucho/heartbeat/Stage-D prior-consensus)、`validate→reason→emit` graph、ReAct テンプレ。**どの actor でも再利用できる**機械(ibuki 等の organism も同型)。
2. **UNSPSC 具体実装** — `capability`(segment 別ドメイン論理)、`taxonomy`(18,342 code データ)、`fleet`(配備)。**1 actor の具体**であり、root の他 Tier-B actor と同列。

この 2 つが混在すると、kotoba(substrate)/ root(actor 群)/ kototama(両方混在)の 3-way の境界が曖昧になる。founder 判断で**3 層に明確分離**する。

# Decision

## D1. 汎用 organism runtime = `com-junkawasaki/kotodama`

`life` + `organism`(graph)+ `react` を、ドメイン非依存の再利用ライブラリ `kotodama` として **com-junkawasaki に langchain-clj / langgraph-clj の兄弟**として配置(published v0.1.0)。ドメイン論理は `:validate` / `:emit` 注入で受け取る。clj のまま、WASM 化して kotoba 上でも動く。

## D2. UNSPSC 具体 actor = `etzhayyim/root 20-actors/unspsc`

`capability` / `taxonomy` / `fleet` / `build_taxonomy` / `enrich` + `resources/unspsc-taxonomy.edn` を **root の actor 層 `20-actors/unspsc`** に配置。kotodama を git 座標で参照(kaiyaku 式 `:dev` override)。`unspsc.organism` が `cap/run` を `:validate`、UNSPSC 結果形(`{:code :title :segment :did :ok ...}`)を `:emit` として kotodama に注入。**他の root actor と完全に同列**。

→ ADR-2606131645 D2(single extracted repo)を**置換**。「actor は root の monorepo に住む」という方針に整合。

## D3. kotoba = 純粋 Rust substrate(不変)

kotoba は外部依存のまま(ADR-2606131645 D3 維持)。**clj を kotoba crate に同梱しない**(`kotoba-kotodama/py` の同梱ロック問題を再現しないため)。「kototama は kotoba の runtime」という意味論は、clj runtime が WASM 化されて kotoba 上で動くことで満たす(物理同梱不要)。

## D4. 独立 `etzhayyim/kototama` repo は廃止(archive)

内容は kotodama(runtime)+ root `20-actors/unspsc`(concrete)に分配済み。standalone repo と top-monorepo submodule を撤去・archive する。

## D5. 不変条件(維持)

18,342 full coverage / 全 actor functional(空 stub 禁止)/ DID `did:web:etzhayyim.com:actor:c<code>` / Murakumo-only inference(ADR-2605215000)/ kotoba Datom = canonical state(ADR-2605262130 / 2605312345)/ Apache-2.0 + Charter Rider。

# Consequences

- **再利用可能な runtime**: kotodama は他 actor family(ibuki 等)も使える汎用 organism 機械になる。organism の重複実装を 1 lib に収斂可能。
- **actor の一元化**: UNSPSC が root `20-actors` の通常 actor に。kotoba/root/kototama の 3-way の曖昧さが解消。
- **kotoba を触らない**: substrate は純 Rust のまま。
- **層境界 = 依存方向**: kotoba ◂ kotodama ◂ unspsc(concrete)。各層は git 座標で疎結合。
- リスク: kotodama の汎用 API 変更が下流 actor に波及 → semver tag + parity test で緩和。

# 実装記録 — Delivered (2026-06-16)

- **kotodama** `com-junkawasaki/kotodama` v0.1.0(802a04d): `kotodama.{life organism react}`、domain-free mock で **7 tests / 17 assertions green**。
- **unspsc** `etzhayyim/root 20-actors/unspsc`(PR #1826): kotodama v0.1.0 を runtime に、capability 33/36 + taxonomy 18,342 + fleet、**39 tests / 212 assertions green**。
- 依存: kotodama → langgraph-clj v0.2.1 → langchain-clj v0.1.1(git 座標)。
- 残: 独立 kototama repo / top-monorepo submodule の撤去・archive(D4 operator step)。

# Alternatives Considered

- **kotoba-kototama crate(kotoba workspace 内に clj 同梱)** — WASM-guest 配備には筋が通るが、ADR-2606131645 が解体した `kotoba-kotodama/py` の同梱ロック・保守摩擦を再現。却下(D3)。
- **kototama 単一 repo 維持(ADR-2606131645 のまま)** — runtime と concrete の混在が境界を曖昧にする(本 ADR の動機)。却下。
- **concrete を kotodama runtime 側に残す** — runtime が UNSPSC に汚染され再利用不能に。却下。

# References

- ADR-2606131645 (kotodama 抽出 + 機能化 — 本 ADR が D2 を置換、D1/D3/D5/D6 維持)
- ADR-2605262130 / 2605312345 (kotoba substrate / Datom = canonical state)
- ADR-2605215000 §4 (Murakumo-only inference)
- ADR-2606101200 (ibuki organism — 汎用 runtime の再利用候補)
- com-junkawasaki/kotodama (runtime) / etzhayyim/root 20-actors/unspsc (concrete) / langgraph-clj / langchain-clj
