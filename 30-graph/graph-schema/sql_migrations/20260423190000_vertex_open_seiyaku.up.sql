CREATE TABLE vertex_open_seiyaku_batch (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      manufacturer_org_id   varchar NOT NULL,
      plant_org_id          varchar NOT NULL,
      product_code          varchar NOT NULL,
      batch_number          varchar NOT NULL,
      dosage_form           varchar,
      process_type          varchar NOT NULL,
      status                varchar NOT NULL,
      batch_hash            varchar NOT NULL,
      qa_required           boolean,
      qa_decision           varchar,
      amendment_count       int,
      released_at           varchar,
      submitted_at          varchar,
      approved_at           varchar,
      approved_by_did       varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    );

CREATE TABLE vertex_open_seiyaku_batch_confidential (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      manufacturer_org_id      varchar NOT NULL,
      plant_org_id             varchar NOT NULL,
      master_formula_payload   varchar,
      material_payload         varchar,
      batch_record_payload     varchar,
      quality_payload          varchar,
      deviation_payload        varchar,
      amendment_log            varchar,
      retention_until          varchar NOT NULL,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE TABLE edge_open_seiyaku_lot_material (
      edge_id                  varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      src_vid                  varchar NOT NULL,
      dst_vid                  varchar NOT NULL,
      material_code            varchar NOT NULL,
      lot_number               varchar NOT NULL,
      quantity                 double precision,
      unit_code                varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE MATERIALIZED VIEW mv_open_seiyaku_released_batches AS
    SELECT
      manufacturer_org_id,
      plant_org_id,
      product_code,
      batch_number,
      vertex_id,
      status,
      released_at,
      approved_at
    FROM vertex_open_seiyaku_batch
    WHERE status IN ('released', 'amended');
