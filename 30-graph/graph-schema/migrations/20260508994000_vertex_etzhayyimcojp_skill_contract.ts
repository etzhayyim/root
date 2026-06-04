import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * etzhayyim.etzhayyim.com Skill matrix + Contract registry
 * Principal: etzhayyim. Vendor: etzhayyim Japan株式会社.
 *
 * Tier 1 (objective, non-PII): skills, contracts, IP assignments.
 * Companion: 20260508995000_vertex_etzhayyim_profile_minimax_tier3
 * (Tier 3 = personality / minimax score / 保身 index, RLS-gated).
 *
 * Tables:
 *   vertex_etzhayyim_skill            Skill taxonomy (skill_id, name, category)
 *   vertex_etzhayyim_person_skill     person × skill × proficiency (1-5) + evidence
 *   vertex_etzhayyim_contract         Contract terms (employment / SOW / vendor)
 *   vertex_etzhayyim_contract_clause  IP / NDA / termination clauses per contract
 *   edge_etzhayyim_person_contract    person ↔ contract binding
 *
 * Streaming MVs:
 *   mv_etzhayyim_skill_coverage       skill_id × headcount × avg_proficiency
 *   mv_etzhayyim_active_contracts     active contracts with party info
 *
 * ADR-0036: Worker-direct Hyperdrive.
 * ADR-0018: Tier 1 (objective + non-PII).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Skill taxonomy ──────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_skill (
      vertex_id   varchar PRIMARY KEY,
      skill_id    varchar NOT NULL,
      name        varchar NOT NULL,
      name_ja     varchar,
      category    varchar,
      description varchar,
      created_at  varchar,
      sensitivity_ord int DEFAULT 100,
      owner_did   varchar)
  `.execute(db);

  // ── Person × Skill (proficiency 1-5 + evidence) ─────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_skill (
      vertex_id     varchar PRIMARY KEY,
      person_did    varchar NOT NULL,
      skill_id      varchar NOT NULL,
      proficiency   int DEFAULT 3,
      self_reported boolean DEFAULT true,
      peer_verified boolean DEFAULT false,
      verified_by   varchar,
      evidence_url  varchar,
      last_used_at  varchar,
      created_at    varchar,
      sensitivity_ord int DEFAULT 100,
      owner_did     varchar)
  `.execute(db);

  // ── Contract registry ───────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_contract (
      vertex_id        varchar PRIMARY KEY,
      contract_id      varchar NOT NULL,
      contract_kind    varchar NOT NULL,
      principal_did    varchar DEFAULT 'did:web:etz-hayim.etzhayyim.com',
      vendor_did       varchar,
      counterparty_did varchar NOT NULL,
      title            varchar,
      summary          varchar,
      start_date       varchar,
      end_date         varchar,
      auto_renewal     boolean DEFAULT false,
      monthly_rate_jpy double precision,
      currency         varchar DEFAULT 'JPY',
      payment_terms    varchar,
      status           varchar DEFAULT 'active',
      signed_at        varchar,
      contract_url     varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 200,
      owner_did        varchar)
  `.execute(db);

  // ── Contract clauses (IP / NDA / termination / non-compete) ────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_contract_clause (
      vertex_id      varchar PRIMARY KEY,
      contract_id    varchar NOT NULL,
      clause_kind    varchar NOT NULL,
      ip_assigned_to varchar,
      nda_scope      varchar,
      term_months    int,
      summary        varchar,
      summary_ja     varchar,
      severity       varchar DEFAULT 'medium',
      created_at     varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did      varchar)
  `.execute(db);

  // ── Person ↔ Contract edge ──────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_etzhayyim_person_contract (
      edge_id       varchar PRIMARY KEY,
      src_vid       varchar NOT NULL,
      dst_vid       varchar NOT NULL,
      person_did    varchar NOT NULL,
      contract_id   varchar NOT NULL,
      role_in_contract varchar,
      created_at    varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did     varchar)
  `.execute(db);

  // ── Streaming MVs ───────────────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_skill_coverage AS
    SELECT
      ps.skill_id,
      s.name,
      s.category,
      COUNT(DISTINCT ps.person_did) AS headcount,
      AVG(ps.proficiency)           AS avg_proficiency,
      MAX(ps.proficiency)           AS max_proficiency,
      SUM(CASE WHEN ps.peer_verified THEN 1 ELSE 0 END) AS verified_count
    FROM vertex_etzhayyim_person_skill ps
    LEFT JOIN vertex_etzhayyim_skill s ON s.skill_id = ps.skill_id
    GROUP BY ps.skill_id, s.name, s.category
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_active_contracts AS
    SELECT
      c.contract_id,
      c.contract_kind,
      c.counterparty_did,
      c.principal_did,
      c.vendor_did,
      c.title,
      c.start_date,
      c.end_date,
      c.monthly_rate_jpy,
      c.status,
      COUNT(DISTINCT cc.clause_kind) AS clause_count
    FROM vertex_etzhayyim_contract c
    LEFT JOIN vertex_etzhayyim_contract_clause cc ON cc.contract_id = c.contract_id
    WHERE c.status = 'active'
    GROUP BY c.contract_id, c.contract_kind, c.counterparty_did,
             c.principal_did, c.vendor_did, c.title, c.start_date,
             c.end_date, c.monthly_rate_jpy, c.status
  `.execute(db);

  // ── Seed: skill taxonomy (engineering core) ─────────────────────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_skill (vertex_id, skill_id, name, name_ja, category, description, created_at, owner_did)
    VALUES
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/deploy-cf-worker', 'deploy.cf-worker', 'Cloudflare Worker Deploy', 'CF Worker デプロイ', 'deploy', 'wrangler / etzhayyim deploy / VKE rollout', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/deploy-k8s-helm', 'deploy.k8s-helm', 'K8s Helm Operations', 'K8s Helm 運用', 'deploy', 'VKE / Helm / kubectl', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/review-code-quality', 'review.code-quality', 'Code Review (Quality)', 'コードレビュー (品質)', 'review', 'PR review / SOC2-grade audit trail', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/review-shannon-eta', 'review.shannon-eta', 'Shannon η Review', 'Shannon η レビュー', 'review', 'redundancy / 8-layer compliance', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/infra-risingwave', 'infra.risingwave', 'RisingWave Operations', 'RisingWave 運用', 'infra', 'streaming MV / Hyperdrive / B2 hummock', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/infra-vke', 'infra.vke', 'Vultr VKE Operations', 'Vultr VKE 運用', 'infra', 'BuildKit / cluster scaling', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/infra-security', 'infra.security', 'Infra Security', 'インフラセキュリティ', 'infra', 'IAM / vault / cert rotation', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/llm-langgraph', 'llm.langgraph', 'LangGraph Agent Design', 'LangGraph エージェント設計', 'llm', 'StateGraph / supervisor / HITL', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/bpmn-zeebe', 'bpmn.zeebe', 'BPMN-as-actor (Zeebe)', 'BPMN-as-actor (Zeebe)', 'workflow', 'pyzeebe / dispatcher / timer-start', now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.skill/sql-kysely', 'sql.kysely', 'Kysely + RisingWave SQL', 'Kysely + RW SQL', 'data', 'type-safe query / MV design', now()::varchar, 'did:web:etzhayyim.etzhayyim.com')
  `.execute(db);

  // ── Seed: person × skill (chikada / tanaka / nishino — chartered roles) ────
  await sql`
    INSERT INTO vertex_etzhayyim_person_skill (vertex_id, person_did, skill_id, proficiency, self_reported, peer_verified, verified_by, last_used_at, created_at, owner_did)
    VALUES
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/chikada-deploy-cf', 'did:web:t-chikada.etzhayyim.com', 'deploy.cf-worker', 5, true, true, 'did:web:j-kawasaki.etzhayyim.com', now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/chikada-deploy-k8s', 'did:web:t-chikada.etzhayyim.com', 'deploy.k8s-helm', 4, true, true, 'did:web:j-kawasaki.etzhayyim.com', now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/chikada-bpmn', 'did:web:t-chikada.etzhayyim.com', 'bpmn.zeebe', 4, true, false, NULL, now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/tanaka-review-quality', 'did:web:f-tanaka.etzhayyim.com', 'review.code-quality', 5, true, true, 'did:web:j-kawasaki.etzhayyim.com', now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/tanaka-review-shannon', 'did:web:f-tanaka.etzhayyim.com', 'review.shannon-eta', 4, true, true, 'did:web:j-kawasaki.etzhayyim.com', now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/tanaka-sql', 'did:web:f-tanaka.etzhayyim.com', 'sql.kysely', 4, true, false, NULL, now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/nishino-infra-rw', 'did:web:y-nishino.etzhayyim.com', 'infra.risingwave', 5, true, true, 'did:web:j-kawasaki.etzhayyim.com', now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/nishino-infra-vke', 'did:web:y-nishino.etzhayyim.com', 'infra.vke', 5, true, true, 'did:web:j-kawasaki.etzhayyim.com', now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.personSkill/nishino-infra-sec', 'did:web:y-nishino.etzhayyim.com', 'infra.security', 4, true, true, 'did:web:n-takahashi.etzhayyim.com', now()::varchar, now()::varchar, 'did:web:etzhayyim.etzhayyim.com')
  `.execute(db);

  // ── Seed: vendor SOW for etzhayyim Japan engineering capacity ───────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_contract (vertex_id, contract_id, contract_kind, principal_did, vendor_did, counterparty_did, title, summary, start_date, auto_renewal, monthly_rate_jpy, payment_terms, status, signed_at, created_at, owner_did)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contract/etzhayyim-japan-vendor-sow-v1',
        'etzhayyim-japan-vendor-sow-v1',
        'vendor_sow',
        'did:web:etz-hayim.etzhayyim.com',
        'did:web:etzhayyim-japan.etzhayyim.com',
        'did:web:etzhayyim-japan.etzhayyim.com',
        'etzhayyim Japan株式会社 Engineering Capacity SOW',
        'etzhayyim が etzhayyim Japan のエンジニアリング capacity を契約調達。IP は etzhayyim 帰属、開発成果物は work-for-hire',
        '2026-01-01',
        true,
        NULL,
        'monthly net-30',
        'active',
        '2026-01-01',
        now()::varchar,
        'did:web:etz-hayim.etzhayyim.com'
      )
  `.execute(db);

  // ── Seed: SOW clauses (IP assignment, NDA, termination) ─────────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_contract_clause (vertex_id, contract_id, clause_kind, ip_assigned_to, nda_scope, term_months, summary, summary_ja, severity, created_at, owner_did)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contractClause/etzhayyim-japan-ip-assignment',
        'etzhayyim-japan-vendor-sow-v1',
        'ip_assignment',
        'did:web:etz-hayim.etzhayyim.com',
        NULL, NULL,
        'All work product (code, schemas, BPMN, ADRs) created under SOW = work-for-hire, IP vests in etzhayyim immediately.',
        '本 SOW 配下で生成された全成果物 (コード/スキーマ/BPMN/ADR) は work-for-hire とし、IP は即時 etzhayyim に帰属。',
        'critical',
        now()::varchar,
        'did:web:etz-hayim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contractClause/etzhayyim-japan-nda',
        'etzhayyim-japan-vendor-sow-v1',
        'nda',
        NULL,
        'all etzhayyim platform internals + roadmap + customer info',
        60,
        'NDA covers all platform internals + roadmap + customer info. 5-year survival post-termination.',
        'プラットフォーム内部仕様/ロードマップ/顧客情報を全面 NDA。終了後 5 年間有効。',
        'high',
        now()::varchar,
        'did:web:etz-hayim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contractClause/etzhayyim-japan-termination',
        'etzhayyim-japan-vendor-sow-v1',
        'termination',
        NULL, NULL, NULL,
        'etzhayyim may terminate for convenience with 30 days notice. Vendor must hand over all materials + access.',
        'etzhayyim は 30 日前通知で随意解除可。Vendor は全資料・アクセス権を引き渡す。',
        'high',
        now()::varchar,
        'did:web:etz-hayim.etzhayyim.com'
      )
  `.execute(db);

  // ── Seed: bind 3 engineers to the etzhayyim Japan vendor SOW ────────────────────
  await sql`
    INSERT INTO edge_etzhayyim_person_contract (edge_id, src_vid, dst_vid, person_did, contract_id, role_in_contract, created_at, owner_did)
    VALUES
      (
        'edge://etzhayyim/personContract/chikada-vendor-sow',
        'did:web:t-chikada.etzhayyim.com',
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contract/etzhayyim-japan-vendor-sow-v1',
        'did:web:t-chikada.etzhayyim.com',
        'etzhayyim-japan-vendor-sow-v1',
        'eng-deploy',
        now()::varchar,
        'did:web:etz-hayim.etzhayyim.com'
      ),
      (
        'edge://etzhayyim/personContract/tanaka-vendor-sow',
        'did:web:f-tanaka.etzhayyim.com',
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contract/etzhayyim-japan-vendor-sow-v1',
        'did:web:f-tanaka.etzhayyim.com',
        'etzhayyim-japan-vendor-sow-v1',
        'eng-review',
        now()::varchar,
        'did:web:etz-hayim.etzhayyim.com'
      ),
      (
        'edge://etzhayyim/personContract/nishino-vendor-sow',
        'did:web:y-nishino.etzhayyim.com',
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.contract/etzhayyim-japan-vendor-sow-v1',
        'did:web:y-nishino.etzhayyim.com',
        'etzhayyim-japan-vendor-sow-v1',
        'eng-infra',
        now()::varchar,
        'did:web:etz-hayim.etzhayyim.com'
      )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_active_contracts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_skill_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_etzhayyim_person_contract`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_contract_clause`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_contract`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_skill`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_skill`.execute(db);
}
