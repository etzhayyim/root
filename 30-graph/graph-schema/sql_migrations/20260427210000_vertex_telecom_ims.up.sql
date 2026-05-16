CREATE TABLE vertex_telecom_ims_subscription (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      subscription_id      varchar NOT NULL,
      profile_vid          varchar NOT NULL,
      subscriber_vid       varchar NOT NULL,
      impi_hash            varchar NOT NULL,
      impu_hash_list       varchar NOT NULL,
      service_profile_ref  varchar,
      s_cscf_fqdn          varchar NOT NULL,
      hss_nf_vid           varchar NOT NULL,
      provisioned_at       varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_sip_registration (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      registration_id      varchar NOT NULL,
      subscription_vid     varchar NOT NULL,
      impi_hash            varchar NOT NULL,
      impu_hash            varchar NOT NULL,
      contact_uri          varchar,
      p_cscf_fqdn          varchar NOT NULL,
      access_network       varchar,
      session_id           varchar,
      expires_seconds      int,
      registered_at        varchar NOT NULL,
      expires_at           varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_voice_call (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      call_id              varchar NOT NULL,
      subscriber_vid       varchar NOT NULL,
      caller_impu_hash     varchar NOT NULL,
      callee_impu_hash     varchar NOT NULL,
      caller_msisdn_hash   varchar,
      callee_msisdn_hash   varchar,
      session_voltype      varchar NOT NULL,
      codec                varchar,
      pdu_session_vid      varchar,
      s_cscf_nf_vid        varchar NOT NULL,
      tas_nf_vid           varchar NOT NULL,
      invited_at           varchar NOT NULL,
      answered_at          varchar,
      released_at          varchar,
      duration_seconds     double precision,
      release_cause        varchar,
      released_by          varchar,
      sip_response_code    int,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_supp_service_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      event_id             varchar NOT NULL,
      call_vid             varchar,
      subscription_vid     varchar NOT NULL,
      service_type         varchar NOT NULL,
      action               varchar NOT NULL,
      target_impu_hash     varchar,
      params               varchar,
      tas_nf_vid           varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_emergency_call (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      emergency_id         varchar NOT NULL,
      call_vid             varchar NOT NULL,
      subscriber_vid       varchar,
      emergency_service    varchar NOT NULL,
      jurisdiction         varchar NOT NULL,
      psap_id              varchar NOT NULL,
      caller_location_hash varchar,
      location_method      varchar,
      e_cscf_nf_vid        varchar NOT NULL,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_voice_interconnect_bridge (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      bridge_id            varchar NOT NULL,
      call_vid             varchar NOT NULL,
      agreement_vid        varchar NOT NULL,
      partner_vid          varchar NOT NULL,
      peer_kind            varchar,
      gateway_kind         varchar NOT NULL,
      gateway_nf_vid       varchar NOT NULL,
      peer_sip_uri_hash    varchar,
      peer_trunk_ref       varchar,
      codec                varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_ims_billing_event (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      billing_id           varchar NOT NULL,
      call_vid             varchar NOT NULL,
      subscriber_vid       varchar NOT NULL,
      event_kind           varchar NOT NULL,
      rating_group         varchar NOT NULL,
      units                double precision NOT NULL,
      unit_of_measure      varchar,
      currency             varchar NOT NULL,
      amount               double precision NOT NULL,
      charging_method      varchar NOT NULL,
      cdf_nf_vid           varchar,
      started_at           varchar NOT NULL,
      ended_at             varchar,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_call_uses_session (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_call_for_subscriber (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_telecom_call_via_interconnect (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_telecom_call_volume AS
      SELECT session_voltype, codec, status,
             COUNT(*) AS call_count,
             SUM(duration_seconds) AS total_duration_seconds
      FROM vertex_telecom_voice_call
      GROUP BY session_voltype, codec, status;

CREATE MATERIALIZED VIEW mv_telecom_emergency_routing AS
      SELECT jurisdiction, emergency_service, psap_id,
             COUNT(*) AS call_count
      FROM vertex_telecom_emergency_call
      GROUP BY jurisdiction, emergency_service, psap_id;

CREATE MATERIALIZED VIEW mv_telecom_supp_service_usage AS
      SELECT service_type, action, COUNT(*) AS event_count
      FROM vertex_telecom_supp_service_event
      GROUP BY service_type, action;

CREATE MATERIALIZED VIEW mv_telecom_ims_billing_summary AS
      SELECT subscriber_vid, currency, charging_method,
             SUM(amount) AS total_amount,
             COUNT(*) AS event_count
      FROM vertex_telecom_ims_billing_event
      GROUP BY subscriber_vid, currency, charging_method;
