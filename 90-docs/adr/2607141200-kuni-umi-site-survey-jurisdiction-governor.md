---
id: adr-2607141200-kuni-umi-site-survey-jurisdiction-governor
title: "ADR-2607141200: kuni-umi site_survey — jurisdiction-eligibility を governed advisor(mock + real Murakumo LLM)に置き換え"
status: active
doc_type: adr
topic: kuni-umi-site-survey-jurisdiction-governor
authoritative: true
last_verified: 2026-07-14
status_note: "sole-member founder session directive の一連の流れ(SDモデル逆トポロジーソートWave進行 → kuni-umi調査 → 安全範囲限定での小規模実装)で実施。kuni-umi自身のCLAUDE.md boundary tableで明記済みの制約(intendedUse: civilian/community/commons のみ許可)をコードとして実装した — 新しい制約の導入ではなく、既存の文書化された制約の実装ギャップを埋めるもの。"
priority: 6.5
axis: safety
weight: 0.55
priority_note: "S0スコープ内(ハードウェア・motion・witness署名には一切触れない)の縮小スコープ。cells/site_survey/cell.cljc の唯一の pure node である jurisdiction_eligibility が、これまで intendedUse に関わらず常に accepted=true を返す R0 placeholder だった実装ギャップを埋める。ADR-2605201400 §5 の本来の Rego policy 統合の代替ではなく、その前段として governed advisor パターン(tashikame/kouhou/yosoku/fleetと同型)を導入する first cut。"
authoritative_for:
  - "kuni-umi site_survey cell の jurisdiction-eligibility 判定ロジックの正本"
  - "com-etzhayyim-kuni-umi における Murakumo-fleet allowed-infer-hosts allowlist(tailnet経由含む)"
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605201500-etzhayyim-kuni-umi-s1-solo-survey
related:
  - adr-2605192100-etzhayyim-mission-charter
supersedes: []
superseded-by: []
---

# ADR-2607141200: kuni-umi site_survey — jurisdiction-eligibility を governed advisor(mock + real Murakumo LLM)に置き換え

**Status**: active
**Date**: 2026-07-14
**Scope**: `com-etzhayyim-kuni-umi` の `cells/site_survey/` のみ。他cell(deployment_planning/
construction_orchestration/commissioning/decommission/audit_witness)・robotics/・
S-phase・witness invariant(N≥2署名)には一切触れない。**S0のまま**——本ADRは
S0→S1のフェーズ遷移ではない。

## Context

`com-junkawasaki/root` 側で進めていたetzhayyim post-nation-state substrate
system dynamicsモデル(ADR-2607132200系列)の逆トポロジーソートWave進行の一環として、
Wave 2の`AttestationCoverage`/`RoboticsUnits`の実世界対応であるkuni-umiを調査した。

kuni-umi自身の`CLAUDE.md`が定める非交渉事項の中に:
> `intendedUse` | 許可: civilian / community / commons | 禁止: military / proprietary closed-design

という制約が既に明記されているが、`cells/site_survey/cell.cljc`の`jurisdiction-
eligibility`(唯一のpure node、他は全てハードウェア/SDK未実装でraiseするR0
scaffold)は、この制約を一切コードとして実装しておらず、**あらゆる`intendedUse`
（militaryを含む）に対して無条件に`accepted=true`を返していた**
(コメント: "R0 scaffold returns accepted=true for syntax validation; real DMN
integration requires the ADR-2605201400 §5 Rego policy")。

本ADRは、tashikame/kouhou/yosoku/fleet(`com-junkawasaki/root`ADR-2607132200系列
及びその直後の作業)で確立した「advisor提案 + 独立governor検証」パターンを
この既知のギャップに適用する。

## Decision

### 1. `jurisdiction-governor`(新規、`cell.cljc`内)

state(サイトメタデータ)から独立に判定を導出——advisorの自己申告
(`:accepted`)を信用しない:

1. **ハード制約(最優先、advisorで上書き不可)**: `intendedUse` ∈
   {civilian, community, commons}。この定数はyosoku等の`ComplianceFloor`と
   同じ役割——本ADRのfollow-upであっても、この集合を広げる変更は別ADRで
   明示的に議論すること。
2. **ソフト制約(R0段階、将来のRego policyで精緻化予定)**: `jurisdictionDid`/
   `localLawAttestationCid`の存在確認。
3. **Advisor自身の判定 + confidence floor(0.5)**。

### 2. `mock-advise`(新規)— オフライン既定

advisorは何も独自判断せず、governorのルールに委ねる決定的関数
(`{:accepted true :confidence 1.0}`固定)。安全側のデフォルト。

### 3. `cells/site_survey/advisor.cljc`(新規ファイル)— 実LLM配線

`langchain.model`経由のMurakumo fleet接続。`allowed-infer-hosts`は
`com-etzhayyim-yosoku`/`tashikame`/`kouhou`/`fleet`(2026-07-13/14に
`api.murakumo.cloud/nodes`レジストリと突き合わせ済み)と同一のtailnetノード
8台を含む。`cell.cljc`自体は`langchain.model`をrequireしない
(「このレイヤーはlanggraph依存なし」という既存方針を「langchain依存なし」にも
拡張——DIとして`state -> proposal`の裸関数を受け取るのみ)。

### 4. 動作確認

- `clojure -M -e`(`load-file`経由——本repoの`kuni-umi.*`namespace宣言は
  実ファイルパスと一致せず、`etzhayyim/root`monorepoのbb classpath外では
  `require`が解決しない既知の構造的事情のため、既存の`run_tests.sh`と
  同様に本ADRの検証でもこの制約に従った): 15 tests / 44 assertions green
  (新規9テスト追加、既存2テストを現実的な入力値に更新)。
- clj-kondo: 本ADRの変更に起因する新規エラー0件(既存の
  namespace/file-path不一致由来のエラーは変更前から存在、対象外)。
- **実LLM経由でのライブ検証**(`dan`ノード、100.98.142.59:11434、
  `gemma4:e4b-it-qat`): eligibleサイト(`intendedUse: community`)→
  `accepted: true`。militaryサイト→ **governorのハード制約により、実LLMの
  判定を待たずに`accepted: false`**(rejectionReason に "constitutional
  boundary" を明記)。実LLM推論が介在してもconstitutional invariantが
  独立に効くことを実証。

## Consequences

- (+) 既知の実装ギャップ(military intendedUseが無条件accepted=trueだった)が
  閉じた。これは新しい制約の追加ではなく、既存文書化済み制約の実装。
- (+) tashikame/kouhou/yosoku/fleetと同型のgoverned-advisorパターンが、
  langgraph-clj StateGraphを持たないシンプルなcell構造にも適用可能である
  ことを実証(裸関数DIで足りる——過剰な依存追加を避けた)。
- (+) `deps.edn`を新規追加し、本repoが(bb経由のmonorepo組み込みに加えて)
  `clojure` CLIでも部分的に検証可能になった(既存の名前空間/ファイルパス
  不一致は未解消のfollow-up、本ADRのスコープ外)。
- (−) `jurisdiction-eligibility`のソフト制約(jurisdictionDid/
  localLawAttestationCid必須)はR0段階の簡易版であり、ADR-2605201400 §5の
  本来のRego DMN policyではない——それは引き続きfollow-up。
- (−) `allocate_scout_fleet`/`collect_sensor_blob`/`witness_attest`/
  `emit_survey`等、他の全nodeは未変更(ハードウェア/SDK未実装でraiseする
  ままR0)——本ADRはsite_surveyの最初の1 nodeのみを対象にした意図的に
  狭いスコープ。
- (−) `com-etzhayyim-kuni_umi`(アンダースコア表記の重複登録repo)は本ADRの
  対象外、未変更のまま(別途の整理が必要、本ADRの範囲外)。

## Artifacts

- `com-etzhayyim-kuni-umi`: `cells/site_survey/cell.cljc`(governor + mock-advise
  追加)、`cells/site_survey/advisor.cljc`(新規)、`cells/site_survey/deploy.clj`
  (新規)、`cells/site_survey/test_cell.cljc`(既存2テスト更新 + 新規9テスト)、
  `deps.edn`(新規)。

## References

- ADR-2605201400(kuni-umi master、CLAUDE.md boundary tableの出典)
- ADR-2605201500(S1 solo survey——本ADRが対象とするsite_survey cellの元設計)
- `com-junkawasaki/root` ADR-2607132200系列(governed-advisorパターンの
  手法的出典)、ADR-2607141500(tailnet allowlistの出典)
