CREATE TABLE IF NOT EXISTS vertex_osm_element (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      sensitivity_ord  BIGINT DEFAULT 0,
      created_date     DATE,
      osm_type         VARCHAR,
      osm_id           BIGINT,
      version          INT,
      changeset_id     BIGINT,
      user_name        VARCHAR,
      uid              BIGINT,
      timestamp        TIMESTAMPTZ,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ,
      lat              DOUBLE PRECISION,
      lon              DOUBLE PRECISION,
      s2_cell_id       BIGINT,
      geohash          VARCHAR,
      tags             JSONB,
      bbox_min_lng     DOUBLE PRECISION,
      bbox_min_lat     DOUBLE PRECISION,
      bbox_max_lng     DOUBLE PRECISION,
      bbox_max_lat     DOUBLE PRECISION
    );

CREATE INDEX IF NOT EXISTS idx_osm_element_s2 ON vertex_osm_element (s2_cell_id);

CREATE INDEX IF NOT EXISTS idx_osm_element_type_id_version ON vertex_osm_element (osm_type, osm_id, version);

CREATE INDEX IF NOT EXISTS idx_osm_element_valid_to ON vertex_osm_element (valid_to);

CREATE INDEX IF NOT EXISTS idx_osm_element_source_seq ON vertex_osm_element (source_did, _seq);

CREATE INDEX IF NOT EXISTS idx_osm_element_type_s2 ON vertex_osm_element (osm_type, s2_cell_id);

CREATE TABLE IF NOT EXISTS edge_osm_way_node (
      edge_id          VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      created_date     DATE,
      way_vertex_id    VARCHAR,
      node_vertex_id   VARCHAR,
      seq              INT,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ
    );

CREATE INDEX IF NOT EXISTS idx_osm_way_node_way_seq ON edge_osm_way_node (way_vertex_id, seq);

CREATE INDEX IF NOT EXISTS idx_osm_way_node_node ON edge_osm_way_node (node_vertex_id);

CREATE INDEX IF NOT EXISTS idx_osm_way_node_source_seq ON edge_osm_way_node (source_did, _seq);

CREATE TABLE IF NOT EXISTS edge_osm_relation_member (
      edge_id             VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      owner_did           VARCHAR,
      source_did          VARCHAR,
      created_date        DATE,
      relation_vertex_id  VARCHAR,
      member_vertex_id    VARCHAR,
      member_type         VARCHAR,
      role                VARCHAR,
      seq                 INT,
      valid_from          TIMESTAMPTZ,
      valid_to            TIMESTAMPTZ
    );

CREATE INDEX IF NOT EXISTS idx_osm_rel_member_rel_seq ON edge_osm_relation_member (relation_vertex_id, seq);

CREATE INDEX IF NOT EXISTS idx_osm_rel_member_member ON edge_osm_relation_member (member_vertex_id);

CREATE INDEX IF NOT EXISTS idx_osm_rel_member_source_seq ON edge_osm_relation_member (source_did, _seq);

CREATE TABLE IF NOT EXISTS vertex_osm_element_stage (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      sensitivity_ord  BIGINT DEFAULT 0,
      created_date     DATE,
      osm_type         VARCHAR,
      osm_id           BIGINT,
      version          INT,
      changeset_id     BIGINT,
      user_name        VARCHAR,
      uid              BIGINT,
      timestamp        TIMESTAMPTZ,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ,
      lat              DOUBLE PRECISION,
      lon              DOUBLE PRECISION,
      s2_cell_id       BIGINT,
      geohash          VARCHAR,
      tags             JSONB,
      bbox_min_lng     DOUBLE PRECISION,
      bbox_min_lat     DOUBLE PRECISION,
      bbox_max_lng     DOUBLE PRECISION,
      bbox_max_lat     DOUBLE PRECISION
    );

CREATE TABLE IF NOT EXISTS edge_osm_way_node_stage (
      edge_id          VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      owner_did        VARCHAR,
      source_did       VARCHAR,
      created_date     DATE,
      way_vertex_id    VARCHAR,
      node_vertex_id   VARCHAR,
      seq              INT,
      valid_from       TIMESTAMPTZ,
      valid_to         TIMESTAMPTZ
    );

CREATE TABLE IF NOT EXISTS edge_osm_relation_member_stage (
      edge_id             VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      owner_did           VARCHAR,
      source_did          VARCHAR,
      created_date        DATE,
      relation_vertex_id  VARCHAR,
      member_vertex_id    VARCHAR,
      member_type         VARCHAR,
      role                VARCHAR,
      seq                 INT,
      valid_from          TIMESTAMPTZ,
      valid_to            TIMESTAMPTZ
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_osm_tag_lookup AS
    SELECT
      v.vertex_id,
      v.osm_type,
      t.key,
      t.value,
      v.s2_cell_id
    FROM vertex_osm_element AS v,
         jsonb_each_text(v.tags) AS t(key, value)
    WHERE v.valid_to IS NULL;
