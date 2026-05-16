import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed: k-bakshi v2 雇用契約 (1年契約) clause-level decomposition
 *       + clause→hourei (法令条文) cite edges using existing edge_cites.
 *
 * Worked example proving end-to-end traceability:
 *   contract → clause → 法令条文 (citation_type / paragraph 付き)
 *
 * Targets `kbakshi-employment-2025-06-01-amended-1y` from
 * `20260509110000_seed_kbakshi_contracts.ts`. Other contracts (labor-notice
 * v0, employment v1) inherit the same clauses by lineage — separate seed
 * not needed until per-version diff matters.
 *
 * Legal interpretation = k-bakshi sign-off required before relying on cite
 * edges for any external (non-internal-audit) purpose. Marked
 * sensitivity_ord=300 (Tier 3 PII).
 */
const NOW = "2026-05-08T00:00:00Z";
const OWNER = "did:web:etz-hayim.gftd.ai";
const HOUREI_OWNER = "did:web:hourei.gftd.ai";
const CONTRACT_ID = "kbakshi-employment-2025-06-01-amended-1y";

type Clause = {
  cid: string;
  kind: string;
  summaryEn: string;
  summaryJa: string;
  severity: "low" | "medium" | "high" | "critical";
  ipAssignedTo?: string;
  ndaScope?: string;
  termMonths?: number;
};

type Cite = {
  clauseCid: string;
  hourei: string;
  art: string;
  citationType: "mandatory_law" | "default_rule" | "persuasive" | "interpretive";
  paragraph: string;
};

const CLAUSES: Clause[] = [
  { cid: "kbakshi-1y-working-hours",   kind: "working_hours",
    summaryEn: "8h/day, 40h/week, flex-time core 11:00-15:00 JST.",
    summaryJa: "1日8時間 / 週40時間。フレックスタイム制 (コア 11:00-15:00 JST)。",
    severity: "high" },
  { cid: "kbakshi-1y-overtime",        kind: "overtime",
    summaryEn: "36 agreement filed; overtime premium 25% / late-night +25% / holiday 35%.",
    summaryJa: "36協定届出済。時間外25% / 深夜25% / 休日35%。",
    severity: "high" },
  { cid: "kbakshi-1y-wages",           kind: "wages",
    summaryEn: "Monthly salary in JPY, paid current-month-end-cut next-month-end. No deductions beyond statutory.",
    summaryJa: "月給制 (JPY)、当月末締翌月末払。法定控除以外なし。賃金支払5原則準拠。",
    severity: "critical" },
  { cid: "kbakshi-1y-leave",           kind: "leave",
    summaryEn: "Paid leave per Labor Standards Act Art 39; 5-day mandatory take per year.",
    summaryJa: "労基法39条準拠の年休。年5日取得義務 (使用者管理)。",
    severity: "high" },
  { cid: "kbakshi-1y-ip-assignment",   kind: "ip_assignment",
    summaryEn: "All work product = work-for-hire to amanomibashira. Moral rights non-exercise covenant.",
    summaryJa: "業務上作成成果物は職務著作として amanomibashira 帰属。著作者人格権不行使特約。",
    severity: "critical",
    ipAssignedTo: "did:web:etz-hayim.gftd.ai" },
  { cid: "kbakshi-1y-confidentiality", kind: "confidentiality",
    summaryEn: "Trade secret + business confidentials, scope = amanomibashira platform internals + roadmap + customer info, term = 60mo post-term.",
    summaryJa: "営業秘密 + 業務上知り得た一切の機密。範囲: amanomibashira platform 内部 + roadmap + 顧客情報。退職後 60ヶ月。",
    severity: "critical",
    ndaScope: "amanomibashira platform internals + roadmap + customer info",
    termMonths: 60 },
  { cid: "kbakshi-1y-data-protection", kind: "data_protection",
    summaryEn: "PII handling per APPI; cross-border transfer (DPDP / EU GDPR) requires explicit consent.",
    summaryJa: "個情法準拠。越境移転 (DPDP / GDPR 圏) は事前明示同意必須。",
    severity: "high" },
  { cid: "kbakshi-1y-non-compete",     kind: "non_compete",
    summaryEn: "Post-employment 12mo non-compete in tech-law SaaS / India lawfirm space, geography = JP+IN, with reasonable compensation.",
    summaryJa: "退職後 12ヶ月、tech-law SaaS / India lawfirm 領域。地理: 日本+インド。合理的補償付。",
    severity: "high",
    termMonths: 12 },
  { cid: "kbakshi-1y-termination",     kind: "termination",
    summaryEn: "1-year fixed-term ending 2026-05-31. Renewal mutual; mid-term termination per LCA Art 16.",
    summaryJa: "1年契約 (2026-05-31迄)。更新は両者合意。中途解雇は労契法16条に従う。",
    severity: "high" },
  { cid: "kbakshi-1y-governing-law",   kind: "governing_law",
    summaryEn: "Governing law = Japan. Dispute = Tokyo District Court exclusive (1st instance).",
    summaryJa: "準拠法 = 日本法。紛争解決 = 東京地裁を第一審専属管轄。",
    severity: "medium" },
];

const CITES: Cite[] = [
  // working_hours → 労基法 32, 36
  { clauseCid: "kbakshi-1y-working-hours", hourei: "labor-standards-act", art: "32", citationType: "mandatory_law", paragraph: "1日8時間 / 週40時間" },
  { clauseCid: "kbakshi-1y-working-hours", hourei: "labor-standards-act", art: "36", citationType: "mandatory_law", paragraph: "36協定根拠" },
  // overtime → 労基法 37
  { clauseCid: "kbakshi-1y-overtime",      hourei: "labor-standards-act", art: "37", citationType: "mandatory_law", paragraph: "割増率根拠" },
  // wages → 労基法 24, 最賃法 4
  { clauseCid: "kbakshi-1y-wages",         hourei: "labor-standards-act", art: "24", citationType: "mandatory_law", paragraph: "賃金支払5原則" },
  { clauseCid: "kbakshi-1y-wages",         hourei: "minimum-wage-act",    art: "4",  citationType: "mandatory_law", paragraph: "最低賃金以上の支払" },
  // leave → 労基法 39
  { clauseCid: "kbakshi-1y-leave",         hourei: "labor-standards-act", art: "39", citationType: "mandatory_law", paragraph: "年休 + 年5日取得義務" },
  // ip_assignment → 著作権法 15, 27, 28, 59
  { clauseCid: "kbakshi-1y-ip-assignment", hourei: "copyright-act",       art: "15", citationType: "mandatory_law", paragraph: "職務著作 (法人著作)" },
  { clauseCid: "kbakshi-1y-ip-assignment", hourei: "copyright-act",       art: "27", citationType: "mandatory_law", paragraph: "翻訳・翻案権" },
  { clauseCid: "kbakshi-1y-ip-assignment", hourei: "copyright-act",       art: "28", citationType: "mandatory_law", paragraph: "二次的著作物利用権" },
  { clauseCid: "kbakshi-1y-ip-assignment", hourei: "copyright-act",       art: "59", citationType: "mandatory_law", paragraph: "著作者人格権の一身専属性 (不行使特約の根拠)" },
  // confidentiality → 不競法 2-1-7, 個情法 17, 23
  { clauseCid: "kbakshi-1y-confidentiality", hourei: "unfair-competition-prevention-act", art: "2-1-7", citationType: "mandatory_law", paragraph: "営業秘密の不正使用 (退職後)" },
  { clauseCid: "kbakshi-1y-confidentiality", hourei: "appi", art: "17", citationType: "mandatory_law", paragraph: "利用目的の特定" },
  { clauseCid: "kbakshi-1y-confidentiality", hourei: "appi", art: "23", citationType: "mandatory_law", paragraph: "第三者提供制限" },
  // data_protection → 個情法 17, 23, 28
  { clauseCid: "kbakshi-1y-data-protection", hourei: "appi", art: "17", citationType: "mandatory_law", paragraph: "利用目的の特定" },
  { clauseCid: "kbakshi-1y-data-protection", hourei: "appi", art: "23", citationType: "mandatory_law", paragraph: "第三者提供制限" },
  { clauseCid: "kbakshi-1y-data-protection", hourei: "appi", art: "28", citationType: "mandatory_law", paragraph: "外国にある第三者への提供 (DPDP / GDPR 設計の根拠)" },
  // non_compete → 民法 90, 不競法 2-1-7
  { clauseCid: "kbakshi-1y-non-compete",   hourei: "civil-code",                          art: "90",    citationType: "mandatory_law", paragraph: "公序良俗 (有効性判断の根拠)" },
  { clauseCid: "kbakshi-1y-non-compete",   hourei: "unfair-competition-prevention-act",   art: "2-1-7", citationType: "mandatory_law", paragraph: "営業秘密保護との重畳" },
  // termination → 労契法 16, 民法 627
  { clauseCid: "kbakshi-1y-termination",   hourei: "labor-contract-act", art: "16",  citationType: "mandatory_law", paragraph: "解雇権濫用法理" },
  { clauseCid: "kbakshi-1y-termination",   hourei: "civil-code",         art: "627", citationType: "default_rule",  paragraph: "期間定めなき雇用解約 (本契約は有期で除外)" },
  // governing_law → 民法 (一般), 民訴法 11 (合意管轄、未 seed: hourei.civil-procedure-act 後続)
  { clauseCid: "kbakshi-1y-governing-law", hourei: "civil-code",         art: "623", citationType: "interpretive",  paragraph: "雇用契約定義" },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── clause inserts ──────────────────────────────────────────────────────────
  for (const c of CLAUSES) {
    const vid = `at://did:web:bpmn.gftd.ai/ai.gftd.apps.gftdcojp.contractClause/${c.cid}`;
    await sql`
      INSERT INTO vertex_gftdcojp_contract_clause
        (vertex_id, contract_id, clause_kind, ip_assigned_to, nda_scope,
         term_months, summary, summary_ja, severity, created_at,
         sensitivity_ord, owner_did)
      SELECT
        ${vid}, ${CONTRACT_ID}, ${c.kind},
        ${c.ipAssignedTo ?? null}, ${c.ndaScope ?? null}, CAST(${c.termMonths ?? null} AS integer),
        ${c.summaryEn}, ${c.summaryJa}, ${c.severity},
        ${NOW}, 300, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_gftdcojp_contract_clause WHERE vertex_id = ${vid})
    `.execute(db);
  }

  // ── clause→hourei.jobun cite edges via existing edge_cites ────────────────
  for (const cite of CITES) {
    const srcVid = `at://did:web:bpmn.gftd.ai/ai.gftd.apps.gftdcojp.contractClause/${cite.clauseCid}`;
    const dstVid = `at://did:web:hourei.gftd.ai/ai.gftd.apps.hourei.article/${cite.hourei}--${cite.art}`;
    const edgeId = `edge:${cite.clauseCid}:cites:${cite.hourei}--${cite.art}`;
    const label = `${cite.hourei} 第${cite.art}条 — ${cite.paragraph}`;
    await sql`
      INSERT INTO edge_cites
        (edge_id, src_vid, dst_vid, owner_did, label,
         citation_type, paragraph, jurisdiction)
      SELECT
        ${edgeId}, ${srcVid}, ${dstVid}, ${HOUREI_OWNER}, ${label},
        ${cite.citationType}, ${cite.paragraph}, 'JP'
      WHERE NOT EXISTS (SELECT 1 FROM edge_cites WHERE edge_id = ${edgeId})
    `.execute(db);
  }

  // ── coverage MV: per-clause statutory cite count ───────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_contract_clause_hourei_coverage AS
    SELECT
      cc.contract_id,
      cc.clause_kind,
      cc.severity,
      COUNT(DISTINCT e.dst_vid) AS cite_count,
      ARRAY_AGG(DISTINCT e.dst_vid) AS cited_jobun
    FROM vertex_gftdcojp_contract_clause cc
    LEFT JOIN edge_cites e ON e.src_vid = cc.vertex_id
    WHERE e.dst_vid LIKE 'at://did:web:hourei.gftd.ai/%'
       OR e.dst_vid IS NULL
    GROUP BY cc.contract_id, cc.clause_kind, cc.severity
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_contract_clause_hourei_coverage`.execute(db);
  for (const cite of CITES) {
    const edgeId = `edge:${cite.clauseCid}:cites:${cite.hourei}--${cite.art}`;
    await sql`DELETE FROM edge_cites WHERE edge_id = ${edgeId}`.execute(db);
  }
  for (const c of CLAUSES) {
    const vid = `at://did:web:bpmn.gftd.ai/ai.gftd.apps.gftdcojp.contractClause/${c.cid}`;
    await sql`DELETE FROM vertex_gftdcojp_contract_clause WHERE vertex_id = ${vid}`.execute(db);
  }
}
