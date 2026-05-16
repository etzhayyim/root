import { Kysely, sql } from "kysely";

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_spec (
      vertex_id VARCHAR PRIMARY KEY,
      modem_id VARCHAR NOT NULL,
      chip_name VARCHAR NOT NULL,
      rat_support VARCHAR,
      baseband_chip VARCHAR,
      open_source_fw BOOLEAN NOT NULL DEFAULT false,
      fw_license VARCHAR,
      max_dl_mbps DOUBLE PRECISION,
      max_ul_mbps DOUBLE PRECISION,
      release_year INTEGER,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-modem'
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_type_approval (
      vertex_id VARCHAR PRIMARY KEY,
      modem_did VARCHAR NOT NULL,
      authority VARCHAR NOT NULL,
      certificate_no VARCHAR NOT NULL,
      jurisdiction_iso3 VARCHAR NOT NULL,
      approved_at VARCHAR,
      expiry_date VARCHAR,
      rat_approved VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-modem'
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_sep_dep (
      vertex_id VARCHAR PRIMARY KEY,
      modem_did VARCHAR NOT NULL,
      patent_no VARCHAR NOT NULL,
      holder_did VARCHAR,
      rat VARCHAR NOT NULL,
      frand_declared BOOLEAN NOT NULL DEFAULT false,
      pool_id VARCHAR,
      expiry_date VARCHAR,
      blocker_status VARCHAR NOT NULL DEFAULT 'active',
      severity VARCHAR,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-modem'
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_smartphone_modem_sep_dep`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_smartphone_modem_type_approval`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_smartphone_modem_spec`.execute(db);
}
