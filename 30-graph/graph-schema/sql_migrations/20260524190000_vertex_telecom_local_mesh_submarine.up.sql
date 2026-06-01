CREATE TABLE vertex_telecom_bluetooth_device (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      device_id            varchar NOT NULL,
      device_name          varchar,
      address_hash         varchar NOT NULL,
      address_kind         varchar NOT NULL,
      bluetooth_version    varchar NOT NULL,
      device_role          varchar NOT NULL,
      gatt_profile_refs    varchar,
      site_vid             varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_bluetooth_mesh_node (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      node_id              varchar NOT NULL,
      device_vid           varchar NOT NULL,
      mesh_network_id      varchar NOT NULL,
      unicast_address      varchar NOT NULL,
      element_count        int NOT NULL,
      relay_enabled        boolean NOT NULL,
      friend_enabled       boolean NOT NULL,
      low_power_enabled    boolean NOT NULL,
      provisioned_at       varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_bluetooth_observation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      observation_id       varchar NOT NULL,
      observer_asset_vid   varchar NOT NULL,
      device_vid           varchar,
      address_hash         varchar NOT NULL,
      rssi_dbm             double precision,
      tx_power_dbm         double precision,
      service_uuid_hashes  varchar,
      advertisement_hash   varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_wlan_mesh_node (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      mesh_node_id         varchar NOT NULL,
      venue_vid            varchar,
      site_vid             varchar,
      ssid                 varchar NOT NULL,
      mesh_id              varchar NOT NULL,
      hwmp_enabled         boolean NOT NULL,
      backhaul_kind        varchar NOT NULL,
      channel              int,
      band                 varchar NOT NULL,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_wlan_mesh_link (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      link_id              varchar NOT NULL,
      source_mesh_node_vid varchar NOT NULL,
      target_mesh_node_vid varchar NOT NULL,
      metric_kind          varchar NOT NULL,
      airtime_link_metric  double precision,
      rssi_dbm             double precision,
      tx_rate_mbps         double precision,
      rx_rate_mbps         double precision,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_submarine_cable_system (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      cable_system_id      varchar NOT NULL,
      display_name         varchar NOT NULL,
      owner_org_id         varchar NOT NULL,
      design_capacity_tbps double precision,
      lit_capacity_tbps    double precision,
      ready_for_service_at varchar,
      jurisdiction_scope   varchar NOT NULL,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_submarine_landing_station (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      station_id           varchar NOT NULL,
      cable_system_vid     varchar NOT NULL,
      display_name         varchar NOT NULL,
      country_code         varchar NOT NULL,
      latitude             double precision,
      longitude            double precision,
      terrestrial_backhaul_vid varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_submarine_repeater (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      repeater_id          varchar NOT NULL,
      cable_system_vid     varchar NOT NULL,
      route_segment_vid    varchar,
      sequence_no          int NOT NULL,
      latitude             double precision,
      longitude            double precision,
      gain_db              double precision,
      power_feed_voltage_v double precision,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_submarine_route_segment (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      segment_id           varchar NOT NULL,
      cable_system_vid     varchar NOT NULL,
      source_station_vid   varchar,
      target_station_vid   varchar,
      optical_span_vid     varchar,
      length_km            double precision NOT NULL,
      seabed_zone          varchar,
      burial_depth_m       double precision,
      route_geometry_ref   varchar,
      registered_at        varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_submarine_repair_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      repair_id            varchar NOT NULL,
      cable_system_vid     varchar NOT NULL,
      route_segment_vid    varchar,
      fault_kind           varchar NOT NULL,
      fault_latitude       double precision,
      fault_longitude      double precision,
      vessel_ref           varchar,
      rov_asset_ref        varchar,
      dispatched_at        varchar,
      completed_at         varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_bluetooth_mesh_neighbor (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_wlan_mesh_link_between_nodes (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_submarine_segment_connects_station (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_telecom_bluetooth_inventory AS
      SELECT device_role, bluetooth_version, status, COUNT(*) AS device_count
      FROM vertex_telecom_bluetooth_device
      GROUP BY device_role, bluetooth_version, status;

CREATE MATERIALIZED VIEW mv_telecom_wlan_mesh_link_state AS
      SELECT mesh_id, status, COUNT(*) AS node_count
      FROM vertex_telecom_wlan_mesh_node
      GROUP BY mesh_id, status;

CREATE MATERIALIZED VIEW mv_telecom_submarine_cable_capacity AS
      SELECT owner_org_id, jurisdiction_scope, status,
             COUNT(*) AS system_count,
             SUM(design_capacity_tbps) AS total_design_capacity_tbps,
             SUM(lit_capacity_tbps) AS total_lit_capacity_tbps
      FROM vertex_telecom_submarine_cable_system
      GROUP BY owner_org_id, jurisdiction_scope, status;
