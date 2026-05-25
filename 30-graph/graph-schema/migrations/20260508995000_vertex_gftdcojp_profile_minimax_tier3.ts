import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * etzhayyim.etzhayyim.com Profile + Minimax Score (Tier 3 PII)
 * Principal: etzhayyim. Vendor: etzhayyim Japan株式会社.
 *
 * Tier 3 PII (ADR-0018): sensitivity_ord=300, NOT in AT Repo, NOT federable.
 * Read access: CEO (j-kawasaki) + COO (a-nakamura) + CLO (k-bakshi) only.
 * Personal text columns SHOULD be signal:v1: encrypted at app layer (ADR §Field-level encrypt).
 *
 * Tables:
 *   vertex_etzhayyim_person_bio        Biographical: birth/gender/birthplace/family
 *   vertex_etzhayyim_person_education  School history (per-degree row)
 *   vertex_etzhayyim_person_career     Career history (per-position row)
 *   vertex_etzhayyim_person_dependent  Family/dependents (spouse/child/parent)
 *   vertex_etzhayyim_person_utterance  Statement/utterance log (Slack/PR/email)
 *                                     — drives behavioral profile via LLM
 *   vertex_etzhayyim_person_profile    Derived: Big5 + 保身 + risk tolerance
 *                                     + conflict style + learning velocity
 *   vertex_etzhayyim_person_minimax    Per-(person × task) minimax score:
 *                                     worst-case regret + expected value
 *
 * Streaming MVs:
 *   mv_etzhayyim_minimax_top_assignments  best person per task (lowest regret)
 *   mv_etzhayyim_profile_risk_summary     org-level Big5 / risk distribution
 *
 * ADR-0036: Worker-direct Hyperdrive.
 * ADR-0018: Tier 3 PII — RLS-gated, full PII allowed in non-Repo storage.
 * ADR-2604291800: Well-Becoming Spirit objective function (per-person Ω axes).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Biographical (birth / gender / birthplace / family environment) ────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_bio (
      vertex_id          varchar PRIMARY KEY,
      person_did         varchar NOT NULL,
      legal_name_ja      varchar,
      legal_name_kana    varchar,
      legal_name_en      varchar,
      birth_date         varchar,
      birth_year         int,
      gender             varchar,
      birthplace_country varchar DEFAULT 'JP',
      birthplace_pref    varchar,
      birthplace_city    varchar,
      nationality        varchar DEFAULT 'JP',
      household_type     varchar,
      family_env_summary varchar,
      socioeconomic_band varchar,
      collected_by       varchar,
      collected_at       varchar,
      consent_at         varchar,
      created_at         varchar,
      sensitivity_ord    int DEFAULT 300,
      owner_did          varchar)
  `.execute(db);

  // ── Education history (per degree / school / certification) ────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_education (
      vertex_id        varchar PRIMARY KEY,
      person_did       varchar NOT NULL,
      level            varchar,
      institution      varchar NOT NULL,
      institution_country varchar DEFAULT 'JP',
      department       varchar,
      degree           varchar,
      major            varchar,
      gpa              double precision,
      start_date       varchar,
      end_date         varchar,
      graduated        boolean,
      thesis_title     varchar,
      notable          varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 300,
      owner_did        varchar)
  `.execute(db);

  // ── Career history (per company / position) ─────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_career (
      vertex_id        varchar PRIMARY KEY,
      person_did       varchar NOT NULL,
      employer         varchar NOT NULL,
      employer_country varchar DEFAULT 'JP',
      title            varchar,
      department       varchar,
      employment_type  varchar,
      start_date       varchar,
      end_date         varchar,
      current          boolean DEFAULT false,
      summary          varchar,
      key_achievement  varchar,
      reason_for_leaving varchar,
      annual_salary_jpy double precision,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 300,
      owner_did        varchar)
  `.execute(db);

  // ── Dependents / family relationships ───────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_dependent (
      vertex_id        varchar PRIMARY KEY,
      person_did       varchar NOT NULL,
      relation         varchar NOT NULL,
      relation_summary varchar,
      birth_year       int,
      financial_dependent boolean DEFAULT false,
      care_dependent   boolean DEFAULT false,
      lives_with       boolean DEFAULT false,
      notes            varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 300,
      owner_did        varchar)
  `.execute(db);

  // ── Utterance log (Slack/PR comment/email — feeds behavioral profile) ──────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_utterance (
      vertex_id        varchar PRIMARY KEY,
      person_did       varchar NOT NULL,
      source           varchar NOT NULL,
      source_uri       varchar,
      uttered_at       varchar,
      audience         varchar,
      text_ciphertext  varchar,
      text_lang        varchar DEFAULT 'ja',
      sentiment        double precision,
      conflict_score   double precision,
      certainty_score  double precision,
      tags             varchar,
      llm_model        varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 300,
      owner_did        varchar)
  `.execute(db);

  // ── Derived profile (Big5 + 保身 + risk + conflict + learning) ─────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_profile (
      vertex_id              varchar PRIMARY KEY,
      person_did             varchar NOT NULL,
      assessed_at            varchar,
      method                 varchar,
      n_utterance_samples    int,
      big5_openness          double precision,
      big5_conscientiousness double precision,
      big5_extraversion      double precision,
      big5_agreeableness     double precision,
      big5_neuroticism       double precision,
      self_preservation      double precision,
      risk_tolerance         double precision,
      conflict_style         varchar,
      learning_velocity      double precision,
      autonomy_level         double precision,
      llm_compat_score       double precision,
      strengths_summary      varchar,
      caveats_summary        varchar,
      assessor_did           varchar,
      llm_model              varchar,
      created_at             varchar,
      sensitivity_ord        int DEFAULT 300,
      owner_did              varchar)
  `.execute(db);

  // ── Minimax score (per person × candidate task/role/contract path) ─────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_etzhayyim_person_minimax (
      vertex_id              varchar PRIMARY KEY,
      person_did             varchar NOT NULL,
      decision_kind          varchar NOT NULL,
      candidate_target       varchar NOT NULL,
      worst_case_loss_jpy    double precision,
      worst_case_summary     varchar,
      worst_case_probability double precision,
      expected_value_jpy     double precision,
      expected_value_summary varchar,
      regret_score           double precision,
      spirit_floor_violated  boolean DEFAULT false,
      wellbecoming_delta     double precision,
      feeling_delta          double precision,
      buffer_delta           double precision,
      ip_leak_risk           double precision,
      retention_risk         double precision,
      recommendation         varchar,
      rationale              varchar,
      assessed_at            varchar,
      assessor_did           varchar,
      llm_model              varchar,
      created_at             varchar,
      sensitivity_ord        int DEFAULT 300,
      owner_did              varchar)
  `.execute(db);

  // ── Streaming MVs ───────────────────────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_minimax_top_assignments AS
    SELECT
      decision_kind,
      candidate_target,
      person_did,
      regret_score,
      worst_case_loss_jpy,
      expected_value_jpy,
      spirit_floor_violated,
      ip_leak_risk,
      recommendation,
      assessed_at
    FROM vertex_etzhayyim_person_minimax
    WHERE spirit_floor_violated = false
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_profile_risk_summary AS
    SELECT
      COUNT(DISTINCT person_did) AS person_count,
      AVG(big5_openness)         AS avg_openness,
      AVG(big5_conscientiousness) AS avg_conscientiousness,
      AVG(big5_extraversion)     AS avg_extraversion,
      AVG(big5_agreeableness)    AS avg_agreeableness,
      AVG(big5_neuroticism)      AS avg_neuroticism,
      AVG(self_preservation)     AS avg_self_preservation,
      AVG(risk_tolerance)        AS avg_risk_tolerance,
      AVG(autonomy_level)        AS avg_autonomy
    FROM vertex_etzhayyim_person_profile
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_profile_risk_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_minimax_top_assignments`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_minimax`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_profile`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_utterance`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_dependent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_career`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_education`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_etzhayyim_person_bio`.execute(db);
}
