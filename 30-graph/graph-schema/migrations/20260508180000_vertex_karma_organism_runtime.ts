import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier: tier B  (curated runtime state).

/**
 * karma.gftd.ai — artificial organism ecosystem runtime schema (Phase K2).
 *
 * Backs the resident LangGraph organism agents — long-running daemons
 * that "live" inside one of three substrates:
 *
 *   - K8s pod   (Vultr VKE mitama-karma-pool)         — default, CPU-bound
 *   - RunPod    (`vyp99t9px7h4dl` 6000 Ada)           — GPU-heavy reasoning
 *   - Ethereum  (ERC-4337 smart wallet)               — on-chain residency
 *
 * Each organism DID has one `vertex_organism_runtime` row pinning its
 * substrate + endpoint + resource profile. The state machine
 * checkpoint is in `vertex_organism_checkpoint` (LangGraph thread state
 * serialized via langgraph-checkpoint MemorySaver / RisingWave saver).
 *
 * Cohort genesis tracking lives in `vertex_organism_cohort` (extends
 * existing ADR-0026 cohort actor with karma-specific generation /
 * lineage / fitness columns).
 *
 * Tables (3 vertex + 3 streaming MV):
 *   vertex_organism_runtime       per-DID substrate + endpoint binding
 *   vertex_organism_checkpoint    LangGraph thread state per (did, thread_id)
 *   vertex_organism_cohort        per-cohort generation + fitness
 *   mv_organism_runtime_alive     active organisms by substrate
 *   mv_organism_cohort_growth     cohort generation + fission cadence
 *   mv_organism_resource_pressure runtime cost / token / GPU usage
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_organism_runtime (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      did varchar NOT NULL,
      substrate varchar NOT NULL,
      pod_name varchar,
      runpod_endpoint_id varchar,
      runpod_pod_id varchar,
      eth_wallet_address varchar,
      eth_chain varchar,
      cpu_request_m bigint,
      memory_request_mi bigint,
      gpu_count int,
      heartbeat_at varchar,
      heartbeat_at_ms bigint,
      tick_count bigint,
      observation_count bigint,
      cost_usd_to_date double precision,
      llm_tokens_to_date bigint,
      status varchar NOT NULL,
      last_error varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_organism_checkpoint (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      did varchar NOT NULL,
      thread_id varchar NOT NULL,
      checkpoint_id varchar NOT NULL,
      parent_checkpoint_id varchar,
      langgraph_node varchar NOT NULL,
      state_json varchar,
      state_byte_size bigint,
      saved_at varchar NOT NULL,
      saved_at_ms bigint NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_organism_cohort (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      cohort_id varchar NOT NULL,
      cohort_did varchar NOT NULL,
      generation int NOT NULL,
      parent_cohort_id varchar,
      member_did_csv varchar,
      member_count int NOT NULL,
      genesis_trigger varchar NOT NULL,
      fitness_score double precision,
      posterior double precision,
      genesis_at varchar NOT NULL,
      genesis_at_ms bigint NOT NULL,
      fission_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // Indexes
  await sql`CREATE INDEX IF NOT EXISTS idx_org_runtime_did ON vertex_organism_runtime (did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_org_runtime_status ON vertex_organism_runtime (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_org_runtime_substrate ON vertex_organism_runtime (substrate)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_org_ckpt_did_thread ON vertex_organism_checkpoint (did, thread_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_org_ckpt_saved ON vertex_organism_checkpoint (saved_at_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_org_cohort_did ON vertex_organism_cohort (cohort_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_org_cohort_gen ON vertex_organism_cohort (generation)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_org_cohort_status ON vertex_organism_cohort (status)`.execute(db);

  // Active organisms by substrate.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_organism_runtime_alive AS
    SELECT
      substrate,
      count(*) AS alive_count,
      sum(observation_count) AS total_observations,
      sum(cost_usd_to_date) AS total_cost_usd,
      sum(llm_tokens_to_date) AS total_llm_tokens
    FROM vertex_organism_runtime
    WHERE status = 'alive'
    GROUP BY substrate
  `.execute(db);

  // Cohort growth — generation aggregate, low cardinality.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_organism_cohort_growth AS
    SELECT
      generation,
      count(*) AS cohort_count,
      sum(member_count) AS total_members,
      avg(fitness_score) AS avg_fitness,
      avg(posterior) AS avg_posterior
    FROM vertex_organism_cohort
    WHERE status IN ('active', 'fissioned')
    GROUP BY generation
  `.execute(db);

  // Resource pressure — bounded by N substrates × active organisms.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_organism_resource_pressure AS
    SELECT
      did,
      substrate,
      cpu_request_m,
      memory_request_mi,
      gpu_count,
      tick_count,
      cost_usd_to_date,
      llm_tokens_to_date,
      heartbeat_at_ms
    FROM vertex_organism_runtime
    WHERE status = 'alive'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organism_resource_pressure`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organism_cohort_growth`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organism_runtime_alive`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_organism_cohort`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_organism_checkpoint`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_organism_runtime`.execute(db);
}
