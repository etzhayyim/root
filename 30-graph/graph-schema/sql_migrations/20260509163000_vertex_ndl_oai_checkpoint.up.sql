CREATE TABLE IF NOT EXISTS vertex_ndl_oai_checkpoint (
  vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
  provider_id varchar NOT NULL,
  set_group varchar NOT NULL,
  metadata_prefix varchar NOT NULL,
  window_start date NOT NULL,
  window_end date NOT NULL,
  resumption_token varchar,
  pages_seen int NOT NULL,
  records_seen bigint NOT NULL,
  items_inserted bigint NOT NULL,
  status varchar NOT NULL,
  error varchar,
  updated_at varchar,
  org_id varchar, user_id varchar, actor_id varchar
);
