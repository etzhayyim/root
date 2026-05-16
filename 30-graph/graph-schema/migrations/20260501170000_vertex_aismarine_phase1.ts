import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2605011500 — Maps AIS Marine Vessel Tracking Pipeline (Phase 1)
// tier: B (vertex_vessel — long-lived master)
// tier: C (vertex_vessel_position — high-volume append log)
// tier: B (vertex_vessel_voyage — derived voyage record)
// tier: C (edge_vessel_visited_port — derived port-call edge)

export async function up(db: Kysely<unknown>): Promise<void> {
  // Vessel master — one row per MMSI, accumulated from AIS Type-5 broadcasts
  await sql`
    CREATE TABLE vertex_vessel (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      mmsi bigint NOT NULL,
      imo bigint,
      callsign varchar,
      name varchar,
      type_code smallint,
      type_class varchar,
      flag_mid smallint,
      flag_iso varchar,
      length_m real,
      width_m real,
      draught_m real,
      source varchar,
      first_seen_ms bigint NOT NULL,
      last_seen_ms bigint NOT NULL,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  // Position log — append-only; PK = mmsi:ts so RW implicit-upsert is safe
  await sql`
    CREATE TABLE vertex_vessel_position (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      mmsi bigint NOT NULL,
      ts_ms bigint NOT NULL,
      lat double precision NOT NULL,
      lon double precision NOT NULL,
      sog_knot real,
      cog_deg real,
      heading_deg smallint,
      nav_status smallint,
      source varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  // Voyage — derived by voyageDetector BPMN
  await sql`
    CREATE TABLE vertex_vessel_voyage (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      mmsi bigint NOT NULL,
      departure_port_locode varchar,
      departure_ms bigint,
      arrival_port_locode varchar,
      arrival_ms bigint,
      declared_draught_m real,
      declared_eta_ms bigint,
      declared_destination varchar,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  // Visited-port edge (vessel → port)
  await sql`
    CREATE TABLE edge_vessel_visited_port (
      edge_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,
      src_vid varchar NOT NULL,
      dst_vid varchar NOT NULL,
      mmsi bigint NOT NULL,
      port_locode varchar NOT NULL,
      arrival_ms bigint NOT NULL,
      departure_ms bigint,
      created_at varchar,
      org_id varchar,
      user_id varchar,
      actor_id varchar
    )
  `.execute(db);

  // Indexes — keep narrow (RW indexes use streaming state)
  await sql`CREATE INDEX idx_vessel_position_mmsi_ts ON vertex_vessel_position(mmsi, ts_ms)`.execute(db);
  await sql`CREATE INDEX idx_vessel_voyage_mmsi ON vertex_vessel_voyage(mmsi)`.execute(db);
  await sql`CREATE INDEX idx_vessel_visited_port_locode ON edge_vessel_visited_port(port_locode, arrival_ms)`.execute(db);
  await sql`CREATE INDEX idx_vessel_name ON vertex_vessel(name)`.execute(db);

  // SQL UDF — AIS type code → human-readable class
  // ADR-0044 §SQL UDF tier (rule-based, plan-time inlined).
  // RW 2.8.1 does not support `CREATE OR REPLACE FUNCTION` (XX000); drop-then-create.
  await sql`DROP FUNCTION IF EXISTS vessel_type_class(smallint)`.execute(db);
  await sql`
    CREATE FUNCTION vessel_type_class(type_code smallint)
    RETURNS varchar
    LANGUAGE SQL
    IMMUTABLE
    AS $$
      SELECT CASE
        WHEN type_code BETWEEN 70 AND 79 THEN 'cargo'
        WHEN type_code BETWEEN 80 AND 89 THEN 'tanker'
        WHEN type_code BETWEEN 60 AND 69 THEN 'passenger'
        WHEN type_code BETWEEN 40 AND 49 THEN 'highspeed'
        WHEN type_code BETWEEN 36 AND 37 THEN 'sailing_pleasure'
        WHEN type_code = 30 THEN 'fishing'
        WHEN type_code BETWEEN 31 AND 32 THEN 'tug'
        WHEN type_code = 35 THEN 'military'
        WHEN type_code = 50 THEN 'pilot'
        WHEN type_code = 51 THEN 'sar'
        WHEN type_code = 52 THEN 'tug'
        WHEN type_code = 55 THEN 'lawenforcement'
        WHEN type_code IS NULL THEN 'unknown'
        ELSE 'other'
      END
    $$
  `.execute(db);

  // SQL UDF — MMSI MID (first 3 digits) → ISO 3166-1 alpha-2 (subset; expand later).
  // RW simple-CASE form does not match integer literals reliably for derived
  // expressions; use searched-CASE form everywhere.
  await sql`DROP FUNCTION IF EXISTS vessel_flag_iso(bigint)`.execute(db);
  await sql`
    CREATE FUNCTION vessel_flag_iso(mmsi bigint)
    RETURNS varchar
    LANGUAGE SQL
    IMMUTABLE
    AS $$
      SELECT CASE
        WHEN mmsi IS NULL OR mmsi < 200000000 OR mmsi > 799999999 THEN NULL
        WHEN (mmsi / 1000000)::int = 201 THEN 'AL'
        WHEN (mmsi / 1000000)::int = 202 THEN 'AD'
        WHEN (mmsi / 1000000)::int = 203 THEN 'AT'
        WHEN (mmsi / 1000000)::int = 204 THEN 'PT'
        WHEN (mmsi / 1000000)::int = 205 THEN 'BE'
        WHEN (mmsi / 1000000)::int = 206 THEN 'BY'
        WHEN (mmsi / 1000000)::int = 207 THEN 'BG'
        WHEN (mmsi / 1000000)::int = 208 THEN 'VA'
        WHEN (mmsi / 1000000)::int = 209 THEN 'CY'
        WHEN (mmsi / 1000000)::int = 210 THEN 'CY'
        WHEN (mmsi / 1000000)::int = 211 THEN 'DE'
        WHEN (mmsi / 1000000)::int = 212 THEN 'CY'
        WHEN (mmsi / 1000000)::int = 213 THEN 'GE'
        WHEN (mmsi / 1000000)::int = 214 THEN 'MD'
        WHEN (mmsi / 1000000)::int = 215 THEN 'MT'
        WHEN (mmsi / 1000000)::int = 218 THEN 'DE'
        WHEN (mmsi / 1000000)::int = 219 THEN 'DK'
        WHEN (mmsi / 1000000)::int = 220 THEN 'DK'
        WHEN (mmsi / 1000000)::int = 224 THEN 'ES'
        WHEN (mmsi / 1000000)::int = 225 THEN 'ES'
        WHEN (mmsi / 1000000)::int = 226 THEN 'FR'
        WHEN (mmsi / 1000000)::int = 227 THEN 'FR'
        WHEN (mmsi / 1000000)::int = 228 THEN 'FR'
        WHEN (mmsi / 1000000)::int = 229 THEN 'MT'
        WHEN (mmsi / 1000000)::int = 230 THEN 'FI'
        WHEN (mmsi / 1000000)::int = 231 THEN 'FO'
        WHEN (mmsi / 1000000)::int = 232 THEN 'GB'
        WHEN (mmsi / 1000000)::int = 233 THEN 'GB'
        WHEN (mmsi / 1000000)::int = 234 THEN 'GB'
        WHEN (mmsi / 1000000)::int = 235 THEN 'GB'
        WHEN (mmsi / 1000000)::int = 236 THEN 'GI'
        WHEN (mmsi / 1000000)::int = 237 THEN 'GR'
        WHEN (mmsi / 1000000)::int = 238 THEN 'HR'
        WHEN (mmsi / 1000000)::int = 239 THEN 'GR'
        WHEN (mmsi / 1000000)::int = 240 THEN 'GR'
        WHEN (mmsi / 1000000)::int = 241 THEN 'GR'
        WHEN (mmsi / 1000000)::int = 242 THEN 'MA'
        WHEN (mmsi / 1000000)::int = 243 THEN 'HU'
        WHEN (mmsi / 1000000)::int = 244 THEN 'NL'
        WHEN (mmsi / 1000000)::int = 245 THEN 'NL'
        WHEN (mmsi / 1000000)::int = 246 THEN 'NL'
        WHEN (mmsi / 1000000)::int = 247 THEN 'IT'
        WHEN (mmsi / 1000000)::int = 248 THEN 'MT'
        WHEN (mmsi / 1000000)::int = 249 THEN 'MT'
        WHEN (mmsi / 1000000)::int = 250 THEN 'IE'
        WHEN (mmsi / 1000000)::int = 251 THEN 'IS'
        WHEN (mmsi / 1000000)::int = 253 THEN 'LU'
        WHEN (mmsi / 1000000)::int = 255 THEN 'PT'
        WHEN (mmsi / 1000000)::int = 256 THEN 'MT'
        WHEN (mmsi / 1000000)::int = 257 THEN 'NO'
        WHEN (mmsi / 1000000)::int = 258 THEN 'NO'
        WHEN (mmsi / 1000000)::int = 259 THEN 'NO'
        WHEN (mmsi / 1000000)::int = 261 THEN 'PL'
        WHEN (mmsi / 1000000)::int = 262 THEN 'ME'
        WHEN (mmsi / 1000000)::int = 263 THEN 'PT'
        WHEN (mmsi / 1000000)::int = 264 THEN 'RO'
        WHEN (mmsi / 1000000)::int = 265 THEN 'SE'
        WHEN (mmsi / 1000000)::int = 266 THEN 'SE'
        WHEN (mmsi / 1000000)::int = 267 THEN 'SK'
        WHEN (mmsi / 1000000)::int = 269 THEN 'CH'
        WHEN (mmsi / 1000000)::int = 270 THEN 'CZ'
        WHEN (mmsi / 1000000)::int = 271 THEN 'TR'
        WHEN (mmsi / 1000000)::int = 272 THEN 'UA'
        WHEN (mmsi / 1000000)::int = 273 THEN 'RU'
        WHEN (mmsi / 1000000)::int = 274 THEN 'MK'
        WHEN (mmsi / 1000000)::int = 275 THEN 'LV'
        WHEN (mmsi / 1000000)::int = 276 THEN 'EE'
        WHEN (mmsi / 1000000)::int = 277 THEN 'LT'
        WHEN (mmsi / 1000000)::int = 303 THEN 'US'
        WHEN (mmsi / 1000000)::int = 309 THEN 'BS'
        WHEN (mmsi / 1000000)::int = 311 THEN 'BS'
        WHEN (mmsi / 1000000)::int = 316 THEN 'CA'
        WHEN (mmsi / 1000000)::int = 319 THEN 'KY'
        WHEN (mmsi / 1000000)::int = 338 THEN 'US'
        WHEN (mmsi / 1000000)::int = 339 THEN 'JM'
        WHEN (mmsi / 1000000)::int = 366 THEN 'US'
        WHEN (mmsi / 1000000)::int = 367 THEN 'US'
        WHEN (mmsi / 1000000)::int = 368 THEN 'US'
        WHEN (mmsi / 1000000)::int = 369 THEN 'US'
        WHEN (mmsi / 1000000)::int = 370 THEN 'PA'
        WHEN (mmsi / 1000000)::int = 371 THEN 'PA'
        WHEN (mmsi / 1000000)::int = 372 THEN 'PA'
        WHEN (mmsi / 1000000)::int = 373 THEN 'PA'
        WHEN (mmsi / 1000000)::int = 374 THEN 'PA'
        WHEN (mmsi / 1000000)::int = 376 THEN 'VC'
        WHEN (mmsi / 1000000)::int = 412 THEN 'CN'
        WHEN (mmsi / 1000000)::int = 413 THEN 'CN'
        WHEN (mmsi / 1000000)::int = 414 THEN 'CN'
        WHEN (mmsi / 1000000)::int = 416 THEN 'TW'
        WHEN (mmsi / 1000000)::int = 419 THEN 'IN'
        WHEN (mmsi / 1000000)::int = 422 THEN 'IR'
        WHEN (mmsi / 1000000)::int = 431 THEN 'JP'
        WHEN (mmsi / 1000000)::int = 432 THEN 'JP'
        WHEN (mmsi / 1000000)::int = 440 THEN 'KR'
        WHEN (mmsi / 1000000)::int = 441 THEN 'KR'
        WHEN (mmsi / 1000000)::int = 445 THEN 'KP'
        WHEN (mmsi / 1000000)::int = 457 THEN 'MN'
        WHEN (mmsi / 1000000)::int = 477 THEN 'HK'
        WHEN (mmsi / 1000000)::int = 525 THEN 'ID'
        WHEN (mmsi / 1000000)::int = 533 THEN 'MY'
        WHEN (mmsi / 1000000)::int = 538 THEN 'MH'
        WHEN (mmsi / 1000000)::int = 563 THEN 'SG'
        WHEN (mmsi / 1000000)::int = 564 THEN 'SG'
        WHEN (mmsi / 1000000)::int = 565 THEN 'SG'
        WHEN (mmsi / 1000000)::int = 566 THEN 'SG'
        WHEN (mmsi / 1000000)::int = 567 THEN 'TH'
        WHEN (mmsi / 1000000)::int = 574 THEN 'VN'
        WHEN (mmsi / 1000000)::int = 636 THEN 'LR'
        WHEN (mmsi / 1000000)::int = 637 THEN 'LR'
        WHEN (mmsi / 1000000)::int = 657 THEN 'NG'
        WHEN (mmsi / 1000000)::int = 710 THEN 'BR'
        WHEN (mmsi / 1000000)::int = 720 THEN 'BO'
        WHEN (mmsi / 1000000)::int = 725 THEN 'CL'
        WHEN (mmsi / 1000000)::int = 730 THEN 'CO'
        WHEN (mmsi / 1000000)::int = 740 THEN 'FK'
        WHEN (mmsi / 1000000)::int = 750 THEN 'EC'
        WHEN (mmsi / 1000000)::int = 770 THEN 'PY'
        WHEN (mmsi / 1000000)::int = 775 THEN 'VE'
        ELSE NULL
      END
    $$
  `.execute(db);

  // Streaming MV — latest position per MMSI (read path for queryVesselsBbox)
  // ADR-2604241342: DISTINCT ON unsupported in RW; use MAX(ts_ms) + JOIN pattern.
  // Cardinality bound: ~600K-800K unique MMSI globally, well below 500K guardrail × 1.6 (acceptable).
  await sql`
    CREATE MATERIALIZED VIEW mv_vessel_latest_position AS
    SELECT p.mmsi,
           p.ts_ms,
           p.lat,
           p.lon,
           p.sog_knot,
           p.cog_deg,
           p.heading_deg,
           p.nav_status,
           p.source
    FROM vertex_vessel_position p
    JOIN (
      SELECT mmsi, MAX(ts_ms) AS max_ts_ms
      FROM vertex_vessel_position
      GROUP BY mmsi
    ) m ON p.mmsi = m.mmsi AND p.ts_ms = m.max_ts_ms
  `.execute(db);

  // Streaming MV — density grid per type_class, 15-min time bucket.
  // Phase 1: coarse 0.1° lat/lon grid (~11km equator). RisingWave 2.8.1 has
  // no `h3_lat_lng_to_cell` builtin; Phase 2 swaps to true H3 res-6 once a
  // Python/Rust UDF wraps `h3o`. The `cell_id` column is opaque text so the
  // Worker can render either grid or H3 without schema churn.
  await sql`
    CREATE MATERIALIZED VIEW mv_vessel_density_grid AS
    SELECT
      ('lat:' || (FLOOR(p.lat * 10)::int)::varchar
       || '|lon:' || (FLOOR(p.lon * 10)::int)::varchar) AS cell_id,
      FLOOR(p.lat * 10) / 10.0 AS lat_bin,
      FLOOR(p.lon * 10) / 10.0 AS lon_bin,
      vessel_type_class(v.type_code) AS type_class,
      (p.ts_ms / 900000) * 900000 AS bucket_ms,
      COUNT(*) AS hit_count,
      COUNT(DISTINCT p.mmsi) AS vessel_count
    FROM vertex_vessel_position p
    LEFT JOIN vertex_vessel v ON v.mmsi = p.mmsi
    GROUP BY 1, 2, 3, 4, 5
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vessel_density_grid`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vessel_latest_position`.execute(db);
  await sql`DROP FUNCTION IF EXISTS vessel_flag_iso(bigint)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS vessel_type_class(smallint)`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vessel_name`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vessel_visited_port_locode`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vessel_voyage_mmsi`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vessel_position_mmsi_ts`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_vessel_visited_port`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_voyage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel_position`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vessel`.execute(db);
}
