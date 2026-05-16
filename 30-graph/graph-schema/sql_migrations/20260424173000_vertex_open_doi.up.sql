CREATE TABLE vertex_open_doi_doi (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      doi varchar NOT NULL, doi_prefix varchar NOT NULL, doi_suffix varchar NOT NULL,
      registrant_org_id varchar NOT NULL, title varchar,
      publication_type varchar NOT NULL, publisher varchar,
      published_at varchar, authors_orcid varchar,
      verification varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_doi_citation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      citing_doi varchar NOT NULL, cited_doi varchar NOT NULL,
      citation_type varchar, confidence double precision, source varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_open_doi_citation_pair (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_open_doi_by_publisher AS
      SELECT publisher, publication_type, COUNT(*) AS doi_count,
             MAX(published_at) AS latest_published_at
      FROM vertex_open_doi_doi WHERE status='active'
      GROUP BY publisher, publication_type;
