import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * ADR-0039 Phase A/B — Repository-in-Graph base schema.
 *
 * 4 vertex + 6 edge tables for the git object model:
 *   vertex_repository_blob    content-addressed file (sha256)
 *   vertex_repository_tree    directory snapshot
 *   vertex_repository_commit  commit object (signed ES256)
 *   vertex_repository_ref     branch / tag / HEAD
 *
 *   edge_repository_parent        commit -> commit (merge = N parents)
 *   edge_repository_tree          commit -> tree (root)
 *   edge_repository_entry         tree -> blob|tree (with path + mode)
 *   edge_repository_authored_by   commit -> vertex_actor (author DID)
 *   edge_repository_ref_points    ref -> commit (ONLY mutable edge)
 *   edge_repository_ref_owner     ref -> vertex_actor (repository identity)
 *
 * Repository == Actor DID (ADR-0039 §2). vertex_actor is reused as the
 * repository entity; path-based DID hierarchy (ADR-0019) gives sub-repo tree
 * via existing edge_path_child.
 *
 * Naming: vertex_repository_* (full word, chosen over vertex_repo_* which
 * is already taken by PDS commit log in vertex_repo_commit / _block).
 *
 * Served by: repository.etzhayyim.com (60-apps/etzhayyim-project-repository).
 * Lexicons: 00-contracts/lexicons/com/etzhayyim/repository/*.json (13 files).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ─── vertex_repository_blob ──────────────────────────────────────────
  // sha256-keyed content-addressed file. >16KB tiered to R2.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_repository_blob (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      hash VARCHAR,
      size_bytes BIGINT,
      tier VARCHAR,
      inline_text VARCHAR,
      bytes_ref VARCHAR,
      mime_type VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // ─── vertex_repository_tree ──────────────────────────────────────────
  // Directory snapshot. tree_hash = sha256(canonical-sorted entry list).
  // Entries are in edge_repository_entry.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_repository_tree (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      tree_hash VARCHAR,
      entry_count BIGINT,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // ─── vertex_repository_commit ───────────────────────────────────────
  // Signed commit object. commit_hash input does NOT include signature_es256
  // so re-signing after key rotation does not change the hash.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_repository_commit (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      commit_hash VARCHAR,
      tree_hash VARCHAR,
      author_did VARCHAR,
      committer_did VARCHAR,
      message VARCHAR,
      author_timestamp VARCHAR,
      committer_timestamp VARCHAR,
      signature_es256 VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // ─── vertex_repository_ref ──────────────────────────────────────────
  // branch / tag / head. head_commit_hash snapshots the current tip;
  // authoritative pointer is edge_repository_ref_points (mutable).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_repository_ref (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      ref_name VARCHAR,
      kind VARCHAR,
      head_commit_hash VARCHAR,
      description VARCHAR,
      created_at VARCHAR, updated_at VARCHAR,
      org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // ─── edge_repository_parent ─────────────────────────────────────────
  // commit -> commit. parent_ordinal preserves merge parent order (0 = first).
  await sql`
    CREATE TABLE IF NOT EXISTS edge_repository_parent (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      parent_ordinal BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  // ─── edge_repository_tree ───────────────────────────────────────────
  // commit -> tree (root tree of the commit).
  await sql`
    CREATE TABLE IF NOT EXISTS edge_repository_tree (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  // ─── edge_repository_entry ──────────────────────────────────────────
  // tree -> blob|tree. mode in {blob, exec, tree}.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_repository_entry (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      path VARCHAR,
      mode VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  // ─── edge_repository_authored_by ────────────────────────────────────
  // commit -> vertex_actor (author DID).
  await sql`
    CREATE TABLE IF NOT EXISTS edge_repository_authored_by (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      role VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  // ─── edge_repository_ref_points ─────────────────────────────────────
  // ref -> commit. THE ONLY MUTABLE EDGE in ADR-0039 (rewritten on updateRef).
  // update_kind ∈ {created, fastForward, rolledBack, forcePushed}.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_repository_ref_points (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      update_kind VARCHAR,
      reason VARCHAR,
      pushed_at VARCHAR,
      committer_did VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  // ─── edge_repository_ref_owner ──────────────────────────────────────
  // ref -> vertex_actor (owning DID). Immutable at ref creation.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_repository_ref_owner (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_repository_ref_owner`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_repository_ref_points`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_repository_authored_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_repository_entry`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_repository_tree`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_repository_parent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_repository_ref`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_repository_commit`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_repository_tree`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_repository_blob`.execute(db);
}
