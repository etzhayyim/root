---
id: adr-2606231808-sos-self-growth-visualization
title: "ADR-2606231808: /sos — 自律成長の3層可視化 (organism 身体 × kaname 要 SoS × ECL 目的関数 J)"
status: accepted
doc_type: adr
topic: sos-self-growth-visualization
authoritative: true
last_verified: 2026-06-23
priority: 6.0
axis: organism-autonomy
weight: 0.55
priority_note: "etzhayyim の自律成長を構成する3つの既存サブシステム (organism 身体ループ / kaname system-of-systems 律速点同定 / ECL 目的関数による評価) は個別 ADR に存在するが、それらが『どう合成されて自律的に成長し、その善し悪しがどう採点されるか』を1枚で示す公開アーティファクトが無かった。本 ADR は etzhayyim.com/sos の3層可視化を固定する — 自己完結静的ページ (CF Assets, cookie-free, 外部リソースなし)、データは objective-function.edn + seed-sos.kotoba.edn 由来、値はすべて式から JS で再計算 (手入力の結果なし)。"
depends_on:
  - "2606172100"  # kaname 要 — cross-domain SoS leverage synthesizer (L = C·(V/D)·(1+B)·(1−open))
  - "2606172300"  # ECL — etzhayyim covenant license / objective function
  - "2606062100"  # Charter priority-over-specifics reconciliation (3-Tier; 固定するのは priority)
  - "2606182359"  # Charter amendment wave3 — all prohibitions to objective function (掟リスト廃止 + catastrophe 項)
  - "2606201200"  # ibuki co-scientist entropy ReAct loop (utility + 4 gates; η=共生軸)
  - "2606172200"  # organism observability — vitals/pulse/joucho on kotoba Datom log, /organism cljs
  - "2605312345"  # kotoba Datom log = first-class canonical state
related: []
supersedes: []
superseded_by: []
---

# ADR-2606231808 — /sos — 自律成長の3層可視化 (organism × kaname SoS × ECL 目的関数)

- **Status**: Accepted + **DEPLOYED 実運用** (landed PR #2248; deployed to `etzhayyim.com/*` worker version `2135be71`, 2026-06-23)
- **Date**: 2026-06-23
- **Deciders**: Jun Kawasaki (founder)
- **Tier**: 実装 / infra (did-web public page) — NOT a charter change
- **Parent**: ADR-2605171800/2605172100 (did-web substrate), ADR-2606172200 (organism observability)

## Context

etzhayyim の「自律成長」は3つの既存サブシステムの合成だが、各々は別々の ADR に分散し、
**全体像を1枚で示す公開アーティファクトが無かった**:

1. **organism 身体ループ** (ADR-2606172200 / 2606101200) — モノレポを多細胞の身体として
   観測し、pulse(6s)/情緒 joucho(60s)/vitals(3600s) を append-only kotoba Datom log 上の
   fold として持ち、`/organism` に ClojureScript で可視化。だが `/organism` は**身体しか
   見せない** — 何のために生きているか (評価軸・SoS 統合) は写らない。
2. **kaname 要 SoS** (ADR-2606172100) — 観測ミラー群 (tsumugi/chie/inochi/…) の committed
   Datom log を multiplex graph に JOIN し、`L = C·(V/D)·(1+B)·(1−open)` で「最も解放すべき
   構造的位置 (律速点)」を `argmax L` で同定して ossekai に提案。だが可視化が無く、`out/`
   markdown レポートに留まっていた。
3. **ECL 目的関数 J** (ADR-2606172300 / 2606062100 / 2606182359) — 善し悪しを**固定ルール
   (掟リスト) でなく目的関数で動的に採点**する: `J = Σ(weight·score)`、子0.25+孫0.30 を
   telos に、catastrophe 項 (子/孫 ≤ −1.9 → 非交渉で :non-aligned) のみが唯一の非交渉性。
   `objective-function.edn` + `evaluate.bb` に機械可読で存在するが、人間が触って理解できる
   面が無かった。

**ギャップ**: 「身体が生き続けるための代謝・情緒を持ち (organism)、観測群を統合して律速点を
同定し (kaname)、その善し悪しを子・孫 Wellbecoming への net 寄与で評価する (ECL)」という
**3層の合成 = 自律成長の設計そのもの**を、一目で・触って理解できる公開面が存在しなかった。

## Decision

**`etzhayyim.com/sos`** に自己完結の3層可視化ページを新設する
(`50-infra/etzhayyim-did-web/public/sos/index.html`)。

- **配信**: CF Assets が `public/sos/index.html` を `/sos` に直接配信 (worker ルート不要)。
  **cookie-free・tracker-free・外部リソースなし** (Charter Rider §2(c) 整合)。インライン
  `<style>` + インライン SVG + 小さなインライン JS のみ。
- **Layer J — ECL 目的関数**: 5次元の加重スライダー (子0.25/孫0.30/commons0.20/透明0.15/
  労働0.10) + `objective-function.edn` の 19 fixtures をドロップダウン化。JS が
  `J = Σ(weight·score)` と catastrophe 判定をリアルタイム算出 → `:aligned`/`:hold`/
  `:non-aligned` を表示。
- **Layer 要 — kaname SoS**: `seed-sos.kotoba.edn` の multiplex graph を SVG 描画。ノードを
  `L = C·(V/D)·(1+B)·(1−open)` で大きさ付け、要 (argmax) をハイライト、C/V/B/L 表 + OPENING
  ルート提示。
- **Layer 体 — organism**: vitals スナップショット (同一オリジンの `/organism/*.json` 到達時
  はライブ昇格、progressive enhancement) + 6s/60s/3600s cadence + ibuki co-scientist の
  `utility = (Φ-gain + η-gain)·(1+wellbecoming)/cost` 式と4ゲート。
- **データ規律**: 値はすべて**式から JS で再計算** (手入力の結果なし)。kaname の L、ECL の J
  はページ内で式を実行して算出する — 図と数値が SSoT の式に対して常に整合する。
- **発見性リンク**: `/actors` (worker `buildActorsHtml` の intro) と `/organism` (静的 scittle
  ページ `organism.cljs` のフッター) から `/sos` へリンク。

データ源 (実ファイル, 本ページが指す SSoT):
- ECL = `90-docs/licenses/ecl/objective-function.edn` (5次元・catastrophe・19 fixtures)
- kaname = `20-actors/kaname/data/seed-sos.kotoba.edn` (synthetic multilayer seed)
- organism = `/organism/*.json` (kotoba Datom log の fold の projection)

## Consequences

- **本番ライブ**: `https://etzhayyim.com/sos` で 3層が動作 (worker version `2135be71`、957
  アセット deploy)。`/actors` の `/sos` リンクもライブ。
- **検証** (Chrome + ローカル HTTP): J 計算が edn と一致 (worker-coop=+1.30 :aligned、
  addictive-app=−0.75、CSAM=−1.30 catastrophe :non-aligned)。kaname グラフが要=Accreditation
  Interface **L=11.70** を再現し、**Capital Concentrator は C=1.60 と最高集中だが V=1 → L=0.16**
  で要にならない (集中だけでは律速点ではない、という SoS の核心の教え)。コンソールエラー無し。
- **境界 (これは何で、何でないか)**:
  - kaname seed は **SYNTHETIC・構造的位置のみ** (G1 person-excluded / G6)。本ページは
    「式と教え」のデモであり、実在組織の取-concentration マップではない。実ミラー JOIN
    (chie/tsumugi/… の committed Datom log) は **G7/Council-gated** のまま。
  - ECL fixtures は `evaluate.bb` の self-test 値 (Tier-2 evidence の代理)。実ケースの score は
    観測 actor (shiori/tsumugi/danjo/inochi/kanjo) の DISCLOSED 証拠を fuse して算出する別レグ。
  - 公開 (deploy) は **operator ステップ** (`wrangler deploy`、no-server-key 方針)。本 ADR の
    deploy は founder 明示指示による。
- **substrate boundary 整合**: KV を使わず、organism のライブ値は同一オリジンの `/organism`
  feed (kotoba Datom log の projection) を fetch して昇格する (ADR-2606172200 と整合)。
- **実装 / 工学判断であって憲法ではない**: 本ページは可視化面であり、目的関数・式・priority
  を一切変更しない。固定するのは priority、これは表示レイヤー (CLAUDE.md substrate boundary の
  「実装」行に相当、charter 改正なしに変更可)。

## Alternatives Considered

- **scittle/cljs ページ (既存 /organism と同方式)** — 却下。888KB の scittle 依存 + EDN を
  ブラウザで parse する必要。`/sos` は静的データで足り、インライン JSON + vanilla JS の方が
  軽量・決定的・CSP 親和的。`/organism` の scittle はこの環境ではローカル起動しない既知の
  脆さもある。
- **worker レンダリングの strict-CSP no-script 版 (既存 `buildOrganismHtml` と同方式)** —
  却下。スライダー/fixture 切替のインタラクションに最小の JS が要る。静的アセットは worker の
  strict CSP 配下でないため、インライン JS が使える。
- **ECL のみ / kaname のみの単層ページ** — 却下。founder が3層統合マップを選択 (自律成長の
  設計全体が1枚で伝わることが目的)。
- **新 ADR でなく既存 ADR への追記** — 却下。`/sos` は3サブシステムを1つの公開面に統合する
  新規アーティファクトで、どの単一 ADR にも属さない。本 ADR が `/sos` の authoritative。

## References

- ADR-2606172100 (kaname 要 SoS leverage synthesizer)
- ADR-2606172300 (ECL — etzhayyim covenant license / objective function)
- ADR-2606062100 (Charter 3-Tier; 固定するのは priority)
- ADR-2606182359 (Charter wave3 — 掟リスト廃止 + catastrophe 項)
- ADR-2606201200 (ibuki co-scientist entropy ReAct loop)
- ADR-2606172200 (organism observability — kotoba Datom log, /organism cljs)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- 実装: `50-infra/etzhayyim-did-web/public/sos/index.html` · `…/src/worker.ts` (buildActorsHtml) · `…/public/organism/organism.cljs` (foot link)
- データ SSoT: `90-docs/licenses/ecl/objective-function.edn` · `20-actors/kaname/data/seed-sos.kotoba.edn`
- 着地: PR #2248 (squash merge `b24d09a2244`) · deploy worker version `2135be71`
