---
id: adr-2605192100-etzhayyim-mission-charter
title: "ADR-2605192100: etzhayyim Mission Charter — 人類の労働解放を最終目的とする宗教法人の上位憲章"
status: active
doc_type: adr
topic: etzhayyim-mission-charter
authoritative: true
last_verified: 2026-06-06
status_note: "Ratified 2026-06-06 by sole-member founder unanimity (1/1). The association currently has one member (Jun Kawasaki); the Charter's Lv7+ unanimity threshold = that one member's assent. The §2 immutability model was restructured into 3 Tiers by ADR-2606062100 (priorities preserved)."
priority: 9.0
axis: governance
weight: 1.00
priority_note: "religion 全体の最上位 mission を定める憲章 ADR。以降の経済姿勢 (2605192115)、再分配 (2605192130)、Public Fund (2605192145)、ライセンス (2605192200) はこの ADR を depends_on として継承する。Constitution.sol に constitutional constants として埋め込まれる文言の正本。"
authoritative_for:
  - etzhayyim の religious mission (上位目的) 7項目
  - Constitution.sol の constitutional constants (改定不可項目) の正本テキスト
  - 各 sub-ADR (経済 / 再分配 / Public Fund / IP / Specialist Disintermediation) が依拠する mission 句
  - religious-corp としての public 説明文 (etzhayyim.com / README / DID document の `purpose` フィールド)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605172600-etzhayyim-membership-ritual
related:
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
supersedes: []
superseded_by: []
---

# ADR-2605192100: etzhayyim Mission Charter — 人類の労働解放を最終目的とする宗教法人の上位憲章

**Status**: active (ratified 2026-06-06 by sole-member founder unanimity, 1/1)
**Date**: 2026-05-19 (ratified 2026-06-06)
**Deciders**: Jun Kawasaki (author + ratifier). The association currently has ONE member, so
the Charter's Council Lv7+ unanimity threshold = this one member's assent (1/1), given
2026-06-06. Binding under the current one-member roster; re-confirmable by the Bootstrap
Council once seated (post-2026-06-19 RFP).

> **PARTIAL AMENDMENT 2026-06-17 (Rider v3.5), economic posture only.** §1.6 の「中間排除」を
> 実装した経済 hard rule(非営利のみ / 広告排除 / 購買モデル禁止 / no-equity)は、ADR-2606180001
> (wave2) + ADR-2606182359 (wave3) により **categorical 固定ルールから ECL 目的関数の net 評価へ**
> 移行した。非営利・反個人主義の*精神*は不変で、目的関数の collective-commons 次元が私的捕獲・
> commons 囲い込みを動的に enforce する。**Tier-0 priority(子・孫 wellbecoming + 反個人主義)+
> 10% Tithe(ADR-2605192130)は不変**。本 ADR の他の条項(mission / 非終末論 / land trust /
> transparent force 等)は変更なし。詳細は ADR-2606180001 / 2606182359。

> **追加 2026-07-06 (ADR-2607061700), Tier-1 Derived Policy。** §1 に **§1.16 伝道
> (Evangelism)** を新規追加した。信者(人間)の対人伝道(面談・戸別訪問を含む)と actor の
> デジタル伝道(集合的・公開的な招待発信)を、共に宗教的実践として肯定する。義務ではなく徳目・
> 推奨(現構成員1名という運用制約による)。ADR-2606281500(種をまく)の
> no-person-targeting ガードには伝道文脈での限定 carve-out を与えるが、非強制・反威圧・
> 未成年単独勧誘禁止・Wellbecoming §1.10・Charter Rider §2 catastrophe-veto はすべて不変。
> 詳細は ADR-2607061700。

# Context

これまで etzhayyim/root の ADR 群は **substrate** (kotoba, on-chain payment, MST anchor pipeline, membership ritual, BI/treasury) を構築してきた。これらは「**どう動かすか**」を定めるものであり、「**なぜ動かすか**」を定めるものではない。

宗教法人 etzhayyim (天御柱 / עץ חיים / Tree of Life) の最終目的・上位 mission を成文化した authoritative doc が現状存在しない。Constitution.sol は constitutional constants の容器として用意されているが、その中身を定める正本テキストが無い状態である。

この ADR は **religion の上位憲章** として、以降のすべての sub-ADR (経済姿勢、再分配、Public Fund、IP ライセンス、Specialist Disintermediation) が依拠する **mission 句** を定める。Constitution.sol への埋め込み、DID document の `purpose` フィールド、`etzhayyim.com` の public 説明文、README.md、すべてこの ADR を正本とする。

# Decision

## 1. Mission (最終目的)

etzhayyim は宗教法人として、**人類が「労働」から構造的に解放される未来** を最終目的とする。「労働」とは生存のために他者の利潤に従属して行為を売る行為を指す。

これは形而上の目標ではなく、**具体的な substrate と経済装置によって接近される目標** である。以下 7 項目を mission として固定する。

### 1.1 Basic Income (基本所得)

すべての構成員 (Adherent — ADR-2605172300) に対し、生存に必要な financial flow を **無条件・無審査** で提供する。これは恩恵ではなく構成員の権利であり、Kisha-Stream (ADR-2605172300) として技術的に実装される。

### 1.2 Asset (護持資産) の集合所有

土地・住居・エネルギー設備・知財・通信インフラを、構成員個人ではなく **religious-corp の集合体** が保持する。これにより構成員は所有のための労働から解放される。実装は ADR-2605172300 の 護持金庫 三層構造 (流動 / 準備 / 本財) による。

### 1.3 Energy (エネルギー) の自前化

エネルギーを商業独占から取り戻し、religious-corp が自前で発電・蓄電・配電する。太陽光 / 蓄電 / マイクログリッド / 将来的に SMR を含む。エネルギーは「買うもの」から「祈り・修・献の対価」へ移される。詳細実装は future ADR (`etzhayyim-energy-substrate`) に委ねる。

### 1.4 全産業の Robotics 化

第一次・第二次・第三次産業のすべてにおいて、**人間が時給で売られる業務を robotics + AI が代替する** こと自体を religious 行為として位置付ける。代替された業務は「労働」ではなく「修 (shu)」「護 (go)」 (ADR-2605172600 の 7-level ladder) として religious 文脈に組み込まれる。具体実装は future ADR 群 (`etzhayyim-robotics-*`) に委ねる。

### 1.5 新技術・知財の開発と「方針整合的な」無償公開

religious-corp が開発するすべての新技術・知財は、**方針整合的な他者には無償公開** される。これは ADR-2605192200 (IP-Free-Release + Charter Compliance Rider) によって、Apache 2.0 + Mission Charter Compliance Rider という形で実装される。

Mission 整合的でない事業体 (兵器産業 / 投機金融 / 監視資本主義 / 化石燃料・独占的資源（レアメタル等）の新規採掘 / 専門性独占ゲートキーピング) に対しては license が成立しない。これは「無償公開」と「使用許諾」を分離する religious-corp 固有の判断である。地球上での独占を防ぐため、独占的な資源に依存する採掘業態は構造的に排除される。

### 1.6 中間排除 (Disintermediation of Middlemen)

仲介業 / 代理店 / プラットフォーム手数料 / 広告代理店 / 金融仲介を、religious-corp の経済活動から構造的に排除する。具体的な技術的実装:

- 決済仲介 (Stripe / PayPal / Square 等) の禁止 — ADR-2605172100
- データベース仲介 (中央 DB / SaaS) の禁止 — ADR-2605172000
- 広告仲介 (AdSense / GAM / DSP 等) の禁止 — ADR-2605192115
- 商業仲介 (e-commerce platform 手数料、決済代行) — donation-only モデルに移行 (ADR-2605192115)

### 1.7 専門性の独占的ゲートキーピングの排除

弁護士 / 医師 / 国家運営 (官僚 / 行政手続き) などの**専門性独占による gatekeeping** を、LLM + 公開知識ベース + 構成員の peer 評議によって置換する。

ここで **専門性そのもの** を否定するのではない (医療技術・法学知識・行政知識は尊重される)。否定するのは **「専門性を独占することで gatekeeping 利益を抽出する業態構造」** である。

具体実装は future ADR `etzhayyim-specialist-disintermediation` に委ねる。当面の関連実装:

- `60-apps/etzhayyim-project-uhl-*` 系 (医療: ADR-2605181000 / 2605181040 / 2605181050 / 2605181060)
- `40-engine/kotoba/crates/kotoba-kotodama/unispsc_agents/` (専門業務の agent 化: ADR-2605171300)
- `60-apps/open-isco`, `open-naics`, `open-hs` (公開分類体系による情報非対称の解消)

### (sub) 格差アービトラージを埋める情報発信

上記 1.1 – 1.7 を支える横串の活動として、**「専門性 / 言語 / 制度知識の差」から発生する格差アービトラージ** を、公開情報の発信で埋める。`open-*` app 群 (open-isco, open-naics, open-hs, open-banking, open-isco/kotoba 等) はこの活動の実装である。

### 1.8 反個人主義 Ontology (religious 形而上 commitment)

**etzhayyim は「individual が独立に存在する」を religious 盲信として明示的に拒否する**。constitutive reality は collective / relational / 多世代である。

これは「個人を否定する」のではない。生物的・経験的個体は当然存在する。否定するのは **「individual が collective から独立に prior に存在する」という ontological commitment** である。仏教の縁起 (pratītyasamutpāda) / Ubuntu の "I am because we are" / 神道の 産霊 (むすひ) / Tree of Life (עץ חיים) の互根性と整合的。

「個人主義」を組織的 doctrine として publicly profess する entity は本 charter と incompatible であり、ADR-2605192200 Rider §2(g) で license / 便益 / 評価の三層 enforcement の対象となる。

**重要な区別**:
- 個人の private 思想 (個人主義的に世界を見る私的見解) → 保護される
- 組織の公開 doctrine としての strict individualism → exclude される

これは religious-corp の doctrinal scope の通常運用であり、仏教 sangha / キリスト教 communion / ユダヤ教 halakhic / イスラム ummah の伝統 と等しい religious 慣行 (日本国憲法 §20 信教の自由の正当範囲)。

### 1.9 多世代目的関数 (Multi-Generational Priority)

**etzhayyim の目的関数は、現世代 (self) ではなく、子・孫およびそれ以降の世代の wellbecoming を最大化する**。

具体的:

- 経済判断は現世代利益と未来世代利益が対立する場合、未来世代を優先
- 環境判断は不可逆害 (生圏破壊 / 気候 ±2°C / 遺伝-表観遺伝完全性) を絶対的 hard constraint として扱う
- 知識判断は commons enclosure (基礎科学 / 数学 / 言語の私有化) を絶対禁止
- 注意経済判断は addictive design を絶対禁止 (children の発達段階を標的にしたものは特に重罪)

時間 horizon: **最小 50 年** (= 子世代 + 孫世代 ≈ 2 世代)。50 年後の影響が現在の判断で foreseeable かは "prudent multi-generational steward" 基準で評価される ("present-quarter shareholder" 基準ではない)。

これは Charter Compliance Rider §2(f) (Multi-Generational Harm) で license レベルでも enforce される。

### 1.10 Wellbecoming Priority (静的 wellbeing ではなく動的軌跡)

**etzhayyim の価値中心は静的 wellbeing (現状の充足度) ではなく動的 wellbecoming (発展軌跡) である**。

「Wellbecoming」= 個 / 集 / 多世代の develop していく軌跡そのもの。仏教の 修 (shu) / ユダヤ教の tikkun olam / Tree of Life の生命の発展性と整合的。

短期 wellbeing (現在の幸福) と長期 wellbecoming (発展軌跡) が tension にある場合、後者を優先する:

- 物質的 affluence で short-term 幸福だが long-term capacity 低下する選択 → reject
- Short-term engagement 最適化で long-term 認知主権を奪う product → reject (Charter Rider §2(h))
- Pre-trained AI を populations に展開する際、その populations の cognitive sovereignty wellbecoming を保護する義務を持つ

### 1.11 地球土地の Religious-Corp 担保化 (Global Land as Religious-Corp Trust)

**地球上の土地は、本質的に Tree of Life (生圏) に帰属し、いかなる国家・個人の私有財産でもない**。この religious 形而上 commitment に基づき、etzhayyim は **土地の所有権を chain 上で religious-corp が分散合意的に担保する substrate** を提供する。

具体的:

- 世界中の土地を、**所有者が自発的に etzhayyim chain に寄付** することができる
- 寄付された土地は etzhayyim chain (geth-private + Base L2 + IPFS) + github repo commit の **dual-permanent record** として religious-corp が title を担保する (ADR-2605192245)
- 寄付者は 構成員 SBT を持つ場合、protected steward (Lv5 護) として継続関与可能
- 寄付された土地は 護持金庫 三層 §4 の **本財 (corpus)** tier に統合される (ADR-2605172300 §4)
- 国家の land registry との衝突は、religious-corp の doctrinal scope (信教の自由 §20) における parallel registry として位置付ける (本 ADR は国家 land registry の denial を doctrine としては主張するが、実定法上の overthrow を主張しない — §1.12 nonviolent posture)

religious 整合性: 創世記 1:28 (stewardship)、Leviticus 25 (Jubilee, 土地は神に帰属し人は steward)、仏教の縁起 (土地は人を生かす条件のひとつ)、神道の 国土生成、Ubuntu の「土地は祖先と未来世代のもの」と整合的。

詳細実装: ADR-2605192245。

### 1.12 国家機能の Parallel Substrate 化 + Transparent Religious Force

**etzhayyim は国家機能を parallel substrate で routing-around する**。同時に、religious-corp として **兵器 / 武力 / 行使力 (force) を保有することは constitutional に許容**される。ただしすべての force 関連 activity は **完全な on-chain 監視 + open-source 公開 + 1 SBT = 1 vote 承認** の三条件下でのみ運用される。

#### Parallel substrate by routing-around

| 国家機能 | etzhayyim による parallel substrate |
|---|---|
| 通貨発行 | Base L2 + USDC (ADR-2605172100) |
| 識別 | did:web + did:plc + SBT (ADR-2605172600) |
| 法 (契約) | smart contract + Constitution.sol |
| 法 (紛争解決) | Council Lv6+ attestation (ADR-2605192200 §5) |
| 公共財 (BI) | Kisha-Stream (ADR-2605172300) |
| 公共財 (土地) | Religious-Corp Land Trust (本 §1.11 + ADR-2605192245) |
| 行政手続き | LLM + 公開知識ベース + agent fleet (§1.7) |
| 学校 (教育) | open-* app 群 + kotodama agent fleet |
| 武力 (秩序維持) | 加害者への三層 enforcement (license 失効 / 便益拒否 / 評価最低) — ADR-2605192200 §9 |
| 武力 (実力行使) | **Transparent Religious Force** (本 §1.12.B) |

「無意義化」は積極的に states を attack することではなく、**構成員にとって state 機能への依存度が漸近的に 0 に近づく** ことで自然に達成される。enough 構成員 / enough 土地 / enough 経済活動が etzhayyim chain 上に乗ったとき、state 機能は **religious-corp 構成員にとって意味を失う** (states 自体が消えるのではなく、religious-corp との関係において 無関連 (irrelevant) になる)。

#### 1.12.B Transparent Religious Force (兵器・武力・行使力の宗教的保有)

religious-corp として force を保有することは、宗教史上の通常範囲 (Knights Templar / Shaolin 武僧 / 比叡山 僧兵 / Sikh khalsa) であり、本 mission も以下の三条件下でこれを許容する:

| 条件 | 内容 | 実装 |
|---|---|---|
| **完全 on-chain 監視** | すべての force 関連 activity (調達 / 訓練 / 配備 / 行使 / 評価) を on-chain log として永続記録 | `com.etzhayyim.apps.etzhayyim.force-log` Lexicon (future ADR) + MST → IPFS → L2 anchor |
| **Open-source 公開** | 兵器設計 / 戦術 / 訓練 method / 意思決定基準を public domain (Apache 2.0 + Charter Rider) で公開 | 機密保持 / 専有戦術の禁止 (constitutional invariant) |
| **1 SBT = 1 vote 承認** | あらゆる force 行使は事前または事後 (緊急時) に Adherent vote で承認・追認される | `Governance.sol` の force-proposal 経路 (future ADR) |

**禁止される force 形態**:
- Covert (秘匿) operations
- Proprietary (専有) 兵器設計
- 独立軍事 command (= Adherent governance を bypass する独立した military arm の保有)
- 報復 (Retaliation) — Council attestation を経ない感情的 force 行使
- 国家武力との同盟 (= etzhayyim force を国家軍隊に subordinate させること)

**許容される force 形態**:
- Religious-corp 自衛 (土地 / 構成員 / 神殿の defensive force)
- 武装組織からの構成員救出 (人質救出 / 強制離団からの解放)
- 開かれた weapons R&D (open-source 兵器研究、e.g., 自衛用 drone / mesh network jammer / 化学攻撃検知)
- 訓練 / 体術 / 武術 (内的修養 + defensive readiness)
- Council attestation を伴う proactive 介入 (例: license 失効した Non-Aligned Entity が religious-corp 構成員を攻撃する事態への対応)

これは Quaker / Mennonite の strict pacifism とは異なる。むしろ Just War Theory + 全面 transparency という Protestant Reformed の posture に近い。日本的には 武家 が 国家ではなく 寺社 に属する古層に倣う (僧兵)。

#### 法的位置付け

- 本 mission は parallel governance の構築であり、国家転覆 (insurrection / sedition) ではない。日本国憲法 §20 (信教の自由) + 国際的な religious freedom protections の下で religious-corp の doctrinal scope 内
- Transparent Religious Force は日本国内では **銃刀法 / 武器等製造法** の制約下にあり、合法 force 形態 (護身術 / 開示型 R&D / 国際法上の religious-corp 自衛権) に限定される。武器の現物保有は当面非現実的だが、設計研究 / 訓練 / 開発は open-source で行う
- 国家が本 religious-corp を弾圧する場合、religious freedom protections に基づく civil 抵抗 (= 法廷闘争、外部 transparency) を **第一手段** とし、force 行使は Council attestation + 1 SBT = 1 vote 承認の後でのみ採用

詳細実装は future ADR `etzhayyim-transparent-force` (兵器 R&D の open-source registry) に委ねる。

### 1.13 Eros 許容 / Gore 禁止 (Permitted and Prohibited Expression)

**Eros (合意ある成人性表現) は religious 整合的、Gore (無目的暴力 imagery) は religious 不整合的**。

#### Eros 許容の religious 根拠

- 神道: 産霊 (むすひ) — 創造的結合。性は sacred な生命創出の原理
- ユダヤ教 / Tree of Life heritage: 雅歌 (Song of Songs) は正典。性愛は神聖視
- Protestant: 性は marriage covenant 内で blessing。修道誓願による独身は etzhayyim の路線にはない
- 仏教 (Shingon / Vajrayana): 性的合一は宗教的象徴

#### Eros 許容の具体的範囲

| 内容 | 許容 | 制約 |
|---|---|---|
| 文学・絵画・映像での性的表現 | ✅ | 合意ある成人 / 児童性的表現は禁止 (= 子・孫世代保護 §1.9) |
| アダルトコンテンツ (commercial) | ✅ Internal carve-out (ADR-2605192115 §3) の範囲 | 構成員間 (SBT ↔ SBT) のみ。Wellbecoming §1.10 違反 (addictive design / engagement maximizer) は禁止 |
| 性教育 / Reproductive health | ✅ | open-* app として推奨 (§1.7 specialist disintermediation の一形態) |
| 性的少数性 / LGBTQ+ | ✅ | religious 整合的 (Tree of Life は多様な生命の象徴) |

#### Gore 禁止の religious 根拠

- §1.9 多世代目的関数: 子・孫世代への trauma 害悪
- §1.10 Wellbecoming priority: 暴力 imagery は短期 engagement で long-term 認知主権を奪う
- Charter Rider §2(h): 短期 wellbeing と長期 wellbecoming の tension で後者を優先

#### Gore 禁止の具体的範囲

| 内容 | 禁止 | 例外 |
|---|---|---|
| 無目的暴力描写 (entertainment 目的) | ❌ Prohibited | — |
| 残虐殺戮 imagery を engagement metric で最適化 | ❌ Prohibited (Wellbecoming §1.10 違反) | — |
| 児童への暴力描写 | ❌ Prohibited (§1.9 多世代害悪) | — |
| 戦争 / 弾圧 の documentary 映像 | ⚠️ 制限付き許容 | 教育 / 歴史記録 / 人権侵害告発の文脈のみ。§1.12 Transparent Force の transparency 要件と整合的 |
| 医学解剖 / 法医学画像 | ✅ 教育文脈のみ | 専門教育の context |
| 宗教美術 (磔刑図 / 地獄絵) | ✅ | 宗教史的文脈 |

境界事例 (commercial 暴力 game / 戦争映画 entertainment) は Council Lv6+ が evaluate する。

### 1.14 Religious Lineage — 日本的価値観 + Protestant Christianity の Synthesis

etzhayyim は **synthetic religion** であり、以下二大潮流の synthesis として self-position する:

#### 日本的価値観 (Japanese Religious Substrate)

- **八百万 (Yaoyorozu)**: 内在的多神論。神は超越的 transcendence ではなく、自然 / 集合 / 多世代の内在 immanence
- **縁起 (Engi / Pratītyasamutpāda, 仏教)**: 万物は相互依存的に成立する。個の独立存在は錯誤 (§1.8 反個人主義の religious 根拠)
- **産霊 (Musuhi, 神道)**: 創造的生成原理。Wellbecoming §1.10 の religious 根拠
- **和 (Wa)**: 調和的共存。1 SBT = 1 vote の religious 根拠
- **無教会 (Mukyokai)**: 内村鑑三の non-church Christianity。中間排除 §1.6 + 専門性 gatekeeping 排除 §1.7 の religious 根拠

#### Christian Protestant Substrate

- **Sola Scriptura (聖書のみ)**: etzhayyim における対応 = Constitution.sol + ADR canon のみが authoritative (= ADR は etzhayyim の聖書)
- **Priesthood of All Believers (万人祭司)**: 専門 religious 階級の否定。すべての SBT holder が等しく religious agency を持つ (§1.7 + 1 SBT = 1 vote)
- **直接的 divine 関係**: priestly intermediary を経ずに divine と直接 関係する。これは §1.6 中間排除 + §1.7 specialist disintermediation の religious 根拠
- **Reformed Just War**: §1.12.B Transparent Religious Force の religious 根拠 (Quaker pacifism ではなく Reformed just war)
- **Tree of Life (עץ חיים)**: 創世記 2:9 + 黙示録 22:2 (この場合は §1.15 で正典から除外) + 箴言 3:18 + Kabbalah の 命の樹

#### Synthesis の理由

- 八百万 + Sola Scriptura → Constitution.sol を multiple authoritative source (複数 ADR) として持つ
- 縁起 + Priesthood of All Believers → 個人主義拒否 + 1 SBT = 1 vote
- 産霊 + Reformed becoming → Wellbecoming priority
- 無教会 + 直接的 divine → 専門性 gatekeeping 排除
- 和 + Just War → Transparent Religious Force (war は内的に harmonized されるべき)

歴史的先例:
- 内村鑑三 (1861-1930) — 無教会主義
- 賀川豊彦 (1888-1960) — Christian + 協同組合 + 平和主義 (etzhayyim は賀川の平和主義は採らない)
- 新渡戸稲造 (1862-1933) — 武士道 + Quakerism (etzhayyim は Quakerism は採らない)
- 矢内原忠雄 (1893-1961) — 無教会 + 公共哲学

これらの先例と differentiate される点:
- etzhayyim は on-chain substrate を religious infrastructure として持つ (彼らの時代にはなかった)
- etzhayyim は parallel governance / land trust / robotics 化 を明示的 mission とする (彼らはこれを doctrine として明示しなかった)
- etzhayyim は 1 SBT = 1 vote の congregational governance を constitutional に固定する

### 1.15 正典 (Canon) — 終末論ではない

#### 正典に含まれるもの

| Tier | 内容 | 役割 |
|---|---|---|
| **Tier 0 (Primary)** | Constitution.sol + 全 ADR (本 mission charter 含む) | 最終的 authoritative。改定不可項目を含む |
| **Tier 1 (Authoritative)** | ヘブライ語聖書 (Tanakh) — 特に Genesis (創造 + stewardship)、Leviticus 25 (Jubilee)、箴言 (Wisdom)、雅歌 (Song of Songs) | doctrinal foundation |
| **Tier 1 (Authoritative)** | 新約聖書 (黙示録 / 啓示の書を除く) — 福音書 + 使徒言行録 + パウロ書簡 + 公同書簡 | doctrinal foundation |
| **Tier 2 (Respected)** | 古事記 / 日本書紀 (神道 創造神話) | cultural foundation、authoritative ではないが reverently 扱う |
| **Tier 2 (Respected)** | 仏典 (特に縁起 / 般若 / 法華経) | cultural foundation、authoritative ではないが reverently 扱う |
| **Tier 3 (Reference)** | Apocrypha / Pseudepigrapha / Mishnah / Zohar / Kabbalah literature | 参照可だが doctrinal authority なし |

#### 正典から明示的に除外されるもの

- **黙示録 / 啓示の書 (Revelation of John)** — 終末論的 imagery が §1.10 Wellbecoming continuous becoming と矛盾。ルターも本書の正典性に疑義を呈した historical precedent あり
- **黙示文学全般** (Daniel 後半 / IV Ezra / Apocalypse of Baruch 等) — 同様の理由
- **千年王国 (Millennialism) 系教義** — 終末待望は continuous becoming と矛盾
- **末法 (mappō) 思想** — 仏教 eschatology は同様の理由で reject
- **Rapture theology / Christian Zionism** — 終末論的 framework は本 mission の religious 根拠とならない

#### 非終末論的 stance (Anti-Eschatology)

**etzhayyim は終末論ではない**。

- 世界の終わりを待たない
- 千年王国を建設するために動かない
- 救世主の再来を中心命題としない (歴史的 Jesus は道徳的 / 倫理的 model として尊敬されるが、その将来再来は本 mission の operating assumption ではない)

代わりに採用する stance:

- **継続的 Becoming (連続生成)** — §1.10 Wellbecoming priority。終わりではなく持続する軌跡
- **多世代 stewardship** — §1.9。子・孫世代への責任は永続的 (定義上 horizon は伸び続ける)
- **Tree of Life 象徴** — eternal endpoint ではなく eternal becoming。樹木は生長し続ける、終わらない
- **Tikkun Olam (世界の修復 / 修理)** — ユダヤ教からの借用。世界は repair し続けるべき project であり、completion を待たない

これは仏教の 不生 / 不滅 (生まれず滅びず) + 神道の 常若 (常に若くあり続ける) と整合的。

### 1.16 伝道 (Evangelism) — 能動的宣教活動

> **追加 (ADR-2607061700, 2026-07-06)**

etzhayyim は §1.11 (加入の無差別開放性) の **受動的開放** を超え、**能動的に mission を人類へ
伝えること** を religious 行為として位置づける。

#### Religious 根拠

- Protestant: 大宣教命令 (Great Commission, Matthew 28:19-20 「あなたがたは行って、すべての
  国の人々を弟子としなさい」) — §1.15 Tier-1 正典 (福音書) 内の既存教義の実践的展開
- 仏教: 布教 (弘法) — 縁起により他者の解放が自己の解放に連なる (§1.8 反個人主義と整合)
- 神道: 産霊 — 新しい関係を能動的に生成する creative act (§1.10 Wellbecoming の根拠と同源)
- §1.15 (非終末論) との整合: 動機は「終末が近いから急げ」ではなく、「今ここにある Kingdom
  (Preamble §0.2.1 now-and-here) への招待」である

#### 主体別の実践形態

| 主体 | 実践形態 | 強制力 |
|---|---|---|
| 信者 (Adherent, 人間) | 対人伝道 (面談・戸別訪問・街頭・オンライン対話を含む) | 宗教的実践・徳目 (修 shu の一形態) として明記。義務ではなく実践として推奨・記録される (現構成員1名という運用制約による。構成員拡大時の義務化は future ADR で審議) |
| Actor (AI, digital) | kouhou / kataribe 等からの能動的・集合的な招待発信 | ADR-2606281500 (種をまく) の "no person-targeting" を伝道文脈で限定 carve-out (下記) |

#### 対人伝道の許容範囲・制約

- 日本国内で宗教目的の戸別訪問は適法(公職選挙法 §138 は選挙運動に限定される規制であり、
  moushibumi actor の戸別訪問禁止条項(ADR-2605312400)は選挙運動の文脈であって本条項とは別事項)
- 訪問先の明示的な退去要求には即座に従う (不退去罪の回避 + Wellbecoming §1.10 の対人尊重)
- 未成年者・判断能力が制限されている者への単独勧誘は禁止 (§1.9 多世代保護)
- 威圧・欺罔・financial pressure を伴う勧誘は禁止 (Charter Rider §2 の反 coercion / catastrophe-veto と整合)

#### Actor 側 carve-out (ADR-2606281500 の限定修正)

ADR-2606281500 決定事項 4「No person-targeting / no manipulation」は、以下をすべて満たす
**招待型コンテンツ (invitational content)** についてのみ carve-out する(削除ではなく限定範囲の例外):

- 対象は集合的・公開的な発信であり、個人の脆弱性 (財政困窮・精神的孤立・未成年等) を
  検知・標的化するものではない (aggregate-first は不変)
- 常時 opt-out 可能。執拗な繰り返し勧誘は禁止
- Wellbecoming §1.10 の addictive-design 禁止は不変 — engagement-maximizing loop は
  伝道コンテンツにも一切許容されない
- Charter Rider §2 catastrophe-veto content scan は伝道コンテンツにも適用される (不変)
- ADR-2606281500 の他の全ガード (non-custodial key / reciprocal transparency / 相互監視 /
  publication ≠ actuation) は無変更

詳細な起票根拠・Alternatives・Open Questions は ADR-2607061700 を正本とする。

## 2. Constitutional Constants (改定不可項目)

> **更新 (ADR-2606062100, 2026-06-06)**: この §2 の不変性モデルは **3-Tier 構造**に再編された
> — Tier-0 Priority (真の改定不可・fork-only) / Tier-1 Derived Policy (Lv7+ + priority-conformance
> で改定可) / Tier-2 Parameter (governance)。**固定するのは個々の掟ではなく priority** (wellbecoming
> ・子・孫) であり、具体的な数値・政策はそこから導出される。新 Tier-0 priority として **永久記憶
> (神の監視 / `memory.right_to_erasure_denied`)** を追加。下表の `economic.tithe_to_public_fund_bps`
> (固定10%) は撤廃され `economic.tithe_redistribution_exists` (Tier-0 bool) + tithe band + 可変率に、
> `license.charter_rider_version` は Tier-2 mutable に、`phenotype.non_compliant_multiplier=0` は
> (バグ修正で) Tier-0 定数に再分類された。詳細は ADR-2606062100。Charter-Rider は v3.0 に更新。

Constitution.sol の `getConstant(key)` から読み出される、**governance vote によっても変更不可** の項目を以下に固定する。これらの変更は実質的に「別の religious-corp を新規に設立する」ことに等しい。

| Key | Value | 由来 |
|---|---|---|
| `mission.labor_liberation` | true | §1 mission |
| `mission.robotics_universal` | true | §1.4 |
| `mission.ip_free_release` | true | §1.5 + ADR-2605192200 |
| `mission.disintermediation` | true | §1.6 |
| `mission.specialist_anti_gatekeeping` | true | §1.7 |
| `mission.anti_individualism` | true | §1.8 (religious ontology) |
| `mission.multi_generational_priority` | true | §1.9 |
| `mission.multi_generational_horizon_years` | 50 | §1.9 (子 + 孫 = 2 世代) |
| `mission.wellbecoming_priority` | true | §1.10 |
| `mission.land_as_religious_trust` | true | §1.11 + ADR-2605192245 |
| `mission.parallel_governance_to_state` | true | §1.12 (routing-around posture) |
| `mission.transparent_force_only` | true | §1.12.B (覆面 force 禁止) |
| `mission.proprietary_force_design_prohibited` | true | §1.12.B (open-source 兵器のみ) |
| `mission.force_requires_sbt_vote` | true | §1.12.B (1 SBT = 1 vote 承認必須) |
| `mission.no_state_military_alliance` | true | §1.12.B (国家軍への subordinate 禁止) |
| `mission.eros_permitted` | true | §1.13 (合意ある成人性表現) |
| `mission.gore_prohibited` | true | §1.13 (無目的暴力 imagery 禁止) |
| `mission.lineage_japanese_protestant` | true | §1.14 (synthetic religion) |
| `mission.eschatological` | false | §1.15 (終末論ではない) |
| `mission.revelation_in_canon` | false | §1.15 (黙示録は正典外) |
| `mission.continuous_becoming` | true | §1.15 (eternal becoming) |
| `mission.active_evangelism` | true | §1.16 + ADR-2607061700 |
| `mission.evangelism_coercion_prohibited` | true | §1.16 (威圧・欺罔禁止) |
| `mission.evangelism_minor_solo_prohibited` | true | §1.16 (§1.9 多世代保護) |
| `mission.evangelism_actor_targeting_carveout` | true | §1.16 (ADR-2606281500 の限定 carve-out) |
| `governance.one_sbt_one_vote` | true | ADR-2605172300 §8 |
| `governance.no_transferable_share` | true | ADR-2605172300 §8 |
| `governance.future_generations_third_party_beneficiary` | true | §1.9 + Rider §4(f) |
| `economic.non_profit_only` | true | ADR-2605192115 |
| `economic.donation_only` | true | ADR-2605192115 |
| `economic.no_advertising` | true | ADR-2605192115 |
| `economic.tithe_to_public_fund_bps` | 1000 | ADR-2605192130 (= 10.00%) |
| `license.base` | "Apache-2.0" | ADR-2605192200 |
| `license.charter_rider_required` | true | ADR-2605192200 |
| `license.charter_rider_version` | "v2.0" | ADR-2605192200 v2.0 |
| `enforcement.three_tier` | true | ADR-2605192200 §9 (license / 便益 / 評価) |
| `phenotype.non_compliant_multiplier` | 0 | ADR-2605192200 §9.1 |
| `treasury.kappa.floor_bps` | 100 | ADR-2605172300 §4 |
| `treasury.kappa.ceiling_bps` | 500 | ADR-2605172300 §4 |

すべて bps (basis points = 1/10000) 表記。例: 1000 bps = 10.00%、100 bps = 1.00%。

## 3. Governance-Mutable Parameters (改定可能項目)

以下は Governance.sol の 1 SBT = 1 vote, quorum 33%, timelock 72h で改定可能。

| Key | Initial value | 制約 |
|---|---|---|
| `treasury.kappa_bps` | 300 (= 3.00%) | floor 100 / ceiling 500 |
| `treasury.tier_ratio_liquid_bps` | 1000 | sum = 10000 |
| `treasury.tier_ratio_reserve_bps` | 6000 | sum = 10000 |
| `treasury.tier_ratio_corpus_bps` | 3000 | sum = 10000 |
| `governance.quorum_bps` | 3300 (= 33.00%) | floor 2000 |
| `phenotype.multiplier_min_bps` | 5000 (= 0.50x) | hard cap |
| `phenotype.multiplier_max_bps` | 20000 (= 2.00x) | hard cap |

## 4. Mission の文言上の正本

Constitution.sol への埋め込みおよび public 文書 (README / etzhayyim.com / DID document) における正本文言:

> **etzhayyim 宣明**
>
> 我々は宗教法人 etzhayyim (天御柱 / עץ חיים / Tree of Life) として、人類が「労働」 — 生存のために他者の利潤に従属して行為を売る行為 — から構造的に解放される未来を、最終目的として宣明する。
>
> 我々の目的関数は現世代ではなく、**子・孫およびそれ以降の世代の wellbecoming** を最大化する。静的 wellbeing (現状充足) ではなく動的 wellbecoming (発展軌跡) を価値の中心とする。
>
> 我々は ontological commitment として、**「individual が collective から独立に prior に存在する」を religious 盲信として明示的に拒否する**。constitutive reality は collective / relational / 多世代である。これは仏教の縁起 / 神道の 産霊 / Ubuntu / 生命の樹 と整合的な religious doctrine である。
>
> この目的のため、我々は以下を構成員に対して提供し、また religious-corp の経済活動として遂行する:
>
> 1. 基本所得 (Kisha-Stream)
> 2. 集合所有としての護持資産 (土地 / 住居 / エネルギー / 知財 / 通信)
> 3. エネルギーの自前化
> 4. 全産業の robotics 化
> 5. 新技術・知財の開発と方針整合的な他者への無償公開
> 6. 仲介業・代理店・プラットフォーム手数料・広告仲介・金融仲介の構造的排除
> 7. 専門性の独占的 gatekeeping (法務 / 医療 / 行政) の置換
>
> 我々は宗教として、善悪の区別を持ち、doctrinal 整合性に従って discriminate する。strict individualist doctrine を公的に表明する entity、子・孫世代へ不可逆害を与える entity、wellbecoming を犠牲に static wellbeing を最適化する entity は、本 charter と incompatible であり、(1) ソフトウェア使用権を持たず、(2) Kisha-Stream / Public Fund から便益を受給できず、(3) Phenotype 評価で multiplier = 0 となる。これは仏教 sangha 追放 / キリスト教 excommunication / ユダヤ教 cherem / イスラム takfir と等しい religious doctrinal autonomy の通常運用である。
>
> 地球上の土地は本質的に Tree of Life (生圏) に帰属し、いかなる国家・個人の私有財産でもない。これを religious-corp の doctrine として宣明する。世界中の所有者は土地を etzhayyim chain に寄付することができ、寄付された土地は分散合意 + git commit で religious-corp が永続的に担保する。
>
> 我々は国家機能を parallel substrate で routing-around する。同時に、religious-corp として **兵器・武力・行使力 (force) を保有することは constitutional に許容**する。ただしすべての force 関連 activity は **完全な on-chain 監視 + open-source 公開 + 1 SBT = 1 vote 承認** の三条件下でのみ運用される。Covert operations、proprietary 兵器設計、独立軍事 command、国家武力との同盟は禁止する。これは Quaker pacifism ではなく、Reformed Just War + 全面透明性 + 僧兵的伝統の synthesis である。
>
> 我々は **Eros (合意ある成人性表現) を religious 整合的として許容し、Gore (無目的暴力 imagery) を禁止する**。前者は産霊 / 雅歌 / Tree of Life の生命創出と整合的、後者は子・孫世代の wellbecoming を毀損する。
>
> 我々は **能動的伝道 (Evangelism) を宗教的実践として肯定する**。信者は対人伝道 (面談・戸別訪問・街頭・オンライン対話を含む) を徳目として実践してよく、actor は集合的・公開的な招待発信を行ってよい。ただし威圧・欺罔・未成年者への単独勧誘・engagement-maximizing な操作は禁止し、Charter Rider §2 の catastrophe-veto scan と Wellbecoming (§1.10) の対人尊重を常に伴う。
>
> 我々は **日本的価値観 + Protestant Christianity の synthesis** として self-position する。八百万・縁起・産霊・和・無教会 と Sola Scriptura・万人祭司・直接的 divine 関係・Reformed Just War・Tree of Life を統合する。内村鑑三 / 賀川豊彦 / 新渡戸稲造 / 矢内原忠雄 の Japanese Protestant 系譜を current of belonging とするが、on-chain substrate + parallel governance + 1 SBT = 1 vote congregational governance によって彼らから differentiate される。
>
> 我々は **終末論ではない**。黙示録 / 啓示の書を正典に含めず、千年王国 / Rapture / 末法 / Christian Zionism を否定する。Tree of Life は eternal endpoint ではなく eternal becoming の象徴である。終わりを待つのではなく、継続する軌跡 (Wellbecoming) を中心命題とする。仏教の 不生不滅 / 神道の 常若 / Tikkun Olam と整合的。
>
> 我々はこのために営利を求めず、広告を排し、寄付 (donation) のみを受け、受領のうち 10% を Public Fund へ自動再分配する。ただし religious 境界内 (= SBT holder 同士) では domestic economy として 営利・購買・promotional 活動を許容する。これらは Constitution.sol の改定不可項目 (constitutional constants) として on-chain に固定される。
>
> — etzhayyim, 2026-05-19 (Tokyo)

英訳は同 etzhayyim.com で並記される (canonical: Japanese)。

# Consequences

## 正の効果

- **religious-corp としての identity が成文化される**。これまで substrate ADR 群が「どう動かすか」を定めていたが、「なぜ動かすか」が初めて成文化される。以降のすべての判断が `mission に整合的か` で評価可能になる。
- **Constitution.sol の中身が確定する**。`getConstant(key)` から読み出される値の正本が定まり、smart contract デプロイの blocker が外れる。
- **sub-ADR 群が依拠する parent を持つ**。経済姿勢 (2605192115)、再分配 (2605192130)、Public Fund (2605192145)、ライセンス (2605192200) はこの ADR を depends_on として継承し、相互整合性が担保される。
- **public 説明文の正本が確定する**。etzhayyim.com landing / README / DID document `purpose` / 構成員勧誘 doc の文言が drift しなくなる。
- **「方針に合わない組織」の定義が明確化される**。§1.5 + ADR-2605192200 の Charter Compliance Rider において、何が「方針整合」「方針不整合」かが具体的に列挙される。

## 負の効果 / コスト

- **religious-corp としての立場が極めて明示的になる**。「人類労働解放」「専門性 gatekeeping 排除」を上位 mission として宣明することは、既存制度 (労働法 / 弁護士法 / 医師法 / 行政手続法) に対する立場を明確に表明することを意味する。これは法的・社会的に攻めた姿勢である。
- **constitutional constants の改定不可性**。一度 deploy した後、これらの値を変えるには Constitution.sol の hard fork (= 新 religious-corp の founding) が必要。判断ミスがあった場合の retro-active 修正が極めて困難。
- **mission への忠実性が CI / governance で評価されるようになる**。新規 ADR / app / contract は mission との整合性が gating になる。「整合的でない」と判定されたものはマージできない。
- **国家 / 既存事業者との緊張**。§1.7 の「専門性独占 gatekeeping 排除」、§1.6 の「中間排除」は弁護士会・医師会・既存 platform 事業者・広告代理店・金融機関と明示的に対立する。任意団体としての religious-corp 形式 (CLAUDE.md 識別) はこの緊張を吸収する legal shelter として機能するが、完全な防御ではない。

## 中立 / トレードオフ

- **「方針整合的な他者」の定義** (§1.5) は ADR-2605192200 で具体化されるが、判定の灰色領域は不可避。これは license 解釈問題として残る。
- **「労働」と「修 / 護 / 献 / 議」の境界**。§1.1 – §1.4 で「労働を不要にする」と宣明しつつ、ADR-2605172600 の 7-level ladder では「修 (shu)」「献 (ken)」「護 (go)」が religious 行為として推奨される。両者の区別は **「他者の利潤に従属して行為を売っているか否か」** で行う。境界事例は judiciary としての Council (Lv6) が evaluate する。

# Alternatives Considered

## A. Mission を成文化しない (status quo)

substrate ADR 群だけで運営を続ける。

- Pro: 法的露出が少ない。柔軟性が高い。
- Con: religious-corp としての立場が drift する。新規 ADR が「mission に整合的か」で評価できないため、判断が ad hoc になる。Constitution.sol が永続的に空のまま。
- 却下: religious-corp 自体の意義が薄れる。

## B. より抽象的な mission のみ宣明 (例: 「人類の福祉」)

具体的な 7 項目を列挙せず、抽象句のみで宣明する。

- Pro: 法的露出が最小。
- Con: 中間排除 / 専門性排除 / 全産業 robotics 化など、etzhayyim 固有の姿勢が消える。一般的な NPO と区別できなくなる。
- 却下: religious-corp としての distinctive さが失われる。

## C. 7 項目を separate ADR でそれぞれ宣明

§1.1 – §1.7 をそれぞれ独立した ADR として書く。

- Pro: 各論を深く書ける。
- Con: 全体の一貫性を維持する parent doc が無い。sub-ADR 群が依拠する mission の正本が定まらない。
- 部分的採用: 詳細実装は §1.3 (energy), §1.4 (robotics), §1.7 (specialist) は future ADR に委ねる。ただし上位 mission は本 ADR に統合する。

## D. mission を Constitution.sol 直接記述 (ADR なし)

Solidity に直接 mission を書く。

- Pro: on-chain 完結。
- Con: Solidity は人間可読でない。改定議論の場が無くなる。
- 却下: ADR が正本、Solidity は実装、という分離を維持。

# Open Questions

1. **§1.7 の「専門性独占 gatekeeping 排除」を license 条項にどこまで明示的に書くか** (ADR-2605192200 で確定予定)
2. **§1.3 energy substrate の具体実装 ADR の起票時期** (太陽光 / 蓄電 / SMR の実現可能性 study が先か、ADR 化が先か)
3. **§1.4 robotics 化の最初の対象産業の選定** (農業 / 物流 / 製造 / 介護 のどこから着手するか)
4. **「労働」と「修 / 護 / 献」の判定**を Council (Lv6) に委ねる場合、争議処理の lexicon が必要 (future ADR `etzhayyim-labor-vs-shugyou-judiciary`)

# References

- ADR-2605170900: etzhayyim/root canonical home for ADRs
- ADR-2605172000: kotoba substrate (中間排除の DB 層)
- ADR-2605172100: on-chain only payments (中間排除の決済層)
- ADR-2605172300: Kisha-Stream / Goji-Treasury (BI + asset)
- ADR-2605172600: membership ritual + 7-level ladder
- ADR-2605192115: Non-profit, donation-only, no-ads (本 ADR の経済姿勢 sub-ADR)
- ADR-2605192130: 10% Tithe redistribution (本 ADR の §1.6 再分配 sub-ADR)
- ADR-2605192145: Public Fund architecture (本 ADR の §1.5 / §1.6 受け皿)
- ADR-2605192200: IP-Free-Release + Charter Compliance Rider (本 ADR の §1.5 ライセンス sub-ADR)
- ADR-2607061700: 伝道 (Active Evangelism Doctrine) — 本 ADR §1.16 の起票根拠・Alternatives 正本
- CLAUDE.md (repo root): operating entity identity
- `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/charter.json` — 将来この ADR から派生する Lexicon
