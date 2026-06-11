/**
 * robot rw-free — registry, kotoba-E2E split.
 *
 * Plaintext path (productCatalog): sdk.write / sdk.read — public storefront
 * register/get/list, FK exists() check.
 * E2E path (customerOrder): sdk.encryptedWrite / sdk.encryptedRead —
 * confidential counterparty body sealed in the kotoba envelope
 * (ADR-2605181100), read-cap = owner DID + explicit recipients. The substrate
 * never sees customerId / commercialTerms in plaintext.
 *
 * Settlement EXECUTION (fiat MoR/Stripe/BSP), robot motion / safety-gate
 * enforcement, and KAMI GPU/LLM inference stay etzhayyim, consumed via
 * consent-capability — only the resulting DATA records live here.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  CATALOG_COLLECTION,
  ORDER_INNER_TYPE,
  isDecimalString,
  isPositiveInt,
  orderRkey,
  productDidFor,
  productRkey,
  type CoverageInput,
  type CoverageOutput,
  type CustomerOrderBody,
  type CustomerOrderView,
  type GetOrderInput,
  type GetOrderOutput,
  type GetProductInput,
  type GetProductOutput,
  type ListOrdersInput,
  type ListOrdersOutput,
  type ListProductsInput,
  type ListProductsOutput,
  type PlaceOrderInput,
  type PlaceOrderOutput,
  type ProductCatalogRecord,
  type ProductCatalogView,
  type RegisterProductInput,
  type RegisterProductOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Product catalog (PLAINTEXT) ────────────────────────────────────

export async function registerProduct(e: Etzhayyim, input: RegisterProductInput): Promise<RegisterProductOutput> {
  if (!input.productId || !input.name || !input.assetKind || !input.region) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isDecimalString(input.priceUsd)) return { status: "rejected", error: "invalidPriceUsd" };
  const rkey = productRkey(input.productId);
  const existing = await e
    .read<ProductCatalogRecord>({ collection: CATALOG_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", productUri: existing.records[0].uri, did: existing.records[0].value.did, productId: input.productId };
  }
  const now = new Date().toISOString();
  const did = productDidFor(input.productId);
  const record: ProductCatalogRecord = {
    did,
    productId: input.productId,
    name: input.name,
    assetKind: input.assetKind,
    region: input.region,
    priceUsd: input.priceUsd,
    status: input.status ?? "available",
    createdAt: now,
  };
  const receipt = await e.write({ collection: CATALOG_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", productUri: receipt.uri, did, productId: input.productId };
}

export async function getProduct(e: Etzhayyim, input: GetProductInput): Promise<GetProductOutput> {
  if (!input.productId) return { error: "invalidProductId" };
  const resp = await e
    .read<ProductCatalogRecord>({ collection: CATALOG_COLLECTION, rkey: productRkey(input.productId) })
    .catch(() => ({ records: [] }));
  const hit = resp.records[0];
  if (!hit?.value) return { error: "notFound" };
  return { product: { ...hit.value, productUri: hit.uri } };
}

/** FK presence check (the mock has no exists() — implemented as read-by-rkey). */
async function productExists(e: Etzhayyim, productId: string): Promise<boolean> {
  const resp = await e
    .read<ProductCatalogRecord>({ collection: CATALOG_COLLECTION, rkey: productRkey(productId) })
    .catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

export async function listProducts(e: Etzhayyim, input: ListProductsInput = {}): Promise<ListProductsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ProductCatalogRecord>({ collection: CATALOG_COLLECTION, cursor: input.cursor, limit });
  const items: ProductCatalogView[] = resp.records
    .filter((r) => !input.assetKind || r.value.assetKind === input.assetKind)
    .filter((r) => !input.region || r.value.region === input.region)
    .map((r) => ({ ...r.value, productUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Customer order (E2E-ENCRYPTED, confidential) ───────────────────

export async function placeOrder(e: Etzhayyim, input: PlaceOrderInput): Promise<PlaceOrderOutput> {
  if (!input.orderId || !input.productId || !input.customerId || !input.itemOrService) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isPositiveInt(input.quantity)) return { status: "rejected", error: "invalidQuantity" };
  if (!isDecimalString(input.commercialTerms)) return { status: "rejected", error: "invalidCommercialTerms" };
  // FK: order.productId must exist in the public catalog.
  if (!(await productExists(e, input.productId))) return { status: "rejected", error: "unknownProduct" };
  const body: CustomerOrderBody = {
    orderId: input.orderId,
    productId: input.productId,
    customerId: input.customerId,
    itemOrService: input.itemOrService,
    quantity: input.quantity,
    commercialTerms: input.commercialTerms,
    placedAt: input.placedAt ?? new Date().toISOString(),
  };
  // Read-cap = owner DID (sender, auto-wrapped) + any explicit recipients.
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: ORDER_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: orderRkey(input.orderId),
  });
  return { status: "placed", uri: receipt.uri, keyId: receipt.keyId, orderId: input.orderId };
}

async function scanOrders(e: Etzhayyim, maxScan: number): Promise<CustomerOrderView[]> {
  const out: CustomerOrderView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<CustomerOrderBody>({ innerType: ORDER_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listOrders(e: Etzhayyim, input: ListOrdersInput = {}): Promise<ListOrdersOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanOrders(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((o) => !input.productId || o.productId === input.productId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getOrder(e: Etzhayyim, input: GetOrderInput): Promise<GetOrderOutput> {
  if (!input.orderId) return { error: "invalidOrderId" };
  const all = await scanOrders(e, DEFAULT_MAX_SCAN);
  const found = all.find((o) => o.orderId === input.orderId);
  if (!found) return { error: "notFound" };
  return { order: found };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const productsByAssetKind: Record<string, number> = {};
  let productCatalogCount = 0;
  let cursor: string | undefined;
  while (productCatalogCount < maxScan) {
    const page = await e.read<ProductCatalogRecord>({ collection: CATALOG_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      productsByAssetKind[r.value.assetKind] = (productsByAssetKind[r.value.assetKind] ?? 0) + 1;
      productCatalogCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const customerOrderCount = (await scanOrders(e, maxScan)).length;
  return {
    productCatalogCount,
    customerOrderCount,
    productsByAssetKind,
    truncated: productCatalogCount >= maxScan || customerOrderCount >= maxScan,
  };
}
