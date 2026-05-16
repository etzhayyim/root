CREATE TABLE vertex_org_unit (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord integer,
      owner_did       varchar,

      -- LEI anchor (denormalized for query convenience)
      lei_vertex_id   varchar NOT NULL,
      lei             varchar NOT NULL,

      -- Recursive parent (nullable = root-level unit, direct child of LEI)
      parent_org_vid  varchar,

      -- Classification (open enum: division | department | project | committee |
      --                            team | board | task_force | workgroup | office | bureau)
      org_type        varchar NOT NULL,

      -- Identity
      name            varchar NOT NULL,
      name_en         varchar,
      code            varchar NOT NULL,   -- short unique key within LEI scope, e.g. "DEPT-001"

      -- Materialized path for subtree queries without recursive CTEs
      path            varchar NOT NULL,   -- e.g. "/PARENT001/DEPT001" or "/PARENT001/DEPT001/TEAM001"
      level           integer NOT NULL,   -- 0 = direct child of LEI, 1 = sub-unit, …

      -- Lifecycle
      status          varchar NOT NULL,   -- active | dissolved | suspended | merged
      valid_from      varchar,
      valid_until     varchar,            -- NULL = still active

      -- Optional metadata
      purpose         varchar,
      url             varchar,
      props           varchar,            -- JSON blob for additional attributes

      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    );

CREATE TABLE edge_org_unit_parent (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord integer,
      owner_did       varchar,
      src_vid         varchar NOT NULL,   -- child org_unit vertex_id
      dst_vid         varchar NOT NULL,   -- parent vertex_id (org_unit OR lei_entity)
      dst_type        varchar NOT NULL,   -- "org_unit" | "lei_entity"
      role            varchar NOT NULL,   -- "child_of" | "reports_to" | "delegates_to"
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    );

CREATE TABLE edge_org_unit_member (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  integer,
      owner_did        varchar,
      person_vertex_id varchar NOT NULL,  -- future vertex_person or vertex_lei_entity (officer)
      org_unit_vid     varchar NOT NULL,
      role             varchar NOT NULL,  -- member | chair | lead | secretary | observer | sponsor
      since            varchar,
      until            varchar,           -- NULL = still active
      confidence       double precision,
      source           varchar,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    );

CREATE MATERIALIZED VIEW mv_org_unit_active_by_lei AS
    SELECT
      lei,
      org_type,
      COUNT(*)        AS unit_count,
      MAX(valid_from) AS latest_valid_from
    FROM vertex_org_unit
    WHERE status = 'active'
    GROUP BY lei, org_type;
