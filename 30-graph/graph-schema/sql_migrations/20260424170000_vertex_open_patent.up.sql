CREATE TABLE vertex_open_patent_patent (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      office_org_id varchar NOT NULL, patent_number varchar NOT NULL, jurisdiction varchar NOT NULL,
      title varchar, inventor_names varchar, assignee_did varchar,
      ipc_classes varchar, filing_date varchar, grant_date varchar,
      priority_date varchar, novelty_score double precision,
      verification varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_patent_citation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      citing_patent varchar NOT NULL, cited_patent varchar NOT NULL,
      citation_type varchar NOT NULL, confidence double precision, source varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_patent_citation_pair (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_patent_by_jurisdiction AS
      SELECT jurisdiction, verification, COUNT(*) AS patent_count,
             AVG(novelty_score) AS avg_novelty, MAX(grant_date) AS latest_grant_date
      FROM vertex_open_patent_patent WHERE status='granted'
      GROUP BY jurisdiction, verification;
