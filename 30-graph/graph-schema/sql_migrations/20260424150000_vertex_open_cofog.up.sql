CREATE TABLE vertex_open_cofog_expenditure (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      gov_org_id       varchar NOT NULL,
      fiscal_year      int NOT NULL,
      cofog_class_code varchar NOT NULL,
      amount           double precision NOT NULL,
      currency         varchar NOT NULL,
      narrative        varchar,
      evidence_url     varchar,
      confidence       double precision,
      status           varchar NOT NULL,
      reported_at      varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_cofog_concordance (
      vertex_id         varchar PRIMARY KEY,
      _seq              bigint, created_date date, sensitivity_ord int, owner_did varchar,
      cofog_class_code  varchar NOT NULL,
      other_taxonomy    varchar NOT NULL,
      other_code        varchar NOT NULL,
      relation          varchar NOT NULL,
      confidence        double precision,
      source            varchar,
      status            varchar NOT NULL,
      created_at        varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE edge_open_cofog_expenditure_class (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid         varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at      varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE MATERIALIZED VIEW mv_open_cofog_expenditure_by_class AS
    SELECT cofog_class_code, fiscal_year, currency,
           COUNT(*) AS expenditure_count,
           SUM(amount) AS total_amount,
           MAX(reported_at) AS latest_reported_at
    FROM vertex_open_cofog_expenditure
    WHERE status='confirmed'
    GROUP BY cofog_class_code, fiscal_year, currency;
