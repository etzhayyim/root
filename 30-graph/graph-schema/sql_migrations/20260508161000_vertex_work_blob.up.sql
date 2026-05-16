CREATE TABLE IF NOT EXISTS vertex_work_blob (
      vertex_id       VARCHAR PRIMARY KEY,
      work_vertex_id  VARCHAR NOT NULL,
      doi             VARCHAR,
      source_url      VARCHAR,
      oa_url          VARCHAR,
      fulltext        VARCHAR,
      lang            VARCHAR,
      license         VARCHAR,
      fetched_at      VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      error           VARCHAR,
      created_date    DATE,
      sensitivity_ord BIGINT DEFAULT 0
    );

CREATE INDEX idx_vertex_work_blob_work_vertex_id
      ON vertex_work_blob(work_vertex_id);

CREATE INDEX idx_vertex_work_blob_status
      ON vertex_work_blob(status);

CREATE INDEX idx_vertex_work_blob_doi
      ON vertex_work_blob(doi);
