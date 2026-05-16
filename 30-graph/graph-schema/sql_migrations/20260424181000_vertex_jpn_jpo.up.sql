CREATE TABLE vertex_jpn_jpo_application (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      application_number varchar NOT NULL, applicant_did varchar NOT NULL,
      inventor_names varchar, ipc_classes varchar, title varchar,
      filing_date varchar NOT NULL, priority_date varchar,
      examination_requested boolean, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_jpn_jpo_examination (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      application_number varchar NOT NULL, decision varchar NOT NULL,
      decision_date varchar NOT NULL, examiner_id varchar,
      rejection_grounds varchar, cited_art varchar,
      next_action varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_jpn_jpo_app_examination (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_jpn_jpo_app_by_ipc AS
      SELECT ipc_classes, status, COUNT(*) AS app_count, MAX(filing_date) AS latest_filing
      FROM vertex_jpn_jpo_application WHERE status IN ('filed','pending','granted')
      GROUP BY ipc_classes, status;
