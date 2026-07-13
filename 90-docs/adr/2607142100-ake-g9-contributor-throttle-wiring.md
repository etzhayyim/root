---
id: adr-2607142100-ake-g9-contributor-throttle-wiring
title: "ADR-2607142100: ake propose — G9 anti-vandalism / contributor-trajectory throttle を intake membrane に配線"
status: active
doc_type: adr
topic: ake-g9-contributor-throttle-wiring
authoritative: true
last_verified: 2026-07-14
status_note: "etzhayyim root成熟度向上タスク(item 4「R0→R1 advancement」)の継続、ADR-2607141600(yadori/watari)・ADR-2607141900(sanae)と同じ監査手法の適用結果。kuni-umi/yadori/watari/sanaeと異なり、本件は既存primitiveの単純な配線ではなく、既存の純粋関数cellにoptional inputフィールドを追加するという設計判断を要したため、agent単独では一旦保留し、sole-member founderの明示的な承認(「pr create merge 2 main」の意図確認を経て「Go ahead with the ake G9 fix」を選択)を得てから実施した。"
priority: 5.5
axis: safety
weight: 0.40
priority_note: "ake CLAUDE.mdは「Structural invariants live in three places each (schema/lexicon/Python)... touch one, touch all three」と警告するが、G9(anti-vandalism/contributor-trajectory)は列挙型(enum)や`:db/allowed`のような構造的invariantではなく、振る舞い的(behavioural)なrate/trajectory throttleであり、schema/lexiconの3点セットには該当しない——`methods/contributor.py`のdocstring自身が「NOT a stored score and NOT permanent」と明記する非構造的invariantであるため、3点セット警告の対象外と判断した。scope: `cells/propose/state_machine.cljc`の`transition-to-screened`のみ。"
authoritative_for:
  - "ake propose cell の G9(anti-vandalism/contributor-trajectory throttle)配線の正本"
depends_on:
  - adr-2606052100-ake-community-edit-membrane-wikipedia-stance-r0
related:
  - adr-2607141600-yadori-watari-documented-gate-implementation-gaps
  - adr-2607141900-sanae-g2-displacement-dividend-coupling-gap
supersedes: []
superseded-by: []
---

# ADR-2607142100: ake propose — G9 anti-vandalism / contributor-trajectory throttle を intake membrane に配線

**Status**: active
**Date**: 2026-07-14
**Scope**: `20-actors/ake/cells/propose/state_machine.cljc` の `transition-to-screened` のみ。
他4cell(edit_triage/review_vote/promote/revision_log)・`methods/contributor.cljc`本体・
G1-G8の既存実装には一切触れない。

## Context

yadori/watari(ADR-2607141600)・sanae(ADR-2607141900)に続き、同じ監査手法(actor
CLAUDE.mdのgate表 vs 実装コード)をake(9 gate・5cellの community-edit membrane)に
適用した。ake CLAUDE.mdは:

> **G9 anti-vandalism / contributor-trajectory** — per-DID rate + a Wellbecoming
> acceptance history (`as-of`), NOT a punitive score-of-soul (kizashi G8). Repeated
> charter-violating proposals throttle; they never mint a permanent reputation number.

および `methods/contributor.py` を「the G9 engine (rate limit + recoverable
Wellbecoming trajectory)」と明記するが、`methods/contributor.cljc`(rate-ok /
throttled? / trajectory 等を完全実装・単体テスト済み)を実際に呼んでいるのは
`methods/analyze.cljc`(オフラインレポート生成スクリプト)のみで、CLAUDE.md自身が
「the runtime path」と呼ぶ実際のcell chain(propose→edit_triage→review_vote→
promote→revision_log)のどこからも呼ばれていなかった。結果、`throttled?`が真を
返すような直近の反復拒否履歴を持つDIDでも、`propose`は無制限に新しい編集提案を
受理し続けていた——kuni-umi/yadori/watari/sanaeと同型の「文書化済みgate + 既に
実装済みのdangling primitive、実行経路への未配線」パターン。

他の3件(kuni-umi/yadori・watari/sanae)と異なり、本件はagentが単独で「既存primitive
をそのまま呼ぶだけ」で完結せず、`transition-to-screened`(現状はstate mapのみを
受け取る純粋関数)に「呼び出し側が持つcontributor trajectoryをどう渡すか」という
設計判断を要した。ake CLAUDE.mdの「Structural invariants live in three places
each...touch one, touch all three」という強い警告もあり、agentはこの実装を一旦
保留してsole-member founderに設計方針を確認し、明示的な承認を得てから実施した。

## Decision

### 1. `transition-to-screened` の入力に `"contributor_trajectory"` を追加(optional)

```clojure
(contributor/throttled? (get state "contributor_trajectory" {}) (get cs "author"))
(refuse "G9: author is currently throttled ...")
```

`state`(cellへの生入力map)から直接読む——`cell_state`(`cs`)側にpersistしない。
理由: `robot_sigs`/`human_attestation`(sanae)や`member_sig`/`server_sig`(yadori)が
「その提案自体の一部」としてcell_stateに残るのに対し、contributor trajectoryは
「その提案とは独立した、著者に関する外部の履歴データ」であり、提案record自体の
プロパティではない——ake自身の`propose`が「REFUSAL gate, not a clamp」という
純粋関数の設計原則を保ったまま、trajectoryを一時的な評価コンテキストとして
渡すだけにとどめた。

未指定時のデフォルトは `{}`(空trajectory)。`contributor/throttled?`は履歴が
`THROTTLE-RECENT`(既定5件)未満なら常にfalseを返す設計のため、空trajectoryは
「このauthorに関する既知の履歴なし」= 「throttleしない」に自然に解決する——
既存の呼び出し側(`contributor_trajectory`を知らないコード、
`cells/test_membrane_flow.cljc`の`run-flow`含む)は本ADR後も無変更で従来通り
動作する(non-breaking, purely additive)。

### 2. `rate-ok`(flood-limit、`now`が必要)は本ADRのスコープ外

`methods/contributor.cljc`のG9はrate-ok(sliding time window、`now`が必要)と
throttled?(履歴ベース、`now`不要)の2半分から成るが、本ADRは**throttled?のみ**
配線した。rate-okを配線するには「`now`をどこから供給するか」という別の設計判断
(wall-clockを注入するデーモン層が必要——`contributor.cljc`自身のdocstringが
「Time (`now`, `as-of`) is passed in — deterministic and testable, no
wall-clock」と明記し、pure関数自身はwall-clockを持たない)が必要で、本ADRの
「1つの明確な欠陥を閉じる」スコープを超えるため、意図的にfollow-upとして残した。

## Consequences

- (+) akeの実際のruntime path(propose cell)に、既に文書化済みだが未配線だった
  G9(の履歴ベース半分)が閉じた。
- (+) 5cellのcell-chain integration test(`test_membrane_flow.cljc`、CLAUDE.mdが
  「the runtime path」と呼ぶ唯一のend-to-endテスト)を含む既存127 test/478
  assertionが無変更(non-breaking)で通過することを確認——`contributor_trajectory`
  未指定時の安全なデフォルトが機能している証跡。
- (+) G9の実装(2つの新規test: throttled-author blocks / single-accepted-edit
  recovers)が、`methods/contributor.cljc`自身が謳う「recoverable, not punitive」
  という性質を実際に検証する。
- (−) rate-ok(flood limit)半分は未配線のまま(上記「スコープ外」参照) — follow-up。
- (−) `contributor_trajectory`の実際のデータソース(誰がこのmapを構築し
  `propose`呼び出し時に渡すか)はR0の設計のみで、live wiring(Council Lv6+ + operator
  gated, G8)は別途。

## Artifacts

- `20-actors/ake/cells/propose/state_machine.cljc`(`ake.methods.contributor`
  require追加 + G9 throttled?チェック追加 + docstring更新)
- `20-actors/ake/cells/test_state_machines.cljc`(2 tests追加: throttled-author
  blocks / recovered-by-one-accepted-edit allows)

動作確認: `bb`(canonical classpath、`require`経由)で
`ake.cells.test-state-machines` + `ake.cells.test-membrane-flow` 29 tests /
71 assertions green。広域回帰確認として ake の methods/cells 全10 namespace
127 tests / 478 assertions green(既存`methods/test_contributor.cljc`含め無退行)。
clj-kondo: 新規エラー・警告0件(pristine origin/mainの同一ファイルと比較——既存の
1 error(Unresolved symbol: clojure)・1 warning(未使用namespace)は変更前から存在し
変更なし)。

## References

- ADR-2606052100(ake community-edit membrane、G9文言の出典)
- ADR-2607141200(kuni-umi)・ADR-2607141600(yadori/watari)・ADR-2607141900
  (sanae)——同型の欠陥クラスの先例(いずれも既存primitiveの単純配線)
- `20-actors/ake/CLAUDE.md`(gate表 + 「3点セット」構造的invariant警告の出典)
- `20-actors/ake/methods/contributor.cljc`(G9エンジン本体、本ADRが配線した
  `throttled?`の実装)
