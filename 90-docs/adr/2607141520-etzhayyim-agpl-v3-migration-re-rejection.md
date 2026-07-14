---
id: adr-2607141520-etzhayyim-agpl-v3-migration-re-rejection
title: "ADR-2607141520: etzhayyim AGPL v3 移行提案の再却下 — Rider×AGPL§7 非両立の明文化と cloud-itonami 結合面の整理"
status: proposed
doc_type: adr
topic: etzhayyim-agpl-v3-migration-re-rejection
authoritative: true
last_verified: 2026-07-14
priority: 8.0
axis: governance
weight: 0.80
priority_note: "License form is constitution-grade (Tier-1 Derived Policy). 本 ADR は org-wide AGPL v3 化の owner 提案 (2026-07-14) を ADR-2605192200 S5/Alt-D の却下根拠の再検証つきで再却下し、これまで暗黙だった AGPLv3 §7 による Rider 無効化リスクと、etzhayyim(Apache+Rider)→cloud-itonami(AGPL) 消費方向の結合面を明文化する。license 既定の変更は行わない。"
authoritative_for:
  - agpl-v3-migration-re-rejection-2026-07
  - rider-agpl-section7-incompatibility
  - etzhayyim-cloud-itonami-license-boundary
depends_on:
  - "2605192200"   # Apache 2.0 + Charter Rider 正本 spec (S5/Alt-D で AGPL 却下済み)
  - "2605192100"   # Mission Charter (§1.5 IP-free-release to charter-aligned others)
  - "2606062100"   # 3-Tier immutability (license 既定 = Tier-1 Derived Policy)
  - "2606182359"   # Rider v3.5 (objective-function 化 + §D6 honest enforceability limit)
related:
  - "2606172300"   # ECL — etzhayyim Covenant License (design-only; 本 ADR が結合面明文化を要請)
  - "2607011000"   # cloud-itonami robotics premise — lib=Apache / blueprint=AGPL の二層 taxonomy 初出
  - "2607012100"   # cloud-itonami org split
supersedes: []
superseded_by: []
---

# ADR-2607141520: etzhayyim AGPL v3 移行提案の再却下 — Rider×AGPL§7 非両立の明文化と cloud-itonami 結合面の整理

**Status**: proposed
**Date**: 2026-07-14
**Deciders**: Jun Kawasaki

# Context

2026-07-14、owner から「etzhayyim は今 Apache 2 だが、cloud-itonami と同じように
AGPL v3 にした方がよいのではないか」という提案があり、分析を行った。本 ADR はその
分析結果を decision record として固定する。

前提事実:

1. **etzhayyim の現行ライセンスは素の Apache 2.0 ではない。**
   Apache 2.0 + etzhayyim Charter Compliance Rider v3.5(ADR-2605192200 初版 →
   2606062100 → 2606082400 → 2606161700 → 2606172359 → 2606180001 → 2606182359)
   である。Rider は三層 enforcement(L1 license 失効 / L2 Kisha・Public Fund 便益遮断 /
   L3 Phenotype 評価 floor=0)の L1 を **Apache 2.0 §3(patent grant termination)+
   §4** を法的トリガーとして実装している。
2. **license 既定は Tier-1 Derived Policy**(ADR-2606062100)。改正は Council Lv7+
   unanimity + priority-conformance attestation(never weaker)のみ。repo 単位の
   chore ではなく憲法級の変更である。
3. **AGPL v3 は ADR-2605192200 で定量的に検討・却下済み。** von Neumann minimax
   分析(8 strategy × 12 adversary)で S5(AGPL v3 単体)は maximin -3 / avg -0.75 で
   reject、Alternative D(AGPL v3 + custom addendum)も「AGPL は SaaS ソース公開は
   強制できるが業態(mission 整合性)は問えない」「copyleft 強制は構成員の自由を下げる」
   を理由に却下されている。
4. **cloud-itonami の AGPL-3.0 は別レイヤーの意図的設計である**(ADR-2607011000):
   - lib(kotoba-lang org、純 cljc、埋め込まれる部品)= **Apache 2.0**
   - blueprint repo(cloud-itonami、自己完結したネットワークサービス設計図)=
     **AGPL-3.0**(network copyleft で proprietary SaaS 化を防ぐ)
   etzhayyim の repo 群は圧倒的に前者側(kotoba 17 crates / kami-engine / SDK /
   protocol lib / データセット / actor 基盤)に属する上流 substrate であり、実際に
   `cloud-itonami-gtin-catalog`(AGPL)が `com-etzhayyim-gtin`(Apache+Rider)を
   上流として消費している。
5. **後継ライセンスとして ECL(etzhayyim Covenant License、ADR-2606172300)が
   design-only で進行中**(独自 conduct 層 × Apache 既製 base、ratification は
   Council Lv7+ gate)。

## 本 ADR で新たに明文化する法的論点: AGPLv3 §7 × Rider の非両立

ADR-2605192200 Alt-D の却下理由には含まれていなかった(あるいは暗黙だった)論点を
明示する。**AGPLv3 §7 第 4 段落**は次を定める:

> "If the Program as you received it, or any part of it, contains a notice
> stating that it is governed by this License along with a term that is a
> further restriction, **you may remove that term.**"

Charter Rider §2 の使用制限(Non-Aligned Entity 排除 / 目的関数による :non-aligned
判定)は AGPL の許諾範囲を狭める「further restriction」に該当する。したがって
**AGPL v3 + Rider という構成は、受領者全員に Rider を合法的に除去する権利を与える**。
Apache 2.0(permissive base + supplemental condition としての Rider)では成立して
いた三層 enforcement の L1 が、AGPL 化した瞬間に法的に無効化される。
「AGPL の方が強い copyleft だから守りも強くなる」という直感とは逆に、etzhayyim に
とって AGPL 化は **Rider という宗教法的中核の一方的な放棄**を意味する。

# Decision

## D1. org-wide AGPL v3 化を再却下する(license 既定は不変)

etzhayyim/root および etzhayyim org 配下の repo の license 既定は
**Apache 2.0 + Charter Compliance Rider v3.5 のまま**とし、ECL(ADR-2606172300)への
移行路線も不変とする。却下根拠は独立に 4 点:

- **(a) 法的非両立**: 上記 AGPLv3 §7 により Rider が strippable になり、三層
  enforcement L1 が崩壊する。Apache §3/§4 termination を trigger とする現行設計は
  AGPL の patent 条項(§11)+ no-further-restrictions 原則では再現できない。
- **(b) 業態排除の不能**: AGPL は OSI 認定 = 無差別許諾が本質であり、Mission Charter
  §1.5「方針整合的な他者への(= 不整合な他者へは公開しない)」を表現できない。
  ADR-2605192200 S5/Alt-D の却下根拠は 2026-07-14 時点でも全て有効。
- **(c) レイヤー taxonomy との矛盾**: etzhayyim は上流 substrate/lib 層であり、
  上流を AGPL 化すると copyleft が全下流消費者 — charter-aligned な第三者を含む —
  に伝播する。Mission §1.5 が無償公開したい相手にこそ compliance 負担を課すことに
  なり、「lib = permissive / end-service = AGPL」という既存の意図的設計
  (ADR-2607011000)にも反する。
- **(d) 目的の重複**: AGPL 化の動機である anti-enclosure(proprietary SaaS 囲い込み
  防止)は、Rider v3.5 / ECL 目的関数の collective-commons 次元での負スコア +
  Council attestation → :non-aligned → L1/L2/L3 発動、という既存機構が既にカバー
  している。機構は copyleft でなく doctrinal/contractual だが、狙う対象は同一。

## D2. 結合面(etzhayyim → cloud-itonami)の明文化

`cloud-itonami-*`(AGPL-3.0)が `com-etzhayyim-*` / etzhayyim substrate
(Apache 2.0 + Rider)を消費する現行方向は**維持・許容**する:

- 両 org の著作権者が同一(founder / その支配下エンティティ)である間は、著作権者
  自身が自己の上流コードを AGPL combined work に組み込む行為として整理され、実務上の
  問題はない。
- ただし**第三者が combined work を再配布する場面**では、Rider(further restriction)
  と AGPL の no-further-restrictions が緊張関係になる。この結合面の扱い
  (どちらの条件が combined work のどの部分に及ぶか、Rider は etzhayyim 由来部分の
  みに付随すること)を **ECL 設計(ADR-2606172300)の ratification までに明示する
  こと**を同 ADR への要請として記録する。
- 逆方向(etzhayyim repo が AGPL コードに依存する)は、Apache+Rider 配布物に AGPL
  を組み込めないため**原則禁止**(vendored fork の例外は従来どおり原ライセンス保持、
  charter-rider-applicator の skip 対象)。

## D3. per-repo escape hatch(org 既定を触らない個別解)

etzhayyim org 内の repo が実態として「lib/substrate ではなく自己完結ネットワーク
サービス」であり、network copyleft による保護が本当に必要な場合の正規経路は:

1. その repo を **cloud-itonami org(blueprint 層)へ移管**し AGPL-3.0 を適用する
   (per-repo ADR 必須)。
2. 移管 repo では **Rider を外す**(D1(a) のとおり AGPL と両立しないため。同時付与は
   禁止)。
3. etzhayyim org の license 既定には一切触れない。

「org 単位で AGPL に倒す」は D1 で却下済みのため、この個別解のみを許容する。

## D4. 手続き的ロック

将来 AGPL 化を再提案する場合は、(1) Tier-1 改正手続(Council Lv7+ unanimity +
priority-conformance attestation)、(2) ADR-2605192200 S5/Alt-D 分析の明示的
supersession、(3) Rider 放棄(= 三層 enforcement L1 の喪失)の受容、の 3 点を
すべて含む ADR としてのみ提出できる。本 ADR を参照しない再提案は differ せず却下する。

# Consequences

## 正の効果

- **Rider / 三層 enforcement の integrity が保たれる。** L1 の法的トリガー
  (Apache §3/§4)が維持される。
- **AGPLv3 §7 × Rider 非両立という暗黙リスクが decision record 化された。**
  ADR-2605192200 Alt-D は「目的不達成」を理由にしたが、本 ADR で「積極的に有害
  (Rider を strippable にする)」まで明文化された。
- **二層 taxonomy(lib=Apache / blueprint=AGPL)が etzhayyim 側からも参照可能に
  なり、license 選定の再燃(re-litigation)を防ぐ。** 同種の提案は D4 の手続きに
  従う場合のみ審議される。
- **ECL 設計への具体的要請(結合面の明示)が積まれた**(D2)。

## 負の効果 / 受容するトレードオフ

- **OSI-legible で判例蓄積のある anti-SaaS copyleft(AGPL)は採用しない。**
  anti-enclosure は Rider/ECL の目的関数 + Council attestation に依存し続けるが、
  その enforceability には ADR-2606182359 §D6 の honest limit がある(法的に exotic
  であることを認めた上での宗教法的選択)。このトレードオフは Mission Charter の
  「業態を問える無償公開」を「無差別 copyleft」より優先する判断として受容する。
- cloud-itonami との「見かけの license 統一」は実現しない(ただし D1(c) のとおり、
  統一に見えるものは taxonomy の誤読である)。

## 中立

- 運用上の変更はゼロ。NOTICE / CHARTER-RIDER.md / charter-rider-applicator / CI lint
  (`lint-charter-rider-notice`)は全て現状のまま。
- 本 ADR は license 文言を 1 文字も変更しない(pure decision record)。

# Alternatives Considered

## A. org-wide AGPL v3 化(owner 提案の原型)

- Pro: network copyleft による SaaS 囲い込み防止が license 層で self-executing に
  なる。cloud-itonami と見かけ上揃う。
- Con: D1(a)-(d) の 4 点。特に §7 による Rider 無効化は宗教法的アーキテクチャの
  中核喪失。
- **却下**(D1)。

## B. AGPL v3 + Charter Rider addendum の併記

- Pro: copyleft と業態排除の両取りに見える。
- Con: AGPLv3 §7 ¶4 により Rider は受領者が合法的に除去可能 = 法的に無意味。
  さらに further restriction を付した時点で配布物は正規の AGPL とも呼べなくなり、
  OSI/tooling 互換性の利点も失う。ADR-2605192200 Alt-D 却下の強化再確認。
- **却下**。

## C. dual-licensing(Apache 2.0 + Rider ‖ AGPL v3 を receiver が選択)

- Pro: 下流が事情に応じて選べる。
- Con: receiver は常に自分に有利な arm を選ぶため、Rider を嫌う entity は AGPL arm
  を選び業態排除が空洞化する(Rider の意味が消える)。管理コストは倍増。
- **却下**。

## D. 実態がサービスである repo の cloud-itonami 移管(per-repo)

- Pro: taxonomy(lib=Apache / blueprint=AGPL)を保ったまま、AGPL が本当に適する
  対象にだけ適用できる。org 既定・Rider に触れない。
- **採用**(D3 の escape hatch として)。

# References

- ADR-2605192200(Apache 2.0 + Charter Compliance Rider 正本 spec — S5/Alt-D で
  AGPL 却下、minimax 分析)
- ADR-2605192100(Mission Charter §1.5 IP-free-release)
- ADR-2606062100(3-Tier immutability — license 既定 = Tier-1)
- ADR-2606182359(Rider v3.5 objective-function 化 + §D6 enforceability honest limit)
- ADR-2606172300(ECL — etzhayyim Covenant License、design-only。D2 の結合面明文化
  要請先)
- ADR-2607011000(cloud-itonami robotics premise — lib=Apache / blueprint=AGPL
  二層 taxonomy)
- ADR-2607012100(cloud-itonami org split)
- GNU AGPL v3 §7(further restrictions の除去権): https://www.gnu.org/licenses/agpl-3.0.html
- Apache License 2.0 §3 / §4: https://www.apache.org/licenses/LICENSE-2.0
- 実結合例: `cloud-itonami-gtin-catalog`(AGPL-3.0)→ `com-etzhayyim-gtin`
  (Apache 2.0 + Rider v3.1 NOTICE)
