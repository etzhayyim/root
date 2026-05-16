CREATE TABLE vertex_sekkei_drawing (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      title                    varchar NOT NULL,
      drawing_type             varchar NOT NULL,
      owner_did_drawing        varchar NOT NULL,
      project_code             varchar,
      assembly_code            varchar,
      current_rev_no           varchar,
      status                   varchar NOT NULL DEFAULT 'draft',
      cad_file_ref             varchar,
      pdf_file_ref             varchar,
      linked_actor_did         varchar,
      tsukuru_manufacturer_did varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_owner       ON vertex_sekkei_drawing (owner_did_drawing);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_status      ON vertex_sekkei_drawing (status);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_project     ON vertex_sekkei_drawing (project_code);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_sekkei_drawing_linked      ON vertex_sekkei_drawing (linked_actor_did);

FLUSH;

CREATE TABLE vertex_sekkei_revision (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      rev_no                   varchar NOT NULL,
      previous_rev_no          varchar,
      revision_reason          varchar NOT NULL,
      change_description       varchar,
      revised_by_did           varchar NOT NULL,
      revised_at               varchar NOT NULL,
      cad_file_ref             varchar,
      pdf_file_ref             varchar,
      status                   varchar NOT NULL DEFAULT 'pending-approval',
      affected_bom_lines       varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE INDEX IF NOT EXISTS idx_sekkei_revision_drawing ON vertex_sekkei_revision (drawing_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_sekkei_revision_status  ON vertex_sekkei_revision (status);

FLUSH;

CREATE TABLE vertex_sekkei_approval (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      rev_no                   varchar NOT NULL,
      approver_did             varchar NOT NULL,
      approver_role            varchar,
      decision                 varchar NOT NULL,
      decided_at               varchar NOT NULL,
      conditions               varchar,
      rejection_reason         varchar,
      signature_ref            varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE INDEX IF NOT EXISTS idx_sekkei_approval_drawing  ON vertex_sekkei_approval (drawing_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_sekkei_approval_decision ON vertex_sekkei_approval (decision);

FLUSH;

CREATE TABLE vertex_sekkei_bom_line (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      bom_line_id              varchar NOT NULL,
      parent_drawing_id        varchar NOT NULL,
      parent_rev_no            varchar,
      child_item_code          varchar NOT NULL,
      child_drawing_id         varchar,
      child_item_name          varchar,
      quantity                 double precision NOT NULL,
      unit                     varchar,
      level                    integer,
      item_type                varchar,
      supplier_did             varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE INDEX IF NOT EXISTS idx_sekkei_bom_parent ON vertex_sekkei_bom_line (parent_drawing_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_sekkei_bom_child  ON vertex_sekkei_bom_line (child_item_code);

FLUSH;

CREATE TABLE vertex_sekkei_release (
      vertex_id                varchar PRIMARY KEY,
      _seq                     bigint,
      created_date             date,
      sensitivity_ord          int,
      owner_did                varchar,
      drawing_id               varchar NOT NULL,
      rev_no                   varchar NOT NULL,
      release_type             varchar NOT NULL,
      released_by_did          varchar NOT NULL,
      released_at              varchar NOT NULL,
      target_product_code      varchar,
      effective_date           varchar,
      obsoletes_drawing_id     varchar,
      distribution_list        varchar,
      notes                    varchar,
      created_at               varchar,
      org_id                   varchar,
      user_id                  varchar,
      actor_id                 varchar
    );

CREATE INDEX IF NOT EXISTS idx_sekkei_release_drawing ON vertex_sekkei_release (drawing_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_sekkei_release_product ON vertex_sekkei_release (target_product_code);

FLUSH;

CREATE MATERIALIZED VIEW mv_sekkei_stale_reviews AS
      SELECT
        drawing_id,
        rev_no,
        revised_by_did,
        revised_at
      FROM vertex_sekkei_revision
      WHERE status = 'pending-approval';

FLUSH;
