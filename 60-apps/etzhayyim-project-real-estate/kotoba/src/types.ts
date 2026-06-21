/**
 * real-estate kotoba — record types.
 *
 * Tier-2 function-split per ADR-2606011400 (on-chain-only). Property listings +
 * offers on AT PDS records; an accepted offer's earnest deposit settles on-chain
 * (USDC + ERC-4337 + TitheRouter 10% Public-Fund split). No Stripe, no RW.
 * ADR-2605172000 kotoba.
 *
 * Amounts are USDC base units (micros) as decimal STRINGS.
 *
 * Identity hierarchy:
 *   did:web:real-estate.etzhayyim.com                       — controller
 *   did:web:real-estate.etzhayyim.com:listing:{listingId}   — a listing
 *   did:web:real-estate.etzhayyim.com:offer:{offerId}       — an offer
 */

export const RE_DID_PREFIX = "did:web:real-estate.etzhayyim.com:" as const;

export const LISTING_COLLECTION = "com.etzhayyim.apps.realEstate.listing";
export const OFFER_COLLECTION = "com.etzhayyim.apps.realEstate.offer";
export const PAYMENT_COLLECTION = "com.etzhayyim.apps.realEstate.payment";

export type RealEstatePaymentPurpose = "internal-purchase" | "escrow-refund";

export type PropertyType = "land" | "house" | "condo" | "commercial" | "other";

export type ListingStatus = "active" | "under_offer" | "sold" | "withdrawn";

export type OfferStatus =
  | "pending"
  | "accepted"
  | "rejected"
  | "withdrawn"
  | "deposited";

// ─── Listing ────────────────────────────────────────────────────────

export interface ListingRecord {
  did: string;
  listingId: string;
  sellerDid: string;
  title: string;
  propertyType: PropertyType;
  location?: string;
  /** Asking price, USDC micros as string. */
  askingPriceMicros: string;
  /** Floor/land area in whole m² (AT Lexicon has no float). */
  sizeM2?: number;
  status: ListingStatus;
  createdAt: string;
}

export interface ListingView extends ListingRecord {
  listingUri: string;
}

export interface CreateListingInput {
  listingId: string;
  sellerDid: string;
  title: string;
  propertyType: PropertyType;
  askingPriceMicros: string;
  location?: string;
  sizeM2?: number;
}

export interface CreateListingOutput {
  status: "created" | "alreadyExists" | "rejected";
  listingUri?: string;
  did?: string;
  listingId?: string;
  error?: string;
}

export interface GetListingInput {
  listingId: string;
}

export interface GetListingOutput {
  listing?: ListingView;
  error?: string;
}

export interface ListListingsInput {
  propertyType?: PropertyType;
  status?: ListingStatus;
  location?: string;
  limit?: number;
  cursor?: string;
}

export interface ListListingsOutput {
  items: ListingView[];
  cursor?: string;
  total: number;
}

// ─── Offer ──────────────────────────────────────────────────────────

export interface OfferRecord {
  did: string;
  offerId: string;
  listingId: string;
  buyerDid: string;
  /** Offered price, USDC micros as string. */
  amountMicros: string;
  status: OfferStatus;
  txHash?: string;
  createdAt: string;
}

export interface OfferView extends OfferRecord {
  offerUri: string;
}

export interface CreateOfferInput {
  offerId: string;
  listingId: string;
  buyerDid: string;
  amountMicros: string;
}

export interface CreateOfferOutput {
  status: "created" | "alreadyExists" | "rejected" | "listingNotFound";
  offerUri?: string;
  did?: string;
  offerId?: string;
  error?: string;
}

export interface GetOfferInput {
  offerId: string;
}

export interface GetOfferOutput {
  offer?: OfferView;
  error?: string;
}

export interface AcceptOfferInput {
  offerId: string;
}

export interface AcceptOfferOutput {
  status: "accepted" | "notFound" | "rejected";
  offerId?: string;
  error?: string;
}

// ─── On-chain earnest deposit ───────────────────────────────────────

export interface PaymentRecord {
  offerId: string;
  listingId: string;
  buyerDid: string;
  purpose: RealEstatePaymentPurpose;
  grossMicros: string;
  titheMicros: string;
  netMicros: string;
  txHash?: string;
  settledAt: string;
}

export interface SettlementExecutor {
  (opts: {
    to: string;
    amountMicros: bigint;
    purpose: RealEstatePaymentPurpose;
    memo?: string;
    forUri?: string;
  }): Promise<{ txHash: string }>;
}

export interface SettleOfferInput {
  offerId: string;
  /** Seller / escrow payout address (Base L2). */
  to: string;
  /** Earnest deposit amount, USDC micros as string. */
  depositMicros: string;
  memo?: string;
}

export interface SettleOfferOutput {
  status: "settled" | "rejected" | "notFound" | "alreadyDeposited" | "notAccepted";
  paymentUri?: string;
  txHash?: string;
  titheMicros?: string;
  netMicros?: string;
  error?: string;
}

// ─── Helpers ────────────────────────────────────────────────────────

const PROPERTY_TYPES = new Set(["land", "house", "condo", "commercial", "other"]);

export function isValidPropertyType(t: string): boolean {
  return PROPERTY_TYPES.has(t);
}

export function listingDid(listingId: string): string {
  return `${RE_DID_PREFIX}listing:${listingId.toLowerCase()}`;
}

export function listingRkey(listingId: string): string {
  return `listing-${listingId.toLowerCase()}`;
}

export function offerDid(offerId: string): string {
  return `${RE_DID_PREFIX}offer:${offerId.toLowerCase()}`;
}

export function offerRkey(offerId: string): string {
  return `offer-${offerId.toLowerCase()}`;
}

export function paymentRkey(offerId: string): string {
  return `payment-${offerId.toLowerCase()}`;
}
