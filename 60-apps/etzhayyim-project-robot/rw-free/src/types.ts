/**
 * robot rw-free — product-front package, kotoba-E2E split.
 *
 * Per ADR-2606011400 (Consensys) + ADR-2605172400 (3-axis) + ADR-2605181100
 * (kotoba E2E encrypted-record envelope). Founder directive 2026-06-03: PII /
 * CUI / confidential migrate to etzhayyim when made safe via kotoba E2E.
 *
 * SPLIT (grounded in the robotics lexicon surface + PROJECT.jsonld
 * "Reachy Mini ... dropshipping storefront"):
 *   PUBLIC (plaintext AT records) — robot product catalog: the open
 *   storefront / dropshipping listing (productId, name, assetKind, region,
 *   priceUsd as decimal STRING, status). Frontable open metadata, no PII.
 *   register/get/list + FK via exists() + coverage countAll.
 *
 *   SENSITIVE / CONFIDENTIAL (kotoba E2E, com.etzhayyim.encrypted.record) —
 *   customer orders (salesPlan surface: customerId + itemOrService + quantity
 *   + commercialTerms). customerId + commercial terms are confidential
 *   counterparty data; sealed via sdk.encryptedWrite (read-cap = owner DID +
 *   explicit recipients), so the substrate never sees them in plaintext.
 *   FK: order.productId must exist in the public catalog (exists()).
 *
 *   STAYS etzhayyim (NOT a collection — consumed via consent-capability) —
 *   fiat merchant-of-record / dropshipping settlement EXECUTION (Stripe/BSP/
 *   bank transfer), robot motion / safety-gate enforcement ACTIONS, and
 *   GPU/LLM INFERENCE for KAMI scene planning. These are regulated *acts*; the
 *   resulting DATA records migrate (catalog plaintext, orders E2E).
 *
 * AT-Lexicon: no float. quantity is integer; priceUsd / commercialTerms /
 * totalUsd are decimal STRINGS.
 */

// Plaintext public collection.
export const CATALOG_COLLECTION = "com.etzhayyim.apps.robot.productCatalog";
// E2E inner-type NSID (body shape inside the encrypted envelope).
export const ORDER_INNER_TYPE = "com.etzhayyim.apps.robot.customerOrder";

export const ROBOT_DID_PREFIX = "did:web:robot.etzhayyim.com:" as const;

// ─── Product catalog (PLAINTEXT, public storefront) ─────────────────

export interface ProductCatalogRecord {
  did: string;
  productId: string;
  name: string;
  /** robot | agv | drone | vehicle | … (from robotics assetKind surface). */
  assetKind: string;
  region: string;
  /** decimal STRING (no float in AT-Lexicon). e.g. "299.00". */
  priceUsd: string;
  /** listing status: "available" | "preorder" | "discontinued". */
  status: string;
  createdAt: string;
}
export interface ProductCatalogView extends ProductCatalogRecord {
  productUri: string;
}
export interface RegisterProductInput {
  productId: string;
  name: string;
  assetKind: string;
  region: string;
  priceUsd: string;
  status?: string;
}
export interface RegisterProductOutput {
  status: "registered" | "alreadyExists" | "rejected";
  productUri?: string;
  did?: string;
  productId?: string;
  error?: string;
}
export interface GetProductInput {
  productId: string;
}
export interface GetProductOutput {
  product?: ProductCatalogView;
  error?: string;
}
export interface ListProductsInput {
  assetKind?: string;
  region?: string;
  limit?: number;
  cursor?: string;
}
export interface ListProductsOutput {
  items: ProductCatalogView[];
  cursor?: string;
  total: number;
}

// ─── Customer order (E2E-ENCRYPTED, confidential) ───────────────────

export interface CustomerOrderBody {
  orderId: string;
  /** FK → ProductCatalogRecord.productId (validated via exists()). */
  productId: string;
  /** confidential counterparty id. */
  customerId: string;
  itemOrService: string;
  /** integer (no float). */
  quantity: number;
  /** decimal STRING, confidential commercial terms / negotiated total. */
  commercialTerms: string;
  placedAt: string;
}
export interface CustomerOrderView extends CustomerOrderBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface PlaceOrderInput {
  orderId: string;
  productId: string;
  customerId: string;
  itemOrService: string;
  quantity: number;
  commercialTerms: string;
  placedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface PlaceOrderOutput {
  status: "placed" | "rejected";
  uri?: string;
  keyId?: string;
  orderId?: string;
  error?: string;
}
export interface ListOrdersInput {
  productId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListOrdersOutput {
  items: CustomerOrderView[];
  cursor?: string;
  total: number;
}
export interface GetOrderInput {
  orderId: string;
}
export interface GetOrderOutput {
  order?: CustomerOrderView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  productCatalogCount?: number;
  customerOrderCount?: number;
  productsByAssetKind?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isPositiveInt(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n > 0;
}
/** decimal STRING guard (no float fields in AT-Lexicon). */
export function isDecimalString(s: unknown): s is string {
  return typeof s === "string" && /^\d+(\.\d+)?$/.test(s);
}
export function productDidFor(id: string): string {
  return `${ROBOT_DID_PREFIX}prod:${id.toLowerCase()}`;
}
export function productRkey(id: string): string {
  return `prod-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
export function orderRkey(id: string): string {
  return `order-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
