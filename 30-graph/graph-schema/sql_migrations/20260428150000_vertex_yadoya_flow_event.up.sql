CREATE TABLE vertex_yadoya_flow_event (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      flow_event_id          varchar NOT NULL,
      source_did             varchar NOT NULL,
      counterparty_did       varchar,
      reservation_vid        varchar,
      hotel_vid              varchar,
      fiscal_period          varchar NOT NULL,
      industry_code          varchar NOT NULL,
      flow_kind              varchar NOT NULL,
      currency               varchar,
      amount_bucket          varchar,
      service_class          varchar,
      service_count          integer,
      service_unit           varchar,
      cohort_id              varchar,
      cohort_size            integer,
      currency_flow_uri      varchar,
      service_flow_uri       varchar,
      source_url             varchar,
      source_license         varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    );

CREATE MATERIALIZED VIEW mv_yadoya_flow_currency_by_chain_period AS
      SELECT
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period,
        currency,
        amount_bucket,
        COUNT(*) AS event_count
      FROM vertex_yadoya_flow_event
      WHERE flow_kind IN ('reservation_revenue', 'cancellation_refund')
      GROUP BY COALESCE(counterparty_did, 'independent'), fiscal_period, currency, amount_bucket;

CREATE MATERIALIZED VIEW mv_yadoya_flow_service_by_chain_period AS
      SELECT
        COALESCE(counterparty_did, 'independent') AS counterparty_did,
        fiscal_period,
        service_class,
        service_unit,
        SUM(service_count) AS total_count,
        COUNT(*) AS event_count
      FROM vertex_yadoya_flow_event
      WHERE service_class IS NOT NULL
      GROUP BY COALESCE(counterparty_did, 'independent'), fiscal_period, service_class, service_unit;
