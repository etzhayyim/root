// ADR-0095 — Simplified 3-Layer Identity: canonical column convention + vertex_signal_identity.
//
// New tables use actor_did / org_did / at_did instead of org_id / user_id / actor_id.
// Existing tables are grandfathered; migration tracked in deps.toml [[migrations]]
// identity-canonical-columns-backfill.
//
// This migration:
//   1. Creates vertex_signal_identity with actor_did (ERC725 DID) as canonical PK.
//   2. Adds indexes for at_did federation lookup.
//
// Prekey bundle XRPC (com.etzhayyim.signal.getPrekeyBundle) resolves by actor_did first,
// falls back to at_did for legacy AT Protocol callers.

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_signal_identity — X25519 prekey store keyed by ERC725 canonical DID.
  // actor_did = did:erc725:etzhayyim:260425:{contract} (L1 root from ADR-0074 / ADR-0095)
  // at_did    = did:plc:{...} or did:web:{...}  (federation alias, nullable)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_signal_identity (
      vertex_id   VARCHAR PRIMARY KEY,
      actor_did   VARCHAR NOT NULL,
      at_did      VARCHAR,
      ik_pub      VARCHAR,
      spk_pub     VARCHAR,
      spk_sig     VARCHAR,
      opk_pubs    VARCHAR,
      org_did     VARCHAR NOT NULL DEFAULT 'anon',
      created_at  VARCHAR NOT NULL,
      _seq        BIGINT,
      sensitivity_ord INTEGER DEFAULT 2,
      owner_did   VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_signal_identity_actor_did
      ON vertex_signal_identity (actor_did)
  `.execute(db);

  // at_did lookup: AppView + legacy AT Protocol callers resolve via federation alias
  await sql`
    CREATE INDEX IF NOT EXISTS idx_signal_identity_at_did
      ON vertex_signal_identity (at_did)
  `.execute(db);

  // vertex_erc725_linked_method — ERC725 root → linked auth methods.
  // Replaces did:pkh as first-class DID with wallet_address field only.
  // Each row = one linked method under an ERC725 root identity.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_erc725_linked_method (
      vertex_id          VARCHAR PRIMARY KEY,
      actor_did          VARCHAR NOT NULL,
      org_did            VARCHAR NOT NULL DEFAULT 'anon',
      at_did             VARCHAR,
      provider           VARCHAR NOT NULL,
      wallet_address     VARCHAR,
      chain_id           VARCHAR,
      wallet_kind        VARCHAR,
      verification_kind  VARCHAR,
      siwe_hash          VARCHAR,
      linked_at          VARCHAR,
      revoked_at         VARCHAR,
      created_at         VARCHAR NOT NULL,
      _seq               BIGINT,
      sensitivity_ord    INTEGER DEFAULT 1,
      owner_did          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_erc725_linked_method_actor_did
      ON vertex_erc725_linked_method (actor_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_erc725_linked_method_wallet_address
      ON vertex_erc725_linked_method (wallet_address)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_erc725_linked_method`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_signal_identity`.execute(db);
}
