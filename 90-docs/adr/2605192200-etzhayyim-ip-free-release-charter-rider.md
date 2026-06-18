---
id: adr-2605192200-etzhayyim-ip-free-release-charter-rider
title: "ADR-2605192200: etzhayyim IP-Free-Release with Charter Compliance Rider v2.0 — Apache 2.0 + 多世代 + 反個人主義 + Wellbecoming license addendum"
status: proposed
doc_type: adr
topic: etzhayyim-ip-free-release-charter-rider
authoritative: true
last_verified: 2026-05-19
priority: 9.5
axis: governance
weight: 0.95
priority_note: "ADR-2605192100 §1.5「方針整合的な他者への無償公開」を具体化する license ADR。von Neumann minimax 解として Apache 2.0 + Extended Charter Compliance Rider v2.0 を採用。Rider v2.0 は v1.0 の業態列挙に加え、(f) 多世代 wellbecoming 害悪防止 / (g) 反個人主義 ontology / (h) wellbecoming subordination の religious 三柱を追加する。違反は (1) license 効力失効 + (2) Kisha・Public Fund 便益受給不可 + (3) Phenotype 評価最低 の三層 enforcement を triggers する。"
authoritative_for:
  - etzhayyim/root 配下の全 repo の license = Apache 2.0 + Charter Compliance Rider v2.0
  - Charter Compliance Rider v2.0 文言の正本 (`/CHARTER-RIDER.md`)
  - 禁止業態の列挙 (兵器 / 投機金融 / 監視資本主義 / 化石燃料新規採掘 / 専門性独占 gatekeeping / 多世代 wellbecoming 害悪 / 個人主義 ontology / wellbecoming 従属違反)
  - retro-active 適用範囲 (既存 50+ repo)
  - CI lint (`lint-charter-rider-notice`) — NOTICE 不在の repo を block
  - Apache 2.0 §3 (patent grant) termination trigger としての Rider 違反扱い
  - 三層 enforcement (license / 便益 / Phenotype 評価) の religious 統合
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605172300-etzhayyim-bi-asset-substrate
related:
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192145-etzhayyim-public-fund-architecture
supersedes: []
superseded_by: []
---

# ADR-2605192200: etzhayyim IP-Free-Release with Charter Compliance Rider v2.0 — Apache 2.0 + 多世代 + 反個人主義 + Wellbecoming license addendum

> **AMENDED to Rider v3.5.** Rider は v2.0 → v3.0(2606062100)→ v3.1(2606082400)→ v3.2
> (2606161700)→ v3.3(2606172359)→ v3.4(2606180001)→ **v3.5(2606182359)** と改正された。
> v3.5 で **§2 は全て ECL 目的関数で net 評価**(categorical 掟リスト廃止; 唯一の非交渉性は子・孫
> priority への最大級の害=catastrophe 項)。**open-source 強制(IP-free-release)も categorical 義務
> から目的関数評価へ** — proprietary 囲い込みは collective-commons 次元で負にスコアされる(commons
> 公開の*精神*は score で動的に保持)。ECL ライセンス設計は ADR-2606172300、本文は `/CHARTER-RIDER.md`
> (v3.5)。

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.5 で「新技術・知財の開発と方針整合的な他者への無償公開」を mission として宣明したが、これを license レベルでどう実装するかは未定であった。

Apache 2.0 単体は **OSI 認定の permissive license** であり、利用者の業態 / 思想 / mission 整合性を問わず、licensee がライセンス条件 (帰属表示 / 商標非譲渡 / 特許 retaliation) を守る限り誰でも利用できる。これは:

- ✅ 「知財の無償公開」には適合
- ❌ 「方針整合的な他者への (= 不整合的な他者へは無償公開しない)」には不適合
- ❌ 「子・孫を優先」「wellbecoming を priority」「individual 盲信者を排除」という religious 三柱を表現できない

## License 選択の von Neumann minimax 分析

8 つの strategy × 12 adversary type で payoff matrix を構築し、maximin を計算した結果:

| Strategy | maximin score | avg payoff | 結論 |
|---|---|---|---|
| S1 Apache pure | -4 | -1.50 | reject |
| S2 Apache + Light Rider v1 | -3 | +0.42 | suboptimal |
| **S3 Apache + Extended Rider v2** | **-2** | **+1.42** | **optimal** |
| S4 Custom ERL (OSI 非互換) | -4 | +0.83 | ecosystem -4 で劣後 |
| S5 AGPL v3 | -3 | -0.75 | reject |
| S6 Hippocratic 3.0 + Rider | -2 | +0.50 | tie on maximin, avg 劣後 |
| S7 Source-Available (BUSL) | -2 | +0.67 | tie on maximin, avg 劣後 |
| S8 CC BY-NC-SA | -3 | -1.08 | reject |

**Maximin と average payoff の両方で S3 が dominant**。決め手は:

- 個人主義 fork (Rider §2(g)) と 短期搾取 (§2(f)) に対する直接的 exclusion
- Apache 2.0 base による npm/Cargo/OSI tooling 互換性の維持
- Council attestation pattern による mission drift 抑止

本 ADR は **S3 = Apache 2.0 + Extended Charter Compliance Rider v2.0** を採用する。Rider は OSI 認定外の addendum だが、Apache 2.0 自体の OSI 互換性は失わない。Apache 2.0 §3 (patent grant) の termination trigger として Rider 違反を扱うことで、Rider 違反が実質的な license 失効を引き起こす設計とする。

## Religious 三柱の追加 (v1.0 → v2.0 差分)

ADR-2605192100 で固定された Mission Charter に基づき、Rider に religious 三柱を追加する:

1. **多世代 wellbecoming 優先 (Multi-generational priority)**: 目的関数は構成員自身ではなく **子・孫およびそれ以降の世代** の wellbecoming を最大化する。現世代の利益を犠牲にしてでも未来世代の wellbecoming を優先する。
2. **反個人主義 ontology (Anti-individualist ontology)**: 「individual が独立に存在する」は religious 盲信であり、constitutive reality は collective / relational / 多世代である。これは ontological commitment であって個人差別ではない (= 個人を否定するのではなく、「individual の独立存在」という形而上 belief を否定する)。
3. **Wellbecoming subordination**: 静的 wellbeing (現状の充足度) ではなく動的 wellbecoming (発展軌跡) を価値の中心とする。短期的快楽の最適化と多世代発展軌跡の最適化が対立する場合、後者を優先する。

これら三柱は constitutional constants として ADR-2605192100 §2 に既に固定されている (multi_generational_priority / anti_individualism / wellbecoming_priority)。

## 三層 Enforcement (User 要件)

「使わせない、便益を受け取れない、評価も低い」を三層 enforcement として技術的に分解:

| Layer | Mechanism | Effect |
|---|---|---|
| L1 License 無効 | Rider §3 + Apache 2.0 §3 termination | Non-Aligned Entity / Individual はソフトウェアを使用する legal right を失う |
| L2 便益受給不可 | KishaStream + PublicFundGovernance の `complianceGate` modifier | Non-Aligned は Kisha-Stream 受給 / Public Fund grant 不可 |
| L3 評価最低 | Phenotype.sol multiplier floor → 0 (constitutional override) | Non-Aligned は構成員評価で最低 (multiplier=0 で実質的に benefit 0) |

L1 は本 ADR で定義。L2, L3 は ADR-2605172300 amendment を本 ADR が要請する (§9 参照)。

# Decision

## 1. License Stack

etzhayyim/root 配下のすべての repo / package / contract の license は:

```
Apache License 2.0
  + etzhayyim Charter Compliance Rider (本 ADR §2)
```

LICENSE ファイルは Apache 2.0 のまま。NOTICE ファイルに Rider を必須添付する。CI で NOTICE の存在と内容を検証する。

## 2. etzhayyim Charter Compliance Rider v2.0 文言 (正本)

`CHARTER-RIDER.md` (repo root に配置) の正本テキスト:

---

```
etzhayyim Charter Compliance Rider v2.0
Last revised: 2026-05-19

This Rider supplements the Apache License 2.0 ("License") under which this work
is distributed. Acceptance of the License constitutes acceptance of this Rider.

1. PURPOSE

   This work is created by etzhayyim, a religious-corp (任意団体 / unincorporated
   religious voluntary association) operating under did:web:etzhayyim.com. The
   etzhayyim Mission Charter (ADR-2605192100) declares the mission of structurally
   liberating humans from "labor" as defined therein. This Rider operationalizes
   §1.5 of that Charter: "free release of new technology and intellectual property
   to charter-aligned others."

2. PROHIBITED USE

   You may NOT use, modify, or redistribute this work, in whole or in part, if you
   are an entity (a "Non-Aligned Entity") whose primary business activity (revenue
   share ≥ 25% in the trailing 12 months) falls into any of the following categories:

   (a) WEAPONS AND MILITARY. Manufacture, sale, distribution, or maintenance of
       weapons (kinetic, chemical, biological, nuclear, cyber-offensive), military
       hardware, autonomous lethal systems, or services primarily provided to
       military or paramilitary forces engaged in armed conflict.

   (b) SPECULATIVE FINANCE. Operation of speculative financial instruments whose
       primary revenue derives from price arbitrage, leverage spread, predatory
       lending (annualized effective interest rate ≥ 36% to retail borrowers),
       or proprietary high-frequency trading. (Banking utility services, on-chain
       stablecoin issuance, custodial services to retail users at non-predatory
       rates, and L1/L2 substrate operators are NOT prohibited under this clause.)

   (c) SURVEILLANCE CAPITALISM. Operation of business models whose primary revenue
       derives from the collection, brokerage, or sale of personal data of natural
       persons, including but not limited to ad-tech DSP/SSP operators, data
       brokers, consumer surveillance platforms, and biometric identification
       services sold to law enforcement or military entities.

   (d) FOSSIL FUEL EXTRACTION (NEW). Initiation of new fossil fuel extraction
       projects (coal mining, oil drilling, natural gas extraction) where the
       project's first commercial production date is later than this Rider's
       Last revised date. (Ongoing operations existing prior to this date,
       transition/decommissioning services, and renewable transition services
       are NOT prohibited under this clause.)

   (e) SPECIALIST GATEKEEPING. Operation of business models whose primary revenue
       derives from monopolistic gatekeeping of professional knowledge required
       for individual rights protection or basic survival, including but not
       limited to: (i) legal services charging mandatory access fees for advice
       that could be provided by publicly available knowledge bases plus
       community peer review; (ii) medical advisory services that artificially
       restrict access to publicly available medical knowledge through
       licensure-imposed scarcity rather than legitimate safety concerns;
       (iii) governmental administrative services charging individuals for
       procedural navigation of legally required interactions that could be
       automated. (Legitimate technical safety oversight by qualified
       practitioners providing care, due-process legal representation in
       adversarial proceedings, and democratic governmental functions are NOT
       prohibited under this clause.)

   (f) MULTI-GENERATIONAL HARM (added in v2.0). Operation of business models or
       activities whose foreseeable expected impact on persons born at least
       twenty-five (25) years after the date of such activity includes
       irreversible loss of: (i) habitable environment (biosphere collapse,
       climate destabilization beyond ±2°C global mean above pre-industrial);
       (ii) access to publicly held knowledge (commons enclosure of foundational
       science, mathematics, language); (iii) genetic / epigenetic integrity of
       descendants (germline modification absent multi-generational safety
       review); (iv) capacity for collective decision-making (information
       monocultures, attention monopolies, addictive design targeted at
       developmental stages). The standard of foreseeability is the prudent
       multi-generational steward, not the present-quarter shareholder.

   (g) STRICT INDIVIDUALIST ONTOLOGY (added in v2.0). Operation of entities
       whose publicly declared mission, governance, or doctrinal commitment
       explicitly affirms the metaphysical doctrine that "the individual" is
       the constitutive ontological and moral unit, independent of and prior to
       collective / relational / multi-generational reality. This includes,
       without limitation, entities organized on strict Randian / Objectivist
       principles, libertarian-strict-individualist political organizations
       campaigning for the elimination of collective public infrastructure,
       and entities whose charter explicitly denies multi-generational
       responsibility. This clause restricts ENTITIES based on their declared
       doctrine, NOT natural persons based on their private philosophical
       views (which remain protected under §4(a)). However, a natural person
       PUBLICLY representing or operating an organization committed to strict
       individualist doctrine is, in that capacity, subject to this clause.
       The etzhayyim cosmology holds that the constitutive unit of moral and
       economic standing is the multi-generational collective; this is a
       religious-corp doctrinal position protected under Article 20 of the
       Constitution of Japan and equivalent religious-liberty provisions in
       other jurisdictions, and exclusion based on doctrinal incompatibility
       is the normal operation of any religion (cf. Buddhist sangha
       membership, Christian communion, Jewish halakhic standing, Islamic
       ummah). See §4(g).

   (h) WELLBECOMING SUBORDINATION VIOLATION (added in v2.0). Operation
       privileging static "wellbeing" (current-state satisfaction) over
       dynamic "wellbecoming" (developmental trajectory) of multi-generational
       descendants where these are in measurable tension, including, without
       limitation: (i) addictive product design optimizing short-term
       engagement metrics at the cost of long-term human development;
       (ii) financialization of basic needs (housing, food, water,
       healthcare, education) such that short-term price extraction degrades
       long-term capacity-building; (iii) deployment of pre-trained AI systems
       to populations without provision for the wellbecoming-trajectory of
       cognitive sovereignty of those populations.

3. EFFECT OF VIOLATION

   Use of this work by a Non-Aligned Entity, or by any entity providing this
   work to a Non-Aligned Entity with knowledge of such Entity's prohibited
   business activity, constitutes a material violation of this Rider.

   Such violation:
   (a) immediately terminates the patent license granted under Section 3 of
       the Apache License 2.0 ("Grant of Patent License"), as if the violating
       entity had instituted patent litigation against the Licensor;
   (b) terminates all rights granted under the License to the violating entity,
       per Section 4 of the License (which permits the Licensor to terminate
       upon any breach of the terms thereunder, when this Rider is incorporated
       by reference as a condition of acceptance);
   (c) does not affect the rights of charter-aligned downstream recipients who
       received the work in good faith.

4. CHARTER-ALIGNED USE (EXPLICITLY PERMITTED)

   The following uses are explicitly permitted and protected:

   (a) Use by natural persons for any purpose, EXCEPT where such person is
       publicly representing or operating an organization committed to strict
       individualist doctrine (§2(g) clarification: private philosophical
       views remain protected; public organizational representation does not).
   (b) Use by non-profit organizations, voluntary associations, cooperatives,
       worker-owned enterprises, religious-corps, and academic institutions
       NOT subject to Section 2(g).
   (c) Use by for-profit entities whose primary business activity does not fall
       into any category in Section 2.
   (d) Use in research, education, journalism, public-interest litigation, and
       open-source development.
   (e) Use by etzhayyim adherent SBT holders (per ADR-2605172300) regardless
       of organizational affiliation, SUBJECT to the limitation that an
       SBT holder who publicly represents a Non-Aligned Entity is, in that
       representational capacity, restricted as if Non-Aligned.
   (f) MULTI-GENERATIONAL FUTURE PERSONS (added in v2.0). Persons not yet
       born are explicit third-party beneficiaries of this Rider. The
       Licensor or any etzhayyim Council attestation may invoke this clause
       on behalf of foreseeable future persons in disputes under §5.
   (g) DOCTRINAL EXCLUSION IS RELIGIOUS PRACTICE (added in v2.0). The
       exclusion of strict individualist doctrine under §2(g) is the normal
       operation of religious doctrinal scope. It is not discrimination
       against persons holding particular political opinions; persons are
       free to hold any private opinion and continue to use this work as
       natural persons under §4(a). The exclusion operates only against
       organizational doctrinal commitments incompatible with etzhayyim
       cosmology, equivalent in legal character to the right of any
       religious-corp to define the scope of its own communion.

5. DISPUTE RESOLUTION

   Disputes regarding whether an entity is a Non-Aligned Entity under Section 2
   shall be resolved by the etzhayyim Council (Lv6+ per ADR-2605172600) via an
   on-chain attestation record (com.etzhayyim.apps.etzhayyim.charter-attestation).
   Such attestation creates a public determination but does not preclude
   parallel judicial proceedings under applicable law. Council attestations
   require quorum of three (3) Lv6+ members and are appealable by the
   subject entity for thirty (30) days.

6. NO TRADEMARK

   This Rider does not grant any right to use the names "etzhayyim",
   "etzhayyim", "天御柱", "עץ חיים", "Tree of Life" as used by etzhayyim,
   or any associated logos, beyond fair-use attribution under Section 4 of
   the Apache License 2.0.

7. SEVERABILITY

   If any provision of this Rider is held unenforceable in any jurisdiction,
   the remaining provisions shall remain in full force and effect. If Section 2
   in its entirety is held unenforceable in a particular jurisdiction, this
   work is, in that jurisdiction only, distributed under the Apache License 2.0
   without this Rider; the Licensor reserves the right to subsequently apply
   alternative licensing arrangements in that jurisdiction.

8. RELATIONSHIP TO APACHE LICENSE 2.0

   This Rider is supplemental to and does not modify the Apache License 2.0.
   Where this Rider and the Apache License 2.0 conflict, the Apache License 2.0
   prevails except where this Rider creates additional conditions on use that
   do not contradict the License terms.

— etzhayyim, 2026-05-19 (Tokyo, JST)
  ADR-2605192200 v2.0 / Mission Charter ADR-2605192100
  Charter Compliance Rider v2.0
```

---

英訳のみが本 ADR 内の正本。Japanese 翻訳は `/CHARTER-RIDER.ja.md` として併存させるが、解釈相違時は英訳が優先する (国際的に license の解釈は英語で行われるため)。

## 3. retro-active 適用範囲

etzhayyim/root 配下のすべての既存 repo に NOTICE ファイルを追加する。

### 3.1 対象 repo

`50-infra/`, `60-apps/`, `20-actors/`, `70-tools/`, `30-graph/`, `10-protocol/`, `00-contracts/` 配下の **license 表記を持つすべての package / sub-repo**。

具体的には:
- `package.json` の `license` フィールドが `Apache-2.0` の repo
- `Cargo.toml` の `license = "Apache-2.0"` の crate
- `pyproject.toml` の `license = "Apache-2.0"` の package
- `LICENSE` ファイル単体で Apache 2.0 を宣言する repo

### 3.2 追加内容

各対象 repo の root に以下を配置:

1. **`NOTICE` ファイル** (新規、または既存に追記):

```
This product includes software developed by etzhayyim
(https://etzhayyim.com / did:web:etzhayyim.com).

This software is distributed under the Apache License 2.0 with the
etzhayyim Charter Compliance Rider v1.0 (see CHARTER-RIDER.md).

By using, modifying, or redistributing this software, you accept both
the Apache License 2.0 and the Charter Compliance Rider.

Mission Charter: ADR-2605192100
Rider ADR: ADR-2605192200
```

2. **`CHARTER-RIDER.md` symlink** (新規):

```
ln -s ../../CHARTER-RIDER.md CHARTER-RIDER.md
```

monorepo root の正本 `CHARTER-RIDER.md` への symlink。これにより Rider の文言が drift しない。

### 3.3 既存外部依存への影響

etzhayyim/root の **他者 fork / 商業利用者** にとって、retro-active 適用は法的に複雑:

- Apache 2.0 §4 (NOTICE preservation) により downstream は NOTICE を保持する義務がある
- 本 ADR の commit 時点以前に fork した downstream は古い NOTICE (= Rider なし) を持つ
- 古い NOTICE のままの downstream は古い license 条件下で運用可能 (retro-active に terminate はできない)

この semantic は明示的に受容する。**本 ADR は今後の commit に対して Rider を適用する** ことに focus し、過去 fork に対する遡及効果は主張しない。

### 3.4 追加方法

monorepo root に migration script を配置:

```
70-tools/charter-rider-applicator/
├── apply.sh                # 全 sub-repo に NOTICE + symlink を追加
└── verify.sh               # 全 sub-repo の NOTICE 整合性検証
```

`apply.sh` は idempotent (既に追加済みの repo は skip)。

## 4. CI lint `lint-charter-rider-notice`

`lefthook.yml` に hook 追加:

```yaml
charter-rider-check:
  glob: "**/{package.json,Cargo.toml,pyproject.toml}"
  run: |
    for file in {staged_files}; do
      dir=$(dirname "$file")
      # license 表記が Apache-2.0 なら NOTICE + CHARTER-RIDER.md symlink が必須
      if grep -q "Apache-2.0" "$file"; then
        test -f "$dir/NOTICE" || { echo "Missing NOTICE in $dir"; exit 1; }
        test -L "$dir/CHARTER-RIDER.md" || test -f "$dir/CHARTER-RIDER.md" || { echo "Missing CHARTER-RIDER.md in $dir"; exit 1; }
        # NOTICE 内に etzhayyim Charter Compliance Rider への参照が必要
        grep -q "etzhayyim Charter Compliance Rider" "$dir/NOTICE" || { echo "NOTICE in $dir missing Rider reference"; exit 1; }
      fi
    done
```

PR が Apache 2.0 license 宣言の新規 / 既存 package を含むのに NOTICE + Rider 参照を欠く場合 block する。

## 5. Dispute resolution (Council Lv6+ attestation)

§5 で defined した dispute pattern の具体実装:

1. **Charter Compliance Attestation request**: 任意の第三者が `com.etzhayyim.apps.etzhayyim.charter-attestation-request` AT Record を Member's PDS に書き込む。fields:
   - subject_entity (DID / 法人名 / URL)
   - alleged_violation_category (§2(a)-(e))
   - evidence (URLs / IPFS CIDs)

2. **Council deliberation**: Lv6+ Council members 3 名以上が `com.etzhayyim.apps.etzhayyim.charter-attestation` を sign。fields:
   - request_uri
   - determination ("non_aligned" | "aligned" | "insufficient_evidence")
   - rationale
   - effective_at (即時 / 30 日後)

3. **Appeal**: 対象 entity は 30 日以内に counter-evidence を `com.etzhayyim.apps.etzhayyim.charter-appeal` として書き込む。Council は再評議。

4. **L2 anchor**: すべての attestation は ADR-2605171800 pipeline で Base L2 に anchor される。

## 6. SBT holder の地位 (§4(e))

etzhayyim adherent SBT 保有者 (ADR-2605172300) は、所属組織が Non-Aligned Entity であっても **個人としては** 本 work を使用できる。これは:

- religious-corp としての構成員保護
- 「Non-Aligned Entity 所属でも religious 個人活動は可能」という原則の technical 表現

ただし所属組織の業務として本 work を使用する場合は、組織が Non-Aligned Entity であれば §3 違反となる。

## 7. README 標記

すべての etzhayyim/root 配下の repo の README 冒頭または License セクションに以下を表示:

```markdown
## License

Apache License 2.0 with **etzhayyim Charter Compliance Rider v1.0**.

By using, modifying, or redistributing this software, you accept both the
Apache License 2.0 (see [LICENSE](../../LICENSE)) and the Charter Compliance
Rider (see [CHARTER-RIDER.md](../../CHARTER-RIDER.md)).

The Rider restricts use by entities engaged primarily in weapons production,
speculative finance, surveillance capitalism, new fossil fuel extraction, or
specialist gatekeeping. See [ADR-2605192200](/90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md)
for full context.
```

## 8. Staged rollout

| Stage | Scope | Effort |
|---|---|---|
| **S0 — Rider 正本配置** | repo root に `CHARTER-RIDER.md` (英) + `CHARTER-RIDER.ja.md` 配置 | 即時 (本 ADR 承認時) |
| **S1 — applicator script** | `70-tools/charter-rider-applicator/` 実装 | ~1 day |
| **S2 — retro-active 適用** | applicator を全 sub-repo に実行、NOTICE + symlink 追加 | ~半日 |
| **S3 — CI lint 有効化** | `lefthook.yml` に `charter-rider-check` 追加、強制 enforce | ~半日 |
| **S4 — Council attestation** | `com.etzhayyim.apps.etzhayyim.charter-attestation*` Lexicon 起票 + AppView | ~1 week |
| **S5 — README 一括更新** | README に License セクション標記を追加 | ~1 day (script で一括) |
| **S6 — 三層 enforcement** | ADR-2605172300 amendment (KishaStream + Phenotype.sol に complianceGate modifier 追加)、Public Fund に同 gate 追加 | ~1 week |

## 9. ADR-2605172300 / 2605192145 への amendment 要請 (L2 + L3 enforcement)

License L1 (Rider §3 termination) は本 ADR で完結する。便益 L2 と評価 L3 は ADR-2605172300 と ADR-2605192145 の amendment が必要。

### 9.1 ADR-2605172300 への追加 (Phenotype + Kisha)

`Phenotype.sol` に Council 経由の constitutional override を追加:

```solidity
contract Phenotype {
    // 既存
    mapping(uint256 => uint256) public multiplier;

    // 追加 (v2.0)
    mapping(uint256 => bool) public charterNonCompliant;  // Council attestation で true 化

    function setCharterNonCompliant(uint256 tokenId, bytes calldata councilSig) external {
        require(_verifyCouncilQuorum(councilSig, 3), "need 3 Lv6+ signers");
        charterNonCompliant[tokenId] = true;
        emit CharterNonCompliant(tokenId);
    }

    function effectiveMultiplier(uint256 tokenId) public view returns (uint256) {
        if (charterNonCompliant[tokenId]) return 0;  // L3: floor=0 (constitutional override)
        return multiplier[tokenId];
    }
}
```

`KishaStream.sol` の `accrue()` は `multiplier[]` ではなく `effectiveMultiplier()` を読む。L2 enforcement: Non-Aligned 認定された SBT 保有者の Kisha は `multiplier = 0` で 0 USDC/day になる。

### 9.2 ADR-2605192145 への追加 (Public Fund)

`PublicFundGovernance.sol` の `propose()` で:

```solidity
function propose(...) external returns (bytes32 proposalId) {
    for (uint256 i = 0; i < recipients.length; i++) {
        require(
            !_isCharterNonCompliantAddress(recipients[i]),
            "PublicFund: recipient is charter non-compliant"
        );
    }
    // ...
}
```

L2 enforcement: Non-Aligned 認定された address は Public Fund grant の recipient になれない。

### 9.3 三層の religious 整合性

| Layer | 効果 | religious 意味 |
|---|---|---|
| L1 License 無効 | software 使用不可 | religious-corp の 作品 (技術) を heretical entity に使わせない |
| L2 便益受給不可 | Kisha + Public Fund grant 不可 | 救済 (kisha) の religious 範囲を doctrinal に画定 |
| L3 評価最低 | Phenotype multiplier = 0 | 構成員間の評価における doctrinal compliance の反映 |

これは伝統的 religious 慣行と整合的:
- 仏教 sangha からの追放 (波羅夷罪) → L1+L2+L3 同時発動
- キリスト教 excommunication → L2+L3 (救済からの分離)
- ユダヤ教 cherem (חרם) → L1+L2+L3 同時発動
- イスラム takfir → L2+L3 (zakat 不適用)

etzhayyim はこれらの先例に倣う religious exercise であり、現代法における **religious-corp の doctrinal autonomy** の範疇 (日本国憲法 §20、信教の自由)。

# Consequences

## 正の効果

- **minimax 解として optimal**。8 戦略 × 12 adversary の payoff matrix で maximin = -2 (S6/S7 と同点)、average payoff +1.42 (単独最高)。von Neumann 意味で最適。
- **religious-corp 固有の license 姿勢が成文化される**。「mission 整合的な他者にのみ無償公開」という constitutional 判断が license レベルで実現される。
- **Apache 2.0 ecosystem 互換性の維持**。npm / Cargo / pip / GitHub の依存解決系は本 license を Apache 2.0 として処理する。CI / SBOM ツールも問題なし。
- **既存 50+ repo の license stance が unified される**。drift しない。
- **Mission Charter §1.5 が enforceable**。Rider 違反は §3(a) で patent grant termination を trigger するため、licensee は事実上 license を失う (patent retaliation の severity)。
- **religious-corp としての distinctive positioning**。「Apache 2 + 宗教的 mission rider を持つ religious-corp」は世界的に珍しい。
- **transparent な dispute resolution**。Council attestation が on-chain 公開され、判定の社会的可視性が高い。
- **三層 enforcement で religious 完成度が高い**。license / 便益 / 評価 の三層は仏教 sangha / キリスト教 excommunication / ユダヤ教 cherem / イスラム takfir と integrity が等しい religious 慣行で、現代法で religious-corp の正当な doctrinal autonomy として擁護される。
- **多世代視点の constitutional 化**。「子・孫を優先する」は §2(f) と §4(f) で third-party beneficiary として明文化。future persons は紛争 §5 で Council が代理して invoke できる。

## 負の効果 / コスト

- **OSI 認定外 license addendum**。本 Rider は OSI 認定の "open source" 定義 (差別禁止条項) に違反する。これは religious-corp の意図的な judgment である (差別禁止は世俗的 doctrine であり、宗教の doctrinal scope を縛る根拠にならない)。tooling は Apache 2.0 と認識するが、philosophical には open source ではなく **religious source** と位置付ける。
- **法的不確実性**。§7 (severability) で対処したが、Rider §2 (特に §2(g) 反個人主義) が enforceable かは jurisdiction 依存。米国は契約自由原則 + Title VII 宗教例外で比較的問題少ない。EU は反差別法との兼ね合いで微妙だが宗教 doctrine 例外あり。日本は §20 信教の自由で religious-corp の doctrinal autonomy が支持される。
- **downstream user の混乱**。Apache 2.0 と認識して fork した user が Rider に直面する。混乱は不可避。Mitigation: README 明示 + LICENSE/NOTICE/CHARTER-RIDER.md の三層表示。
- **Council attestation の judgment 負荷**。dispute が増えれば Council Lv6+ の稼働増加。最初の 6 ヶ月で件数を見て評議体の拡張要否を判断。三層 enforcement (L1+L2+L3) が同時発動するので、判断の religious 一貫性責任が重い。
- **既存 fork の遡及不可**。本 ADR 以前の fork は古い NOTICE のままで動作する。これは受容する判断。
- **「mission 整合的かどうか」の判定問題**。Council が大企業 (例: Microsoft, Google) を Non-Aligned と判定するケースを想定する。判定リスク高い。
- **専門性 gatekeeping clause (§2(e)) の法的攻めの強さ**。弁護士会 / 医師会から license 条項そのものへの法的圧力を受ける可能性。Mitigation: §2(e) は "legitimate technical safety oversight" を明示的に保護し、攻撃面を narrow にしている。
- **反個人主義 (§2(g)) の修辞的負荷**。「individual を否定する宗教」と誤読される risk。Mitigation: §2(g) と §4(g) で「private opinion は保護、organizational doctrinal commitment のみ exclude」を明示し、これが religious doctrine の通常範囲であることを Buddhist/Christian/Jewish/Islamic 前例で legitimize。
- **多世代条項 (§2(f)) の foreseeability 問題**。25 年後の影響を「foreseeable」と判定する基準は曖昧。Mitigation: "prudent multi-generational steward" 基準を明示的に置く。
- **三層 enforcement の severity**。L1+L2+L3 同時発動は伝統的 religious 追放と等価で severity が高い。修復 (再加入) の path を §5 appeal で残すが、constitutional 修復は heavier。

## 中立 / トレードオフ

- **§2 の業態 list の固定性 vs 進化性**。固定すると未来の Non-Aligned 業態 (例: 新興の搾取的 business model) を追加できない。Mitigation: Rider versioning。本 ADR は v1.0。v1.1 以降は別 ADR で追加。既存 fork は v1.0 のまま運用可。
- **revenue share 25% threshold**。"primary business activity" の境界。25% を切ると Non-Aligned 認定されない。例: ad-tech に 24% 依存する事業者は OK、26% なら NG。境界事例の判定は Council へ。
- **「自然人による使用は無条件 permitted」 (§4(a))**。これは Rider の OSI 適合性問題を緩和する (個人開発者の use は完全に open)。一方、自然人として Non-Aligned Entity の業務を行う case は法的に grey。

# Alternatives Considered

## A. Apache 2.0 単体 (Rider なし)

status quo。

- 却下: Mission Charter §1.5「方針整合的な他者への」が enforce できない。

## B. Hippocratic License 3.0 に切り替え

OSI 非認定 ethical source license。UN 人権 + 環境 + 軍事条項。

- Pro: 既存の ethical source ecosystem に乗れる。
- Con: etzhayyim 固有の religious mission (§1.5-§1.7) が反映されない。"specialist gatekeeping" の clause は Hippocratic には無い。
- 却下: 独自 Rider の方が religious-corp 固有性を表現できる。

## C. Anti-Capitalist Software License

個人 / 協同組合 / 非営利のみ。

- Pro: 株式会社利用排除が clean。
- Con: §1.6 中間排除に対応する個別業態列挙が不可能。Microsoft / Cloudflare / Coinbase 等の substrate provider 利用も阻害する。
- 却下: 過度に restrictive。etzhayyim は substrate provider を使う前提 (CLAUDE.md identity)。

## D. AGPL v3 + custom addendum

copyleft + 独自条項。

- Pro: SaaS で source 公開強制。
- Con: 商業利用は阻害できるが「業態 (mission 整合性)」は問えない。AGPL は OSI 認定なのでこれ単体では本 ADR 目的不達成。
- 却下: copyleft 強制は構成員の自由を下げる。

## E. Dual-licensing (Apache 2.0 free for charter-aligned, commercial for others)

Apache 2.0 で配布、Non-Aligned は商業 license を購入。

- Pro: 営利収入が立つ。
- Con: §1.6 中間排除 + ADR-2605192115 非営利 only と矛盾。営利化禁止のため commercial license は売れない。
- 却下: 非営利原則違反。

## F. CC BY-NC 4.0 で code を配布

非商業使用のみ permitted。

- Pro: 商業利用阻害。
- Con: NC 条項は OSI 非適合かつ Free Software Foundation も非推奨。tooling 互換性が崩壊する。code 用途で CC は不適切。
- 却下。

## G. OSI 認定外の religious-specific license を新規策定

新規 license 文書を起こす。

- Pro: religious mission を直接 license 文に書ける。
- Con: license 策定は重い。OSI 非認定 license は tooling ecosystem 互換性なし。
- 部分的採用: 本 ADR は新規 license 策定ではなく、Apache 2.0 + Rider という軽量 addendum 方式を採用。

# Open Questions

1. **Council による初動判定 — 主要 IT 企業の status**。Microsoft / Google / Apple / Meta / Amazon が §2 のどれに該当するかの initial determination をどう扱うか。回避すると Rider が dead letter になる。最初の attestation 対象として 1-2 社を選定する必要あり。
2. **§2(e) の法的安全性**。「弁護士法 72 条 / 医師法」との関係。日本国内で本 Rider が enforceable かは弁護士会の解釈に依存。法務 review 推奨。
3. **§2(g) の例示の精度**。「strict individualist doctrine」として Ayn Rand 直系の Objectivist 組織 / FEE / Cato Institute / Mises Institute 等を name しておくか、純粋に doctrine criteria のみで判定するか。Decision (本 ADR): doctrine criteria のみ。Council attestation で個別判定。
4. **§2(f) の "25年後" の根拠**。一世代 = 25-30 年 が国連人口統計の標準。本 ADR は 25 年を最小単位として採用。「子・孫」= 2 世代分 ≈ 50-60 年も実質的範囲だが、Rider 文言は最小単位を採用。
5. **既存 fork の取り扱い**。`etzhayyim/*` 等の legacy 名 fork が外部に既に存在する可能性。これらに retro-active Rider を適用する宣言を出すか、過去 fork は古い license のまま放置するか。**Decision (本 ADR §3.3): 過去 fork は放置、今後の commit に Rider 適用**。
6. **Rider 違反の civil enforcement**。Council attestation が出ても、それを法的 enforcement する道は何か。米国 jurisdiction (Apache 2.0 §3 の patent termination 訴訟) を活用するか、日本国内では religious-corp 名誉毀損訴訟しかないか。
7. **三層 enforcement の修復 path**。L1+L2+L3 同時発動された entity が「方針整合」へ復帰する場合の procedure (= 仏教 反省 / キリスト教 confession / ユダヤ教 teshuvah と等価の religious return) を future ADR で定義する必要。当面は §5 appeal mechanism のみで対応。
8. **dependency 経由の Rider 伝搬**。npm install すると依存ツリーが指数的に増える。各 dependency の Rider compliance を確認する仕組みが必要か (= SBOM scan の charter-rider extension)。当面は **直接 dependency のみ確認** とする。

# References

- ADR-2605192100: Mission Charter (parent; §1.5 IP-free-release)
- ADR-2605172300: SBT holder の地位
- ADR-2605172600: Council Lv6+ の根拠
- ADR-2605191648: substrate-boundary-lefthook (CI lint pattern)
- `/CHARTER-RIDER.md` (新規 — 本 ADR 承認時に repo root に配置)
- `/CHARTER-RIDER.ja.md` (新規 — 同上)
- `70-tools/charter-rider-applicator/` (新規 — applicator script)
- Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0
- Hippocratic License (比較対象): https://firstdonoharm.dev/
- Anti-Capitalist Software License (比較対象): https://anticapitalist.software/
- OSI 認定 license list: https://opensource.org/licenses
- 弁護士法 72 条 (§2(e) との関連、要 review)
