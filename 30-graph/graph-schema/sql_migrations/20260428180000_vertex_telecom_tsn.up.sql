CREATE TABLE vertex_telecom_tsn_domain (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      domain_id            varchar NOT NULL,
      owner_org_id         varchar NOT NULL,
      display_name         varchar NOT NULL,
      profile_kind         varchar NOT NULL,
      snpn_vid             varchar,
      controller_kind      varchar NOT NULL,
      controller_endpoint  varchar,
      gptp_domain_number   int NOT NULL,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tsn_bridge (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      bridge_id            varchar NOT NULL,
      domain_vid           varchar NOT NULL,
      vendor               varchar NOT NULL,
      model                varchar NOT NULL,
      bridge_kind          varchar NOT NULL,
      port_count           int NOT NULL,
      supported_shapers    varchar NOT NULL,
      supports_frer        boolean,
      supports_srp         boolean,
      attached_asset_vid   varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tsn_sync_profile (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      sync_profile_id      varchar NOT NULL,
      domain_vid           varchar NOT NULL,
      grandmaster_bridge_vid varchar NOT NULL,
      profile_kind         varchar NOT NULL,
      sync_interval_log    int NOT NULL,
      announce_interval_log int NOT NULL,
      priority1            int,
      priority2            int,
      redundant_gm_bridge_vids varchar,
      provisioned_at       varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tsn_stream (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      stream_id            varchar NOT NULL,
      domain_vid           varchar NOT NULL,
      talker_endpoint_vid  varchar NOT NULL,
      listener_endpoint_vids varchar NOT NULL,
      stream_rank          int,
      traffic_class        int NOT NULL,
      max_frame_bytes      int NOT NULL,
      frames_per_interval  int NOT NULL,
      interval_ns          bigint NOT NULL,
      max_latency_ns       bigint NOT NULL,
      path_bridge_vids     varchar,
      reservation_kind     varchar NOT NULL,
      reserved_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tsn_shaper (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      shaper_id            varchar NOT NULL,
      bridge_vid           varchar NOT NULL,
      port_index           int NOT NULL,
      shaper_kind          varchar NOT NULL,
      traffic_class        int NOT NULL,
      idle_slope_bps       bigint,
      gate_schedule_hash   varchar,
      gate_schedule_ref    varchar,
      cycle_time_ns        bigint,
      action               varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tsn_frer_profile (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      frer_profile_id      varchar NOT NULL,
      stream_vid           varchar NOT NULL,
      replication_kind     varchar NOT NULL,
      replication_count    int NOT NULL,
      replication_path_bridge_vids varchar,
      elimination_bridge_vids varchar,
      sequence_recovery_window int,
      enabled_at           varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tsn_sync_deviation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      deviation_id         varchar NOT NULL,
      sync_profile_vid     varchar NOT NULL,
      observed_bridge_vid  varchar NOT NULL,
      deviation_kind       varchar NOT NULL,
      offset_ns            bigint NOT NULL,
      path_delay_ns        bigint,
      path_delay_variance_ns bigint,
      source_clock_id_hash varchar,
      breach               boolean NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tsn_sla_breach (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      breach_id            varchar NOT NULL,
      stream_vid           varchar NOT NULL,
      breach_kind          varchar NOT NULL,
      severity             varchar NOT NULL,
      observed_latency_ns  bigint,
      sla_latency_ns       bigint,
      observed_jitter_ns   bigint,
      observed_frame_loss_ppm bigint,
      witness_bridge_vid   varchar NOT NULL,
      ticket_id            varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_tsn_bridge_in_domain (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_tsn_stream_via_bridges (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_tsn_breach_for_stream (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_telecom_tsn_domain_state AS
      SELECT profile_kind, controller_kind, status, COUNT(*) AS domain_count
      FROM vertex_telecom_tsn_domain
      GROUP BY profile_kind, controller_kind, status;

CREATE MATERIALIZED VIEW mv_telecom_tsn_bridge_inventory AS
      SELECT vendor, bridge_kind, status, COUNT(*) AS bridge_count
      FROM vertex_telecom_tsn_bridge
      GROUP BY vendor, bridge_kind, status;

CREATE MATERIALIZED VIEW mv_telecom_tsn_stream_state AS
      SELECT reservation_kind, traffic_class, status,
             COUNT(*) AS stream_count,
             AVG(max_latency_ns) AS avg_max_latency_ns
      FROM vertex_telecom_tsn_stream
      GROUP BY reservation_kind, traffic_class, status;

CREATE MATERIALIZED VIEW mv_telecom_tsn_shaper_state AS
      SELECT shaper_kind, action, status, COUNT(*) AS shaper_count
      FROM vertex_telecom_tsn_shaper
      GROUP BY shaper_kind, action, status;

CREATE MATERIALIZED VIEW mv_telecom_tsn_sync_health AS
      SELECT deviation_kind, breach,
             COUNT(*) AS event_count,
             AVG(offset_ns) AS avg_offset_ns,
             MAX(offset_ns) AS max_offset_ns
      FROM vertex_telecom_tsn_sync_deviation
      GROUP BY deviation_kind, breach;

CREATE MATERIALIZED VIEW mv_telecom_tsn_breach_summary AS
      SELECT breach_kind, severity, status, COUNT(*) AS breach_count
      FROM vertex_telecom_tsn_sla_breach
      GROUP BY breach_kind, severity, status;
