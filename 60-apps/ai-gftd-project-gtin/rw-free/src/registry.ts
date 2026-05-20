/**
 * gtin rw-free — registry (slice 1, 4/4 canonical complete).
 *
 *   registerProduct — register a Product (rkey=product-{canonicalGtin14})
 *                     Canonicalizes any of gtin/jan/upc/ean to GTIN-14.
 *                     Validates checksum; rejects invalid.
 *   lookupProduct   — by any GTIN family (normalizes + canonicalizes)
 *   validateGtin    — pure helper: validate + return canonicalGtin14
 *
 * GTIN-14 is the canonical storage form — GTIN-8/UPC-12/EAN-13/JAN-13
 * all left zero-pad to GTIN-14. Lookup accepts any form.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  detectCodeType,
  gtinCheckDigit,
  isValidGtin,
  normalizeGtinDigits,
  productDid,
  productRkey,
  toGtin14,
  type CodeType,
  type LookupProductInput,
  type LookupProductOutput,
  type ProductRecord,
  type ProductView,
  type RegisterProductInput,
  type RegisterProductOutput,
  type ValidateGtinInput,
  type ValidateGtinOutput,
} from "./types.js";

const PRODUCT_COLLECTION = "ai.gftd.gtin.product";

function pickGtin(input: RegisterProductInput): {
  digits: string;
  codeType: CodeType;
} {
  const candidate =
    input.gtin ??
    input.jan ??
    input.ean ??
    input.upc ??
    "";
  const digits = normalizeGtinDigits(candidate);
  const codeType = detectCodeType(digits);
  return { digits, codeType };
}

export async function registerProduct(
  e: Etzhayyim,
  input: RegisterProductInput
): Promise<RegisterProductOutput> {
  if (!input.productId || !input.name) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const { digits, codeType } = pickGtin(input);
  if (codeType === "invalid" || !isValidGtin(digits)) {
    return { status: "invalidChecksum", error: "invalidGtin" };
  }
  const canonicalGtin14 = toGtin14(digits);
  if (!canonicalGtin14) {
    return { status: "rejected", error: "canonicalizationFailed" };
  }
  const rkey = productRkey(canonicalGtin14);
  const existing = await e
    .read<ProductRecord>({ collection: PRODUCT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      productId: existing.records[0].value.productId,
      productDid: existing.records[0].value.did,
      canonicalGtin14,
      productUri: existing.records[0].uri,
    };
  }
  const did = productDid(canonicalGtin14);
  const now = new Date().toISOString();
  const original =
    input.gtin ?? input.jan ?? input.ean ?? input.upc ?? digits;
  const record: ProductRecord = {
    did,
    productId: input.productId,
    canonicalGtin14,
    name: input.name,
    brand: input.brand,
    model: input.model,
    originalCodeType: codeType,
    originalCode: original,
    packSize: input.packSize,
    category: input.category,
    createdAt: now,
  };
  const receipt = await e.write({
    collection: PRODUCT_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    productId: input.productId,
    productDid: did,
    canonicalGtin14,
    productUri: receipt.uri,
  };
}

export async function lookupProduct(
  e: Etzhayyim,
  input: LookupProductInput
): Promise<LookupProductOutput> {
  if (!input.code) return { error: "missingCode" };
  const digits = normalizeGtinDigits(input.code);
  const codeType = detectCodeType(digits);
  if (codeType === "invalid" || !isValidGtin(digits)) {
    return { error: "invalidGtin", codeType };
  }
  const canonicalGtin14 = toGtin14(digits);
  if (!canonicalGtin14) return { error: "canonicalizationFailed" };
  const resp = await e
    .read<ProductRecord>({
      collection: PRODUCT_COLLECTION,
      rkey: productRkey(canonicalGtin14),
    })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { codeType, canonicalGtin14, error: "notFound" };
  const view: ProductView = { ...r.value, productUri: r.uri };
  return { product: view, codeType, canonicalGtin14 };
}

export async function validateGtin(
  _e: Etzhayyim,
  input: ValidateGtinInput
): Promise<ValidateGtinOutput> {
  if (!input.code) return { valid: false, error: "missingCode" };
  const digits = normalizeGtinDigits(input.code);
  const codeType = detectCodeType(digits);
  if (codeType === "invalid") {
    return { valid: false, codeType, normalized: digits };
  }
  const valid = isValidGtin(digits);
  if (!valid) return { valid, codeType, normalized: digits };
  const checkDigit = Number(digits[digits.length - 1]);
  const canonicalGtin14 = toGtin14(digits);
  return {
    valid,
    codeType,
    normalized: digits,
    canonicalGtin14,
    checkDigit,
  };
}

// Re-export gtinCheckDigit for caller diagnostics.
export { gtinCheckDigit };
