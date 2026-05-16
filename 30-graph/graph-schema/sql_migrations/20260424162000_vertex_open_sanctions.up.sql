CREATE TABLE vertex_open_sanctions_entry (
      vertex_id     varchar PRIMARY KEY,
      _seq          bigint, created_date date, sensitivity_ord int, owner_did varchar,
      program       varchar NOT NULL,
      list_id       varchar NOT NULL,
      entity_name   varchar NOT NULL,
      entity_type   varchar NOT NULL,
      country       varchar,
      sanction_type varchar,
      aliases       varchar,
      listed_at     varchar NOT NULL,
      delisted_at   varchar,
      status        varchar NOT NULL,
      created_at    varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE vertex_open_sanctions_screening (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      caller_org_id  varchar NOT NULL,
      candidate_name varchar NOT NULL,
      candidate_country varchar,
      candidate_lei  varchar,
      best_match_name varchar,
      best_match_program varchar,
      match_score    double precision NOT NULL,
      decision       varchar NOT NULL,
      require_manual_review boolean,
      screened_at    varchar NOT NULL,
      created_at     varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE TABLE edge_open_sanctions_screening_entry (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    );

CREATE MATERIALIZED VIEW mv_open_sanctions_blocks_by_program AS
    SELECT best_match_program AS program, decision,
           COUNT(*) AS screening_count,
           MAX(screened_at) AS latest_screened_at
    FROM vertex_open_sanctions_screening
    WHERE decision IN ('block','manual-review')
    GROUP BY best_match_program, decision;
