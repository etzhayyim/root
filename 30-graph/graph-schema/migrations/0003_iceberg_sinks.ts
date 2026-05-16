import { Kysely, sql } from 'kysely';

/**
 * Iceberg sinks: RisingWave MVs + base tables → S3 Parquet (Nessie REST catalog).
 *
 * Architecture:
 *   Primary OLTP: RisingWave (Hummock, PG :4566)
 *   Archive OLAP: Iceberg → S3 Parquet via Nessie REST → Spark/Trino/DuckDB
 *
 * Required environment variables (set in deploy environment):
 *   NESSIE_URI        — Nessie REST catalog URI
 *   S3_BUCKET         — S3 bucket name
 *   S3_ENDPOINT       — S3 endpoint URL
 *   S3_REGION         — S3 region
 *   S3_ACCESS_KEY     — S3 access key
 *   S3_SECRET_KEY     — S3 secret key
 *
 * Note: sql.raw() is used for env vars — never pass user input here.
 */

function sinkWith(opts: {
  name: string;
  type: 'upsert' | 'append-only';
  primaryKey: string;
  forceAppendOnly?: boolean;
}): string {
  const nessieUri  = process.env.NESSIE_URI!;
  const s3Bucket   = process.env.S3_BUCKET!;
  const s3Endpoint = process.env.S3_ENDPOINT!;
  const s3Region   = process.env.S3_REGION!;
  const s3Key      = process.env.S3_ACCESS_KEY!;
  const s3Secret   = process.env.S3_SECRET_KEY!;

  const lines = [
    `  connector = 'iceberg'`,
    `  type = '${opts.type}'`,
    `  primary_key = '${opts.primaryKey}'`,
    ...(opts.forceAppendOnly ? [`  force_append_only = 'true'`] : []),
    `  catalog.type = 'rest'`,
    `  catalog.uri = '${nessieUri}'`,
    `  catalog.name = 'graphar'`,
    `  database.name = 'graphar'`,
    `  table.name = '${opts.name}'`,
    `  warehouse.path = 's3://${s3Bucket}/iceberg/warehouse'`,
    `  s3.endpoint = '${s3Endpoint}'`,
    `  s3.region = '${s3Region}'`,
    `  s3.access.key = '${s3Key}'`,
    `  s3.secret.key = '${s3Secret}'`,
    `  s3.path.style.access = 'true'`,
    `  create_table_if_not_exists = 'true'`,
  ];
  return `WITH (\n${lines.join(',\n')}\n)`;
}

export async function up(db: Kysely<any>): Promise<void> {
  // Sink 1: Follow out-degree MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_follow_out_degree FROM mv_follow_out_degree
    ${sql.raw(sinkWith({ name: 'mv_follow_out_degree', type: 'upsert', primaryKey: 'src_vid' }))}`.execute(db);

  // Sink 2: Follow in-degree MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_follow_in_degree FROM mv_follow_in_degree
    ${sql.raw(sinkWith({ name: 'mv_follow_in_degree', type: 'upsert', primaryKey: 'dst_vid' }))}`.execute(db);

  // Sink 3: Post like count MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_post_like_count FROM mv_post_like_count
    ${sql.raw(sinkWith({ name: 'mv_post_like_count', type: 'upsert', primaryKey: 'dst_vid' }))}`.execute(db);

  // Sink 4: Actor suggestions MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_actor_suggestions FROM mv_actor_suggestions
    ${sql.raw(sinkWith({ name: 'mv_actor_suggestions', type: 'upsert', primaryKey: 'vertex_id' }))}`.execute(db);

  // Sink 5: Actor by DID MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_actor_by_did FROM mv_actor_by_did
    ${sql.raw(sinkWith({ name: 'mv_actor_by_did', type: 'upsert', primaryKey: 'did' }))}`.execute(db);

  // Sink 6: Feed timeline MV → Iceberg (append-only, large volume)
  await sql`CREATE SINK IF NOT EXISTS sink_feed_timeline FROM mv_feed_timeline
    ${sql.raw(sinkWith({ name: 'mv_feed_timeline', type: 'append-only', primaryKey: 'post_id', forceAppendOnly: true }))}`.execute(db);

  // Sink 7: CC domain page count MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_cc_domain_page_count FROM mv_cc_domain_page_count
    ${sql.raw(sinkWith({ name: 'mv_cc_domain_page_count', type: 'upsert', primaryKey: 'domain_did' }))}`.execute(db);

  // Sink 8: CC domain out-degree MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_cc_domain_out_degree FROM mv_cc_domain_out_degree
    ${sql.raw(sinkWith({ name: 'mv_cc_domain_out_degree', type: 'upsert', primaryKey: 'domain_did' }))}`.execute(db);

  // Sink 9: CC domain in-degree MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_cc_domain_in_degree FROM mv_cc_domain_in_degree
    ${sql.raw(sinkWith({ name: 'mv_cc_domain_in_degree', type: 'upsert', primaryKey: 'domain_did' }))}`.execute(db);

  // Sink 10: CC domain coverage MV → Iceberg
  await sql`CREATE SINK IF NOT EXISTS sink_cc_domain_coverage FROM mv_cc_domain_coverage
    ${sql.raw(sinkWith({ name: 'mv_cc_domain_coverage', type: 'upsert', primaryKey: 'domain_did' }))}`.execute(db);

  // Sink 11: vertex_domain → Iceberg archive
  await sql`CREATE SINK IF NOT EXISTS sink_vertex_domain FROM vertex_domain
    ${sql.raw(sinkWith({ name: 'vertex_domain', type: 'upsert', primaryKey: 'vertex_id' }))}`.execute(db);

  // Sink 12: vertex_page → Iceberg archive
  await sql`CREATE SINK IF NOT EXISTS sink_vertex_page FROM vertex_page
    ${sql.raw(sinkWith({ name: 'vertex_page', type: 'upsert', primaryKey: 'vertex_id' }))}`.execute(db);

  // Sink 13: vertex_actor → Iceberg archive
  await sql`CREATE SINK IF NOT EXISTS sink_vertex_actor FROM vertex_actor
    ${sql.raw(sinkWith({ name: 'vertex_actor', type: 'upsert', primaryKey: 'vertex_id' }))}`.execute(db);

  // Sink 14: vertex_profile → Iceberg archive
  await sql`CREATE SINK IF NOT EXISTS sink_vertex_profile FROM vertex_profile
    ${sql.raw(sinkWith({ name: 'vertex_profile', type: 'upsert', primaryKey: 'vertex_id' }))}`.execute(db);

  // Sink 15: edge_hosts_page → Iceberg archive
  await sql`CREATE SINK IF NOT EXISTS sink_edge_hosts_page FROM edge_hosts_page
    ${sql.raw(sinkWith({ name: 'edge_hosts_page', type: 'upsert', primaryKey: 'src_vid,dst_vid,edge_id' }))}`.execute(db);

  // Sink 16: edge_links_to → Iceberg archive
  await sql`CREATE SINK IF NOT EXISTS sink_edge_links_to FROM edge_links_to
    ${sql.raw(sinkWith({ name: 'edge_links_to', type: 'upsert', primaryKey: 'src_vid,dst_vid,edge_id' }))}`.execute(db);

  // Sink 17: edge_links_to_domain → Iceberg archive
  await sql`CREATE SINK IF NOT EXISTS sink_edge_links_to_domain FROM edge_links_to_domain
    ${sql.raw(sinkWith({ name: 'edge_links_to_domain', type: 'upsert', primaryKey: 'src_vid,dst_vid,edge_id' }))}`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  const sinks = [
    'sink_edge_links_to_domain',
    'sink_edge_links_to',
    'sink_edge_hosts_page',
    'sink_vertex_profile',
    'sink_vertex_actor',
    'sink_vertex_page',
    'sink_vertex_domain',
    'sink_cc_domain_coverage',
    'sink_cc_domain_in_degree',
    'sink_cc_domain_out_degree',
    'sink_cc_domain_page_count',
    'sink_feed_timeline',
    'sink_actor_by_did',
    'sink_actor_suggestions',
    'sink_post_like_count',
    'sink_follow_in_degree',
    'sink_follow_out_degree',
  ];
  for (const sink of sinks) {
    await sql`DROP SINK IF EXISTS ${sql.raw(sink)}`.execute(db);
  }
}
