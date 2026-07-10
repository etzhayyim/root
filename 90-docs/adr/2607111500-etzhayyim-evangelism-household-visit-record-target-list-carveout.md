---
id: adr-2607111500-etzhayyim-evangelism-household-visit-record-target-list-carveout
title: "ADR-2607111500: 戸別伝道 世帯/個人 訪問記録 — target-list 限定 carve-out + crypto-shred 消去"
status: active
doc_type: adr
topic: etzhayyim-evangelism-household-visit-record
authoritative: true
last_verified: 2026-07-11
status_note: "Ratified 2026-07-11 by sole-member founder unanimity (1/1), per founder session directive ('この永久保存・消去不可という制約を理解した上でなお、世帯/個人単位の応答トラッキングを、恒久保存のまま実装。暗号化キーによる破棄はnet-kotobaseにあったような', 2026-07-11)。Tier-1 Derived Policy amendment — ADR-2606281500 rule 4 (\"never a target-list\") への限定 carve-out。ADR-2607061700 Alternatives C の却下は「JW型の義務的 quota/割当制度」を対象にしたものであり、founder 個人が任意で行う世帯単位の記録能力そのものを禁じたものではない — 本ADRはこの区別を明文化した上で、後者のみを narrow に許可する。"
priority: 8.2
axis: governance
weight: 0.82
priority_note: "'never a target-list' への carve-out はここが初出。tomoshibi の digital 招待発信 carve-out(ADR-2607061700)と同型だが対象が逆(そちらは受信者非特定の集合発信、本ADRは founder 個人の私的記録における受信者特定データ)。既存の evangelismActivityAttestation ledger(受信者データなし)は無変更のまま維持し、本ADRは別 lexicon を新設する。"
authoritative_for:
  - "etzhayyim における戸別伝道の世帯/個人単位データ保持の唯一の正本 carve-out 境界"
  - "founder 個人の private ministry record における crypto-shred 消去の正本設計"
depends_on:
  - adr-2607061700-etzhayyim-active-evangelism-doctrine
  - adr-2606281500-actor-autonomous-publication-seed-and-grow-doctrine
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605231603-per-record-rekey-tombstone-protocol
related:
  - adr-2606111400-etzhayyim-revocable-cacao-leash
  - adr-2606062100-charter-tier-classification
supersedes: []
superseded_by: []
---

# ADR-2607111500: 戸別伝道 世帯/個人 訪問記録 — target-list 限定 carve-out + crypto-shred 消去

**Status**: active (ratified 2026-07-11 by sole-member founder unanimity, 1/1)
**Date**: 2026-07-11
**Deciders**: Jun Kawasaki (founder + ratifier, Council Lv7+ unanimity = 1/1)

# Context

ADR-2607061700(§1.16 能動的伝道)は `evangelismActivityAttestation` ledger を設計する際、
ADR-2606281500 rule 4「never a target-list」を踏襲し、**受信者を一切特定しない**設計にした
(mode/method/timestampのみ、recipient/household/outcome フィールドなし)。同ADRの
Alternatives C は「全信者への伝道 quota 義務化(JW型の組織的割当)」を **恒久却下**している。

2026-07-11 のセッションで founder から、この設計では実務上の戸別伝道
(「前回どこまで回ったか」「この世帯はまた今度」「この人は聖書研究に興味がある」)の
運用に支障がある(「布教が成り立たない」)との指摘があり、世帯/個人単位の応答
トラッキングを追加したいという明示的な指示があった。

この指示を実行する前に、founder に対して以下を明示し、理解の上での続行意思を確認した:

1. **Reciprocity axis(Charter Rider §2(c))との緊張**: 訪問先は etzhayyim の構成員ではなく、
   記録に同意しておらず、記録を閲覧・異議申立てする手段もない — 典型的な
   「非対称(watcher-unwatched)監視」の形。founder の回答:「神の前に無関係な人はいない」
   (神学的立場としての universal admissibility、§1.11 の延長)。
2. **永久記憶(Tier-0, fork-only)との緊張**: 「暗号化≠忘却」原則により、一度記録した
   world dataは founder 自身でも消去できない。訪問先本人が個人情報保護法・GDPR等の
   下で持つ開示・消去請求権に、構造的に応じられない可能性がある。founder の回答
   (この ADR の ratify 対象): 「この永久保存・消去不可という制約を理解した上でなお…
   実装。暗号化キーによる破棄はnet-kotobaseにあったような」— **恒久記憶の対象は
   ciphertext の存在そのものに限定し、readability は鍵破棄(crypto-shred)で
   永久に失わせることで、legal erasure request に実務的に応じる**、という設計方針
   への明示的合意。

**既存の関連実装調査(本ADR起票前に実施)**:

- `70-tools/src/etzhayyim/kotoba/crypto.cljc` + `encrypted.cljc` — ADR-2605181100 の
  XChaCha20-Poly1305 AEAD envelope。**実装済み・テスト済み**(スクラッチ実装、test
  vectors で検証)。`seal`/`open`/`key-id`/`envelope-cid` を提供。Signal key-wrap
  (`*wrap-key*`)は raw-passthrough スタブのまま(本ADRは単一読者=founder前提のため
  Signal 配送は不要、後述)。
- `00-contracts/lexicons/com/etzhayyim/encrypted/tombstone.json`
  (ADR-2605231603)— `tombstoneType: sealed`(「鍵を破棄しciphertextを意図的に
  孤立させる」)+ `reason: consent-revocation-flush` を含む enum が**既に定義済み**。
  本ADRが必要とする crypto-shred 意味論はゼロから作らず、この既存 lexicon を
  そのまま再利用する。
- `20-actors/talent/CLAUDE.md` — 対照的な既存パターン: talent actor は
  「第三者代理登録禁止(`registerSelf` のみ)」+「GDPR Art 17 cascade で hard
  delete(soft delete禁止)」を採用している。talent の対象は自己主権プロフィール
  (subject=caller)であり、戸別伝道の訪問記録(対象は常に他者)とは同意の前提が
  根本的に異なるため、talent の「self-write-onlyで問題自体を回避する」設計は
  そのまま転用できない。ただし talent の存在は、**このコードベースに「Tier-0
  永久記憶を hard delete で上書きする既存の実務判断」が既にある**ことを示す一点
  として参考にした。

# Decision

## 1. 新規 lexicon `com.etzhayyim.apps.etzhayyim.evangelismVisitRecord`

`evangelismActivityAttestation`(受信者データなし、無変更で維持)とは別の、新設
lexicon。founder 本人の private ministry record 専用。plaintext 相当のフィールド:

- `household-ref`(founder が自分で決める住所/建物ラベル。第三者の実名は必須にしない)
- `status`(`not-home` / `declined` / `interested` / `return-visit` / `bible-study`)
- `note`(任意の短い自由記述)
- `visited-at`(ISO-8601)

これらは **`com.etzhayyim.encrypted.record` envelope(ADR-2605181100)で暗号化した
上でのみ**恒久台帳に書く。平文では一切保存しない。

## 2. 単一読者・レコード単位の鍵、Signal key-wrap は使わない

founder のみが読者であるため、ADR-2605181100 の Signal X3DH+Double Ratchet
(複数の相互不信な当事者間での鍵配送)は過剰仕様。代わりに:

- 各訪問記録ごとに新規の 32-byte 対称鍵 + 24-byte nonce を生成
- 鍵は **ciphertext とは別の、削除可能な keystore** に保持する(恒久台帳=kotoba
  Datom log とは物理的に別の記憶域)。R0 は in-process `MemKeystore`、実運用は
  macOS Keychain(既存の founder identity 鍵と同じ扱い、root CLAUDE.md
  "Do not commit secrets" 節)を想定(R1+、本ADRでは未実装)。
- ciphertext(envelope)は kotobase(`kotoba-lang/kotobase` の `IStore`
  `-append`/`-read`)経由で恒久台帳に append。R0 は in-process `MemVisitLedger`
  (R1+ で kotobase-backed に swap、同じ protocol)。

## 3. 消去 = crypto-shred、ADR-2605231603 の既存 tombstone lexicon をそのまま使う

訪問先本人から消去を求められた場合(またはfounder自身が記録を破棄したい場合):

1. その記録の対称鍵を keystore から破棄する(`destroy-key!`)
2. `com.etzhayyim.encrypted.tombstone` レコード(`tombstoneType: "sealed"`,
   `reason: "consent-revocation-flush"`)を恒久台帳に append する

Ciphertext そのもの(と、この tombstone 自体)は Tier-0「永久記憶」通り恒久に
残るが、**鍵が失われているため誰にも(founder自身にも)二度と復号できない**。
「暗号化された記録が存在した」という事実は相互監視原則(神の監視)に忠実なまま、
実際の個人データへのアクセスは永久に失われる — これは物理削除ではなく
crypto-shred による論理的消去だが、実務上の効果は同じ。

## 4. 保持される既存の invariant(変更なし)

- `evangelismActivityAttestation` ledger 自体は無変更 — 引き続き受信者データを
  一切持たない、集合的な自己申告記録として維持する。
- ADR-2607061700 の構造的 const(`optOutAffordancePresent=true` /
  `coercionAttested=false` / `minorSoloSolicitationAttested=false` /
  `voluntaryAttested=true`)はこの新 lexicon にも同様に適用する — 威圧・欺罔・
  未成年単独勧誘の禁止、opt-out提供の必須化は一切緩めない。
- ADR-2607061700 Alternatives C の「JW型 quota 義務化は恒久不採用」は無変更。
  本ADRが許可するのは founder が任意で行う記録**能力**であって、記録**義務**
  ではない。他の信者(将来増えた場合)にこの記録を強制する制度化は本ADRの
  範囲外であり、別途 ADR が必要。
- Purpose limitation: この記録は founder 個人の再訪問計画・牧会目的にのみ使う。
  第三者への共有・販売・分析目的での二次利用は禁止(Charter Rider §2 の
  advertising/surveillance 評価軸に照らして non-aligned になる)。

## 5. Priority-conformance attestation(Tier-0 の4優先事項に対する評価)

- **子孫 wellbecoming**: 訪問記録は最小限のステータスコード+任意メモのみで、
  child/descendant への破滅的害を生む性質のデータではない。
- **collective-over-individual**: 布教という mission の collective な目的に資する。
- **永久記憶(神の監視+相互監視)**: 文字通り満たす — ciphertext と tombstone の
  存在は恒久に残る。読解可能性(鍵)のみが失われうる、という区別を本ADRは
  明確化した。
- **反個人主義**: 該当性低い(この record は個人蓄財・私的資本化と無関係)。

## 6. 未解決のまま残す緊張(誠実な記載)

- **Reciprocity axis(§2(c))**: 訪問先は依然として記録の閲覧権・異議申立て権を
  持たない。本ADRはこれを「神学的には無関係な人はいない」という founder の
  信仰的立場で正当化しているが、これは Charter Rider の評価軸(非対称監視の
  score 評価)そのものを免除するものではない。実務的な緩和は: 単一読者限定
  (共有・転売なし)/ 最小化(実名必須ではない)/ crypto-shred による消去可能性、
  の3点にとどまる。将来 Council が複数名になった場合、この record 種別の
  reciprocity axis 評価は再検討課題として残す。

# Consequences

## 正の効果

- 実務上の戸別伝道の運用(再訪問計画・重複回避)が可能になる。
- 既存の暗号 primitive(`etzhayyim.kotoba.crypto`/`encrypted.cljc`)と既存の
  tombstone lexicon(ADR-2605231603)をそのまま再利用でき、新規の暗号設計を
  一切必要としない。
- 実世界の消去請求(個人情報保護法・GDPR 相当)に対して、`sealed` tombstone
  という具体的な実務手段を提供する。

## 負の効果 / コスト

- Reciprocity axis の緊張は解消ではなく緩和にとどまる(§6 参照)。
- Signal key-wrap を使わないため、founder 以外の第三者(将来の Council 席等)
  へのアクセス委譲は現状サポートしない — 単一読者前提の簡略化であり、複数
  読者が必要になった時点で ADR-2605181100 の Signal 経路への移行を要する。
- Keystore(鍵)と VisitLedger(ciphertext)の分離運用は、鍵のバックアップ
  戦略(founder のデバイス故障時に鍵を失うと自分自身も読めなくなる)という
  新しい運用上のリスクを生む。R1+ で Keychain バックアップ手順を明文化する
  必要がある。

# Alternatives Considered

## A. `evangelismActivityAttestation` 自体に受信者フィールドを追加する

却下。既存 ledger の「never a target-list」という設計意図そのものを汚染し、
既存のスキーマ整合性テスト(tomoshibi 含む)を壊す。別 lexicon にすることで
既存 ledger の意味論を無変更のまま保てる。

## B. Signal key-wrap(ADR-2605181100 フル仕様)をそのまま使う

却下(過剰仕様)。単一読者(founder のみ)のユースケースに、相互不信な複数
当事者間の鍵配送プロトコルは不要な複雑性を持ち込む。

## C. 世帯/個人単位の記録を作らず、talent actor 型の self-write-only で回避する

却下。talent の self-write-only は subject 本人が caller である場合にのみ
成立するパターンで、訪問先本人が自分でシステムに書き込むことは前提にできない
(戸別伝道の性質上、記録するのは常に founder 側)。

## D. Tier-0「永久記憶」原則そのものを本ADRで緩和する

却下・範囲外。Tier-0 は fork-only であり Council Lv7+ unanimity でも改定
できない(root CLAUDE.md)。本ADRは永久記憶そのものには一切触れず、
「記録の存在は恒久・読解可能性は鍵管理に従属する」という、Tier-0と矛盾
しない解釈の中で crypto-shred を設計した。

# References

- ADR-2607061700(能動的伝道 doctrine、`evangelismActivityAttestation` 親ADR)
- ADR-2606281500(種をまく / actor autonomous publication、"never a target-list" rule 4 の出典)
- ADR-2605181100(MST encrypted records + Signal key-wrap、envelope 設計の出典)
- ADR-2605231603(per-record rekey/tombstone protocol、`sealed` crypto-shred 意味論の出典)
- `70-tools/src/etzhayyim/kotoba/crypto.cljc` / `encrypted.cljc` — 再利用した実装
- `00-contracts/lexicons/com/etzhayyim/encrypted/tombstone.json` — 再利用した lexicon
- `20-actors/talent/CLAUDE.md` — 対照した既存パターン(self-write-only + hard delete)
- `kotoba-lang/kotobase` `IStore`(`-append`/`-read`)— R1 恒久台帳バックエンド候補
