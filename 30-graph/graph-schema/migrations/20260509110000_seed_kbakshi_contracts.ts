import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed: k-bakshi (Kuunal Bakshi) employment contract lineage.
 *
 * Source documents (M365 SharePoint, audited 2026-05-08):
 *   - GJ_労働条件通知書_バクシ・クナル様.pdf                              (2025-05-08)
 *   - 20250601_GJ_雇用契約書兼労働条件通知書_クナル・バクシ.pdf            (2025-05-11, effective 2025-06-01)
 *   - (1年に変更)GJ_雇用契約書兼労働条件通知書.docx                          (2025-05-28, 1y term amendment)
 *
 * Lineage:
 *   labor-notice-2025-05-08
 *     ←─ supersedes ── employment-2025-06-01
 *                          ←─ amendment ── employment-2025-06-01-amended-1y
 *
 * Tier 3 PII (sensitivity_ord=300). owner_did = etzhayyim (operating entity).
 * principal_did = etzhayyim. counterparty_did = k-bakshi.
 *
 * NOTE: Day-1 audit row with source URI only. Clause extraction (Step 2 of
 * contract-clause-statute-mapping-plan.md) lands in a follow-up migration.
 */
const NOW = "2026-05-08T00:00:00Z";
const OWNER = "did:web:etz-hayim.etzhayyim.com";
const COUNTERPARTY = "did:web:k-bakshi.etzhayyim.com";
const PRINCIPAL_etzhayyim_JAPAN = "did:web:etzhayyim-japan.etzhayyim.com";

const CONTRACTS = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contract/kbakshi-labor-notice-2025-05-08",
    contractId: "kbakshi-labor-notice-2025-05-08",
    contractKind: "labor_condition_notice",
    title: "労働条件通知書 (Kuunal Bakshi)",
    summary: "労基法15条に基づく労働条件通知書 (1次)。雇用形態 / 賃金 / 就業時間 / 休日 / 社保 を明示。",
    startDate: "2025-05-08",
    endDate: null,
    signedAt: "2025-05-08",
    contractUrl: "sharepoint://etzhayyim.com/Shared%20Documents/HR/GJ_労働条件通知書_バクシ・クナル様.pdf",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contract/kbakshi-employment-2025-06-01",
    contractId: "kbakshi-employment-2025-06-01",
    contractKind: "employment",
    title: "雇用契約書兼労働条件通知書 (Kuunal Bakshi, v1 期間定めなし)",
    summary: "etzhayyim Japan株式会社 採用、CLO 兼 LLP DP 候補。allocation 50%。当初 期間定めなし版。",
    startDate: "2025-06-01",
    endDate: null,
    signedAt: "2025-05-11",
    contractUrl: "sharepoint://etzhayyim.com/Shared%20Documents/HR/20250601_GJ_雇用契約書兼労働条件通知書_クナル・バクシ.pdf",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contract/kbakshi-employment-2025-06-01-amended-1y",
    contractId: "kbakshi-employment-2025-06-01-amended-1y",
    contractKind: "employment",
    title: "雇用契約書兼労働条件通知書 (Kuunal Bakshi, v2 1年契約)",
    summary: "v1 を 1年契約に修正 (2026-05-31迄)。在留資格変更受理 + 外弁申請に伴う雇用継続性確保のため期間明示化。",
    startDate: "2025-06-01",
    endDate: "2026-05-31",
    signedAt: "2025-05-28",
    contractUrl: "sharepoint://etzhayyim.com/Shared%20Documents/HR/(1年に変更)GJ_雇用契約書兼労働条件通知書.docx",
  },
];

const DEPS = [
  {
    edgeId: "edge:kbakshi-employment-2025-06-01-supersedes-labor-notice",
    srcVid: CONTRACTS[1].vertexId,
    dstVid: CONTRACTS[0].vertexId,
    relKind: "supersedes",
    effectiveAt: "2025-06-01",
  },
  {
    edgeId: "edge:kbakshi-employment-2025-06-01-amended-1y-amendment-of-v1",
    srcVid: CONTRACTS[2].vertexId,
    dstVid: CONTRACTS[1].vertexId,
    relKind: "amendment",
    effectiveAt: "2025-05-28",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── edge_contract_dep ── (idempotent CREATE; first migration that needs it)
  await sql`
    CREATE TABLE IF NOT EXISTS edge_contract_dep (
      edge_id      varchar PRIMARY KEY,
      src_vid      varchar NOT NULL,
      dst_vid      varchar NOT NULL,
      rel_kind     varchar NOT NULL,
      effective_at varchar,
      created_at   varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did    varchar)
  `.execute(db);

  for (const c of CONTRACTS) {
    await sql`
      INSERT INTO vertex_etzhayyim_contract
        (vertex_id, contract_id, contract_kind, principal_did, vendor_did,
         counterparty_did, title, summary, start_date, end_date,
         auto_renewal, monthly_rate_jpy, currency, payment_terms, status,
         signed_at, contract_url, created_at, sensitivity_ord, owner_did)
      SELECT
        ${c.vertexId}, ${c.contractId}, ${c.contractKind}, ${OWNER}, ${PRINCIPAL_etzhayyim_JAPAN},
        ${COUNTERPARTY}, ${c.title}, ${c.summary}, ${c.startDate}, ${c.endDate},
        false, CAST(NULL AS DOUBLE PRECISION), 'JPY', '当月末締翌月末払 (社員給与同準)', 'active',
        ${c.signedAt}, ${c.contractUrl}, ${NOW}, 300, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_etzhayyim_contract WHERE vertex_id = ${c.vertexId})
    `.execute(db);

    // person ↔ contract edge (k-bakshi as employee)
    const edgeId = `edge:${c.contractId}:kbakshi-employee`;
    await sql`
      INSERT INTO edge_etzhayyim_person_contract
        (edge_id, src_vid, dst_vid, person_did, contract_id,
         role_in_contract, created_at, sensitivity_ord, owner_did)
      SELECT
        ${edgeId}, ${COUNTERPARTY}, ${c.vertexId},
        ${COUNTERPARTY}, ${c.contractId}, 'employee',
        ${NOW}, 300, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM edge_etzhayyim_person_contract WHERE edge_id = ${edgeId})
    `.execute(db);
  }

  for (const d of DEPS) {
    await sql`
      INSERT INTO edge_contract_dep
        (edge_id, src_vid, dst_vid, rel_kind, effective_at,
         created_at, sensitivity_ord, owner_did)
      SELECT
        ${d.edgeId}, ${d.srcVid}, ${d.dstVid}, ${d.relKind}, ${d.effectiveAt},
        ${NOW}, 300, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM edge_contract_dep WHERE edge_id = ${d.edgeId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const d of DEPS) {
    await sql`DELETE FROM edge_contract_dep WHERE edge_id = ${d.edgeId}`.execute(db);
  }
  for (const c of CONTRACTS) {
    const edgeId = `edge:${c.contractId}:kbakshi-employee`;
    await sql`DELETE FROM edge_etzhayyim_person_contract WHERE edge_id = ${edgeId}`.execute(db);
    await sql`DELETE FROM vertex_etzhayyim_contract WHERE vertex_id = ${c.vertexId}`.execute(db);
  }
}
