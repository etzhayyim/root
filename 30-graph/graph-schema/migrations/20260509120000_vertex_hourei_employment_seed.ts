import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_hourei + vertex_hourei_jobun — 法令 / 条文 vertex schema.
 *
 * Seeds 14 laws + 32 key articles relevant to employment contracts.
 * Article body text = short Japanese summary (full statutory text loaded
 * later via e-Gov 法令 API ingest worker — out of migration scope).
 *
 * Identifiers follow at://did:web:hourei.etzhayyim.com/... convention so
 * edge_cites (existing) can reference them as dst_vid.
 *
 * Cite linkage to vertex_etzhayyim_contract_clause lands in a follow-up
 * migration (clause→hourei seed), which CEO/k-bakshi must sign-off
 * row-by-row (legal interpretation).
 */
const NOW = "2026-05-08T00:00:00Z";
const OWNER = "did:web:hourei.etzhayyim.com";

const HOUREI = [
  { hid: "labor-standards-act",          short: "労働基準法",                   en: "Labor Standards Act",                 cat: "labor",          enacted: "1947-04-07", lawNo: "昭和22年法律第49号" },
  { hid: "labor-contract-act",           short: "労働契約法",                   en: "Labor Contracts Act",                  cat: "labor",          enacted: "2007-12-05", lawNo: "平成19年法律第128号" },
  { hid: "minimum-wage-act",             short: "最低賃金法",                   en: "Minimum Wages Act",                    cat: "labor",          enacted: "1959-04-15", lawNo: "昭和34年法律第137号" },
  { hid: "industrial-safety-health-act", short: "労働安全衛生法",               en: "Industrial Safety and Health Act",     cat: "labor",          enacted: "1972-06-08", lawNo: "昭和47年法律第57号" },
  { hid: "equal-employment-opportunity-act", short: "男女雇用機会均等法",        en: "Equal Employment Opportunity Act",     cat: "labor",          enacted: "1972-07-01", lawNo: "昭和47年法律第113号" },
  { hid: "childcare-family-care-leave-act",   short: "育児・介護休業法",         en: "Childcare and Family Care Leave Act",  cat: "labor",          enacted: "1991-05-15", lawNo: "平成3年法律第76号" },
  { hid: "trade-union-act",              short: "労働組合法",                   en: "Trade Union Act",                       cat: "labor",          enacted: "1949-06-01", lawNo: "昭和24年法律第174号" },
  { hid: "employment-insurance-act",     short: "雇用保険法",                   en: "Employment Insurance Act",              cat: "social_insurance", enacted: "1974-12-28", lawNo: "昭和49年法律第116号" },
  { hid: "health-insurance-act",         short: "健康保険法",                   en: "Health Insurance Act",                  cat: "social_insurance", enacted: "1922-04-22", lawNo: "大正11年法律第70号" },
  { hid: "appi",                         short: "個人情報保護法",               en: "Act on the Protection of Personal Information", cat: "data_protection", enacted: "2003-05-30", lawNo: "平成15年法律第57号" },
  { hid: "unfair-competition-prevention-act", short: "不正競争防止法",            en: "Unfair Competition Prevention Act",   cat: "ip_trade_secret", enacted: "1993-05-19", lawNo: "平成5年法律第47号" },
  { hid: "copyright-act",                short: "著作権法",                     en: "Copyright Act",                         cat: "ip",             enacted: "1970-05-06", lawNo: "昭和45年法律第48号" },
  { hid: "civil-code",                   short: "民法",                         en: "Civil Code",                            cat: "general",        enacted: "1896-04-27", lawNo: "明治29年法律第89号" },
  { hid: "companies-act",                short: "会社法",                       en: "Companies Act",                         cat: "corporate",      enacted: "2005-07-26", lawNo: "平成17年法律第86号" },
];

const JOBUN = [
  // 労基法
  { hid: "labor-standards-act", art: "15",  title: "労働条件の明示",          summary: "使用者は労働契約締結時に労働条件を明示。明示と相違の場合、労働者は即時解除可。" },
  { hid: "labor-standards-act", art: "24",  title: "賃金支払の5原則",        summary: "通貨/直接/全額/月1回以上/一定期日 払。" },
  { hid: "labor-standards-act", art: "32",  title: "法定労働時間",            summary: "1日8時間 / 週40時間。" },
  { hid: "labor-standards-act", art: "36",  title: "時間外労働協定 (36協定)", summary: "労使協定 + 労基署届出で時間外労働可。上限規制あり。" },
  { hid: "labor-standards-act", art: "37",  title: "時間外・休日・深夜割増賃金", summary: "時間外25%/休日35%/深夜25%/月60h超50% (中小2023~)。" },
  { hid: "labor-standards-act", art: "39",  title: "年次有給休暇",            summary: "勤続6月で10日。年5日取得義務 (2019~)。" },
  { hid: "labor-standards-act", art: "89",  title: "就業規則作成義務",        summary: "常時10人以上使用 = 就業規則作成 + 労基署届出義務。" },
  // 労契法
  { hid: "labor-contract-act", art: "3",  title: "労働契約の原則",            summary: "対等合意 / 均衡考慮 / 仕事と生活調和 / 信義則 / 権利濫用禁止。" },
  { hid: "labor-contract-act", art: "16", title: "解雇権濫用法理",            summary: "客観合理性 + 社会通念相当性 を欠く解雇 = 無効。" },
  { hid: "labor-contract-act", art: "18", title: "有期→無期転換 (5年ルール)", summary: "通算5年超の有期契約 = 労働者申込で無期転換権。" },
  { hid: "labor-contract-act", art: "19", title: "雇止め法理",                summary: "実質無期 / 合理的期待 ある雇止め = 解雇権濫用法理準用。" },
  // 個情法
  { hid: "appi", art: "17",  title: "利用目的の特定",                          summary: "個人情報取得時に利用目的を特定。" },
  { hid: "appi", art: "23",  title: "第三者提供の制限",                        summary: "本人同意なき第三者提供禁止 (例外あり)。" },
  { hid: "appi", art: "27",  title: "オプトアウト方式 第三者提供",            summary: "事前通知 + 個人情報委員会届出で本人同意不要。要配慮個人情報は不可。" },
  { hid: "appi", art: "28",  title: "外国にある第三者への提供制限",            summary: "原則本人同意必須 (適切体制基準国は除く)。DPDP / GDPR-region と相互運用設計の根拠。" },
  // 不競法
  { hid: "unfair-competition-prevention-act", art: "2-1-4", title: "営業秘密の不正取得", summary: "窃取/詐欺等で営業秘密取得 = 不正競争。" },
  { hid: "unfair-competition-prevention-act", art: "2-1-7", title: "営業秘密の不正使用 (元従業員)", summary: "正当取得後に図利加害目的で使用 = 不正競争。退職後競業避止のコア根拠。" },
  // 著作権法
  { hid: "copyright-act", art: "15", title: "職務著作",                        summary: "法人等業務従事者 が職務上作成 + 法人名義公表 = 法人著作。雇用契約のIP帰属の根拠。" },
  { hid: "copyright-act", art: "27", title: "翻訳権・翻案権等",                summary: "原著作者が翻訳/編曲/変形/翻案権を専有。" },
  { hid: "copyright-act", art: "28", title: "二次的著作物の利用権",            summary: "原著作者が二次的著作物利用に同等権利。" },
  { hid: "copyright-act", art: "59", title: "著作者人格権の一身専属性",        summary: "著作者人格権 (公表/氏名表示/同一性保持) は譲渡不可。雇用契約での moral rights 不行使条項の根拠。" },
  // 民法
  { hid: "civil-code", art: "90",   title: "公序良俗",                         summary: "公序良俗違反の法律行為は無効。退職後競業避止有効性判断の根拠。" },
  { hid: "civil-code", art: "415",  title: "債務不履行責任",                   summary: "債務不履行による損害賠償。" },
  { hid: "civil-code", art: "623",  title: "雇用契約の定義",                   summary: "労働従事 + 報酬支払 = 雇用契約。" },
  { hid: "civil-code", art: "627",  title: "期間定めなき雇用解約",             summary: "各当事者いつでも解約申入可、2週間で終了。労基法・労契法が修正。" },
  { hid: "civil-code", art: "709",  title: "不法行為責任",                     summary: "故意過失による権利侵害損害賠償。" },
  { hid: "civil-code", art: "715",  title: "使用者責任",                       summary: "事業執行で被用者が第三者に与えた損害を使用者が賠償。" },
  // 会社法
  { hid: "companies-act", art: "330", title: "委任関係",                       summary: "会社と取締役は委任関係。雇用ではない。役員契約の根拠。" },
  { hid: "companies-act", art: "356", title: "競業取引承認",                   summary: "取締役の競業取引は株主総会承認。" },
  { hid: "companies-act", art: "423", title: "取締役の任務懈怠責任",           summary: "任務懈怠で会社に損害 = 賠償責任。" },
  // 雇均法 / 育介法 / 最賃法 / 労安衛法 / 雇用保険法 / 健保法 / 労組法 — 各法 1 条のみ seed (拡張は後続 ingest worker)
  { hid: "minimum-wage-act", art: "4", title: "最低賃金以上の支払義務",        summary: "使用者は最低賃金額以上を支払う義務。" },
  { hid: "industrial-safety-health-act", art: "66", title: "健康診断",         summary: "使用者は労働者に医師健康診断を実施する義務。" },
  { hid: "equal-employment-opportunity-act", art: "5", title: "募集採用差別禁止", summary: "性別を理由とする募集・採用差別禁止。" },
  { hid: "childcare-family-care-leave-act", art: "5", title: "育児休業申出権", summary: "1歳未満の子を養育する労働者は育児休業申出可。" },
  { hid: "trade-union-act", art: "7", title: "不当労働行為禁止",               summary: "組合員理由の不利益取扱 / 黄犬契約 / 団交拒否 / 支配介入 を禁止。" },
  { hid: "employment-insurance-act", art: "4", title: "被保険者の定義",        summary: "適用事業に雇用される労働者 = 被保険者。" },
  { hid: "health-insurance-act", art: "3", title: "被保険者の定義",            summary: "適用事業所に使用される者 = 被保険者。" },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hourei (
      vertex_id        varchar PRIMARY KEY,
      hourei_id        varchar NOT NULL,
      short_name       varchar NOT NULL,
      short_name_en    varchar,
      category         varchar,
      law_number       varchar,
      enacted_at       varchar,
      last_amended_at  varchar,
      source_uri       varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 0,
      owner_did        varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hourei_jobun (
      vertex_id        varchar PRIMARY KEY,
      hourei_id        varchar NOT NULL,
      article_no       varchar NOT NULL,
      title            varchar,
      summary          varchar,
      text             varchar,
      text_byte_size   int,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 0,
      owner_did        varchar)
  `.execute(db);

  for (const h of HOUREI) {
    const vid = `at://did:web:hourei.etzhayyim.com/app.etzhayyim.apps.hourei.law/${h.hid}`;
    const sourceUri = `https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/?lawId=${encodeURIComponent(h.lawNo)}`;
    await sql`
      INSERT INTO vertex_hourei
        (vertex_id, hourei_id, short_name, short_name_en, category,
         law_number, enacted_at, source_uri, created_at, sensitivity_ord, owner_did)
      SELECT
        ${vid}, ${h.hid}, ${h.short}, ${h.en}, ${h.cat},
        ${h.lawNo}, ${h.enacted}, ${sourceUri}, ${NOW}, 0, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_hourei WHERE vertex_id = ${vid})
    `.execute(db);
  }

  for (const j of JOBUN) {
    const vid = `at://did:web:hourei.etzhayyim.com/app.etzhayyim.apps.hourei.article/${j.hid}--${j.art}`;
    const size = Buffer.byteLength(j.summary, "utf8");
    await sql`
      INSERT INTO vertex_hourei_jobun
        (vertex_id, hourei_id, article_no, title, summary,
         text_byte_size, created_at, sensitivity_ord, owner_did)
      SELECT
        ${vid}, ${j.hid}, ${j.art}, ${j.title}, ${j.summary},
        CAST(${size} AS integer), ${NOW}, 0, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_hourei_jobun WHERE vertex_id = ${vid})
    `.execute(db);
  }

  // ── coverage MV: per-law article count + last-update ─────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourei_coverage AS
    SELECT
      h.hourei_id,
      h.short_name,
      h.category,
      COUNT(j.vertex_id) AS article_count,
      MAX(j.created_at)  AS last_seeded_at
    FROM vertex_hourei h
    LEFT JOIN vertex_hourei_jobun j ON j.hourei_id = h.hourei_id
    GROUP BY h.hourei_id, h.short_name, h.category
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_hourei_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_hourei_jobun`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_hourei`.execute(db);
}
