---
id: adr-2607141600-yadori-watari-documented-gate-implementation-gaps
title: "ADR-2607141600: yadori G6(IDN homograph)・watari G1(military craft) — 文書化済みゲートの実装ギャップを解消"
status: active
doc_type: adr
topic: yadori-watari-documented-gate-implementation-gaps
authoritative: true
last_verified: 2026-07-14
status_note: "etzhayyim root成熟度向上タスク(sole-member founder directive「etzhayyim root としての 成熟度を 向上」、ランク付け4項目のうち item 4「R0→R1 advancement via 同型の安全スコープ小規模修正」)の一環。kuni-umi jurisdiction-eligibility修正(ADR-2607141200)と同じ欠陥クラス——CLAUDE.md/actor CLAUDE.mdが既に明記するgate要件を、コードが実装していなかった箇所——をrepo横断でaudit(shomei/tedaiも監査したが該当なし)した結果、yadori/watariの2件で発見。"
priority: 6.0
axis: safety
weight: 0.45
priority_note: "S0スコープの小規模修正2件、いずれもactor自身のCLAUDE.mdが既に明記する制約の実装であって新しい制約の導入ではない。yadori: methods/availability.cljcの既存実装済みconfusable-fqdn?primitiveをreservation cellのG6ゲートに配線(kuni-umi修正と同型パターン——実装済みprimitiveの配線漏れ)。watari: CLAUDE.md G1が明記する「military / blocked-from-display aircraft」「naval vessels not openly broadcasting」forbidden-inputsに対する実際の screen が methods/ingest.cljcに存在しなかったので新規追加。"
authoritative_for:
  - "yadori reservation cell の G6(no-squatting)IDN-homograph screen 配線の正本"
  - "watari methods/ingest.cljc の G1(public-broadcast-only)military-craft screen の正本"
depends_on:
  - adr-2606038400-yadori-dns-availability-and-domain-acquisition-tier-b-actor-r0
  - adr-2606041827-watari-live-ship-aircraft-position-kotoba-native
related:
  - adr-2607141200-kuni-umi-site-survey-jurisdiction-governor
supersedes: []
superseded-by: []
---

# ADR-2607141600: yadori G6(IDN homograph)・watari G1(military craft) — 文書化済みゲートの実装ギャップを解消

**Status**: active
**Date**: 2026-07-14
**Scope**: `20-actors/yadori/cells/reservation/state_machine.cljc`(G6のconfusable-fqdn?配線のみ)
と `20-actors/watari/methods/ingest.cljc`(G1のmilitary-craft screenのみ)。両actorとも
他cell/method・robotics・live-fetch(G7)には一切触れない。

## Context

kuni-umi `jurisdiction-eligibility`(ADR-2607141200)で見つかった欠陥クラス——**actor自身の
CLAUDE.mdが既に明記するgate要件を、コードが実装していない**——が他actorにも存在しないか、
shomei/tedaiを含む複数actorを監査した。shomei/tedaiには該当なし(既存gateは実装済み)だった
一方、以下2件を発見した:

1. **yadori G6(no-squatting)**: `cells/reservation/state_machine.cljc`の
   `transition-to-screened`は`blocked-names`(held-trademark集合)・`speculative`・
   `charter_clean`はチェックしていたが、`methods/availability.cljc`が既に実装・テスト済みの
   `confusable-fqdn?`(IDN homograph screen)を一切呼んでいなかった。結果、Cyrillic
   "а" + Latin "pple" のようなconfusable SLDが、held-trademark listに文字列として
   一致しない限りG6を素通りしていた——kuni-umiと同じ「実装済みprimitiveの配線漏れ」。
2. **watari G1(public-broadcast-only)**: actor自身のCLAUDE.mdが"Forbidden inputs"として
   明記する「military / blocked-from-display aircraft (FAA LADD, PIA)」「naval vessels not
   openly broadcasting」に対応するscreenが`methods/ingest.cljc`の`vessel-fix`/`aircraft-fix`
   に一切存在せず、有効な位置情報を持つ限り軍用callsign(RCH/NAVY/ARMY等)・軍艦名
   (USS/HMS等)もそのまま正規化されていた。

## Decision

### 1. yadori: `transition-to-screened`に confusable screen を追加

```clojure
(when (availability/confusable-fqdn? (get cs "sld"))
  (throw (ex-info (str "G6 violation: '" (get cs "sld")
                       "' is an IDN homograph (mixes Unicode scripts) — fails the confusable screen")
                  {:gate "G6" :confusable-labels (availability/confusable-labels (get cs "sld"))})))
```

`blocked-names`チェックの直後、`speculative`チェックの前に追加。単一スクリプトの
アクセント付き名前(例: "café")は`confusable-fqdn?`がfalseを返すため素通りする
(過剰ブロックしない)。

### 2. watari: `vessel-fix`/`aircraft-fix`に military-craft screen を追加

```clojure
(def military-callsign-prefixes
  #{"RCH" "NAVY" "ARMY" "CNV" "SAM" "PAT" "COBRA" "VIPER" "TANKER"})
(def military-ship-name-prefixes
  #{"USS " "USNS " "HMS " "HMCS " "HMAS " "FGS " "FS " "ITS " "INS " "JS " "ROKS "})
```

`vessel-fix`は`military-ship-name?`が真なら`[nil nil]`を返す(craft/fix双方を捨てる)。
`aircraft-fix`の既存フィルタ条件に`military-callsign?`をORで追加。いずれも
:representative sourcingの範囲での文字列prefixマッチであり、AISStream/ADS-Bメッセージ
仕様上取得できるフィールド(callsign/ship name)だけを使う——`ShipType`のような
別メッセージ種別が必要なフィールドには依存しない。

## Consequences

- (+) 両actorとも、既に文書化済みだが未実装だったgate要件が閉じた。新しい制約の追加では
  なく実装ギャップの解消。
- (+) 民間トラフィックは無影響(既存fixture/testが変更後も green)。
- (+) kuni-umiに続き、「actor CLAUDE.mdのgate表 vs 実コード」の監査パターンが本ADRで
  3回目の独立再現(yadori/watari)——repo横断の体系的gapクラスである可能性を示唆
  (follow-up: 残る全actorの網羅監査は本ADRのスコープ外)。
- (−) military-callsign/ship-nameのprefix集合は代表的なものの縮小seed(G8)であり、
  網羅的な軍用機・軍艦の検知ではない(例えば民間チャーター化した退役軍艦や、
  prefixを持たない軍用機は素通りしうる)。より網羅的な screen は別途follow-up。
- (−) yadori/watariとも他のgate(G2-G5/G7-G9、watari G2-G8)には一切触れていない。

## Artifacts

- `20-actors/yadori/cells/reservation/state_machine.cljc`(`availability`require + G6
  confusable check 追加)
- `20-actors/yadori/cells/reservation/test_state_machine.cljc`(2 tests追加:
  homograph-blocks / single-script-allows)
- `20-actors/watari/methods/ingest.cljc`(military-callsign-prefixes/military-ship-name-prefixes
  + 2 predicate + `vessel-fix`/`aircraft-fix`への配線)
- `20-actors/watari/methods/test_ingest.cljc`(3 tests追加: military callsign drops /
  military ship name drops / civilian traffic still passes)

動作確認: `bb`(canonical classpath、`require`経由)で
`watari.methods.test-ingest` + `yadori.cells.reservation.test-state-machine`
21 tests / 90 assertions green。clj-kondo: 新規エラー0件(pristine origin/mainの
同一パスと比較——namespace/file-path不一致・Unresolved symbolの警告は変更前から
存在し変更なし)。

## References

- ADR-2606038400(yadori設計、G6 no-squatting定義の出典)
- ADR-2606041827(watari設計、G1 public-broadcast-only定義の出典)
- ADR-2607141200(kuni-umi jurisdiction-eligibility——同型の欠陥クラスの先例)
- `20-actors/yadori/CLAUDE.md` / `20-actors/watari/CLAUDE.md`(gate表の出典)
