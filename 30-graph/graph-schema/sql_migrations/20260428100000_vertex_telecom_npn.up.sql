CREATE TABLE vertex_telecom_npn_snpn_deployment (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      snpn_id              varchar NOT NULL,
      enterprise_org_id    varchar NOT NULL,
      deployment_kind      varchar NOT NULL,
      plmn_id              varchar NOT NULL,
      nid_value            varchar NOT NULL,
      hosting_nf_vids      varchar,
      jurisdiction         varchar NOT NULL,
      registered_at        varchar NOT NULL,
      valid_until          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_npn_cag (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      cag_id               varchar NOT NULL,
      snpn_vid             varchar NOT NULL,
      cag_value            varchar NOT NULL,
      display_name         varchar NOT NULL,
      allowed_cell_site_vids varchar,
      allowed_ran_node_vids varchar,
      access_kind          varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_npn_nid_allocation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      allocation_id        varchar NOT NULL,
      snpn_vid             varchar NOT NULL,
      nid_value            varchar NOT NULL,
      assignment_kind      varchar NOT NULL,
      oui_prefix           varchar,
      ieee_authority_ref   varchar,
      allocated_at         varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_npn_pni_slice (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      pni_id               varchar NOT NULL,
      enterprise_org_id    varchar NOT NULL,
      hosting_plmn_id      varchar NOT NULL,
      snssai               varchar NOT NULL,
      dnn                  varchar NOT NULL,
      cag_vid              varchar,
      isolation_kind       varchar NOT NULL,
      sla_tier             varchar NOT NULL,
      provisioned_at       varchar NOT NULL,
      valid_until          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_npn_id_mapping (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      mapping_id           varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      supi_hash            varchar NOT NULL,
      gpsi_kind            varchar NOT NULL,
      gpsi_hash            varchar NOT NULL,
      snpn_vid             varchar,
      action               varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_npn_nsacf_decision (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      decision_id          varchar NOT NULL,
      nsacf_nf_vid         varchar NOT NULL,
      snssai               varchar NOT NULL,
      snpn_vid             varchar,
      requester_nf_vid     varchar NOT NULL,
      profile_vid          varchar,
      request_kind         varchar NOT NULL,
      current_registered_ues int,
      current_established_sessions int,
      max_registered_ues   int,
      max_established_sessions int,
      decision             varchar NOT NULL,
      decision_reason      varchar,
      admit                boolean NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_npn_prose_policy (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      prose_id             varchar NOT NULL,
      snpn_vid             varchar NOT NULL,
      communication_kind   varchar NOT NULL,
      layer2_group_id      varchar,
      prose_policy_hash    varchar NOT NULL,
      prose_policy_ref     varchar,
      sidelink_profile     varchar,
      allowed_ran_node_vids varchar,
      provisioned_at       varchar NOT NULL,
      valid_until          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_npn_subscriber_enrollment (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      enrollment_id        varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      snpn_vid             varchar,
      pni_vid              varchar,
      cag_vids             varchar,
      allowed_device_class varchar,
      device_count         int,
      sponsored_by_enterprise_org_id varchar NOT NULL,
      enrolled_at          varchar NOT NULL,
      valid_until          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_npn_cag_under_snpn (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_npn_pni_under_cag (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_npn_enrollment_for_profile (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_telecom_npn_snpn_state AS
      SELECT deployment_kind, jurisdiction, status, COUNT(*) AS deployment_count
      FROM vertex_telecom_npn_snpn_deployment
      GROUP BY deployment_kind, jurisdiction, status;

CREATE MATERIALIZED VIEW mv_telecom_npn_pni_inventory AS
      SELECT hosting_plmn_id, snssai, isolation_kind, sla_tier, status, COUNT(*) AS slice_count
      FROM vertex_telecom_npn_pni_slice
      GROUP BY hosting_plmn_id, snssai, isolation_kind, sla_tier, status;

CREATE MATERIALIZED VIEW mv_telecom_npn_nsacf_admission_rate AS
      SELECT snssai, request_kind, decision, COUNT(*) AS decision_count
      FROM vertex_telecom_npn_nsacf_decision
      GROUP BY snssai, request_kind, decision;

CREATE MATERIALIZED VIEW mv_telecom_npn_prose_policy_state AS
      SELECT communication_kind, sidelink_profile, status, COUNT(*) AS policy_count
      FROM vertex_telecom_npn_prose_policy
      GROUP BY communication_kind, sidelink_profile, status;

CREATE MATERIALIZED VIEW mv_telecom_npn_enrollment_summary AS
      SELECT sponsored_by_enterprise_org_id, allowed_device_class, status,
             COUNT(*) AS enrollment_count,
             SUM(device_count) AS total_devices
      FROM vertex_telecom_npn_subscriber_enrollment
      GROUP BY sponsored_by_enterprise_org_id, allowed_device_class, status;
