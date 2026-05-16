CREATE TABLE vertex_open_hs_classification (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      shipper_org_id  varchar NOT NULL,
      hs_code         varchar NOT NULL,
      product_description varchar,
      country_of_origin varchar,
      value_usd       double precision,
      quantity        double precision,
      unit_code       varchar,
      confidence      double precision NOT NULL,
      verification    varchar NOT NULL,
      status          varchar NOT NULL,
      classified_at   varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_hs_concordance (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      hs_code        varchar NOT NULL,
      other_taxonomy varchar NOT NULL,
      other_code     varchar NOT NULL,
      relation       varchar NOT NULL,
      confidence     double precision,
      source         varchar,
      status         varchar NOT NULL,
      created_at     varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE edge_open_hs_classification_class (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE MATERIALIZED VIEW mv_open_hs_shipments_by_code AS
    SELECT hs_code, country_of_origin,
           COUNT(*) AS shipment_count,
           SUM(value_usd) AS total_value_usd,
           AVG(confidence) AS avg_confidence,
           MAX(classified_at) AS latest_classified_at
    FROM vertex_open_hs_classification
    WHERE status='confirmed'
    GROUP BY hs_code, country_of_origin;
