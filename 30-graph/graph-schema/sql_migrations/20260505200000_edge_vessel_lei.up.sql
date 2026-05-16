CREATE TABLE IF NOT EXISTS edge_vessel_owned_by (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      mmsi bigint NOT NULL,
      imo bigint,
      lei varchar,
      wikidata_qid varchar,
      entity_label varchar,
      share_pct real,
      effective_from_ms bigint,
      effective_to_ms bigint,
      source varchar NOT NULL,
      source_record_id varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    );

CREATE TABLE IF NOT EXISTS edge_vessel_operated_by (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      mmsi bigint NOT NULL,
      imo bigint,
      lei varchar,
      wikidata_qid varchar,
      entity_label varchar,
      role varchar,
      effective_from_ms bigint,
      effective_to_ms bigint,
      source varchar NOT NULL,
      source_record_id varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    );

CREATE INDEX IF NOT EXISTS idx_edge_vessel_owned_by_mmsi ON edge_vessel_owned_by(mmsi);

CREATE INDEX IF NOT EXISTS idx_edge_vessel_owned_by_lei  ON edge_vessel_owned_by(lei);

CREATE INDEX IF NOT EXISTS idx_edge_vessel_owned_by_qid  ON edge_vessel_owned_by(wikidata_qid);

CREATE INDEX IF NOT EXISTS idx_edge_vessel_operated_by_mmsi ON edge_vessel_operated_by(mmsi);

CREATE INDEX IF NOT EXISTS idx_edge_vessel_operated_by_lei  ON edge_vessel_operated_by(lei);

CREATE INDEX IF NOT EXISTS idx_edge_vessel_operated_by_qid  ON edge_vessel_operated_by(wikidata_qid);
