CREATE TABLE vertex_resource_flow_currency (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_did         varchar NOT NULL,
      counterparty_did   varchar,
      fiscal_period      varchar NOT NULL,
      flow_type          varchar NOT NULL,
      amount             double precision,
      amount_bucket      varchar,
      currency           varchar NOT NULL,
      industry_code      varchar NOT NULL,
      cohort_id          varchar,
      cohort_size        integer,
      source_url         varchar,
      source_license     varchar,
      note               varchar,
      record_uri         varchar NOT NULL,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE vertex_resource_flow_service (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_did         varchar NOT NULL,
      counterparty_did   varchar,
      fiscal_period      varchar NOT NULL,
      service_class      varchar NOT NULL,
      service_count      integer NOT NULL,
      service_unit       varchar NOT NULL,
      revenue            double precision,
      revenue_currency   varchar,
      industry_code      varchar NOT NULL,
      cohort_id          varchar,
      cohort_size        integer,
      source_url         varchar,
      source_license     varchar,
      note               varchar,
      record_uri         varchar NOT NULL,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE vertex_resource_flow_personnel (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_did         varchar NOT NULL,
      counterparty_did   varchar,
      fiscal_period      varchar NOT NULL,
      flow_type          varchar NOT NULL,
      headcount_delta    integer NOT NULL,
      industry_code      varchar NOT NULL,
      cohort_id          varchar,
      cohort_size        integer,
      source_url         varchar,
      source_license     varchar,
      note               varchar,
      record_uri         varchar NOT NULL,
      observed_at        varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE MATERIALIZED VIEW mv_resource_flow_sankey_currency AS
      SELECT
        source_did,
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period,
        flow_type,
        currency,
        industry_code,
        amount_bucket,
        SUM(COALESCE(amount, 0)) AS amount_sum,
        COUNT(*) AS event_count
      FROM vertex_resource_flow_currency
      GROUP BY source_did, COALESCE(counterparty_did, 'independent'),
               fiscal_period, flow_type, currency, industry_code, amount_bucket;

CREATE MATERIALIZED VIEW mv_resource_flow_sankey_service AS
      SELECT
        source_did,
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period,
        service_class,
        service_unit,
        industry_code,
        SUM(service_count) AS total_count,
        SUM(COALESCE(revenue, 0)) AS revenue_sum,
        COUNT(*) AS event_count
      FROM vertex_resource_flow_service
      GROUP BY source_did, COALESCE(counterparty_did, 'independent'),
               fiscal_period, service_class, service_unit, industry_code;

CREATE MATERIALIZED VIEW mv_resource_flow_sankey_personnel AS
      SELECT
        source_did,
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period,
        flow_type,
        industry_code,
        SUM(headcount_delta) AS headcount_sum,
        COUNT(*) AS event_count
      FROM vertex_resource_flow_personnel
      GROUP BY source_did, COALESCE(counterparty_did, 'independent'),
               fiscal_period, flow_type, industry_code;
