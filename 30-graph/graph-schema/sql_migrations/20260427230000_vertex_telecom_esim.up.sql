CREATE TABLE vertex_telecom_esim_euicc (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      eid                  varchar NOT NULL,
      device_kind          varchar NOT NULL,
      manufacturer_name    varchar,
      platform_version     varchar,
      smdp_address         varchar,
      smds_address         varchar,
      profile_slots        int,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_esim_profile (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      download_id          varchar NOT NULL,
      eid                  varchar NOT NULL,
      iccid                varchar NOT NULL,
      matching_id          varchar,
      smdp_address         varchar NOT NULL,
      profile_type         varchar,
      mno                  varchar,
      profile_state        varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_esim_profile_op (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      operation_id         varchar NOT NULL,
      eid                  varchar NOT NULL,
      iccid                varchar NOT NULL,
      op_kind              varchar NOT NULL,
      reason               varchar,
      refresh_flag         boolean,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_esim_smds_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      event_id             varchar NOT NULL,
      eid                  varchar NOT NULL,
      smdp_address         varchar NOT NULL,
      smds_address         varchar,
      event_type           varchar NOT NULL,
      iccid                varchar,
      expires_at           varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_esim_audit (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      audit_id             varchar NOT NULL,
      eid                  varchar NOT NULL,
      profile_count        int,
      active_iccid         varchar,
      free_memory_bytes    bigint,
      last_contact_at      varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_esim_ownership_transfer (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      transfer_id          varchar NOT NULL,
      eid                  varchar NOT NULL,
      iccid                varchar NOT NULL,
      source_mno           varchar NOT NULL,
      target_mno           varchar NOT NULL,
      target_smdp_address  varchar NOT NULL,
      porting_ref          varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_esim_profile_on_euicc (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    );

CREATE TABLE edge_telecom_esim_smds_event_for_profile (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    );

CREATE MATERIALIZED VIEW mv_telecom_esim_active_profiles AS
    SELECT eid, iccid, mno, smdp_address, profile_state, observed_at, org_id
    FROM vertex_telecom_esim_profile
    WHERE profile_state = 'enabled';

CREATE MATERIALIZED VIEW mv_telecom_esim_pending_smds_events AS
    SELECT event_id, eid, smdp_address, event_type, expires_at, status, org_id
    FROM vertex_telecom_esim_smds_event
    WHERE status = 'pending';

CREATE MATERIALIZED VIEW mv_telecom_esim_audit_recent AS
    SELECT audit_id, eid, profile_count, active_iccid, free_memory_bytes, last_contact_at, observed_at, org_id
    FROM vertex_telecom_esim_audit
    ORDER BY observed_at DESC;
