ALTER TABLE edge_business_person_relation
    ADD COLUMN confidence DOUBLE PRECISION;

ALTER TABLE edge_business_person_relation
    ADD COLUMN verification_status VARCHAR;

CREATE INDEX IF NOT EXISTS idx_bpcareer_person
    ON vertex_business_person_career_event(person_vertex_id);

CREATE INDEX IF NOT EXISTS idx_bpskill_person
    ON edge_business_person_skill(person_vertex_id);

CREATE INDEX IF NOT EXISTS idx_bpcert_person
    ON vertex_business_person_cert(person_vertex_id);

CREATE INDEX IF NOT EXISTS idx_bpedu_person
    ON vertex_business_person_edu(person_vertex_id);

CREATE INDEX IF NOT EXISTS idx_bprel_src
    ON edge_business_person_relation(src_person_id);

CREATE INDEX IF NOT EXISTS idx_bprel_dst
    ON edge_business_person_relation(dst_person_id);

CREATE INDEX IF NOT EXISTS idx_bprel_type
    ON edge_business_person_relation(relation_type);

CREATE TABLE IF NOT EXISTS vertex_influence_score (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      person_vertex_id  VARCHAR,
      faction_label     VARCHAR,
      hub_score         DOUBLE PRECISION,
      bridge_score      DOUBLE PRECISION,
      gov_score         DOUBLE PRECISION,
      out_degree        BIGINT,
      in_degree         BIGINT,
      cross_faction_edges BIGINT,
      career_span_years BIGINT,
      computed_at       VARCHAR
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_influence_centrality AS
    SELECT
      p.vertex_id                                         AS person_id,
      p.name_ja,
      p.org_name,
      COALESCE(o.out_deg, 0)                              AS out_degree,
      COALESCE(i.in_deg, 0)                               AS in_degree,
      COALESCE(o.out_deg, 0) + COALESCE(i.in_deg, 0)     AS hub_score,
      COALESCE(g.gov_deg, 0)                              AS gov_score,
      COALESCE(x.cross_deg, 0)                            AS bridge_score,
      COALESCE(str.strong_deg, 0)                         AS strong_tie_count,
      COALESCE(c.career_count, 0)                         AS career_event_count
    FROM vertex_business_person p
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS out_deg
      FROM edge_business_person_relation
      GROUP BY src_person_id
    ) o ON o.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT dst_person_id, COUNT(*) AS in_deg
      FROM edge_business_person_relation
      GROUP BY dst_person_id
    ) i ON i.dst_person_id = p.vertex_id
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS gov_deg
      FROM edge_business_person_relation
      WHERE relation_type = 'government_advisory'
      GROUP BY src_person_id
    ) g ON g.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS cross_deg
      FROM edge_business_person_relation
      WHERE relation_type IN ('conference_co_speaker', 'consortium_member', 'government_advisory')
      GROUP BY src_person_id
    ) x ON x.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT src_person_id, COUNT(*) AS strong_deg
      FROM edge_business_person_relation
      WHERE strength = 'strong'
      GROUP BY src_person_id
    ) str ON str.src_person_id = p.vertex_id
    LEFT JOIN (
      SELECT person_vertex_id, COUNT(*) AS career_count
      FROM vertex_business_person_career_event
      GROUP BY person_vertex_id
    ) c ON c.person_vertex_id = p.vertex_id;
