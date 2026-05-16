import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_id VARCHAR,
      owner_did VARCHAR,
      label VARCHAR,
      status VARCHAR,
      stream_id VARCHAR,
      agent_did VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_stream`)} ON ${sql.table(table)} (stream_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_agent`)} ON ${sql.table(table)} (agent_did)`.execute(db);
}

async function baseEdge(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Layer 1: kobo (酵母) — individual agents ──────────────────────────────

  await baseVertex(db, "vertex_kobo_agent");
  await sql`ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS parent_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS role VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS eta DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_kobo_agent ADD COLUMN IF NOT EXISTS stress_score DOUBLE PRECISION`.execute(db);

  // prion = heritable non-volatile state transferred during budding
  await baseVertex(db, "vertex_kobo_prion");
  await sql`ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS pattern_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS heritable BOOLEAN`.execute(db);
  await sql`ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS malignant_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_kobo_prion ADD COLUMN IF NOT EXISTS content TEXT`.execute(db);

  // budding edge: parent → child with prion transfer record
  await baseEdge(db, "edge_kobo_budding");
  await sql`ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS parent_did VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS child_did VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS budded_at VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kobo_budding ADD COLUMN IF NOT EXISTS prion_count BIGINT`.execute(db);

  // ── Layer 2: kabi (カビ) — mycelium network ──────────────────────────────

  // hypha = directed nutrient flow channel between agents
  await baseEdge(db, "edge_kabi_hypha");
  await sql`ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS src_agent_did VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS dst_agent_did VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS eta DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS flow DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE edge_kabi_hypha ADD COLUMN IF NOT EXISTS pruned_at VARCHAR`.execute(db);

  // anastomosis = network merge compatibility check result
  await baseEdge(db, "edge_kabi_anastomosis");
  await sql`ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS network_a_did VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS network_b_did VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS compatibility_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS result VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_kabi_anastomosis ADD COLUMN IF NOT EXISTS reason TEXT`.execute(db);

  // network aggregate vertex (one per kabi network cluster)
  await baseVertex(db, "vertex_kabi_network");
  await sql`ALTER TABLE vertex_kabi_network ADD COLUMN IF NOT EXISTS root_agent_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kabi_network ADD COLUMN IF NOT EXISTS hypha_count BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_kabi_network ADD COLUMN IF NOT EXISTS total_flow DOUBLE PRECISION`.execute(db);

  // ── Layer 3: kinoko (きのこ) — fruiting body / PoNF consensus ────────────

  await baseVertex(db, "vertex_kinoko_block");
  await sql`ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS prev_block_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS block_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS total_flow DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS participant_count BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS eta_min_used DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_kinoko_block ADD COLUMN IF NOT EXISTS block_status VARCHAR`.execute(db);

  // ── Auxiliary: houshi (胞子) — sporulation / stress escape ───────────────

  await baseVertex(db, "vertex_houshi_spore");
  await sql`ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS origin_agent_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS blob_cbor TEXT`.execute(db);
  await sql`ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS revival_key_hint VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS quorum_n BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_houshi_spore ADD COLUMN IF NOT EXISTS germinated_at VARCHAR`.execute(db);

  // custody edge: spore → custodian agent
  await baseEdge(db, "edge_houshi_custody");
  await sql`ALTER TABLE edge_houshi_custody ADD COLUMN IF NOT EXISTS custodian_did VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_houshi_custody ADD COLUMN IF NOT EXISTS custody_confirmed BOOLEAN`.execute(db);

  // ── Auxiliary: hakkou (発酵) — fermentation pipeline ────────────────────

  await baseVertex(db, "vertex_hakkou_ferment");
  await sql`ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS input_kind VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS input_ref TEXT`.execute(db);
  await sql`ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS output_vertex_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS output_kind VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS ethanol_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_hakkou_ferment ADD COLUMN IF NOT EXISTS co2_audit_ref TEXT`.execute(db);

  // ── Indexes ──────────────────────────────────────────────────────────────

  await sql`CREATE INDEX IF NOT EXISTS idx_kobo_agent_parent ON vertex_kobo_agent (parent_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kobo_agent_eta ON vertex_kobo_agent (eta, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kobo_prion_pattern ON vertex_kobo_prion (pattern_hash, heritable)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kabi_hypha_flow ON edge_kabi_hypha (src_agent_did, dst_agent_did, pruned_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kabi_anastomosis_result ON edge_kabi_anastomosis (result, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kinoko_block_chain ON vertex_kinoko_block (prev_block_id, block_status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_houshi_spore_origin ON vertex_houshi_spore (origin_agent_did, germinated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_hakkou_ferment_input ON vertex_hakkou_ferment (agent_did, input_kind, created_at)`.execute(db);

  // ── Streaming Materialized Views ─────────────────────────────────────────

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kabi_nutrient_flow`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_kabi_nutrient_flow AS
    SELECT
      src_agent_did,
      dst_agent_did,
      COUNT(*)::BIGINT AS hypha_count,
      SUM(flow) AS total_flow,
      AVG(eta) AS avg_eta
    FROM edge_kabi_hypha
    WHERE pruned_at IS NULL
    GROUP BY src_agent_did, dst_agent_did
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kabi_eta_gradient`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_kabi_eta_gradient AS
    SELECT
      dst_agent_did AS agent_did,
      COUNT(*)::BIGINT AS inbound_count,
      SUM(flow) AS inbound_flow,
      AVG(eta) AS inbound_eta_avg,
      MAX(eta) AS inbound_eta_max
    FROM edge_kabi_hypha
    WHERE pruned_at IS NULL
    GROUP BY dst_agent_did
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kabi_eta_gradient`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kabi_nutrient_flow`.execute(db);
  for (const table of [
    "vertex_hakkou_ferment",
    "edge_houshi_custody",
    "vertex_houshi_spore",
    "vertex_kinoko_block",
    "vertex_kabi_network",
    "edge_kabi_anastomosis",
    "edge_kabi_hypha",
    "edge_kobo_budding",
    "vertex_kobo_prion",
    "vertex_kobo_agent",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
