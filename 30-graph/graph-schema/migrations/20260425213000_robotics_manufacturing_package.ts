import { Kysely, sql } from 'kysely';

/**
 * Robotics product manufacturing package graph.
 *
 * Mirrors ADR 2604252100 and the EMS / Alibaba ZIP package profile:
 *   CAD/       STEP, PDF drawings, DXF/DWG machining references
 *   PCB/       Gerber RS-274X, Excellon drill, pick/place, schematics
 *   BOM/       CSV/XLSX with MPN, manufacturer, quantity, alternates
 *   Assembly/  assembly drawings, work instructions, torque/ESD notes
 *   QA/        OK/NG criteria, measurement method, sample photos
 *   RFQ.pdf    MOQ, quantity, lead time, target price, Incoterms, packing
 *
 * Large artifacts remain in blob storage. These tables hold graph metadata,
 * content hashes, process topology, quality gates, and supplier RFQ readiness.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_robotics_product_package (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      package_id VARCHAR,
      product_id VARCHAR,
      revision VARCHAR,
      asset_kind VARCHAR,
      package_profile VARCHAR,
      package_zip_blob_key VARCHAR,
      manifest_blob_key VARCHAR,
      manifest_sha256 VARCHAR,
      source_system VARCHAR,
      validation_status VARCHAR,
      readiness_status VARCHAR,
      risk_level VARCHAR,
      target_supplier_kind VARCHAR,
      target_supplier_region VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_pkg_package_id ON vertex_robotics_product_package (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_pkg_asset_kind ON vertex_robotics_product_package (asset_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_pkg_readiness ON vertex_robotics_product_package (readiness_status, validation_status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_robotics_product_file (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      file_id VARCHAR,
      package_id VARCHAR,
      path VARCHAR,
      folder VARCHAR,
      role VARCHAR,
      format VARCHAR,
      standard VARCHAR,
      sha256 VARCHAR,
      blob_key VARCHAR,
      required BOOLEAN,
      present BOOLEAN,
      file_status VARCHAR,
      machine_capability VARCHAR,
      process_kind VARCHAR,
      notes VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_file_package ON vertex_robotics_product_file (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_file_folder_role ON vertex_robotics_product_file (folder, role)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_file_sha256 ON vertex_robotics_product_file (sha256)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_file_required_status ON vertex_robotics_product_file (required, present, file_status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_robotics_manufacturing_process (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      process_id VARCHAR,
      package_id VARCHAR,
      process_kind VARCHAR,
      sequence_no BIGINT,
      bpmn_process_id VARCHAR,
      bpmn_task_type VARCHAR,
      required_machine VARCHAR,
      operator_skill VARCHAR,
      input_roles_json VARCHAR,
      output_roles_json VARCHAR,
      acceptance_criteria_json VARCHAR,
      estimated_minutes BIGINT,
      process_status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_process_package ON vertex_robotics_manufacturing_process (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_process_kind ON vertex_robotics_manufacturing_process (process_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_process_sequence ON vertex_robotics_manufacturing_process (package_id, sequence_no)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_robotics_quality_gate (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      gate_id VARCHAR,
      package_id VARCHAR,
      process_id VARCHAR,
      gate_kind VARCHAR,
      measurement_method VARCHAR,
      ok_ng_criteria_json VARCHAR,
      sample_photo_blob_key VARCHAR,
      inspection_record_blob_key VARCHAR,
      gate_status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_gate_package ON vertex_robotics_quality_gate (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_gate_process ON vertex_robotics_quality_gate (process_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_gate_status ON vertex_robotics_quality_gate (gate_status, gate_kind)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_robotics_rfq (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      rfq_id VARCHAR,
      package_id VARCHAR,
      supplier_kind VARCHAR,
      supplier_region VARCHAR,
      quantity BIGINT,
      moq BIGINT,
      target_unit_cost DOUBLE PRECISION,
      currency VARCHAR,
      incoterms VARCHAR,
      lead_time_days BIGINT,
      packaging_spec VARCHAR,
      rfq_pdf_blob_key VARCHAR,
      export_zip_blob_key VARCHAR,
      rfq_status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_rfq_package ON vertex_robotics_rfq (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_rfq_region_status ON vertex_robotics_rfq (supplier_region, rfq_status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_robotics_control_adapter_spec (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      adapter_id VARCHAR,
      package_id VARCHAR,
      asset_kind VARCHAR,
      control_standard VARCHAR,
      sdk_name VARCHAR,
      adapter_tool VARCHAR,
      config_roles_json VARCHAR,
      safety_requirements_json VARCHAR,
      telemetry_topics_json VARCHAR,
      adapter_status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_adapter_package ON vertex_robotics_control_adapter_spec (package_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_robotics_adapter_asset_standard ON vertex_robotics_control_adapter_spec (asset_kind, control_standard)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_robotics_package_has_file (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      package_id VARCHAR,
      file_id VARCHAR,
      role VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_pkg_file_src ON edge_robotics_package_has_file (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_pkg_file_dst ON edge_robotics_package_has_file (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_robotics_package_has_process (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      package_id VARCHAR,
      process_id VARCHAR,
      sequence_no BIGINT,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_pkg_process_src ON edge_robotics_package_has_process (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_pkg_process_dst ON edge_robotics_package_has_process (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_robotics_process_consumes_file (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      process_id VARCHAR,
      file_id VARCHAR,
      input_role VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_consumes_process ON edge_robotics_process_consumes_file (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_consumes_file ON edge_robotics_process_consumes_file (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_robotics_process_produces_file (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      process_id VARCHAR,
      file_id VARCHAR,
      output_role VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_produces_process ON edge_robotics_process_produces_file (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_produces_file ON edge_robotics_process_produces_file (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_robotics_process_has_quality_gate (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      process_id VARCHAR,
      gate_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_process_gate_src ON edge_robotics_process_has_quality_gate (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_process_gate_dst ON edge_robotics_process_has_quality_gate (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_robotics_package_rfq (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      package_id VARCHAR,
      rfq_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_package_rfq_src ON edge_robotics_package_rfq (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_package_rfq_dst ON edge_robotics_package_rfq (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_robotics_package_uses_control_adapter (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      package_id VARCHAR,
      adapter_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_package_adapter_src ON edge_robotics_package_uses_control_adapter (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_robotics_package_adapter_dst ON edge_robotics_package_uses_control_adapter (dst_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_robotics_manufacturing_package_readiness AS
      SELECT
        p.vertex_id AS package_vid,
        p.package_id,
        p.product_id,
        p.revision,
        p.asset_kind,
        p.package_profile,
        p.validation_status,
        p.readiness_status,
        COUNT(DISTINCT f.vertex_id) AS file_count,
        COUNT(DISTINCT CASE WHEN f.required THEN f.vertex_id ELSE NULL END) AS required_file_count,
        COUNT(DISTINCT CASE WHEN f.required AND f.present THEN f.vertex_id ELSE NULL END) AS present_required_file_count,
        COUNT(DISTINCT CASE WHEN f.required AND NOT f.present THEN f.vertex_id ELSE NULL END) AS missing_required_file_count,
        COUNT(DISTINCT pr.vertex_id) AS process_count,
        COUNT(DISTINCT qg.vertex_id) AS quality_gate_count,
        COUNT(DISTINCT rfq.vertex_id) AS rfq_count,
        MAX(p._seq) AS _seq
      FROM vertex_robotics_product_package p
      LEFT JOIN vertex_robotics_product_file f ON f.package_id = p.package_id
      LEFT JOIN vertex_robotics_manufacturing_process pr ON pr.package_id = p.package_id
      LEFT JOIN vertex_robotics_quality_gate qg ON qg.package_id = p.package_id
      LEFT JOIN vertex_robotics_rfq rfq ON rfq.package_id = p.package_id
      GROUP BY p.vertex_id, p.package_id, p.product_id, p.revision, p.asset_kind,
               p.package_profile, p.validation_status, p.readiness_status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_robotics_supplier_rfq_export AS
      SELECT
        p.package_id,
        p.product_id,
        p.revision,
        p.asset_kind,
        rfq.rfq_id,
        rfq.supplier_kind,
        rfq.supplier_region,
        rfq.quantity,
        rfq.moq,
        rfq.target_unit_cost,
        rfq.currency,
        rfq.incoterms,
        rfq.lead_time_days,
        rfq.rfq_status,
        SUM(CASE WHEN f.folder = 'CAD' THEN 1 ELSE 0 END) AS cad_file_count,
        SUM(CASE WHEN f.folder = 'PCB' THEN 1 ELSE 0 END) AS pcb_file_count,
        SUM(CASE WHEN f.folder = 'BOM' THEN 1 ELSE 0 END) AS bom_file_count,
        SUM(CASE WHEN f.folder = 'Assembly' THEN 1 ELSE 0 END) AS assembly_file_count,
        SUM(CASE WHEN f.folder = 'QA' THEN 1 ELSE 0 END) AS qa_file_count,
        SUM(CASE WHEN f.folder = 'RFQ' THEN 1 ELSE 0 END) AS rfq_file_count,
        MAX(p._seq) AS _seq
      FROM vertex_robotics_product_package p
      JOIN vertex_robotics_rfq rfq ON rfq.package_id = p.package_id
      LEFT JOIN vertex_robotics_product_file f ON f.package_id = p.package_id
      GROUP BY p.package_id, p.product_id, p.revision, p.asset_kind,
               rfq.rfq_id, rfq.supplier_kind, rfq.supplier_region, rfq.quantity,
               rfq.moq, rfq.target_unit_cost, rfq.currency, rfq.incoterms,
               rfq.lead_time_days, rfq.rfq_status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_robotics_supplier_rfq_export`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_robotics_manufacturing_package_readiness`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_robotics_package_uses_control_adapter`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_robotics_package_rfq`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_robotics_process_has_quality_gate`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_robotics_process_produces_file`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_robotics_process_consumes_file`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_robotics_package_has_process`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_robotics_package_has_file`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_robotics_control_adapter_spec`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_robotics_rfq`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_robotics_quality_gate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_robotics_manufacturing_process`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_robotics_product_file`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_robotics_product_package`.execute(db);
}
