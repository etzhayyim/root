CREATE TABLE vertex_open_swift_institution (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      bic varchar NOT NULL, institution_did varchar NOT NULL, legal_name varchar,
      country varchar, settlement_agent varchar,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_swift_message (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      uetr varchar NOT NULL, message_type varchar NOT NULL,
      sender_vid varchar NOT NULL, receiver_vid varchar NOT NULL,
      debtor_name varchar, creditor_name varchar,
      amount double precision NOT NULL, currency varchar NOT NULL,
      value_date varchar, screening_decision varchar,
      require_manual_review boolean,
      status varchar NOT NULL, submitted_at varchar NOT NULL,
      settled_at varchar, created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE edge_open_swift_message_party (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE MATERIALIZED VIEW mv_open_swift_pending_messages AS
    SELECT sender_vid,
           COUNT(*) AS pending_count,
           BOOL_OR(require_manual_review) AS any_manual_review,
           SUM(amount) AS pending_amount_sum,
           MAX(submitted_at) AS latest_submitted_at
    FROM vertex_open_swift_message WHERE status IN ('submitted','pending') GROUP BY sender_vid;
