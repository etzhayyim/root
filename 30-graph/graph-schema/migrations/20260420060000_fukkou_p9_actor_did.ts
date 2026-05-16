import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0037 — 復興予算 Phase 9: Actor DID registry + LEI + person↔org.
 *
 * 公開記録にある org / person すべてを actor DID 空間に紐付ける:
 *   corp   : did:web:jpn-corp.gftd.ai:{slug}      + 任意 GLEIF LEI
 *   person : did:web:jpn-people.gftd.ai:{slug}
 *   state  : did:web:jpn-state.gftd.ai:{path}     (既存、登録のみ)
 *
 * + edge_fukkou_person_represents_org (閣僚ポスト / 次官 / 担当官)
 * + edge_fukkou_actor_succeeds        (次官後任 / 総理交代 / 役職継承)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_actor_did (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      actor_did         VARCHAR,
      actor_type        VARCHAR,
      display_name      VARCHAR,
      display_name_kana VARCHAR,
      handle            VARCHAR,
      country           VARCHAR,
      lei_code          VARCHAR,
      corporate_number  VARCHAR,
      gender            VARCHAR,
      role              VARCHAR,
      linked_vertex_id  VARCHAR,
      linked_vertex_type VARCHAR,
      did_verification_status VARCHAR,
      canonical         BOOLEAN,
      created_at        TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_person_represents_org (
      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,
      person_actor_did VARCHAR, org_actor_did VARCHAR,
      role VARCHAR, start_date DATE, end_date DATE,
      confidence NUMERIC, created_at TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_fukkou_actor_succeeds (
      edge_id VARCHAR PRIMARY KEY, _seq BIGINT,
      from_actor_did VARCHAR, to_actor_did VARCHAR,
      relation VARCHAR, effective_date DATE, created_at TIMESTAMPTZ
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const t of [
    'edge_fukkou_actor_succeeds',
    'edge_fukkou_person_represents_org',
    'vertex_fukkou_actor_did',
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
