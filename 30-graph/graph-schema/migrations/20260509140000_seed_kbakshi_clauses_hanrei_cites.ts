import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed: leading 判例 case records + clause→hanrei cite edges.
 *
 * Companion to 20260509130000 (clause→hourei). Hourei sets the statutory
 * frame, hanrei sets the judicial-interpretation frame. Together they form
 * dual-source legal traceability for each k-bakshi contract clause.
 *
 * Targets vertex_hanrei_case_record (existing, seeded 2026-04-29).
 * actor_did / org_did = hanrei.etzhayyim.com (curation-tier provenance).
 *
 * k-bakshi sign-off required before any external publication of cite edges.
 */
const NOW = "2026-05-08 00:00:00";
const HANREI_OWNER = "did:web:hanrei.etzhayyim.com";

type CaseRec = {
  rkey: string;
  title: string;
  caseNumber: string;
  court: string;            // court_id reference
  decisionDate: string;
  summary: string;
};

const CASES: CaseRec[] = [
  {
    rkey: "foseco-japan-1970",
    title: "フォセコ・ジャパン・リミテッド事件",
    caseNumber: "奈良地判 昭和45年10月23日",
    court: "court:nara-district",
    decisionDate: "1970-10-23",
    summary: "退職後競業避止義務有効性判断の 4 要素 (期間・地域・業務範囲・代償措置) 確立。",
  },
  {
    rkey: "art-nature-2005",
    title: "アートネイチャー事件",
    caseNumber: "東京地判 平成17年2月23日",
    court: "court:tokyo-district",
    decisionDate: "2005-02-23",
    summary: "営業秘密 + 退職後競業避止 重畳判断。代償措置不在 = 公序良俗違反で無効。",
  },
  {
    rkey: "kochi-broadcasting-1977",
    title: "高知放送事件",
    caseNumber: "最判 昭和52年1月31日",
    court: "court:supreme-court",
    decisionDate: "1977-01-31",
    summary: "解雇権濫用法理確立。客観合理性 + 社会通念相当性 を欠く解雇は無効。",
  },
  {
    rkey: "toyo-sanso-1979",
    title: "東洋酸素事件",
    caseNumber: "東京高判 昭和54年10月29日",
    court: "court:tokyo-high",
    decisionDate: "1979-10-29",
    summary: "整理解雇 4 要件 (人員削減必要性 / 解雇回避努力 / 人選合理性 / 手続妥当性) 確立。",
  },
  {
    rkey: "rgb-adventure-2012",
    title: "RGB アドベンチャー事件",
    caseNumber: "知財高判 平成24年10月25日",
    court: "court:ip-high",
    decisionDate: "2012-10-25",
    summary: "職務著作 (著作権法15条) 該当性判断 = 法人発意 + 業務従事者の職務 + 法人名義公表 + 別段合意なし。",
  },
  {
    rkey: "toa-paint-1986",
    title: "東亜ペイント事件",
    caseNumber: "最判 昭和61年7月14日",
    court: "court:supreme-court",
    decisionDate: "1986-07-14",
    summary: "配転命令権の濫用判断 = 業務上必要性 + 不当な動機 + 通常甘受すべき程度を超える不利益。",
  },
  {
    rkey: "northwest-airlines-1987",
    title: "ノースウエスト航空事件",
    caseNumber: "最判 昭和62年7月17日",
    court: "court:supreme-court",
    decisionDate: "1987-07-17",
    summary: "賃金請求権の発生根拠 = 労働契約上の合意 + 就業規則。労働者の労務提供が前提。",
  },
];

type Cite = {
  clauseCid: string;
  caseRkey: string;
  citationType: "persuasive" | "binding" | "interpretive";
  paragraph: string;        // どの判旨を引用するか
};

const CITES: Cite[] = [
  // non_compete → フォセコ + アートネイチャー
  { clauseCid: "kbakshi-1y-non-compete",   caseRkey: "foseco-japan-1970",        citationType: "persuasive", paragraph: "競業避止 4 要素 (期間 12mo / 地理 JP+IN / 業務範囲限定 / 代償措置) 適合性判断" },
  { clauseCid: "kbakshi-1y-non-compete",   caseRkey: "art-nature-2005",          citationType: "persuasive", paragraph: "代償措置あり故に有効推認、無代償なら無効リスク" },
  // termination → 高知放送 + 東洋酸素
  { clauseCid: "kbakshi-1y-termination",   caseRkey: "kochi-broadcasting-1977",  citationType: "binding",    paragraph: "解雇権濫用法理 (労契法16条の判例淵源)" },
  { clauseCid: "kbakshi-1y-termination",   caseRkey: "toyo-sanso-1979",          citationType: "persuasive", paragraph: "整理解雇 4 要件 (経営悪化時の適用基準)" },
  // ip_assignment → RGB アドベンチャー
  { clauseCid: "kbakshi-1y-ip-assignment", caseRkey: "rgb-adventure-2012",       citationType: "binding",    paragraph: "職務著作 4 要件 (法人発意 / 業務従事 / 法人名義 / 別段合意なし) の判断基準" },
  // wages → ノースウエスト
  { clauseCid: "kbakshi-1y-wages",         caseRkey: "northwest-airlines-1987",  citationType: "interpretive", paragraph: "賃金請求権の発生根拠論" },
  // governing_law (transfer / 配転) → 東亜ペイント (条項明示なくとも黙示で配転権発生する場合の判断軸)
  { clauseCid: "kbakshi-1y-governing-law", caseRkey: "toa-paint-1986",           citationType: "interpretive", paragraph: "配転命令権濫用判断 (本契約は限定なし故 全国・全業務 黙示配転権の上限)" },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── case records ────────────────────────────────────────────────────────────
  for (const c of CASES) {
    const vid = `at://did:web:hanrei.etzhayyim.com/ai.gftd.apps.hanrei.caseRecord/${c.rkey}`;
    await sql`
      INSERT INTO vertex_hanrei_case_record
        (vertex_id, rkey, title, case_number, court_id, decision_date,
         summary, iso3, status, actor_did, org_did, created_at)
      SELECT
        ${vid}, ${c.rkey}, ${c.title}, ${c.caseNumber}, ${c.court},
        ${c.decisionDate}, ${c.summary}, 'jpn', 'active',
        ${HANREI_OWNER}, ${HANREI_OWNER}, CAST(${NOW} AS timestamp)
      WHERE NOT EXISTS (SELECT 1 FROM vertex_hanrei_case_record WHERE vertex_id = ${vid})
    `.execute(db);
  }

  // ── clause→hanrei cite edges via edge_cites ─────────────────────────────────
  for (const cite of CITES) {
    const srcVid = `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.gftdcojp.contractClause/${cite.clauseCid}`;
    const dstVid = `at://did:web:hanrei.etzhayyim.com/ai.gftd.apps.hanrei.caseRecord/${cite.caseRkey}`;
    const edgeId = `edge:${cite.clauseCid}:cites:hanrei--${cite.caseRkey}`;
    const label = `判例 ${cite.caseRkey} — ${cite.paragraph}`;
    await sql`
      INSERT INTO edge_cites
        (edge_id, src_vid, dst_vid, owner_did, label,
         citation_type, paragraph, jurisdiction)
      SELECT
        ${edgeId}, ${srcVid}, ${dstVid}, ${HANREI_OWNER}, ${label},
        ${cite.citationType}, ${cite.paragraph}, 'JP'
      WHERE NOT EXISTS (SELECT 1 FROM edge_cites WHERE edge_id = ${edgeId})
    `.execute(db);
  }

  // ── full clause coverage MV (hourei + hanrei union) ────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_contract_clause_full_coverage AS
    SELECT
      cc.contract_id,
      cc.clause_kind,
      cc.severity,
      COUNT(DISTINCT e.dst_vid) FILTER (WHERE e.dst_vid LIKE 'at://did:web:hourei.etzhayyim.com/%') AS hourei_cites,
      COUNT(DISTINCT e.dst_vid) FILTER (WHERE e.dst_vid LIKE 'at://did:web:hanrei.etzhayyim.com/%') AS hanrei_cites,
      COUNT(DISTINCT e.dst_vid)                                                                AS total_cites
    FROM vertex_gftdcojp_contract_clause cc
    LEFT JOIN edge_cites e ON e.src_vid = cc.vertex_id
    GROUP BY cc.contract_id, cc.clause_kind, cc.severity
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_contract_clause_full_coverage`.execute(db);
  for (const cite of CITES) {
    const edgeId = `edge:${cite.clauseCid}:cites:hanrei--${cite.caseRkey}`;
    await sql`DELETE FROM edge_cites WHERE edge_id = ${edgeId}`.execute(db);
  }
  for (const c of CASES) {
    const vid = `at://did:web:hanrei.etzhayyim.com/ai.gftd.apps.hanrei.caseRecord/${c.rkey}`;
    await sql`DELETE FROM vertex_hanrei_case_record WHERE vertex_id = ${vid}`.execute(db);
  }
}
