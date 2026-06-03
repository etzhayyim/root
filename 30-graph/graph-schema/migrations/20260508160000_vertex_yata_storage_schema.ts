import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (yatabase customer-owned data — not etzhayyim-internal Tier-3 PII,
//          but per-tenant business-confidential.)

/**
 * yatabase.etzhayyim.com — Phase 3 Supabase-style integrated storage schema
 * (ADR-2605080000 §D10, supersedes §D4 obj-as-separate-product).
 *
 * Pattern: T2 BPMN-as-actor (ADR-0036 Worker-direct Hyperdrive +
 * ADR-0056 BPMN-as-actor + ADR-2604282300 pymagatama + Zeebe). The
 * yatabase CF Worker is a thin edge proxy; all writes hit RisingWave
 * directly via Hyperdrive, all blob bytes hit B2 / Vultr Object Storage
 * via SigV4.
 *
 * Tenant model:
 *   The control-plane tables below live in the etzhayyim platform RW
 *   database (`postgres` / `dev`). Per-tenant data lives in
 *   `yata_<sha256(did)[:16]>` databases provisioned by
 *   task_yata_database_provision (P3 primitive). The MVs over the
 *   control-plane tables drive billing + quota enforcement.
 *
 *   Customer schema *inside* a tenant DB is declared by the customer
 *   (yata Rust crate `#[derive(Vertex)]` proc-macro emits CREATE TABLE).
 *   The `vertex_yata_*` storage tables are also created inside each
 *   tenant DB at provision time so customer SQL sees them as part of
 *   the same schema — that's the Supabase-style integration.
 *
 * Control-plane tables (8 vertex):
 *   vertex_yata_database         per-tenant RW database catalog
 *   vertex_yata_role             per-tenant PG role
 *   vertex_yata_quota            plan limits per tenant
 *   vertex_yata_bucket           bucket metadata (cross-tenant catalog)
 *   vertex_yata_blob             blob metadata (cross-tenant catalog)
 *   vertex_yata_blob_acl         per-DID grant
 *   vertex_yata_blob_embedding   pgvector hybrid (768-dim, Gemma-4-E2B)
 *   vertex_yata_blob_tag         LLM auto-tag
 *   vertex_yata_blob_version     versioning + delete markers
 *   vertex_yata_multipart        in-progress multipart upload state
 *
 * Edges (2):
 *   edge_yata_blob_in_bucket
 *   edge_yata_blob_referenced_by  (blob ↔ arbitrary customer vertex)
 *
 * Streaming MVs (4):
 *   mv_yata_storage_by_org       per-org × tier bytes_stored × tier
 *                                  feeds billing.event metering rollup
 *   mv_yata_egress_by_org        per-org egress_gb (BWA flag)
 *   mv_yata_blob_count_by_org
 *   mv_yata_blob_embedding_queue blobs with NULL embedding ready for
 *                                  R/PT5M batch worker
 *
 * NOTE: Vector column uses real[] (RW does not support pgvector
 * extension; we store the 768-dim embedding as REAL[] and rely on
 * SQL UDF cosine similarity for KNN — see ADR-0044 + 0044 reference
 * impl in graph-schema/migrations/20260421160000_udf_classify_t1.ts).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Control plane: tenant DB catalog ──────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_database (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      db_name varchar NOT NULL,
      org_did varchar NOT NULL,
      cluster_id varchar NOT NULL,
      region varchar NOT NULL,
      plan varchar NOT NULL,
      pg_user varchar NOT NULL,
      pg_password_hash varchar NOT NULL,
      provisioned_at varchar NOT NULL,
      last_active_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_database_org ON vertex_yata_database (org_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_database_status ON vertex_yata_database (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_role (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      role_name varchar NOT NULL,
      org_did varchar NOT NULL,
      db_name varchar NOT NULL,
      grants varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_quota (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      org_did varchar NOT NULL,
      max_nodes bigint,
      max_edges bigint,
      max_state_gb double precision,
      max_mvs int,
      max_storage_gb double precision,
      max_egress_gb double precision,
      max_class_a_per_month bigint,
      max_class_b_per_month bigint,
      max_concurrent_connections int,
      max_dml_rows_per_second int,
      reasoning_profile varchar,
      effective_from date NOT NULL,
      effective_until date,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_quota_org ON vertex_yata_quota (org_did)`.execute(db);

  // ── Storage plane: bucket / blob / version / acl / embedding / tag / multipart ──

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_bucket (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      bucket_name varchar NOT NULL,
      org_did varchar NOT NULL,
      db_name varchar,
      region varchar NOT NULL,
      encryption varchar NOT NULL,
      tier_policy varchar NOT NULL,
      versioning_enabled boolean NOT NULL,
      cors_json varchar,
      lifecycle_json varchar,
      public_read boolean NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_bucket_org ON vertex_yata_bucket (org_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_bucket_name ON vertex_yata_bucket (bucket_name)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_blob (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      bucket_id varchar NOT NULL,
      bucket_name varchar NOT NULL,
      org_did varchar NOT NULL,
      object_key varchar NOT NULL,
      version_id varchar,
      size_bytes bigint NOT NULL,
      content_type varchar,
      etag varchar NOT NULL,
      cid varchar,
      storage_tier varchar NOT NULL,
      storage_provider varchar NOT NULL,
      storage_path varchar NOT NULL,
      encryption varchar NOT NULL,
      vault_member_did varchar,
      is_delete_marker boolean NOT NULL,
      checksum_sha256 varchar,
      uploaded_by_did varchar,
      last_accessed_at varchar,
      embedding_status varchar,
      tag_status varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_org ON vertex_yata_blob (org_did, bucket_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_key ON vertex_yata_blob (bucket_name, object_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_tier ON vertex_yata_blob (storage_tier, last_accessed_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_embedding_q ON vertex_yata_blob (embedding_status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_blob_version (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      blob_id varchar NOT NULL,
      bucket_name varchar NOT NULL,
      object_key varchar NOT NULL,
      version_id varchar NOT NULL,
      size_bytes bigint NOT NULL,
      etag varchar NOT NULL,
      is_delete_marker boolean NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_blob_acl (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      blob_id varchar NOT NULL,
      grantee_did varchar NOT NULL,
      permission varchar NOT NULL,
      granted_by_did varchar NOT NULL,
      expires_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_acl_blob ON vertex_yata_blob_acl (blob_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_acl_grantee ON vertex_yata_blob_acl (grantee_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_blob_embedding (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      blob_id varchar NOT NULL,
      bucket_name varchar NOT NULL,
      object_key varchar NOT NULL,
      org_did varchar NOT NULL,
      model varchar NOT NULL,
      vec_norm double precision,
      vec_dim int,
      vec_floats real[],
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_embedding_blob ON vertex_yata_blob_embedding (blob_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_blob_tag (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      blob_id varchar NOT NULL,
      tag varchar NOT NULL,
      confidence double precision,
      model varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_tag_blob ON vertex_yata_blob_tag (blob_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_tag_tag ON vertex_yata_blob_tag (tag)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yata_multipart (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      upload_id varchar NOT NULL,
      bucket_name varchar NOT NULL,
      object_key varchar NOT NULL,
      org_did varchar NOT NULL,
      content_type varchar,
      parts_received int NOT NULL,
      total_bytes bigint NOT NULL,
      storage_provider varchar NOT NULL,
      provider_upload_id varchar NOT NULL,
      parts_json varchar,
      initiated_at varchar NOT NULL,
      expires_at varchar NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_multipart_upload ON vertex_yata_multipart (upload_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_multipart_status ON vertex_yata_multipart (status, expires_at)`.execute(db);

  // ── Edges ──

  await sql`
    CREATE TABLE IF NOT EXISTS edge_yata_blob_in_bucket (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_yata_blob_referenced_by (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL,
      relation varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_in_bucket_src ON edge_yata_blob_in_bucket (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yata_blob_referenced_by_dst ON edge_yata_blob_referenced_by (dst_vid)`.execute(db);

  // ── Streaming MVs ──

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yata_storage_by_org AS
      SELECT
        org_did,
        bucket_name,
        storage_tier,
        storage_provider,
        SUM(size_bytes) AS bytes_stored,
        COUNT(*) AS blob_count
      FROM vertex_yata_blob
      WHERE is_delete_marker = false AND status = 'active'
      GROUP BY org_did, bucket_name, storage_tier, storage_provider;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yata_blob_count_by_org AS
      SELECT
        org_did,
        COUNT(*) AS total_blobs,
        SUM(size_bytes) AS total_bytes
      FROM vertex_yata_blob
      WHERE is_delete_marker = false AND status = 'active'
      GROUP BY org_did;
  `.execute(db);

  // Egress is computed by metering: each GET/HEAD response logs an
  // `egress_gb` event into vertex_billing_event (P1). This MV joins
  // the billing event table and re-projects per-org × bucket so an
  // ops dashboard can read it without re-aggregating raw events.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yata_egress_by_org AS
      SELECT
        org_did,
        ref_resource AS bucket_name,
        CAST(to_timestamp(ts_ms / 1000.0) AS date) AS day,
        SUM(qty) AS egress_gb,
        SUM(COALESCE(billed_amount_jpy_micro, 0)) AS billed_jpy_micro
      FROM vertex_billing_event
      WHERE metric = 'egress_gb' AND product = 'yata'
      GROUP BY org_did, ref_resource, CAST(to_timestamp(ts_ms / 1000.0) AS date);
  `.execute(db);

  // Embedding queue MV: blobs that need an embedding generated. The
  // R/PT5M `yata_embedding_queue_drain` BPMN reads from this and feeds
  // RunPod / Vultr Inference. embedding_status = 'pending' on insert,
  // 'inflight' while batched, 'done' on success, 'failed' after retry.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yata_blob_embedding_queue AS
      SELECT
        vertex_id AS blob_id,
        bucket_name,
        object_key,
        org_did,
        content_type,
        size_bytes,
        created_at
      FROM vertex_yata_blob
      WHERE embedding_status = 'pending'
        AND status = 'active'
        AND is_delete_marker = false;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yata_blob_embedding_queue`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yata_egress_by_org`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yata_blob_count_by_org`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yata_storage_by_org`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_yata_blob_referenced_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_yata_blob_in_bucket`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_multipart`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_blob_tag`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_blob_embedding`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_blob_acl`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_blob_version`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_blob`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_bucket`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_quota`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_role`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yata_database`.execute(db);
}
