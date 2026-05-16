import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Generic decision context graph for agents, conversations, processes, and
 * infrastructure.
 *
 * This is intentionally broader than infra topology:
 * - capability: what a subject can do
 * - constraint: what limits or prohibits a subject/action
 * - dependency: what must exist or happen first
 *
 * Direction contract:
 * - edge_context_depends_on.src_vid depends on edge_context_depends_on.dst_vid
 * - edge_context_constrained_by.src_vid is constrained by dst_vid
 * - edge_context_has_capability.src_vid has capability dst_vid
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_context_subject (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      subject_ref VARCHAR NOT NULL,
      subject_kind VARCHAR NOT NULL,
      scope_kind VARCHAR NOT NULL,
      display_name VARCHAR,
      description VARCHAR,
      status VARCHAR DEFAULT 'active',
      tags_json VARCHAR,
      payload_json VARCHAR,
      source_ref VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_context_capability (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      capability_id VARCHAR NOT NULL,
      subject_ref VARCHAR NOT NULL,
      subject_kind VARCHAR NOT NULL,
      scope_kind VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      description VARCHAR,
      capability_kind VARCHAR,
      capability_level VARCHAR,
      status VARCHAR DEFAULT 'active',
      confidence DOUBLE PRECISION,
      evidence_ref VARCHAR,
      tags_json VARCHAR,
      payload_json VARCHAR,
      source_ref VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_context_constraint (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      constraint_id VARCHAR NOT NULL,
      subject_ref VARCHAR NOT NULL,
      subject_kind VARCHAR NOT NULL,
      scope_kind VARCHAR NOT NULL,
      title VARCHAR NOT NULL,
      rule VARCHAR NOT NULL,
      constraint_kind VARCHAR,
      severity VARCHAR DEFAULT 'medium',
      status VARCHAR DEFAULT 'active',
      hard BOOLEAN DEFAULT false,
      permitted BOOLEAN,
      enforcement VARCHAR,
      rationale VARCHAR,
      evidence_ref VARCHAR,
      tags_json VARCHAR,
      payload_json VARCHAR,
      source_ref VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_context_dependency (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      dependency_id VARCHAR NOT NULL,
      subject_ref VARCHAR NOT NULL,
      subject_kind VARCHAR NOT NULL,
      prerequisite_ref VARCHAR NOT NULL,
      prerequisite_kind VARCHAR,
      scope_kind VARCHAR NOT NULL,
      dependency_kind VARCHAR,
      status VARCHAR DEFAULT 'active',
      required BOOLEAN DEFAULT true,
      strength DOUBLE PRECISION,
      rationale VARCHAR,
      evidence_ref VARCHAR,
      tags_json VARCHAR,
      payload_json VARCHAR,
      source_ref VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_context_has_capability (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation_kind VARCHAR DEFAULT 'has_capability',
      status VARCHAR DEFAULT 'active',
      evidence_ref VARCHAR,
      payload_json VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_context_constrained_by (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation_kind VARCHAR DEFAULT 'constrained_by',
      status VARCHAR DEFAULT 'active',
      evidence_ref VARCHAR,
      payload_json VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_context_depends_on (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      relation_kind VARCHAR DEFAULT 'depends_on',
      status VARCHAR DEFAULT 'active',
      evidence_ref VARCHAR,
      payload_json VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_context_subject_ref ON vertex_context_subject (subject_ref)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_context_subject_scope ON vertex_context_subject (scope_kind, subject_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_context_capability_subject ON vertex_context_capability (subject_ref, scope_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_context_capability_id ON vertex_context_capability (capability_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_context_constraint_subject ON vertex_context_constraint (subject_ref, scope_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_context_constraint_severity ON vertex_context_constraint (severity, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_context_dependency_subject ON vertex_context_dependency (subject_ref, scope_kind)`.execute(db);




  await sql`
    INSERT INTO vertex_context_subject (
      vertex_id, created_date, owner_did, subject_ref, subject_kind, scope_kind,
      display_name, description, status, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'context-subject:oka-training',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'oka-training',
      'model_training_policy',
      'training',
      'Oka training precision policy',
      'Generic decision context for Oka A40 BF16 fallback and L40S FP8 promotion.',
      'active',
      '["oka","training","gpu","runpod","fp8","bf16"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_subject WHERE vertex_id = 'context-subject:oka-training'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_context_capability (
      vertex_id, created_date, owner_did, capability_id, subject_ref, subject_kind,
      scope_kind, name, description, capability_kind, capability_level, status,
      confidence, evidence_ref, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'capability:oka-training:a40-bf16-fallback',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'capability:oka-training:a40-bf16-fallback',
      'oka-training',
      'model_training_policy',
      'training',
      'A40 BF16 fallback training',
      'A40 supports BF16 Tensor Core training and is the current fallback path for Oka smoke runs.',
      'gpu_training_precision',
      'available',
      'active',
      0.95,
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '["oka","training","gpu","runpod","a40","bf16"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_capability WHERE vertex_id = 'capability:oka-training:a40-bf16-fallback'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_context_capability (
      vertex_id, created_date, owner_did, capability_id, subject_ref, subject_kind,
      scope_kind, name, description, capability_kind, capability_level, status,
      confidence, evidence_ref, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'capability:oka-training:l40s-fp8-training',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'capability:oka-training:l40s-fp8-training',
      'oka-training',
      'model_training_policy',
      'training',
      'L40S FP8 training',
      'L40S has FP8 Tensor Core capability and can be used for Transformer Engine FP8 training when capacity and implementation are available.',
      'gpu_training_precision',
      'capacity-dependent',
      'pending',
      0.9,
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '["oka","training","gpu","runpod","l40s","fp8","transformer-engine"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_capability WHERE vertex_id = 'capability:oka-training:l40s-fp8-training'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_context_subject (
      vertex_id, created_date, owner_did, subject_ref, subject_kind, scope_kind,
      display_name, description, status, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'context-subject:oka-training:a40-fp8',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'oka-training:a40-fp8',
      'training_action',
      'training',
      'Oka A40 FP8 training action',
      'Decision subject for whether Oka FP8 training may run on A40.',
      'active',
      '["oka","training","gpu","runpod","a40","fp8"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_subject WHERE vertex_id = 'context-subject:oka-training:a40-fp8'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_context_subject (
      vertex_id, created_date, owner_did, subject_ref, subject_kind, scope_kind,
      display_name, description, status, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'context-subject:oka-training:l40s-fp8',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'oka-training:l40s-fp8',
      'training_action',
      'training',
      'Oka L40S FP8 training action',
      'Decision subject for promoting Oka training from BF16 fallback to L40S FP8.',
      'active',
      '["oka","training","gpu","runpod","l40s","fp8","transformer-engine"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_subject WHERE vertex_id = 'context-subject:oka-training:l40s-fp8'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_context_constraint (
      vertex_id, created_date, owner_did, constraint_id, subject_ref, subject_kind,
      scope_kind, title, rule, constraint_kind, severity, status, hard, permitted,
      enforcement, rationale, evidence_ref, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'constraint:oka-training:a40-no-fp8-training',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'constraint:oka-training:a40-no-fp8-training',
      'oka-training:a40-fp8',
      'training_action',
      'training',
      'A40 cannot be used for FP8 training',
      'Do not schedule Oka FP8 Tensor Core training on A40. Use BF16 fallback on A40.',
      'hardware_precision_limit',
      'high',
      'active',
      true,
      false,
      'scheduler_gate',
      'A40 is Ampere with third-generation Tensor Cores and does not provide FP8 Tensor Core training support.',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '["oka","training","gpu","runpod","a40","fp8","bf16"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_constraint WHERE vertex_id = 'constraint:oka-training:a40-no-fp8-training'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_context_constraint (
      vertex_id, created_date, owner_did, constraint_id, subject_ref, subject_kind,
      scope_kind, title, rule, constraint_kind, severity, status, hard, permitted,
      enforcement, rationale, evidence_ref, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'constraint:oka-training:fp8-requires-bf16-fallback',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'constraint:oka-training:fp8-requires-bf16-fallback',
      'oka-training:l40s-fp8',
      'training_action',
      'training',
      'FP8 training requires BF16 or FP32 fallback islands',
      'Keep embedding head, loss, norm, optimizer state, checkpoint metadata, and unstable layers in BF16 or FP32 when enabling FP8.',
      'precision_stability_gate',
      'high',
      'active',
      true,
      true,
      'implementation_gate',
      'FP8 training requires scale/amax management and layer-wise fallback for stability.',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '["oka","training","fp8","bf16","stability","transformer-engine"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_constraint WHERE vertex_id = 'constraint:oka-training:fp8-requires-bf16-fallback'
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_context_dependency (
      vertex_id, created_date, owner_did, dependency_id, subject_ref, subject_kind,
      prerequisite_ref, prerequisite_kind, scope_kind, dependency_kind, status,
      required, strength, rationale, evidence_ref, tags_json, source_ref, created_at, updated_at
    )
    SELECT
      'dependency:oka-training:l40s-fp8-capacity',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'dependency:oka-training:l40s-fp8-capacity',
      'oka-training:l40s-fp8',
      'training_action',
      'capability:oka-training:l40s-fp8-training',
      'context_capability',
      'training',
      'capacity_and_implementation',
      'active',
      true,
      0.9,
      'Oka L40S FP8 promotion depends on L40S capacity plus Transformer Engine FP8 implementation and smoke comparison gates.',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '["oka","training","l40s","fp8","runpod","transformer-engine"]',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md',
      '2026-05-09T00:00:00Z',
      '2026-05-09T00:00:00Z'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_context_dependency WHERE vertex_id = 'dependency:oka-training:l40s-fp8-capacity'
    )
  `.execute(db);

  await sql`
    INSERT INTO edge_context_has_capability (
      edge_id, src_vid, dst_vid, created_date, owner_did, relation_kind, status, evidence_ref
    )
    SELECT
      'edge:capability:oka-training:a40-bf16-fallback',
      'oka-training',
      'capability:oka-training:a40-bf16-fallback',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'has_capability',
      'active',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md'
    WHERE NOT EXISTS (
      SELECT 1 FROM edge_context_has_capability WHERE edge_id = 'edge:capability:oka-training:a40-bf16-fallback'
    )
  `.execute(db);

  await sql`
    INSERT INTO edge_context_has_capability (
      edge_id, src_vid, dst_vid, created_date, owner_did, relation_kind, status, evidence_ref
    )
    SELECT
      'edge:capability:oka-training:l40s-fp8-training',
      'oka-training',
      'capability:oka-training:l40s-fp8-training',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'has_capability',
      'pending',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md'
    WHERE NOT EXISTS (
      SELECT 1 FROM edge_context_has_capability WHERE edge_id = 'edge:capability:oka-training:l40s-fp8-training'
    )
  `.execute(db);

  await sql`
    INSERT INTO edge_context_constrained_by (
      edge_id, src_vid, dst_vid, created_date, owner_did, relation_kind, status, evidence_ref
    )
    SELECT
      'edge:constraint:oka-training:a40-no-fp8-training',
      'oka-training:a40-fp8',
      'constraint:oka-training:a40-no-fp8-training',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'constrained_by',
      'active',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md'
    WHERE NOT EXISTS (
      SELECT 1 FROM edge_context_constrained_by WHERE edge_id = 'edge:constraint:oka-training:a40-no-fp8-training'
    )
  `.execute(db);

  await sql`
    INSERT INTO edge_context_constrained_by (
      edge_id, src_vid, dst_vid, created_date, owner_did, relation_kind, status, evidence_ref
    )
    SELECT
      'edge:constraint:oka-training:fp8-requires-bf16-fallback',
      'oka-training:l40s-fp8',
      'constraint:oka-training:fp8-requires-bf16-fallback',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'constrained_by',
      'active',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md'
    WHERE NOT EXISTS (
      SELECT 1 FROM edge_context_constrained_by WHERE edge_id = 'edge:constraint:oka-training:fp8-requires-bf16-fallback'
    )
  `.execute(db);

  await sql`
    INSERT INTO edge_context_depends_on (
      edge_id, src_vid, dst_vid, created_date, owner_did, relation_kind, status, evidence_ref
    )
    SELECT
      'edge:dependency:oka-training:l40s-fp8-capacity',
      'oka-training:l40s-fp8',
      'capability:oka-training:l40s-fp8-training',
      DATE '2026-05-09',
      'did:web:gftd.co.jp',
      'depends_on',
      'active',
      '90-docs/adr/2605092345-runpod-l40s-fp8-multimodal-model-design.md'
    WHERE NOT EXISTS (
      SELECT 1 FROM edge_context_depends_on WHERE edge_id = 'edge:dependency:oka-training:l40s-fp8-capacity'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_context_dependency_subject`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_context_constraint_severity`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_context_constraint_subject`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_context_capability_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_context_capability_subject`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_context_subject_scope`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_context_subject_ref`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_context_depends_on`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_context_constrained_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_context_has_capability`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_context_dependency`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_context_constraint`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_context_capability`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_context_subject`.execute(db);
}
