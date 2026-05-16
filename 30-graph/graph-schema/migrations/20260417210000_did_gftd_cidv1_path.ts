import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * ADR-0029 — did:gftd Method Specification (CIDv1 + path-form).
 *
 * Extends `vertex_gftd_identity` with CIDv1 metadata columns. The
 * `parent_did` and `depth` columns were already added by an earlier
 * out-of-band migration (`20260417150000_gftd_did_recursive_tree`); this
 * migration is purely additive on top of that.
 *
 * Reference:
 *   - 90-docs/adr/0029-did-gftd-method-specification.md
 *   - 10-protocol/did-gftd/  (TypeScript reference impl)
 *
 * Columns added to vertex_gftd_identity (CIDv1 specific only):
 *   cid_version       BIGINT   -- 1 (CIDv1)
 *   multicodec        VARCHAR  -- 'raw' (0x55)
 *   multihash_code    VARCHAR  -- 'sha2-256' (0x12) — future: 'blake3', etc.
 *   multibase_prefix  VARCHAR  -- 'b' (base32 lowercase, IPFS canonical)
 *   genesis_op_cid    VARCHAR  -- CID of the genesis op CBOR (= last segment of did, for verify)
 *   root_did          VARCHAR  -- did:gftd of the root (depth=0 ancestor)
 *   path_segment      VARCHAR  -- UTF-8 segment used in genesis op (NULL for root)
 *
 * Already present (do NOT re-ADD):
 *   parent_did        VARCHAR  -- from 20260417150000_gftd_did_recursive_tree
 *   depth             BIGINT   -- from 20260417150000_gftd_did_recursive_tree
 *
 * New tables:
 *   edge_gftd_path_child  parent did:gftd → child did:gftd, with segment label
 *   vertex_gftd_op_log    signed op history per DID
 */

export async function up(db: Kysely<any>): Promise<void> {

  // ── ALTER vertex_gftd_identity: CIDv1 metadata only ───────────────────
  // (parent_did + depth already added by 20260417150000_gftd_did_recursive_tree)

  await sql`ALTER TABLE vertex_gftd_identity ADD COLUMN cid_version       BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity ADD COLUMN multicodec        VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity ADD COLUMN multihash_code    VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity ADD COLUMN multibase_prefix  VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity ADD COLUMN genesis_op_cid    VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity ADD COLUMN root_did          VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity ADD COLUMN path_segment      VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gftd_identity_root
    ON vertex_gftd_identity(root_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gftd_identity_genesis_cid
    ON vertex_gftd_identity(genesis_op_cid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── New table: edge_gftd_path_child (parent → child path lineage) ─────

  await sql`CREATE TABLE IF NOT EXISTS edge_gftd_path_child (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,    -- parent did:gftd
    dst_vid         VARCHAR,    -- child  did:gftd
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    segment         VARCHAR,
    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_gftd_path_child_dst
    ON edge_gftd_path_child(dst_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_gftd_path_child_src
    ON edge_gftd_path_child(src_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── New table: vertex_gftd_op_log (signed op history per DID) ─────────

  await sql`CREATE TABLE IF NOT EXISTS vertex_gftd_op_log (
    vertex_id       VARCHAR PRIMARY KEY,    -- {did}:{seq}
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    did             VARCHAR,    -- did:gftd
    op_seq          BIGINT,     -- 0 = genesis, 1+ = updates
    op_type         VARCHAR,    -- 'create' | 'update' | 'deactivate'
    op_cid          VARCHAR,    -- CIDv1 of this op CBOR
    prev_cid        VARCHAR,    -- CIDv1 of previous op (NULL at genesis)
    op_cbor_hex     VARCHAR,    -- canonical DAG-CBOR encoded op (hex)
    sig             VARCHAR,    -- signature over op_cid (NULL at genesis)
    sig_kid         VARCHAR,    -- verificationMethod id used to sign
    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gftd_op_log_did_seq
    ON vertex_gftd_op_log(did, op_seq)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── MV: latest op per DID (resolver fast path) ────────────────────────

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gftd_op_log_head AS
    SELECT did, MAX(op_seq) AS head_seq
    FROM vertex_gftd_op_log
    GROUP BY did`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── MV: path tree depth distribution (telemetry) ──────────────────────
  // (depth column added by 20260417150000_gftd_did_recursive_tree)

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gftd_path_depth_dist AS
    SELECT depth, COUNT(*) AS dids
    FROM vertex_gftd_identity
    WHERE depth IS NOT NULL
    GROUP BY depth`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gftd_path_depth_dist`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gftd_op_log_head`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_gftd_op_log_did_seq`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gftd_op_log`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_edge_gftd_path_child_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_gftd_path_child_dst`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gftd_path_child`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_gftd_identity_genesis_cid`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_gftd_identity_root`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_gftd_identity DROP COLUMN path_segment`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity DROP COLUMN root_did`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity DROP COLUMN genesis_op_cid`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity DROP COLUMN multibase_prefix`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity DROP COLUMN multihash_code`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity DROP COLUMN multicodec`.execute(db);
  await sql`ALTER TABLE vertex_gftd_identity DROP COLUMN cid_version`.execute(db);
  await sql`FLUSH`.execute(db);
}
