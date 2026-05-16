CREATE TABLE vertex_open_naics_classification (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      entity_did varchar NOT NULL, naics_code varchar NOT NULL,
      entity_name varchar, country varchar, evidence_url varchar,
      confidence double precision NOT NULL, verification varchar NOT NULL,
      status varchar NOT NULL, classified_at varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_naics_concordance (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      naics_code varchar NOT NULL, other_taxonomy varchar NOT NULL, other_code varchar NOT NULL,
      relation varchar NOT NULL, confidence double precision, source varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_naics_classification_class (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_naics_entities_by_class AS
      SELECT naics_code, country, COUNT(*) AS entity_count,
             AVG(confidence) AS avg_confidence, MAX(classified_at) AS latest_classified_at
      FROM vertex_open_naics_classification WHERE status='confirmed'
      GROUP BY naics_code, country;
