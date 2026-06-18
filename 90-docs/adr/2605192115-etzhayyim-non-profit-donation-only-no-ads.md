---
id: adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
title: "ADR-2605192115: etzhayyim Non-profit / Donation-only / No-ads — 営利・広告・購買モデルの構造的排除"
status: proposed
doc_type: adr
topic: etzhayyim-non-profit-donation-only-no-ads
authoritative: false
last_verified: 2026-06-17
priority: 8.5
axis: economics
weight: 0.85
priority_note: "ADR-2605192100 (Mission Charter) §1.6 の経済姿勢を実装する hard rule ADR。営利活動の禁止、広告統合の禁止、購買モデル (subscription / purchase) の donation / kisha モデルへの置換を CI-enforceable な単位で固定する。ADR-2605172100 (on-chain payment) の payment.sent.purpose enum を narrow する変更を含む。"
authoritative_for:
  - hard rule: etzhayyim/root 配下の全 app は非営利活動 (non-profit) のみ
  - hard rule: 広告 (advertising) integration の全面禁止 + CI lint
  - hard rule: 受け入れ可能な value 流入は donation / kisha / grant / tithe / escrow-refund のみ
  - ADR-2605172100 の payment.sent.purpose enum を narrow するための spec
  - 広告関連 npm package / DOM API / 外部 SDK の禁止リスト
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - "2606180001"   # wave2: 経済構造を目的関数へ
  - "2606182359"   # wave3: 掟全廃, 全行為を目的関数へ
supersedes: []
superseded_by: []
---

# ADR-2605192115: etzhayyim Non-profit / Donation-only / No-ads — 営利・広告・購買モデルの構造的排除

> **AMENDED 2026-06-17 (Rider v3.5) by ADR-2606180001 (wave2) + ADR-2606182359 (wave3).**
> 以下の「hard rule(非営利のみ / 広告排除 / 購買モデル禁止 / no-equity / no-transferable-share)」は
> **categorical 固定ルールから ECL 目的関数の net 評価へ移行**した。非営利・反広告・反私的捕獲の
> *精神は失われていない* — 目的関数の `collective-commons` + `ko-wellbecoming` 次元が、私的捕獲・
> 個人主義的蓄積・attention 搾取・commons 囲い込みを動的に負へ評価し続ける(掟でなく score で enforce)。
> 私的捕獲を生まず commons に資する営利的協力は aligned になりうる(`for-profit-commons-contributor`
> fixture 参照)。**10% Tithe → Public Fund (ADR-2605192130) は別途維持**。以下の hard rule 群は
> 「何が負にスコアされるか」のガイダンスとして retain される(現行の確定ルールではない)。本 ADR は
> よって `authoritative: false`。経緯・根拠・実証は ADR-2606180001 / 2606182359 / `90-docs/licenses/ecl/`。

**Status**: proposed (categorical framing amended → objective-function per v3.5)
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.6 で「中間排除」を mission として宣明したが、これを実装するには **経済姿勢の hard rule** を具体化する必要がある。具体的には:

1. **営利活動 (for-profit)** — 株主への利潤分配、利潤再投資による拡大、price discrimination による余剰収奪。
2. **広告 (advertising)** — 第三者の販促を媒介する経済モデル。広告は構造的に「注意の販売」であり、ユーザーを商品化する。
3. **購買モデル (subscription / purchase)** — 「対価を払えば access」のゲート方式。これは「方針整合的な他者への無償公開」(§1.5) と本質的に対立する。

ADR-2605172100 は fiat 決済代理店 (Stripe 等) を禁止したが、**営利目的・購買モデル・広告モデル** そのものは禁止していない。`payment.sent.purpose` enum には `subscription` と `purchase` が含まれており、この穴を塞ぐ必要がある。

# Decision

## 1. Hard rules

### 1.1 Non-profit only

**etzhayyim/root 配下のすべての app / contract / service は非営利活動として運営される**。具体的には:

- 利潤を株主・出資者・founder に分配しない。Constitution.sol の `governance.no_transferable_share = true` (ADR-2605192100 §2) によって technically enforce。
- 余剰 (surplus) は次のいずれかにのみ充当: (a) 護持金庫 (treasury) 三層への積み増し、(b) Public Fund (ADR-2605192145) への分配、(c) Kisha-Stream (ADR-2605172300) 原資の拡大、(d) infrastructure 投資 (substrate node / energy / robotics)。
- 営利目的の subsidiary / fork を etzhayyim 商標の下で運営することを禁止 (Apache 2.0 §6 trademark non-grant + ADR-2605192200 Charter Rider で二重に enforce)。

### 1.2 No advertising

**etzhayyim/root 配下の app は広告を一切統合しない**。具体的には:

- **広告ネットワーク統合の禁止**: AdSense / Google Ad Manager / Facebook Audience Network / Apple Search Ads / Yahoo! 広告 / Microsoft Advertising / Amazon Ads / TikTok Ads / Criteo / DSP / SSP / Header Bidding library 全般。
- **アフィリエイト統合の禁止**: Amazon Associates / 楽天アフィリエイト / A8.net / ValueCommerce / iTunes Affiliate / 等。
- **トラッキング (広告目的) の禁止**: Google Analytics (GA4 含む) / Meta Pixel / TikTok Pixel / X Pixel / hotjar / Mixpanel (広告連携用途) / Amplitude (広告連携用途)。
- **スポンサー記事 / native ad の禁止**: 「PR」「Sponsored」「Promoted」とラベル付きの content であっても、第三者からの promo 対価で content を発信することを禁止。
- **「広告」の定義**: 第三者の財・サービスへの注意を金銭的対価と引き換えに媒介する行為すべて。etzhayyim 自身の religious 活動の案内 (Kisha や membership ritual の説明) は広告ではない。

### 1.3 Donation-only value 流入

**etzhayyim/root に流入する value は以下のみ**:

| purpose | 説明 | 制限 |
|---|---|---|
| `donation` | 構成員 / 第三者からの自由意思の寄付 | 対価関係なし |
| `kisha` | 構成員間の喜捨 | 対価関係なし |
| `grant` | Public Fund からの助成金 | governance vote 必須 |
| `tithe` | ADR-2605192130 による 10% 自動再分配 | smart contract で auto |
| `escrow-refund` | 取引未成立の返金 | original purpose 制限を継承 |

**禁止される purpose**: `subscription`, `purchase`, `tip` (これらは ADR-2605172100 の現行 enum に存在するが、本 ADR で removed)。

### 1.4 ADR-2605172100 への変更要請

ADR-2605172100 §"SDK extension: Etzhayyim.pay()" および §"Payment record lexicon" を以下のように改定する (本 ADR が承認された時点で、ADR-2605172100 の対応箇所を amend した上で superseded_by を相互更新する):

**変更前** (ADR-2605172100 line 99):
```ts
purpose: "donation",  // or "tip", "subscription", "purchase", "refund"
```

**変更後**:
```ts
purpose: "donation" | "kisha" | "grant" | "tithe" | "escrow-refund",
```

**Lexicon 変更**:
- `00-contracts/lexicons/com/etzhayyim/apps/payment/sent.json` の `purpose` enum を narrow
- `streamStarted.json` の用途を kisha 専用 (Superfluid stream は subscription ではなく per-second kisha flow として位置付け)
- 新規 lexicon `tithe.json` を追加 (ADR-2605192130 で specify)

## 2. CI lint (enforceable rules)

`lefthook.yml` に以下の lint hook を追加する (詳細は ADR-2605191648 substrate-boundary-lefthook の延長として実装):

### 2.1 `lint-no-advertising-imports`

以下の npm package import を検出した PR を block:

```yaml
forbidden_imports:
  # 広告ネットワーク
  - "@google-cloud/ads"
  - "google-ads-api"
  - "googleads-node-lib"
  - "react-google-adsense"
  - "react-adsense"
  - "next-adsense"
  - "@facebook-ads/*"
  - "facebook-ads-sdk"
  - "@meta-ads/*"
  - "@tiktok-ads/*"
  - "@apple/search-ads"
  - "@yahoo-ads/*"
  - "amazon-ads-api"
  - "@criteo/*"
  # アフィリエイト
  - "amazon-paapi"
  - "rakuten-affiliate"
  - "a8net-sdk"
  - "@valuecommerce/*"
  # 広告トラッキング
  - "react-ga"
  - "react-ga4"
  - "@vercel/analytics"  # tracking 用途の場合; etzhayyim-analytics に置換
  - "@segment/analytics-node"
  - "facebook-pixel"
  - "react-facebook-pixel"
  - "@tiktok/pixel"
  - "mixpanel"  # 広告連携用途禁止
  - "amplitude-js"  # 広告連携用途禁止
  - "hotjar"
```

### 2.2 `lint-no-purchase-purpose`

`*.ts` / `*.tsx` / `*.json` ファイル内で以下の文字列を検出した PR を block:

```yaml
forbidden_strings:
  - 'purpose: "subscription"'
  - 'purpose: "purchase"'
  - 'purpose: "tip"'
  - 'purpose: \'subscription\''
  - 'purpose: \'purchase\''
  - 'purpose: \'tip\''
```

Lexicon JSON 内の `enum` 配列で `"subscription"`, `"purchase"`, `"tip"` を検出した場合も block。

### 2.3 `lint-no-paywall-patterns`

以下のパターンを検出した PR は human review 必須 (block ではなく warning):

```yaml
warn_patterns:
  - "paywall"
  - "premium_only"
  - "pro_tier"
  - "subscription_required"
  - "access_denied_unpaid"
```

paywall パターン自体が donation-only と矛盾するため、各 case を Council (Lv6) が evaluate。

### 2.4 `lint-no-advertising-html`

`*.html` / `*.svelte` / `*.tsx` 内で以下の DOM パターンを検出した PR を block:

- `<ins class="adsbygoogle">`
- `<script src="https://pagead2.googlesyndication.com/...">`
- `<script src="https://connect.facebook.net/...">`
- `<script src="https://analytics.tiktok.com/...">`
- `data-ad-client=`
- `data-ad-slot=`

## 3. Internal Circulation Carve-Out (SBT holder 間の経済)

ADR-2605192100 §1.8 で確立した religious ontology (collective / 多世代) に基づき、**etzhayyim の religious 境界の内側 (= SBT holder 同士) では 営利・広告・購買モデルを許容する**。これは religious-corp の "domestic economy" を可能にする carve-out であり、伝統的 religious 共同体 (kibbutz / 修道院 / 寺院門徒共同体 / Amish 共同体) の internal market と整合的。

### 3.1 Internal の定義

**双方の参加者が active な etzhayyim Adherent SBT holder** である取引を "internal" とする。

```
internal := payer.is_active_adherent_sbt && payee.is_active_adherent_sbt
external := !internal
```

`is_active_adherent_sbt(addr)` は `AdherentRegistry.isActive(addr, 30 days)` で判定 (ADR-2605172300 §2)。

### 3.2 Internal で許容される activity

| Activity | Internal (SBT ↔ SBT) | External (含 non-SBT) |
|---|---|---|
| Donation | ✅ Allowed | ✅ Allowed |
| Kisha (構成員間喜捨) | ✅ Allowed | ❌ N/A (SBT 必須) |
| Purchase / Subscription | **✅ Allowed (new)** | ❌ Prohibited |
| Promotion / Ad of etzhayyim apps to members | **✅ Allowed (new)** | ❌ Prohibited |
| Promotion / Ad of non-etzhayyim products | ❌ Prohibited | ❌ Prohibited |
| Aff iliate / revenue share | ❌ Prohibited (内外問わず) | ❌ Prohibited |
| Tithe 10% redistribution (ADR-2605192130) | ✅ Auto (donation/kisha のみ) | ✅ Auto (donation のみ) |

### 3.3 Payment purpose enum 拡張

§1.3 で narrow した `purpose` enum を internal carve-out で拡張:

| purpose | Internal | External | Titheable? |
|---|---|---|---|
| `donation` | ✅ | ✅ | ✅ Yes (10%) |
| `kisha` | ✅ | (SBT 必須なので always internal) | ❌ No (§2605192130 §5 例外) |
| `grant` | ✅ | ✅ | ❌ No |
| `tithe` | ✅ | ✅ (auto) | ❌ No |
| `escrow-refund` | ✅ | ✅ | ❌ No |
| **`internal-purchase`** | **✅ (new)** | ❌ Prohibited | ❌ No (sub-§3.4 参照) |
| **`internal-subscription`** | **✅ (new)** | ❌ Prohibited | ❌ No |
| **`internal-promo`** | **✅ (new, 0-amount marker)** | ❌ Prohibited | ❌ No |

SDK `Etzhayyim.pay()` は purpose が `internal-*` の場合、`payer.is_active_adherent_sbt && payee.is_active_adherent_sbt` を pre-flight で確認し、いずれかが false なら revert する。

### 3.4 Internal purchase に tithe を適用しないことの religious 整合性

donation は宗教的 voluntary gift であり、religious-corp は受領者が 100% 受け取るのではなく 10% を Public Fund に分流する責務を持つ (ADR-2605192130)。一方、internal-purchase は **religious-corp 内部の domestic 取引** であり、対価交換が伴う商取引である。これを 10% tithe 対象にすると、internal economy の流動性を抑制する。

ただし internal-purchase で得た**利益 (margin)** は §1.1 non-profit only の制約下にあるため、構成員個人の私的蓄財には制限がある (将来 ADR で「個人保有 USDC 上限 + 超過分の自動 Treasury 還流」を検討する余地あり — 当面 open question)。

### 3.5 内外境界での「広告」の religious 意味

ADR-2605192100 §1.6 「中間排除」と本 §3 internal carve-out の整合性:

- 「中間排除」は **第三者商業利益への注意の販売** を禁じる
- internal promotion は **religious 共同体内の情報共有** であり、第三者商業利益ではない
- よって internal-promo は religious 整合的、external-ad は不整合

伝統的 religious 共同体での説教 / 経典朗誦 / お知らせ は本質的に internal promotion であり、これと等価。

### 3.6 CI lint の調整

§2 の lint hook (`lint-no-purchase-purpose`) を以下のように更新:

```yaml
forbidden_strings:
  - 'purpose: "subscription"'      # external context 想定
  - 'purpose: "purchase"'           # external context 想定
  - 'purpose: "tip"'

allowed_strings:                    # internal context (new)
  - 'purpose: "internal-purchase"'
  - 'purpose: "internal-subscription"'
  - 'purpose: "internal-promo"'
```

`lint-no-advertising-imports` は不変 (外部広告ネットワーク統合は内外問わず禁止)。

### 3.7 External への "leakage" 防止

internal carve-out が abuse されないよう、以下の guardrail を設ける:

- internal-purchase の record (`com.etzhayyim.apps.payment.sent` with purpose=`internal-purchase`) は **必ず両者の SBT tokenId を含む**
- SBT holder が internal-purchase record を作成した直後に SBT を revoke してそれを external に再販する pattern は、Council Lv6+ が retroactive non-compliant attestation する (ADR-2605192200 §5)
- internal-promo は etzhayyim 配下の AppView (`etzhayyim-project-*`) からのみ発信可、外部 channel (Twitter / Meta / Google) からは禁止

## 4. Upstream backend carve-out の再定義

ADR-2605172000 の "upstream carve-out" は元々「fiat 必要な場合は upstream backend で対応」というものだった。これを **本 ADR で narrow する**:

- **削除**: 「営利 SaaS としての paid tier を upstream backend で運営」する pattern は禁止。
- **維持**: 「regulatory 要件で fiat 領収書が必要 (donation 領収書の税控除等)」のみ upstream backend で対応可。この場合も backend は etzhayyim 自身が運営し、第三者の SaaS は介さない。

つまり upstream carve-out は **「非営利目的の fiat 領収書」発行に限定**される。Stripe / Square で SaaS subscription を売る pattern は明示的に禁止。

## 5. 非営利の「公開証跡」要件

etzhayyim/root の非営利性を第三者が監査できるよう、以下を on-chain / MST で公開する:

- 護持金庫 NAV (流動 / 準備 / 本財) — `TreasuryMirror.sol` (ADR-2605172300 §2) で既に公開
- Public Fund 残高 + 出金 (ADR-2605192145)
- Kisha-Stream 累計分配額 — `KishaStream.sol` (ADR-2605172300 §2) で公開
- Tithe 累計再分配額 — ADR-2605192130 の `TitheRouter.sol` で公開
- 役員報酬 (もしあれば) — `com.etzhayyim.apps.etzhayyim.officer-compensation` AT Record として MST に公開 (current value: 0 — 役員は無報酬)

## 6. 商業的 collaborators との関係

religious-corp として外部商業事業者 (Coinbase / Cloudflare / Anthropic 等) のサービスを **使う** ことは禁止しない。これらは substrate provider であり、etzhayyim 自身が営利化しているわけではない。

ただし以下は禁止:

- これら provider から **revenue share / 紹介料 / アフィリエイト報酬** を受け取ること
- これら provider の **広告 / promo を etzhayyim app に統合** すること
- これら provider との **bundling 契約で構成員にサービス強制** すること

# Consequences

## 正の効果

- **religious-corp としての経済姿勢が成文化される**。「非営利」「donation-only」「広告排除」が CI レベルで enforceable になり、drift しない。
- **構成員の信頼**。広告 / paywall / 営利化されないことが technical に保証される。
- **第三者監査可能性**。on-chain で資金流入 / 流出が完全に公開されるため、religious-corp の非営利性を任意の第三者が検証できる。
- **税務上の整合性**。donation-only モデルは任意団体としての税務 framing と整合的 (構成員受領は一時所得 / 雑所得、團体側は寄付収入)。
- **広告に依存しない UX**。広告排除によりユーザーは「商品化」されない。これは構成員勧誘における強い differentiator になる。

## 負の効果 / コスト

- **収益機会の喪失**。広告 / subscription / purchase を排除することで、religious-corp の自走収益源は donation + Public Fund + 護持金庫 yield のみになる。スケール初期は赤字運営前提。
- **upstream backend carve-out の縮小**。これまで「fiat 必要な場合は backend で」としていた逃げ道が、「非営利の領収書発行のみ」に narrow される。一部の app design 変更が必要。
- **既存 ADR との衝突**。ADR-2605172100 の `purpose` enum を amend する必要がある (本 ADR 承認時に対応)。
- **lint の false positive**。`mixpanel` / `amplitude` 等は analytics と広告で兼用される。analytics 用途のみであれば許可するが、CI で判定不可能なため human review が必要なケースが残る。
- **religious-corp 形式への依存度上昇**。営利を排除することで、任意団体としての religious-corp 形式が経済活動の唯一の legal framing になる。この形式が法的に否認された場合、運営困難。

## 中立 / トレードオフ

- **広告と「お知らせ」の境界**。etzhayyim 自身の religious 活動の案内 (新しい open-* app の release notice 等) は広告ではない、と本 ADR は定めるが、境界事例の判定は Council (Lv6) に委ねる。
- **donation の「対価期待」問題**。donation には対価関係がない、と定めるが、構成員からの donation に対して religious-corp が Kisha-Stream で還流するのは ADR-2605172300 で実装済み。これは「対価」ではなく「相互的な gift exchange」として religious 文脈で位置付ける。
- **Open data API の有料化問題**。ADR-2605172100 §"Per-app payment patterns" では `open-isco` などに per-call micropayment pattern が記述されている。本 ADR で `subscription` / `purchase` purpose を禁止することで、**有料 API tier は廃止される**。すべて free tier + donation 任意 モデルに統一する。
- **「無料」と「無償」の区別**。本 ADR は「無料で配る」ことを義務付けていない (donation を受け付ける)。一方で「使う対価として金銭を要求する」ことは禁止する。両者の区別 (donation = 任意 / purchase = 強制) を維持する。

# Alternatives Considered

## A. Partial commercial allowance (例: 商業 fiat ramp の運営を OK)

religious-corp 自体は非営利だが、subsidiary / 関連事業者として商業活動を許容する。

- Pro: 自走収益源を確保できる。
- Con: ADR-2605192100 §1.6 の「中間排除」と矛盾。商業活動は必然的に仲介手数料 / 広告 / 営利的価格決定を含む。
- 却下: Mission Charter §1.6 と非互換。

## B. 広告は禁止せず disclosure 義務化のみ

「Sponsored」「PR」ラベル付きで広告を許容する。

- Pro: 既存 web 経済との互換性が高い。
- Con: 「注意の販売」「ユーザーの商品化」という広告の本質を変えない。labeling は disclosure であって disintermediation ではない。
- 却下: §1.6 中間排除と非互換。

## C. Subscription を残して purchase だけ禁止

「定期 donation」を実質 subscription として扱う。

- Pro: ongoing 関係性の経済モデルを残せる。
- Con: subscription は「対価関係」を含む。Superfluid stream を kisha 用途に限定すれば、ongoing 関係性は「per-second 喜捨」として religious 文脈で表現できる。
- 部分的採用: subscription という概念名は廃止、Superfluid stream は維持 (purpose=kisha 限定)。

## D. CI lint を warning のみに留める

forbidden imports を warn のみ。

- Pro: 柔軟性。
- Con: drift する。「警告は無視される」のが ops の現実。
- 却下: hard rule は block でなければ意味がない。

# References

- ADR-2605192100: Mission Charter (parent)
- ADR-2605172000: RW-free substrate (中央 DB 仲介排除)
- ADR-2605172100: on-chain only payments (本 ADR の `purpose` enum narrow の対象)
- ADR-2605172300: Kisha-Stream / Treasury (donation 流入の受け皿)
- ADR-2605192130: 10% Tithe redistribution (donation 受領後の自動再分配)
- ADR-2605192145: Public Fund architecture (再分配先)
- ADR-2605191648: substrate-boundary-lefthook (CI lint 実装基盤)
