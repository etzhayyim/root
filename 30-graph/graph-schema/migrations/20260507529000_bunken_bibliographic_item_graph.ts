import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bunken_bibliographic_item (
      vertex_id VARCHAR PRIMARY KEY,
      scheme VARCHAR,
      external_id VARCHAR,
      did VARCHAR,
      source_url TEXT,
      title TEXT,
      author TEXT,
      year BIGINT,
      language VARCHAR,
      material_type VARCHAR,
      era VARCHAR,
      country VARCHAR,
      digital_url TEXT,
      did_registered BOOLEAN,
      did_registered_at VARCHAR,
      content_hash VARCHAR,
      discovered_at VARCHAR,
      enriched_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR
    )
  `.execute(db);

  const oldTable = await sql<{ exists: boolean }>`
    SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = current_schema()
        AND table_name = 'vertex_bunken_record'
    ) AS exists
  `.execute(db);
  if (oldTable.rows[0]?.exists) {
    await sql`
      INSERT INTO vertex_bunken_bibliographic_item (
        vertex_id, scheme, external_id, did, source_url, title, author, year,
        language, material_type, era, country, digital_url, did_registered,
        did_registered_at, content_hash, discovered_at, enriched_at, org_id,
        user_id, actor_id, sensitivity_ord, owner_did
      )
      SELECT
        vertex_id, scheme, external_id, did, source_url, title, author, year,
        language, material_type, era, country, digital_url, did_registered,
        did_registered_at, content_hash, discovered_at, enriched_at, org_id,
        user_id, actor_id, sensitivity_ord, owner_did
      FROM vertex_bunken_record
      ON CONFLICT (vertex_id) DO NOTHING
    `.execute(db);
  }

  await sql`
    CREATE INDEX IF NOT EXISTS idx_bunken_bibliographic_item_scheme_external
      ON vertex_bunken_bibliographic_item (scheme, external_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_bunken_bibliographic_item_did_registered
      ON vertex_bunken_bibliographic_item (did_registered, enriched_at)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_bunken_bibliographic_item_title_author
      ON vertex_bunken_bibliographic_item (title, author)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_bunken_bibliographic_item_era_country
      ON vertex_bunken_bibliographic_item (era, country)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_bunken_same_as_src_dst
      ON edge_bunken_same_as (src_vid, dst_vid)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bunken_scheme_coverage AS
    SELECT
      scheme,
      COUNT(*) AS item_count,
      COUNT(*) FILTER (WHERE did_registered) AS did_registered_count,
      COUNT(*) FILTER (WHERE title IS NOT NULL AND title <> '') AS enriched_count
    FROM vertex_bunken_bibliographic_item
    GROUP BY scheme
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bunken_era_country_counts AS
    SELECT era, country, COUNT(*) AS item_count
    FROM vertex_bunken_bibliographic_item
    GROUP BY era, country
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_bunken_era_country_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_bunken_scheme_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bunken_bibliographic_item`.execute(db);
}
