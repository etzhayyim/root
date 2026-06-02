CREATE TABLE IF NOT EXISTS vertex_gftdcojp_person (
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
      owner_did       varchar);

CREATE TABLE IF NOT EXISTS vertex_gftdcojp_role (
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
      owner_did       varchar);

CREATE TABLE IF NOT EXISTS vertex_gftdcojp_assignment (
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
      owner_did       varchar);

CREATE TABLE IF NOT EXISTS vertex_gftdcojp_raci (
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
      owner_did       varchar);

CREATE TABLE IF NOT EXISTS vertex_gftdcojp_okr (
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
      owner_did        varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gftdcojp_active_assignments AS
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
    FROM vertex_gftdcojp_assignment a
    LEFT JOIN vertex_gftdcojp_person p ON p.person_did = a.person_did
    LEFT JOIN vertex_gftdcojp_role r ON r.role_id = a.role_id
    WHERE a.status = 'active';

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gftdcojp_raci_by_task AS
    SELECT
      r.task_nsid,
      r.task_name,
      r.domain,
      r.raci_role,
      COUNT(*) AS person_count,
      STRING_AGG(p.display_name, ', ') AS persons
    FROM vertex_gftdcojp_raci r
    LEFT JOIN vertex_gftdcojp_person p ON p.person_did = r.person_did
    WHERE r.status = 'active'
    GROUP BY r.task_nsid, r.task_name, r.domain, r.raci_role;

INSERT INTO vertex_gftdcojp_person
      (vertex_id, person_did, display_name, display_name_ja, employment_type, department, title, title_ja, status, joined_at, timezone, created_at, owner_did)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/j-kawasaki',
        'did:web:j-kawasaki.etzhayyim.com',
        'Jun Kawasaki', '川崎 潤',
        'founder', 'executive', 'CEO', '最高経営責任者',
        'active', '2023-01-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/a-nakamura',
        'did:web:a-nakamura.etzhayyim.com',
        'A. Nakamura', '中村 A',
        'employee', 'executive', 'COO', '最高執行責任者',
        'active', '2023-04-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/k-bakshi',
        'did:web:k-bakshi.etzhayyim.com',
        'Kunal Bakshi', 'クナル・バクシ',
        'contractor', 'legal', 'CLO', '最高法務責任者',
        'active', '2023-06-01', 'Asia/Kolkata', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/t-chikada',
        'did:web:t-chikada.etzhayyim.com',
        'T. Chikada', '近田 T',
        'contractor', 'engineering', 'Deploy Engineer', 'デプロイエンジニア',
        'active', '2024-01-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/f-tanaka',
        'did:web:f-tanaka.etzhayyim.com',
        'F. Tanaka', '田中 F',
        'contractor', 'engineering', 'Review Engineer', 'レビューエンジニア',
        'active', '2024-01-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/y-nishino',
        'did:web:y-nishino.etzhayyim.com',
        'Y. Nishino', '西野 Y',
        'contractor', 'engineering', 'Infrastructure Engineer', 'インフラエンジニア',
        'active', '2024-01-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/t-ichihara',
        'did:web:t-ichihara.etzhayyim.com',
        'T. Ichihara', '市原 T',
        'contractor', 'brand', 'Brand Manager', 'ブランドマネージャー',
        'active', '2024-03-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/k-takahashi',
        'did:web:k-takahashi.etzhayyim.com',
        'K. Takahashi', '高橋 K',
        'contractor', 'creative', 'Creative Director', 'クリエイティブディレクター',
        'active', '2024-03-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.person/n-takahashi',
        'did:web:n-takahashi.gftd.works',
        'N. Takahashi', '高橋 N',
        'contractor', 'security', 'Cybersecurity Lead', 'サイバーセキュリティ事業部責任者',
        'active', '2024-06-01', 'Asia/Tokyo', now(), 'did:web:gftdcojp.etzhayyim.com'
      );

INSERT INTO vertex_gftdcojp_role
      (vertex_id, role_id, role_name, role_name_ja, department, level, description, is_leadership, created_at, owner_did)
    VALUES
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/ceo', 'ceo', 'CEO', '最高経営責任者', 'executive', 'c-suite', 'Overall strategy and operations', true, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/coo', 'coo', 'COO', '最高執行責任者', 'executive', 'c-suite', 'Day-to-day operations and HR', true, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/clo', 'clo', 'CLO', '最高法務責任者', 'legal', 'c-suite', 'Legal strategy, contracts, litigation', true, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/eng-deploy', 'eng-deploy', 'Deploy Engineer', 'デプロイエンジニア', 'engineering', 'individual', 'CI/CD, release management, infra deploy', false, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/eng-review', 'eng-review', 'Review Engineer', 'レビューエンジニア', 'engineering', 'individual', 'Code review, QA, testing', false, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/eng-infra', 'eng-infra', 'Infrastructure Engineer', 'インフラエンジニア', 'engineering', 'individual', 'Cloud infra, k8s, networking', false, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/brand', 'brand', 'Brand Manager', 'ブランドマネージャー', 'brand', 'individual', 'Brand identity, marketing, BD support', false, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/creative', 'creative', 'Creative Director', 'クリエイティブディレクター', 'creative', 'individual', 'Visual design, UX, content creation', false, now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.role/security-lead', 'security-lead', 'Cybersecurity Lead', 'サイバーセキュリティ事業部責任者', 'security', 'lead', 'Cybersecurity strategy, incident response, audit', true, now(), 'did:web:gftdcojp.etzhayyim.com');

INSERT INTO vertex_gftdcojp_assignment
      (vertex_id, person_did, role_id, project_name, allocation_pct, start_date, status, created_at, owner_did)
    VALUES
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/ceo-main', 'did:web:j-kawasaki.etzhayyim.com', 'ceo', 'gftdcojp platform', 100.0, '2023-01-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/coo-main', 'did:web:a-nakamura.etzhayyim.com', 'coo', 'gftdcojp platform', 100.0, '2023-04-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/clo-main', 'did:web:k-bakshi.etzhayyim.com', 'clo', 'gftdcojp platform', 80.0, '2023-06-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/eng-deploy-main', 'did:web:t-chikada.etzhayyim.com', 'eng-deploy', 'gftdcojp platform', 100.0, '2024-01-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/eng-review-main', 'did:web:f-tanaka.etzhayyim.com', 'eng-review', 'gftdcojp platform', 100.0, '2024-01-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/eng-infra-main', 'did:web:y-nishino.etzhayyim.com', 'eng-infra', 'gftdcojp platform', 100.0, '2024-01-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/brand-main', 'did:web:t-ichihara.etzhayyim.com', 'brand', 'gftdcojp platform', 100.0, '2024-03-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/creative-main', 'did:web:k-takahashi.etzhayyim.com', 'creative', 'gftdcojp platform', 100.0, '2024-03-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.assignment/security-main', 'did:web:n-takahashi.gftd.works', 'security-lead', 'gftdcojp security', 80.0, '2024-06-01', 'active', now(), 'did:web:gftdcojp.etzhayyim.com');

INSERT INTO vertex_gftdcojp_raci
      (vertex_id, task_nsid, task_name, task_name_ja, domain, person_did, raci_role, status, created_at, owner_did)
    VALUES
      -- HR domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/hr-onboard-r', 'com.etzhayyim.apps.gftdcojp.hr.onboard', 'Onboarding', '入社手続', 'hr', 'did:web:a-nakamura.etzhayyim.com', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/hr-onboard-a', 'com.etzhayyim.apps.gftdcojp.hr.onboard', 'Onboarding', '入社手続', 'hr', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/hr-payroll-r', 'com.etzhayyim.apps.gftdcojp.hr.payroll', 'Payroll', '給与計算', 'hr', 'did:web:a-nakamura.etzhayyim.com', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/hr-payroll-a', 'com.etzhayyim.apps.gftdcojp.hr.payroll', 'Payroll', '給与計算', 'hr', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      -- Legal domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/legal-review-r', 'com.etzhayyim.apps.gftdcojp.legal.review', 'Contract Review', '契約レビュー', 'legal', 'did:web:k-bakshi.etzhayyim.com', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/legal-review-a', 'com.etzhayyim.apps.gftdcojp.legal.review', 'Contract Review', '契約レビュー', 'legal', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/legal-litigation-r', 'com.etzhayyim.apps.gftdcojp.legal.litigation', 'Litigation', '訴訟対応', 'legal', 'did:web:k-bakshi.etzhayyim.com', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/legal-litigation-a', 'com.etzhayyim.apps.gftdcojp.legal.litigation', 'Litigation', '訴訟対応', 'legal', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      -- Finance domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/finance-journal-r', 'com.etzhayyim.apps.gftdcojp.finance.journal', 'Journal Entry', '仕訳処理', 'finance', 'did:web:j-kawasaki.etzhayyim.com', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/finance-journal-a', 'com.etzhayyim.apps.gftdcojp.finance.journal', 'Journal Entry', '仕訳処理', 'finance', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      -- Governance domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/governance-okr-r', 'com.etzhayyim.apps.gftdcojp.governance.okr', 'OKR Review', 'OKRレビュー', 'governance', 'did:web:j-kawasaki.etzhayyim.com', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/governance-okr-c', 'com.etzhayyim.apps.gftdcojp.governance.okr', 'OKR Review', 'OKRレビュー', 'governance', 'did:web:a-nakamura.etzhayyim.com', 'C', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      -- Personnel domain (self-referential: who manages personnel ops)
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/personnel-assign-r', 'com.etzhayyim.apps.gftdcojp.personnel.assign', 'Assignment Management', 'アサイン管理', 'personnel', 'did:web:a-nakamura.etzhayyim.com', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/personnel-assign-a', 'com.etzhayyim.apps.gftdcojp.personnel.assign', 'Assignment Management', 'アサイン管理', 'personnel', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      -- Security domain
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/security-incident-r', 'com.etzhayyim.apps.gftdcojp.security.incident', 'Incident Response', 'インシデント対応', 'security', 'did:web:n-takahashi.gftd.works', 'R', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/security-incident-a', 'com.etzhayyim.apps.gftdcojp.security.incident', 'Incident Response', 'インシデント対応', 'security', 'did:web:j-kawasaki.etzhayyim.com', 'A', 'active', now(), 'did:web:gftdcojp.etzhayyim.com'),
      ('at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.gftdcojp.raci/security-incident-c', 'com.etzhayyim.apps.gftdcojp.security.incident', 'Incident Response', 'インシデント対応', 'security', 'did:web:k-bakshi.etzhayyim.com', 'C', 'active', now(), 'did:web:gftdcojp.etzhayyim.com');

INSERT INTO vertex_bpmn_process_def
      (vertex_id, process_id, name, description, version, bpmn_xml, status, created_at)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gftdcojp-personnel-ops-v1',
        'gftdcojp_personnel_ops_dispatch',
        'gftdcojp Personnel Ops Dispatch',
        'XRPC-triggered personnel management (role/responsibility/assignment/RACI) via LangGraph gftdcojp-company-ops',
        1,
        '',
        'active',
        now()
      );

INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, process_id, nsid, binding_type, status, created_at)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/gftdcojp-personnel-ops-xrpc-v1',
        'gftdcojp_personnel_ops_dispatch',
        'com.etzhayyim.apps.gftdcojp.personnelOpsDispatch',
        'xrpc',
        'active',
        now()
      );
