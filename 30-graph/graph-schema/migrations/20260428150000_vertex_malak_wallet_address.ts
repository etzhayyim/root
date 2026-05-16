// ADR-0056 / ADR-0036 — vertex_malak_wallet_address schema.
//
// Creates the wallet address table (CONTROLS_WALLET vertex) and its
// edge table so linkWalletToActor BPMN can persist directly to
// Hyperdrive (bypassing the legacy PDS createRecord path).
//
// Paired seed migration: 20260428160000_seed_malak_link_wallet_bpmn.ts

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_malak_wallet_address (
      vertex_id       VARCHAR NOT NULL PRIMARY KEY,
      rkey            VARCHAR NOT NULL,
      repo            VARCHAR NOT NULL,
      did             VARCHAR NOT NULL,
      chain           VARCHAR NOT NULL,
      address         VARCHAR NOT NULL,
      actor_node_id   VARCHAR NOT NULL,
      label           VARCHAR NOT NULL DEFAULT '',
      confidence      BIGINT  NOT NULL DEFAULT 70,
      evidence        VARCHAR NOT NULL DEFAULT '',
      linked_at       VARCHAR NOT NULL,
      sensitivity_ord BIGINT  NOT NULL DEFAULT 100,
      owner_did       VARCHAR NOT NULL,
      created_date    DATE    NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_malak_controls_wallet (
      edge_id         VARCHAR NOT NULL PRIMARY KEY,
      src_vid         VARCHAR NOT NULL,
      dst_vid         VARCHAR NOT NULL,
      sensitivity_ord BIGINT  NOT NULL DEFAULT 100,
      owner_did       VARCHAR NOT NULL,
      created_date    DATE    NOT NULL
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_wallet_address
      ON vertex_malak_wallet_address (address)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_wallet_chain_address
      ON vertex_malak_wallet_address (chain, address)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_controls_wallet_src
      ON edge_malak_controls_wallet (src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_malak_controls_wallet_dst
      ON edge_malak_controls_wallet (dst_vid)
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_malak_controls_wallet_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_malak_controls_wallet_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_malak_wallet_chain_address`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_malak_wallet_address`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_malak_controls_wallet`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_malak_wallet_address`.execute(db);
  await sql`FLUSH`.execute(db);
}
