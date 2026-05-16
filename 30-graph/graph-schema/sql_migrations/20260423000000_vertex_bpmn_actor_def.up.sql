CREATE TABLE vertex_bpmn_process_def (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      bpmn_process_id    varchar NOT NULL,
      version            int     NOT NULL,
      xml                varchar NOT NULL,
      xml_byte_size      int,
      source_path        varchar,
      deployed_at        varchar,
      deployed_zeebe_key bigint,
      status             varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE vertex_bpmn_lexicon_binding (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      nsid               varchar NOT NULL,
      bpmn_process_id    varchar NOT NULL,
      bpmn_version       int,
      result_timeout_ms  int,
      status             varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );
