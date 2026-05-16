import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_projector_flow_* + edge_projector_flow_* — Kyber BPMN Projector
 * extension for Path F agentInfer-backed flow execution (Design A).
 *
 * Per ADR-0036 (Worker-direct Hyperdrive Persistence) and the Design A
 * decision (2026-04-21), projector flow state moves off AT records
 * (ai.gftd.projector.flow / .branch / .reflection) and lives in
 * RisingWave directly. Each app writes via
 *   createKyselyDb(env.HYPERDRIVE).insertInto("vertex_projector_flow_*")
 * from its own Worker; BPMN Projector (kyber-projector.gftd.ai) keeps
 * catalog + RACI gate + OCEL audit responsibility, not storage.
 *
 * Schema:
 *   vertex_projector_flow        DAG metadata (1 row / definition)
 *   vertex_projector_flow_node   node config (agent.reasoning / script / approval / http)
 *   edge_projector_flow_edge     DAG transitions (GraphAr-native edge table)
 *   vertex_projector_flow_run    execution instance (1 row / run)
 *   vertex_projector_flow_step   step log (append-only; per-step LLM usage)
 *
 * Pilot actor: projector. Other actors (mangaka, briefing, ...) replicate
 * with vertex_<actor>_flow_* namespaced to their own domain when they
 * opt in.
 *
 * Migration entry: deps.toml [[migrations]] projector-flow-to-hyperdrive.
 * Depends on: worker-direct-hyperdrive-per-actor.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // DAG metadata — 1 row per flow definition.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_projector_flow (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      flow_key VARCHAR, name VARCHAR, description VARCHAR, version BIGINT,
      bpmn_task_id VARCHAR, bpmn_process_id VARCHAR,
      entry_node VARCHAR, status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Node definitions (Camunda 8.9 agentic BPMN-aligned, Phase 3 re-spec).
  //
  // node_type enum:
  //   agentLoop — serviceTask + AI Agent connector container. Runs the
  //               LLM feedback loop, selects tool nodes (by
  //               flow_vertex_id) based on its own reasoning.
  //   tool      — activity inside the ad-hoc sub-process. The LLM can
  //               invoke it. If bpmn_task_id is set, this is a
  //               reference to a Kyber BPMN_CATALOG entry (ADR-0025),
  //               and the catalog entry's ocelEventType is used for
  //               the audit event.
  //   approval  — userTask + escalation event (Camunda pattern #3).
  //               Suspends the run for human review.
  //   script    — scriptTask / businessRuleTask (Camunda pattern #4).
  //               Deterministic guardrail / pre/post-processing.
  //   http      — serviceTask. Outbound request via sdk.Send. Never
  //               selected by the LLM; only by deterministic edges.
  //
  // LLM-specific knobs (model_id / temperature_bps / max_tokens /
  // prompt_template / tools_json) are promoted columns so the runner
  // can read them without JSON parse. They are meaningful on
  // agentLoop rows; ignored elsewhere.
  // temperature_bps = temperature × 10000 (fixed-point; RW has no REAL
  // default in our convention).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_projector_flow_node (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      flow_vertex_id VARCHAR, node_key VARCHAR, node_type VARCHAR,
      model_id VARCHAR, temperature_bps BIGINT, max_tokens BIGINT,
      prompt_template VARCHAR, tools_json VARCHAR, config_json VARCHAR,
      retry_max BIGINT, timeout_ms BIGINT,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Deterministic DAG transitions. edge_kind ∈ {sequence, conditional,
  // interrupt, fallback}. condition_expr is an opaque string the
  // runner evaluates against vars_json on conditional edges; priority
  // breaks ties when multiple edges match.
  //
  // Edges are used ONLY for deterministic sequencing between nodes
  // (script → agentLoop → approval → script etc.). The LLM's tool
  // selection inside an agentLoop does NOT use edges — tools are
  // discovered by (flow_vertex_id, node_type='tool') and the LLM picks
  // based on its own reasoning. This matches Camunda 8.9's ad-hoc
  // sub-process pattern where tool invocation is not a pre-defined
  // sequence flow.
  await sql`
    CREATE TABLE IF NOT EXISTS edge_projector_flow_edge (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      flow_vertex_id VARCHAR, condition_expr VARCHAR, priority BIGINT,
      edge_kind VARCHAR,
      created_at VARCHAR, org_id VARCHAR
    )
  `.execute(db);

  // Run instance = 1 row per execution. status ∈ {pending, running,
  // suspended, done, failed}. runner_kind ∈ {cron, durable_object,
  // on_commit} — picked per-app (see Design A runner matrix).
  // parent_run_id carries ToT fork lineage (replaces the deleted
  // ai.gftd.projector.branch AT record).
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_projector_flow_run (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      flow_vertex_id VARCHAR, parent_run_id VARCHAR,
      status VARCHAR, current_node VARCHAR, vars_json VARCHAR,
      convo_id VARCHAR, project_id VARCHAR,
      started_at VARCHAR, resume_at VARCHAR, finished_at VARCHAR,
      error_code VARCHAR, error_message VARCHAR,
      runner_kind VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Append-only step log. Per-step LLM token accounting lives here so
  // we never have to retro-compute from the run row. ocel_event_id is
  // the rkey of the ai.gftd.apps.apqc.apqcEvent record emitted by the
  // runner for this step (see Kyber projector emitOcel contract,
  // ADR-0025). bpmn_activity_id optionally references a Kyber
  // BPMN_CATALOG taskId when the step invoked a catalog entry as a
  // tool; in that case the ocelEventType matches the catalog entry's
  // specific event name (e.g. journal.posted), not the generic
  // tool.called. Phase-3 OCEL event naming convention:
  //   flow.started / flow.completed / flow.failed
  //   agent.iteration.start / agent.iteration.end
  //   tool.called / tool.completed
  //   agent.guardrail.denied / agent.escalated / agent.human.resumed
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_projector_flow_step (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      run_vertex_id VARCHAR, node_key VARCHAR, node_type VARCHAR,
      attempt BIGINT, status VARCHAR,
      input_json VARCHAR, output_json VARCHAR,
      model_id VARCHAR, prompt_tokens BIGINT, completion_tokens BIGINT, total_tokens BIGINT,
      latency_ms BIGINT,
      ocel_event_id VARCHAR, bpmn_activity_id VARCHAR,
      started_at VARCHAR, finished_at VARCHAR,
      error_code VARCHAR, error_message VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Hot-path indexes for the cron runner (R1) — it polls for runs
  // whose resume_at has fired and for pending steps within a run.
  await sql`CREATE INDEX IF NOT EXISTS idx_projector_flow_run_resume
            ON vertex_projector_flow_run (status, resume_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_projector_flow_run_flow
            ON vertex_projector_flow_run (flow_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_projector_flow_step_run
            ON vertex_projector_flow_step (run_vertex_id, _seq)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_projector_flow_node_flow
            ON vertex_projector_flow_node (flow_vertex_id, node_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_projector_flow_edge_flow
            ON edge_projector_flow_edge (flow_vertex_id, src_vid)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_projector_flow_edge_flow`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_projector_flow_node_flow`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_projector_flow_step_run`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_projector_flow_run_flow`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_projector_flow_run_resume`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_projector_flow_step`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_projector_flow_run`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_projector_flow_edge`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_projector_flow_node`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_projector_flow`.execute(db);
}
