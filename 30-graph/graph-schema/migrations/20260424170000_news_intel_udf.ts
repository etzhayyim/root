import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  const udfHost =
    process.env.RW_UDF_SERVER_HOST || "udf-cluster.mitama-udf.svc.cluster.local:8815";
  const link = udfHost.startsWith("http") ? udfHost : `http://${udfHost}`;

  await sql`DROP FUNCTION IF EXISTS news_source_credibility(varchar, boolean, boolean)`.execute(
    db
  );
  await sql`DROP FUNCTION IF EXISTS news_intel_priority(int, int, int, double precision, double precision)`.execute(
    db
  );

  await sql`
    CREATE FUNCTION news_source_credibility(source_type varchar, primary_source boolean, official_source boolean)
      RETURNS double precision
      AS 'news_source_credibility'
      USING LINK ${sql.lit(link)}
  `.execute(db);

  await sql`
    CREATE FUNCTION news_intel_priority(evidence_count int, official_count int, corroborated_count int, recency_hours double precision, impact double precision)
      RETURNS double precision
      AS 'news_intel_priority'
      USING LINK ${sql.lit(link)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS news_intel_priority(int, int, int, double precision, double precision)`.execute(
    db
  );
  await sql`DROP FUNCTION IF EXISTS news_source_credibility(varchar, boolean, boolean)`.execute(
    db
  );
}
