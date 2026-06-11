/**
 * HC Platform Contracts — Single Source of Truth (日本法基準)
 *
 * Referenced by `60-apps/etzhayyim-project-hc/CLAUDE.md` §Contracts.
 * 全契約の準拠法：日本法 / 専属管轄：東京地方裁判所。
 * 国別 locale addendum は各国強行法規の override 条項のみ。
 * Effective date: 2026-04-22. Amend via PR; versioning by effectiveDate + rev.
 */

export const GOVERNING_LAW = "日本法";
export const EXCLUSIVE_JURISDICTION = "東京地方裁判所";
export const OPERATOR = "etzhayyim（עץ חיים／宗教法人・任意団体。規約・名簿は public blockchain 上に登記。以下「当社」）";
export const OPERATOR_NOTE =
  "etzhayyim は日本国 宗教法人法 上の登記宗教法人ではなく、所轄庁 (文部科学省・都道府県知事) の認証を受けた宗教法人ではない。本契約上の「当社」とは、本サービスの運営主体である etzhayyim を指す。";
export const EFFECTIVE_DATE = "2026-04-27";
export const REV = 2;

export type ContractType =
  | "worker-agreement"
  | "sp-service-agreement"
  | "task-terms"
  | "shift-terms";

export type Locale =
  | "ja" | "us" | "eu" | "gb" | "cn" | "kr" | "in" | "vn"
  | "th" | "de" | "tw" | "id" | "my";

export interface Contract {
  type: ContractType;
  did: string;
  title: string;
  governingLaw: string;
  jurisdiction: string;
  effectiveDate: string;
  rev: number;
  locale: Locale;
  body: string;      // canonical Japanese text (locale="ja")
  addendum?: string; // locale-specific override text
}

/* ========================================================================
 * 1. Worker Agreement — ギグ/タスクワーカー向け
 * ======================================================================== */

const WORKER_AGREEMENT_JA = `
# ワーカー利用規約（Worker Agreement）

${OPERATOR}が運営する Human Computing Platform（hc.etzhayyim.com, 以下「本サービス」）の
ワーカーとして役務を提供する個人（以下「ワーカー」）は、本規約に同意するものとします。

## 第1条（本規約の適用）
本規約は、ワーカーと当社との間の本サービスに関する一切の関係に適用されます。
個別タスクの条件（Task Terms）、シフトの条件（Shift Terms）は本規約に付随し、矛盾する場合は本規約が優先します。

## 第2条（ワーカーの資格）
1. ワーカーは満18歳以上であることを表明・保証します。16歳以上18歳未満の者は、保護者の同意のもと別途「保護者同意付きワーカー規約」に従います。
2. 本人確認（KYC）を完了したワーカーのみ役務を提供できます。
3. ワーカーは個人事業主として独立して役務を提供し、当社との間に雇用関係・使用従属関係は生じません。

## 第3条（役務の提供）
1. ワーカーは、公開されたタスク／シフトのうち自己の判断で選択した案件についてのみ役務を提供します。
2. ワーカーは、提供する役務の方法・時間・場所を自己の裁量で決定します。
3. ワーカーは、労働基準法の法定上限（週40時間、1日8時間）の範囲内で役務を提供するものとし、当社は提供時間を自動集計します。上限超過の予約は拒否されます。

## 第4条（成果物及び知的財産権）
1. ワーカーが本サービスを通じて作成・提出した一切の成果物（動画・画像・音声・テキスト・データを含む。以下「成果物」）に関する著作権（著作権法第27条及び第28条の権利を含む）その他一切の知的財産権は、作成時点または提出時点で当社に**完全かつ排他的に帰属**します。
2. ワーカーは、当社及び当社が指定する第三者に対し、成果物に関する**著作者人格権を行使しない**ことに同意します。
3. ワーカーは、成果物について第三者の権利を侵害しないこと及び第三者の権利処理を自己の責任で完了させていることを保証し、万一紛争が生じた場合は自己の費用と責任で解決します。

## 第5条（報酬）
1. 報酬は個別タスク／シフト毎の規定額とし、当社が承認した役務についてのみ発生します。
2. 支払手段は原則として電子的な Amazon ギフトカード（円建）とし、タスク承認後 1〜7 営業日以内にワーカーが登録したメールアドレス宛に配布します。
3. 当社は、ワーカーが本規約に違反した場合、未払報酬の全部または一部を没収することができます。

## 第6条（禁止事項）
ワーカーは以下の行為を行ってはなりません。違反した場合、当社は即時にアカウントを停止し、未払報酬を没収することができます。
1. 虚偽の申告・成りすまし・本人確認書類の偽変造
2. 成果物の盗用・自動生成ツール等による不正な大量生成
3. 他のワーカー、依頼者、当社役職員への嫌がらせ・誹謗中傷
4. 法令、公序良俗、第三者の権利を侵害する行為
5. 本サービスの運営を妨害する行為

## 第7条（免責・責任の上限）
1. 本サービスは「現状有姿」で提供され、当社は特定目的適合性・エラー不発生・継続稼働を保証しません。
2. 当社の責任は、直接かつ通常の損害に限定され、逸失利益・事業機会の喪失等の間接損害及び特別損害は負いません。
3. 当社の責任総額は、請求の原因が生じた時点から遡って**直近12ヶ月間にワーカーが当社から受領した報酬総額**を上限とします。

## 第8条（アカウント停止・解約）
1. 当社は、理由を問わず、ワーカーのアカウントを即時停止または削除することができます。
2. ワーカーはいつでも退会できますが、退会時点で提供中の役務は完了まで責任を負います。

## 第9条（競業避止・秘密保持）
1. ワーカーは、本サービスを通じて知り得た当社・依頼者・第三者の**業務上の秘密**を、本サービスの目的以外に使用せず、第三者に開示・漏洩してはなりません。本義務は退会後も**無期限**で存続します。
2. ワーカーは、本サービスを通じて知り得た情報・ノウハウを用いて、退会後1年間、本サービスと競合するサービスで役務を提供しないものとします。
3. 秘密保持義務違反につき、1件あたり金100万円の違約金を定めます。実損害がこれを超える場合の差額請求を妨げません。

## 第10条（規約の変更）
当社は、本規約を変更できます。変更内容及び発効日を本サービス上に公表することにより効力を生じ、公表後14日以上経過した時点でワーカーが本サービスを継続利用した場合、変更に同意したものとみなします。

## 第11条（準拠法・管轄）
本規約の準拠法は${GOVERNING_LAW}とし、本規約に関する一切の紛争は${EXCLUSIVE_JURISDICTION}を第一審の**専属的合意管轄裁判所**とします。

発効日：${EFFECTIVE_DATE}  版：rev.${REV}
${OPERATOR}
`.trim();

/* ========================================================================
 * 2. SP (Service Provider) Service Agreement — OEM 製造者／工場向け
 * ======================================================================== */

const SP_SERVICE_AGREEMENT_JA = `
# サービスプロバイダ契約（SP Service Agreement）

${OPERATOR}は、本サービス上で OEM 製造者・工場（以下「SP」）の登録を受け、
当社又は当社の顧客の発注に応じる SP と、本契約を締結します。

## 第1条（契約の成立）
SP が本サービス上で登録申請を行い、当社による KYC/KYB 検証及び工場監査を経て承認された時点で、本契約が成立します。

## 第2条（品質保証・瑕疵担保）
1. SP は、納品する製品が発注仕様に適合し、通常有すべき品質を備えていることを保証します。
2. 保証期間は納品日から**2年間**とし、期間内に発見された瑕疵については SP の費用で交換・再製造・返金のいずれかの対応を行います。
3. 不合格品の再製造・再検査・返送等に要する一切の費用は SP の負担とします。

## 第3条（納期・遅延）
1. SP は発注書記載の納期を厳守します。
2. SP の責に帰すべき事由により納期が遅延した場合、SP は発注金額に対し**1日あたり0.5%**の遅延損害金を当社に支払います。

## 第4条（製造物責任）
本サービスを通じて納品された製品に起因する第三者に対する損害賠償責任（製造物責任法を含む）は、**全面的に SP が負担**します。

## 第5条（監査権）
当社は、SP の工場・品質管理体制・労働環境・環境法令遵守状況等について、**3営業日前の通知**により監査を実施できます。監査費用は原則として当社負担ですが、重大な違反が発見された場合は SP 負担とします。

## 第6条（知的財産）
本契約に基づく業務の遂行過程で SP が行った**改良・考案・発明**（以下「改良等」）に関する知的財産権は、改良等の成立時点で当社に帰属します。SP は必要な権利譲渡手続に協力するものとします。

## 第7条（秘密保持・競業避止）
1. 本契約及び業務を通じて知り得た秘密情報は、契約終了後**5年間**秘密として保持します。
2. SP は、契約終了後**2年間**、当社又は当社の顧客と実質的に競合する者との間で、本業務と同種の業務を行わないものとします。

## 第8条（一方的解除権）
当社は、**30日前の書面通知**により、理由を問わず本契約を解除できます。解除により SP に生じた損害について、当社は賠償義務を負いません。

## 第9条（準拠法・管轄）
本契約の準拠法は${GOVERNING_LAW}、専属的合意管轄裁判所は${EXCLUSIVE_JURISDICTION}とします。

発効日：${EFFECTIVE_DATE}  版：rev.${REV}
${OPERATOR}
`.trim();

/* ========================================================================
 * 3. Task Terms — マイクロタスク個別
 * ======================================================================== */

const TASK_TERMS_JA = `
# タスク利用規約（Task Terms）

本規約は、Worker Agreement を前提として、個別のマイクロタスクに適用されます。

## 第1条（成果物の受理と報酬）
1. 成果物の受理可否は、依頼者又は当社が定める基準に基づき判定します。
2. 受理（approve）された場合に限り、タスク規定額の報酬が発生します。**却下（reject）された成果物については報酬は発生しません。**
3. 依頼者が定められた期限内に判定を行わなかった場合、期限経過の時点で**自動承認**されたものとみなします（当該自動承認期限は個別タスクに記載）。

## 第2条（禁止行為）
1. 生成AIその他の自動化手段により、本来求められる役務を代替すること（当該タスクで明示的に許可されている場合を除く）。
2. 同一成果物の複数タスクへの使い回し。
3. 他ワーカーに成果物の提供を下請けさせる行為。

## 第3条（紛争解決）
成果物の受理可否、報酬の発生・不発生その他個別タスクに関する紛争について、**当社の裁定を最終・拘束的なものとし、ワーカーはこれに対する不服申立を行わない**ものとします。

## 第4条（未払報酬の没収）
前条及び Worker Agreement 第6条（禁止事項）に違反した場合、当社は当該ワーカーの未払報酬全額を没収することができます。

発効日：${EFFECTIVE_DATE}  版：rev.${REV}
`.trim();

/* ========================================================================
 * 4. Shift Terms — シフトワーク個別
 * ======================================================================== */

const SHIFT_TERMS_JA = `
# シフト利用規約（Shift Terms）

本規約は、Worker Agreement を前提として、個別のシフト型役務に適用されます。

## 第1条（当社の役割）
当社は、ワーカーと発注者（現場）との間のマッチングプラットフォームを提供するものであり、**個別シフト契約の当事者とはなりません**。シフト中の役務提供に関する一切の責任は、ワーカーと発注者の間で処理されるものとします。

## 第2条（労働基準法の遵守）
1. ワーカーは、シフト予約にあたり、Worker Agreement 第3条第3項（週40時間・1日8時間上限）を遵守します。
2. 6時間を超える役務には45分、8時間を超える役務には60分の休憩を確保します。
3. 22:00〜翌5:00の深夜時間帯における役務には、基本単価に25%を割増した報酬が表示されます。

## 第3条（チェックイン／チェックアウト）
ワーカーは、シフト開始時にチェックイン、終了時にチェックアウトを行います。所定時刻にチェックインがない場合、当該シフトはキャンセルされ報酬は発生しません。

## 第4条（免責）
シフト中にワーカー又は第三者に生じた事故・疾病・損害について、**当社は責任を負いません**。ワーカーは必要に応じて自己の費用で労災保険その他の保険を付保するものとします。

## 第5条（即時払い手数料）
ワーカーは、通常の支払サイクルに優先して報酬を受け取る「即時払い」を選択できます。即時払いを選択した場合、**報酬額の3%を手数料として控除**します。当該手数料率は当社の一方的判断により変更できます。

発効日：${EFFECTIVE_DATE}  版：rev.${REV}
`.trim();

/* ========================================================================
 * Contract registry
 * ======================================================================== */

const NANOID = "hc0mp7ng";
const didOf = (type: ContractType) => `did:web:${NANOID}.etzhayyim.com:legal:${type}`;

const contracts: Record<ContractType, Record<Locale, Contract>> = {} as any;

const baseBodies: Record<ContractType, string> = {
  "worker-agreement": WORKER_AGREEMENT_JA,
  "sp-service-agreement": SP_SERVICE_AGREEMENT_JA,
  "task-terms": TASK_TERMS_JA,
  "shift-terms": SHIFT_TERMS_JA,
};

const titles: Record<ContractType, string> = {
  "worker-agreement": "ワーカー利用規約",
  "sp-service-agreement": "サービスプロバイダ契約",
  "task-terms": "タスク利用規約",
  "shift-terms": "シフト利用規約",
};

// Locale addenda (override clauses only; empty = base JA applies as-is)
const ADDENDA: Partial<Record<Locale, string>> = {
  us: `US addendum: (1) FLSA independent contractor classification; (2) CCPA/CPRA applies to personal information of California residents; (3) class action and jury trial waivers; (4) CA Civil Code §1542 waiver.`,
  eu: `EU/EEA addendum: (1) GDPR applies; the operator is the data controller. (2) Platform Work Directive (EU) 2024/2831 transparency obligations apply where mandatory. (3) Unfair Terms Directive 93/13/EEC may render certain limitation clauses unenforceable against consumers.`,
  gb: `UK addendum: (1) UK GDPR applies. (2) Unfair Contract Terms Act 1977 may restrict the enforceability of exclusion clauses against consumers.`,
  cn: `中国 addendum：(1) PIPL 適用；(2) 労働関連強行法規が優先；(3) CIETAC 北京を補完的仲裁地とする。`,
  kr: `韓国 addendum：개인정보보호법 및 근로기준법 적용。`,
  in: `India addendum: DPDP Act 2023, Code on Social Security 2020, FEMA 1999 apply where mandatory.`,
  vn: `Vietnam addendum: Nghị định 13/2023 (PDPA), Bộ luật Lao động 2019 apply where mandatory.`,
  th: `Thailand addendum: PDPA 2562 and Labor Protection Act 2541 apply where mandatory.`,
  de: `Deutschland addendum: BGB §§305-310 (AGB-Kontrolle) kann einzelne Haftungsklauseln unwirksam machen.`,
  tw: `台灣 addendum：個人資料保護法及勞動基準法適用。`,
  id: `Indonesia addendum: UU PDP 2022 and UU 13/2003 apply where mandatory.`,
  my: `Malaysia addendum: PDPA 2010 and Employment Act 1955 apply where mandatory.`,
  ja: undefined,
};

const ALL_LOCALES: Locale[] = ["ja","us","eu","gb","cn","kr","in","vn","th","de","tw","id","my"];

for (const type of Object.keys(baseBodies) as ContractType[]) {
  contracts[type] = {} as any;
  for (const loc of ALL_LOCALES) {
    contracts[type][loc] = {
      type,
      did: didOf(type),
      title: titles[type],
      governingLaw: GOVERNING_LAW,
      jurisdiction: EXCLUSIVE_JURISDICTION,
      effectiveDate: EFFECTIVE_DATE,
      rev: REV,
      locale: loc,
      body: baseBodies[type],
      addendum: ADDENDA[loc],
    };
  }
}

export function getContract(type: ContractType, locale: Locale = "ja"): Contract | null {
  return contracts[type]?.[locale] ?? null;
}

export function listContracts(): Array<{ type: ContractType; did: string; title: string }> {
  return (Object.keys(baseBodies) as ContractType[]).map((t) => ({
    type: t,
    did: didOf(t),
    title: titles[t],
  }));
}

export const SUPPORTED_LOCALES = ALL_LOCALES;
