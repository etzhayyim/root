import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * etzhayyim.etzhayyim.com Personnel Management schema
 * Principal: etzhayyim. Vendor: etzhayyim Japan株式会社.
 *
 * Tables:
 *   vertex_etzhayyim_person       People registry (contractors + employees)
 *   vertex_etzhayyim_role         Role definitions per department
 *   vertex_etzhayyim_assignment   Person ↔ Role/Project assignment
 *   vertex_etzhayyim_raci         RACI matrix (R/A/C/I per task × person)
 *   vertex_etzhayyim_okr          OKR tracking per person/team
 *
 * Streaming MVs:
 *   mv_etzhayyim_active_assignments  open assignments with role info
 *   mv_etzhayyim_raci_by_task        RACI summary per task NSID
 *
 * ADR-0036: Worker-direct Hyperdrive.
 * ADR-2605080600: LangGraph Server L3 Runtime (etzhayyim-company-ops graph).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const createdAt = new Date().toISOString();
  // ── People registry ─────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person (
      vertex_id       varchar PRIMARY KEY,
      person_did      varchar NOT NULL,
      display_name    varchar NOT NULL,
      display_name_ja varchar,
      email           varchar,
      employment_type varchar DEFAULT 'contractor',
      department      varchar,
      title           varchar,
      title_ja        varchar,
      status          varchar DEFAULT 'active',
      joined_at       varchar,
      contract_end_at varchar,
      github_handle   varchar,
      timezone        varchar DEFAULT 'Asia/Tokyo',
      created_at      varchar,
      owner_did       varchar)
  `.execute(db);

  // ── Role definitions ─────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_role (
      vertex_id       varchar PRIMARY KEY,
      role_id         varchar NOT NULL,
      role_name       varchar NOT NULL,
      role_name_ja    varchar,
      department      varchar,
      level           varchar DEFAULT 'individual',
      description     varchar,
      permissions_json varchar DEFAULT '[]',
      is_leadership   boolean DEFAULT false,
      created_at      varchar,
      owner_did       varchar)
  `.execute(db);

  // ── Person ↔ Role/Project assignments ───────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_assignment (
      vertex_id       varchar PRIMARY KEY,
      person_did      varchar NOT NULL,
      role_id         varchar NOT NULL,
      project_id      varchar,
      project_name    varchar,
      allocation_pct  double precision DEFAULT 100.0,
      start_date      varchar,
      end_date        varchar,
      status          varchar DEFAULT 'active',
      notes           varchar,
      assigned_by_did varchar,
      created_at      varchar,
      owner_did       varchar)
  `.execute(db);

  // ── RACI matrix ──────────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_raci (
      vertex_id       varchar PRIMARY KEY,
      task_nsid       varchar NOT NULL,
      task_name       varchar,
      task_name_ja    varchar,
      domain          varchar,
      person_did      varchar NOT NULL,
      raci_role       varchar NOT NULL,
      context         varchar,
      effective_date  varchar,
      status          varchar DEFAULT 'active',
      created_at      varchar,
      owner_did       varchar)
  `.execute(db);

  // ── OKR tracking ─────────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_okr (
      vertex_id        varchar PRIMARY KEY,
      person_did       varchar,
      team             varchar,
      period           varchar NOT NULL,
      objective        varchar NOT NULL,
      key_result       varchar NOT NULL,
      target_value     double precision,
      current_value    double precision DEFAULT 0.0,
      progress_pct     double precision DEFAULT 0.0,
      status           varchar DEFAULT 'active',
      updated_at       varchar,
      created_at       varchar,
      owner_did        varchar)
  `.execute(db);

  // ── Streaming MVs ─────────────────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_active_assignments AS
    SELECT
      a.person_did,
      a.role_id,
      a.project_id,
      a.project_name,
      a.allocation_pct,
      a.start_date,
      a.end_date,
      p.display_name,
      p.display_name_ja,
      p.department,
      p.title,
      p.title_ja,
      r.role_name,
      r.role_name_ja,
      r.is_leadership
    FROM vertex_etzhayyim_assignment a
    LEFT JOIN vertex_etzhayyim_person p ON p.person_did = a.person_did
    LEFT JOIN vertex_etzhayyim_role r ON r.role_id = a.role_id
    WHERE a.status = 'active'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_raci_by_task AS
    SELECT
      r.task_nsid,
      r.task_name,
      r.domain,
      r.raci_role,
      COUNT(*) AS person_count,
      STRING_AGG(p.display_name, ', ') AS persons
    FROM vertex_etzhayyim_raci r
    LEFT JOIN vertex_etzhayyim_person p ON p.person_did = r.person_did
    WHERE r.status = 'active'
    GROUP BY r.task_nsid, r.task_name, r.domain, r.raci_role
  `.execute(db);

  // ── Seed: People registry (all 9 known members) ───────────────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_person
      (vertex_id, person_did, display_name, display_name_ja, employment_type, department, title, title_ja, status, joined_at, timezone, created_at, owner_did)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/j-kawasaki',
        'did:web:j-kawasaki.etzhayyim.com',
        'Jun Kawasaki', '川崎 潤',
        'founder', 'executive', 'CEO', '最高経営責任者',
        'active', '2023-01-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/a-nakamura',
        'did:web:a-nakamura.etzhayyim.com',
        'A. Nakamura', '中村 A',
        'employee', 'executive', 'COO', '最高執行責任者',
        'active', '2023-04-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/k-bakshi',
        'did:web:k-bakshi.etzhayyim.com',
        'Kunal Bakshi', 'クナル・バクシ',
        'contractor', 'legal', 'CLO', '最高法務責任者',
        'active', '2023-06-01', 'Asia/Kolkata', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/t-chikada',
        'did:web:t-chikada.etzhayyim.com',
        'T. Chikada', '近田 T',
        'contractor', 'engineering', 'Deploy Engineer', 'デプロイエンジニア',
        'active', '2024-01-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/f-tanaka',
        'did:web:f-tanaka.etzhayyim.com',
        'F. Tanaka', '田中 F',
        'contractor', 'engineering', 'Review Engineer', 'レビューエンジニア',
        'active', '2024-01-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/y-nishino',
        'did:web:y-nishino.etzhayyim.com',
        'Y. Nishino', '西野 Y',
        'contractor', 'engineering', 'Infrastructure Engineer', 'インフラエンジニア',
        'active', '2024-01-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/t-ichihara',
        'did:web:t-ichihara.etzhayyim.com',
        'T. Ichihara', '市原 T',
        'contractor', 'brand', 'Brand Manager', 'ブランドマネージャー',
        'active', '2024-03-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/k-takahashi',
        'did:web:k-takahashi.etzhayyim.com',
        'K. Takahashi', '高橋 K',
        'contractor', 'creative', 'Creative Director', 'クリエイティブディレクター',
        'active', '2024-03-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.person/n-takahashi',
        'did:web:n-takahashi.etzhayyim.works',
        'N. Takahashi', '高橋 N',
        'contractor', 'security', 'Cybersecurity Lead', 'サイバーセキュリティ事業部責任者',
        'active', '2024-06-01', 'Asia/Tokyo', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'
      )
  `.execute(db);

  // ── Seed: Role definitions ─────────────────────────────────────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_role
      (vertex_id, role_id, role_name, role_name_ja, department, level, description, is_leadership, created_at, owner_did)
    VALUES
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/ceo', 'ceo', 'CEO', '最高経営責任者', 'executive', 'c-suite', 'Overall strategy and operations', true, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/coo', 'coo', 'COO', '最高執行責任者', 'executive', 'c-suite', 'Day-to-day operations and HR', true, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/clo', 'clo', 'CLO', '最高法務責任者', 'legal', 'c-suite', 'Legal strategy, contracts, litigation', true, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/eng-deploy', 'eng-deploy', 'Deploy Engineer', 'デプロイエンジニア', 'engineering', 'individual', 'CI/CD, release management, infra deploy', false, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/eng-review', 'eng-review', 'Review Engineer', 'レビューエンジニア', 'engineering', 'individual', 'Code review, QA, testing', false, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/eng-infra', 'eng-infra', 'Infrastructure Engineer', 'インフラエンジニア', 'engineering', 'individual', 'Cloud infra, k8s, networking', false, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/brand', 'brand', 'Brand Manager', 'ブランドマネージャー', 'brand', 'individual', 'Brand identity, marketing, BD support', false, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/creative', 'creative', 'Creative Director', 'クリエイティブディレクター', 'creative', 'individual', 'Visual design, UX, content creation', false, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.role/security-lead', 'security-lead', 'Cybersecurity Lead', 'サイバーセキュリティ事業部責任者', 'security', 'lead', 'Cybersecurity strategy, incident response, audit', true, ${createdAt}, 'did:web:etzhayyim.etzhayyim.com')
  `.execute(db);

  // ── Seed: Active assignments ───────────────────────────────────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_assignment
      (vertex_id, person_did, role_id, project_name, allocation_pct, start_date, status, created_at, owner_did)
    VALUES
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/ceo-main', 'did:web:j-kawasaki.etzhayyim.com', 'ceo', 'etzhayyim platform', 100.0, '2023-01-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/coo-main', 'did:web:a-nakamura.etzhayyim.com', 'coo', 'etzhayyim platform', 100.0, '2023-04-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/clo-main', 'did:web:k-bakshi.etzhayyim.com', 'clo', 'etzhayyim platform', 80.0, '2023-06-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/eng-deploy-main', 'did:web:t-chikada.etzhayyim.com', 'eng-deploy', 'etzhayyim platform', 100.0, '2024-01-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/eng-review-main', 'did:web:f-tanaka.etzhayyim.com', 'eng-review', 'etzhayyim platform', 100.0, '2024-01-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/eng-infra-main', 'did:web:y-nishino.etzhayyim.com', 'eng-infra', 'etzhayyim platform', 100.0, '2024-01-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/brand-main', 'did:web:t-ichihara.etzhayyim.com', 'brand', 'etzhayyim platform', 100.0, '2024-03-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/creative-main', 'did:web:k-takahashi.etzhayyim.com', 'creative', 'etzhayyim platform', 100.0, '2024-03-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.assignment/security-main', 'did:web:n-takahashi.etzhayyim.works', 'security-lead', 'etzhayyim security', 80.0, '2024-06-01', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com')
  `.execute(db);

  // ── Seed: RACI matrix (core domain tasks) ─────────────────────────────────
  await sql`
    INSERT INTO vertex_etzhayyim_raci
      (vertex_id, task_nsid, task_name, task_name_ja, domain, person_did, raci_role, status, created_at, owner_did)
    VALUES
      -- HR domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/hr-onboard-r', 'com.etzhayyim.apps.etzhayyim.hr.onboard', 'Onboarding', '入社手続', 'hr', 'did:web:a-nakamura.etzhayyim.com', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/hr-onboard-a', 'com.etzhayyim.apps.etzhayyim.hr.onboard', 'Onboarding', '入社手続', 'hr', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/hr-payroll-r', 'com.etzhayyim.apps.etzhayyim.hr.payroll', 'Payroll', '給与計算', 'hr', 'did:web:a-nakamura.etzhayyim.com', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/hr-payroll-a', 'com.etzhayyim.apps.etzhayyim.hr.payroll', 'Payroll', '給与計算', 'hr', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      -- Legal domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/legal-review-r', 'com.etzhayyim.apps.etzhayyim.legal.review', 'Contract Review', '契約レビュー', 'legal', 'did:web:k-bakshi.etzhayyim.com', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/legal-review-a', 'com.etzhayyim.apps.etzhayyim.legal.review', 'Contract Review', '契約レビュー', 'legal', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/legal-litigation-r', 'com.etzhayyim.apps.etzhayyim.legal.litigation', 'Litigation', '訴訟対応', 'legal', 'did:web:k-bakshi.etzhayyim.com', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/legal-litigation-a', 'com.etzhayyim.apps.etzhayyim.legal.litigation', 'Litigation', '訴訟対応', 'legal', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      -- Finance domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/finance-journal-r', 'com.etzhayyim.apps.etzhayyim.finance.journal', 'Journal Entry', '仕訳処理', 'finance', 'did:web:j-kawasaki.etzhayyim.com', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/finance-journal-a', 'com.etzhayyim.apps.etzhayyim.finance.journal', 'Journal Entry', '仕訳処理', 'finance', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      -- Governance domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/governance-okr-r', 'com.etzhayyim.apps.etzhayyim.governance.okr', 'OKR Review', 'OKRレビュー', 'governance', 'did:web:j-kawasaki.etzhayyim.com', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/governance-okr-c', 'com.etzhayyim.apps.etzhayyim.governance.okr', 'OKR Review', 'OKRレビュー', 'governance', 'did:web:a-nakamura.etzhayyim.com', 'C', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      -- Personnel domain (self-referential: who manages personnel ops)
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/personnel-assign-r', 'com.etzhayyim.apps.etzhayyim.personnel.assign', 'Assignment Management', 'アサイン管理', 'personnel', 'did:web:a-nakamura.etzhayyim.com', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/personnel-assign-a', 'com.etzhayyim.apps.etzhayyim.personnel.assign', 'Assignment Management', 'アサイン管理', 'personnel', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      -- Security domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/security-incident-r', 'com.etzhayyim.apps.etzhayyim.security.incident', 'Incident Response', 'インシデント対応', 'security', 'did:web:n-takahashi.etzhayyim.works', 'R', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/security-incident-a', 'com.etzhayyim.apps.etzhayyim.security.incident', 'Incident Response', 'インシデント対応', 'security', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.etzhayyim.raci/security-incident-c', 'com.etzhayyim.apps.etzhayyim.security.incident', 'Incident Response', 'インシデント対応', 'security', 'did:web:k-bakshi.etzhayyim.com', 'C', 'active', ${createdAt}, 'did:web:etzhayyim.etzhayyim.com')
  `.execute(db);

  // ── BPMN process def: Personnel Ops Dispatch (canonical schema) ──────────
  const _bpmnXml = (await import("node:fs")).readFileSync(
    (await import("node:path")).resolve(
      (await import("node:path")).dirname(
        (await import("node:url")).fileURLToPath(import.meta.url),
      ),
      "..", "..", "..",
      "00-contracts/bpmn/com/etzhayyim/etzhayyim/personnelOpsDispatch.bpmn",
    ),
    "utf8",
  );
  const _bpmnSize = Buffer.byteLength(_bpmnXml, "utf8");
  const _ownerDid = "did:web:etzhayyim.etzhayyim.com";
  const _actorTag = "sys.bpmn.seed.etzhayyim";
  const _processVid = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/etzhayyim-personnel-ops-v1";
  const _bindingVid = "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-personnel-ops-xrpc-v1";

  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${_processVid}, ${_ownerDid}, 'etzhayyim_personnel_ops_dispatch', 1, ${_bpmnXml}, CAST(${_bpmnSize} AS integer), '00-contracts/bpmn/com/etzhayyim/etzhayyim/personnelOpsDispatch.bpmn', 'active', ${createdAt}, 1, ${_ownerDid}, ${_ownerDid}, ${_actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${_processVid})
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${_bindingVid}, ${_ownerDid}, 'com.etzhayyim.apps.etzhayyim.personnelOpsDispatch', 'etzhayyim_personnel_ops_dispatch', 1, CAST(180000 AS integer), 'active', ${createdAt}, 1, ${_ownerDid}, ${_ownerDid}, ${_actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${_bindingVid})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE bpmn_process_id LIKE 'etzhayyim_personnel%'`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id LIKE 'etzhayyim_personnel%'`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_raci_by_task`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_active_assignments`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_okr`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_raci`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_assignment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_role`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person`.execute(db);
}
