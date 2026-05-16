CREATE TABLE IF NOT EXISTS vertex_shosha_sanctions_list (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      list_source varchar NOT NULL,
      source_ref varchar NOT NULL,
      entity_type varchar,
      name varchar NOT NULL,
      name_normalized varchar NOT NULL,
      aliases varchar,
      country varchar,
      nationality varchar,
      list_program varchar,
      title varchar,
      remarks varchar,
      listed_at date,
      raw_json varchar,
      refreshed_at varchar NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_sanctions_count_by_source AS
      SELECT
        list_source,
        entity_type,
        COUNT(*) AS active_count
      FROM vertex_shosha_sanctions_list
      WHERE status = 'active'
      GROUP BY list_source, entity_type;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_sanctions_list TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_sanctions_list TO kaisya_app;
