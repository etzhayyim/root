CREATE TABLE IF NOT EXISTS vertex_graph_expand_proposal (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      source_vid         VARCHAR NOT NULL,
      proposed_dst_vid   VARCHAR,
      proposed_dst_label VARCHAR,
      edge_kind          VARCHAR NOT NULL,
      confidence         DOUBLE PRECISION NOT NULL,
      rationale          VARCHAR,
      llm_model          VARCHAR NOT NULL,
      status             VARCHAR NOT NULL DEFAULT 'proposed',
      created_at         VARCHAR NOT NULL,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_graph_expand_proposal_source
      ON vertex_graph_expand_proposal (source_vid, llm_model, created_at);

CREATE INDEX IF NOT EXISTS idx_graph_expand_proposal_status
      ON vertex_graph_expand_proposal (status, confidence);
