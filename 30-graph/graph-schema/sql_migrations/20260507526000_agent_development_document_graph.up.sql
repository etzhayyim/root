CREATE TABLE IF NOT EXISTS vertex_agent_development_document (
      vertex_id VARCHAR PRIMARY KEY,
      doc_id VARCHAR NOT NULL,
      doc_type VARCHAR NOT NULL,
      title TEXT,
      summary TEXT,
      body_text TEXT,
      source_path VARCHAR,
      status VARCHAR,
      agent_did VARCHAR,
      topic VARCHAR,
      tags_json TEXT,
      related_ref VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT,
      actor_id VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_agent_development_document_ref (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      ref_kind VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_agent_dev_doc_id ON vertex_agent_development_document (doc_id);

CREATE INDEX IF NOT EXISTS idx_agent_dev_doc_topic_status ON vertex_agent_development_document (topic, status);

CREATE INDEX IF NOT EXISTS idx_agent_dev_doc_updated ON vertex_agent_development_document (updated_at);

CREATE INDEX IF NOT EXISTS idx_agent_dev_edge_src ON edge_agent_development_document_ref (src_vid);

CREATE INDEX IF NOT EXISTS idx_agent_dev_edge_dst ON edge_agent_development_document_ref (dst_vid);

CREATE INDEX IF NOT EXISTS idx_agent_dev_edge_kind ON edge_agent_development_document_ref (relation_kind, ref_kind);

DROP MATERIALIZED VIEW IF EXISTS mv_agent_development_document_status_counts;

CREATE MATERIALIZED VIEW mv_agent_development_document_status_counts AS
    SELECT topic, doc_type, status, count(*)::BIGINT AS document_count
    FROM vertex_agent_development_document
    GROUP BY topic, doc_type, status;

DROP MATERIALIZED VIEW IF EXISTS mv_agent_development_document_latest;

CREATE MATERIALIZED VIEW mv_agent_development_document_latest AS
    SELECT doc_id, doc_type, title, topic, status, updated_at, agent_did, related_ref
    FROM vertex_agent_development_document;
