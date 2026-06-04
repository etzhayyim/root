import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * ADR-0029 — did:etzhayyim Method Specification (CIDv1 + path-form).
 *
 * Extends `vertex_etzhayyim_identity` with CIDv1 metadata columns. The
 * `parent_did` and `depth` columns were already added by an earlier
 * out-of-band migration (`20260417150000_etzhayyim_did_recursive_tree`); this
 * migration is purely additive on top of that.
 *
 * Reference:
 *   - 90-docs/adr/0029-did-etzhayyim-method-specification.md
 *   - 10-protocol/did-etzhayyim/  (TypeScript reference impl)
 *
 * Columns added to vertex_etzhayyim_identity (CIDv1 specific only):
 *   cid_version       BIGINT   -- 1 (CIDv1)
 *   multicodec        VARCHAR  -- 'raw' (0x55)
 *   multihash_code    VARCHAR  -- 'sha2-256' (0x12) — future: 'blake3', etc.
 *   multibase_prefix  VARCHAR  -- 'b' (base32 lowercase, IPFS canonical)
 *   genesis_op_cid    VARCHAR  -- CID of the genesis op CBOR (= last segment of did, for verify)
 *   root_did          VARCHAR  -- did:etzhayyim of the root (depth=0 ancestor)
 *   path_segment      VARCHAR  -- UTF-8 segment used in genesis op (NULL for root)
 *
 * Already present (do NOT re-ADD):
 *   parent_did        VARCHAR  -- from 20260417150000_etzhayyim_did_recursive_tree
 *   depth             BIGINT   -- from 20260417150000_etzhayyim_did_recursive_tree
 *
 * New tables:
 *   edge_etzhayyim_path_child  parent did:etzhayyim → child did:etzhayyim, with segment label
 *   vertex_etzhayyim_op_log    signed op history per DID
 */

export async function up(db: Kysely<any>): Promise<void> {

  // ── ALTER vertex_etzhayyim_identity: CIDv1 metadata only ───────────────────
  // (parent_did + depth already added by 20260417150000_etzhayyim_did_recursive_tree)

  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN cid_version       BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN multicodec        VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN multihash_code    VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN multibase_prefix  VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN genesis_op_cid    VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_did          VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity ADD COLUMN path_segment      VARCHAR`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_root
    ON vertex_etzhayyim_identity(root_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_genesis_cid
    ON vertex_etzhayyim_identity(genesis_op_cid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── New table: edge_etzhayyim_path_child (parent → child path lineage) ─────

  await sql`CREATE TABLE IF NOT EXISTS edge_etzhayyim_path_child (
    edge_id         VARCHAR PRIMARY KEY,
    src_vid         VARCHAR,    -- parent did:etzhayyim
    dst_vid         VARCHAR,    -- child  did:etzhayyim
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    segment         VARCHAR,
    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_path_child_dst
    ON edge_etzhayyim_path_child(dst_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_path_child_src
    ON edge_etzhayyim_path_child(src_vid)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── New table: vertex_etzhayyim_op_log (signed op history per DID) ─────────

  await sql`CREATE TABLE IF NOT EXISTS vertex_etzhayyim_op_log (
    vertex_id       VARCHAR PRIMARY KEY,    -- {did}:{seq}
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    did             VARCHAR,    -- did:etzhayyim
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

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_op_log_did_seq
    ON vertex_etzhayyim_op_log(did, op_seq)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── MV: latest op per DID (resolver fast path) ────────────────────────

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_op_log_head AS
    SELECT did, MAX(op_seq) AS head_seq
    FROM vertex_etzhayyim_op_log
    GROUP BY did`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── MV: path tree depth distribution (telemetry) ──────────────────────
  // (depth column added by 20260417150000_etzhayyim_did_recursive_tree)

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_path_depth_dist AS
    SELECT depth, COUNT(*) AS dids
    FROM vertex_etzhayyim_identity
    WHERE depth IS NOT NULL
    GROUP BY depth`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_path_depth_dist`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_op_log_head`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_op_log_did_seq`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_op_log`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_edge_etzhayyim_path_child_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_etzhayyim_path_child_dst`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_etzhayyim_path_child`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_genesis_cid`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_root`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN path_segment`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN root_did`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN genesis_op_cid`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN multibase_prefix`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN multihash_code`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN multicodec`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_identity DROP COLUMN cid_version`.execute(db);
  await sql`FLUSH`.execute(db);
}
