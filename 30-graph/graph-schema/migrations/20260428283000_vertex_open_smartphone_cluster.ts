import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── BOM sub-cluster ─────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom (
      vertex_id VARCHAR PRIMARY KEY,
      bom_id VARCHAR NOT NULL,
      design_name VARCHAR NOT NULL,
      version VARCHAR NOT NULL,
      soc_did VARCHAR,
      modem_did VARCHAR,
      os_did VARCHAR,
      ems_facility_did VARCHAR,
      target_price_usd DOUBLE PRECISION,
      open_score_pct DOUBLE PRECISION,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom_line (
      vertex_id VARCHAR PRIMARY KEY,
      line_id VARCHAR NOT NULL,
      bom_did VARCHAR NOT NULL,
      component_type VARCHAR NOT NULL,
      vendor_name VARCHAR NOT NULL,
      part_number VARCHAR NOT NULL,
      unit_cost_usd DOUBLE PRECISION,
      open_source BOOLEAN NOT NULL DEFAULT false,
      license VARCHAR,
      patent_did VARCHAR,
      alternative_count INTEGER NOT NULL DEFAULT 0,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_bom_sourcer (
      vertex_id VARCHAR PRIMARY KEY,
      bom_line_did VARCHAR NOT NULL,
      alt_vendor VARCHAR NOT NULL,
      alt_part_number VARCHAR NOT NULL,
      alt_unit_cost_usd DOUBLE PRECISION,
      open_source BOOLEAN NOT NULL DEFAULT false,
      availability VARCHAR,
      lead_time_weeks INTEGER,
      notes VARCHAR,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  // ── EMS sub-cluster ──────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_ems_facility (
      vertex_id VARCHAR PRIMARY KEY,
      facility_id VARCHAR NOT NULL,
      operator_name VARCHAR NOT NULL,
      operator_lei VARCHAR,
      location_iso3 VARCHAR NOT NULL,
      city VARCHAR,
      facility_type VARCHAR NOT NULL,
      monthly_capacity_units BIGINT,
      certifications VARCHAR,
      rba_audit_status VARCHAR,
      conflict_mineral_compliant BOOLEAN NOT NULL DEFAULT false,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_ems_order (
      vertex_id VARCHAR PRIMARY KEY,
      order_id VARCHAR NOT NULL,
      facility_did VARCHAR NOT NULL,
      bom_did VARCHAR NOT NULL,
      quantity_units BIGINT NOT NULL,
      target_unit_cost_usd DOUBLE PRECISION,
      delivery_quarter VARCHAR,
      quality_standard VARCHAR,
      order_status VARCHAR NOT NULL DEFAULT 'pending',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  // ── Modem sub-cluster ────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_spec (
      vertex_id VARCHAR PRIMARY KEY,
      modem_id VARCHAR NOT NULL,
      chip_name VARCHAR NOT NULL,
      rat_support VARCHAR,
      baseband_chip VARCHAR,
      open_source_fw BOOLEAN NOT NULL DEFAULT false,
      fw_license VARCHAR,
      max_dl_mbps DOUBLE PRECISION,
      max_ul_mbps DOUBLE PRECISION,
      release_year INTEGER,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_type_approval (
      vertex_id VARCHAR PRIMARY KEY,
      modem_did VARCHAR NOT NULL,
      authority VARCHAR NOT NULL,
      certificate_no VARCHAR NOT NULL,
      jurisdiction_iso3 VARCHAR NOT NULL,
      approved_at VARCHAR,
      expiry_date VARCHAR,
      rat_approved VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_modem_sep_dep (
      vertex_id VARCHAR PRIMARY KEY,
      modem_did VARCHAR NOT NULL,
      patent_no VARCHAR NOT NULL,
      holder_did VARCHAR,
      rat VARCHAR NOT NULL,
      frand_declared BOOLEAN NOT NULL DEFAULT false,
      pool_id VARCHAR,
      expiry_date VARCHAR,
      blocker_status VARCHAR NOT NULL DEFAULT 'unknown',
      severity VARCHAR NOT NULL DEFAULT 'medium',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  // ── OS sub-cluster ───────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_build (
      vertex_id VARCHAR PRIMARY KEY,
      build_id VARCHAR NOT NULL,
      os_name VARCHAR NOT NULL,
      os_base VARCHAR NOT NULL,
      version VARCHAR NOT NULL,
      kernel_version VARCHAR,
      soc_support VARCHAR,
      open_blobs_pct DOUBLE PRECISION,
      verified_boot BOOLEAN NOT NULL DEFAULT false,
      build_url VARCHAR,
      release_date VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_hal_driver (
      vertex_id VARCHAR PRIMARY KEY,
      driver_id VARCHAR NOT NULL,
      os_did VARCHAR NOT NULL,
      soc_did VARCHAR,
      sensor_did VARCHAR,
      driver_type VARCHAR NOT NULL,
      upstream_status VARCHAR,
      vendor_blobs_required BOOLEAN NOT NULL DEFAULT false,
      license VARCHAR,
      version VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_os_ota (
      vertex_id VARCHAR PRIMARY KEY,
      ota_id VARCHAR NOT NULL,
      os_did VARCHAR NOT NULL,
      from_version VARCHAR NOT NULL,
      to_version VARCHAR NOT NULL,
      release_notes_url VARCHAR,
      patch_level VARCHAR,
      cve_fixes VARCHAR,
      ota_size_mb DOUBLE PRECISION,
      signed BOOLEAN NOT NULL DEFAULT false,
      release_date VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  // ── Patent sub-cluster ───────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_sep (
      vertex_id VARCHAR PRIMARY KEY,
      patent_no VARCHAR NOT NULL,
      holder_did VARCHAR,
      rat VARCHAR NOT NULL,
      standard VARCHAR,
      frand_declared BOOLEAN NOT NULL DEFAULT false,
      pool_id VARCHAR,
      expiry_date VARCHAR,
      blocker_status VARCHAR NOT NULL DEFAULT 'unknown',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_pool (
      vertex_id VARCHAR PRIMARY KEY,
      pool_id VARCHAR NOT NULL,
      pool_name VARCHAR NOT NULL,
      administrator VARCHAR,
      standards_covered VARCHAR,
      member_count INTEGER NOT NULL DEFAULT 0,
      license_fee_usd_per_unit DOUBLE PRECISION,
      frand_compliant BOOLEAN NOT NULL DEFAULT false,
      url VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_dep (
      vertex_id VARCHAR PRIMARY KEY,
      dep_id VARCHAR NOT NULL,
      component_type VARCHAR NOT NULL,
      component_did VARCHAR,
      patent_no VARCHAR NOT NULL,
      holder_did VARCHAR,
      standard VARCHAR,
      dependency_type VARCHAR NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  // ── Sensor sub-cluster ───────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_sensor_module (
      vertex_id VARCHAR PRIMARY KEY,
      sensor_id VARCHAR NOT NULL,
      sensor_type VARCHAR NOT NULL,
      vendor VARCHAR NOT NULL,
      model VARCHAR NOT NULL,
      interface_type VARCHAR,
      open_driver BOOLEAN NOT NULL DEFAULT false,
      mainline_kernel_status VARCHAR,
      pixel_count_mp DOUBLE PRECISION,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_sensor_calibration (
      vertex_id VARCHAR PRIMARY KEY,
      sensor_did VARCHAR NOT NULL,
      calibration_type VARCHAR NOT NULL,
      standard_ref VARCHAR,
      calibrated_at VARCHAR NOT NULL,
      valid_until VARCHAR,
      calibrated_by VARCHAR,
      pass BOOLEAN NOT NULL DEFAULT false,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  // ── SoC sub-cluster ──────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_design (
      vertex_id VARCHAR PRIMARY KEY,
      chip_id VARCHAR NOT NULL,
      chip_name VARCHAR NOT NULL,
      isa VARCHAR NOT NULL,
      process_node_nm INTEGER,
      die_area_mm2 DOUBLE PRECISION,
      transistor_count_b DOUBLE PRECISION,
      open_source_rtl BOOLEAN NOT NULL DEFAULT false,
      rtl_license VARCHAR,
      fab_did VARCHAR,
      tape_out_date VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_fab_order (
      vertex_id VARCHAR PRIMARY KEY,
      order_id VARCHAR NOT NULL,
      chip_did VARCHAR NOT NULL,
      fab_did VARCHAR NOT NULL,
      process_node_nm INTEGER,
      wafer_qty INTEGER,
      delivery_estimate VARCHAR,
      price_usd_k DOUBLE PRECISION,
      order_status VARCHAR NOT NULL DEFAULT 'pending',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_smartphone_soc_export_flag (
      vertex_id VARCHAR PRIMARY KEY,
      chip_did VARCHAR NOT NULL,
      flag_type VARCHAR NOT NULL,
      entity_list_entry VARCHAR,
      jurisdiction VARCHAR NOT NULL,
      flagged_at VARCHAR NOT NULL,
      severity VARCHAR NOT NULL DEFAULT 'medium',
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR NOT NULL,
      user_id VARCHAR NOT NULL,
      actor_id VARCHAR NOT NULL
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    "vertex_open_smartphone_soc_export_flag",
    "vertex_open_smartphone_soc_fab_order",
    "vertex_open_smartphone_soc_design",
    "vertex_open_smartphone_sensor_calibration",
    "vertex_open_smartphone_sensor_module",
    "vertex_open_smartphone_patent_dep",
    "vertex_open_smartphone_patent_pool",
    "vertex_open_smartphone_patent_sep",
    "vertex_open_smartphone_os_ota",
    "vertex_open_smartphone_os_hal_driver",
    "vertex_open_smartphone_os_build",
    "vertex_open_smartphone_modem_sep_dep",
    "vertex_open_smartphone_modem_type_approval",
    "vertex_open_smartphone_modem_spec",
    "vertex_open_smartphone_ems_order",
    "vertex_open_smartphone_ems_facility",
    "vertex_open_smartphone_bom_sourcer",
    "vertex_open_smartphone_bom_line",
    "vertex_open_smartphone_bom",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
