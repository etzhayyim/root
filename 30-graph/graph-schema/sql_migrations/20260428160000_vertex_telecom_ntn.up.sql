CREATE TABLE vertex_telecom_ntn_satellite (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      satellite_id         varchar NOT NULL,
      operator_org_id      varchar NOT NULL,
      display_name         varchar NOT NULL,
      orbit_class          varchar NOT NULL,
      norad_id             varchar,
      intl_designator      varchar,
      frequency_bands      varchar NOT NULL,
      service_modes        varchar NOT NULL,
      launched_at          varchar NOT NULL,
      eol_at               varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ntn_earth_station (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      station_id           varchar NOT NULL,
      operator_org_id      varchar NOT NULL,
      display_name         varchar NOT NULL,
      station_kind         varchar NOT NULL,
      latitude             double precision NOT NULL,
      longitude            double precision NOT NULL,
      altitude_meters      double precision,
      jurisdiction         varchar NOT NULL,
      antenna_count        int,
      gateway_kind         varchar NOT NULL,
      peering_nf_vid       varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ntn_cell (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      ntn_cell_id          varchar NOT NULL,
      satellite_vid        varchar NOT NULL,
      ran_node_vid         varchar NOT NULL,
      cell_pattern         varchar NOT NULL,
      beam_count           int NOT NULL,
      plmn_id              varchar NOT NULL,
      snssai               varchar,
      frequency_band       varchar NOT NULL,
      payload_kind         varchar NOT NULL,
      jurisdiction         varchar,
      valid_from           varchar NOT NULL,
      valid_until          varchar,
      provisioned_at       varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ntn_ephemeris (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      ephemeris_id         varchar NOT NULL,
      satellite_vid        varchar NOT NULL,
      source_kind          varchar NOT NULL,
      source_provider      varchar,
      epoch_at             varchar NOT NULL,
      payload_format       varchar NOT NULL,
      payload_hash         varchar NOT NULL,
      payload_ref          varchar,
      payload_size         bigint,
      valid_until          varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ntn_handover (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      handover_id          varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      handover_kind        varchar NOT NULL,
      source_cell_vid      varchar NOT NULL,
      target_cell_vid      varchar NOT NULL,
      source_satellite_vid varchar,
      target_satellite_vid varchar,
      trigger_kind         varchar NOT NULL,
      doppler_offset_hz    double precision,
      one_way_delay_ms     double precision,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ntn_isl (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      isl_id               varchar NOT NULL,
      source_satellite_vid varchar NOT NULL,
      target_satellite_vid varchar NOT NULL,
      link_kind            varchar NOT NULL,
      capacity_mbps        double precision NOT NULL,
      frequency_band       varchar,
      encryption_ref       varchar,
      valid_from           varchar NOT NULL,
      valid_until          varchar,
      provisioned_at       varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ntn_contact (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      contact_id           varchar NOT NULL,
      station_vid          varchar NOT NULL,
      satellite_vid        varchar NOT NULL,
      contact_kind         varchar NOT NULL,
      aos_at               varchar NOT NULL,
      los_at               varchar NOT NULL,
      duration_seconds     double precision,
      peak_elevation_deg   double precision,
      doppler_shift_hz     double precision,
      ingress_bytes        bigint,
      egress_bytes         bigint,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ntn_partner (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      ntn_partner_id       varchar NOT NULL,
      operator_org_id      varchar NOT NULL,
      agreement_vid        varchar NOT NULL,
      constellation_kind   varchar NOT NULL,
      supported_satellite_vids varchar,
      supported_earth_station_vids varchar,
      plmn_id              varchar NOT NULL,
      settlement_mode      varchar NOT NULL,
      registered_at        varchar NOT NULL,
      valid_until          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_ntn_cell_on_satellite (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_ntn_handover_for_profile (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_ntn_isl_between_sats (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_ntn_contact_for_station (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_telecom_ntn_satellite_inventory AS
      SELECT operator_org_id, orbit_class, status, COUNT(*) AS satellite_count
      FROM vertex_telecom_ntn_satellite
      GROUP BY operator_org_id, orbit_class, status;

CREATE MATERIALIZED VIEW mv_telecom_ntn_earth_station_inventory AS
      SELECT operator_org_id, station_kind, jurisdiction, status, COUNT(*) AS station_count
      FROM vertex_telecom_ntn_earth_station
      GROUP BY operator_org_id, station_kind, jurisdiction, status;

CREATE MATERIALIZED VIEW mv_telecom_ntn_cell_state AS
      SELECT cell_pattern, payload_kind, plmn_id, status, COUNT(*) AS cell_count, AVG(beam_count) AS avg_beam_count
      FROM vertex_telecom_ntn_cell
      GROUP BY cell_pattern, payload_kind, plmn_id, status;

CREATE MATERIALIZED VIEW mv_telecom_ntn_handover_summary AS
      SELECT handover_kind, trigger_kind, status,
             COUNT(*) AS handover_count,
             AVG(doppler_offset_hz) AS avg_doppler_hz,
             AVG(one_way_delay_ms) AS avg_owd_ms
      FROM vertex_telecom_ntn_handover
      GROUP BY handover_kind, trigger_kind, status;

CREATE MATERIALIZED VIEW mv_telecom_ntn_contact_throughput AS
      SELECT station_vid, contact_kind,
             COUNT(*) AS contact_count,
             SUM(duration_seconds) AS total_duration_seconds,
             SUM(ingress_bytes) AS total_ingress_bytes,
             SUM(egress_bytes) AS total_egress_bytes
      FROM vertex_telecom_ntn_contact
      GROUP BY station_vid, contact_kind;

CREATE MATERIALIZED VIEW mv_telecom_ntn_partner_state AS
      SELECT constellation_kind, settlement_mode, status, COUNT(*) AS partner_count
      FROM vertex_telecom_ntn_partner
      GROUP BY constellation_kind, settlement_mode, status;
