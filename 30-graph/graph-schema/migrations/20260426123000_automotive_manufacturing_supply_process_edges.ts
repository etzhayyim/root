import { Kysely, sql } from 'kysely';

/**
 * Automotive manufacturing supply/process graph extension.
 *
 * Extends the robotics manufacturing package graph with vehicle-specific
 * procurement, processing, intermediate part, responsibility, legal-entity,
 * craftsperson/person, and patent links. Existing canonical vertices remain
 * the targets for identity:
 *   - vertex_legal_entity via LEI/source registry
 *   - vertex_business_person / vertex_natural_person for responsible persons
 *   - vertex_patent for public patent evidence
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_automotive_material_requirement (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      material_id VARCHAR,
      package_id VARCHAR,
      material_kind VARCHAR,
      material_grade VARCHAR,
      specification VARCHAR,
      preferred_standard VARCHAR,
      quantity_per_vehicle DOUBLE PRECISION,
      unit VARCHAR,
      country_of_origin VARCHAR,
      recycled_content_pct DOUBLE PRECISION,
      restricted_substance_check VARCHAR,
      source_system VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auto_material_package ON vertex_automotive_material_requirement (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auto_material_kind_grade ON vertex_automotive_material_requirement (material_kind, material_grade)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_automotive_intermediate_part (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      intermediate_id VARCHAR,
      package_id VARCHAR,
      part_number VARCHAR,
      part_name VARCHAR,
      intermediate_kind VARCHAR,
      build_level VARCHAR,
      revision VARCHAR,
      traceability_lot VARCHAR,
      inspection_status VARCHAR,
      storage_requirement VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auto_intermediate_package ON vertex_automotive_intermediate_part (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auto_intermediate_part_number ON vertex_automotive_intermediate_part (part_number)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_automotive_responsibility_assignment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      assignment_id VARCHAR,
      package_id VARCHAR,
      scope_kind VARCHAR,
      scope_id VARCHAR,
      responsibility_kind VARCHAR,
      raci_role VARCHAR,
      approver_required BOOLEAN,
      person_vid VARCHAR,
      legal_entity_vid VARCHAR,
      role_title VARCHAR,
      evidence_url VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auto_resp_package ON vertex_automotive_responsibility_assignment (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_auto_resp_scope ON vertex_automotive_responsibility_assignment (scope_kind, scope_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_package_requires_material (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      package_id VARCHAR,
      material_id VARCHAR,
      requirement_kind VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_pkg_material_src ON edge_automotive_package_requires_material (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_pkg_material_dst ON edge_automotive_package_requires_material (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_material_supplied_by (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      material_id VARCHAR,
      supplier_lei VARCHAR,
      supplier_role VARCHAR,
      contract_ref VARCHAR,
      qualification_status VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_material_supplier_src ON edge_automotive_material_supplied_by (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_material_supplier_dst ON edge_automotive_material_supplied_by (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_material_supplier_lei ON edge_automotive_material_supplied_by (supplier_lei)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_process_uses_material (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      process_id VARCHAR,
      material_id VARCHAR,
      input_role VARCHAR,
      yield_pct DOUBLE PRECISION,
      scrap_handling VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_process_material_src ON edge_automotive_process_uses_material (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_process_material_dst ON edge_automotive_process_uses_material (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_process_produces_intermediate (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      process_id VARCHAR,
      intermediate_id VARCHAR,
      output_role VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_process_intermediate_src ON edge_automotive_process_produces_intermediate (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_process_intermediate_dst ON edge_automotive_process_produces_intermediate (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_intermediate_feeds_process (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      intermediate_id VARCHAR,
      process_id VARCHAR,
      input_role VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_intermediate_process_src ON edge_automotive_intermediate_feeds_process (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_intermediate_process_dst ON edge_automotive_intermediate_feeds_process (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_responsible_party (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      assignment_id VARCHAR,
      target_kind VARCHAR,
      responsibility_kind VARCHAR,
      raci_role VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_resp_src ON edge_automotive_responsible_party (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_resp_dst ON edge_automotive_responsible_party (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_process_performed_by (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      process_id VARCHAR,
      performer_kind VARCHAR,
      skill_name VARCHAR,
      certification_ref VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_performed_src ON edge_automotive_process_performed_by (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_performed_dst ON edge_automotive_process_performed_by (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_automotive_package_references_patent (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      package_id VARCHAR,
      patent_pub_number VARCHAR,
      relevance_kind VARCHAR,
      evidence_url VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_pkg_patent_src ON edge_automotive_package_references_patent (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_auto_pkg_patent_dst ON edge_automotive_package_references_patent (dst_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_automotive_package_supply_process_graph AS
      SELECT
        p.package_id,
        p.product_id,
        p.revision,
        p.asset_kind,
        COUNT(DISTINCT m.vertex_id) AS material_count,
        COUNT(DISTINCT ip.vertex_id) AS intermediate_count,
        COUNT(DISTINCT pr.vertex_id) AS process_count,
        COUNT(DISTINCT rp.vertex_id) AS responsibility_count,
        COUNT(DISTINCT ms.dst_vid) AS supplier_entity_count,
        COUNT(DISTINCT pp.dst_vid) AS patent_count,
        MAX(p._seq) AS _seq
      FROM vertex_robotics_product_package p
      LEFT JOIN vertex_automotive_material_requirement m ON m.package_id = p.package_id
      LEFT JOIN vertex_automotive_intermediate_part ip ON ip.package_id = p.package_id
      LEFT JOIN vertex_robotics_manufacturing_process pr ON pr.package_id = p.package_id
      LEFT JOIN vertex_automotive_responsibility_assignment rp ON rp.package_id = p.package_id
      LEFT JOIN edge_automotive_material_supplied_by ms ON ms.material_id = m.material_id
      LEFT JOIN edge_automotive_package_references_patent pp ON pp.package_id = p.package_id
      WHERE p.asset_kind IN ('autonomous_vehicle', 'vehicle', 'bev', 'hybrid', 'commercial_vehicle')
         OR p.package_profile = 'automotive'
      GROUP BY p.package_id, p.product_id, p.revision, p.asset_kind
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_automotive_package_supply_process_graph`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_package_references_patent`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_process_performed_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_responsible_party`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_intermediate_feeds_process`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_process_produces_intermediate`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_process_uses_material`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_material_supplied_by`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_automotive_package_requires_material`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_automotive_responsibility_assignment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_automotive_intermediate_part`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_automotive_material_requirement`.execute(db);
}
