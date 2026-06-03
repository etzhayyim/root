/**
 * real-estate rw-free — barrel.
 *
 * Tier-2 on-chain property marketplace on the etzhayyim substrate (AT PDS records
 * + on-chain earnest deposit via TitheRouter). Per ADR-2606011400 (on-chain-only).
 * No Stripe, no RW.
 *
 *   listing : createListing / getListing / listListings
 *   offer   : createOffer / getOffer / acceptOffer / settleOffer
 *   tithe   : splitTithe / parseMicros
 *   settle  : donateSettlementExecutor (real on-chain adapter)
 */

export * from "./types.js";
export { splitTithe, parseMicros, TITHE_PERMILLE, type TitheSplit } from "./tithe.js";
export { createListing, getListing, listListings } from "./listing.js";
export { createOffer, getOffer, acceptOffer, settleOffer } from "./offer.js";
export { donateSettlementExecutor } from "./settlement.js";
