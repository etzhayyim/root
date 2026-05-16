CREATE TABLE vertex_open_malacca_emission_report (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    report_id varchar NOT NULL, imo varchar NOT NULL, fuel_type varchar,
    co2_tonnes double precision NOT NULL, nox_tonnes double precision, sox_tonnes double precision,
    period_start varchar NOT NULL, period_end varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_open_malacca_imo_compliance (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    compliance_id varchar NOT NULL, imo varchar NOT NULL,
    metric varchar NOT NULL, rating varchar NOT NULL, numeric_value double precision,
    compliance_tier varchar NOT NULL, require_action boolean,
    measured_period varchar NOT NULL, reported_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
