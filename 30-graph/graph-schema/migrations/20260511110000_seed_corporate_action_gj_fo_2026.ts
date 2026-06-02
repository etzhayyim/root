import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 tier: B — seed data for etzhayyim Japan 定款変更プロジェクト 2026

/**
 * Seed: etzhayyim Japan株式会社 定款第２条変更 (プライベートオフィス専用化)
 *
 * 事業概要:
 *   23項目の現行目的（介護・障害福祉・IT受託・職業紹介等）を全廃し、
 *   プライベートオフィス専用6項目に変更する。
 *
 *   登記項目:
 *     ① 事業目的変更 (¥30,000) — 株主総会特別決議
 *     ② 役員任期10年 (¥30,000) — 中村リストとの合流 (同一決議)
 *   定款変更のみ (登記不要):
 *     ③ 招集通知3日
 *     ④ 議事録押印廃止
 *
 *   登記費用合計: ¥60,000 (①②を同一申請に合流した場合)
 *
 * 資料: _working/family-office-registration/ (7ファイル)
 * 連絡: 取締役会Teams投稿済 (2026-05-11, board@etzhayyim.com)
 *
 * Idempotent INSERT WHERE NOT EXISTS — re-applying is a no-op.
 */

const NOW = "2026-05-11T00:00:00Z";
const OWNER = "did:web:etzhayyim.com";
const RESPONSIBLE = "did:web:j-kawasaki.etzhayyim.com";

const ACTION_CODE = "GJ-CA-2026-001";
const ACTION_VID = `at://did:web:etzhayyim.com/com.etzhayyim.apps.kaisya.corporateAction/${ACTION_CODE}`;

type ActionItem = {
  itemCode: string;
  itemType: string;
  description: string;
  beforeText: string;
  afterText: string;
  requiresRegistration: boolean;
  registrationTaxJpy: number | null;
};

const ITEMS: ActionItem[] = [
  {
    itemCode: "GJ-CA-2026-001-01",
    itemType: "mokuteki_henkou",
    description: "定款第２条（目的）全面変更 — 23項目削除・プライベートオフィス専用6項目に置換",
    beforeText: [
      "１．コーチングサポート業務",
      "２．人材育成に関する業務",
      "（省略: 介護・障害福祉・IT受託・職業紹介等 全23項目）",
      "２３．前各号に関する技術援助及びコンサルティング業務",
      "前項各号に附帯関連する一切の事業",
    ].join("\n"),
    afterText: [
      "１．自己の資産の管理、運用及び保全に関する業務",
      "２．有価証券、デジタルアセット及び暗号資産の保有、運用管理及び売買",
      "３．不動産の取得、保有、管理及び処分",
      "４．国内外の会社の株式又は持分の取得及び保有並びに当該会社の経営管理",
      "５．資産の承継並びに相続及び事業承継の計画立案及び実行に関する業務",
      "６．前各号に附帯関連する一切の業務",
    ].join("\n"),
    requiresRegistration: true,
    registrationTaxJpy: 30000,
  },
  {
    itemCode: "GJ-CA-2026-001-02",
    itemType: "yakuin_henkou",
    description: "定款 役員任期を2年から10年に変更（中村リスト②）",
    beforeText: "取締役の任期は、選任後2年以内に終了する最終の事業年度に関する定時株主総会終結の時までとする。",
    afterText: "取締役の任期は、選任後10年以内に終了する最終の事業年度に関する定時株主総会終結の時までとする。",
    requiresRegistration: true,
    registrationTaxJpy: 30000,
  },
  {
    itemCode: "GJ-CA-2026-001-03",
    itemType: "teikan_henkou",
    description: "定款 株主総会招集通知期間を2週間前から3日前に短縮（中村リスト①）",
    beforeText: "株主総会を招集するには、会日より少なくとも2週間前に、議決権を行使することができる各株主に対してその通知を発しなければならない。",
    afterText: "株主総会を招集するには、会日より少なくとも3日前に、議決権を行使することができる各株主に対してその通知を発しなければならない。",
    requiresRegistration: false,
    registrationTaxJpy: null,
  },
  {
    itemCode: "GJ-CA-2026-001-04",
    itemType: "teikan_henkou",
    description: "定款 株主総会議事録・取締役会議事録の押印義務廃止（中村リスト①）",
    beforeText: "株主総会の議事については、議事録を作成し、出席した取締役及び監査役がこれに署名又は記名押印しなければならない。",
    afterText: "株主総会の議事については、議事録を作成する。署名又は記名押印は省略することができる。",
    requiresRegistration: false,
    registrationTaxJpy: null,
  },
];

type Doc = {
  edgeId: string;
  docRole: string;
  filePath: string;
};

const DOCS: Doc[] = [
  {
    edgeId: `${ACTION_CODE}/doc-readme`,
    docRole: "project_overview",
    filePath: "_working/family-office-registration/00-README.md",
  },
  {
    edgeId: `${ACTION_CODE}/doc-shinkyu`,
    docRole: "shinkyu_taisho",
    filePath: "_working/family-office-registration/01-teikan-shinkyu-taisho.md",
  },
  {
    edgeId: `${ACTION_CODE}/doc-gijiroku`,
    docRole: "gijiroku_draft",
    filePath: "_working/family-office-registration/02-kabunushi-sokai-gijiroku.md",
  },
  {
    edgeId: `${ACTION_CODE}/doc-shinseisho`,
    docRole: "shinseisho_draft",
    filePath: "_working/family-office-registration/03-touki-shinseisho.md",
  },
  {
    edgeId: `${ACTION_CODE}/doc-external`,
    docRole: "external_comms",
    filePath: "_working/family-office-registration/04-taisho-documents.md",
  },
  {
    edgeId: `${ACTION_CODE}/doc-legal-ref`,
    docRole: "legal_references",
    filePath: "_working/family-office-registration/05-yoyo-legal-references.md",
  },
  {
    edgeId: `${ACTION_CODE}/doc-board`,
    docRole: "board_comms",
    filePath: "_working/family-office-registration/06-teams-message-draft.md",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── vertex_corporate_action ───────────────────────────────────────────────
  await sql`
    INSERT INTO vertex_corporate_action
      (vertex_id, action_code, action_type, legal_entity_did, title, status,
       resolution_type, registration_tax_jpy, responsible_did, notes,
       created_at, owner_did)
    SELECT
      ${ACTION_VID},
      ${ACTION_CODE},
      'teikan_henkou',
      ${OWNER},
      '定款第２条変更・プライベートオフィス専用化 (2026)',
      'draft',
      'shomen_ketsugi',
      CAST(60000 AS BIGINT),
      ${RESPONSIBLE},
      '23項目から6項目へ全面変更。登記項目（目的変更¥30K＋役員任期10年¥30K）を1申請に合流。Teams通知済 2026-05-11。',
      ${NOW},
      ${OWNER}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_corporate_action WHERE vertex_id = ${ACTION_VID}
    )
  `.execute(db);

  // ── vertex_corporate_action_item ─────────────────────────────────────────
  for (const item of ITEMS) {
    const vid = `at://did:web:etzhayyim.com/com.etzhayyim.apps.kaisya.corporateActionItem/${item.itemCode}`;
    await sql`
      INSERT INTO vertex_corporate_action_item
        (vertex_id, action_vid, item_code, item_type, description,
         before_text, after_text, requires_registration, registration_tax_jpy,
         status, created_at, owner_did)
      SELECT
        ${vid},
        ${ACTION_VID},
        ${item.itemCode},
        ${item.itemType},
        ${item.description},
        ${item.beforeText},
        ${item.afterText},
        ${item.requiresRegistration},
        ${item.registrationTaxJpy === null ? null : String(item.registrationTaxJpy)},
        'pending',
        ${NOW},
        ${OWNER}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_corporate_action_item WHERE vertex_id = ${vid}
      )
    `.execute(db);
  }

  // ── edge_corporate_action_document ───────────────────────────────────────
  for (const doc of DOCS) {
    const eid = `at://did:web:etzhayyim.com/com.etzhayyim.apps.kaisya.corporateActionDocument/${doc.edgeId}`;
    await sql`
      INSERT INTO edge_corporate_action_document
        (edge_id, src_vid, action_code, doc_role, file_path, created_at, owner_did)
      SELECT
        ${eid},
        ${ACTION_VID},
        ${ACTION_CODE},
        ${doc.docRole},
        ${doc.filePath},
        ${NOW},
        ${OWNER}
      WHERE NOT EXISTS (
        SELECT 1 FROM edge_corporate_action_document WHERE edge_id = ${eid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const doc of DOCS) {
    const eid = `at://did:web:etzhayyim.com/com.etzhayyim.apps.kaisya.corporateActionDocument/${doc.edgeId}`;
    await sql`DELETE FROM edge_corporate_action_document WHERE edge_id = ${eid}`.execute(db);
  }
  for (const item of ITEMS) {
    const vid = `at://did:web:etzhayyim.com/com.etzhayyim.apps.kaisya.corporateActionItem/${item.itemCode}`;
    await sql`DELETE FROM vertex_corporate_action_item WHERE vertex_id = ${vid}`.execute(db);
  }
  await sql`DELETE FROM vertex_corporate_action WHERE vertex_id = ${ACTION_VID}`.execute(db);
}
