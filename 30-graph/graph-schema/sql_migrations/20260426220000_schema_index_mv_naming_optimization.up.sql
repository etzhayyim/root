CREATE INDEX IF NOT EXISTS idx_maps_coverage_target_source_label
      ON vertex_maps_coverage_target (source_did, label);

CREATE INDEX IF NOT EXISTS idx_maps_coverage_target_last_fetched
      ON vertex_maps_coverage_target (last_fetched_at);

CREATE INDEX IF NOT EXISTS idx_contracts_org_source_record_id
      ON vertex_contracts_organization (source_record_id);

CREATE INDEX IF NOT EXISTS idx_open_lei_entity_lei
      ON vertex_open_lei_entity (lei);

CREATE INDEX IF NOT EXISTS idx_open_lei_entity_country_status
      ON vertex_open_lei_entity (country, status);

CREATE INDEX IF NOT EXISTS idx_open_lei_ownership_parent
      ON vertex_open_lei_ownership (parent_lei);

CREATE INDEX IF NOT EXISTS idx_open_lei_ownership_child
      ON vertex_open_lei_ownership (child_lei);

CREATE INDEX IF NOT EXISTS idx_edge_open_lei_ownership_pair_src
      ON edge_open_lei_ownership_pair (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_open_lei_ownership_pair_dst
      ON edge_open_lei_ownership_pair (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_ads_operated_by_lei
      ON edge_ads_operated_by (lei);

CREATE INDEX IF NOT EXISTS idx_edge_hospitality_lei_bridge_lei
      ON edge_hospitality_lei_bridge (lei);

CREATE INDEX IF NOT EXISTS idx_vertex_hc_sp_application_lei
      ON vertex_hc_sp_application (lei);

CREATE INDEX IF NOT EXISTS idx_vertex_open_carrier_fleet_carrier_lei
      ON vertex_open_carrier_fleet_carrier (lei);

CREATE INDEX IF NOT EXISTS idx_vertex_real_estate_party_lei
      ON vertex_real_estate_party (lei);

DROP VIEW IF EXISTS mv_maps_coverage_gap_ranked;

DROP VIEW IF EXISTS view_world_coverage_live;

CREATE VIEW view_world_coverage_live AS
    SELECT * FROM mv_world_coverage_live;
