CREATE TABLE vertex_telecom_tmf_product_offering (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      offering_id          varchar NOT NULL,
      name                 varchar NOT NULL,
      description          varchar,
      lifecycle_status     varchar NOT NULL,
      product_spec_id      varchar,
      category_ids         varchar,
      channel_ids          varchar,
      market_ids           varchar,
      price_ref            varchar,
      valid_from_at        varchar,
      valid_to_at          varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tmf_product_order (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      product_order_id     varchar NOT NULL,
      account_id           varchar NOT NULL,
      order_kind           varchar NOT NULL,
      offering_id          varchar,
      product_id           varchar,
      order_item_hash      varchar,
      order_item_ref       varchar,
      requested_start_at   varchar,
      requested_completion_at varchar,
      priority             int,
      channel_id           varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tmf_product_inventory (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      record_id            varchar NOT NULL,
      product_id           varchar NOT NULL,
      account_id           varchar NOT NULL,
      offering_id          varchar,
      product_order_id     varchar,
      lifecycle_status     varchar NOT NULL,
      started_at           varchar,
      terminated_at        varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tmf_service_order (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      service_order_id     varchar NOT NULL,
      product_order_id     varchar NOT NULL,
      product_id           varchar,
      service_spec         varchar,
      order_kind           varchar NOT NULL,
      order_item_hash      varchar,
      order_item_ref       varchar,
      requested_start_at   varchar,
      requested_completion_at varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tmf_service_activation (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      activation_id        varchar NOT NULL,
      service_order_id     varchar NOT NULL,
      service_instance_kind varchar NOT NULL,
      service_instance_vid varchar,
      action               varchar NOT NULL,
      configuration_hash   varchar,
      configuration_ref    varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tmf_service_inventory (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      record_id            varchar NOT NULL,
      service_instance_kind varchar NOT NULL,
      service_instance_vid varchar,
      product_id           varchar,
      service_order_id     varchar,
      lifecycle_status     varchar NOT NULL,
      operational_state    varchar,
      started_at           varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tmf_customer_account (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      account_id           varchar NOT NULL,
      customer_kind        varchar NOT NULL,
      account_kind         varchar NOT NULL,
      party_name           varchar,
      party_contact        varchar,
      party_tax_id         varchar,
      billing_address      varchar,
      currency             varchar,
      payment_method_kind  varchar,
      payment_method_ref   varchar,
      parent_subscriber_id varchar,
      jurisdiction         varchar,
      observed_at          varchar NOT NULL,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE vertex_telecom_tmf_customer_bill (
      vertex_id            varchar PRIMARY KEY,
      _seq                 bigint,
      created_date         date,
      sensitivity_ord      int,
      owner_did            varchar,
      bill_id              varchar NOT NULL,
      account_id           varchar NOT NULL,
      period_start         varchar NOT NULL,
      period_end           varchar NOT NULL,
      currency             varchar,
      source_invoice_vids  varchar,
      due_at               varchar,
      delivery_channel     varchar,
      bill_document_ref    varchar,
      total_amount         double precision,
      status               varchar NOT NULL,
      created_at           varchar,
      org_id               varchar,
      user_id              varchar,
      actor_id             varchar
    );

CREATE TABLE edge_telecom_tmf_order_offering (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    );

CREATE TABLE edge_telecom_tmf_inventory_order (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    );

CREATE TABLE edge_telecom_tmf_service_order_product_order (
      edge_id              varchar PRIMARY KEY,
      src_vertex_id        varchar NOT NULL,
      dst_vertex_id        varchar NOT NULL,
      created_at           varchar
    );

CREATE MATERIALIZED VIEW mv_telecom_tmf_active_offerings AS
    SELECT offering_id, name, lifecycle_status, valid_from_at, valid_to_at, org_id
    FROM vertex_telecom_tmf_product_offering
    WHERE lifecycle_status IN ('Active', 'Launched');

CREATE MATERIALIZED VIEW mv_telecom_tmf_open_product_orders AS
    SELECT product_order_id, account_id, order_kind, offering_id, priority, observed_at, status, org_id
    FROM vertex_telecom_tmf_product_order
    WHERE status NOT IN ('completed', 'cancelled', 'rejected');

CREATE MATERIALIZED VIEW mv_telecom_tmf_open_service_orders AS
    SELECT service_order_id, product_order_id, order_kind, service_spec, observed_at, status, org_id
    FROM vertex_telecom_tmf_service_order
    WHERE status NOT IN ('completed', 'cancelled', 'rejected');

CREATE MATERIALIZED VIEW mv_telecom_tmf_active_product_inventory AS
    SELECT record_id, product_id, account_id, lifecycle_status, started_at, org_id
    FROM vertex_telecom_tmf_product_inventory
    WHERE lifecycle_status = 'Active';

CREATE MATERIALIZED VIEW mv_telecom_tmf_active_service_inventory AS
    SELECT record_id, service_instance_kind, service_instance_vid, lifecycle_status, operational_state, started_at, org_id
    FROM vertex_telecom_tmf_service_inventory
    WHERE lifecycle_status = 'active';

CREATE MATERIALIZED VIEW mv_telecom_tmf_bill_summary AS
    SELECT account_id, period_start, period_end, currency, total_amount, due_at, status, org_id
    FROM vertex_telecom_tmf_customer_bill
    ORDER BY period_end DESC;
