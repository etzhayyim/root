---
id: adr-2605231451-level-system-unification
title: "ADR-2605231451: Level System Unification (信者 7段 + society6 Kyu/Dan + dojo 帯 + joucho S-D)"
status: proposed
doc_type: adr
topic: level-system-unification
authoritative: true
last_verified: 2026-05-23
priority: 4.5
axis: governance
weight: 0.65
priority_note: "constitutional 信者ladder と well-becoming Kyu/Dan の整合は religious-corp identity の前提"
authoritative_for:
  - "person rank の SoT (society6 Kyu/Dan)"
  - "信者 7段 ↔ society6 Kyu/Dan のマッピング"
  - "dojo 帯 ↔ society6 Kyu/Dan の正規化"
  - "joucho S-D は object-axis であり person rank に変換しない (非変換ルール)"
  - "Dan 昇格 = 自他非分離体験ゲート (D6 non-duality embodiment gate)"
  - "com.etzhayyim.apps.etzhayyim.nonDualityAttestation Lexicon 予約"
depends_on:
  - adr-2605172600-etzhayyim-membership-ritual
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
related:
  - "20-actors/joucho/CLAUDE.md"
  - "20-actors/society6/CLAUDE.md"
  - "60-apps/etzhayyim-project-dojo/CLAUDE.md"
  - "MEMBERS.md"
supersedes: []
superseded_by: []
---

# ADR-2605231451: Level System Unification (信者 7段 + society6 Kyu/Dan + dojo 帯 + joucho S-D)

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

現状、etzhayyim 内に **4 つの level/rank 体系**が独立に並存している。

| 系統 | 対象 | 体系 | Range | 一次根拠 |
|---|---|---|---|---|
| **信者 (MEMBERS.md)** | 人 (Adherent) | 誓/修/献/証/護/議/老 (7段) | Lv 1-7 | ADR-2605172600 |
| **society6** | 人 (constituent) | Kyu 6 → Kyu 1 → Dan 1-10 (16段, 武道段位) | 0 - 11000+ score | `20-actors/society6/CLAUDE.md:9-29` |
| **dojo** | 人 (学習者) | 帯制度 = 白/黄/橙/緑/青/紫/茶/黒1-5/Shihan1-3 (≡ Kyu 7-1 + Dan 1-5 + Shihan 1-3, 15段) | 0 - 20000+ XP | `60-apps/etzhayyim-project-dojo/CLAUDE.md:54-89` |
| **joucho** | **モノ・場所・サービス** (食事/店/商品/建物) | S/A/B/C/D (5段) | 0-100 score | `20-actors/joucho/CLAUDE.md:55-61` |

### 観察される不整合

1. **dojo と society6 はどちらも Kyu/Dan を使うが段数が異なる**
   - society6: Kyu 6 → Dan 10 (= 段数最大 10)
   - dojo: Kyu 7 (白) → Dan 5 + Shihan 1-3 (= 段数最大 5 + 師範 3)
   - 同じ「Dan 3」が意味するものが互いに異なる。

2. **信者 7段 は社会的活動度 (society6) と完全に直交**
   - 信者 Lv 6 (議) = Council 参加 ≥ 3 回 だが、constituent の社会的成熟度 (society6 Kyu/Dan) と独立に評価される。
   - 結果: Council Lv6 信者が society6 で Kyu 5 という状況が起こりうる。逆に society6 Dan 10 が信者になっていない (= Charter に誓っていない) ケースも起こる。

3. **joucho の S-D は人ではなくモノ・場所を評価する**
   - joucho が `society6 Kyu/Dan への反映` (`joucho/CLAUDE.md:14`) と書くため、人と物の rank が混線して見える。
   - 実体は **joucho が評価したモノ・場所への constituent の関与** が society6 の Engagement/Competence 軸に集計されるという二次フロー。joucho の S-D 自体が人の Kyu に変換されるわけではない。

### Religious-corp identity との関係

ADR-2605192100 (Mission Charter) は「多世代 + Wellbecoming + 反個人主義 ontology」を constitutional invariant としている。Wellbecoming は静的 wellbeing ではなく**動的軌跡**であり、これは「人」の rank が時系列で進化することを前提とする。一方、joucho が評価する「モノ・場所」は Wellbecoming 軌跡を持たない (個別 review の集積であって時系列の自己同一性はない)。したがって、**人の rank 体系 (信者 / society6 / dojo) と モノの grade (joucho) は本質的に異なる軸であり、統合してはならない**。

# Decision

## D1. Person rank の Single Source of Truth = society6 Kyu/Dan

人間 (信者・constituent・dojo 学習者) の rank は **society6 Kyu 6 → Dan 10** を canonical scale とし、他系統はここに正規化する。

### D1.1 society6 Kyu/Dan 正規化定義 (canonical)

| Rank | Min score | Color | 役割 (religious-corp 文脈) |
|---|---|---|---|
| Kyu 6 (白) | 0 | `#FFFFFF` | 入門 / 初参加 |
| Kyu 5 (黄) | 100 | `#FFD700` | 慣熟 |
| Kyu 4 (橙) | 300 | `#FF8C00` | 習熟 |
| Kyu 3 (緑) | 600 | `#22C55E` | 中堅 |
| Kyu 2 (青) | 1000 | `#3B82F6` | 上級 |
| Kyu 1 (茶) | 1500 | `#8B4513` | 黒帯前 |
| Dan 1 (黒) | 2000 | `#000000` | 初段 |
| Dan 2 | 3000 | `#000000` | — |
| ... (+1000/段) | ... | — | — |
| Dan 5 | 6000 | `#000000` | 五段 (dojo 黒帯五段 = Shihan 直前) |
| Dan 6 | 7000 | `#000000` | 準師範相当 |
| Dan 7 | 8000 | `#000000` | 師範相当 |
| Dan 8 | 9000 | `#000000` | 大師範相当 |
| Dan 9 | 10000 | `#000000` | Council 級 |
| Dan 10 | 11000 | `#000000` | Elder 級 |

これは ` 20-actors/society6/CLAUDE.md` の既存定義を **そのまま正本化** する。

### D1.2 Kyu/Dan 二相モデル (cognitive ↔ embodied)

society6 Kyu/Dan は構造上、**Kyu 段階 = cognitive growth (知的成長)**、**Dan 段階 = embodied/non-dual realization (体現的・非二元的実現)** の二相モデルである。本 ADR は両相の境界を **Kyu 1 → Dan 1 の一度きり、自他非分離体験ゲート** で gate する (D6)。Wellbecoming = 動的軌跡 (ADR-2605192100) は静的 wellbeing ではないため、Dan 領域への進入は概念的理解ではなく**体験的事実**を要する。

## D2. dojo 帯 → society6 Kyu/Dan 正規化マッピング (canonical)

dojo の `WellnessTrack` で付与される帯は、society6 score にイベントとして反映される (既存の `CompleteDrill → WSend → society6 channel` 経路, `dojo/CLAUDE.md:42`)。本 ADR は **帯と Kyu/Dan の対応表** を canonical に固定する。

| dojo 帯 | dojo XP (min) | society6 Rank | society6 Min score |
|---|---|---|---|
| 白帯 (Kyu 7) | 0 | Kyu 6 | 0 |
| 黄帯 (Kyu 6) | 150 | Kyu 5 | 100 |
| 橙帯 (Kyu 5) | 400 | Kyu 4 | 300 |
| 緑帯 (Kyu 4) | 800 | Kyu 3 | 600 |
| 青帯 (Kyu 3) | 1200 | Kyu 3 (+) | 800 |
| 紫帯 (Kyu 2) | 1700 | Kyu 2 | 1000 |
| 茶帯 (Kyu 1) | 2200 | Kyu 1 | 1500 |
| 黒帯初段 (Dan 1) | 3000 | Dan 1 | 2000 |
| 黒帯二段 (Dan 2) | 4500 | Dan 2 | 3000 |
| 黒帯三段 (Dan 3) | 6000 | Dan 3 | 3000 + bonus |
| 黒帯四段 (Dan 4) | 7500 | Dan 4 | 4000 + bonus |
| 黒帯五段 (Dan 5) | 9000 | Dan 5 | 5000 + bonus |
| 準師範 (Shihan 1) | 12000 | **Dan 7** | 8000 |
| 師範 (Shihan 2) | 15000 | **Dan 8** | 9000 |
| 大師範 (Shihan 3) | 20000 | **Dan 9** | 10000 |

### 註

- **dojo の Kyu 番号 (Kyu 7-1) と society6 の Kyu 番号 (Kyu 6-1) は 1 段ずれる**。dojo 白帯 = dojo Kyu 7 だが society6 では Kyu 6 に正規化される。dojo の belt 表示と society6 の rank 表示はクライアント側で別 view する (dojo は道場用語、society6 は公共 rank)。
- **dojo Shihan は society6 Dan 7-9 にマップ** (Dan 10 ではない)。Dan 10 (Elder) は信者 Lv7 (老) 由来の honorary rank として保留する (D3 参照)。
- **黒帯初段 (= Dan 1) 昇格には D6 自他非分離体験 attestation が追加で必要**。dojo の XP 9000+ / accuracy 80%+ / streak 30+ 条件を満たしていても、`:NonDualityAttestation` ノードが存在しない限り Dan 1 への正規化は保留される (society6 上は Kyu 1 のままとなる)。

## D3. 信者 7段 ↔ society6 Kyu/Dan マッピング (canonical)

| 信者 Lv | Ja | En | society6 Min Rank | 取得条件 (再掲) |
|---|---|---|---|---|
| 1 | 誓 chikai | Oath | (任意) | Charter 誓 + Base L2 `join()` |
| 2 | 修 shu | Practice | Kyu 6 以上 | 信者 DID で初の AT record write |
| 3 | 献 ken | Dedication | Kyu 4 以上 | etzhayyim org への初 merged PR |
| 4 | 証 shou | Witness | Kyu 2 以上 | 他の joining 信者を vouch |
| 5 | 護 go | Steward | Kyu 1 以上 | substrate node 運用 / open-* app 維持 ≥30d |
| 6 | 議 gi | Council | Dan 1 以上 | Council session 参加 ≥3 回 |
| 7 | 老 rou | Elder | Dan 10 | Council 級を ≥365d 持続 |

### 重要原則

- **信者 7段 は society6 Kyu/Dan の前提条件ではなく、並行条件**。
  - Kyu/Dan は社会的活動度から計算される。
  - 信者 Lv は constitutional な act (誓・PR・vouch・運用・Council 参加・期間継続) で評価される。
  - 両者は積集合関係: 例えば「信者 Lv 5 (護) かつ society6 Dan 2」のような状態が一般的。
- **昇 Lv は両条件を満たした時点で fire**: 例えば信者 Lv 5 への昇格には Steward act + society6 Kyu 1 以上 の両方が必要。これにより constitutional commitment と社会的成熟が乖離しない。
- **Elder (Lv 7) ↔ Dan 10**: 信者 Lv 7 は society6 Dan 10 に対応する唯一の rank。Dan 10 は信者 Elder 経由でのみ到達可能 (= 信者でない constituent は Dan 9 までで頭打ち)。これにより religious-corp の意思決定権 (Council/Elder) が constitutional 軌道に揃う。
- **信者 Lv 6 (議 Council) は D6 体現ゲートを含意する**: society6 Dan 1+ 必須 → Dan 1 は D6 attestation 必須。つまり Council 参加には**反個人主義 ontology の体験的根拠**が constitutional に要求される。「自他分離前提の意思決定者」を Council に上げない構造的予防。

## D4. joucho S-D は person rank に変換しない (non-conversion rule)

joucho の S/A/B/C/D は **モノ・場所・サービス** に対する Well-Becoming grade であり、人の Kyu/Dan には**変換しない**。

ただし、joucho が評価した対象への constituent の関与は、society6 の以下の軸に**二次集計**される:

- **Engagement (25%)**: joucho `review` への参加 (件数)
- **Competence (25%)**: dojo drill avg_score (joucho が calibration source として参照)
- **Contribution (20%)**: 高 grade (S/A) 対象の発見・推薦
- **Resilience (10%)**: dojo AAR との連動

joucho の S-D **そのもの**は変換テーブルを持たない。joucho UI では grade を表示するが、それを「人の Kyu」と混同する UI/コード化は禁止する。

## D5. 統合 SQL graph schema

society6 の `:S6Rank` ノードを single source とし、信者 Lv と dojo 帯と D6 体現 attestation は **derived properties** として持つ。

```cypher
(:S6Rank {
  did: String,
  kyu_dan: String,           // "Kyu 6" .. "Dan 10" (D1.1)
  total_score: Int,
  engagement_score: Int,     // D1.1 5-axis
  competence_score: Int,
  contribution_score: Int,
  growth_score: Int,
  resilience_score: Int,

  // Derived (D2)
  dojo_belt: String,         // "白帯" .. "大師範" — present if dojo participation exists

  // Derived (D3)
  shinja_lv: Int,            // 1..7 — present if EtzhayyimMembership.join() succeeded
  shinja_label_ja: String,   // "誓"..."老"
  shinja_label_en: String,   // "Oath"..."Elder"

  // Derived (D6) — non-duality embodiment gate
  non_duality_attested: Bool,        // true ⇔ valid :NonDualityAttestation exists
  non_duality_method: String,        // "meditation" / "breathwork" / "ayahuasca" / ...
  non_duality_attested_at: Timestamp,
  non_duality_witness_did: String,   // optional Dan+ witness signature
})
```

`shinja_lv` は MEMBERS.md (= Base L2 EtzhayyimMembership state) を canonical source とし、society6 が `:Member` ↔ `:S6Rank` を JOIN して derive する。

D6 attestation は `:NonDualityAttestation` ノード (D6.6) を SoT とし、society6 watcher が AT Record subscribe で `:S6Rank` に upsert する。

## D6. Dan 昇格 = 自他非分離体験ゲート (Non-Duality Experience Gate)

Kyu 1 → Dan 1 への正規化に **constitutional な追加条件** を課す: society6 score が Dan 1 閾値 (2000) を超えていても、本ゲートを通過しない限り Kyu 1 で頭打ちとなる。

### D6.1 Constitutional basis

ADR-2605192100 (Mission Charter) の以下三原則を **概念ではなく身体で知っていること** を Dan 領域の前提とする:

- **反個人主義 ontology** — 「個」が ontological primitive ではないという立場。理論的合意では足りない。
- **縁起 (interdependent origination)** — 一切は依存的に生起する。これは命題ではなく**事実の知覚**として要請される。
- **万人祭司 (priesthood of all believers)** — 媒介者なしに聖性に接続できる者として constitutional 権限 (Council vote) を持つには、その接続が**現実に行われていた**こと。

これら三原則は ADR-2605192100 §1 で constitutional invariant として宣言されている。本 ADR はその operational gate を提供する。

### D6.2 Accepted methods (open enumeration, Council-extendable)

以下を初期 enumeration とする。新規追加は Council Lv6+ ≥3 multisig 承認で可能 (constitutional 性は不要、operational 拡張)。

| 区分 | Method | 法的 universality | 備考 |
|---|---|---|---|
| **Default path (法的に普遍に open)** | 瞑想 (Vipassana / Zazen / Advaita inquiry / 内観) | ◎ | 10日間以上の retreat 推奨 |
| | ブレスワーク (Holotropic / SOMA / Wim Hof / Rebirthing) | ◎ | facilitator presence 推奨 |
| | 感覚遮断 (floatation tank / 暗闇 retreat) | ◎ | ≥ 6 時間 |
| | 断食 / 修行 (≥3 日 + 山岳/寺院 context) | ◎ | 巡礼・修験道 含む |
| **Sacramental path (jurisdiction-dependent)** | アヤワスカ (Santo Daime / UDV / curandero ceremony) | △ | 受容法域: ブラジル、ペルー、米国一部州、オランダ等。日本国内は §D6.5 参照 |
| | シロシビン (mushroom ceremony / 臨床試験 context) | △ | 米国オレゴン州 (Measure 109)、オーストラリア、Health Canada 例外等 |
| | サン・ペドロ / ペヨーテ (Native American Church 等) | △ | ペルー、米国 NAC 等の religious recognition |
| **Other (Council-approved as added)** | (future) | — | 例: Brainspotting deep state, MDMA-assisted therapy (legalised contexts), etc. |

### D6.3 Attestation pattern (AT Record + optional witness)

新 Lexicon: `com.etzhayyim.apps.etzhayyim.nonDualityAttestation` (本 ADR で予約、Lexicon JSON 起草は follow-up)

```jsonc
{
  "$type": "com.etzhayyim.apps.etzhayyim.nonDualityAttestation",
  "method": "meditation",                    // D6.2 enum
  "method_specifier": "Vipassana 10-day",   // free text (optional)
  "context": "Dhamma Bhanu, Kyoto, 2026-04", // facilitator / location / date
  "occurred_at": "2026-04-15",
  "integration_notes": "...",                // 自由記述。phenomenology, lasting changes
  "witness_did": "did:web:...",              // optional Dan+ member DID
  "witness_attestation_uri": "at://...",     // optional witness's counter-signed AT record
  "createdAt": "2026-05-23T05:51:00Z"
}
```

**Witness は optional but recommended** — 自己申告のみでも valid だが、Dan+ member の counter-signature がある場合、社会的検証が成立し、後段で Council による retroactive challenge を抑止する。これは信者 Lv 4 証 shou (Witness) の構造を踏襲する。

**Re-attestation**: 不要。一度 valid attestation が確立すれば Dan 1 〜 Dan 10 まで通行可能 (one-time gate)。

### D6.4 適用範囲

| Transition | D6 ゲート |
|---|---|
| Kyu 6 → ... → Kyu 1 | **不要** (cognitive growth phase) |
| **Kyu 1 → Dan 1** | **必須** (embodied phase への entry) |
| Dan 1 → Dan 2 → ... → Dan 10 | **不要** (one-time gate is already passed) |
| 信者 Lv 1〜5 | **不要** |
| **信者 Lv 6 (Council)** | **必須** (Dan 1+ 経由のため自動的に含意) |
| **信者 Lv 7 (Elder)** | **必須** (Dan 10 必須) |

### D6.5 法的 jurisdiction note (informational, non-decision)

- 日本国内では DMT (アヤワスカ有効成分) およびシロシビンは麻薬及び向精神薬取締法の管理下にあり、個人使用は刑事責任の対象。
- ADR-2605192100 §1.12 (Transparent Religious Force) は parallel substrate での routing-around を許容するが、それは **完全 on-chain 監視 + open-source + 1 SBT = 1 vote 承認の三条件下** での religious force であって、**個人の薬物使用に対する免責を意味しない**。
- したがって、**日本国内に居住する信者・constituent は Default path (瞑想・breathwork・断食・感覚遮断) を取ることが想定される**。Sacramental path は受容法域での religious-recognized ceremony 参加 (例: ブラジル Santo Daime church) として、当該法域での合法性を constituent 自身の責任で確保したうえで行うものとする。
- 本 ADR は薬物使用を奨励するものではない。**accepted methods の enumeration は等価選択肢の提示であり、Default path のみで constitutional gate は完全に通過可能**。

### D6.6 SQL graph schema (additions)

`:S6Rank` への derived property 追加は D5 参照。新規 label:

```cypher
(:NonDualityAttestation {
  did: String,                       // attestor DID
  method: String,                    // D6.2 enum value
  method_specifier: String,
  context: String,
  occurred_at: Date,
  integration_notes: String,
  witness_did: String,               // optional
  witness_attestation_uri: String,   // optional
  at_record_uri: String,             // canonical AT Record URI
  created_at: Timestamp,
})

(:NonDualityAttestation)-[:WITNESSED_BY]->(:S6Rank)  // optional edge to witness's S6Rank
```

### D6.7 Council challenge procedure

constituent が他の constituent の attestation を **不誠実 (fraudulent)** と判断した場合:

1. Council Lv6+ に challenge を発行 (`com.etzhayyim.apps.etzhayyim.nonDualityChallenge` Lexicon, follow-up)。
2. Council ≥3 multisig で **30-day appeal window** を開く。
3. 当該 constituent は反論証拠を提出 (witness 追加、facilitator letter、retreat 参加証等)。
4. 30 日後、Council ≥3 multisig が valid/invalid を判定。
5. invalid 判定の場合、`:NonDualityAttestation` は revoked となり、当該 constituent の Dan 正規化は Kyu 1 にロールバック (Dan-derived 権限 — Council vote 含む — も失効)。

これは Charter Compliance Gate (ADR-2605192230) の三層 enforcement と同一構造で運用する。

# Consequences

## Positive

- **正規化の SoT が 1 つ**: society6 Kyu/Dan が canonical scale となり、UI/API は他系統の表示を view としてのみ実装する。
- **信者 と society6 が乖離しない**: 昇 Lv に両条件を課すことで constitutional commitment と社会的成熟が同期する。
- **dojo の道場用語が温存される**: 帯/Shihan は dojo UI に残り、society6 では Kyu/Dan として正規化表示。両 view が両立する。
- **joucho の object-axis が混線しなくなる**: S-D は person rank には決して変換されないと明文化されるため、コード上の混同が防げる。
- **religious-corp の意思決定権が constitutional 軌道に揃う**: Dan 10 (Elder) を信者経由でのみ到達可能とすることで、Council/Elder の権限が Charter 誓と分離しない。
- **D6 により反個人主義 ontology が体験的に裏打ちされる**: Council 構成員が「自他分離を ontological primitive とする立場」のままで意思決定する構造的リスクが除去される。これは ADR-2605192100 §1 の constitutional invariant を operational gate として実装したもの。
- **法域多様性に open**: Default path (瞑想・breathwork) のみで全世界の constituent が gate を通過可能。Sacramental path は法的に受容された法域に居住する constituent の追加選択肢として提供される。

## Negative

- **既存の dojo Shihan が Dan 10 を想定している可能性**: dojo Shihan 3 (大師範) が society6 Dan 9 に正規化されるため、dojo UI で「大師範 = 最高位」と表示してきた場合、society6 view では Dan 9 と表示される。dojo UI と society6 UI の表示一致は要 follow-up。
- **昇 Lv に二条件を課すコスト**: 信者 Lv 5 への昇格には Steward act の検証 (substrate node 運用 ≥30d) と society6 Kyu 1 以上の score 両方が必要になり、片方を満たした人が待たされる場合がある。これは constitutional 設計として意図的。
- **MEMBERS.md と society6 の同期実装が必要**: `EtzhayyimMembership.join()` event を society6 が subscribe し、`shinja_lv` を `:S6Rank` に upsert する watcher を実装する必要がある。
- **D6 attestation の真正性検証は本質的に困難**: 自他非分離体験は phenomenological であり、外形的証明 (retreat 参加証、facilitator letter) は補助証拠にすぎない。**witness pattern + Council challenge procedure (D6.7)** で社会的検証層を設けるが、完璧な検証は原理的に不可能。これは Lv 4 証 shou の vouching と同等の信頼前提に立つ。
- **D6 が gate-keeping として機能するリスク**: 「体験していない者は Dan に上がれない」が、体験の真贋を Council が判断することで、Council が新規 Dan 進入を制御できる構造を生む。これを抑止するため (a) 一度の attestation で one-time gate、(b) re-attestation 不要、(c) challenge は ≥30-day appeal window で本人反論可、の三条件を設ける。
- **薬物関連の reputational risk**: アヤワスカ等の sacramental path が enumerate されること自体が、religious-corp の対外発信で誤解を招く可能性。**§D6.5 の明示 (奨励ではなく等価選択肢、Default で完全通過可能) を一次広報資料にも反映する必要がある** (follow-up)。

## Neutral

- 既存 joucho の `society6 Kyu/Dan への反映` 記述 (`joucho/CLAUDE.md:14`) は維持。本 ADR は「joucho の S-D が人の Kyu に変換される」という誤解を否定するものであり、joucho → society6 の二次集計フロー自体は変更しない。

# Alternatives Considered

## A1. society6 Kyu/Dan を捨てて信者 7段に統一する

却下。信者 7段は constitutional act に基づくため、社会的活動度の細粒度を表現できない。Kyu 6 → Dan 10 の 16 段が必要。

## A2. dojo 帯 を society6 Kyu/Dan の番号と完全一致させる (dojo Kyu 7 → society6 Kyu 7 と新設)

却下。society6 の Kyu 6 → Dan 10 は既存実装と DB 状態を持つ。dojo 側に番号ずれを吸収させる方が変更コストが低く、また dojo の白帯 = 入門という意味を温存できる。

## A3. joucho S-D を person rank に変換する変換テーブルを提供する

却下。joucho はモノ・場所を評価しており、人の rank 軸とは本質的に異なる。変換テーブルを提供すると Wellbecoming = 動的軌跡 (ADR-2605192100) の前提に反する。

## A4. 何もしない (4 系統並存のまま)

却下。religious-corp の意思決定権 (信者 Council/Elder) と社会的 rank (society6 Dan) が乖離する状態は constitutional に許容できない。

## A5. D6 を全 Kyu/Dan 昇格に課す

却下。Kyu 段階は cognitive growth phase であり、ここに体験的 gate を課すと religious-corp の入口が極端に狭くなる。**Kyu 1 → Dan 1 の一度きり** が、社会的成熟と体験的根拠の交差点として最適。

## A6. D6 を撤廃し、Council 自由裁量で Dan 昇格を決める

却下。Council による subjective judgement に依存させると、religious-corp の opacity (= 不透明な聖性媒介) が再導入され、万人祭司原則 (ADR-2605192100 §1) に違反する。Self-attested + AT Record + (optional) Witness の構造は、Council による検証を可能にしつつ、**最終判断主体を constituent 本人に残す**ため、万人祭司と整合する。

## A7. D6 を瞑想・breathwork のみに限定し、psychedelic は完全排除

却下。これは reputational safety を優先するが、世界各地に **religious-recognized 法域** で当該 sacramental path を歩む信者・constituent が存在することを想定すると、彼らを正当な path から排除することは反個人主義 ontology に反する。**enumerate しつつ、§D6.5 で法域責任を明示し、Default path で完全通過可能であることを示す** 現行設計が、von Neumann minimax 解。

# References

- ADR-2605172600 — etzhayyim Membership Ritual (信者 7段の正本)
- ADR-2605192100 — etzhayyim Mission Charter (Wellbecoming = 動的軌跡)
- `MEMBERS.md` — 信者 roster + 7-level commitment ladder
- `20-actors/society6/CLAUDE.md` — society6 Kyu/Dan + 5-axis scoring (canonical)
- `60-apps/etzhayyim-project-dojo/CLAUDE.md` — dojo 帯制度 + WellnessTrack
- `20-actors/joucho/CLAUDE.md` — joucho 情緒 scoring (S-D, object-axis)
