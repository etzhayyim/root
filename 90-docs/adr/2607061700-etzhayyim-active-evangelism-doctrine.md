---
id: adr-2607061700-etzhayyim-active-evangelism-doctrine
title: "ADR-2607061700: 伝道 (Active Evangelism Doctrine) — Mission Charter §1.16 追加"
status: active
doc_type: adr
topic: etzhayyim-active-evangelism
authoritative: true
last_verified: 2026-07-06
status_note: "Ratified 2026-07-06 by sole-member founder unanimity (1/1), per founder session directive ('伝道, 能動的な活動は入れてください', 2026-07-06)。Tier-1 Derived Policy — ADR-2605192100 Mission Charter に §1.16 を追加する派生 ADR。既存の Tier-0 priority (子・孫 wellbecoming / 反個人主義 / 永久記憶) はいずれも変更しない。"
priority: 8.5
axis: governance
weight: 0.85
priority_note: "Mission Charter §1 系列への新規セクション追加。ADR-2606281500 (種をまく) の no-person-targeting ガードに、伝道という宗教的 speech-act に限った carve-out を与える唯一の派生元。"
implementation:
  repo: etzhayyim/root
  path: 20-actors/etzhayyim-organism/src/etzhayyim_organism/sensors/evangelism_gate.cljc
  landed_via: "cljc-native shared sensor module (no Python counterpart — owner directive 2026-07-06) implementing §1.16(a)-(d): individual-vulnerability targeting / coercion / minor-solo solicitation / no-opt-out-affordance. Composes with (does not duplicate) charter_rider.scan (charter-rider.cljc) for §2(c)/(f)/(h) engagement-maximizing categories. Closes Open Question 2. Tests: sensors/test_sensors.cljc (10 cases appended) — 31 bb clojure.test (61 assertions), all green."
authoritative_for:
  - "etzhayyim の能動的伝道 doctrine 正本 (信者の対人伝道 + actor のデジタル伝道)"
  - "Mission Charter (ADR-2605192100) §1.16 の正本テキスト"
  - "ADR-2606281500 (種をまく) の no-person-targeting ガードに対する伝道 carve-out の境界定義"
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605252300-etzhayyim-charter-preamble-kingdom-of-god-on-blockchain
  - adr-2605172600-etzhayyim-membership-ritual
  - adr-2606281500-actor-autonomous-publication-seed-and-grow-doctrine
related:
  - adr-2606182359-charter-amendment-wave3-all-prohibitions-to-objective-function
  - adr-2606111400-etzhayyim-revocable-cacao-leash
  - adr-2606072802-no-server-key-clarification-read-only-exempt
supersedes: []
superseded_by: []
---

# ADR-2607061700: 伝道 (Active Evangelism Doctrine) — Mission Charter §1.16 追加

**Status**: active (ratified 2026-07-06 by sole-member founder unanimity, 1/1)
**Date**: 2026-07-06
**Deciders**: Jun Kawasaki (author + ratifier). The association currently has ONE member, so
the Charter's Council Lv7+ unanimity threshold = this one member's assent (1/1).

# Context

ADR-2605192100 (Mission Charter) §1.11 は「加入の無差別開放性 (universal admissibility)」を定める
— 門は全人類に開かれているが、これは **受動的開放** であって、構成員や actor に対して
「能動的に他者へ伝える」ことを求めるものではなかった。実際、直近の分析セッション (2026-07-06) で
確認した通り、既存 charter 中で「伝道」に最も近い規定である ADR-2606281500 (種をまく / actor
autonomous publication) は、むしろ **明示的に対人ターゲティングと説得を禁止** している:

> 「No person-targeting / no manipulation... A post is speech, never a target-list or a
> persuasion lever」

Founder 指示 (2026-07-06, セッション内):

> 「伝道, 能動的な活動は入れてください」

これを受け、以下の設計判断を founder に確認した:

1. **主体**: 信者(人間)の対人伝道 **と** actor のデジタル伝道の **両方**
2. **手段**: 対人 (面談・戸別訪問を含む) **と** デジタル (SNS・公開発信・招待コンテンツ) の **両方を並記**

これらを Mission Charter に **§1.16 伝道 (Evangelism)** として追加する。

## Religious 根拠の所在

etzhayyim は既に Protestant Christianity を synthetic religion の一系統として採用しており
(§1.14)、その正典 Tier-1 に「福音書」を含む (§1.15)。大宣教命令 (Great Commission,
Matthew 28:19-20 「あなたがたは行って、すべての国の人々を弟子としなさい」) は **既存の正典内
にある教義の実践的展開** であり、新たな正典を持ち込むものではない。仏教の 布教 (弘法。縁起により
他者の解放が自己の解放に連なる) / 神道の 産霊 (新しい関係を能動的に生成する creative act) とも
整合的であり、§1.14 の日本的価値観 + Protestant Christianity の synthesis 路線から自然に導出される。

これは §1.15 (非終末論) と矛盾しない: 伝道の動機は「終末が近いから急げ」という終末論的切迫感
ではなく、「今ここにある Kingdom (Wellbecoming の軌跡, Preamble §0.2.1) への招待」である。

# Decision

## 1. Mission Charter (ADR-2605192100) §1 に新規セクション §1.16 を追加

> 完全なテキストは ADR-2605192100 本文 §1.16 に正本として inline する (本 ADR は起票根拠 +
> Constitutional Constants + carve-out 境界を定める)。

要旨:

### 1.16 伝道 (Evangelism) — 能動的宣教活動

etzhayyim は §1.11 (加入の無差別開放性) の **受動的開放** を超え、**能動的に mission を人類へ
伝えること** を religious 行為として位置づける。

#### 主体別の実践形態

| 主体 | 実践形態 | 強制力 |
|---|---|---|
| 信者 (Adherent, 人間) | 対人伝道 (面談・戸別訪問・街頭・オンライン対話を含む) | 宗教的実践・徳目 (修 shu の一形態) として明記。義務ではなく実践として推奨・記録される — 任意団体・現構成員1名という現状の運用制約による (下記 Alternatives C 参照) |
| Actor (AI, digital) | kouhou / kataribe / kouhou 系等からの能動的・集合的な招待発信 | ADR-2606281500 の "no person-targeting" を伝道文脈で限定 carve-out (下記 §2) |

#### 対人伝道の許容範囲・制約

- 日本国内で宗教目的の戸別訪問は適法 (公職選挙法 §138 は選挙運動に限定される規制であり、政教は
  無関係。既存 charter 中の「戸別訪問」言及は moushibumi actor の選挙運動禁止条項であり、本条項とは
  別事項)
- 訪問先の明示的な退去要求には即座に従う (不退去罪の回避 + Wellbecoming §1.10 の対人尊重)
- 未成年者・判断能力が制限されている者への単独勧誘は禁止 (§1.9 多世代保護)
- 威圧・欺罔・financial pressure を伴う勧誘は禁止 (Charter Rider §2 の反 coercion / 反 catastrophe と整合)

#### Actor 側 carve-out (ADR-2606281500 の限定修正)

ADR-2606281500 決定事項 4「No person-targeting / no manipulation」は、以下の条件を **すべて**
満たす **招待型コンテンツ (invitational content)** についてのみ carve-out する (削除ではなく
限定範囲の例外):

- 対象は集合的・公開的な発信であり、個人の脆弱性 (財政困窮・精神的孤立・未成年等) を検知・
  標的化するものではない (aggregate-first は不変)
- 常時 opt-out 可能。執拗な繰り返し勧誘 (unsolicited follow-up の反復) は禁止
- Wellbecoming §1.10 の addictive-design 禁止は不変 — engagement-maximizing loop は
  伝道コンテンツにも一切許容されない
- Charter Rider §2 catastrophe-veto content scan (`charter_rider.scan`) は伝道コンテンツにも
  適用される (不変)
- ADR-2606281500 の他の全ガード (non-custodial key / reciprocal transparency / 相互監視 /
  publication ≠ actuation) は無変更

## 2. Constitutional Constants (ADR-2605192100 §2) への追加

| Key | Value | 由来 |
|---|---|---|
| `mission.active_evangelism` | true | 本 ADR §1.16 |
| `mission.evangelism_coercion_prohibited` | true | 本 ADR §1.16 (威圧・欺罔禁止) |
| `mission.evangelism_minor_solo_prohibited` | true | 本 ADR §1.16 (§1.9 多世代保護) |
| `mission.evangelism_actor_targeting_carveout` | true | 本 ADR §1.16 (ADR-2606281500 の限定 carve-out) |

Tier 分類: **Tier-1 Derived Policy** (ADR-2606062100 の3層モデルに従う。Council Lv7+ unanimity +
priority-conformance attestation で改定可。Tier-0 priority (子・孫 wellbecoming / 反個人主義 /
永久記憶) はいずれも不変のまま)。

## 3. Mission Charter §4 (宣明文, 正本文言) への追記

Mission Charter §4 の宣明文 (Constitution.sol embedding 用の正本テキスト) に、Eros/Gore
paragraph の後・非終末論 paragraph の前に、以下を追加する:

> 我々は **能動的伝道 (Evangelism)** を宗教的実践として肯定する。信者は対人伝道 (面談・戸別訪問・
> 街頭・オンライン対話を含む) を徳目として実践してよく、actor は集合的・公開的な招待発信を行って
> よい。ただし威圧・欺罔・未成年者への単独勧誘・engagement-maximizing な操作は禁止し、Charter
> Rider §2 の catastrophe-veto scan と Wellbecoming (§1.10) の対人尊重を常に伴う。

## 4. ADR-2606281500 への forward-pointer

ADR-2606281500 の Consequences に、本 ADR による carve-out の存在を明記する一文を追加する
(該当 ADR 自体の既存ガードは削除・弱体化しない)。

# Consequences

## 正の効果

- **etzhayyim の「開放だが受動的」という非対称が解消**され、mission を能動的に人類へ伝える
  religious 実践が charter 上に明記される。
- **Protestant 大宣教命令という既存正典 (§1.15 Tier-1) からの自然な導出** であり、新規の教義的
  逸脱を伴わない。
- **actor 側の carve-out は限定的**であり、ADR-2606281500 の中核ガード (non-custodial key /
  reciprocal transparency / anti-manipulation / catastrophe-veto) はすべて保持される — 伝道の
  ために安全策を犠牲にしない設計。

## 負の効果 / コスト

- **対人伝道 (特に戸別訪問) は社会的摩擦・誤解のリスクを伴う**。訪問先の明示的拒絶への即時遵守を
  constitutional に明記することで緩和するが、完全な防御ではない。
- **「義務」ではなく「徳目・推奨」に留めた**ため、JW のような組織的な伝道割当制度 (時間記録・
  quota) は本 ADR の対象外。構成員が増えた場合、義務化の当否は改めて Council で審議が必要
  (Open Questions 参照)。
- **actor carve-out の運用境界は依然として灰色領域を含む** (「集合的発信」と「個人ターゲティング」
  の境界の実装判定)。運用は Council Lv6+ の evaluate に委ねる (Mission Charter §1.13 の
  境界事例判定と同型)。

## 中立 / トレードオフ

- 「伝道」と「布教資金の勧誘 (寄付強要)」の境界。本 ADR は伝道を **信仰の伝達** に限定し、
  金銭的勧誘は Non-profit / donation-only 原則 (ADR-2605192115) の別途規律に従う。伝道活動
  そのものを収益化・KPI 化することは Wellbecoming §1.10 違反として扱う。

# Alternatives Considered

## A. 伝道を doctrine 化しない (status quo)

- Pro: 法的・社会的露出が最小。
- Con: founder 指示に反する。既存の「開放だが伝えない」非対称が残る。
- 却下。

## B. actor 側の carve-out のみとし、人間信者には求めない

- Pro: 運用負荷が小さい (現構成員1名)。
- Con: founder が明示的に「両方」を求めている。宗教的実践としての対人伝道 (JW型の徳目) を
  排除する理由がない。
- 却下 (founder 選択により両方を採用)。

## C. 全信者への伝道 quota 義務化 (JW 型の組織的割当)

- Pro: 伝道活動の定量化・記録が可能。
- Con: **現在の association は構成員1名**であり、quota 制度を設計する実務的意味が薄い。
  任意団体としての信教の自由 (§1.8 の個人主義批判とは別に、実践の強制は §1.9 多世代保護・
  Wellbecoming の「強制されない発展軌跡」という精神とも緊張しうる)。
- 部分採用: 「義務ではなく徳目・推奨」として §1.16 に明記し、quota 化は構成員規模拡大時の
  future ADR (`etzhayyim-evangelism-quota-governance`) に委ねる (Open Questions 参照)。

## D. 対人伝道 (戸別訪問等) を明示的に除外し、digital のみ採用

- Pro: 訪問先とのトラブルリスクを完全に回避。
- Con: founder が「両方を並記」を明示的に選択している。JW 型の対人伝道という比較対象を
  意図的に含める founder 意図に反する。
- 却下。

# Open Questions

1. **伝道 quota 義務化の閾値**: 構成員数が一定規模を超えた場合、Council がどの基準で
   義務化を審議するか (future ADR)。
2. ~~**actor carve-out の「集合的発信 vs 個人ターゲティング」の実装判定基準**~~ —
   **RESOLVED 2026-07-06**: `etzhayyim_organism.sensors.evangelism_gate.cljc`
   (cljc-native, no Python counterpart — owner directive)。§1.16(a)-(d): 個人脆弱性
   ターゲティング / coercion / 未成年単独勧誘 / opt-out 欠如。charter_rider.scan
   (charter-rider.cljc) と composition(重複させず delegate)。31 bb clojure.test
   (61 assertions) green。個別 actor(kouhou/kataribe 等)への wiring 自体は各 actor 側の
   future work として残る — 本 ADR が閉じるのは「判定基準そのもの」(共有 sensor モジュール)
   の実装まで。
3. **対人伝道の記録媒体**: MEMBERS.md 型の dual-permanent record に伝道活動ログを追記するか、
   別途 append-only ledger を設けるか。
4. **各 actor(kouhou/kataribe 等)への evangelism_gate 実際の wiring**: どの actor が
   最初に招待型コンテンツを発信するか、その governor にどう `evangelism_gate.gate` を
   呼び出させるか (未着手 — actor 側 future work)。

# References

- `20-actors/etzhayyim-organism/src/etzhayyim_organism/sensors/evangelism_gate.cljc` —
  §1.16(a)-(d) 判定基準の共有 sensor モジュール実装(cljc-native, Open Question 2 の解)
- ADR-2605192100: etzhayyim Mission Charter (本 ADR が §1.16 として追加する親 ADR)
- ADR-2605252300: Charter Preamble — Kingdom of God on Blockchain (§0.2.1 now-and-here との整合)
- ADR-2605172600: Membership ritual (信者 / Adherent の定義)
- ADR-2606281500: Actor autonomous publication (種をまく) — 本 ADR が limited carve-out を与える対象
- ADR-2606111400: Revocable member CACAO leash (actor 発信の off-switch, 不変)
- ADR-2606072802: no-server-key clarification (read-only exempt / 自律 write の位置づけ)
- ADR-2605192115: Non-profit, donation-only, no-ads (伝道と金銭勧誘の境界)
- Matthew 28:19-20 (Great Commission — Tier-1 正典内、福音書)
- Luke 17:21 / Matthew 6:10 (Preamble §0.2.1 now-and-here Kingdom)
