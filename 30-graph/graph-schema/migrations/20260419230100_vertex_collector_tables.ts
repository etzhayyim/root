import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_collector_* — 8 new tables covering the write path for c0ll3ct1.
 * Complements existing vertex_collector_run.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_dns_observation (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      node_id VARCHAR, domain VARCHAR, handle VARCHAR, status VARCHAR, observed_at VARCHAR,
      registrar VARCHAR, registrar_handle VARCHAR, registrar_iana_id VARCHAR,
      registration_date VARCHAR, expiration_date VARCHAR, last_changed_date VARCHAR,
      dnssec VARCHAR, run_id VARCHAR,
      a_records VARCHAR, aaaa_records VARCHAR, cname_records VARCHAR,
      mx_records VARCHAR, ns_records VARCHAR, txt_records VARCHAR, nameservers VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_dns_snapshot (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      node_id VARCHAR, domain VARCHAR, registrar VARCHAR, dnssec VARCHAR,
      run_id VARCHAR, snapshot_at VARCHAR,
      a_records VARCHAR, aaaa_records VARCHAR, cname_records VARCHAR,
      mx_records VARCHAR, ns_records VARCHAR, txt_records VARCHAR, nameservers VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_dns_change (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      node_id VARCHAR, domain VARCHAR, change_type VARCHAR, field VARCHAR, run_id VARCHAR,
      detected_at VARCHAR, prev_value VARCHAR, new_value VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_organization (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      node_id VARCHAR, name VARCHAR, handle VARCHAR, iana_id VARCHAR, type VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_blockchain_actor (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      address VARCHAR, chain VARCHAR, label VARCHAR, source VARCHAR,
      balance VARCHAR, total_received VARCHAR, total_sent VARCHAR,
      tx_count BIGINT, unconfirmed_tx_count BIGINT, observed_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_risk_signal (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      node_id VARCHAR, target_node_id VARCHAR, signal_type VARCHAR,
      address VARCHAR, chain VARCHAR, currency VARCHAR, domain VARCHAR,
      value VARCHAR, confidence VARCHAR, detected_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_archive_snapshot (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      node_id VARCHAR, domain VARCHAR, source VARCHAR, url_key VARCHAR, original VARCHAR,
      mimetype VARCHAR, status_code VARCHAR, digest VARCHAR, observed_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_collector_scan_result (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      node_id VARCHAR, ip VARCHAR, port BIGINT, protocol VARCHAR, state VARCHAR,
      service VARCHAR, software VARCHAR, version VARCHAR, banner VARCHAR,
      cert_issuer VARCHAR, cert_subject VARCHAR, cert_expires VARCHAR,
      tls_version VARCHAR, tls_cipher VARCHAR, os_guess VARCHAR,
      scanner_host VARCHAR, scanned_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const t of [
    'vertex_collector_scan_result',
    'vertex_collector_archive_snapshot',
    'vertex_collector_risk_signal',
    'vertex_collector_blockchain_actor',
    'vertex_collector_organization',
    'vertex_collector_dns_change',
    'vertex_collector_dns_snapshot',
    'vertex_collector_dns_observation',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
