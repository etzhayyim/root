import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_api_key — add AWS-style credentials for /s3/* SigV4 compat
 * (ADR-2605080000 §D10 P3.2).
 *
 * P2 added `product_scope` so a single sk_live_yata_* token can carry
 * the yata product gate.  P3.2 adds a parallel AWS-style identity
 * (`aws_access_key_id` + `aws_secret_access_key`) on the same row so
 * boto3 / aws-sdk-js / mc clients can talk to yatabase.etzhayyim.com/s3/*
 * with native AWS Signature Version 4.
 *
 * Each api key row now carries TWO equivalent identities:
 *   - sk_live_yata_<...>     wire prefix, hashed in `key_hash`
 *   - aws_access_key_id      AKIA-prefix synthetic id, indexed for SigV4 lookup
 *   - aws_secret_access_key  40-byte random secret, plaintext-stored
 *                            (see Security note below)
 *
 * Both refer to the same owner_did + product_scope.  Customers pick
 * which to use:
 *   - sk_live_yata_*  for /xrpc/* and /storage/v1/* (Bearer)
 *   - AWS creds       for /s3/{bucket}/{key} (SigV4)
 *
 * Security note:
 *   aws_secret_access_key is stored *plaintext* in vertex_api_key.
 *   Rationale: AWS SigV4 verification requires the raw secret to
 *   recompute the canonical signature.  This is the same trade-off
 *   AWS IAM has had for 15+ years (the secret is retrievable in the
 *   IAM console until the user rotates).  Mitigations:
 *
 *   1. Sensitivity: the row is sensitivity_ord=2 (NOT Tier-3 PII), but
 *      access is restricted to the owner_did + billing admin.
 *   2. Rotation: customers can revoke + re-issue by calling
 *      ai.gftd.auth.revokeApiKey + ai.gftd.auth.createApiKey.
 *   3. KEK encryption: a follow-up phase will optionally KEK-encrypt
 *      this column with the platform signing-key custody (ADR-0010
 *      Stage 1) — schema slot reserved by name.
 *
 * Index `idx_vertex_api_key_aws` enables O(log N) lookup by access
 * key id from the SigV4 verifier hot path; reads happen on every
 * inbound /s3/* request.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_api_key ADD COLUMN IF NOT EXISTS aws_access_key_id     VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_api_key ADD COLUMN IF NOT EXISTS aws_secret_access_key VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_api_key_aws ON vertex_api_key (aws_access_key_id)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_api_key_aws`.execute(db);
  await sql`ALTER TABLE vertex_api_key DROP COLUMN IF EXISTS aws_secret_access_key`.execute(db);
  await sql`ALTER TABLE vertex_api_key DROP COLUMN IF EXISTS aws_access_key_id`.execute(db);
}
