import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_api_key — add `product_scope` column for retail cloud P2
 * (ADR-2605080000 §D9 / Roadmap P2).
 *
 * Existing keys (`sk_live_*`) get product_scope=NULL meaning "all
 * products" (legacy / admin / unscoped). New product-scoped keys are
 * minted with `product_scope` ∈ {'yata', 'obj'} and key_prefix
 * `sk_live_yata_` / `sk_live_obj_` so the prefix carries the scope on
 * the wire and the column carries it for indexed lookups.
 *
 * verifyApiKey() returns product_scope alongside owner_did + scopes;
 * the auth layer enforces NSID-prefix gating:
 *   product_scope='yata' → com.etzhayyim.apps.yata.* + com.etzhayyim.apps.billing.* read
 *   product_scope='obj'  → com.etzhayyim.apps.obj.*  + com.etzhayyim.apps.billing.* read
 *   product_scope=NULL   → all NSIDs (legacy + admin + cross-product)
 *
 * Read path is scoped: a yata key calling /xrpc/com.etzhayyim.apps.obj.* is
 * 403, and vice versa. Billing read is always allowed (callers need
 * to query their own usage / invoices).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_api_key ADD COLUMN IF NOT EXISTS product_scope VARCHAR`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_api_key DROP COLUMN IF EXISTS product_scope`.execute(db);
}
