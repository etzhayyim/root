CREATE TABLE vertex_arms_firearm (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      serial_number_hash   varchar NOT NULL,
      make                 varchar NOT NULL,
      model                varchar NOT NULL,
      caliber              varchar NOT NULL,
      category             varchar NOT NULL,
      status               varchar NOT NULL DEFAULT 'active',
      registered_at        varchar,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE INDEX idx_arms_firearm_owner ON vertex_arms_firearm (owner_did);

CREATE INDEX idx_arms_firearm_serial ON vertex_arms_firearm (serial_number_hash);

CREATE INDEX idx_arms_firearm_status ON vertex_arms_firearm (status, category);

CREATE TABLE vertex_arms_firearm_pii (
      vertex_id            varchar PRIMARY KEY,
      firearm_vid          varchar NOT NULL,
      serial_number        varchar NOT NULL,
      manufacturer_code    varchar,
      country_of_origin    varchar,
      year_of_manufacture  int,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE INDEX idx_arms_firearm_pii_vid ON vertex_arms_firearm_pii (firearm_vid);

CREATE TABLE vertex_arms_permit (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      holder_did           varchar NOT NULL,
      permit_type          varchar NOT NULL,
      permit_number_hash   varchar NOT NULL,
      category_allowed     varchar NOT NULL,
      issuer_did           varchar NOT NULL,
      issued_at            varchar,
      expires_at           varchar,
      status               varchar NOT NULL DEFAULT 'active',
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE INDEX idx_arms_permit_holder ON vertex_arms_permit (holder_did, status);

CREATE INDEX idx_arms_permit_issuer ON vertex_arms_permit (issuer_did);

CREATE TABLE vertex_arms_permit_pii (
      vertex_id            varchar PRIMARY KEY,
      permit_vid           varchar NOT NULL,
      permit_number        varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE INDEX idx_arms_permit_pii_vid ON vertex_arms_permit_pii (permit_vid);

CREATE TABLE vertex_arms_custody_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      firearm_vid          varchar NOT NULL,
      event_type           varchar NOT NULL,
      from_holder_did      varchar,
      to_holder_did        varchar,
      auth_session_vid     varchar,
      permit_vid           varchar,
      location_code        varchar,
      notes                varchar,
      occurred_at          varchar,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE INDEX idx_arms_custody_firearm ON vertex_arms_custody_event (firearm_vid, occurred_at);

CREATE INDEX idx_arms_custody_from ON vertex_arms_custody_event (from_holder_did);

CREATE INDEX idx_arms_custody_to ON vertex_arms_custody_event (to_holder_did);

CREATE INDEX idx_arms_custody_type ON vertex_arms_custody_event (event_type, occurred_at);

CREATE TABLE vertex_arms_auth_session (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      firearm_vid          varchar NOT NULL,
      holder_did           varchar NOT NULL,
      challenge            varchar NOT NULL,
      response_hash        varchar,
      auth_status          varchar NOT NULL DEFAULT 'pending',
      initiated_at         varchar,
      completed_at         varchar,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE INDEX idx_arms_auth_firearm ON vertex_arms_auth_session (firearm_vid, auth_status);

CREATE INDEX idx_arms_auth_holder ON vertex_arms_auth_session (holder_did, auth_status);

CREATE TABLE edge_arms_firearm_to_holder (
      src        varchar NOT NULL,
      dst        varchar NOT NULL,
      rel        varchar NOT NULL DEFAULT 'held_by',
      since      varchar,
      permit_vid varchar,
      PRIMARY KEY (src, dst)
    );

CREATE INDEX idx_arms_f2h_dst ON edge_arms_firearm_to_holder (dst);

CREATE TABLE edge_arms_firearm_to_permit (
      src  varchar NOT NULL,
      dst  varchar NOT NULL,
      rel  varchar NOT NULL DEFAULT 'covered_by',
      PRIMARY KEY (src, dst)
    );

CREATE MATERIALIZED VIEW mv_arms_active_by_holder AS
    SELECT
      e.dst         AS holder_did,
      f.vertex_id   AS firearm_vid,
      f.make,
      f.model,
      f.caliber,
      f.category,
      f.status,
      e.since       AS held_since
    FROM edge_arms_firearm_to_holder e
    JOIN vertex_arms_firearm f ON f.vertex_id = e.src
    WHERE f.status IN ('active', 'checked_out');

FLUSH;
