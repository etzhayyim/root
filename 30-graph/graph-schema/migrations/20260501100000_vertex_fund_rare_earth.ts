import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fund (
      vertex_id       VARCHAR PRIMARY KEY,
      fund_id         VARCHAR,
      name            VARCHAR,
      fund_kind       VARCHAR,
      jurisdiction    VARCHAR,
      aum_amount      DOUBLE PRECISION,
      source_url      VARCHAR,
      source_license  VARCHAR,
      created_date    VARCHAR,
      sensitivity_ord INT         DEFAULT 0,
      owner_did       VARCHAR,
      _seq            BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_rare_earth_coverage (
      vertex_id   VARCHAR PRIMARY KEY,
      mineral     VARCHAR,
      symbol      VARCHAR,
      source      VARCHAR,
      created_at  TIMESTAMPTZ,
      sensitivity_ord INT DEFAULT 0,
      owner_did   VARCHAR,
      _seq        BIGINT
    )
  `.execute(db);

  await sql`GRANT SELECT, INSERT ON vertex_fund TO root`.execute(db);
  await sql`GRANT SELECT, INSERT ON vertex_fund TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT ON vertex_rare_earth_coverage TO root`.execute(db);
  await sql`GRANT SELECT, INSERT ON vertex_rare_earth_coverage TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON vertex_fund FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_fund FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_rare_earth_coverage FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_rare_earth_coverage FROM kaisya_app`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_rare_earth_coverage`.execute(db);
}
