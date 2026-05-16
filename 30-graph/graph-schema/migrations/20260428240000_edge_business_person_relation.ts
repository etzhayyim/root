import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 20260428240000: person-to-person relationship edges + business_person_edu table.
 *
 * edge_business_person_relation: known professional links between registered persons.
 * relation_type values: hierarchical | peer | industry_group | alumni |
 *   government_advisory | conference_co_speaker | consortium_member | corporate_group
 * strength: strong | moderate | weak
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS edge_business_person_relation (
      edge_id           VARCHAR PRIMARY KEY,
      src_person_id     VARCHAR,
      dst_person_id     VARCHAR,
      relation_type     VARCHAR,
      org_context       VARCHAR,
      direction         VARCHAR,
      strength          VARCHAR,
      since             VARCHAR,
      description       VARCHAR,
      source            VARCHAR,
      ingested_at       VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_business_person_relation`.execute(db);
}
